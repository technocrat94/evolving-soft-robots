"""Pillow rendering of deformed voxel polygons with a following camera."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
import config as C
from sim import simulate, voxel_polygons


def save_animation(body, frames, filename, fitness):
    if len(frames) == 0:
        raise ValueError('Cannot animate a failed simulation')
    polygons = voxel_polygons(body)
    width, height = C.IMAGE_SIZE
    scale = width / C.CAMERA_WIDTH
    images = []
    # Omit the endpoint so 125 frames at 25 FPS play for exactly five seconds.
    for index, points in enumerate(frames[:-1] if len(frames) > 1 else frames):
        center = points[:,0].mean()
        left = center - C.CAMERA_WIDTH/2
        ground = height - 60
        def screen(x, y):
            return ((x-left)*scale, ground-y*scale)
        image = Image.new('RGB', (width, height), '#fafafa')
        draw = ImageDraw.Draw(image)
        draw.line([(0,ground), (width,ground)], fill='#555555', width=2)
        for x in range(math.floor(left), math.ceil(left+C.CAMERA_WIDTH)+1):
            sx, sy = screen(x, 0)
            draw.line([(sx,sy), (sx,sy+10)], fill='#555555', width=2)
            draw.text((sx+2,sy+12), str(x), fill='#555555')
        for r, c, ids in polygons:
            draw.polygon([screen(*points[i]) for i in ids], fill=C.COLORS[int(body[r,c])],
                         outline='#333333', width=2)
        draw.text((14,14), f'Soft robot | t = {index/C.FPS:.2f} s | final distance = {fitness:+.3f} m', fill='#222222')
        draw.text((14,34), 'Orange: horizontal actuator   Blue: vertical actuator', fill='#444444')
        images.append(image)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(path, save_all=True, append_images=images[1:], duration=round(1000/C.FPS), loop=0)
    images[0].save(path.with_suffix('.png'))


def animate(body, controller_params, filename):
    """Simulate and save a GIF; return its signed horizontal displacement."""
    fitness, frames = simulate(body, controller_params, record=True)
    save_animation(np.asarray(body), frames, filename, fitness)
    return fitness


def _read_saved(run_dir, generation):
    """Read numeric NPZ fields without importing evolve (avoids circular imports)."""
    with np.load(Path(run_dir)/f'best_gen_{generation}.npz', allow_pickle=False) as data:
        return (data['body'].copy(),
                {'omega': float(data['omega']), 'phases': data['phases'].copy()},
                float(data['fitness']))


def comparison(run_dir, filename):
    """Synchronized, equally scaled following-camera panels from saved winners."""
    from PIL import ImageFont
    entries = []
    for generation in C.COMPARISON_GENERATIONS:
        body, controller, saved_fitness = _read_saved(run_dir, generation)
        fitness, frames = simulate(body, controller, record=True)
        if not len(frames) or not np.isclose(fitness, saved_fitness, rtol=1e-10, atol=1e-10):
            raise ValueError(f'Generation {generation} does not reproduce saved fitness')
        entries.append((generation, body, fitness, frames, voxel_polygons(body)))
    frame_count = len(entries[0][3])
    if any(len(entry[3]) != frame_count for entry in entries):
        raise ValueError('Comparison simulations have unequal lengths')
    width, height = C.COMPARISON_PANEL_SIZE
    ground = height-C.COMPARISON_GROUND_MARGIN
    max_height = max(float(entry[3][:,:,1].max()) for entry in entries)
    max_width = max(float(np.ptp(entry[3][:,:,0], axis=1).max()) for entry in entries)
    # One scale across every panel AND every frame. Include extra vertical and
    # horizontal room for deformations, so auto framing cannot hide growth.
    view_height = max(C.COMPARISON_MIN_VIEW_HEIGHT, max_height+0.6)
    scale = min(width/max(C.CAMERA_WIDTH, max_width+2),
                (ground-C.COMPARISON_HEADER_HEIGHT)/view_height)
    view_width = width/scale
    font = ImageFont.load_default(size=20)
    small = ImageFont.load_default(size=16)
    images = []
    for frame_index in range(frame_count-1):
        image = Image.new('RGB', (width*len(entries), height), '#fafafa')
        draw = ImageDraw.Draw(image)
        for panel_index, (generation, body, fitness, frames, polygons) in enumerate(entries):
            offset = panel_index*width
            points = frames[frame_index]
            center = points[:,0].mean()
            left = center-view_width/2
            def screen(x, y):
                return (offset+(x-left)*scale, ground-y*scale)
            draw.text((offset+width/2, 24),
                      f'Generation {generation}, distance {fitness:.2f} m',
                      font=font, anchor='mt', fill='#222222')
            delta = center-frames[0,:,0].mean()
            draw.text((offset+width/2, 57),
                      f't = {frame_index/C.FPS:.2f} s   |   COM {delta:+.2f} m',
                      font=small, anchor='mt', fill='#555555')
            draw.line([(offset,ground),(offset+width-1,ground)], fill='#555555', width=2)
            for x in range(math.ceil(left), math.floor(left+view_width)+1):
                sx, sy = screen(x, 0)
                if sx-offset < 14 or offset+width-sx < 14:
                    continue  # Keep tick labels within their own panel.
                draw.line([(sx,sy),(sx,sy+8)], fill='#777777', width=1)
                draw.text((sx,sy+14), str(x), font=small, anchor='mt', fill='#666666')
            for r, c, ids in polygons:
                draw.polygon([screen(*points[node]) for node in ids],
                             fill=C.COLORS[int(body[r,c])], outline='#333333', width=2)
            draw.text((offset+width/2,height-12), 'Ground ticks: 1 m', font=small,
                      anchor='ms', fill='#666666')
            if panel_index:
                draw.line([(offset,0),(offset,height)], fill='#dddddd', width=2)
        images.append(image)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(path, save_all=True, append_images=images[1:],
                   duration=round(1000/C.FPS), loop=0)
    return {'generations':list(C.COMPARISON_GENERATIONS),
            'distances_m':[entry[2] for entry in entries],
            'frames':len(images), 'duration_seconds':len(images)/C.FPS,
            'pixels_per_meter':scale, 'max_recorded_height_m':max_height}


def _plot_tools():
    """Import plotting lazily; GIF generation requires only numpy and Pillow."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Patch
    return plt, Rectangle, Patch


def _body_axes(ax, body, rectangle):
    """Draw the undeformed 5x5 design grid with fixed size and orientation."""
    rows, cols = body.shape
    for r in range(rows):
        for c in range(cols):
            material = int(body[r,c])
            ax.add_patch(rectangle((c,rows-1-r), 1, 1,
                         facecolor=C.COLORS[material] if material else '#fafafa',
                         edgecolor='#444444' if material else '#e4e4e4',
                         linewidth=0.9 if material else 0.5))
    ax.set(xlim=(-0.2,C.MAX_BODY_SIZE+0.2), ylim=(-0.2,C.MAX_BODY_SIZE+0.2), aspect='equal')
    ax.axis('off')


def _legend(figure, patch):
    handles = [patch(facecolor=C.COLORS[k], edgecolor='#444444', label=C.MATERIAL_NAMES[k])
               for k in sorted(C.MATERIAL_NAMES)]
    figure.legend(handles=handles, loc='lower center', ncol=4, frameon=False,
                  fontsize=11, bbox_to_anchor=(0.5,0.015))


def fitness_plot(run_dir, filename):
    plt, _, _ = _plot_tools()
    data = np.genfromtxt(Path(run_dir)/'fitness_history.csv', delimiter=',', names=True)
    fig, ax = plt.subplots(figsize=(10,5.6), layout='constrained')
    generations = data['generation']
    ax.plot(generations, data['best'], color='#267896', linewidth=2.4, label='Best fitness')
    ax.plot(generations, data['average'], color='#e2912e', linewidth=2, label='Average fitness')
    ax.set(xlabel='Generation', ylabel='Rightward COM distance (m)',
           title='Evolving soft robots: fitness and tilt disqualifications',
           xlim=(1,int(generations.max())))
    ax.grid(alpha=0.22)
    secondary = ax.twinx()
    secondary.plot(generations, data['tilt_disqualified'], color='#9467a0',
                   linestyle='--', linewidth=1.6, alpha=0.85, label='Tilt disqualified')
    # Counts refer to evaluations out of the whole population, not a percentage.
    import json
    settings = json.loads((Path(run_dir)/'config_snapshot.json').read_text())
    secondary.set(ylabel=f'Tilt-disqualified robots (out of {settings["POPULATION_SIZE"]})',
                  ylim=(0,settings['POPULATION_SIZE']))
    secondary.tick_params(axis='y', colors='#80598b')
    lines = ax.lines+secondary.lines
    ax.legend(lines, [line.get_label() for line in lines], loc='upper left', frameon=True)
    fig.savefig(filename, dpi=C.PLOT_DPI)
    plt.close(fig)


def body_image(run_dir, filename):
    plt, rectangle, patch = _plot_tools()
    generation = C.COMPARISON_GENERATIONS[-1]
    body, controller, fitness = _read_saved(run_dir, generation)
    fig, ax = plt.subplots(figsize=(8,7))
    fig.subplots_adjust(top=0.80, bottom=0.14)
    _body_axes(ax, body, rectangle)
    fig.suptitle(f'Best robot | Generation {generation}', fontsize=21, fontweight='bold', y=0.96)
    fig.text(0.5,0.885,f'{fitness:.2f} m in {C.SIM_SECONDS:g} s  |  '
             f'omega = {controller["omega"]:.2f} rad/s  |  undeformed body',
             ha='center', fontsize=12, color='#555555')
    _legend(fig, patch)
    fig.savefig(filename,dpi=C.PLOT_DPI)
    plt.close(fig)


def evolution_timeline(run_dir, filename):
    plt, rectangle, patch = _plot_tools()
    generations = C.TIMELINE_GENERATIONS
    fig, axes = plt.subplots(1,len(generations), figsize=(21,4.8))
    fig.subplots_adjust(left=0.015,right=0.985,bottom=0.18,top=0.70,wspace=0.16)
    fig.suptitle('How the body evolved', fontsize=23,fontweight='bold',y=0.97)
    fig.text(0.5,0.865,'Best individual at each checkpoint | Same 5 x 5 design grid and scale',
             ha='center',fontsize=13,color='#555555')
    for ax, generation in zip(axes,generations):
        body, _, fitness = _read_saved(run_dir,generation)
        _body_axes(ax,body,rectangle)
        ax.set_title(f'Generation {generation}\n{fitness:.2f} m',fontsize=13,pad=12)
    _legend(fig,patch)
    fig.savefig(filename,dpi=C.PLOT_DPI)
    plt.close(fig)


def main():
    import argparse
    import json
    from time import perf_counter
    parser = argparse.ArgumentParser(description='Generate Step 3 README assets from a saved run')
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--assets',type=Path,default=Path(__file__).parent/'assets')
    args = parser.parse_args()
    args.assets.mkdir(parents=True,exist_ok=True)
    start = perf_counter()
    metadata = comparison(args.run,args.assets/'comparison.gif')
    fitness_plot(args.run,args.assets/'fitness_plot.png')
    body_image(args.run,args.assets/'best_robot.png')
    evolution_timeline(args.run,args.assets/'evolution_timeline.png')
    metadata.update(source_run=args.run.resolve().name,render_seconds=perf_counter()-start)
    (args.assets/'visualization_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metadata,indent=2))
    for name in ('comparison.gif','fitness_plot.png','best_robot.png','evolution_timeline.png'):
        path=args.assets/name
        print(f'{path.name}: {path.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
