# Cut champion pose strips (idle / walk / attack / death frames on a magenta background) into frames.
# python3 tools/poses.py  -> art/poses/<key><tier>_<n>.png + art/poses/poses.json
import json,numpy as np
from PIL import Image
from scipy import ndimage
TARGET=170  # idle frame height in px
# sheet: [(key, tier, frame count, states)] per row, top to bottom. states map name -> frame indexes in that row.
S4={'idle':[0],'walk':[1,0],'atk':[2],'die':[3]}
SHEETS={
 'djc1':[('djc',1,4,S4)],'djc2':[('djc',2,4,S4)],'djc3':[('djc',3,4,S4)],
 'wym1':[('wym',1,4,S4)],'wym2':[('wym',2,4,{'idle':[0,1],'walk':[0,1],'atk':[2],'die':[3]})],
 'vec1':[('vec',1,4,S4)],'vec3':[('vec',3,4,S4)],'vec2_muc2':[('vec',2,4,S4),('muc',2,4,S4)],
 'muc1':[('muc',1,4,S4)],
 'muc3':[('muc',3,6,{'idle':[0,2,4]}),('muc',3,8,{'walk':[0,2,4,6]}),('muc',3,8,{'atk':[3,4,5,6]}),('muc',3,8,{'die':[1,3,5,7]})],
 'knc1':[('knc',1,5,{'idle':[0],'walk':[1,0],'atk':[2],'die':[3,4]})],'knc2':[('knc',2,4,S4)],'knc3':[('knc',3,4,S4)],
 'gbc1':[('gbc',1,4,S4)],'lch1':[('lch',1,4,S4)],'lch3':[('lch',3,4,S4)],
 'col1':[('col',1,4,S4)],'col2':[('col',2,4,S4)],'col3':[('col',3,4,S4)]}
CROP={'muc3':(130,0)}
ROWNORM={'muc3'}  # rows drawn at different sizes: scale each row's first frame to the target  # left label column to drop
def key(im):
    border=np.concatenate([im[:12].reshape(-1,3),im[-12:].reshape(-1,3),im[:,:12].reshape(-1,3),im[:,-12:].reshape(-1,3)])
    bg=np.median(border,axis=0);d=np.sqrt(((im-bg)**2).sum(-1));mag=np.minimum(im[...,0],im[...,2])-im[...,1]
    fg=(d>70)&~((mag>110)&(d<150));fg=ndimage.binary_opening(fg,iterations=1)
    lab,n=ndimage.label(fg);sz=ndimage.sum(fg,lab,range(1,n+1));fg=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>40])
    filled=ndimage.binary_fill_holes(fg);bgl=(d<75)|((mag>85)&(d<170));mask=filled&~bgl
    a=ndimage.gaussian_filter(mask.astype(np.float32),0.7);a=np.clip((a-0.15)/0.7,0,1)
    rgb=im.copy();sp=np.clip(np.minimum(rgb[...,0],rgb[...,2])-rgb[...,1],0,None)*(a<0.99);rgb[...,0]-=sp*0.7;rgb[...,2]-=sp*0.7
    return np.dstack([np.clip(rgb,0,255),a*255]).astype(np.uint8),mask
def spans(proj,gap,n,cnt=None):
    on=proj>0;segs=[];i=0;L=len(on)
    while i<L:
        if on[i]:
            j=i
            while j<L and on[j]:j+=1
            segs.append([i,j]);i=j
        else:i+=1
    # merge across small gaps, then merge smallest until n
    out=[]
    for s in segs:
        if out and s[0]-out[-1][1]<gap:out[-1][1]=s[1]
        else:out.append(s)
    while len(out)>n:
        w=[(s[1]-s[0]) for s in out];i=int(np.argmin(w))
        if i==0:j=1
        elif i==len(out)-1:j=i-1
        else:j=i-1 if out[i][0]-out[i-1][1]<out[i+1][0]-out[i][1] else i+1
        a,b=sorted([i,j]);out[a]=[out[a][0],out[b][1]];del out[b]
    while cnt is not None and len(out)<n:
        w=[(s[1]-s[0]) for s in out];i=int(np.argmax(w));a,b=out[i];lo=a+(b-a)*3//10;hi=a+(b-a)*7//10
        c=lo+int(np.argmin(cnt[lo:hi]));out[i:i+1]=[[a,c],[c,b]]
    return out
out={}
for name,rows in SHEETS.items():
    im=np.asarray(Image.open(f'art/poses/src/{name}.png').convert('RGB')).astype(np.float32)
    cx,cy=CROP.get(name,(0,0));im=im[cy:,cx:]
    rgba,mask=key(im)
    rb=spans(mask.sum(1)>3,12,len(rows))
    assert len(rb)==len(rows),(name,len(rb))
    scale=None
    for (k,t,n,states),(y0,y1) in zip(rows,rb):
        band=mask[y0:y1];cs=spans(band.sum(0)>0,6,n,band.sum(0));assert len(cs)==n,(name,k,len(cs))
        # give each blob to one frame: whole if it is mostly on one side of a cut, else split at the cut
        er=ndimage.binary_erosion(band,iterations=4);lab,nl=ndimage.label(er)
        if nl:
            _,(iy,ix)=ndimage.distance_transform_edt(lab==0,return_indices=True);lab=np.where(band,lab[iy,ix],0)
        owner=np.zeros(band.shape,np.int8)-1;cuts=[c[1] for c in cs[:-1]]
        colseg=np.searchsorted(np.array(cuts),np.arange(band.shape[1]),side='right')
        for li,sl in enumerate(ndimage.find_objects(lab)):
            m=lab[sl]==li+1;cols=np.arange(sl[1].start,sl[1].stop);seg=colseg[cols];cnt=np.bincount(seg,weights=m.sum(0),minlength=n)
            if True:
                o=owner[sl];o[m]=int(cnt.argmax())
            else:
                o=owner[sl];o[m]=np.broadcast_to(seg,m.shape)[m]
        # small blobs (slashes, sparks, smoke) go to the frame whose main body is closest
        sizes=np.bincount(lab.ravel(),minlength=nl+1);sizes[0]=0
        mains={}
        for f in range(n):
            ls,cn=np.unique(lab[(owner==f)&(lab>0)],return_counts=True)
            if len(ls):mains[f]=ls[np.argmax(cn)]
        if len(mains)==n:
            dts=[ndimage.distance_transform_edt(lab!=mains[f]) for f in range(n)];big=max(sizes)
            for li in range(1,nl+1):
                if li in mains.values() or sizes[li]>0.25*big:continue
                m=lab==li;owner[m]=int(np.argmin([d[m].min() for d in dts]))
        fmask=[];boxes=[]
        for f in range(n):
            m=owner==f;ys,xs=np.where(m);fmask.append(m);boxes.append((xs.min(),xs.max()+1,y0+ys.min(),y0+ys.max()+1))
        ground=boxes[0][3]
        if scale is None or (k,t)!=prev or name in ROWNORM:scale=TARGET/(boxes[0][3]-boxes[0][2]);ground0=ground
        prev=(k,t)
        ent=out.setdefault(k+str(t),{'f':[]})
        idx0=len(ent['f'])
        for fi,(x0,x1,ya,yb) in enumerate(boxes):
            pad=6;X0=max(0,x0-pad);X1=x1+pad;Y0=max(0,ya-pad);Y1=max(yb,ground)+pad
            fm=np.zeros(mask.shape,bool);fm[y0:y1]=fmask[fi];fm=ndimage.binary_dilation(fm,iterations=2)
            cr=rgba[Y0:Y1,X0:X1].copy();cr[...,3]=cr[...,3]*fm[Y0:Y1,X0:X1]
            crop=Image.fromarray(cr,'RGBA');W=max(1,round(crop.width*scale));H=max(1,round(crop.height*scale))
            crop=crop.resize((W,H),Image.LANCZOS)
            idh=boxes[0][3]-boxes[0][2]
            FM=np.zeros(mask.shape,bool);FM[y0:y1]=fmask[fi];body=FM[ground-int(idh*0.6):ground,X0:X1];feet=FM[ground-int(idh*0.2):ground,X0:X1]
            fx=np.where(feet)[1];back=float(np.percentile(fx,8)) if len(fx) else 0
            if fi==0:
                xs=np.where(body)[1];ax=float(np.median(xs));back0=back
            else:ax=back+(ax_idle-back0)
            if fi==0:ax_idle=ax
            fn=f'{k}{t}_{idx0+fi}.png';crop.save('art/poses/'+fn,optimize=True)
            ent['f'].append({'png':fn,'ax':round(ax*scale,1),'fy':round((ground-Y0)*scale,1),'w':W,'h':H})
        for st,ix in states.items():ent.setdefault(st,[]).extend(idx0+i for i in ix)
    print(name,'ok')
json.dump(out,open('art/poses/poses.json','w'),indent=1)
print(sorted(out))
