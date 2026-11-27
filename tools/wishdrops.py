# Embed the Airstrike bomber and the Meteor Shower meteor (art/wish_fx/drops/) in index.html as DROP_DATA.
#
#   python3 tools/wishdrops.py
#
# Each file is one row of 4 equal frames (played at 12 fps in game), transparent or on solid magenta:
#   goblin_bomber.png  4 x 300x210, faces right (mirrored in game when it flies left)
#   meteor.png         4 x 306x346, falls toward the bottom-right
# Per sheet the tool records the frame size and an anchor in frame pixels:
#   bomber: the centre of the plane (the union of all frames' opaque pixels)
#   meteor: the centre of the dark rock (the hit point), plus the art's flight angle (tail -> rock), so the game can turn
#           the sprite to its real flight direction.
import base64, io, json, math, os, re
from PIL import Image

SRC, HTML = 'art/wish_fx/drops', 'index.html'
SHEETS = {'bomber': 'goblin_bomber.png', 'meteor': 'meteor.png'}


def clean(im):
    """RGBA with solid magenta keyed out."""
    im = im.convert('RGBA'); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and r > 200 and b > 200 and g < 90: px[x, y] = (0, 0, 0, 0)
    return im


def measure(im, n, rock):
    fw, fh = im.width // n, im.height; px = im.load()
    xs = ys = cnt = 0; rx = ry = rc = 0; x0, y0, x1, y1 = fw, fh, -1, -1
    for f in range(n):
        for y in range(fh):
            for x in range(fw):
                r, g, b, a = px[f * fw + x, y]
                if a < 128: continue
                xs += x; ys += y; cnt += 1; x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
                # the meteor's rock: dark, unsaturated pixels (the flames are bright orange/yellow)
                if rock and max(r, g, b) < 110 and max(r, g, b) - min(r, g, b) < 45: rx += x; ry += y; rc += 1
    o = {'fw': fw, 'fh': fh, 'n': n, 'box': [x0, y0, x1, y1]}
    if rock and rc:
        cx, cy = rx / rc, ry / rc; o['ax'], o['ay'] = round(cx, 1), round(cy, 1)
        o['ang'] = round(math.atan2(cy - ys / cnt, cx - xs / cnt), 4)   # from the whole sprite's centre to the rock
    else:
        o['ax'], o['ay'] = round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1)
    return o


def main():
    out = {}
    for key, fn in SHEETS.items():
        im = clean(Image.open(os.path.join(SRC, fn))); o = measure(im, 4, key == 'meteor')
        b = io.BytesIO(); im.save(b, 'WEBP', lossless=True, method=6)
        o['d'] = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(); out[key] = o
        print('%-7s %d frames %dx%d  anchor %s,%s%s  %d KB' % (key, o['n'], o['fw'], o['fh'], o['ax'], o['ay'],
              '  angle %.1f deg' % math.degrees(o['ang']) if 'ang' in o else '', len(b.getvalue()) // 1024))
    s = open(HTML).read(); js = 'const DROP_DATA=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const DROP_DATA=' in s: s = re.sub(r'const DROP_DATA=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const TOWER_DATA=', js + 'const TOWER_DATA=', 1)
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML)


if __name__ == '__main__':
    main()
