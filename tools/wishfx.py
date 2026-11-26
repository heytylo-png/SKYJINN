# Embed the faction power effect sheets (art/wish_fx/wish_fx_<name>.png) in index.html as WFX_DATA.
#
#   python3 tools/wishfx.py
#
# Each sheet is 1024x1024: a 4x4 grid of 256x256 frames, read left to right, top to bottom. Frames 1-4 build up,
# 5-12 loop while the power is active, 13-16 fade out; 12 fps in game. The tool measures the drawn extent of the loop
# frames (left, right, bottom) so the game can match the effect's drawn width to the power's area and stand it on the
# ground.
import base64, io, json, os, re, glob
import numpy as np
from PIL import Image

SRC, HTML, CELL = 'art/wish_fx', 'index.html', 256

def main():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, 'wish_fx_*.png'))):
        name = re.match(r'wish_fx_(\w+)\.png', os.path.basename(f)).group(1)
        im = Image.open(f).convert('RGBA'); a = np.asarray(im)[..., 3] > 40
        xs0, xs1, ys1 = [], [], []
        for i in range(4, 12):                     # the loop frames define the effect's footprint
            r, c = divmod(i, 4); cell = a[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
            ys, xs = np.nonzero(cell)
            if len(xs): xs0.append(xs.min()); xs1.append(xs.max() + 1); ys1.append(ys.max() + 1)
        b = io.BytesIO(); im.save(b, 'WEBP', quality=88, alpha_quality=100, method=6)
        out[name] = dict(d='data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(),
                         x0=int(min(xs0)), x1=int(max(xs1)), by=int(max(ys1)))
        print('%-16s drawn x %d-%d, base y %d  %d KB' % (name, out[name]['x0'], out[name]['x1'], out[name]['by'], len(b.getvalue()) // 1024))
    s = open(HTML).read(); js = 'const WFX_DATA=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const WFX_DATA=' in s: s = re.sub(r'const WFX_DATA=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const TOWER_DATA=', js + 'const TOWER_DATA=', 1)
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML)

if __name__ == '__main__':
    main()
