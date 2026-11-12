"""Articulated six-frame rat run. The selected red-eye artwork is preserved."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import math
from rat_remove_fringe import clean_fringe
ROOT=Path(__file__).resolve().parent
src=clean_fringe(Image.open(ROOT/'rat_rig_source.png').convert('RGBA'))
W,H=src.size

def part(poly):
    m=Image.new('L',(W,H));ImageDraw.Draw(m).polygon(poly,fill=255)
    a=np.array(src);a[:,:,3]=np.minimum(a[:,:,3],np.array(m))
    return Image.fromarray(a)

def bone(im,a,b,c,d):
    q=complex(d[0]-c[0],d[1]-c[1])/complex(b[0]-a[0],b[1]-a[1])
    mat=np.array([[q.real,-q.imag],[q.imag,q.real]]);inv=np.linalg.inv(mat);off=np.array(a)-inv@np.array(c)
    return im.transform((W,H),Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)

body=part([(268,0),(680,0),(680,173),(579,174),(530,169),(508,179),(480,164),(459,151),(438,145),(419,143),(394,148),(375,153),(353,166),(324,177),(302,167),(282,154),(268,151)])
tail=part([(0,120),(268,120),(293,130),(293,151),(267,162),(240,177),(0,192)])
hind_far=part([(267,154),(300,155),(290,177),(262,179),(248,203),(232,220),(206,226),(204,211),(230,198),(243,172)])
hind_upper=part([(303,155),(330,153),(353,162),(335,178),(307,190),(294,211),(272,210),(273,191),(288,172)])
hind_lower=part([(273,202),(295,201),(298,234),(328,240),(333,254),(276,260),(270,236)])
front_far=part([(520,168),(541,173),(574,175),(581,191),(587,213),(577,226),(562,222),(553,203),(552,193),(519,194)])
front_upper=part([(472,154),(502,156),(516,182),(539,202),(526,218),(490,203),(477,189)])
front_lower=part([(519,201),(539,199),(560,223),(582,229),(590,243),(574,250),(551,241),(529,223)])
frames=[]
# Bone lengths never change: bend at the knee/elbow, not scale the leg.
HL1=math.hypot(285-322,207-166);HL2=math.hypot(290-285,242-207)
FL1=math.hypot(527-492,209-169);FL2=math.hypot(567-527,235-209)
SX=[.97,1.0,1.03,1.02,.99,.96]
FLAT=[0,.35,1,.70,.20,0]
BOB=[10,-5,-32,-14,4,12]
# Angles measured from downward: negative reaches back, positive reaches forward.
HA=[25,-40,-78,-45,25,48]
HB=[-30,-55,-85,55,-65,-100]
FA=[-15,25,68,32,-12,-40]
FB=[70,110,80,18,-25,100]
length_checks=[]
for f in range(6):
    phase=2*math.pi*f/6;sx=SX[f];flat=FLAT[f];bob=BOB[f]
    def compress(x):return 1-.50*flat*math.exp(-((x-390)/105)**2)
    def joint(x,y):return np.array([430+(x-430)*sx,150+(y-150)*compress(x)+bob])
    def endpoint(a,length,angle):
        t=math.radians(angle)
        return a+length*np.array([math.sin(t),math.cos(t)])
    pose=Image.new('RGBA',(W,H))
    # Bend each vertical slice of the back independently. The hunch flattens
    # while the head keeps its shape; no global vertical squash of the rat.
    mesh=[];tailmesh=[]
    for x in range(0,W,8):
        x1=min(W,x+8)
        def inv(xx,yy,istail=False):
            ox=430+(xx-430)/sx
            wave=12*max(0,1-ox/290)*math.sin(phase-ox/95) if istail else 0
            return (ox,150+(yy-150-bob-wave)/compress(ox))
        mesh.append(((x,0,x1,H),(*inv(x,0),*inv(x,H),*inv(x1,H),*inv(x1,0))))
        tailmesh.append(((x,0,x1,H),(*inv(x,0,True),*inv(x,H,True),*inv(x1,H,True),*inv(x1,0,True))))
    pose.alpha_composite(tail.transform((W,H),Image.Transform.MESH,tailmesh,Image.Resampling.BICUBIC))
    for far in (True,False):
        if not far:
            pose.alpha_composite(body.transform((W,H),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC))
        delta=np.array([-13,-6]) if far else np.array([0,0])
        offset=-5 if far else 0
        hip=joint(322,166)+delta
        knee=endpoint(hip,HL1,HA[f]+offset);foot=endpoint(knee,HL2,HB[f]+offset)
        shoulder=joint(492,169)+delta
        elbow=endpoint(shoulder,FL1,FA[f]+offset);paw=endpoint(elbow,FL2,FB[f]+offset)
        for a,b,L in [(hip,knee,HL1),(knee,foot,HL2),(shoulder,elbow,FL1),(elbow,paw,FL2)]:
            assert abs(np.linalg.norm(b-a)-L)<1e-8
        legs=Image.new('RGBA',(W,H))
        legs.alpha_composite(bone(hind_upper,(322,166),(285,207),hip,knee))
        legs.alpha_composite(bone(hind_lower,(285,207),(290,242),knee,foot))
        legs.alpha_composite(bone(front_upper,(492,169),(527,209),shoulder,elbow))
        legs.alpha_composite(bone(front_lower,(527,209),(567,235),elbow,paw))
        if far:
            pixels=np.array(legs);pixels[:,:,:3]=(pixels[:,:,:3]*.72).astype('uint8');legs=Image.fromarray(pixels)
        pose.alpha_composite(legs)
    frame=Image.new('RGBA',(256,128))
    small=pose.resize((256,113),Image.Resampling.LANCZOS)
    frame.alpha_composite(small,(0,7));frames.append(frame)
sheet=Image.new('RGBA',(1536,128));preview=[]
for i,fr in enumerate(frames):
    sheet.alpha_composite(fr,(i*256,0))
    bg=Image.new('RGB',(256,128),(27,30,36));bg.paste(fr,(0,0),fr)
    preview.append(bg.resize((768,384),Image.Resampling.NEAREST))
sheet.save(ROOT/'rat_run_right6.png')
preview[0].save(ROOT/'rat_run_right6.gif',save_all=True,append_images=preview[1:],duration=[100]*6,loop=0,disposal=2)
print('Six bounding-run frames: push-off, airborne extension, landing, gathering; 10 fps.')
