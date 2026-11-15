# Rebuild SPRITE_DATA / SPR_META / SPR_ANIM in the game from art/units/<key><tier>.png, meta.json and anim.json
import base64,json,re,glob,os
p='index.html';s=open(p).read()
meta=json.load(open('art/units/meta.json'))
anim=json.load(open('art/units/anim.json'))
data={}
for f in sorted(glob.glob('art/units/*.png')):
    m=re.match(r'([a-z]+)(\d)\.png',os.path.basename(f))
    if not m or m.group(1) not in meta:continue
    data.setdefault(m.group(1),{})[m.group(2)]='data:image/png;base64,'+base64.b64encode(open(f,'rb').read()).decode()
c=lambda o:json.dumps(o,separators=(',',':'))
s,n1=re.subn(r'const SPRITE_DATA=\{.*?\};\n',lambda _:'const SPRITE_DATA='+json.dumps(data)+';\n',s,count=1,flags=re.S)
s,n2=re.subn(r'const SPR_META=\{.*?\};',lambda _:'const SPR_META='+json.dumps(meta)+';',s,count=1)
s,n3=re.subn(r'const SPR_ANIM=\{.*?\};\n',lambda _:'const SPR_ANIM='+c(anim)+';\n',s,count=1)
assert n1==1 and n2==1 and n3==1
open(p,'w').write(s);print({k:sorted(v) for k,v in data.items()},'animated:',sorted(anim),len(s))
