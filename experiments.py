"""Run Upgrade A or reanalyze its saved matched-seed results; numpy-only inference.

Use python experiments.py; raw results stay in ignored results/experiments/.
The co-evolution condition is A1 and is reused as A2's third condition.
"""
import argparse
import csv
from itertools import product
import json
import multiprocessing as mp
from pathlib import Path
from time import perf_counter
import numpy as np
import config as C
from evolve import run, new_run_directory


def paired_sign_flip(first, second):
    """Exact two-sided test of mean paired differences (all 2**n sign flips).

    Assumes exchangeability of labels within a seed pair under the null, or
    independent symmetric differences about zero. There is no Monte Carlo
    error. With five pairs the minimum two-sided p-value is 2/32 = 0.0625.
    """
    first, second = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if first.ndim != 1 or first.shape != second.shape or len(first) == 0:
        raise ValueError('Require nonempty paired 1D samples of equal size')
    if not np.all(np.isfinite(first)) or not np.all(np.isfinite(second)):
        raise ValueError('Require finite samples')
    difference = first-second
    signs = np.array(list(product((-1,1), repeat=len(difference))))
    null = (signs*difference).mean(axis=1)
    observed = float(difference.mean())
    tolerance = np.finfo(float).eps*max(1.0, abs(observed))*100
    pvalue = float(np.mean(np.abs(null) >= abs(observed)-tolerance))
    return {'mean_paired_difference_m':observed, 'p_value':pvalue,
            'permutations':len(null), 'method':'exact paired two-sided sign-flip test'}


def holm_adjust(pvalues):
    """Holm family-wise adjustment for the two planned comparisons."""
    values = np.asarray(pvalues, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(values)-rank)*values[index])
        adjusted[index] = min(1.0,running)
    return adjusted


def analyze(study, assets):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    study, assets = Path(study), Path(assets)
    manifest = json.loads((study/'manifest.json').read_text())
    assets.mkdir(parents=True,exist_ok=True)
    curves, records = {}, []
    for condition in C.EXPERIMENT_CONDITIONS:
        curves[condition] = []
        for entry in manifest['runs']:
            if entry['condition'] != condition:
                continue
            folder = study/entry['path']
            history = np.genfromtxt(folder/'fitness_history.csv', delimiter=',', names=True)
            audit = json.loads((folder/'final_best_metrics.json').read_text())
            if len(history)!=manifest['generations']:
                raise ValueError('Incomplete experiment')
            curves[condition].append(history['best'])
            summary = json.loads((folder/'run_summary.json').read_text())
            records.append({'condition':condition,'seed':entry['seed'],
                'final_best_m':float(history['best'][-1]), **audit,
                'tilt_disqualified':sum(h['fallen'] for h in summary['history']),
                'unstable_evaluations':sum(h['unstable'] for h in summary['history']),
                'run_seconds':summary['total_seconds']})
        if len(curves[condition])!=len(manifest['seeds']):
            raise ValueError('Missing seed run')
        curves[condition] = np.array(curves[condition])
    statistics = []
    for condition in C.EXPERIMENT_CONDITIONS:
        final = curves[condition][:,-1]
        statistics.append({'condition':condition,'seeds':len(final),
             'mean_m':float(final.mean()),'std_m':float(final.std(ddof=1)),
             'min_m':float(final.min()),'max_m':float(final.max())})
    comparisons = []
    for other in ('body_only','control_only'):
        test = paired_sign_flip(curves['co_evolution'][:,-1],curves[other][:,-1])
        comparisons.append({'comparison':f'co_evolution vs {other}',**test})
    adjusted = holm_adjust([row['p_value'] for row in comparisons])
    for row, adj in zip(comparisons,adjusted):
        row['holm_adjusted_p_value'] = float(adj)
        row['significant_after_holm'] = bool(adj < C.STATISTICAL_ALPHA)
    table = ['| Condition | Final best distance, mean ± sample SD (m) | Seeds |',
             '|---|---:|---:|']
    table += [f'| {s["condition"]} | {s["mean_m"]:.3f} ± {s["std_m"]:.3f} | {s["seeds"]} |' for s in statistics]
    markdown = '\n'.join(table)+'\n'
    for output in (study,assets):
        for name,rows in (('ablation_table.csv',statistics),('ablation_runs.csv',records)):
            with (output/name).open('w',newline='',encoding='utf-8') as file:
                writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n')
                writer.writeheader();writer.writerows(rows)
        (output/'ablation_table.md').write_text(markdown,encoding='utf-8')
        (output/'ablation_statistics.json').write_text(json.dumps(comparisons,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    colors={'co_evolution':'#267896','body_only':'#e2912e','control_only':'#9467a0'}
    generations=np.arange(1,manifest['generations']+1)
    curve_rows=[]
    for condition,values in curves.items():
        mean=values.mean(axis=0);std=values.std(axis=0,ddof=1)
        ax.plot(generations,mean,label=condition,color=colors[condition],linewidth=2.2)
        ax.fill_between(generations,mean-std,mean+std,color=colors[condition],alpha=0.16)
        for gen,m,s in zip(generations,mean,std):
            curve_rows.append({'condition':condition,'generation':int(gen),'mean_m':float(m),'std_m':float(s)})
    ax.set(xlabel='Generation',ylabel='Best eligible rightward COM distance (m)',
           title=f'Body vs controller evolution | {len(manifest["seeds"])} seeds, {manifest["population"]} robots/run')
    ax.text(0.02,0.98,'Mean line; shaded band = ±1 sample SD (not a confidence interval)',
            transform=ax.transAxes,va='top',fontsize=9,color='#555555')
    ax.grid(alpha=0.22);ax.legend(loc='upper left',bbox_to_anchor=(0,0.91))
    for output in (study,assets):
        fig.savefig(output/'ablation_plot.png',dpi=C.PLOT_DPI)
        with (output/'ablation_curves.csv').open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=list(curve_rows[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(curve_rows)
    plt.close(fig)
    print(markdown,flush=True)
    print(json.dumps(comparisons,indent=2),flush=True)
    return statistics, comparisons


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze',type=Path,help='Reanalyze an existing study without simulations')
    parser.add_argument('--assets',type=Path,default=Path(__file__).parent/'assets')
    args=parser.parse_args()
    if args.analyze:
        analyze(args.analyze,args.assets);return
    start=perf_counter()
    study=new_run_directory(Path(__file__).parent/'results/experiments')
    manifest={'seeds':list(C.EXPERIMENT_SEEDS),'conditions':list(C.EXPERIMENT_CONDITIONS),
              'population':C.POPULATION_SIZE,'generations':C.GENERATIONS,'runs':[],
              'band':'mean ±1 sample standard deviation (ddof=1)',
              'statistical_method':'exact paired two-sided mean-difference sign-flip test; Holm adjustment',
              'method_reference':'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html'}
    print(f'STUDY={study}',flush=True)
    for condition in C.EXPERIMENT_CONDITIONS:
        for seed in C.EXPERIMENT_SEEDS:
            print(f'BEGIN condition={condition} seed={seed}',flush=True)
            folder=run(C.POPULATION_SIZE,C.GENERATIONS,seed,C.WORKERS,
                       study/condition/f'seed_{seed}',condition)
            manifest['runs'].append({'condition':condition,'seed':seed,'path':str(folder.relative_to(study))})
            (study/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    manifest['simulations_seconds']=perf_counter()-start
    (study/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    analyze(study,args.assets)
    manifest['total_seconds']=perf_counter()-start
    (study/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (args.assets/'ablation_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'STUDY_TOTAL_SECONDS={manifest["total_seconds"]:.3f}',flush=True)


if __name__=='__main__':
    mp.freeze_support()
    main()
