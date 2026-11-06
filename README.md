[English](README.md) | [繁體中文](README.zh-TW.md)

# Evolving Soft Robots

A Python portfolio project that evolves the **body materials and motion** of voxel robots using a custom 2D mass-spring simulator and a genetic algorithm.

![Generations 1, 30 and 60 moving side by side](assets/comparison.gif)

Built from scratch with **NumPy, Matplotlib and Pillow**—no physics engine. The final robot travels **19.24 m in five simulated seconds**, compared with **1.70 m** for generation 1, using a galloping/hopping gait.

## How it works

### Mass-spring physics

A robot is an integer grid up to 5 × 5. Row zero is the top. Each occupied voxel is a unit square with four corner point masses, four edge springs and two diagonal springs. Adjacent voxels **share corners and edges**; springs are never duplicated. Diagonals resist collapse and shear.

| Value | Material | Behavior |
|---|---|---|
| 0 | Empty | No voxel |
| 1 | Rigid, dark gray | Stiff springs |
| 2 | Soft, light gray | Weaker springs |
| 3 | Horizontal actuator, orange | Horizontal edge rest lengths oscillate |
| 4 | Vertical actuator, light blue | Vertical edge rest lengths oscillate |

For spring endpoints `a` and `b`, let `n` be the unit vector from `a` to `b`, `l` the current length and `L(t)` the target length:

```text
Force on a = [k (l − L(t)) + c ((v_b − v_a) · n)] n
Force on b = −Force on a
Actuator target: L(t) = L0 [1 + A sin(omega t + phase)]
Gravity: F_y = −m g
```

Stiffness and actuator modulation are averaged across the owners of a shared edge. Only matching horizontal or vertical edges actuate; diagonals do not. Each unique node has the same mass, rather than accumulating mass for each adjoining voxel.

Integration uses **semi-implicit Euler**:

```text
v_next = v + dt F / m
x_next = x + dt v_next
```

Defaults are `dt = 0.002 s`, `m = 0.1 kg`, gravity `9.81 m/s²`, and actuator amplitude `A = 0.2`. Each voxel is **1 m × 1 m in model units**; these are illustrative parameters, not a calibrated physical robot.

The floor is `y = 0`. Penetrating nodes are projected onto it, downward velocity is removed, and horizontal velocity is reduced by Coulomb friction:

```text
Normal impulse: Jn = m max(−v_y, 0)
Tangential impulse magnitude ≤ friction_coefficient × Jn
```

Spring damping acts along relative axial velocity. Springs incident on a grounded node receive additional damping to dissipate elastic energy near contact; the forces remain equal and opposite, without adhesive forces. Non-finite or excessive positions stop a simulation and return zero fitness. Spring-force accumulation is vectorized; there is no Python loop over springs inside the integration loop.

### Genetic algorithm

The genome contains a **5 × 5 material grid**, one actuator phase per voxel, and one global angular frequency `omega`. Valid bodies have at least one occupied voxel, four-neighbor connectivity and at least one actuator. Initialization regenerates random grids until valid.

Each generation:

1. Evaluate candidates using `multiprocessing.Pool` with spawn workers.
2. Rank by fitness and copy the top **20% unchanged**.
3. Choose parents by tournament selection.
4. Cross over a contiguous block of rows or columns, including phases.
5. Mutate materials, perturb phases and frequency, and clamp omega to **1–6 rad/s**.
6. Retry invalid children with a bounded retry count and a valid-parent fallback.

Eligible fitness is the **signed rightward center-of-mass displacement**:

```text
fitness = mean(x_final) − mean(x_initial)
```

Negative distances remain negative. Invalid, unstable or tilt-disqualified runs receive zero. The final actuation-disabled control is an audit measurement; it is not subtracted from fitness.

All tunable parameters live in [config.py](config.py). The default full run uses **100 robots, 60 generations, seed 42 and all available CPU cores**. Random draws happen in the parent process, and ordered worker results make scheduling independent of selection. Floating-point differences across platforms or dependency versions can still change an evolutionary trajectory.

## Results

![Best and average fitness, with tilt disqualifications on the secondary axis](assets/fitness_plot.png)

![Body evolution at generations 1, 10, 20, 30, 40, 50 and 60](assets/evolution_timeline.png)

Generation 1 resembles an **unstable-looking arch that shuffles slowly**, although it passes the tilt rule. By generation 30, a **large body with a hooked front leg** has emerged. Generation 60 keeps that overall body plan while refining materials and motion. In this run, evolution first finds a useful body plan, then fine-tunes it; the timeline shows selected best individuals rather than a complete ancestry.

Best fitness plateaus at **14.33 m from generations 30–40**, followed by a breakthrough visible at the generation-45 checkpoint. The complete log places renewed improvement at generation **42**, with a larger jump at **43**. This is a punctuated pattern of improvement—an analogy to **punctuated equilibrium**, not evidence for a biological mechanism.

![Final robot's undeformed body and material legend](assets/best_robot.png)

The final robot uses a **galloping/hopping gait**. Its coordinated actuation alternates support and airborne motion, and omega reaches the allowed upper limit of **6 rad/s**.

| Measurement | Recorded result |
|---|---:|
| Generation 1 best distance | 1.696913 m |
| Generation 30 best distance | 14.325100 m |
| Generation 60 best distance | **19.239387 m** |
| Final maximum sampled tilt | 19.325716° |
| Final time with at least one grounded node | 46.12% |
| Final distance with actuation disabled | 0.078180 m |
| Full-run wall time, including GIFs and final audit | 107.262 s |

Runtime was measured on the development macOS machine with 10 CPU cores and Python 3.12.14; it is not a performance guarantee. Saved scores come from that recorded run; the pinned dependencies provide a tested release environment.

## Validation

- **Tilt rule:** the best-fit rotation of all nodes relative to the starting body is checked every `0.02 s`. More than **30°** of tilt sustained for **0.2 s** disqualifies the run. This discourages falling and sliding; it is a conservative heuristic, not a guarantee against every possible exploit.
- **Actuation-disabled check:** rerun the same final body from the same initial state with actuator amplitude zero. It moves **0.078180 m**, compared with **19.239387 m** actively. The passive distance is raw displacement even if a passive run would fail the tilt rule.
- **Stability:** all **6,000 candidate evaluations** in the full run stayed finite and within the simulator's safety bounds. The tilt rule disqualified **820 evaluations**, including repeated genomes across generations; no evaluation was numerically unstable.
- **Tests:** 12 unit tests cover shared mesh topology, valid bodies, repeatability, ground contact, dense-body stability, frequency bounds, unchanged elites, saved-genome reloads and fall disqualification.

The curated CSV retains each generation's `best`, `average` and `tilt_disqualified` values. Supporting metrics and the original full-run integrity summary are included under `assets/`; large raw results are excluded.

## How to run

Requires **Python 3.10+**. Commands below use `python`; on some macOS/Linux setups use `python3` instead. First clone your repository and enter its directory:

```sh
git clone https://github.com/YOUR_USERNAME/evolving-soft-robots.git
cd evolving-soft-robots
python -m venv .venv
```

Activate the environment on macOS/Linux:

```sh
source .venv/bin/activate
```

Or on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and run tests:

```sh
python -m pip install -r requirements.txt
python -m unittest -v test_sim test_evolve
```

Run the hand-designed demonstration, then the small evolution test:

```sh
python main.py
python evolve.py --small
```

`main.py` saves `preview_step1.gif` and prints distance and physics runtime. `--small` runs 10 robots for five generations without changing the full-run defaults.

Run the full experiment:

```sh
python evolve.py
```

This creates a fresh `results/run_YYYYMMDD_HHMM/` directory (with a suffix on collisions), saves the best genome every generation and a GIF every five generations, and writes fitness history, per-candidate diagnostics, configuration, timing and final active/passive metrics. Timestamps use Taipei time. Existing results are never overwritten. To limit CPU usage or change the seed:

```sh
python evolve.py --workers 4 --seed 42
```

Regenerate the README visuals immediately using the **seven bundled checkpoints**, without rerunning evolution:

```sh
python visualize.py --run assets/checkpoints
```

Or render a new full run by replacing the example timestamp with your newly printed results folder:

```sh
python visualize.py --run results/run_YYYYMMDD_HHMM
```

Visualization expects generations 1, 10, 20, 30, 40, 50 and 60, so a five-generation smoke test is not sufficient. Use the configuration that produced a run: the renderer checks comparison fitness against saved values. The bundled GIF uses 125 frames at 25 FPS with equal scale and duration across all panels.

## Project structure

```text
evolving-soft-robots/
├── config.py               # Physics, evolution and rendering parameters
├── sim.py                  # Shared-node mesh, physics, contact and tilt checks
├── evolve.py               # Genome, selection, mutation, multiprocessing and audit
├── visualize.py            # GIFs, fitness plot, body image and timeline
├── main.py                 # Hand-designed robot demonstration
├── test_sim.py             # Physics and mesh tests
├── test_evolve.py          # Evolution and audit tests
├── assets/                 # README media, curated metrics and validation summaries
│   └── checkpoints/        # Seven best genomes, fitness CSV and configuration
├── README.md               # English documentation
├── README.zh-TW.md         # Traditional Chinese documentation
├── requirements.txt        # Pinned direct dependencies
├── LICENSE                 # MIT
└── .gitignore              # Excludes raw results, caches and local environments
```

`results/` is generated locally and ignored by Git. The small curated checkpoints remain tracked inside `assets/`. No working environment or large experiment folder is bundled.

## Limitations

- **No self-collision:** limbs can slightly pass through the body; ground contact is modeled, robot-to-robot-part contact is not.
- **2D only:** out-of-plane motion, 3D stability and real material behavior are not represented.
- **Frequency bound reached:** omega finishes at **6 rad/s**, suggesting selection pressure toward the allowed limit. It is not evidence that 6 rad/s is a physical optimum.
- **Simplified mechanics:** lumped equal node masses, linear springs, projected contact and fixed-step integration are illustrative approximations. These results do not certify hardware performance.
- **Hopping is allowed:** no minimum ground-contact percentage is enforced. The final winner is airborne for a substantial fraction of time.
- **Validation scope:** direct execution was tested on macOS. Spawn-safe entry points support Windows/Linux usage, but those platforms have not been directly tested.

## What I learned

*Personal reflection placeholders—replace these with your own experience.*

- [ ] Explain what building a mass-spring model taught me about stiffness, damping and timestep stability.
- [ ] Describe how friction, contact and shared mesh topology affected locomotion.
- [ ] Reflect on fitness exploits, passive controls and interpreting evolutionary plateaus.
- [ ] Describe one debugging decision and one design tradeoff I would approach differently.

## Future work

*Choose and expand the directions that interest you.*

- [ ] Add different terrains, slopes and rough surfaces.
- [ ] Evolve jumping or climbing tasks.
- [ ] Compare evolved bodies with topology optimization.
- [ ] Add self-collision and investigate more realistic contact models.
- [ ] Compare multiple seeds and perform timestep-convergence studies.
- [ ] Extend the simulator to 3D.

## License

[MIT](LICENSE).
