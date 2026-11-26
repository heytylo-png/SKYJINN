# Embed the layered battle maps (art/maps/layers/<map>_{sky,mid,ground}.png) in index.html as MAP_LAYERS.
#
#   python3 tools/maps.py
#
# Each map has 3 layers, all 720 px tall: sky (opaque), mid and ground (transparent). Every layer tiles seamlessly
# left to right. The game scales each to the canvas height, tiles it, and scrolls sky/mid/ground at 0.15x/0.45x/1x.
# The old single-image art for these maps is removed from MAP_SRC (other maps keep theirs).
import base64, io, json, os, re
from PIL import Image

SRC, HTML, LAYERS = 'art/maps/layers', 'index.html', ('sky', 'mid', 'ground')

def b64(im, lossless):
    b = io.BytesIO()
    if lossless: im.save(b, 'WEBP', lossless=True, method=6)          # crisp pixel edges on the layers units stand on
    else: im.save(b, 'WEBP', quality=94, method=6)                    # the distant sky: lossy is invisible there
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), len(b.getvalue())

def main():
    maps = sorted({f.rsplit('_', 1)[0] for f in os.listdir(SRC) if f.endswith('.png')})
    out = {}
    for m in maps:
        out[m] = {}
        for L in LAYERS:
            im = Image.open(os.path.join(SRC, '%s_%s.png' % (m, L)))
            im = im.convert('RGB') if L == 'sky' else im.convert('RGBA')
            d, n = b64(im, L != 'sky'); out[m][L] = d
            print('%-8s %-6s %dx%d  %d KB' % (m, L, im.width, im.height, n // 1024))
    s = open(HTML).read(); js = 'const MAP_LAYERS=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const MAP_LAYERS=' in s: s = re.sub(r'const MAP_LAYERS=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const MAP_SRC=', js + 'const MAP_SRC=', 1)
    # drop the old single-image art for maps that now have layers
    m = re.search(r'const MAP_SRC=(\{.*?\});\n', s, re.S); src = json.loads(m.group(1))
    for k in maps: src.pop(k, None)
    s = s[:m.start(1)] + json.dumps(src) + s[m.end(1):]
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML, '| old art kept for:', ', '.join(src) or 'none')

if __name__ == '__main__':
    main()
