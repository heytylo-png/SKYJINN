# Embed champion pose frames (art/poses/poses.json + PNGs) into index.html as SPR_POSE (lossy WebP, only frames that are used).
import json,base64,io,re
from PIL import Image
P=json.load(open('art/poses/poses.json'));out={}
for id,e in P.items():
    used=sorted({i for s in ('idle','walk','atk','die') for i in e.get(s,[])});remap={o:n for n,o in enumerate(used)};fr=[]
    for o in used:
        f=e['f'][o];im=Image.open('art/poses/'+f['png']).convert('RGBA');b=io.BytesIO();im.save(b,'WEBP',quality=86,alpha_quality=90,method=6)
        fr.append({'d':'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode(),'ax':f['ax'],'fy':f['fy']})
    out[id]={'f':fr,**{s:[remap[i] for i in e[s]] for s in ('idle','walk','atk','die') if s in e}}
p='index.html';s=open(p).read();js='const SPR_POSE='+json.dumps(out,separators=(',',':'))+';\n'
if 'const SPR_POSE=' in s:s=re.sub(r'const SPR_POSE=\{.*?\};\n',lambda _:js,s,count=1,flags=re.S)
else:i=s.index('const SPR={}');s=s[:i]+js+s[i:]
open(p,'w').write(s);print(len(js)//1024,'KB',{k:len(v['f']) for k,v in out.items()})
