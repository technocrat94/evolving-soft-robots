"""NumPy sensor-feedback policy, held constant between control updates."""
import numpy as np
import config as C
from functools import lru_cache


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
    if controller.get('kind') == 'neural_clock_only':
        inputs = inputs.copy()
        inputs[:5] = 0.0
    hidden = np.tanh(np.sum(np.asarray(controller['w1'])*inputs[None,:],axis=1)
                     + controller['b1'])
    return np.tanh(np.sum(np.asarray(controller['w2'])*hidden[None,:],axis=1)
                   + controller['b2'])


@lru_cache(maxsize=256)
def terrain_profile(seed=C.ROUGH_SEED):
    x = np.arange(C.ROUGH_START, C.ROUGH_END+C.ROUGH_SPACING/2, C.ROUGH_SPACING)
    heights = np.random.default_rng(seed).uniform(0,C.ROUGH_HEIGHT,len(x))
    return x, heights


ROUGH_X, ROUGH_Y = terrain_profile()


def ground(x, terrain='flat', terrain_seed=C.ROUGH_SEED):
    if terrain == 'flat':
        return np.zeros_like(x), np.zeros_like(x)
    if terrain != 'rough':
        raise ValueError('terrain must be flat or rough')
    profile_x, profile_y = terrain_profile(terrain_seed)
    index = np.clip(np.searchsorted(profile_x,x,side='right')-1,0,len(profile_x)-2)
    slope = (profile_y[index+1]-profile_y[index])/C.ROUGH_SPACING
    height = np.interp(x,profile_x,profile_y)
    slope = np.where((x<profile_x[0]) | (x>profile_x[-1]),0,slope)
    return height,slope
