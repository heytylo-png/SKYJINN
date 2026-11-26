# Embed the UI art (art/ui/*.png) in index.html as UI_ART.
#
#   python3 tools/ui.py
#
# title_bg.png: start-menu background (opaque, lossy). logo.png: title logo. emblem_<faction>.png: faction emblems
# (faction picker, campaign stage cards, AI-vs-AI HUD). wish_<faction>.png / wish_shield.png: wish button icons.
import base64, io, json, os, re
from PIL import Image

SRC, HTML = 'art/ui', 'index.html'

def enc(path, lossy=False, maxw=None, alpha_lossy=False):
    im = Image.open(path); im = im.convert('RGB') if lossy else im.convert('RGBA')
    if maxw and im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    if lossy: im.save(b, 'WEBP', quality=82, method=6)
    elif alpha_lossy: im.save(b, 'WEBP', quality=88, alpha_quality=100, method=6)
    else: im.save(b, 'WEBP', lossless=True, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()

def main():
    out = {'bg': enc(os.path.join(SRC, 'title_bg.png'), lossy=True), 'logo': enc(os.path.join(SRC, 'logo.png'), maxw=720, alpha_lossy=True), 'emblem': {}, 'wish': {}}
    for f in sorted(os.listdir(SRC)):
        m = re.match(r'(emblem|wish)_(\w+)\.png$', f)
        if m: out[m.group(1)][m.group(2)] = enc(os.path.join(SRC, f))
    s = open(HTML).read(); js = 'const UI_ART=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const UI_ART=' in s: s = re.sub(r'const UI_ART=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const TOWER_DATA=', js + 'const TOWER_DATA=', 1)
    open(HTML, 'w').write(s)
    print('emblems', sorted(out['emblem']), '| wishes', sorted(out['wish']), '|', len(js) // 1024, 'KB ->', HTML)

if __name__ == '__main__':
    main()
