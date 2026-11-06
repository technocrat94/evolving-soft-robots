"""Independently replay every B winner and validate frozen bodies/checkpoints."""
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from robustness import analyze,load_controller
from sim import simulate


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).parent;assets=root/'assets'
    manifest=json.loads((assets/'robustness_manifest.json').read_text())
    study=args.study
    analyze(study,assets)
    with np.load(assets/'checkpoints/best_gen_60.npz') as saved:fixed=saved['body']
    unstable=fallen=checked=0
    for entry in manifest['runs']:
        folder=study/entry['path'];summary=json.loads((folder/'run_summary.json').read_text())
        unstable+=sum(r['unstable'] for r in summary['history'])
        fallen+=sum(r['tilt_disqualified'] for r in summary['history'])
        for path in folder.glob('best_gen_*.npz'):
            body,controller,score=load_controller(path)
            np.testing.assert_array_equal(body,fixed)
            assert 1<=controller.omega<=6;checked+=1
        body,controller,score=load_controller(folder/'final_best.npz')
        actual=simulate(body,controller.parameters())
        np.testing.assert_allclose(actual,score,rtol=1e-12,atol=1e-12)
    rows=list(csv.DictReader((assets/'robustness_runs.csv').open()))
    assert all(r['stable']=='True' and r['actuation_disabled_stable']=='True' for r in rows)
    validation={'candidate_evaluations':24000,'unstable_evaluations':unstable,
                'tilt_disqualified_evaluations':fallen,'fixed_body_checkpoints_checked':checked,
                'final_training_winners_replayed':10,'active_passive_environment_audits':30}
    (assets/'robustness_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    gif=Image.open(assets/'closed_loop_vs_open_loop.gif')
    sheet=Image.new('RGB',(1240,3*560),'white');draw=ImageDraw.Draw(sheet)
    for i,index in enumerate((0,62,124)):
        gif.seek(index);sheet.paste(gif.convert('RGB'),(0,i*560+30))
        draw.text((10,i*560+8),f'Frame {index}, t={index/25:.2f}s',fill='black')
    (root/'work').mkdir(exist_ok=True);sheet.save(root/'work/b_gif_contact_sheet.png')
    print(json.dumps(validation,indent=2))


if __name__=='__main__':main()
