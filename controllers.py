"""NumPy sensor-feedback policy, held constant between control updates."""
import numpy as np
import config as C


def angle(reference, positions):
    dot = np.sum(reference * positions)
    cross = np.sum(reference[:,0]*positions[:,1]-reference[:,1]*positions[:,0])
    return float(np.arctan2(cross, dot))


def sensors(reference, positions, velocities, height, front, previous_angle, t, omega):
    tilt = angle(reference, positions)
    delta = np.arctan2(np.sin(tilt-previous_angle), np.cos(tilt-previous_angle))
    angular_velocity = delta/(C.CONTROL_INTERVAL*C.DT)
    contact = positions[:,1] <= height+C.CONTACT_TOLERANCE
    values = np.array([tilt/np.pi, angular_velocity/10,
                       velocities[:,1].mean()/5, float(np.any(contact[front])),
                       float(np.any(contact[~front])), np.sin(omega*t), np.cos(omega*t)])
    return values, tilt


def neural_output(controller, inputs):
    hidden = np.tanh(np.sum(np.asarray(controller['w1'])*inputs[None,:],axis=1)
                     + controller['b1'])
    return np.tanh(np.sum(np.asarray(controller['w2'])*hidden[None,:],axis=1)
                   + controller['b2'])


def terrain_profile():
    x = np.arange(C.ROUGH_START, C.ROUGH_END+C.ROUGH_SPACING/2, C.ROUGH_SPACING)
    heights = np.random.default_rng(C.ROUGH_SEED).uniform(0,C.ROUGH_HEIGHT,len(x))
    return x, heights


ROUGH_X, ROUGH_Y = terrain_profile()


def ground(x, terrain='flat'):
    if terrain == 'flat':
        return np.zeros_like(x), np.zeros_like(x)
    if terrain != 'rough':
        raise ValueError('terrain must be flat or rough')
    index = np.clip(np.searchsorted(ROUGH_X,x,side='right')-1,0,len(ROUGH_X)-2)
    slope = (ROUGH_Y[index+1]-ROUGH_Y[index])/C.ROUGH_SPACING
    height = np.interp(x,ROUGH_X,ROUGH_Y)
    slope = np.where((x<ROUGH_X[0]) | (x>ROUGH_X[-1]),0,slope)
    return height,slope
