# Embed normalized unit sheets (from tools/sheets.py) into index.html as SPR_SHEET.
#   python3 tools/embed_sheets.py [out_dir] [html]      (defaults: art/sheets/out index.html)
# Frames are stored as lossy WebP with alpha to keep the game file small.
import base64, io, json, os, re, sys
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else 'art/sheets/out'
HTML = sys.argv[2] if len(sys.argv) > 2 else 'index.html'
man_path = os.path.join(OUT, 'sheets.json')
man = json.load(open(man_path)) if os.path.exists(man_path) else {}
data = {}
for id, e in sorted(man.items()):
    p = os.path.join(OUT, id + '.png')
    if not os.path.exists(p): continue
    b = io.BytesIO(); Image.open(p).convert('RGBA').save(b, 'WEBP', quality=88, alpha_quality=95, method=6)
    data[id] = dict(d='data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), F=e['F'], n=e['n'], ih=e['ih'])
s = open(HTML).read()
js = 'const SPR_SHEET=' + json.dumps(data, separators=(',', ':')) + ';\n'
s, n = re.subn(r'const SPR_SHEET=\{.*?\};\n', lambda _: js, s, count=1, flags=re.S)
assert n == 1, 'SPR_SHEET not found in ' + HTML
open(HTML, 'w').write(s)
print(len(data), 'sheets,', len(js) // 1024, 'KB ->', HTML)
