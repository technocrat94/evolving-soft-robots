"""Upgrade B: neuroevolution and a matched-seed robustness experiment.

Both controller families use the same fixed showcase body, evaluation budget,
tournament selection, elitism and omega bounds. Training is on flat ground;
rough terrain and a fixed-time backward push are held-out evaluations.
"""
import csv
from dataclasses import dataclass
import json
import multiprocessing as mp
from pathlib import Path
from time import perf_counter

import numpy as np

import config as C
from controllers import ground
from evolve import available_cpu_count, new_run_directory, tournament
from sim import simulate, voxel_polygons


@dataclass
class ControllerGenome:
    kind: str
    omega: float
    phases: np.ndarray | None = None
    w1: np.ndarray | None = None
    b1: np.ndarray | None = None
    w2: np.ndarray | None = None
    b2: np.ndarray | None = None

    def copy(self):
        return ControllerGenome(self.kind, self.omega,
            None if self.phases is None else self.phases.copy(),
            None if self.w1 is None else self.w1.copy(),
            None if self.b1 is None else self.b1.copy(),
            None if self.w2 is None else self.w2.copy(),
            None if self.b2 is None else self.b2.copy())

    def parameters(self):
        if self.kind == 'open_loop':
            return {'kind':self.kind, 'omega':self.omega, 'phases':self.phases}
        return {'kind':self.kind, 'omega':self.omega, 'w1':self.w1, 'b1':self.b1,
                'w2':self.w2, 'b2':self.b2}


def random_controller(kind, body, rng, output_count=None):
    omega = float(rng.uniform(C.OMEGA_MIN, C.OMEGA_MAX))
    if kind == 'open_loop':
        return ControllerGenome(kind, omega, phases=rng.uniform(0,2*np.pi,body.shape))
    if kind not in ('closed_loop', 'neural_clock_only'):
        raise ValueError('kind must be open_loop, closed_loop, or neural_clock_only')
    outputs = (int(np.count_nonzero((body == 3) | (body == 4)))
               if output_count is None else output_count)
    return ControllerGenome(kind, omega,
        w1=rng.normal(0,C.NN_INITIAL_STD,(C.NN_HIDDEN,C.NN_INPUTS)),
        b1=rng.normal(0,C.NN_INITIAL_STD,C.NN_HIDDEN),
        w2=rng.normal(0,C.NN_INITIAL_STD,(outputs,C.NN_HIDDEN)),
        b2=rng.normal(0,C.NN_INITIAL_STD,outputs))


def mutate(genome, rng):
    child = genome.copy()
    child.omega = float(np.clip(child.omega+rng.normal(0,C.OMEGA_MUTATION_STD),
                                C.OMEGA_MIN,C.OMEGA_MAX))
    if child.kind == 'open_loop':
        child.phases = (child.phases+rng.normal(0,C.PHASE_MUTATION_STD,
                                               child.phases.shape)) % (2*np.pi)
    else:
        for array in (child.w1,child.b1,child.w2,child.b2):
            mask = rng.random(array.shape) < C.MUTATION_RATE
            array[mask] += rng.normal(0,C.NN_MUTATION_STD,np.count_nonzero(mask))
    return child


def crossover(first, second, rng):
    child = first.copy()
    child.omega = first.omega if rng.random() < .5 else second.omega
    if child.kind == 'open_loop':
        mask = rng.random(child.phases.shape) < .5
        child.phases[mask] = second.phases[mask]
    else:
        for target, source in zip((child.w1,child.b1,child.w2,child.b2),
                                  (second.w1,second.b1,second.w2,second.b2)):
            mask = rng.random(target.shape) < .5
            target[mask] = source[mask]
    return child


def next_generation(population, fitness, rng):
    order = np.argsort(-fitness,kind='stable')
    elite_count = max(1,int(len(population)*C.ELITE_FRACTION))
    children = [population[i].copy() for i in order[:elite_count]]
    while len(children) < len(population):
        first = tournament(population,fitness,rng)
        second = tournament(population,fitness,rng)
        children.append(mutate(crossover(first,second,rng),rng))
    return children


def evaluate_task(task):
    body, genome = task
    diagnostics = {}
    fitness = simulate(body,genome.parameters(),diagnostics=diagnostics,
                       terrain=C.ROBUSTNESS_TRAINING)
    return fitness, diagnostics['raw_distance'], diagnostics['fell'], diagnostics['stable'], \
           diagnostics.get('max_tilt_degrees',0.0)


def save_controller(path, body, genome, fitness=None):
    values = {'body':body,'kind':np.array(genome.kind),'omega':genome.omega}
    if fitness is not None:
        values['fitness'] = fitness
    if genome.kind == 'open_loop':
        values['phases'] = genome.phases
    else:
        values.update(w1=genome.w1,b1=genome.b1,w2=genome.w2,b2=genome.b2)
    np.savez_compressed(path,**values)


def load_controller(path):
    with np.load(path,allow_pickle=False) as data:
        kind = str(data['kind'])
        genome = (ControllerGenome(kind,float(data['omega']),phases=data['phases'].copy())
                  if kind == 'open_loop' else
                  ControllerGenome(kind,float(data['omega']),w1=data['w1'].copy(),
                      b1=data['b1'].copy(),w2=data['w2'].copy(),b2=data['b2'].copy()))
        return data['body'].copy(),genome,float(data['fitness'])


def run_one(kind, seed, body, root, workers=None):
    workers = available_cpu_count() if workers is None else workers
    folder = new_run_directory(Path(root))
    rng = np.random.default_rng(seed)
    population = [random_controller(kind,body,rng) for _ in range(C.POPULATION_SIZE)]
    start = perf_counter()
    history = []
    with mp.get_context('spawn').Pool(workers) as pool, \
            (folder/'fitness_history.csv').open('w',newline='',encoding='utf-8') as file:
        writer = csv.writer(file,lineterminator='\n')
        writer.writerow(['generation','best','average','tilt_disqualified','unstable'])
        for generation in range(1,C.GENERATIONS+1):
            gen_start = perf_counter()
            evaluations = pool.map(evaluate_task,[(body,g) for g in population])
            fitness = np.array([e[0] for e in evaluations])
            best_index = int(np.argmax(fitness)); best = population[best_index]
            row = {'generation':generation,'best':float(fitness[best_index]),
                   'average':float(fitness.mean()),
                   'tilt_disqualified':sum(e[2] for e in evaluations),
                   'unstable':sum(not e[3] for e in evaluations),
                   'seconds':perf_counter()-gen_start}
            writer.writerow([row[key] for key in ('generation','best','average',
                                                   'tilt_disqualified','unstable')])
            file.flush(); history.append(row)
            save_controller(folder/f'best_gen_{generation}.npz',body,best,row['best'])
            print(f'{kind} seed={seed} gen={generation:02d} best={row["best"]:.6f} '
                  f'avg={row["average"]:.6f} fallen={row["tilt_disqualified"]} '
                  f's={row["seconds"]:.3f}',flush=True)
            if generation < C.GENERATIONS:
                population = next_generation(population,fitness,rng)
    total = perf_counter()-start
    save_controller(folder/'final_best.npz',body,best,history[-1]['best'])
    summary = {'controller':kind,'seed':seed,'population':C.POPULATION_SIZE,
               'generations':C.GENERATIONS,'workers':workers,'training_terrain':C.ROBUSTNESS_TRAINING,
               'total_seconds':total,'history':history}
    (folder/'run_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return folder


def audit(body, genome, terrain='flat', push=False):
    diagnostics = {}; fitness = simulate(body,genome.parameters(),diagnostics=diagnostics,
                                          terrain=terrain,push=push)
    passive = {}; simulate(body,genome.parameters(),diagnostics=passive,
                           terrain=terrain,push=push,actuation_enabled=False)
    return {'fitness_m':fitness,'raw_distance_m':diagnostics['raw_distance'],
            'max_tilt_degrees':diagnostics['max_tilt_degrees'],'fell':diagnostics['fell'],
            'stable':diagnostics['stable'],
            'grounded_percentage':float(100*np.mean(diagnostics['min_y'][1:]<=C.CONTACT_TOLERANCE)),
            'actuation_disabled_raw_distance_m':passive['raw_distance'],
            'actuation_disabled_fell':passive['fell'],
            'actuation_disabled_stable':passive['stable']}


def render_comparison(open_entry, closed_entry, filename):
    from PIL import Image,ImageDraw,ImageFont
    entries=[]
    for label,(body,genome,_) in [('Open-loop sine',open_entry),('Closed-loop neural',closed_entry)]:
        fitness,frames=simulate(body,genome.parameters(),record=True,terrain='rough')
        entries.append((label,body,fitness,frames,voxel_polygons(body)))
    width,height=620,520; ground_y=height-65; scale=63.0
    font=ImageFont.load_default(size=19); small=ImageFont.load_default(size=15)
    images=[]
    for frame_index in range(min(len(e[3]) for e in entries)-1):
        image=Image.new('RGB',(2*width,height),'#fafafa');draw=ImageDraw.Draw(image)
        for panel,(label,body,fitness,frames,polygons) in enumerate(entries):
            offset=panel*width; points=frames[frame_index]; center=points[:,0].mean()
            left=center-width/(2*scale)
            def screen(x,y): return offset+(x-left)*scale,ground_y-y*scale
            samples=np.linspace(left,left+width/scale,240); heights,_=ground(samples,'rough')
            terrain=[screen(float(x),float(y)) for x,y in zip(samples,heights)]
            draw.polygon(terrain+[(offset+width,height),(offset,height)],fill='#e8dfcf')
            draw.line(terrain,fill='#5e594f',width=3)
            for r,c,ids in polygons:
                draw.polygon([screen(*points[i]) for i in ids],fill=C.COLORS[int(body[r,c])],
                             outline='#333333',width=2)
            draw.text((offset+width/2,22),label,font=font,anchor='mt',fill='#222222')
            draw.text((offset+width/2,52),f'rough terrain | t={frame_index/C.FPS:.2f} s | '
                      f'final {fitness:+.2f} m',font=small,anchor='mt',fill='#555555')
            if panel: draw.line([(offset,0),(offset,height)],fill='#d1d1d1',width=2)
        images.append(image)
    path=Path(filename);path.parent.mkdir(parents=True,exist_ok=True)
    images[0].save(path,save_all=True,append_images=images[1:],
                   duration=round(1000/C.FPS),loop=0)
    images[0].save(path.with_suffix('.png'))


def analyze(study, assets):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    study,assets=Path(study),Path(assets);assets.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((study/'manifest.json').read_text())
    environments=(('flat','flat',False),('rough','rough',False),('push','flat',True))
    details=[]; winners={}
    for entry in manifest['runs']:
        body,genome,training_fitness=load_controller(study/entry['path']/'final_best.npz')
        winners[(entry['controller'],entry['seed'])]=(body,genome,training_fitness)
        for name,terrain,push in environments:
            details.append({'controller':entry['controller'],'seed':entry['seed'],
                            'environment':name,'training_best_m':training_fitness,
                            **audit(body,genome,terrain,push)})
    rows=[]
    for kind in ('open_loop','closed_loop'):
        for name,_,_ in environments:
            values=np.array([r['fitness_m'] for r in details if r['controller']==kind and r['environment']==name])
            raw=np.array([r['raw_distance_m'] for r in details if r['controller']==kind and r['environment']==name])
            rows.append({'controller':kind,'environment':name,'seeds':len(values),
                         'mean_distance_m':float(values.mean()),'std_distance_m':float(values.std(ddof=1)),
                         'min_distance_m':float(values.min()),'max_distance_m':float(values.max()),
                         'mean_raw_distance_m':float(raw.mean()),
                         'tilt_disqualified':sum(r['fell'] for r in details if r['controller']==kind and r['environment']==name)})
    for output in (study,assets):
        with (output/'robustness_table.csv').open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
        with (output/'robustness_runs.csv').open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,fieldnames=list(details[0]),lineterminator='\n');writer.writeheader();writer.writerows(details)
    x=np.arange(3);bar_width=.36;fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    colors={'open_loop':'#e2912e','closed_loop':'#267896'}
    for index,kind in enumerate(('open_loop','closed_loop')):
        kind_rows=[r for r in rows if r['controller']==kind]
        mean=[r['mean_distance_m'] for r in kind_rows];std=[r['std_distance_m'] for r in kind_rows]
        ax.bar(x+(index-.5)*bar_width,mean,bar_width,yerr=std,capsize=5,
               label=kind.replace('_',' ').title(),color=colors[kind],alpha=.92)
    ax.axhline(0,color='#555555',linewidth=.8)
    ax.set(xticks=x,xticklabels=['Flat ground','Rough terrain','Backward push'],
           ylabel='Eligible rightward COM distance (m)',
           title='Controller robustness on a fixed evolved body')
    ax.text(.01,.98,'Bars = mean; error bars = ±1 sample SD across five matched seeds',
            transform=ax.transAxes,va='top',fontsize=9,color='#555555')
    ax.grid(axis='y',alpha=.22);ax.legend(loc='upper right')
    for output in (study,assets): fig.savefig(output/'robustness_plot.png',dpi=C.PLOT_DPI)
    plt.close(fig)
    # Predeclared seed 42 provides the qualitative comparison; the exported
    # closed-loop robot is selected only by flat-ground training fitness.
    render_comparison(winners[('open_loop',C.ROBUSTNESS_SEEDS[0])],
                      winners[('closed_loop',C.ROBUSTNESS_SEEDS[0])],
                      assets/'closed_loop_vs_open_loop.gif')
    best_open=max((v for (k,_),v in winners.items() if k=='open_loop'),key=lambda v:v[2])
    best_closed=max((v for (k,_),v in winners.items() if k=='closed_loop'),key=lambda v:v[2])
    save_controller(assets/'open_loop_robot.npz',*best_open[:2],best_open[2])
    save_controller(assets/'closed_loop_robot.npz',*best_closed[:2],best_closed[2])
    (assets/'robustness_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return rows,details


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume-open',type=Path,help='Reuse completed sine runs; rerun all neural seeds')
    args=parser.parse_args()
    showcase=Path(__file__).parent/'assets/checkpoints/best_gen_60.npz'
    with np.load(showcase,allow_pickle=False) as data: body=data['body'].copy()
    start=perf_counter();study=new_run_directory(Path(__file__).parent/'results/experiments/robustness')
    manifest={'seeds':list(C.ROBUSTNESS_SEEDS),'controllers':['open_loop','closed_loop'],
              'population':C.POPULATION_SIZE,'generations':C.GENERATIONS,
              'training_terrain':C.ROBUSTNESS_TRAINING,'runs':[],'runs_total':10,
              'evaluation_design':'train on flat; evaluate frozen winners on flat, rough, and flat plus push'}
    if args.resume_open:
        old=json.loads((args.resume_open/'manifest.json').read_text())
        import shutil
        for entry in old['runs']:
            if entry['controller']=='open_loop':
                target=study/entry['path'];shutil.copytree(args.resume_open/entry['path'],target)
                manifest['runs'].append(entry)
        if len(manifest['runs'])!=5: raise ValueError('Need five complete sine runs')
        manifest['reused_open_loop_source']=str(args.resume_open)
    print(f'STUDY={study}',flush=True)
    for kind in manifest['controllers']:
        for seed in C.ROBUSTNESS_SEEDS:
            if any(e['controller']==kind and e['seed']==seed for e in manifest['runs']):continue
            folder=run_one(kind,seed,body,study/kind/f'seed_{seed}')
            manifest['runs'].append({'controller':kind,'seed':seed,
                                     'path':str(folder.relative_to(study))})
            (study/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    manifest['training_seconds']=perf_counter()-start
    if args.resume_open:
        manifest['training_seconds']+=sum(json.loads((study/e['path']/'run_summary.json').read_text())['total_seconds'] for e in manifest['runs'] if e['controller']=='open_loop')
    (study/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows,_=analyze(study,Path(__file__).parent/'assets')
    manifest['total_seconds']=perf_counter()-start
    if args.resume_open:
        manifest['total_seconds']+=sum(json.loads((study/e['path']/'run_summary.json').read_text())['total_seconds'] for e in manifest['runs'] if e['controller']=='open_loop')
    (study/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (Path(__file__).parent/'assets/robustness_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(rows,indent=2));print(f'TOTAL_SECONDS={manifest["total_seconds"]:.3f}',flush=True)


if __name__=='__main__':
    mp.freeze_support()
    main()
