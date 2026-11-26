# Cut effect and ground-decal sheets (4x4 on magenta) and embed them in index.html as FX_DATA / DECAL_DATA.
#
#   python3 tools/fx.py            (reads art/fx/src, writes art/fx/out + index.html)
#
# fx_*.png: each row is one effect, frames left to right. Every frame keeps its position inside its cell, so a
# row plays back exactly as drawn; each row is scaled by one factor to fit FX_MAX px.
# decals_ground.png: 16 still variants (rows: blood, scorch, rubble, bile), each trimmed and fitted to DECAL_W x DECAL_H.
# Pixels drawn semi-transparent over the magenta (fading smoke) are un-mixed back to grey with partial alpha.
import base64, io, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, OUT, HTML = 'art/fx/src', 'art/fx/out', 'index.html'
FX_MAX, DECAL_W, DECAL_H = 112, 96, 56
# per sheet: row name and blending per frame ('add' = additive light, 'normal' = painted over)
A, N = 'add', 'normal'
SHEETS = {
    'fx_explosions': [('explosion', [A, A, A, N]), ('debris', N), ('fire', A), ('smoke', N)],
    'fx_hits_a': [('hit_mutant', N), ('hit_dragon', A), ('hit_undead', A), ('hit_auto', A)],
    'fx_hits_b': [('hit_knight', A), ('hit_verdant', N), ('hit_djinn', N), ('hit_goblin', N)],
    'fx_impacts': [('blood', N), ('spark', A), ('dust', N), ('crystal', A)],
}
DECAL_ROWS = ['blood', 'scorch', 'rubble', 'bile']

def key(im):
    """alpha from the magenta background, un-mixing translucent grey drawn over it"""
    border = np.concatenate([im[:10].reshape(-1, 3), im[-10:].reshape(-1, 3), im[:, :10].reshape(-1, 3), im[:, -10:].reshape(-1, 3)])
    bg = np.median(border, axis=0); d = np.sqrt(((im - bg) ** 2).sum(-1))
    mag = np.minimum(im[..., 0], im[..., 2]) - im[..., 1]
    fg = (d > 60) & ~((mag > 120) & (d < 140)); fg = ndimage.binary_opening(fg, iterations=1)
    lab, n = ndimage.label(fg); sz = ndimage.sum(fg, lab, range(1, n + 1)); fg = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s > 12])
    a = ndimage.gaussian_filter(fg.astype(np.float32), 0.6); a = np.clip((a - 0.12) / 0.7, 0, 1)
    rgb = im.copy()
    # translucent grey over magenta: C = k*F + (1-k)*B with F grey -> k = 1 - magenta-ness/255
    m = np.clip(mag, 0, 255); k = np.clip(1 - m / 255, 0.05, 1)
    F = (im - (1 - k)[..., None] * bg) / k[..., None]
    neutral = (np.abs(F[..., 0] - F[..., 1]) < 40) & (np.abs(F[..., 2] - F[..., 1]) < 40) & (m > 18)
    rgb[neutral] = np.clip(F[neutral], 0, 255); a = np.where(neutral, a * k, a)
    # despill the remaining pink fringe
    sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None) * (a < 0.99) * ~neutral
    rgb[..., 0] -= sp * 0.7; rgb[..., 2] -= sp * 0.7
    return np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), fg

def cells(path):
    """masks per cell: each connected piece goes to the cell its centre falls in"""
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32); rgba, fg = key(im)
    H, W = fg.shape; ch, cw = H / 4, W / 4
    lab, n = ndimage.label(ndimage.binary_dilation(fg, iterations=2))
    out = [[np.zeros_like(fg) for _ in range(4)] for _ in range(4)]
    for i, sl in enumerate(ndimage.find_objects(lab)):
        comp = (lab[sl] == i + 1) & fg[sl]
        if not comp.any(): continue
        ys, xs = np.nonzero(comp); r = min(3, int((ys.mean() + sl[0].start) // ch)); c = min(3, int((xs.mean() + sl[1].start) // cw))
        out[r][c][sl] |= comp
    return rgba, out, ch, cw

def b64(img, q=88):
    b = io.BytesIO(); img.save(b, 'WEBP', quality=q, alpha_quality=95, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()

def fx_sheet(name, rows):
    rgba, cm, ch, cw = cells(os.path.join(SRC, name + '.png')); packed = []; y = 0; meta = []
    for r, (rname, blend) in enumerate(rows):
        # union box of the row in cell-local coordinates, so frames keep their drawn positions
        boxes = []
        for c in range(4):
            m = cm[r][c]; ys, xs = np.nonzero(m)
            if len(ys): boxes.append((ys.min() - r * ch, ys.max() + 1 - r * ch, xs.min() - c * cw, xs.max() + 1 - c * cw))
        if not boxes: continue
        y0, y1 = min(b[0] for b in boxes), max(b[1] for b in boxes); x0, x1 = min(b[2] for b in boxes), max(b[3] for b in boxes)
        bw, bh = x1 - x0, y1 - y0; s = FX_MAX / max(bw, bh); fw, fh = max(1, round(bw * s)), max(1, round(bh * s))
        strip = Image.new('RGBA', (fw * 4, fh), (0, 0, 0, 0)); n = 0
        for c in range(4):
            m = cm[r][c]
            if not m.any(): continue
            keep = ndimage.binary_dilation(m, iterations=2); fr = rgba.copy(); fr[..., 3] = (fr[..., 3] * keep).astype(np.uint8)
            X0, Y0 = int(round(c * cw + x0)), int(round(r * ch + y0))
            crop = Image.fromarray(fr).crop((X0, Y0, X0 + int(round(bw)), Y0 + int(round(bh)))).resize((fw, fh), Image.LANCZOS)
            strip.alpha_composite(crop, (n * fw, 0)); n += 1
        bl = blend if isinstance(blend, list) else [blend] * n
        meta.append(dict(name=rname, y=y, w=fw, h=fh, n=n, blend=bl[:n])); packed.append(strip); y += fh
        print('  %-12s %d frames %dx%d %s' % (rname, n, fw, fh, bl[:n]))
    atlas = Image.new('RGBA', (max(p.width for p in packed), y), (0, 0, 0, 0)); yy = 0
    for p in packed: atlas.alpha_composite(p, (0, yy)); yy += p.height
    atlas.save(os.path.join(OUT, name + '.png'), optimize=True)
    return dict(d=b64(atlas), rows=meta)

def decal_sheet():
    rgba, cm, ch, cw = cells(os.path.join(SRC, 'decals_ground.png'))
    atlas = Image.new('RGBA', (DECAL_W * 4, DECAL_H * 4), (0, 0, 0, 0)); v = []
    for r in range(4):
        for c in range(4):
            m = cm[r][c]; ys, xs = np.nonzero(m)
            if not len(ys): v.append(None); continue
            keep = ndimage.binary_dilation(m, iterations=2); fr = rgba.copy(); fr[..., 3] = (fr[..., 3] * keep).astype(np.uint8)
            crop = Image.fromarray(fr).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
            s = min(DECAL_W / crop.width, DECAL_H / crop.height); w, h = max(1, round(crop.width * s)), max(1, round(crop.height * s))
            x, y = c * DECAL_W + (DECAL_W - w) // 2, r * DECAL_H + (DECAL_H - h) // 2
            atlas.alpha_composite(crop.resize((w, h), Image.LANCZOS), (x, y)); v.append([x, y, w, h])
    atlas.save(os.path.join(OUT, 'decals_ground.png'), optimize=True)
    groups = {k: [i for i in range(r * 4, r * 4 + 4) if v[i]] for r, k in enumerate(DECAL_ROWS)}
    print('  decals', {k: len(g) for k, g in groups.items()})
    return dict(d=b64(atlas), v=v, groups=groups)

def main():
    os.makedirs(OUT, exist_ok=True); fx = {}
    for name, rows in SHEETS.items():
        if os.path.exists(os.path.join(SRC, name + '.png')): print(name); fx[name] = fx_sheet(name, rows)
    dec = decal_sheet() if os.path.exists(os.path.join(SRC, 'decals_ground.png')) else None
    json.dump({'fx': {k: v['rows'] for k, v in fx.items()}, 'decals': dec and {'v': dec['v'], 'groups': dec['groups']}},
              open(os.path.join(OUT, 'fx.json'), 'w'), indent=1)
    s = open(HTML).read()
    js = 'const FX_DATA=' + json.dumps(fx, separators=(',', ':')) + ';\nconst DECAL_DATA=' + json.dumps(dec, separators=(',', ':')) + ';\n'
    s, n = re.subn(r'const FX_DATA=.*?;\nconst DECAL_DATA=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    assert n == 1, 'FX_DATA placeholder not found in ' + HTML
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML)

if __name__ == '__main__':
    main()
