"""Remove pale background spill without eroding the rat silhouette or red eye."""
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

def clean_fringe(im):
    a=np.array(im.convert('RGBA'));rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]
    lum=rgb.mean(axis=2)
    spread=rgb.max(axis=2)-rgb.min(axis=2)
    edge=distance_transform_edt(alpha>220)<6
    pale=(lum>105)&(spread<65)&edge&(alpha>0)
    core=(alpha>220)&(lum<110)&(distance_transform_edt(alpha>220)>2)
    if core.any():
        _,indices=distance_transform_edt(~core,return_indices=True)
        color=rgb[indices[0],indices[1]]
        a[:,:,:3][pale]=color[pale].astype('uint8')
    a[alpha==0,:3]=0
    return Image.fromarray(a,'RGBA')
