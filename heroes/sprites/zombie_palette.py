from PIL import Image,ImageDraw
import numpy as np

def recolor_zombie(im,direction):
 a=np.array(im);rgb=a[:,:,:3].astype(float);y,x=np.mgrid[:256,:192]
 mask=Image.new('L',im.size);d=ImageDraw.Draw(mask)
 if direction=='down':d.polygon([(70,82),(118,82),(129,110),(139,170),(122,191),(64,190),(49,174),(62,110)],fill=255)
 elif direction=='right':d.polygon([(92,81),(133,79),(151,116),(150,168),(126,190),(73,181),(73,133)],fill=255)
 apron=np.array(mask)>0
 # Back is bare; all pale exposed flesh is tinted, while boots and steel remain unchanged.
 skin=(y<169)&(~apron)&(rgb[:,:,1]>=rgb[:,:,2]*.95)
 if direction=='up':skin&=(y<133)|((x<48)|(x>137))
 lum=rgb@np.array([.2126,.7152,.0722])
 green=lum[:,:,None]*np.array([.43,.59,.36])
 brown=lum[:,:,None]*np.array([.91,.61,.36])
 rgb=np.where(skin[:,:,None],green,rgb)
 rgb=np.where(apron[:,:,None],brown,rgb)
 a[:,:,:3]=np.clip(rgb,0,255).astype('uint8');return Image.fromarray(a)
