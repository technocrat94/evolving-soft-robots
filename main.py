"""Step 1 demonstration: python main.py (outputs beside this script)."""
from pathlib import Path
from time import perf_counter
import numpy as np
import config as C
from sim import simulate
from visualize import save_animation


def main():
    body = np.array(C.DEMO_BODY, dtype=int)
    controller = {'omega': C.OMEGA, 'phases': np.array(C.DEMO_PHASES)}
    start = perf_counter()
    distance, frames = simulate(body, controller, record=True)
    elapsed = perf_counter()-start
    if not len(frames):
        raise RuntimeError('Demonstration failed stability checks')
    filename = Path(__file__).parent / 'preview_step1.gif'
    save_animation(body, frames, filename, distance)
    print(f'distance_m={distance:.6f} simulation_seconds={elapsed:.4f}')
    print(f'frames={len(frames)} min_y={frames[:,:,1].min():.6f} max_y={frames[:,:,1].max():.6f}')
    print(f'preview={filename.name}')


if __name__ == '__main__':
    main()
