"""Independent Upgrade D audit: checkpoint constraints, final batch replay,
held-out seed isolation, episode aggregation and passive checks.
"""
import argparse
import csv
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import numpy as np
import config as C
from controllers import ground,neural_output
from domain_randomization import (ROOT,SEEDS,KINDS,evaluate_batch,heldout_schedule,
                                  test_winner,write_csv,write_json,episode_options)
from evolve import available_cpu_count
from robustness import load_controller


def replay_final(task):
    path,episodes=task;body,genome,score=load_controller(path)
    rows=evaluate_batch((body,genome,episodes))
    actual=np.mean([r[0] for r in rows])
    np.testing.assert_allclose(actual,score,atol=1e-12,rtol=1e-12)
    return actual


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True);args=parser.parse_args()
    study=args.study;assets=ROOT/'assets';manifest=json.loads((study/'manifest.json').read_text())
    with np.load(assets/'checkpoints/best_gen_60.npz') as data:fixed=data['body'].copy()
    checkpoints=0;stable=0;fallen=0;evaluations=0;tasks=[];history=[]
    test_seeds={e.get('terrain_seed',e.get('setting_seed')) for e in heldout_schedule()}-{None}
    training_seeds=set()
    for seed,schedule in manifest['training_schedules'].items():
        assert len(schedule)==40
        for batch in schedule:
            assert len(batch)==4
            training_seeds.update(e['terrain_seed'] for e in batch if 'terrain_seed' in e)
        assert schedule==json.loads((study/'manifest.json').read_text())['training_schedules'][seed]
    assert not test_seeds & training_seeds
    for run in manifest['runs']:
        folder=study/run['path'];batch=manifest['training_schedules'][str(run['seed'])][-1]
        tasks.append((folder/'final_best.npz',batch))
        rows=list(csv.DictReader((folder/'episode_evaluations.csv').open()))
        assert len(rows)==60*40*4
        for row in rows:
            fitness=float(row['fitness_m']);raw=float(row['raw_distance_m']);fell=row['fell']=='True'
            assert fitness==(0 if fell else raw)
            stable+=row['stable']=='True';fallen+=fell;evaluations+=1
        means=np.array([float(row['fitness_m']) for row in rows]).reshape(40,60,4).mean(axis=2)
        for path in folder.glob('best_gen_*.npz'):
            body,genome,saved_fitness=load_controller(path);np.testing.assert_array_equal(body,fixed)
            generation=int(path.stem.split('_')[-1])
            np.testing.assert_allclose(saved_fitness,means[generation-1].max(),atol=1e-12,rtol=1e-12)
            assert 1<=genome.omega<=6 and genome.kind==KINDS[run['condition']]
            if genome.kind!='open_loop':
                assert genome.w1.shape==(8,7)
                assert genome.w2.shape==(np.count_nonzero((body==3)|(body==4)),8)
                assert all(np.isfinite(a).all() for a in (genome.w1,genome.w2,genome.b1,genome.b2))
            checkpoints+=1
        for row in csv.DictReader((folder/'fitness_history.csv').open()):
            history.append({'condition':run['condition'],'seed':run['seed'],**row})
    assert checkpoints==600 and evaluations==144000
    with mp.get_context('spawn').Pool(available_cpu_count()) as pool:
        replay=pool.map(replay_final,tasks)
    heldout=list(csv.DictReader((assets/'domain_randomization_episodes.csv').open()))
    assert len(heldout)==25*21
    assert all(r['stable']=='True' and r['passive_stable']=='True' for r in heldout)
    for r in heldout:
        assert (r['success']=='True')==(float(r['fitness_m'])==float(r['raw_distance_m'])) or (r['success']=='False' and float(r['fitness_m'])==0)
    for row in csv.DictReader((assets/'domain_randomization_table.csv').open()):
        seed_values=[];seed_success=[]
        for seed in SEEDS:
            episodes=[r for r in heldout if r['condition']==row['condition'] and int(r['seed'])==seed and (row['subset']=='all' or r['environment']==row['subset'])]
            seed_values.append(np.mean([float(r['fitness_m']) for r in episodes]))
            seed_success.append(np.mean([r['success']=='True' for r in episodes]))
        np.testing.assert_allclose([np.mean(seed_values),np.std(seed_values,ddof=1),np.mean(seed_success),np.std(seed_success,ddof=1)],
                                   [float(row[k]) for k in ('distance_mean_m','distance_std_m','success_mean','success_std')],rtol=1e-12,atol=1e-12)
    # Passive body is identical across all controller families; independently
    # verify all 21 unique environment/passive outcomes, not 25 duplicates.
    passive=[r for r in heldout if r['condition']=='flat_neural' and int(r['seed'])==42]
    from sim import simulate
    for episode,row in zip(heldout_schedule(),passive):
        diag={};simulate(fixed,actuation_enabled=False,diagnostics=diag,**episode_options(episode))
        np.testing.assert_allclose(diag['raw_distance'],float(row['passive_raw_distance_m']),rtol=1e-12,atol=1e-12)
        assert diag['fell']==(row['passive_fell']=='True') and diag['stable']
    validation={'training_candidate_evaluations':36000,'training_episodes':evaluations,
                'numerically_unstable_training_episodes':evaluations-stable,
                'tilt_disqualified_training_episodes':fallen,'fixed_body_checkpoints':checkpoints,
                'final_batch_winners_replayed':len(replay),'heldout_active_episodes':len(heldout),
                'heldout_passive_episodes':len(heldout),'passive_unique_episodes_independently_replayed':21,
                'training_test_seed_overlap':0,'summary_recomputed_from_episode_rows':True,
                'showcase_body_sha256':hashlib.sha256(fixed.tobytes()).hexdigest()}
    write_json(assets/'domain_randomization_validation.json',validation)
    settings={k:v for k,v in vars(C).items() if k.isupper()}
    settings.update(DOMAIN_POPULATION=60,DOMAIN_GENERATIONS=40,
                    TEST_ROUGH_SEEDS=list(range(2000000,2000010)),
                    TEST_PUSH_SETTING_SEEDS=list(range(3000000,3000010)),
                    TRAINING_SCHEDULE_SEED_SEQUENCE=[314159,'optimizer_seed'])
    write_json(assets/'domain_randomization_settings.json',settings)
    import platform
    import PIL
    import matplotlib
    write_json(assets/'domain_randomization_environment.json',{
        'python':platform.python_version(),'platform':platform.platform(),
        'machine':platform.machine(),'available_cpus':available_cpu_count(),
        'numpy':np.__version__,'matplotlib':matplotlib.__version__,'pillow':PIL.__version__})
    write_csv(assets/'domain_randomization_training_history.csv',history)
    from PIL import Image,ImageDraw
    gif=Image.open(assets/'robust_controller_rough.gif')
    assert gif.n_frames==125
    sheet=Image.new('RGB',(gif.width,3*(gif.height+30)),'white')
    draw=ImageDraw.Draw(sheet)
    for row,frame in enumerate((0,62,124)):
        gif.seek(frame);y=row*(gif.height+30)
        draw.text((12,y+8),f'Frame {frame}, t={frame/25:.2f}s',fill='black')
        sheet.paste(gif.convert('RGB'),(0,y+30))
    (ROOT/'work').mkdir(exist_ok=True)
    sheet.save(ROOT/'work/domain_gif_contact_sheet.png')
    print(json.dumps(validation,indent=2))


if __name__=='__main__':mp.freeze_support();main()
