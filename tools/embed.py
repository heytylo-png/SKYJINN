# Needs Pillow with WebP support (pip install pillow).
# Rebuild SPRITE_DATA / SPR_META / SPR_ANIM in the game from art/units/<key><tier>.png, meta.json and anim.json
import base64,json,re,glob,os,io
from PIL import Image
p='index.html';s=open(p).read()
meta=json.load(open('art/units/meta.json'))
anim=json.load(open('art/units/anim.json'))
data={}
for f in sorted(glob.glob('art/units/*.png')):
    m=re.match(r'([a-z]+)(\d)\.png',os.path.basename(f))
    if not m or m.group(1) not in meta:continue
    # embedded as lossy WebP (colour q90, exact alpha): looks the same in game at about a third of the lossless size
    im=Image.open(f).convert('RGBA');b=io.BytesIO();im.save(b,'WEBP',quality=90,alpha_quality=100,method=6)
    data.setdefault(m.group(1),{})[m.group(2)]='data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
c=lambda o:json.dumps(o,separators=(',',':'))
s,n1=re.subn(r'const SPRITE_DATA=\{.*?\};\n',lambda _:'const SPRITE_DATA='+json.dumps(data)+';\n',s,count=1,flags=re.S)
s,n2=re.subn(r'const SPR_META=\{.*?\};',lambda _:'const SPR_META='+json.dumps(meta)+';',s,count=1)
s,n3=re.subn(r'const SPR_ANIM=\{.*?\};\n',lambda _:'const SPR_ANIM='+c(anim)+';\n',s,count=1)
assert n1==1 and n2==1 and n3==1
open(p,'w').write(s);print({k:sorted(v) for k,v in data.items()},'animated:',sorted(anim),len(s))
