from pathlib import Path
from PIL import Image
import numpy as np
from zombie_palette import recolor_zombie
from scipy.ndimage import map_coordinates
R=Path(__file__).resolve().parent
for direction in ['down','up','right']:
 a=np.array(Image.open(R.parent/'assets'/f'zombie_butcher_{direction}.png').convert('RGB')).astype(float)
 r,g,b=a[:,:,0],a[:,:,1],a[:,:,2];alpha=np.clip(1-(g-np.maximum(r,b))/180,0,1)
 alpha[(g>r*1.45)&(g>b*1.45)&(g>75)]=0;a[:,:,1]=np.minimum(g,np.maximum(r,b)*1.05)
 im=Image.fromarray(np.dstack([a,alpha*255]).astype('uint8'));im=im.crop(im.getbbox());im.thumbnail((166,218),Image.Resampling.LANCZOS)
 base=Image.new('RGBA',(192,256));base.alpha_composite(im,((192-im.width)//2,240-im.height));base=recolor_zombie(base,direction);base.save(R/f'zombie_butcher_{direction}.png')
 a=np.array(base);yy,xx=np.mgrid[:256,:192].astype(float);sheet=Image.new('RGBA',(1152,256))
 for f in range(6):
  t=f*2*np.pi/6;side=np.where(xx<96,-1.,1.);leg=np.clip((yy-173)/60,0,1)
  sway=np.sin(t)*2*(1-leg);sx=xx-sway-leg*side*np.sin(t)*(7 if direction=='right' else 3)
  sy=yy+2*(1-np.cos(2*t))+leg*side*np.sin(t)*6
  ar=np.stack([map_coordinates(a[:,:,c],[sy,sx],order=1,mode='constant',cval=0) for c in range(4)],axis=-1).astype('uint8')
  sheet.paste(Image.fromarray(ar),(f*192,0))
 sheet.save(R/f'zombie_butcher_{direction}6.png')
 if direction=='right':
  left=Image.new('RGBA',sheet.size)
  for f in range(6):left.paste(sheet.crop((f*192,0,(f+1)*192,256)).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(f*192,0))
  left.save(R/'zombie_butcher_left6.png')
