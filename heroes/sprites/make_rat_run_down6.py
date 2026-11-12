"""Downward bounding rat: four articulated limbs with constant bone lengths."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import math
from rat_remove_fringe import clean_fringe
ROOT=Path(__file__).resolve().parent
src=clean_fringe(Image.open(ROOT/'rat_run_down.png').convert('RGBA'))
W,H=src.size
OUT=(W+120,H+120)
PAD=np.array([60.,60.])

def part(poly):
    m=Image.new('L',(W,H));ImageDraw.Draw(m).polygon(poly,fill=255)
    a=np.array(src);a[:,:,3]=np.minimum(a[:,:,3],np.array(m));return Image.fromarray(a)

def bone(im,a,b,c,d):
    a=np.array(a,float);b=np.array(b,float);c=np.array(c,float)+PAD;d=np.array(d,float)+PAD
    q=complex(*(d-c))/complex(*(b-a))
    assert abs(abs(q)-1)<1e-7, 'Limb scale changed'
    mat=np.array([[q.real,-q.imag],[q.imag,q.real]]);inv=np.linalg.inv(mat);off=a-inv@c
    return im.transform(OUT,Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)

def end(p,a,b,angle):
    length=math.dist(a,b);t=math.radians(angle)
    return p+length*np.array([math.sin(t),math.cos(t)])

tail=part([(170,0),(335,0),(335,244),(206,252),(183,223)])
body=part([(184,232),(280,226),(333,256),(369,306),(369,349),(349,385),(322,409),(336,463),(352,508),(348,561),(323,599),(280,620),(245,627),(210,607),(174,577),(159,544),(168,488),(185,442),(195,411),(167,380),(135,354),(130,311),(158,268)])
hlU=part([(131,300),(173,316),(172,360),(142,373),(110,365),(92,337),(79,314),(91,270),(114,266)])
hlL=part([(85,299),(117,315),(97,346),(76,382),(47,405),(16,397),(16,365),(52,329)])
hrU=part([(337,325),(374,329),(388,321),(407,321),(421,354),(400,390),(370,410),(344,392)])
hrL=part([(382,339),(407,331),(430,380),(457,405),(460,446),(440,450),(410,427),(395,392)])
flU=part([(172,555),(198,558),(216,600),(211,638),(191,643),(179,611)])
flL=part([(188,618),(214,616),(225,652),(247,678),(242,706),(218,708),(198,687),(189,654)])
frU=part([(311,559),(340,553),(337,591),(318,634),(296,632),(298,603)])
frL=part([(297,616),(320,625),(310,654),(309,676),(287,683),(265,673),(272,644)])
frames=[]
for f in range(6):
    phase=2*math.pi*f/6
    stretch=[.72,.88,1.12,1.04,.90,.76][f]
    bob=[14,0,-18,-5,8,16][f]
    bend=[-.04,.02,.12,.07,0,-.04][f]
    def waist(y):return 1-bend*math.exp(-((y-390)/110)**2)
    # Compress the torso longitudinally but retain the head's proportions.
    def forward_y(y):return 450+(min(y,500)-450)*stretch+bob+max(0,y-500)
    def inverse_y(y):
        neck=450+50*stretch+bob
        return 500+(y-neck) if y>neck else 450+(y-450-bob)/stretch
    def joint(x,y):return np.array([245+(x-245)*waist(y),forward_y(y)])
    pose=Image.new('RGBA',OUT)
    # Tail bends sideways around its root, with ample margin above the image.
    mesh=[]
    for y in range(0,OUT[1],12):
        y1=min(OUT[1],y+12)
        def inv(x,yy):
            oy=yy-60-bob-(stretch-1)*(240-450)
            shift=14*max(0,1-oy/240)*math.sin(phase+oy/65)
            return (x-60-shift,oy)
        mesh.append(((0,y,OUT[0],y1),(*inv(0,y),*inv(0,y1),*inv(OUT[0],y1),*inv(OUT[0],y))))
    pose.alpha_composite(tail.transform(OUT,Image.Transform.MESH,mesh,Image.Resampling.BICUBIC))
    # In the gathered pose hind legs reach forward beneath the belly, toward the head.
    ha=[8,-35,-65,-50,-15,6][f]
    hb=[0,-25,-90,-65,5,0][f]
    for im1,im2,a,b,c,side in [(hlU,hlL,(155,340),(106,307),(48,378),-1),(hrU,hrL,(354,365),(398,345),(437,421),1)]:
        hip=joint(*a);knee=end(hip,a,b,ha if side==-1 else -ha)
        paw=end(knee,b,c,hb if side==-1 else -hb)
        pose.alpha_composite(bone(im1,a,b,hip,knee));pose.alpha_composite(bone(im2,b,c,knee,paw))
    # Bend the waist locally; preserve head width, eyes, and slim silhouette.
    mesh=[]
    for y in range(0,OUT[1],10):
        y1=min(OUT[1],y+10)
        def inv(x,yy):
            oy=inverse_y(yy-60)
            return (245+(x-60-245)/waist(oy),oy)
        mesh.append(((0,y,OUT[0],y1),(*inv(0,y),*inv(0,y1),*inv(OUT[0],y1),*inv(OUT[0],y))))
    body_layer=body.transform(OUT,Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)
    fore_layer=Image.new('RGBA',OUT)
    # Front paws keep their original shape and orientation. Only uniform
    # scaling about the shoulder creates the tucked/extended appearance.
    fore_scale=[.42,.65,1.0,1.0,.75,.42][f]
    for im1,im2,a in [(flU,flL,(191,574)),(frU,frL,(325,573))]:
        limb=Image.new('RGBA',(W,H));limb.alpha_composite(im1);limb.alpha_composite(im2)
        shoulder=joint(*a)+PAD
        inv=1/fore_scale
        coeff=(inv,0,a[0]-shoulder[0]*inv,0,inv,a[1]-shoulder[1]*inv)
        fore_layer.alpha_composite(limb.transform(OUT,Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC))
    if f in (0,1,5):
        # Shortened forelegs sit beneath the chest without bending or rotating.
        pose.alpha_composite(fore_layer);pose.alpha_composite(body_layer)
    else:
        pose.alpha_composite(body_layer);pose.alpha_composite(fore_layer)
    frame=Image.new('RGBA',(192,256));small=pose.copy();small.thumbnail((192,256),Image.Resampling.LANCZOS)
    frame.alpha_composite(small,((192-small.width)//2,(256-small.height)//2));frames.append(frame)
sheet=Image.new('RGBA',(192*6,256));preview=[]
for i,fr in enumerate(frames):
    sheet.alpha_composite(fr,(i*192,0))
    bg=Image.new('RGB',fr.size,(27,30,36));bg.paste(fr,(0,0),fr)
    preview.append(bg.resize((384,512),Image.Resampling.NEAREST))
sheet.save(ROOT/'rat_run_down6.png')
preview[0].save(ROOT/'rat_run_down6.gif',save_all=True,append_images=preview[1:],duration=[100]*6,loop=0,disposal=2)
print('Down run: 6 frames, 192x256, 10 fps; rigid hind legs, front paws scale without bending.')
