# Soften art that is cut off at a frame edge in cleaned sprite sheets (transparent, square frames).
#
#   python3 tools/declip.py art/sheets/src/djinn_*.png        (edits the files in place)
#
# Where a frame's art touches its cell edge (a lance tip, a lightning bolt, a puff of smoke cut by the frame), the
# alpha fades to zero over RAMP px towards that edge, only along the stretch of edge the art touches. The hard
# straight cut becomes a soft trail-off. Edges the idle pose already touches (the unit's body is wider or taller
# than the frame) are left alone, so solid parts never fade. Small detached pieces against the edge (art spilled over from the
# neighbouring frame) are removed first. Frames that don't touch an edge are left untouched, so running it twice
# changes nothing more.
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

RAMP, REACH = 12, 10       # fade length into the frame; how far along the edge each touching pixel reaches
EDGE = 3                   # art within this many px of the frame edge counts as cut off

def strays(a):
    """Remove small pieces that are detached from the sprite and sit against the frame edge: art from the
    neighbouring frame that spilled across the cell boundary (e.g. the next horse's tail)."""
    F = a.shape[0]; lab, n = ndimage.label(ndimage.binary_dilation(a > 0.12, iterations=2))
    if n < 2: return a, 0
    sz = ndimage.sum(a > 0.12, lab, range(1, n + 1)); main = sz.max(); gone = 0
    for i, o in enumerate(ndimage.find_objects(lab)):
        near = o[0].start < EDGE or o[1].start < EDGE or o[1].stop > F - EDGE
        if near and sz[i] < main * 0.04 and sz[i] < 220:
            a = np.where(lab == i + 1, 0, a); gone += 1
    return a, gone

def soften(a, skip=()):
    """a: float alpha 0..1 of one frame. Returns new alpha and which edges were touched."""
    F = a.shape[0]; out = a.copy(); hit = []
    ramp = np.clip(np.arange(F) / RAMP, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)   # smoothstep from the edge inward
    # the bottom edge is the ground line (feet and shadows stand on it by design), so only top, left and right are softened
    for name, line in (('top', a[:EDGE].max(0)), ('left', a[:, :EDGE].max(1)), ('right', a[:, -EDGE:].max(1))):
        touch = line > 0.15
        if touch.sum() <= 2 or name in skip: continue
        hit.append(name)
        band = ndimage.gaussian_filter1d(ndimage.binary_dilation(touch, iterations=REACH).astype(float), REACH / 2)
        band = np.clip(band * 1.5, 0, 1)
        if name == 'top': m = 1 - band[None, :] * (1 - ramp[:, None])
        elif name == 'bottom': m = 1 - band[None, :] * (1 - ramp[::-1][:, None])
        elif name == 'left': m = 1 - band[:, None] * (1 - ramp[None, :])
        else: m = 1 - band[:, None] * (1 - ramp[::-1][None, :])
        out *= m
    return out, hit

def main(paths):
    for p in paths:
        im = np.asarray(Image.open(p).convert('RGBA')).copy(); F = im.shape[0] // 4; cols = im.shape[1] // F; fixed = []
        # edges the unit's own body reaches in its idle pose (a wide trebuchet, a tall wing) are part of the drawing,
        # not something cut off: leave those edges alone in every row
        body = set()
        for c in range(cols):
            a0 = im[0:F, c * F:(c + 1) * F, 3] / 255.0
            if a0.any(): body.update(soften(a0)[1])
        for r in range(4):
            for c in range(cols):
                cell = im[r * F:(r + 1) * F, c * F:(c + 1) * F]
                if not cell[..., 3].any(): continue
                a, g = strays(cell[..., 3] / 255.0)
                a, hit = soften(a, body)
                if g: hit = hit + ['%d stray' % g]
                if hit:
                    cell[..., 3] = np.round(a * 255).astype(np.uint8); fixed.append('r%dc%d:%s' % (r, c, '+'.join(hit)))
        if fixed:
            Image.fromarray(im).save(p, optimize=True)
        print('%-36s %s' % (p.split('/')[-1], ' '.join(fixed) or '-'))

if __name__ == '__main__':
    main(sys.argv[1:])
