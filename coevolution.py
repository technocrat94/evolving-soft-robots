"""Upgrade E: body/controller co-evolution using Upgrade D's exact episodes.

Run python coevolution.py; --analyze STUDY rebuilds the small curated outputs.
No rendering of trajectories or changes to the website are involved.
"""
import argparse
from dataclasses import dataclass
import json
import multiprocessing as mp
from pathlib import Path
from time import perf_counter
import numpy as np
import config as C
import evolve
import robustness as R
import domain_randomization as D
from experiments import paired_sign_flip, holm_adjust
from sim import is_valid

ROOT = Path(__file__).parent
SEEDS = tuple(range(42, 48))
CONDITIONS = ('coevo_sine', 'coevo_feedback')


@dataclass
class Candidate:
    body: np.ndarray
    controller: R.ControllerGenome

    def copy(self):
        return Candidate(self.body.copy(), self.controller.copy())


def next_generation(population, fitness, rng):
    order = np.argsort(-fitness, kind='stable')
    children = [population[i].copy() for i in order[:max(1, int(len(population)*C.ELITE_FRACTION))]]
    while len(children) < len(population):
        first = evolve.tournament(population, fitness, rng)
        for _ in range(C.MAX_CHILD_RETRIES):
            second = evolve.tournament(population, fitness, rng)
            # Reuse the original contiguous body crossover and body mutation.
            dummy = np.zeros(first.body.shape)
            crossed = evolve.crossover(evolve.Genome(first.body, dummy, 3),
                                       evolve.Genome(second.body, dummy, 3), rng)
            body = evolve.mutate(crossed, rng, condition='body_only').body
            controller = R.mutate(R.crossover(first.controller, second.controller, rng), rng)
            if is_valid(body):
                child = Candidate(body, controller)
                break
        else:
            child = Candidate(first.body.copy(), R.mutate(first.controller, rng))
        children.append(child)
    return children


def train(condition, seed, study, schedule, pool):
    folder = study/f'{condition}_{seed}'
    folder.mkdir()
    # Identical initial bodies across the paired conditions; independent
    # controller/variation draws avoid coupling morphology to network size.
    body_rng = np.random.default_rng(np.random.SeedSequence([271828, seed]))
    rng = np.random.default_rng(seed)
    kind = 'open_loop' if condition == 'coevo_sine' else 'closed_loop'
    bodies = [evolve.random_genome(body_rng).body for _ in range(D.POPULATION)]
    population = [Candidate(body, R.random_controller(kind, body, rng,
                  output_count=25 if kind == 'closed_loop' else None)) for body in bodies]
    history = []
    start = perf_counter()
    for generation, episodes in enumerate(schedule, 1):
        tick = perf_counter()
        evaluations = pool.map(D.evaluate_batch, [(g.body, g.controller, episodes) for g in population])
        fitness = np.array([np.mean([e[0] for e in rows]) for rows in evaluations])
        index = int(np.argmax(fitness))
        best = population[index]
        history.append({'generation': generation, 'best_mean_m': float(fitness[index]),
                        'population_mean_m': float(fitness.mean()),
                        'tilt_disqualified_episodes': sum(e[1] for rows in evaluations for e in rows),
                        'unstable_episodes': sum(not e[2] for rows in evaluations for e in rows),
                        'seconds': perf_counter()-tick})
        D.write_csv(folder/'fitness_history.csv', history)
        if generation == 1 or generation % 5 == 0:
            print(f'{condition} seed={seed} gen={generation:02d} best={fitness[index]:.4f} '
                  f'fell={history[-1]["tilt_disqualified_episodes"]}/240 s={history[-1]["seconds"]:.2f}', flush=True)
        if generation < D.GENERATIONS:
            population = next_generation(population, fitness, rng)
    R.save_controller(folder/'final_best.npz', best.body, best.controller, fitness[index])
    result = {'condition': condition, 'seed': seed, 'path': folder.name,
              'seconds': perf_counter()-start}
    D.write_json(folder/'summary.json', result)
    return result


def analyze(study, pool):
    import shutil
    assets = ROOT/'assets'
    curated = assets/'coevo_winners'
    curated.mkdir(exist_ok=True)
    manifest = json.loads((study/'manifest.json').read_text())
    training_seeds = {e['terrain_seed'] for schedule in manifest['training_schedules'].values()
                      for batch in schedule for e in batch if 'terrain_seed' in e}
    assert not training_seeds.intersection(e.get('terrain_seed') for e in D.heldout_schedule())
    tasks = []
    for run in manifest['runs']:
        target = curated/f'{run["condition"]}_{run["seed"]}.npz'
        shutil.copyfile(study/run['path']/'final_best.npz', target)
        tasks.append((run['condition'], run['seed'], target, D.heldout_schedule()))
    details = [row for batch in pool.map(D.test_winner, tasks) for row in batch]
    D.write_csv(study/'heldout_episodes.csv', details)
    runs, summary = [], []
    for condition in CONDITIONS:
        for subset in ('all', 'flat', 'rough', 'push'):
            for seed in SEEDS:
                body, _, _ = R.load_controller(curated/f'{condition}_{seed}.npz')
                rows = [r for r in details if r['condition'] == condition and r['seed'] == seed
                        and (subset == 'all' or r['environment'] == subset)]
                runs.append({'condition': condition, 'seed': seed, 'environment': subset,
                             'episodes': len(rows), 'distance_m': float(np.mean([r['fitness_m'] for r in rows])),
                             'success_rate': float(np.mean([r['success'] for r in rows])),
                             'cells': int(np.count_nonzero(body)),
                             'actuators': int(np.count_nonzero((body == 3) | (body == 4))),
                             'passive_distance_m': float(np.mean([r['passive_raw_distance_m'] for r in rows])),
                             'passive_success_rate': float(np.mean([not r['passive_fell'] for r in rows]))})
            group = [r for r in runs if r['condition'] == condition and r['environment'] == subset]
            row = {'condition': condition, 'environment': subset}
            for key in ('distance_m', 'success_rate', 'cells', 'actuators', 'passive_distance_m'):
                values = np.array([r[key] for r in group])
                row[key+'_mean'] = float(values.mean())
                row[key+'_sd'] = float(values.std(ddof=1))
            summary.append(row)
    tests = []
    for metric in ('distance_m', 'success_rate'):
        values = [[r[metric] for r in runs if r['condition'] == condition and r['environment'] == 'all']
                  for condition in CONDITIONS]
        result = paired_sign_flip(values[1], values[0])
        result['mean_paired_difference'] = result.pop('mean_paired_difference_m')
        tests.append({'metric': metric, **result})
    for test, adjusted in zip(tests, holm_adjust([t['p_value'] for t in tests])):
        test['holm_adjusted_p_value'] = float(adjusted)
    unstable = sum(not r['stable'] or not r['passive_stable'] for r in details)
    stats = {'summary': summary, 'paired_tests': tests, 'heldout_unstable_pairs': unstable,
             'seeds': list(SEEDS), 'episodes_per_seed': 21,
             'population': D.POPULATION, 'generations': D.GENERATIONS,
             'training_episodes': len(SEEDS)*len(CONDITIONS)*D.POPULATION*D.GENERATIONS*4,
             'training_tilt_disqualified_episodes': 0, 'training_unstable_episodes': 0,
             'training_test_terrain_seed_overlap': 0,
             'training_seconds': manifest.get('training_seconds'),
             'distance_definition': 'mean eligible signed COM displacement; tilt-disqualified episodes score zero',
             'sd_definition': 'sample SD across six seeds', 'comparison': 'coevo_feedback minus coevo_sine',
             'decisions': ['Seeds 42-47; paired initial random bodies and shared Upgrade D schedules.',
                           'Fixed 25 row-major feedback outputs; inactive cells ignored; legacy actuator-only checkpoints unchanged.',
                           'Best on generation-40 training batch; no held-out winner selection.',
                           'Two-sided exact paired sign-flip tests with raw and Holm-adjusted p-values across the two outcomes.',
                           'Passive checks are measurements, not a post-hoc selection criterion.']}
    import csv
    for run in manifest['runs']:
        with (study/run['path']/'fitness_history.csv').open() as file:
            for row in csv.DictReader(file):
                stats['training_tilt_disqualified_episodes'] += int(row['tilt_disqualified_episodes'])
                stats['training_unstable_episodes'] += int(row['unstable_episodes'])
    D.write_csv(assets/'coevolution_runs.csv', runs)
    D.write_json(assets/'coevolution_statistics.json', stats)
    table = ['| Condition | Environment | Distance (m), mean ± SD | Success (%), mean ± SD | Cells, mean | Actuators, mean |',
             '|---|---|---:|---:|---:|---:|']
    for r in summary:
        table.append(f'| {r["condition"]} | {r["environment"]} | {r["distance_m_mean"]:.3f} ± {r["distance_m_sd"]:.3f} | '
                     f'{100*r["success_rate_mean"]:.2f} ± {100*r["success_rate_sd"]:.2f} | {r["cells_mean"]:.2f} | {r["actuators_mean"]:.2f} |')
    table += ['', 'Exact paired two-sided sign-flip tests (feedback − sine; 6 seed pairs, 64 sign patterns):', '',
              '| Metric | Mean paired difference | Exact p | Holm p (2 outcomes) |', '|---|---:|---:|---:|']
    for t in tests:
        table.append(f'| {t["metric"]} | {t["mean_paired_difference"]:.6f} | {t["p_value"]:.5f} | {t["holm_adjusted_p_value"]:.5f} |')
    table += ['', 'Distances include tilt-disqualified episodes as zero; success means no tilt disqualification. '
              'SD is across seeds, not across episodes. All = 1 flat + 10 rough + 10 push episodes.', '',
              '| Condition | Passive held-out raw distance (m), mean ± SD |', '|---|---:|']
    for r in summary:
        if r['environment'] == 'all':
            table.append(f'| {r["condition"]} | {r["passive_distance_m_mean"]:.3f} ± {r["passive_distance_m_sd"]:.3f} |')
    (assets/'coevolution_table.md').write_text('\n'.join(table)+'\n', encoding='utf-8')
    render_bodies(curated, runs, assets)
    return stats


def render_bodies(curated, runs, assets):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    colors = ['#ffffff'] + [C.COLORS[i] for i in range(1, 5)]
    fig, axes = plt.subplots(2, 6, figsize=(14, 7))
    for row, condition in enumerate(CONDITIONS):
        for column, seed in enumerate(SEEDS):
            body, _, _ = R.load_controller(curated/f'{condition}_{seed}.npz')
            ax = axes[row, column]
            ax.imshow(body, cmap=ListedColormap(colors), norm=BoundaryNorm(np.arange(-.5, 5.5), 5), interpolation='nearest')
            ax.set_xticks(np.arange(-.5, 5, 1), minor=True)
            ax.set_yticks(np.arange(-.5, 5, 1), minor=True)
            ax.grid(which='minor', color='#cccccc', linewidth=.7)
            ax.tick_params(which='both', bottom=False, left=False, labelbottom=False, labelleft=False)
            result = next(r for r in runs if r['condition'] == condition and r['seed'] == seed and r['environment'] == 'all')
            ax.set_title(f'Seed {seed} · {result["distance_m"]:.2f} m', fontsize=10)
            if column == 0:
                ax.set_ylabel(condition, fontsize=11)
    fig.legend(handles=[Patch(facecolor=colors[i], edgecolor='#777777', label=name)
                        for i, name in enumerate(('Empty', 'Rigid', 'Soft', 'Horizontal actuator', 'Vertical actuator'))],
               loc='lower center', ncol=5, frameon=False)
    fig.suptitle('Co-evolved winning bodies · mean held-out eligible distance', fontsize=14)
    fig.tight_layout(rect=(0, .07, 1, .95), h_pad=2.5)
    fig.savefig(assets/'coevo_bodies.png', dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze', type=Path)
    args = parser.parse_args()
    start = perf_counter()
    workers = evolve.available_cpu_count()
    with mp.get_context('spawn').Pool(workers) as pool:
        if args.analyze:
            study = args.analyze
        else:
            study = evolve.new_run_directory(ROOT/'results/experiments/coevolution')
            schedules = {str(seed): D.training_schedule(seed) for seed in SEEDS}
            manifest = {'population': D.POPULATION, 'generations': D.GENERATIONS,
                        'seeds': list(SEEDS), 'workers': workers, 'training_schedules': schedules, 'runs': [],
                        'feedback_outputs': '25 row-major grid cells; inactive-cell outputs ignored',
                        'winner_selection': 'best on generation 40 shared training batch; no held-out selection'}
            D.write_json(study/'manifest.json', manifest)
            print(f'STUDY {study} workers={workers}', flush=True)
            for condition in CONDITIONS:
                for seed in SEEDS:
                    result = train(condition, seed, study, schedules[str(seed)], pool)
                    manifest['runs'].append(result)
                    D.write_json(study/'manifest.json', manifest)
            manifest['training_seconds'] = perf_counter()-start
            D.write_json(study/'manifest.json', manifest)
        analyze(study, pool)
    manifest = json.loads((study/'manifest.json').read_text())
    elapsed = perf_counter()-start
    manifest['analysis_seconds' if args.analyze else 'total_seconds'] = elapsed
    D.write_json(study/'manifest.json', manifest)
    stats_path = ROOT/'assets/coevolution_statistics.json'
    stats = json.loads(stats_path.read_text())
    stats.update(total_seconds=manifest.get('total_seconds'), workers=manifest['workers'])
    D.write_json(stats_path, stats)
    print(f'COMPLETE {study} elapsed_seconds={elapsed:.3f}', flush=True)


if __name__ == '__main__':
    main()
