"""Export portable controllers and Python reference scores for the web demo."""
import json
from pathlib import Path
import shutil
import numpy as np
import config as C
from controllers import ROUGH_Y
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
    payload={'schema_version':1,'constants':constants,'robots':robots,
             'demo_body':C.DEMO_BODY,'demo_phases':C.DEMO_PHASES}
    (docs/'robots.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    (docs/'assets').mkdir(exist_ok=True)
    for name in ('fitness_plot.png','ablation_plot.png','robustness_plot.png'):
        shutil.copyfile(root/'assets'/name,docs/'assets'/name)
    print('Exported four robots and three result figures.')


if __name__=='__main__':main()
