# Embed the faction towers (art/towers/src/tower_<faction>.png) in index.html as TOWER_DATA.
#
#   python3 tools/towers.py
#
# Each sheet is 512x512: a 2x2 grid of 256x256 states, base bottom-centre.
#   top-left: above 66% HP · top-right: 33-66% · bottom-left: 1-33% · bottom-right: destroyed (0 HP)
# For each state the tool measures the base line and the top of the structure (ignoring translucent smoke), which
# the game uses for the tower's shot origin.
import base64, io, json, os, re, glob
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, HTML, CELL = 'art/towers/src', 'index.html', 256

def structure_top(cell):
    """top of the tower itself: the largest solid piece once the mauve smoke (painted solid) is removed"""
    r, g, b, a = [cell[..., i].astype(int) for i in range(4)]
    smoke = (r - g > 22) & (b - g > 10) & (np.abs(r - b) < 40) & (np.maximum(r, b) < 160)
    solid = ndimage.binary_opening((a > 200) & ~smoke, iterations=2)
    lab, n = ndimage.label(solid)
    if not n: return CELL // 2
    sz = ndimage.sum(solid, lab, range(1, n + 1)); big = lab == (int(np.argmax(sz)) + 1)
    return int(np.nonzero(big.any(1))[0].min())

def main():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, 'tower_*.png'))):
        fac = re.match(r'tower_(\w+)\.png', os.path.basename(f)).group(1)
        im = Image.open(f).convert('RGBA'); a = np.asarray(im); top, bot = [], []
        for q in range(4):
            r, c = divmod(q, 2); cell = a[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
            ys = np.nonzero((cell[..., 3] > 40).any(1))[0]
            bot.append(int(ys.max()) if len(ys) else CELL - 4); top.append(structure_top(cell))
        b = io.BytesIO(); im.save(b, 'WEBP', quality=86, alpha_quality=95, method=6)
        out[fac] = dict(d='data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), top=top, bot=bot)
        print('%-8s tops %s base %s  %d KB' % (fac, top, bot, len(b.getvalue()) // 1024))
    s = open(HTML).read(); js = 'const TOWER_DATA=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const TOWER_DATA=' in s:
        s = re.sub(r'const TOWER_DATA=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else:
        s = s.replace('const BASE_SRC=', js + 'const BASE_SRC=', 1)
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML)

if __name__ == '__main__':
    main()
