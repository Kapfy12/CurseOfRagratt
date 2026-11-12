from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent
for name in ['rat','skeleton']:
 a=np.array(Image.open(R.parent/'assets'/f'{name}_remains_source.png').convert('RGB')).astype(float)
 r,g,b=a[:,:,0],a[:,:,1],a[:,:,2];alpha=np.clip(1-(g-np.maximum(r,b))/180,0,1)
 alpha[(g>r*1.45)&(g>b*1.45)&(g>75)]=0
 a[:,:,1]=np.minimum(g,np.maximum(r,b)*1.05)
 lum=a@np.array([.2126,.7152,.0722]);a=(a*.2+lum[:,:,None]*.8)*np.array([.75,.79,.84])
 im=Image.fromarray(np.dstack([np.clip(a,0,255),alpha*255]).astype('uint8'));im=im.crop(im.getbbox());im.thumbnail((256,160),Image.Resampling.LANCZOS)
 im.save(R/f'{name}_remains.png')
