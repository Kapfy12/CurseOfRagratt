"""Six-frame front three-quarter run from the matching HD down-right warrior."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import math
ROOT=Path(__file__).resolve().parent
W,H=144,114
src=Image.open(ROOT/'warrior_frames8_hd.png').convert('RGBA').crop((0,114,144,228))
def part(poly):
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255)
    im=src.copy();im.putalpha(Image.fromarray(np.minimum(np.array(src.getchannel('A')),np.array(mask))))
    return im

def bone(im,a,b,c,d):
    v=complex(b[0]-a[0],b[1]-a[1]);q=complex(d[0]-c[0],d[1]-c[1])/v
    mat=np.array([[q.real,-q.imag],[q.imag,q.real]]);inv=np.linalg.inv(mat)
    off=np.array(a)-inv@np.array(c)
    return im.transform((W,H),Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)

# Preserve hand, hilt and blade together: no independent wrist rotation.
upper=part([(0,0),(144,0),(144,66),(99,66),(86,65),(77,61),(66,66),(54,67),(54,59),(0,59)])
leftU=part([(57,65),(70,64),(64,76),(56,84),(52,90),(45,87),(45,79)])
leftL=part([(45,82),(56,82),(54,96),(48,106),(40,113),(31,113),(36,104),(42,96)])
rightU=part([(82,64),(94,65),(100,76),(105,83),(104,92),(93,92),(87,81)])
rightL=part([(93,85),(105,85),(108,99),(117,108),(116,114),(104,114),(98,105),(96,98)])
# Separate boots from shin artwork so a raised toe can expose the sole.
for calf in (leftL,rightL):
    pixels=np.array(calf); pixels[101:,:,:]=0
    calf.paste(Image.fromarray(pixels))

def front_boot(im,foot,sole):
    x,y=[int(round(v)) for v in foot]
    boot=Image.new('RGBA',(W,H))
    d=ImageDraw.Draw(boot)
    if sole:
        # The toe lifts toward the camera: dark sole with worn rim and tread.
        d.polygon([(x-3,y-7),(x+3,y-7),(x+5,y-4),(x+4,y+3),
                   (x+2,y+5),(x-3,y+5),(x-5,y+2),(x-5,y-4)],fill=(12,13,15,255))
        d.polygon([(x-2,y-5),(x+2,y-5),(x+3,y-2),(x+2,y+3),
                   (x-2,y+3),(x-3,y),(x-3,y-2)],fill=(66,60,51,255))
        d.line([(x-3,y-4),(x+2,y-5)],fill=(107,100,86,255),width=1)
        for yy in (-2,1):
            d.line([(x-3,y+yy),(x+2,y+yy)],fill=(24,24,23,255),width=1)
        d.line([(x-2,y+3),(x+2,y+3)],fill=(91,84,72,255),width=1)
    else:
        d.polygon([(x-3,y-3),(x+3,y-3),(x+5,y+2),(x+3,y+4),
                   (x-4,y+4),(x-5,y+1)],fill=(25,27,30,255))
        d.line([(x-3,y),(x+2,y-1),(x+3,y+1)],fill=(89,91,91,255),width=1)
        d.line([(x-4,y+4),(x+3,y+4)],fill=(10,11,13,255),width=1)
    if sole:
        boot=boot.transform((W,H),Image.Transform.AFFINE,
            (1,0,0,0,1/0.72,y-y/0.72),Image.Resampling.BICUBIC)
        boot=boot.rotate(25, resample=Image.Resampling.BICUBIC, center=(x,y))
    im.alpha_composite(boot)
frames=[]
for f in range(6):
    bob=[0,-1,-2,0,-1,-2][f]
    sway=[-1,0,1,1,0,-1][f]
    im=Image.new('RGBA',(W,H))
    # Narrow forward-running tracks, with alternating lifted knees.
    knees=[84,78,73,78,85,86]
    feet=[105,91,83,88,105,105]
    # Opposite legs are three phases apart. At least one ankle stays on
    # the ground line in every frame, independently of body bobbing.
    assert max(feet[f],feet[(f+3)%6])==105
    # Far/recovering leg first; approaching leg in front.
    order=sorted((0,1),key=lambda side:feet[(f+3*side)%6])
    for side in order:
        k=(f+side*3)%6
        hip=np.array([71 if side==0 else 85,64+bob],float)
        bend=[0,2,3,2,1,0][k]
        travel=[4,7,5,-4,-7,0][k]
        knee=np.array([(71-bend if side==0 else 85+bend)+travel*0.5,knees[k]+bob],float)
        foot=np.array([(70 if side==0 else 86)+travel,feet[k]],float)
        if side==0:
            im.alpha_composite(bone(leftU,(63,65),(51,84),hip,knee))
            im.alpha_composite(bone(leftL,(51,84),(43,103),knee,foot))
        else:
            im.alpha_composite(bone(rightU,(88,65),(99,85),hip,knee))
            im.alpha_composite(bone(rightL,(99,85),(108,105),knee,foot))
        front_boot(im,foot,k in (1,2,3))
    # Upper-body counter-sway keeps the weapon rigid in the fist.
    im.alpha_composite(bone(upper,(78,63),(78,25),(78+sway,63+bob),(81-sway,26+bob)))
    frames.append(im)
sheet=Image.new('RGBA',(W*6,H));preview=[]
for f,im in enumerate(frames):
    sheet.alpha_composite(im,(f*W,0))
    bg=Image.new('RGB',(W,H),(31,34,39));bg.paste(im,(0,0),im)
    preview.append(bg.resize((W*4,H*4),Image.Resampling.NEAREST))
sheet.save(ROOT/'warrior_run_downright6.png')
preview[0].save(ROOT/'warrior_run_downright6.gif',save_all=True,append_images=preview[1:],duration=[140,140,140,150,140,150],loop=0,disposal=2)
