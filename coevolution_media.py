"""Render the Upgrade E race GIF from committed winners (no retraining).

    python coevolution_media.py

Seed 42 is used for both conditions by the same predeclared convention as
Upgrade D, so the example is not chosen by test score.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config as C
from domain_randomization import episode_options, heldout_schedule
from robustness import load_controller
from sim import ground, simulate, voxel_polygons

ASSETS = Path(__file__).parent / 'assets'
ENTRIES = [('Co-evolved sine (seed 42)', ASSETS / 'coevo_winners/coevo_sine_42.npz'),
           ('Co-evolved feedback (seed 42)', ASSETS / 'coevo_winners/coevo_feedback_42.npz')]


def main():
    episode = heldout_schedule()[1]
    records = []
    for label, path in ENTRIES:
        body, genome, _ = load_controller(path)
        diag = {}
        fitness, frames = simulate(body, genome.parameters(), record=True, diagnostics=diag,
                                   **episode_options(episode))
        records.append((label, body, fitness, frames, voxel_polygons(body), diag))
    w, h = 600, 500
    ground_y = h - 55
    max_y = max(r[3][:, :, 1].max() for r in records)
    max_width = max(np.ptp(r[3][:, :, 0], axis=1).max() for r in records)
    scale = min(w / max(10, max_width + 2), (ground_y - 105) / max(7, max_y + .5))
    font, small = ImageFont.load_default(size=18), ImageFont.load_default(size=14)
    images = []
    for frame in range(len(records[0][3]) - 1):
        image = Image.new('RGB', (w * len(records), h), '#fafafa')
        draw = ImageDraw.Draw(image)
        for panel, (label, body, fitness, frames, polygons, diag) in enumerate(records):
            offset, p = panel * w, frames[frame]
            left = p[:, 0].mean() - w / (2 * scale)

            def screen(x, y):
                return offset + (x - left) * scale, ground_y - y * scale
            xs = np.linspace(left, left + w / scale, 250)
            ys, _ = ground(xs, 'rough', episode['terrain_seed'])
            line = [screen(x, y) for x, y in zip(xs, ys)]
            draw.polygon(line + [(offset + w, h), (offset, h)], fill='#e8dfcf')
            draw.line(line, fill='#5e594f', width=2)
            for r, c, ids in polygons:
                draw.polygon([screen(*p[i]) for i in ids], fill=C.COLORS[int(body[r, c])], outline='#333333', width=2)
            draw.text((offset + w / 2, 20), label, font=font, anchor='mt', fill='#193631')
            draw.text((offset + w / 2, 49), f't={frame / C.FPS:.2f}s | eligible {fitness:.2f} m', font=small, anchor='mt', fill='#444444')
            draw.text((offset + w / 2, 73), f'raw {diag["raw_distance"]:.2f} m | ' + ('tilt-disqualified' if diag['fell'] else 'passes tilt rule'),
                      font=small, anchor='mt', fill='#444444')
            if panel:
                draw.line([(offset, 0), (offset, h)], fill='#cccccc', width=2)
        images.append(image)
    out = ASSETS / 'coevo_race.gif'
    images[0].save(out, save_all=True, append_images=images[1:], duration=40, loop=0, optimize=True)
    print(f'Wrote {out}: {len(images)} frames; held-out episode {episode["id"]}; '
          + '; '.join(f'{r[0]} = {r[2]:.3f} m' for r in records))


if __name__ == '__main__':
    main()
