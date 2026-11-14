# Key out the magenta background, keep the left-most figure, despill, trim, resize.
import sys,numpy as np
from PIL import Image
from scipy import ndimage
src,dst,H=sys.argv[1],sys.argv[2],int(sys.argv[3]);MODE=sys.argv[4] if len(sys.argv)>4 else 'first'
im=np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
# background colour = median of border pixels
border=np.concatenate([im[:20].reshape(-1,3),im[-20:].reshape(-1,3),im[:,:20].reshape(-1,3),im[:,-20:].reshape(-1,3)])
bg=np.median(border,axis=0)
d=np.sqrt(((im-bg)**2).sum(-1))
# "magenta-ness": high R and B relative to G
mag=(np.minimum(im[...,0],im[...,2])-im[...,1])
fg=(d>70)&~((mag>120)&(d<140))
fg=ndimage.binary_opening(fg,iterations=1)
lab,n=ndimage.label(fg)
sizes=ndimage.sum(fg,lab,range(1,n+1))
big=[i+1 for i,sz in enumerate(sizes) if sz>sizes.max()*0.3]
objs=ndimage.find_objects(lab)
big.sort(key=lambda i:objs[i-1][1].start)
if MODE=='all':
    ids=[i+1 for i,sz in enumerate(sizes) if sz>150]
    mask=np.isin(lab,ids);ys,xs=np.where(mask);sl=(slice(ys.min(),ys.max()+1),slice(xs.min(),xs.max()+1))
elif MODE=='last':
    keep=big[-1];sl=objs[keep-1];mask=(lab==keep)
else:
    keep=big[0];sl=objs[keep-1];mask=(lab==keep)
filled=ndimage.binary_fill_holes(mask)
bgl=(d<80)|((mag>90)&(d<170))
mask=filled&~bgl
mask=ndimage.binary_opening(mask,iterations=1)|(mask&~ndimage.binary_erosion(filled,iterations=2))
# soft alpha at the edge
alpha=ndimage.gaussian_filter(mask.astype(np.float32),0.7)
alpha=np.clip((alpha-0.15)/0.7,0,1)
# despill: pull pink fringe toward neutral on edge pixels
rgb=im.copy()
spill=np.clip(np.minimum(rgb[...,0],rgb[...,2])-rgb[...,1],0,None)*(alpha<0.99)
rgb[...,0]-=spill*0.6;rgb[...,2]-=spill*0.6
y0,y1,x0,x1=sl[0].start,sl[0].stop,sl[1].start,sl[1].stop
pad=4;y0=max(0,y0-pad);x0=max(0,x0-pad);y1+=pad;x1+=pad
rgba=np.dstack([np.clip(rgb,0,255),alpha*255])[y0:y1,x0:x1].astype(np.uint8)
img=Image.fromarray(rgba,'RGBA')
w=round(img.width*H/img.height)
img=img.resize((w,H),Image.LANCZOS)
img.save(dst,optimize=True)
# report foot anchor: x of lowest opaque pixels, relative
a=np.asarray(img)[...,3]
rows=np.where(a.max(1)>128)[0];bottom=rows[-1]
print(dst,img.size,'feet-x',round(np.where(a[bottom-6:bottom+1].max(0)>128)[0].mean()/w,3))
