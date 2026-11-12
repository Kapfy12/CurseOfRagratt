"""Cold, desaturated dungeon palette; alpha remains unchanged."""
import numpy as np
from PIL import Image
def dungeon_palette(im):
 a=np.array(im.convert('RGBA'));rgb=a[:,:,:3].astype(float)
 lum=rgb@np.array([.2126,.7152,.0722])
 mixed=rgb*.18+lum[:,:,None]*.82
 mixed*=np.array([.77,.81,.86])
 a[:,:,:3]=np.clip(mixed,0,255).astype('uint8')
 return Image.fromarray(a)
