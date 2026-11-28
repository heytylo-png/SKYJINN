# Embed the Glacial Hydra's extra parts (art/hydra/src/) in index.html as HYDRA_DATA.
#
#   python3 tools/hydra.py
#
# The Hydra's body is an ordinary unit sheet (art/sheets/src/frost_hydra_t1.png). Its three necks and heads are drawn by
# the game on top of it, assembled at the socket ring on its back (drawHydra in index.html):
#   frost_hydra_neck_1/2/3.png  one neck each, a ring at both ends. The left ring joins the body, the right ring the head.
#                               Neck 1 runs flat, 2 rises, 3 rises steeply, so attached together they fan out.
#   frost_hydra_head_closed/half/open.png  the head states (open = firing). The neck stump is at the bottom left.
#   frost_beam_mouth/mid/impact.png  4 frames each in a row (12 fps): the burst at the mouth, the beam body (tiled) and
#                               the ground impact.
# Sources may be transparent or on solid magenta. Each part is stored downscaled by K (the game draws it far smaller
# than the art) with its original size and, for necks, both ring centres in original pixels (found as the dark hole of
# each ring).
import base64, io, json, os, re
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, HTML = 'art/hydra/src', 'index.html'
K_PART, K_BEAM = 0.4, 0.5


def load(name):
    im = Image.open(os.path.join(SRC, name)).convert('RGBA'); a = np.asarray(im).copy()
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    a[(r > 200) & (b > 200) & (g < 90), 3] = 0          # solid magenta, if any, becomes transparent
    return Image.fromarray(a, 'RGBA')


def rings(im):
    """centres of the two ring holes (the largest very dark, solid regions), left one first"""
    a = np.asarray(im).astype(int); dark = (a[..., 3] > 200) & (a[..., :3].max(-1) < 45)
    lab, n = ndimage.label(ndimage.binary_opening(dark, iterations=2)); sz = ndimage.sum(dark, lab, range(1, n + 1))
    c = [ndimage.center_of_mass(lab == i + 1) for i in np.argsort(-sz)[:2]]
    c = sorted([(round(x, 1), round(y, 1)) for y, x in c]); return [list(c[0]), list(c[1])]


def enc(im, k):
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS); b = io.BytesIO()
    im.save(b, 'WEBP', quality=90, alpha_quality=100, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()


def main():
    out = {}
    for i in range(3):
        im = load('frost_hydra_neck_%d.png' % (i + 1)); a, b = rings(im)
        out['neck%d' % i] = dict(d=enc(im, K_PART), w=im.width, h=im.height, k=K_PART, a=a, b=b)
        print('neck%d %dx%d rings %s %s' % (i, im.width, im.height, a, b))
    for n in ('closed', 'half', 'open'):
        im = load('frost_hydra_head_%s.png' % n); out[n] = dict(d=enc(im, K_PART), w=im.width, h=im.height, k=K_PART)
    for n in ('mouth', 'mid', 'impact'):
        im = load('frost_beam_%s.png' % n)
        out['beam_' + n] = dict(d=enc(im, K_BEAM), fw=round(im.width / 4 * K_BEAM), fh=round(im.height * K_BEAM), k=K_BEAM)
    s = open(HTML).read(); js = 'const HYDRA_DATA=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if re.search(r'const HYDRA_DATA=', s): s = re.sub(r'const HYDRA_DATA=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const TOWER_DATA=', js + 'const TOWER_DATA=', 1)
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML)


if __name__ == '__main__':
    main()
