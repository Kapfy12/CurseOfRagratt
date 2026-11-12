"""Six-frame rear-view run articulated from the original HD up-facing warrior."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import math
ROOT=Path(__file__).resolve().parent
W,H=144,114
src=Image.open(ROOT/'warrior_frames8_hd.png').convert('RGBA').crop((0,456,144,570))
def part(poly):
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255)
    im=src.copy();im.putalpha(Image.fromarray(np.minimum(np.array(src.getchannel('A')),np.array(mask))))
    return im

def bone(im,a,b,c,d):
    v=complex(b[0]-a[0],b[1]-a[1]);q=complex(d[0]-c[0],d[1]-c[1])/v
    mat=np.array([[q.real,-q.imag],[q.imag,q.real]]);inv=np.linalg.inv(mat)
    off=np.array(a)-inv@np.array(c)
    return im.transform((W,H),Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)

torso=part([(42,20),(49,24),(52,0),(74,0),(78,24),(83,27),(76,43),(75,52),(83,66),(69,70),(60,65),(48,70),(43,64),(48,50),(48,39)])
leftarm=part([(28,18),(42,18),(50,28),(47,39),(41,47),(30,49),(25,36)])
rightarm=part([(79,25),(88,29),(95,41),(94,52),(98,61),(88,65),(79,54),(75,41)])
leftU=part([(45,64),(59,65),(51,83),(46,92),(35,88),(35,81)])
leftL=part([(35,82),(47,85),(43,99),(43,112),(26,112),(29,100)])
rightU=part([(64,65),(77,64),(86,76),(89,90),(77,93),(73,83)])
rightL=part([(76,86),(89,85),(91,100),(97,105),(96,113),(78,113),(77,99)])
# Remove the original outward-pointing toes. Rear-facing boots are drawn
# at the animated ankles, including their soles on the recovery stride.
for calf in (leftL,rightL):
    pixels=np.array(calf); pixels[103:,:,:]=0
    calf.paste(Image.fromarray(pixels))

def rear_boot(im,foot,lift):
    x,y=map(lambda v:int(round(v)),foot)
    d=ImageDraw.Draw(im)
    if lift:
        # Sole facing the camera: narrow toe, broad heel, dark leather tread.
        d.polygon([(x-3,y-8),(x+3,y-8),(x+5,y-3),(x+4,y+4),
                   (x+2,y+6),(x-3,y+6),(x-5,y+2),(x-5,y-3)],fill=(15,16,18,255))
        d.polygon([(x-2,y-6),(x+2,y-6),(x+3,y-2),(x+2,y+4),
                   (x-2,y+4),(x-3,y+1),(x-3,y-2)],fill=(57,52,45,255))
        d.line([(x-3,y-2),(x+3,y-2)],fill=(23,23,23,255),width=1)
        d.line([(x-3,y+1),(x+2,y+1)],fill=(22,22,22,255),width=1)
        d.line([(x-2,y+4),(x+2,y+4)],fill=(100,93,79,255),width=1)
        d.line([(x-4,y-3),(x-4,y+1)],fill=(88,89,86,255),width=1)
    else:
        # Back of a planted armored boot, with a distinct heel edge.
        d.polygon([(x-4,y-5),(x+3,y-5),(x+4,y+2),(x+3,y+4),
                   (x-4,y+4),(x-5,y+1)],fill=(23,25,28,255))
        d.line([(x-3,y-4),(x-3,y)],fill=(84,86,87,255),width=1)
        d.line([(x-3,y+1),(x+2,y+1)],fill=(64,62,56,255),width=1)
        d.line([(x-4,y+4),(x+3,y+4)],fill=(9,10,12,255),width=1)
frames=[]
for f in range(6):
    bob=[0,-2,-4,0,-2,-4][f]
    sway=[-1,0,1,1,0,-1][f]
    im=Image.new('RGBA',(W,H))
    # Rear-view perspective: recovery heel rises toward the seat, while
    # the opposite leg extends toward the floor; no sideways running pose.
    knees=[(0,85),(2,79),(1,75),(0,80),(-1,85),(-1,88)]
    feet=[(0,106),(1,96),(2,84),(1,91),(0,104),(-1,108)]
    for side in (0,1):
        k=(f+side*3)%6; sign=-1 if side==0 else 1
        hip=np.array([55 if side==0 else 69,65+bob],float)
        knee=np.array([hip[0]-sign*1+knees[k][0]*0.4,knees[k][1]+bob],float)
        foot=np.array([hip[0]-sign*1+feet[k][0]*0.4,feet[k][1]+bob],float)
        if side==0:
            im.alpha_composite(bone(leftU,(51,67),(42,86),hip,knee))
            im.alpha_composite(bone(leftL,(42,86),(35,105),knee,foot))
        else:
            im.alpha_composite(bone(rightU,(71,67),(82,87),hip,knee))
            im.alpha_composite(bone(rightL,(82,87),(86,106),knee,foot))
        rear_boot(im,foot,k in (2,3))
    upper=Image.new('RGBA',(W,H))
    for side,arm,pivot in [(0,leftarm,(46,30)),(1,rightarm,(80,30))]:
        k=(f+3*side)%6
        angle=math.radians([-15,-7,8,15,7,-8][k])
        dy=[-3,-1,2,3,1,-2][k]
        dest=(pivot[0]+sway,pivot[1]+bob+dy)
        tip=(dest[0]+18*math.sin(angle),dest[1]+18*math.cos(angle))
        upper.alpha_composite(bone(arm,pivot,(pivot[0],pivot[1]+18),dest,tip))
    upper.alpha_composite(bone(torso,(62,65),(62,25),(62+sway,65+bob),(62-sway,26+bob)))
    im.alpha_composite(upper)
    frames.append(im)
sheet=Image.new('RGBA',(W*6,H));preview=[]
for f,im in enumerate(frames):
    sheet.alpha_composite(im,(f*W,0))
    bg=Image.new('RGB',(W,H),(31,34,39));bg.paste(im,(0,0),im)
    preview.append(bg.resize((W*4,H*4),Image.Resampling.NEAREST))
sheet.save(ROOT/'warrior_run_up6.png')
preview[0].save(ROOT/'warrior_run_up6.gif',save_all=True,append_images=preview[1:],duration=[140,140,140,150,140,150],loop=0,disposal=2)
