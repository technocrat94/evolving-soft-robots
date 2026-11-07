"""Export portable controllers and Python reference scores for the web demo."""
import json
from pathlib import Path
import shutil
import numpy as np
import config as C
from controllers import ROUGH_Y,terrain_profile
from robustness import load_controller
from sim import simulate


def main():
    root=Path(__file__).parent;docs=root/'docs';docs.mkdir(exist_ok=True)
    constants={k:v for k,v in vars(C).items() if k.isupper() and isinstance(v,(float,int,dict))}
    constants['ROUGH_Y']=ROUGH_Y.tolist()
    robots=[]
    for generation in (1,30,60):
        with np.load(root/f'assets/checkpoints/best_gen_{generation}.npz',allow_pickle=False) as data:
            body=data['body'];controller={'kind':'open_loop','omega':float(data['omega']),
                                         'phases':data['phases'].tolist()}
            score=simulate(body,controller)
            robots.append({'id':f'gen{generation}','generation':generation,'body':body.tolist(),
                           'controller':controller,'python_distance_m':score})
    body,genome,_=load_controller(root/'assets/closed_loop_robot.npz')
    controller={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in genome.parameters().items()}
    robots.append({'id':'closed_loop','generation':None,'body':body.tolist(),
                   'controller':controller,'python_distance_m':simulate(body,genome.parameters())})
    demo_terrain=None
    demo_push=None
    if (root/'assets/demo_randomized_neural_feedback.npz').exists():
        from domain_randomization import heldout_schedule,episode_options
        demo_push=episode_options(heldout_schedule()[11])
        demo_terrain={'seed':2000000,'heights':terrain_profile(2000000)[1].tolist()}
        for label in ('flat_neural','randomized_neural_feedback','randomized_sine'):
            body,genome,_=load_controller(root/f'assets/demo_{label}.npz')
            params=genome.parameters()
            controller={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in params.items()}
            references={}
            for environment in ('flat','rough','push'):
                options=demo_push if environment=='push' else {'terrain':environment,'terrain_seed':2000000}
                diag={};fitness=simulate(body,params,diagnostics=diag,**options)
                references[environment]={'distance_m':fitness,'raw_distance_m':diag['raw_distance'],'fell':diag['fell']}
            robots.append({'id':label,'generation':None,'body':body.tolist(),'controller':controller,
                           'python_distance_m':references['flat']['distance_m'],'references':references})
    payload={'schema_version':1,'constants':constants,'robots':robots,
             'demo_body':C.DEMO_BODY,'demo_phases':C.DEMO_PHASES,
             'robustness_terrain':demo_terrain,'robustness_push':demo_push}
    (docs/'robots.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    (docs/'assets').mkdir(exist_ok=True)
    for name in ('fitness_plot.png','ablation_plot.png','robustness_plot.png'):
        shutil.copyfile(root/'assets'/name,docs/'assets'/name)
    if (root/'assets/domain_randomization_plot.png').exists():
        shutil.copyfile(root/'assets/domain_randomization_plot.png',docs/'assets/domain_randomization_plot.png')
    print(f'Exported {len(robots)} robots and result figures.')


if __name__=='__main__':main()
