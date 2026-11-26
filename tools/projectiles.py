# Embed the projectile sheets (art/projectiles/proj_<sheet>.png) in index.html as PROJ_DATA.
#
#   python3 tools/projectiles.py
#
# Each sheet is 256x256: a 4x4 grid of 64x64 cells, one projectile per row, 4 looping frames (12 fps in game),
# all pointing right. Which unit fires which row is PROJ_SPR in index.html.
import base64, io, json, os, re, glob
from PIL import Image

SRC, HTML = 'art/projectiles', 'index.html'

def main():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, 'proj_*.png'))):
        name = re.match(r'proj_(\w+)\.png', os.path.basename(f)).group(1)
        im = Image.open(f).convert('RGBA'); b = io.BytesIO(); im.save(b, 'WEBP', lossless=True, method=6)
        out[name] = 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()
        print('%-9s %dx%d  %d KB' % (name, im.width, im.height, len(b.getvalue()) // 1024))
    s = open(HTML).read(); js = 'const PROJ_DATA=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const PROJ_DATA=' in s: s = re.sub(r'const PROJ_DATA=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const TOWER_DATA=', js + 'const TOWER_DATA=', 1)
    open(HTML, 'w').write(s); print(len(js) // 1024, 'KB ->', HTML)

if __name__ == '__main__':
    main()
