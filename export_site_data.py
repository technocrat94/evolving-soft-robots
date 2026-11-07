"""Export everything the redesigned web lab needs into docs/lab.json.

Reads committed assets only (checkpoints, CSV logs, JSON summaries), so it can be
re-run on any clone:  python export_site_data.py
"""
import csv
import json
from pathlib import Path

import numpy as np

from sim import simulate
from robustness import load_controller
from domain_randomization import heldout_schedule,episode_options

ROOT = Path(__file__).parent
ASSETS = ROOT / 'assets'


def rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(x)
        return int(v) if v.is_integer() and 'e' not in str(x).lower() and '.' not in str(x) else v
    except (TypeError, ValueError):
        return {'True': True, 'False': False}.get(x, x)


def open_loop(path):
    with np.load(path, allow_pickle=False) as d:
        body = d['body'].astype(int)
        controller = {'kind': 'open_loop', 'omega': float(d['omega']), 'phases': d['phases'].tolist()}
    return body, controller


def main():
    checkpoints = []
    for g in (1, 10, 20, 30, 40, 50, 60):
        body, controller = open_loop(ASSETS / f'checkpoints/best_gen_{g}.npz')
        checkpoints.append({'id': f'gen{g}', 'generation': g, 'body': body.tolist(),
                            'controller': controller,
                            'python_distance_m': float(simulate(body, controller))})

    body, controller = open_loop(ASSETS / 'open_loop_robot.npz')
    sine = {'id': 'sine_best', 'body': body.tolist(), 'controller': controller,
            'python_distance_m': float(simulate(body, controller))}

    history = [{k: num(v) for k, v in r.items()} for r in rows(ASSETS / 'checkpoints/fitness_history.csv')]
    curves = {}
    for r in rows(ASSETS / 'ablation_curves.csv'):
        curves.setdefault(r['condition'], []).append(
            [int(r['generation']), float(r['mean_m']), float(r['std_m'])])

    payload = {
        'schema_version': 1,
        'checkpoints': checkpoints,
        'sine_robustness_robot': sine,
        'showcase_history': history,
        'final_metrics': json.loads((ASSETS / 'final_best_metrics.json').read_text()),
        'ablation': {
            'curves': curves,
            'table': [{k: num(v) for k, v in r.items()} for r in rows(ASSETS / 'ablation_table.csv')],
            'runs': [{k: num(v) for k, v in r.items()} for r in rows(ASSETS / 'ablation_runs.csv')],
            'statistics': json.loads((ASSETS / 'ablation_statistics.json').read_text()),
        },
        'robustness': {
            'table': [{k: num(v) for k, v in r.items()} for r in rows(ASSETS / 'robustness_table.csv')],
            'runs': [{k: num(v) for k, v in r.items()} for r in rows(ASSETS / 'robustness_runs.csv')],
        },
        'js_parity': [{k: num(v) for k, v in r.items()} for r in rows(ASSETS / 'js_parity.csv')],
    }
    controllers={}
    for condition in ('flat_sine','flat_neural','randomized_sine',
                      'randomized_neural_feedback','randomized_neural_clock_only'):
        body,genome,_=load_controller(ASSETS/f'domain_controllers/{condition}_42.npz')
        parameters=genome.parameters()
        references={}
        for environment,episode in [('flat',heldout_schedule()[0]),
                                     ('rough',heldout_schedule()[1]),
                                     ('push',heldout_schedule()[11])]:
            diag={};fitness=simulate(body,parameters,diagnostics=diag,**episode_options(episode))
            references[environment]={'distance_m':fitness,'raw_distance_m':diag['raw_distance'],'fell':diag['fell']}
        controllers[condition]={'id':condition,'body':body.tolist(),
            'controller':{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in parameters.items()},
            'python_distance_m':references['flat']['distance_m'],'references':references,'seed':42}
    payload['domain_randomization']={
        'table':[{k:num(v) for k,v in r.items()} for r in rows(ASSETS/'domain_randomization_table.csv')],
        'per_seed':[{k:num(v) for k,v in r.items()} for r in rows(ASSETS/'domain_randomization_per_seed.csv')],
        'statistics':json.loads((ASSETS/'domain_randomization_statistics.json').read_text()),
        'validation':json.loads((ASSETS/'domain_randomization_validation.json').read_text()),
        'controllers':controllers,'test_set':heldout_schedule(),
        'population':60,'generations':40,'seeds':[42,43,44,45,46]}
    out = ROOT / 'docs' / 'lab.json'
    out.write_text(json.dumps(payload, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Wrote {out} ({out.stat().st_size/1024:.1f} KB): {len(checkpoints)} checkpoints.')


if __name__ == '__main__':
    main()
