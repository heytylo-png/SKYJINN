# Cut unit sprite sheets into normalized animation frames.
#
#   python3 tools/sheets.py [src_dir] [out_dir]      (defaults: art/sheets/src art/sheets/out)
#
# Input: one PNG per unit per tier, named <faction>_<unit>_t<tier>.png (e.g. mutant_leaper_t1.png,
# mutant_acid_spitter_t2.png). 4 rows x 4 columns on a solid magenta background, all frames facing right:
#   row 1 idle, row 2 walk, row 3 attack (the hit lands on frame 2), row 4 death.
#   Flying units: hover idle, fly, attack, death fall.
# Cells don't have to be even: each sprite is found by where its centre falls in the 4x4 grid, then trimmed.
# Already-cleaned sheets (transparent background, square, 4x4 equal frames with feet bottom-centre) are kept
# as-is: the tool only measures them (idle height, baseline, drawn projectile) and the game scales them.
# Output (magenta sheets): <out_dir>/<key><tier>.png, a 4x4 grid of F x F frames (F=64, champions 128) with every frame
# bottom-centre aligned so the feet sit on one baseline, plus <out_dir>/sheets.json. Embed with
# python3 tools/embed_sheets.py.
import json, os, re, sys, glob
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = sys.argv[1] if len(sys.argv) > 1 else 'art/sheets/src'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'art/sheets/out'
HTML = 'index.html'
FRAME, FRAME_CHAMP, ROWS, COLS = 64, 128, 4, 4
FACTIONS = {'djinn': 'djinn', 'verdant': 'verdant', 'mutant': 'mutant', 'mutants': 'mutant', 'knight': 'knight',
            'knights': 'knight', 'magic_knights': 'knight', 'goblin': 'goblin', 'goblins': 'goblin', 'undead': 'undead',
            'auto': 'auto', 'automaton': 'auto', 'automatons': 'auto', 'dragon': 'dragon', 'dragons': 'dragon'}

def units():
    """unit key, faction, role, name, air flag for every unit, read from the game's TYPES table"""
    s = open(HTML).read(); out = []
    for m in re.finditer(r"\n (\w+):\{fac:'(\w+)',role:'(\w+)'([^\n]*?)name:'([^']+)'([^\n]*)", s):
        out.append(dict(key=m.group(1), fac=m.group(2), role=m.group(3), name=m.group(5), air='air:1' in m.group(4) + m.group(6)))
    return out

def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

def resolve(fname, U):
    m = re.match(r'(.+)_t(\d)\.png$', os.path.basename(fname).lower())
    if not m: return None, None, 'name must end in _t<tier>.png'
    stem, tier = m.group(1), int(m.group(2))
    for fk in sorted(FACTIONS, key=len, reverse=True):
        if stem.startswith(fk + '_'):
            fac, unit = FACTIONS[fk], stem[len(fk) + 1:]; break
    else: return None, None, 'unknown faction prefix'
    cands = [u for u in U if u['fac'] == fac]
    for test in (lambda u: unit == u['key'], lambda u: unit == slug(u['name']),
                 lambda u: unit in slug(u['name']).split('_'), lambda u: slug(u['name']).startswith(unit)):
        hit = [u for u in cands if test(u)]
        if len(hit) == 1: return hit[0], tier, None
        if len(hit) > 1: return None, None, 'ambiguous unit name: ' + ', '.join(u['name'] for u in hit)
    return None, None, 'no %s unit called "%s"' % (fac, unit)

def key_out(im):
    """alpha-key the magenta background; returns RGBA array and the opaque mask"""
    border = np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3), im[:, -12:].reshape(-1, 3)])
    bg = np.median(border, axis=0); d = np.sqrt(((im - bg) ** 2).sum(-1)); mag = np.minimum(im[..., 0], im[..., 2]) - im[..., 1]
    fg = (d > 70) & ~((mag > 110) & (d < 150)); fg = ndimage.binary_opening(fg, iterations=1)
    filled = ndimage.binary_fill_holes(fg); mask = filled & ~((d < 75) | ((mag > 85) & (d < 170)))
    a = ndimage.gaussian_filter(mask.astype(np.float32), 0.7); a = np.clip((a - 0.15) / 0.7, 0, 1)
    rgb = im.copy(); sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None) * (a < 0.99)
    rgb[..., 0] -= sp * 0.7; rgb[..., 2] -= sp * 0.7
    return np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), mask

def cut(path):
    """split a sheet into up to 16 trimmed RGBA frames, keyed [row][col] (None where a cell is empty)"""
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    rgba, mask = key_out(im); H, W = mask.shape; ch, cw = H / ROWS, W / COLS
    lab, n = ndimage.label(ndimage.binary_dilation(mask, iterations=3))
    cell = [[np.zeros_like(mask) for _ in range(COLS)] for _ in range(ROWS)]
    for i, sl in enumerate(ndimage.find_objects(lab)):
        comp = (lab[sl] == i + 1) & mask[sl]
        if comp.sum() < 30: continue                                   # stray specks
        ys, xs = np.nonzero(comp); cy, cx = ys.mean() + sl[0].start, xs.mean() + sl[1].start
        r, c = min(ROWS - 1, int(cy // ch)), min(COLS - 1, int(cx // cw))
        cell[r][c][sl] |= comp
    frames = [[None] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            m = cell[r][c]
            if m.sum() < 60: continue
            ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            keep = ndimage.binary_dilation(m, iterations=2)[y0:y1, x0:x1]
            fr = rgba[y0:y1, x0:x1].copy(); fr[..., 3] = (fr[..., 3] * keep).astype(np.uint8)
            frames[r][c] = fr
    return frames

def anchor_x(fr, air):
    """horizontal anchor: centre of the feet (bottom 12% of opaque pixels) for ground units, bbox centre for fliers"""
    a = fr[..., 3] > 100; h, w = a.shape
    if air or not a.any(): return w / 2
    rows = np.nonzero(a.any(1))[0]; band = a[max(0, rows[-1] - max(2, int(h * 0.12))):rows[-1] + 1]
    xs = np.nonzero(band.any(0))[0]
    return (xs.min() + xs.max() + 1) / 2 if len(xs) else w / 2

def normalize(frames, F, air):
    """one scale for the whole sheet so the unit never changes size; feet on the bottom row, anchor centred"""
    fs = [(r, c, fr, anchor_x(fr, air)) for r, row in enumerate(frames) for c, fr in enumerate(row) if fr is not None]
    s = min((F - 2) / max(2 * max(ax, fr.shape[1] - ax), fr.shape[0]) for _, _, fr, ax in fs)
    atlas = Image.new('RGBA', (F * COLS, F * ROWS), (0, 0, 0, 0)); counts = [0] * ROWS; heights = {}
    for r in range(ROWS):
        col = 0
        for c in range(COLS):
            fr = frames[r][c]
            if fr is None: continue
            ax = anchor_x(fr, air); h, w = fr.shape[:2]
            img = Image.fromarray(fr, 'RGBA').resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
            x = round(F / 2 - ax * s); y = F - 1 - img.height
            atlas.alpha_composite(img, (col * F + max(0, x), r * F + max(0, y)))
            heights.setdefault(r, img.height); col += 1
        counts[r] = col
    return atlas, counts, heights.get(0, F - 2)

def is_clean(path):
    im = Image.open(path)
    if im.mode != 'RGBA' or im.width != im.height or im.width % COLS: return False
    a = np.asarray(im)[..., 3]; w = im.width
    return all(a[y, x] == 0 for y in (0, w - 1) for x in (0, w - 1))

def measure_clean(path, air):
    """keep a cleaned sheet's pixels; measure frame counts, idle height, baseline and any drawn projectile"""
    im = Image.open(path).convert('RGBA'); F = im.width // COLS; al = np.asarray(im)[..., 3] > 40
    cell = lambda r, c: al[r * F:(r + 1) * F, c * F:(c + 1) * F]
    n = [int(sum(cell(r, c).any() for c in range(COLS))) for r in range(ROWS)]
    bots, tops, cxs = [], [], []
    for c in range(n[0]):
        ys, xs = np.nonzero(cell(0, c)); bots.append(ys.max()); tops.append(ys.min())
        band = cell(0, c)[max(0, ys.max() - max(2, F // 8)):ys.max() + 1]; bx = np.nonzero(band.any(0))[0]
        cxs.append((bx.min() + bx.max() + 1) / 2)
    fy = float(np.median(bots)); ax = F / 2  # cleaned sheets are already centred: trust the frame centre
    ih = int(fy - min(tops) + 1)
    # drawn projectile / slash: an attack frame that reaches well past the idle body's front edge
    idle = np.zeros((F, F), bool)
    for c in range(n[0]): idle |= cell(0, c)
    front = np.nonzero(idle.any(0))[0].max(); hit, mz, best = 1, None, 0
    reach = [np.nonzero(cell(2, c).any(0))[0].max() for c in range(n[2])]
    if reach: hit = int(np.argmax(reach))  # no drawn effect: the hit is the frame that reaches furthest forward
    for c in range(n[2]):
        m = cell(2, c).copy(); m[:, :front + 3] = False; k = int(m.sum())
        if k >= 40 and k > best and np.nonzero(cell(2, c).any(0))[0].max() - front >= 8:
            ys, xs = np.nonzero(m); best, hit, mz = k, int(c), [round(float(xs.mean()), 1), round(float(ys.mean()), 1)]
    return im, dict(F=F, n=n, ih=ih, fy=fy, ax=ax, hit=hit, mz=mz)

def main():
    U = units(); os.makedirs(OUT, exist_ok=True)
    man_path = os.path.join(OUT, 'sheets.json'); man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    files = sorted(glob.glob(os.path.join(SRC, '*.png')))
    if not files: print('no sheets in', SRC); return
    bad = 0
    for f in files:
        u, tier, err = resolve(f, U)
        if err: print('SKIP', os.path.basename(f), '-', err); bad += 1; continue
        id = u['key'] + str(tier)
        if is_clean(f):
            atlas, e = measure_clean(f, u['air']); F, n = e['F'], e['n']
            man[id] = dict(src=os.path.basename(f), air=u['air'], clean=True, **e)  # used as-is: no copy in OUT
        else:
            F = FRAME_CHAMP if u['role'] == 'champion' else FRAME
            frames = cut(f); counts = [sum(fr is not None for fr in row) for row in frames]
            if not counts[0]: print('SKIP', os.path.basename(f), '- no idle frames found'); bad += 1; continue
            atlas, n, ih = normalize(frames, F, u['air'])
            atlas.save(os.path.join(OUT, id + '.png'), optimize=True)
            man[id] = dict(src=os.path.basename(f), F=F, n=n, ih=ih, fy=F - 1, ax=F / 2, hit=1, mz=None, air=u['air'])
        warn = '' if n == [4, 4, 4, 4] else '  (frames per row: %s)' % n
        e = man[id]
        print('%-28s -> %s  %s %dpx%s%s%s' % (os.path.basename(f), id, u['name'], F, ' as-is' if e.get('clean') else '',
              '  drawn effect on attack frame %d' % (e['hit'] + 1) if e['mz'] else '', warn))
    txt = json.dumps(man, indent=1, sort_keys=True)  # build fully before writing, so a failure can't leave a broken file
    open(man_path, 'w').write(txt)
    print(len(files) - bad, 'cut,', bad, 'skipped ->', OUT)

if __name__ == '__main__':
    main()
