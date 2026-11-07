"""Vectorized 2D mass-spring dynamics. Array row zero is the body's top.

Each unique corner has equal mass. A shared edge averages its owners'
stiffness and rest-length modulation; a diagonal belongs to one voxel.
Contact uses a non-bouncing normal impulse and Coulomb friction.
"""
import numpy as np
import config as C
from controllers import angle, sensors, neural_output, ground


def _body_ok(body):
    a = np.asarray(body)
    return (a.ndim == 2 and 0 < min(a.shape) and max(a.shape) <= C.MAX_BODY_SIZE
            and np.issubdtype(a.dtype, np.integer) and np.all((a >= 0) & (a <= 4)))


def is_valid(body):
    """Require a bounded integer grid, edge connectivity, and an actuator."""
    if not _body_ok(body):
        return False
    a = np.asarray(body)
    occupied = set(map(tuple, np.argwhere(a != 0)))
    if not occupied or not np.any((a == 3) | (a == 4)):
        return False
    seen = {next(iter(occupied))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for cell in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if cell in occupied and cell not in seen:
                seen.add(cell)
                stack.append(cell)
    return seen == occupied


def _mesh(body):
    if not _body_ok(body) or not np.any(body):
        raise ValueError('Body must be a nonempty integer grid of types 0–4, at most 5x5')
    body = np.asarray(body)
    nodes, edges, polygons = {}, {}, []
    for r, c in np.argwhere(body != 0):
        y = body.shape[0] - 1 - r
        corners = [(c, y), (c+1, y), (c+1, y+1), (c, y+1)]
        ids = [nodes.setdefault(p, len(nodes)) for p in corners]
        polygons.append((r, c, ids))
        for u, v in ((0,1), (1,2), (2,3), (3,0), (0,2), (1,3)):
            key = tuple(sorted((ids[u], ids[v])))
            horizontal = corners[u][1] == corners[v][1]
            vertical = corners[u][0] == corners[v][0]
            material = int(body[r,c])
            active = (material == 3 and horizontal) or (material == 4 and vertical)
            edges.setdefault(key, []).append((r, c, material, active))
    points = np.array(list(nodes), dtype=float)
    springs = np.array(list(edges), dtype=int)
    rest = np.linalg.norm(points[springs[:,1]] - points[springs[:,0]], axis=1)
    return points, springs, list(edges.values()), rest, polygons


def build_robot(body):
    """Return points (N,2), unique springs (S,2), types (S,), rest lengths.

    Shared types use the largest owning material code; dynamics averages the
    actual material contributions, including both phases on a shared edge.
    """
    p, s, owners, rest, _ = _mesh(np.asarray(body))
    types = np.array([max(o[2] for o in group) for group in owners])
    return p, s, types, rest


def voxel_polygons(body):
    """Return (row, column, four node indices) in counterclockwise order."""
    return _mesh(np.asarray(body))[4]


def upright_cosine(reference, positions):
    """Cosine of the best-fit planar rotation of a centered rest mesh.

    dot and cross are the 2D orthogonal Procrustes solution. Using all nodes
    tolerates local leg deformation and works for wide or one-voxel bodies.
    Translation cancels because reference has zero mean.
    """
    dot = np.sum(reference * positions)
    cross = np.sum(reference[:,0]*positions[:,1] - reference[:,1]*positions[:,0])
    return float(dot / max(np.hypot(dot, cross), 1e-12))


def simulate(body, controller_params=None, steps=None, record=False, diagnostics=None,
             actuation_enabled=True, terrain='flat', push=False,
             terrain_seed=C.ROUGH_SEED, push_time=C.PUSH_TIME,
             push_magnitude=-C.PUSH_DELTA_V, track_contact=True):
    """Return signed COM displacement; with record, return (fitness, frames).

    Open-loop params contain ``omega`` and body-shaped ``phases``. Closed-loop
    params set ``kind='closed_loop'`` and provide the four neural arrays;
    ``kind='neural_clock_only'`` uses the same network with five sensors masked.
    Invalid bodies or unstable runs return zero; failed recordings are empty.
    Sustained toppling disqualifies a run (fitness zero); otherwise fitness is
    exactly signed COM displacement. actuation_enabled=False provides a passive
    control run without changing global configuration. Diagnostics include raw distance and fall
    status as well as time/min_y at EVERY physics step when track_contact=True.
    Terrain seeds and push settings are per-rollout arguments, never mutable
    globals, so multiprocessing candidates share exactly the intended episodes.
    """
    empty = np.empty((0, 0, 2))
    if diagnostics is not None:
        diagnostics.clear()
        diagnostics.update(valid=False, stable=False, fell=False, raw_distance=0.0)
    if not is_valid(body):
        return (0.0, empty) if record else 0.0
    body = np.asarray(body)
    if terrain not in ('flat', 'rough'):
        raise ValueError('terrain must be flat or rough')
    if not np.isfinite(push_time) or push_time < 0 or not np.isfinite(push_magnitude) or push_magnitude < 0:
        raise ValueError('Push time and magnitude must be finite and nonnegative')
    def surface_at(x):
        return ground(x, terrain, terrain_seed)
    params = controller_params or {}
    omega = float(params.get('omega', C.OMEGA))
    phases = np.asarray(params.get('phases', np.zeros(body.shape)), dtype=float)
    if phases.shape != body.shape or not np.all(np.isfinite(phases)) or not np.isfinite(omega):
        raise ValueError('Controller requires finite omega and body-shaped finite phases')
    omega = float(np.clip(omega, C.OMEGA_MIN, C.OMEGA_MAX))
    steps = round(C.SIM_SECONDS / C.DT) if steps is None else steps
    if not isinstance(steps, (int, np.integer)) or steps < 0:
        raise ValueError('steps must be a nonnegative integer')
    p, springs, owners, rest, _ = _mesh(body)
    p[:,1] += C.START_HEIGHT
    if terrain != 'flat':
        p[:,1] += float(surface_at(p[:,0])[0].max())
    v = np.zeros_like(p)
    initial_x = p[:,0].mean()
    reference = p - p.mean(axis=0)
    fall_cosine = np.cos(np.deg2rad(C.FALL_ANGLE_DEGREES))
    tilted_time = 0.0
    fell = False
    worst_cosine = 1.0
    a, b = springs.T
    neural = params.get('kind', 'open_loop') in ('closed_loop', 'neural_clock_only')
    actuator_cells = np.argwhere((body == 3) | (body == 4))
    cell_index = {tuple(cell):i for i,cell in enumerate(actuator_cells)}
    outputs = len(actuator_cells)
    if neural:
        # Co-evolution keeps a fixed row-major output for every 5x5 grid cell.
        # Legacy fixed-body checkpoints retain their actuator-only layout.
        if np.shape(params.get('w2')) == (25, C.NN_HIDDEN) and body.shape == (5, 5):
            outputs = 25
            cell_index = {(r,c):r*5+c for r,c in actuator_cells}
        expected = ((C.NN_HIDDEN, C.NN_INPUTS), (C.NN_HIDDEN,),
                    (outputs, C.NN_HIDDEN), (outputs,))
        arrays = tuple(np.asarray(params.get(name), dtype=float)
                       for name in ('w1', 'b1', 'w2', 'b2'))
        if tuple(a.shape for a in arrays) != expected or not all(np.all(np.isfinite(a)) for a in arrays):
            raise ValueError('Closed-loop controller has invalid neural-network parameters')
    owner_matrix = np.zeros((len(owners),outputs))
    if neural:
        for spring, group in enumerate(owners):
            for r,c,_,active in group:
                if active:
                    owner_matrix[spring,cell_index[(r,c)]] += 1/len(group)
    output = np.zeros(outputs)
    previous_angle = angle(reference,p)
    front = reference[:,0] >= 0
    if neural and not np.any(~front):
        front = p[:,0] > p[:,0].min()
    pushed = False
    stiffness = np.array([np.mean([C.STIFFNESS[o[2]] for o in group]) for group in owners])
    # Precompute sine/cosine coefficients so no spring loop occurs in integration.
    sin_coef = np.array([np.mean([np.cos(phases[r,c]) if active else 0.0
                                  for r,c,_,active in group]) for group in owners])
    cos_coef = np.array([np.mean([np.sin(phases[r,c]) if active else 0.0
                                  for r,c,_,active in group]) for group in owners])
    amplitude = C.AMPLITUDE if actuation_enabled else 0.0
    stride = max(1, round(1 / (C.FPS * C.DT)))
    frames = [p.copy()] if record else []
    if diagnostics is not None and track_contact:
        min_y = np.empty(steps + 1)
        min_y[0] = (p[:,1]-surface_at(p[:,0])[0]).min()
    for step in range(steps):
        t = step * C.DT
        surface, _ = surface_at(p[:,0]) if terrain != 'flat' else (0.0, 0.0)
        if neural:
            if step % C.CONTROL_INTERVAL == 0:
                inputs, previous_angle = sensors(reference,p,v,surface,front,previous_angle,t,omega)
                output = neural_output(params,inputs)
            modulation = np.sum(owner_matrix * output[None,:], axis=1)
        else:
            modulation = sin_coef*np.sin(omega*t) + cos_coef*np.cos(omega*t)
        target = rest * (1 + amplitude*modulation)
        delta = p[b] - p[a]
        length = np.sqrt(np.sum(delta*delta, axis=1))
        direction = delta / np.maximum(length[:,None], 1e-12)
        speed = np.sum((v[b]-v[a])*direction, axis=1)
        # Dissipate axial motion in springs incident on a contacting node.
        # Equal/opposite forces remove elastic energy without sticking feet to
        # the floor or adding a downward adhesive ground force.
        if terrain == 'flat':
            touching = ((p[a,1] <= C.CONTACT_TOLERANCE)
                        | (p[b,1] <= C.CONTACT_TOLERANCE))
        else:
            touching = ((p[a,1] <= surface[a] + C.CONTACT_TOLERANCE)
                        | (p[b,1] <= surface[b] + C.CONTACT_TOLERANCE))
        damping = C.SPRING_DAMPING + C.CONTACT_SPRING_DAMPING * touching
        force = (stiffness*(length-target) + damping*speed)[:,None]*direction
        # bincount accumulates equal-and-opposite forces at shared nodes.
        acc = np.empty_like(p)
        for axis in (0, 1):
            acc[:,axis] = (np.bincount(a, weights=force[:,axis], minlength=len(p))
                          - np.bincount(b, weights=force[:,axis], minlength=len(p))) / C.MASS
        acc[:,1] -= C.GRAVITY
        if push and not pushed and step >= round(push_time/C.DT):
            v[:,0] -= push_magnitude
            pushed = True
        v += C.DT * acc
        p += C.DT * v
        if terrain == 'flat':
            contact = p[:,1] < 0
            normal_dv = np.maximum(-v[contact,1], 0)
            p[contact,1] = 0
            v[contact,1] = np.maximum(v[contact,1], 0)
            vx = v[contact,0]
            v[contact,0] = np.sign(vx)*np.maximum(np.abs(vx)-C.FRICTION*normal_dv, 0)
        else:
            heights, slopes = surface_at(p[:,0])
            contact = p[:,1] < heights
            p[contact,1] = heights[contact]
            slopes = slopes[contact]
            normal = np.column_stack([-slopes,np.ones(len(slopes))])
            normal /= np.sqrt(1+slopes*slopes)[:,None]
            tangent = np.column_stack([normal[:,1],-normal[:,0]])
            normal_dv = np.maximum(-np.sum(v[contact]*normal,axis=1),0)
            velocity = v[contact]+normal_dv[:,None]*normal
            vt = np.sum(velocity*tangent,axis=1)
            friction_dv = np.clip(vt,-C.FRICTION*normal_dv,C.FRICTION*normal_dv)
            v[contact] = velocity-friction_dv[:,None]*tangent
        if not np.all(np.isfinite(p)) or np.max(np.abs(p)) > C.MAX_POSITION:
            return (0.0, empty) if record else 0.0
        if (step+1) % C.POSTURE_CHECK_INTERVAL == 0:
            cosine = upright_cosine(reference, p)
            worst_cosine = min(worst_cosine, cosine)
            tilted_time = (tilted_time + C.DT*C.POSTURE_CHECK_INTERVAL
                           if cosine < fall_cosine else 0.0)
            fell = fell or tilted_time >= C.FALL_DURATION - 1e-12
        if diagnostics is not None and track_contact:
            min_y[step+1] = (p[:,1]-surface_at(p[:,0])[0]).min() if terrain != 'flat' else p[:,1].min()
        if record and ((step+1) % stride == 0 or step+1 == steps):
            frames.append(p.copy())
    if diagnostics is not None and track_contact:
        diagnostics.update(time=np.arange(steps+1)*C.DT, min_y=min_y)
    raw_distance = float(p[:,0].mean()-initial_x)
    if diagnostics is not None:
        diagnostics.update(valid=True, stable=True, fell=fell,
                           raw_distance=raw_distance, omega=omega,
                           max_tilt_degrees=float(np.rad2deg(np.arccos(np.clip(worst_cosine,-1,1)))))
    fitness = 0.0 if fell else raw_distance
    return (fitness, np.array(frames)) if record else fitness
