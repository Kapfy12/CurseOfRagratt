from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import label,binary_dilation
from rat_remove_fringe import clean_fringe
ROOT=Path(__file__).resolve().parents[2]
a=np.asarray(Image.open(ROOT/'heroes/assets/rat_run_up_source.png').convert('RGB')).astype(np.float32)/255
bg=np.median(a[:24].reshape(-1,3),axis=0)
excess=np.maximum(0,a[:,:,1]-np.maximum(a[:,:,0],a[:,:,2]))
strength=max(.1,bg[1]-max(bg[0],bg[2]))
alpha=np.clip(1-excess/strength,0,1);alpha[alpha<.08]=0
rgb=np.clip((a-(1-alpha[:,:,None])*bg)/np.maximum(alpha[:,:,None],.001),0,1)
# Discard background flecks; preserve fine edges near the animal silhouette.
components,n=label(alpha>.2)
counts=np.bincount(components.ravel());counts[0]=0
keep=binary_dilation(components==counts.argmax(),iterations=4)
alpha[~keep]=0;rgb[alpha==0]=0
im=Image.fromarray(np.uint8(np.dstack((rgb,alpha))*255),'RGBA')
im=clean_fringe(im)
im=im.crop(im.getbbox())
padded=Image.new('RGBA',(im.width+32,im.height+32));padded.alpha_composite(im,(16,16))
padded.save(ROOT/'heroes/sprites/rat_run_up.png')
small=padded.copy();small.thumbnail((120,248),Image.Resampling.LANCZOS)
cell=Image.new('RGBA',(128,256));cell.alpha_composite(small,((128-small.width)//2,(256-small.height)//2))
cell.save(ROOT/'heroes/sprites/rat_run_up_128x256.png')
print('Transparent source:',padded.size,'game cell:',cell.size)
