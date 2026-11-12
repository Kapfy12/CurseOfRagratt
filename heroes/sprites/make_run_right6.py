"""Six-frame articulated right run, using the existing HD warrior pixels."""
from PIL import Image, ImageDraw
import numpy as np
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
src=Image.open(ROOT/'warrior_frames8_hd.png').convert('RGBA').crop((0,228,144,342))
W,H=144,114

def part(poly):
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255)
    im=src.copy();im.putalpha(Image.fromarray(np.minimum(np.array(src.getchannel('A')),np.array(mask))))
    return im

def segment(im,a,b,c,d):
    # Similarity transform from source bone a->b to animated c->d.
    v=complex(b[0]-a[0],b[1]-a[1]); q=complex(d[0]-c[0],d[1]-c[1])/v
    A=np.array([[q.real,-q.imag],[q.imag,q.real]])
    inv=np.linalg.inv(A); off=np.array(a)-inv@np.array(c)
    return im.transform((W,H),Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)

body=part([(0,0),(144,0),(144,62),(94,62),(84,66),(82,72),(62,74),(0,67)])
# Isolate the bent sword arm and the far hand so the torso no longer carries
# a second, motionless copy of either arm.
arm_poly=[(68,26),(80,28),(80,38),(76,42),(94,53),(144,24),(144,46),(96,60),(87,59),(68,47),(65,38)]
far_poly=[(97,29),(106,30),(111,38),(104,46),(94,46),(93,38)]
arm=part(arm_poly)
# Hand, hilt and blade remain one rigid piece in every frame.
far_arm=part(far_poly)
body_array=np.array(body)
for poly in (arm_poly,far_poly):
    mask=Image.new('L',(W,H)); ImageDraw.Draw(mask).polygon(poly,fill=255)
    cut=np.array(mask)>0
    body_array[cut]=0
# Patch only the torso under the removed foreground arm, with existing armor
# texture; outer silhouette stays transparent.
patch=Image.new('L',(W,H));ImageDraw.Draw(patch).polygon([(71,29),(80,30),(89,45),(89,57),(73,51),(69,41)],fill=255)
raw=np.array(src)
for y,x in zip(*np.where(np.array(patch)>0)):
    pixel=raw[y,83+(x%5)].copy()
    if pixel[3]==0: pixel=np.array([23,25,28,255],dtype=np.uint8)
    body_array[y,x]=pixel
body=Image.fromarray(body_array)
farU=part([(81,61),(91,65),(107,79),(102,88),(91,86),(78,71)])
farL=part([(91,80),(106,80),(106,100),(115,104),(115,111),(91,111),(90,94)])
nearU=part([(63,69),(82,70),(76,83),(67,92),(55,88),(55,82)])
nearL=part([(56,83),(72,86),(65,99),(61,105),(65,111),(48,113),(48,104)])
frames=[]
for f in range(6):
    # Explicit sprint poses: strike, push-off, flight; other leg is half a cycle apart.
    bob=[-2,1,-4,-2,1,-4][f]
    thighs=[55,15,-38,-55,-5,65]
    shins=[15,-15,-55,-120,-140,-60]
    im=Image.new('RGBA',(W,H))
    for near in (False,True):
        k=(f+(0 if near else 3))%6
        hip=np.array([69 if near else 77,66 if near else 63],float)+[0,bob]
        t=math.radians(thighs[k]); u=math.radians(shins[k])
        knee=hip+22*np.array([math.sin(t),math.cos(t)])
        ankle=knee+25*np.array([math.sin(u),math.cos(u)])
        if near:
            im.alpha_composite(segment(nearU,(73,72),(63,86),hip,knee))
            im.alpha_composite(segment(nearL,(63,86),(55,106),knee,ankle))
        else:
            im.alpha_composite(segment(farU,(84,65),(99,82),hip,knee))
            im.alpha_composite(segment(farL,(99,82),(99,105),knee,ankle))
    # Lean the whole upper body into the run; weapon follows the shoulder sway.
    lean=math.radians(15+[0,2,-2,0,2,-2][f])
    anchor=np.array([72,64+bob],float)
    shoulder=anchor+np.array([34*math.sin(lean),-34*math.cos(lean)])
    # Counter-swing arms opposite the forward leg; retain the bent elbows.
    swing=math.radians([-45,-27,13,30,0,-29][f])
    upper=Image.new('RGBA',(W,H))
    far_pivot=np.array([94,33],float)
    far_end=far_pivot+np.array([12*math.sin(-swing),12*math.cos(-swing)])
    upper.alpha_composite(segment(far_arm,(94,33),(94,45),far_pivot,far_end))
    upper.alpha_composite(body)
    pivot=np.array([74,31],float)
    end=pivot+np.array([22*math.sin(swing),22*math.cos(swing)])
    # No wrist/blade-only transform: the original grip is preserved exactly.
    upper.alpha_composite(segment(arm,(74,31),(74,53),pivot,end))
    im.alpha_composite(segment(upper,(77,69),(77,35),anchor,shoulder))
    frames.append(im)
sheet=Image.new('RGBA',(W*6,H))
for i,im in enumerate(frames):sheet.alpha_composite(im,(i*W,0))
sheet.save(ROOT/'warrior_run_right6.png')
preview=[]
for im in frames:
    bg=Image.new('RGB',(W,H),(31,34,39));bg.paste(im,(0,0),im)
    preview.append(bg.resize((W*4,H*4),Image.Resampling.NEAREST))
preview[0].save(ROOT/'warrior_run_right6.gif',save_all=True,append_images=preview[1:],duration=[140,140,140,150,140,150],loop=0,disposal=2)
print('Saved six frames and animated preview')
