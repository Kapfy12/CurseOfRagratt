from pathlib import Path
from PIL import Image
import numpy as np
from crossbow_palette import dungeon_palette
from scipy.ndimage import map_coordinates
R=Path(__file__).resolve().parent
for direction in ['down','up','right']:
 a=np.array(Image.open(R.parent/'assets'/f'crossbow_reload_{direction}.png').convert('RGB')).astype(float)
 r,g,b=a[:,:,0],a[:,:,1],a[:,:,2];alpha=np.clip(1-(g-np.maximum(r,b))/180,0,1)
 alpha[(g>r*1.45)&(g>b*1.45)&(g>75)]=0;a[:,:,1]=np.minimum(g,np.maximum(r,b)*1.05)
 im=Image.fromarray(np.dstack([a,alpha*255]).astype('uint8'));im=im.crop(im.getbbox());im.thumbnail((152,220),Image.Resampling.LANCZOS)
 reload=Image.new('RGBA',(192,256));reload.alpha_composite(im,((192-im.width)//2,240-im.height))
 reload=dungeon_palette(reload)
 reload.save(R/f'crossbow_reload_{direction}.png')
 ready=Image.open(R/f'crossbow_skeleton_{direction}.png').convert('RGBA')
 frames=[];a=np.array(reload);yy,xx=np.mgrid[:256,:192].astype(float)
 for i in range(6):
  if i in (0,5):fr=ready.copy()
  else:
   # Local hand/forearm travel around the chest, without distorting legs.
   strength=[0,0,3,5,1,0][i]
   weight=np.exp(-((yy-85)/24)**2-((xx-(120 if direction=='right' else 105))/30)**2)
   sx=xx+weight*strength;sy=yy-weight*strength*.65
   ar=np.stack([map_coordinates(a[:,:,c],[sy,sx],order=1,mode='constant',cval=0) for c in range(4)],axis=-1).astype('uint8')
   fr=Image.fromarray(ar)
  frames.append(fr)
 sheet=Image.new('RGBA',(1152,256));preview=[]
 for i,fr in enumerate(frames):
  sheet.paste(fr,(192*i,0));bg=Image.new('RGBA',fr.size,(27,30,36,255));bg.alpha_composite(fr);preview.append(bg.convert('RGB').resize((384,512)))
 sheet.save(R/f'crossbow_reload_{direction}6.png')
 preview[0].save(R/f'crossbow_reload_{direction}6.gif',save_all=True,append_images=preview[1:],duration=[300,500,700,700,700,300],loop=0)
 if direction=='right':
  left=Image.new('RGBA',sheet.size)
  for i,fr in enumerate(frames):left.paste(fr.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(192*i,0))
  left.save(R/'crossbow_reload_left6.png')
print('Four reload sheets complete')
