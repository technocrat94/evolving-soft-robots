"""Reproducible body-and-controller evolution with spawn-safe worker functions.

Run `python evolve.py --small` before the full `python evolve.py` experiment.
Each candidate is evaluated from rest under exactly the same physics settings.
"""
import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import multiprocessing as mp
import os
from pathlib import Path
from time import perf_counter
import numpy as np
import config as C
from sim import is_valid, simulate
from visualize import animate


@dataclass
class Genome:
    body: np.ndarray
    phases: np.ndarray
    omega: float

    def copy(self):
        return Genome(self.body.copy(), self.phases.copy(), self.omega)

    def controller(self):
        return {'phases': self.phases, 'omega': self.omega}


def random_genome(rng):
    shape = (C.MAX_BODY_SIZE, C.MAX_BODY_SIZE)
    for _ in range(C.MAX_INITIALIZATION_ATTEMPTS):
        body = rng.choice(5, size=shape, p=C.INITIAL_MATERIAL_PROBABILITIES)
        if is_valid(body):
            return Genome(body, rng.uniform(0, 2*np.pi, shape),
                          float(rng.uniform(C.OMEGA_MIN, C.OMEGA_MAX)))
    raise RuntimeError('Could not initialize a valid body; check material probabilities')


def mutate(genome, rng):
    """Return a new genome; parents and elites are never modified in place."""
    child = genome.copy()
    mask = rng.random(child.body.shape) < C.MUTATION_RATE
    child.body[mask] = rng.integers(0, 5, np.count_nonzero(mask))
    child.phases = (child.phases + rng.normal(0, C.PHASE_MUTATION_STD,
                                             child.phases.shape)) % (2*np.pi)
    child.omega = float(np.clip(child.omega + rng.normal(0, C.OMEGA_MUTATION_STD),
                               C.OMEGA_MIN, C.OMEGA_MAX))
    return child


def crossover(first, second, rng):
    """Copy a contiguous row/column block and its phases from the second parent."""
    child = first.copy()
    axis = int(rng.integers(0, 2))
    start = int(rng.integers(0, child.body.shape[axis]))
    stop = int(rng.integers(start+1, child.body.shape[axis]+1))
    region = (slice(start, stop), slice(None)) if axis == 0 else (slice(None), slice(start,stop))
    child.body[region] = second.body[region]
    child.phases[region] = second.phases[region]
    child.omega = first.omega if rng.random() < 0.5 else second.omega
    return child


def tournament(population, fitness, rng):
    contestants = rng.integers(0, len(population), size=C.TOURNAMENT_SIZE)
    return population[int(contestants[np.argmax(fitness[contestants])])]


def next_generation(population, fitness, rng):
    order = np.argsort(-fitness, kind='stable')
    elite_count = max(1, int(len(population)*C.ELITE_FRACTION))
    children = [population[i].copy() for i in order[:elite_count]]
    while len(children) < len(population):
        first = tournament(population, fitness, rng)
        for _ in range(C.MAX_CHILD_RETRIES):
            second = tournament(population, fitness, rng)
            child = mutate(crossover(first, second, rng), rng)
            if is_valid(child.body):
                break
        else:
            # Bounded retry fallback: preserve a valid parent's body, still
            # mutate its controller. Never insert a disconnected candidate.
            child = mutate(first, rng)
            child.body = first.body.copy()
        children.append(child)
    return children


def evaluate(genome):
    """Top-level, picklable Pool worker; no random draws or rendering here."""
    diagnostics = {}
    fitness = simulate(genome.body, genome.controller(), diagnostics=diagnostics)
    return (fitness, diagnostics['raw_distance'], diagnostics['fell'],
            diagnostics['stable'], diagnostics.get('max_tilt_degrees', 0.0))


def save_genome(path, genome, fitness, evaluation):
    np.savez_compressed(path, body=genome.body, phases=genome.phases,
                        omega=genome.omega, fitness=fitness,
                        raw_distance=evaluation[1], fell=evaluation[2],
                        stable=evaluation[3], max_tilt_degrees=evaluation[4])


def load_genome(path):
    with np.load(path, allow_pickle=False) as data:
        return Genome(data['body'].copy(), data['phases'].copy(), float(data['omega']))


def new_run_directory(root):
    stamp = datetime.now(timezone(timedelta(hours=C.RUN_UTC_OFFSET_HOURS))).strftime('%Y%m%d_%H%M')
    root.mkdir(parents=True, exist_ok=True)
    for suffix in range(10000):
        path = root / (f'run_{stamp}' + (f'_{suffix:02d}' if suffix else ''))
        try:
            path.mkdir()  # Never overwrite or delete a previous experiment.
            return path
        except FileExistsError:
            continue
    raise RuntimeError('Too many runs with the same timestamp')


def available_cpu_count():
    """Respect CPU affinity on Linux; use all reported cores on macOS/Windows."""
    if hasattr(os, 'process_cpu_count'):
        return os.process_cpu_count() or 1
    if hasattr(os, 'sched_getaffinity'):
        return len(os.sched_getaffinity(0))
    return os.cpu_count() or 1


def audit_genome(genome):
    """Save active/passive controls as measurements, not a changed objective."""
    active, passive = {}, {}
    fitness = simulate(genome.body, genome.controller(), diagnostics=active)
    simulate(genome.body, genome.controller(), diagnostics=passive,
             actuation_enabled=False)
    if not active['stable'] or not passive['stable']:
        raise RuntimeError('Final active/passive audit was unstable')
    return {'fitness_m':fitness, 'distance_m':active['raw_distance'],
            'max_tilt_degrees':active['max_tilt_degrees'],
            'grounded_percentage':float(100*np.mean(active['min_y'][1:] <= C.CONTACT_TOLERANCE)),
            'fell':active['fell'], 'omega_rad_s':genome.omega,
            'actuation_disabled_distance_m':passive['raw_distance'],
            'actuation_disabled_max_tilt_degrees':passive['max_tilt_degrees'],
            'actuation_disabled_fell':passive['fell'],
            'sim_seconds':C.SIM_SECONDS}


def run(population_size, generations, seed, workers, results_root):
    workers = available_cpu_count() if workers is None else workers
    if population_size < 2 or generations < 1 or workers < 1:
        raise ValueError('Need population >=2, generations >=1, workers >=1')
    start = perf_counter()
    rng = np.random.default_rng(seed)
    population = [random_genome(rng) for _ in range(population_size)]
    folder = new_run_directory(Path(results_root))
    settings = {key: value for key, value in vars(C).items() if key.isupper()}
    settings.update(POPULATION_SIZE=population_size, GENERATIONS=generations,
                    RANDOM_SEED=seed, WORKERS=workers)
    (folder/'config_snapshot.json').write_text(json.dumps(settings, indent=2)+'\n', encoding='utf-8')
    print(f'results={folder} workers={workers} population={population_size} generations={generations}', flush=True)
    history = []
    # spawn works on Windows/macOS/Linux. Ordering from Pool.map is deterministic.
    with mp.get_context('spawn').Pool(workers) as pool, \
            (folder/'fitness_history.csv').open('w', newline='', encoding='utf-8') as log, \
            (folder/'evaluation_details.csv').open('w', newline='', encoding='utf-8') as details:
        writer = csv.writer(log)
        writer.writerow(['generation', 'best', 'average', 'tilt_disqualified'])
        detail_writer = csv.writer(details)
        detail_writer.writerow(['generation','candidate','fitness','raw_distance','fell',
                                'stable','max_tilt_degrees','omega'])
        for generation in range(1, generations+1):
            gen_start = perf_counter()
            evaluations = pool.map(evaluate, population)
            fitness = np.array([e[0] for e in evaluations])
            best_index = int(np.argmax(fitness))
            best = population[best_index]
            best_fitness, average = float(fitness[best_index]), float(fitness.mean())
            fallen = sum(e[2] for e in evaluations)
            writer.writerow([generation,best_fitness,average,fallen])
            log.flush()
            for index, (genome, evaluation) in enumerate(zip(population, evaluations)):
                detail_writer.writerow([generation,index,*evaluation,genome.omega])
            details.flush()
            save_genome(folder/f'best_gen_{generation}.npz', best, best_fitness, evaluations[best_index])
            if generation % C.PREVIEW_INTERVAL == 0:
                animate(best.body, best.controller(), folder/f'preview_gen_{generation}.gif')
            elapsed = perf_counter()-gen_start
            fallen = sum(e[2] for e in evaluations)
            unstable = sum(not e[3] for e in evaluations)
            history.append({'generation':generation,'best':best_fitness,'average':average,
                            'seconds':elapsed,'fallen':fallen,'unstable':unstable})
            print(f'gen={generation:02d} best={best_fitness:.6f} average={average:.6f} '
                  f'seconds={elapsed:.3f} fallen={fallen} unstable={unstable} '
                  f'best_omega={best.omega:.4f}', flush=True)
            if generation < generations:
                population = next_generation(population, fitness, rng)
    final_audit = audit_genome(best)
    (folder/'final_best_metrics.json').write_text(json.dumps(final_audit,indent=2)+'\n', encoding='utf-8')
    with (folder/'final_best_metrics.csv').open('w', newline='', encoding='utf-8') as metrics_file:
        metrics_writer = csv.DictWriter(metrics_file, fieldnames=list(final_audit))
        metrics_writer.writeheader()
        metrics_writer.writerow(final_audit)
    total = perf_counter()-start
    summary = {'total_seconds':total, 'seed':seed, 'population':population_size,
               'generations':generations, 'workers':workers, 'history':history, 'final_best_metrics':final_audit}
    (folder/'run_summary.json').write_text(json.dumps(summary,indent=2)+'\n', encoding='utf-8')
    print(f'total_seconds={total:.3f}', flush=True)
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--small', action='store_true', help='10 candidates, 5 generations')
    parser.add_argument('--seed', type=int, default=C.RANDOM_SEED)
    parser.add_argument('--workers', type=int, default=C.WORKERS)
    parser.add_argument('--results', type=Path, default=Path(__file__).parent/'results')
    args = parser.parse_args()
    run(C.SMALL_POPULATION_SIZE if args.small else C.POPULATION_SIZE,
        C.SMALL_GENERATIONS if args.small else C.GENERATIONS,
        args.seed, args.workers, args.results)


if __name__ == '__main__':
    mp.freeze_support()
    main()
