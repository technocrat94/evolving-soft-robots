"""Upgrade D: common-random-number training and an untouched 21-episode test set.

Run python domain_randomization.py; --analyze STUDY regenerates held-out outputs.
The test set is never accessed by run_training. All candidates, including elites,
are evaluated anew on the current generation's shared four-episode batch.
"""
import argparse
import csv
import json
import multiprocessing as mp
from pathlib import Path
import shutil
from time import perf_counter
import numpy as np
import config as C
from controllers import ground
from evolve import available_cpu_count,new_run_directory
from experiments import paired_sign_flip,holm_adjust
from robustness import (random_controller,next_generation,save_controller,load_controller)
from sim import simulate,voxel_polygons

SEEDS=(42,43,44,45,46)
CONDITIONS=('sine','neural_feedback','neural_clock_only')
KINDS={'sine':'open_loop','neural_feedback':'closed_loop','neural_clock_only':'neural_clock_only'}
POPULATION=60
GENERATIONS=40
ROOT=Path(__file__).parent


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def training_schedule(seed,generations=GENERATIONS):
    # Disjoint, unique terrain seeds: training [100000, 1000000), test >2000000.
    rng=np.random.default_rng(np.random.SeedSequence([314159,seed]))
    terrain_seeds=rng.choice(900000,2*generations,replace=False)+100000
    result=[]
    for generation in range(generations):
        result.append([{'terrain':'flat'},
            {'terrain':'rough','terrain_seed':int(terrain_seeds[2*generation])},
            {'terrain':'rough','terrain_seed':int(terrain_seeds[2*generation+1])},
            {'terrain':'flat','push':True,'push_time':float(rng.uniform(1.5,3.5)),
             'push_magnitude':float(rng.uniform(.8,2.0))}])
    return result


def heldout_schedule():
    episodes=[{'id':'flat','terrain':'flat'}]
    for i in range(10):
        episodes.append({'id':f'rough_{i+1:02d}','terrain':'rough','terrain_seed':2000000+i})
    for i in range(10):
        seed=3000000+i;rng=np.random.default_rng(seed)
        episodes.append({'id':f'push_{i+1:02d}','terrain':'flat','push':True,
                         'setting_seed':seed,'push_time':float(rng.uniform(1.5,3.5)),
                         'push_magnitude':float(rng.uniform(.8,2.0))})
    return episodes


def episode_options(episode):
    return {k:v for k,v in episode.items() if k not in ('id','setting_seed')}


def evaluate_batch(task):
    body,genome,episodes=task;rows=[]
    for episode in episodes:
        diagnostics={}
        fitness=simulate(body,genome.parameters(),diagnostics=diagnostics,
                         track_contact=False,**episode_options(episode))
        rows.append((fitness,diagnostics['fell'],diagnostics['stable'],diagnostics['raw_distance']))
    return rows


def run_training(condition,seed,body,folder,schedule,pool):
    folder.mkdir(parents=True,exist_ok=False);start=perf_counter()
    # Feedback and clock-only get exactly matching initial weights and GA draws.
    rng=np.random.default_rng(seed)
    population=[random_controller(KINDS[condition],body,rng) for _ in range(POPULATION)]
    history=[]
    with (folder/'episode_evaluations.csv').open('w',newline='') as file:
        writer=csv.writer(file,lineterminator='\n')
        writer.writerow(['generation','candidate','episode','fitness_m','fell','stable','raw_distance_m'])
        for generation,episodes in enumerate(schedule,1):
            tick=perf_counter();evaluations=pool.map(evaluate_batch,[(body,g,episodes) for g in population])
            fitness=np.array([np.mean([e[0] for e in rows]) for rows in evaluations])
            index=int(np.argmax(fitness));best=population[index]
            for candidate,rows in enumerate(evaluations):
                for episode,row in enumerate(rows):writer.writerow([generation,candidate,episode,*row])
            file.flush()
            row={'generation':generation,'best_mean_m':float(fitness[index]),
                 'population_mean_m':float(fitness.mean()),
                 'tilt_disqualified_episodes':sum(e[1] for rows in evaluations for e in rows),
                 'unstable_episodes':sum(not e[2] for rows in evaluations for e in rows),
                 'seconds':perf_counter()-tick}
            history.append(row)
            save_controller(folder/f'best_gen_{generation}.npz',body,best,fitness[index])
            write_csv(folder/'fitness_history.csv',history)
            if generation==1 or generation%5==0:
                print(f'{condition} seed={seed} gen={generation:02d} mean_best={fitness[index]:.6f} '
                      f'fell={row["tilt_disqualified_episodes"]}/240 seconds={row["seconds"]:.2f}',flush=True)
            if generation<GENERATIONS:population=next_generation(population,fitness,rng)
    save_controller(folder/'final_best.npz',body,best,fitness[index])
    write_json(folder/'summary.json',{'condition':condition,'seed':seed,'history':history,
                                     'total_seconds':perf_counter()-start})
    return {'condition':condition,'seed':seed,'path':str(folder),'seconds':perf_counter()-start}


def test_winner(task):
    label,seed,path,episodes=task;body,genome,training_score=load_controller(path);rows=[]
    for episode in episodes:
        options=episode_options(episode);diag={};passive={}
        fitness=simulate(body,genome.parameters(),diagnostics=diag,**options)
        simulate(body,genome.parameters(),diagnostics=passive,actuation_enabled=False,**options)
        rows.append({'condition':label,'seed':seed,'episode':episode['id'],
                     'environment':'rough' if episode['terrain']=='rough' else 'push' if episode.get('push') else 'flat',
                     'fitness_m':fitness,'raw_distance_m':diag['raw_distance'],
                     'success':not diag['fell'],'stable':diag['stable'],
                     'max_tilt_degrees':diag.get('max_tilt_degrees',0),
                     'grounded_percentage':float(100*np.mean(diag['min_y'][1:]<=C.CONTACT_TOLERANCE)),
                     'passive_raw_distance_m':passive['raw_distance'],
                     'passive_fell':passive['fell'],'passive_stable':passive['stable'],
                     'training_fitness_m':training_score})
    return rows


def render_rough(entries,episode,filename):
    from PIL import Image,ImageDraw,ImageFont
    records=[]
    for label,path in entries:
        body,genome,_=load_controller(path);diag={}
        fitness,frames=simulate(body,genome.parameters(),record=True,diagnostics=diag,**episode_options(episode))
        records.append((label,body,fitness,frames,voxel_polygons(body),diag))
    w,h=540,530;ground_y=h-55
    max_y=max(e[3][:,:,1].max() for e in records)
    max_width=max(np.ptp(e[3][:,:,0],axis=1).max() for e in records)
    scale=min(w/max(10,max_width+2),(ground_y-105)/max(7,max_y+.5))
    font=ImageFont.load_default(size=18);small=ImageFont.load_default(size=14);images=[]
    for frame in range(len(records[0][3])-1):
        image=Image.new('RGB',(w*3,h),'#fafafa');draw=ImageDraw.Draw(image)
        for panel,(label,body,fitness,frames,polygons,diag) in enumerate(records):
            offset=panel*w;p=frames[frame];left=p[:,0].mean()-w/(2*scale)
            def screen(x,y):return offset+(x-left)*scale,ground_y-y*scale
            xs=np.linspace(left,left+w/scale,250);ys,_=ground(xs,'rough',episode['terrain_seed'])
            line=[screen(x,y) for x,y in zip(xs,ys)]
            draw.polygon(line+[(offset+w,h),(offset,h)],fill='#e8dfcf');draw.line(line,fill='#5e594f',width=2)
            for r,c,ids in polygons:draw.polygon([screen(*p[i]) for i in ids],fill=C.COLORS[int(body[r,c])],outline='#333333',width=2)
            draw.text((offset+w/2,20),label,font=font,anchor='mt',fill='#193631')
            draw.text((offset+w/2,49),f't={frame/C.FPS:.2f}s | eligible {fitness:.2f} m',font=small,anchor='mt',fill='#444444')
            draw.text((offset+w/2,73),f'raw {diag["raw_distance"]:.2f} m | '+('tilt-disqualified' if diag['fell'] else 'passes tilt rule'),font=small,anchor='mt',fill='#444444')
            if panel:draw.line([(offset,0),(offset,h)],fill='#cccccc',width=2)
        images.append(image)
    images[0].save(filename,save_all=True,append_images=images[1:],duration=40,loop=0)
    images[0].save(Path(filename).with_suffix('.png'))
    return {'episode':episode,'seed':42,'frames':len(images),'pixels_per_meter':scale}


def analyze(study,workers=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    start=perf_counter();study=Path(study);assets=ROOT/'assets'
    manifest=json.loads((study/'manifest.json').read_text());episodes=heldout_schedule()
    training_seeds={e['terrain_seed'] for schedule in manifest['training_schedules'].values() for batch in schedule for e in batch if 'terrain_seed' in e}
    assert not training_seeds.intersection(e.get('terrain_seed') for e in episodes)
    curated=assets/'domain_controllers';curated.mkdir(exist_ok=True)
    tasks=[];lookup={}
    for entry in manifest['runs']:
        label='randomized_'+entry['condition'];seed=entry['seed'];path=study/entry['path']/'final_best.npz'
        shutil.copyfile(path,curated/f'{label}_{seed}.npz');lookup[(label,seed)]=path
        tasks.append((label,seed,path,episodes))
    old=json.loads((assets/'robustness_manifest.json').read_text())
    old_study=ROOT/'results/experiments/robustness/run_20261107_0533'
    for entry in old['runs']:
        label='flat_sine' if entry['controller']=='open_loop' else 'flat_neural'
        seed=entry['seed'];path=old_study/entry['path']/'final_best.npz'
        target=curated/f'{label}_{seed}.npz'
        if path.exists():shutil.copyfile(path,target)
        if not target.exists():raise FileNotFoundError('Upgrade B per-seed winners required: '+str(path))
        lookup[(label,seed)]=target;tasks.append((label,seed,target,episodes))
    with mp.get_context('spawn').Pool(workers or available_cpu_count()) as pool:
        details=[r for batch in pool.map(test_winner,tasks) for r in batch]
    labels=('flat_sine','flat_neural','randomized_sine','randomized_neural_feedback','randomized_neural_clock_only')
    per_seed=[];summary=[]
    for label in labels:
        for subset in ('all','flat','rough','push'):
            for seed in SEEDS:
                rows=[r for r in details if r['condition']==label and r['seed']==seed and (subset=='all' or r['environment']==subset)]
                per_seed.append({'condition':label,'subset':subset,'seed':seed,'episodes':len(rows),
                                 'mean_distance_m':float(np.mean([r['fitness_m'] for r in rows])),
                                 'success_rate':float(np.mean([r['success'] for r in rows]))})
            values=[r for r in per_seed if r['condition']==label and r['subset']==subset]
            distance=np.array([r['mean_distance_m'] for r in values]);success=np.array([r['success_rate'] for r in values])
            summary.append({'condition':label,'subset':subset,'seeds':5,'episodes_per_seed':len(rows),
                            'distance_mean_m':float(distance.mean()),'distance_std_m':float(distance.std(ddof=1)),
                            'success_mean':float(success.mean()),'success_std':float(success.std(ddof=1))})
    tests=[]
    for other in ('randomized_neural_clock_only','randomized_sine'):
        for metric in ('mean_distance_m','success_rate'):
            first=[r[metric] for r in per_seed if r['condition']=='randomized_neural_feedback' and r['subset']=='all']
            second=[r[metric] for r in per_seed if r['condition']==other and r['subset']=='all']
            result=paired_sign_flip(first,second)
            result['mean_paired_difference']=result.pop('mean_paired_difference_m')
            tests.append({'comparison':'randomized_neural_feedback vs '+other,'metric':metric,**result})
    for row,pvalue in zip(tests,holm_adjust([r['p_value'] for r in tests])):
        row['holm_adjusted_p_value']=float(pvalue);row['significant']=bool(pvalue<.05)
    table=['| Controller / training | Held-out distance, mean ± SD (m) | Success, mean ± SD (%) |',
           '|---|---:|---:|']
    for row in summary:
        if row['subset']=='all':table.append(f'| {row["condition"]} | {row["distance_mean_m"]:.3f} ± {row["distance_std_m"]:.3f} | {100*row["success_mean"]:.2f} ± {100*row["success_std"]:.2f} |')
    for output in (study,assets):
        write_csv(output/'domain_randomization_table.csv',summary)
        write_csv(output/'domain_randomization_per_seed.csv',per_seed)
        write_csv(output/'domain_randomization_episodes.csv',details)
        write_json(output/'domain_randomization_statistics.json',tests)
        write_json(output/'domain_randomization_test_set.json',episodes)
        (output/'domain_randomization_table.md').write_text('\n'.join(table)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(15,6),layout='constrained');x=np.arange(3);width=.16
    colors=['#e2912e','#94bdb3','#c66f31','#247d6a','#7f79a8']
    for i,label in enumerate(labels):
        rows=[r for r in summary if r['condition']==label and r['subset'] in ('flat','rough','push')]
        for ax,mean,std,mult in ((axes[0],'distance_mean_m','distance_std_m',1),(axes[1],'success_mean','success_std',100)):
            ax.bar(x+(i-2)*width,[r[mean]*mult for r in rows],width,yerr=[r[std]*mult for r in rows],capsize=3,color=colors[i],label=label.replace('_',' '))
    for ax in axes:ax.set_xticks(x,['Flat','Held-out rough','Held-out push']);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Eligible distance (m)');axes[1].set_ylabel('Success rate (%)')
    axes[1].axhline(100,color='#888888',linewidth=.7,linestyle=':')
    # Leave SD bars untruncated even when their endpoints exceed [0, 100].
    fig.suptitle('Domain randomization and feedback ablation | mean ± sample SD across five seeds')
    handles,legend=axes[0].get_legend_handles_labels();fig.legend(handles,legend,loc='outside lower center',ncol=3,fontsize=9)
    for output in (study,assets):fig.savefig(output/'domain_randomization_plot.png',dpi=C.PLOT_DPI)
    plt.close(fig)
    gif_info=render_rough([('Flat-trained neural',lookup[('flat_neural',42)]),
                          ('Randomized neural feedback',lookup[('randomized_neural_feedback',42)]),
                          ('Randomized sine',lookup[('randomized_sine',42)])],episodes[1],assets/'robust_controller_rough.gif')
    write_json(assets/'domain_randomization_gif.json',gif_info)
    # Seed 42 is predeclared for the demo and GIF, never chosen by test score.
    for label in ('flat_neural','randomized_neural_feedback','randomized_sine'):
        shutil.copyfile(lookup[(label,42)],assets/f'demo_{label}.npz')
    manifest['analysis_seconds']=perf_counter()-start
    write_json(assets/'domain_randomization_manifest.json',manifest)
    print('\n'.join(table),flush=True);print(json.dumps(tests,indent=2),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--analyze',type=Path)
    parser.add_argument('--workers',type=int,default=available_cpu_count());args=parser.parse_args()
    if args.analyze:analyze(args.analyze,args.workers);return
    start=perf_counter();study=new_run_directory(ROOT/'results/experiments/domain_randomization')
    with np.load(ROOT/'assets/checkpoints/best_gen_60.npz') as data:body=data['body'].copy()
    schedules={str(seed):training_schedule(seed) for seed in SEEDS}
    manifest={'seeds':list(SEEDS),'conditions':list(CONDITIONS),'population':POPULATION,
              'generations':GENERATIONS,'workers':args.workers,'training_schedules':schedules,'runs':[],
              'selection':'best of generation 40 on its shared training batch; test set never used for selection',
              'statistics':'paired exact sign-flip; Holm over two comparisons x two primary metrics'}
    write_json(study/'manifest.json',manifest);print(f'STUDY={study}',flush=True)
    with mp.get_context('spawn').Pool(args.workers) as pool:
        for condition in CONDITIONS:
            for seed in SEEDS:
                entry=run_training(condition,seed,body,study/condition/f'seed_{seed}',schedules[str(seed)],pool)
                entry['path']=str(Path(entry['path']).relative_to(study));manifest['runs'].append(entry)
                write_json(study/'manifest.json',manifest)
    manifest['training_seconds']=perf_counter()-start;write_json(study/'manifest.json',manifest)
    analyze(study,args.workers);manifest['total_seconds']=perf_counter()-start
    write_json(study/'manifest.json',manifest);write_json(ROOT/'assets/domain_randomization_manifest.json',manifest)
    print(f'TOTAL_SECONDS={manifest["total_seconds"]:.3f}',flush=True)


if __name__=='__main__':mp.freeze_support();main()
