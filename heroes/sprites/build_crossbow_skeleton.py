"""Four six-frame crossbowman walk sheets, transparent and matching game scale."""
from pathlib import Path
from PIL import Image
import numpy as np
from crossbow_palette import dungeon_palette
from scipy.ndimage import map_coordinates
R=Path(__file__).resolve().parent
for direction in ['down','up','right']:
 src=np.array(Image.open(R.parent/'assets'/f'crossbow_skeleton_{direction}.png').convert('RGB')).astype(float)
 r,g,b=src[:,:,0],src[:,:,1],src[:,:,2]
 # Green chroma, including holes between bones. Unmix contaminated edges.
 alpha=np.clip(1-(g-np.maximum(r,b))/180,0,1)
 alpha[(g>r*1.45)&(g>b*1.45)&(g>75)]=0
 rgb=src.copy();rgb[:,:,1]=np.minimum(g,np.maximum(r,b)*1.05)
 a=np.dstack([rgb,alpha*255]).astype('uint8');im=Image.fromarray(a);im=im.crop(im.getbbox());im.thumbnail((152,220),Image.Resampling.LANCZOS)
 base=Image.new('RGBA',(192,256));base.alpha_composite(im,((192-im.width)//2,240-im.height))
 base=dungeon_palette(base)
 base.save(R/f'crossbow_skeleton_{direction}.png')
 a=np.array(base);yy,xx=np.mgrid[0:256,0:192].astype(float)
 frames=[]
 for f in range(6):
  phase=f*2*np.pi/6;stride=np.sin(phase);bob=2*(1-np.cos(phase*2))
  # Upper body, hands and crossbow remain a single rigid unit.
  weight=np.clip((yy-167)/65,0,1)
  side=np.where(xx<96,-1.,1.)
  sy=yy+bob+weight*side*stride*7
  sx=xx-weight*side*stride*(8 if direction=='right' else 3)
  ar=np.stack([map_coordinates(a[:,:,c],[sy,sx],order=1,mode='constant',cval=0) for c in range(4)],axis=-1).astype('uint8')
  frames.append(Image.fromarray(ar))
 sheet=Image.new('RGBA',(1152,256));preview=[]
 for i,fr in enumerate(frames):
  sheet.paste(fr,(192*i,0));bg=Image.new('RGBA',fr.size,(27,30,36,255));bg.alpha_composite(fr);preview.append(bg.convert('RGB').resize((384,512)))
 sheet.save(R/f'crossbow_skeleton_{direction}6.png')
 preview[0].save(R/f'crossbow_skeleton_{direction}6.gif',save_all=True,append_images=preview[1:],duration=120,loop=0)
 if direction=='right':
  left=Image.new('RGBA',sheet.size)
  for i,fr in enumerate(frames):left.paste(fr.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(192*i,0))
  left.save(R/'crossbow_skeleton_left6.png')
print('Four directions; six frames per direction; 192x256 cells.')
