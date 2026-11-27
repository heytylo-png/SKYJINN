# Embed the pixel UI kit (art/ui_kit/ui_*.png + ui_kit.json) in index.html as UI_KIT.
#
#   python3 tools/uikit.py
#
# UI_KIT[name] = {d: data URI (lossless WebP), w, h, slice}. At startup each piece becomes a CSS variable
# --k-<name> (url(...)) so the stylesheet can 9-slice it with border-image; the canvas HUD draws bar_hp and
# bar_progress itself.
import base64, io, json, os, re
from PIL import Image

SRC, HTML = 'art/ui_kit', 'index.html'

def main():
    meta = json.load(open(os.path.join(SRC, 'ui_kit.json')))
    out = {}
    for name, m in meta.items():
        im = Image.open(os.path.join(SRC, f'ui_{name}.png')).convert('RGBA')
        b = io.BytesIO(); im.save(b, 'WEBP', lossless=True, method=6)
        out[name] = {'d': 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), 'w': im.width, 'h': im.height}
        if 'slice' in m: out[name]['slice'] = m['slice']
    # card_champion has its crown above the frame (rows 0..61), so a 9-slice would stretch the crown along the top
    # edge: split it into a crownless frame (9-sliced like the other cards) and the crown, drawn unscaled on top.
    im = Image.open(os.path.join(SRC, 'ui_card_champion.png')).convert('RGBA')
    top = next(y for y in range(im.height) if any(im.getpixel((x, y))[3] for x in range(0, 60)))
    frame = im.crop((0, top, im.width, im.height)); crown = im.crop((0, 0, im.width, top)); crown = crown.crop(crown.getbbox())
    for name, part, extra in (('card_champion_frame', frame, {'slice': meta['card_champion']['slice']}), ('crown', crown, {})):
        b = io.BytesIO(); part.save(b, 'WEBP', lossless=True, method=6)
        out[name] = {'d': 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode(), 'w': part.width, 'h': part.height, **extra}
    s = open(HTML).read(); js = 'const UI_KIT=' + json.dumps(out, separators=(',', ':')) + ';\n'
    if 'const UI_KIT=' in s: s = re.sub(r'const UI_KIT=.*?;\n', lambda _: js, s, count=1, flags=re.S)
    else: s = s.replace('const TOWER_DATA=', js + 'const TOWER_DATA=', 1)
    open(HTML, 'w').write(s)
    print(len(out), 'pieces |', len(js) // 1024, 'KB ->', HTML)

if __name__ == '__main__':
    main()
