"""Upward rat bound with separate original limbs and strong forward paw reach."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import math
from rat_remove_fringe import clean_fringe
ROOT=Path(__file__).resolve().parent
src=clean_fringe(Image.open(ROOT/'rat_run_up.png').convert('RGBA'))
W,H=src.size
OW,OH=W+200,H+200
PAD=np.array([100.,100.])

def part(poly):
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255)
    a=np.array(src);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));return Image.fromarray(a)

def move_limb(im,root,tip,dest,angle,scale=1):
    root=np.array(root,float);tip=np.array(tip,float);dest=np.array(dest,float)+PAD
    length=np.linalg.norm(tip-root)*scale;t=math.radians(angle)
    end=dest+length*np.array([math.sin(t),math.cos(t)])
    q=complex(*(end-dest))/complex(*(tip-root))
    matrix=np.array([[q.real,-q.imag],[q.imag,q.real]])
    inv=np.linalg.inv(matrix);off=root-inv@dest
    return im.transform((OW,OH),Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)

frontpoly=[(113,250),(157,288),(137,345),(105,395),(63,430),(54,460),(16,470),(10,433),(34,410),(55,373),(78,315)]
hindpoly=[(99,575),(153,625),(143,686),(116,726),(84,763),(61,791),(20,777),(17,737),(55,741),(81,705),(87,644)]
fronts=[part(frontpoly),part([(W-x,y) for x,y in frontpoly])]
hinds=[part(hindpoly),part([(W-x,y) for x,y in hindpoly])]
# Forepaw size is independent of the longitudinal reach of the arm.
hands=[]
handpoly=[(19,418),(63,418),(65,446),(53,471),(12,474),(8,438)]
for side in (0,1):
    poly=handpoly if side==0 else [(W-x,y) for x,y in handpoly]
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255)
    pixels=np.array(fronts[side]);cut=np.array(mask)>0
    hand=pixels.copy();hand[~cut]=0;hands.append(Image.fromarray(hand))
    pixels[cut]=0;fronts[side]=Image.fromarray(pixels)

# Separate rear paws from shins: their toes point forward independently of stride.
feet=[]
footpoly=[(26,723),(61,736),(87,751),(78,782),(53,797),(16,778),(15,739)]
for side in (0,1):
    poly=footpoly if side==0 else [(W-x,y) for x,y in footpoly]
    mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(poly,fill=255)
    pixels=np.array(hinds[side]);cut=np.array(mask)>0
    foot=pixels.copy();foot[~cut]=0;feet.append(Image.fromarray(foot))
    pixels[cut]=0;hinds[side]=Image.fromarray(pixels)

body=part([(200,0),(259,45),(279,105),(275,170),(271,219),(302,273),(307,335),(297,409),(315,480),(315,565),(290,640),(259,700),(209,730),(156,705),(124,650),(101,575),(96,495),(115,430),(115,345),(110,300),(145,220),(145,145),(130,90)])
tail=part([(145,705),(260,705),(265,H),(80,H),(80,900),(140,820)])
# Torso shortens while the hind feet are drawn toward the head.
source_y=np.array([0,180,300,600,730,1180],float)
poses=[
 [170,300,370,505,650,1180],
 [95,240,335,550,700,1180],
 [25,190,310,610,750,1180],
 [45,205,320,590,730,1180],
 [125,270,355,525,670,1180],
 [180,310,380,500,640,1180],
]
# Forward is upward on screen. The two pairs alternate: rear feet gather
# towards the head while forelegs withdraw; then forepaws reach past the nose.
front_reach=[0,.40,1,.85,.30,0]
rear_angle=[-173,-145,-55,-75,-155,-175]
frames=[]
for f,dest_y in enumerate(poses):
    dest_y=np.array(dest_y,float)
    def joint(x,y):return np.array([x,np.interp(y,source_y,dest_y)])
    pose=Image.new('RGBA',(OW,OH))
    mesh=[]
    for y in range(0,OH,12):
        y1=min(OH,y+12)
        def inv(x,yy):
            oy=np.interp(yy-100,dest_y,source_y,left=-100,right=H+100)
            wave=13*max(0,(oy-730)/(H-730))*math.sin(f*math.pi/3+oy/130)
            return x-100-wave,oy
        mesh.append(((0,y,OW,y1),(*inv(0,y),*inv(0,y1),*inv(OW,y1),*inv(OW,y))))
    pose.alpha_composite(tail.transform((OW,OH),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC))
    rear=Image.new('RGBA',(OW,OH));fore=Image.new('RGBA',(OW,OH))
    for side in (0,1):
        sign=1 if side==0 else -1
        root=(122,306) if side==0 else (W-122,306)
        tip=(34,445) if side==0 else (W-34,445)
        shoulder=joint(*root)
        reach=front_reach[f]
        # A nearly longitudinal paw track, starting at the original location.
        lane=140 if side==0 else W-140
        target=np.array([tip[0]*(1-reach)+lane*reach,
            (shoulder[1]+tip[1]-root[1])*(1-reach)+(dest_y[0]-30)*reach])
        v=target-shoulder
        angle=math.degrees(math.atan2(v[0],v[1]))
        scale=np.linalg.norm(v)/math.dist(root,tip)
        # Stretch along the arm only; do not magnify its width or the paw.
        axis=(np.array(tip)-root)/math.dist(root,tip)
        perp=np.array([-axis[1],axis[0]])
        direction=v/np.linalg.norm(v);normal=np.array([-direction[1],direction[0]])
        matrix=scale*np.outer(direction,axis)+(1-.25*reach)*np.outer(normal,perp)
        inv=np.linalg.inv(matrix);off=np.array(root)-inv@(shoulder+PAD)
        arm=fronts[side].transform((OW,OH),Image.Transform.AFFINE,
            (*inv[0],off[0],*inv[1],off[1]),Image.Resampling.BICUBIC)
        fore.alpha_composite(arm)
        wrist=np.array([43 if side==0 else W-43,427.])
        dest_wrist=shoulder+matrix@(wrist-root)
        # At full forward reach the hand is 55% of its original size.
        fore.alpha_composite(move_limb(hands[side],wrist,tip,dest_wrist,angle,1-.45*reach))
        root=(117,617) if side==0 else (W-117,617)
        tip=(54,767) if side==0 else (W-54,767)
        scale=[1.15,1.08,1.0,1.0,1.10,1.15][f]
        angle=rear_angle[f]*sign
        hip=joint(*root)
        rear.alpha_composite(move_limb(hinds[side],root,tip,hip,angle,scale))
        wrist=np.array([77 if side==0 else W-77,751.])
        toe=np.array([35 if side==0 else W-35,754.])
        t=math.radians(angle)
        end=math.dist(root,tip)*scale*np.array([math.sin(t),math.cos(t)])
        q=complex(*end)/complex(*(np.array(tip)-root))
        v=complex(*(wrist-root))*q
        dest_wrist=hip+np.array([v.real,v.imag])
        # Toe direction stays screen-up; no sideways/backward-facing hind feet.
        rear.alpha_composite(move_limb(feet[side],wrist,toe,dest_wrist,180,1))
    # The rear legs pass under the torso, but the paws remain visible beside neck.
    pose.alpha_composite(rear)
    mesh=[]
    for y in range(0,OH,12):
        y1=min(OH,y+12)
        def inv(x,yy):return x-100,np.interp(yy-100,dest_y,source_y,left=-100,right=H+100)
        mesh.append(((0,y,OW,y1),(*inv(0,y),*inv(0,y1),*inv(OW,y1),*inv(OW,y))))
    pose.alpha_composite(body.transform((OW,OH),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC))
    pose.alpha_composite(fore)
    pose.thumbnail((160,256),Image.Resampling.LANCZOS)
    frame=Image.new('RGBA',(160,256));frame.alpha_composite(pose,((160-pose.width)//2,0));frames.append(frame)
sheet=Image.new('RGBA',(160*6,256));preview=[]
for i,fr in enumerate(frames):
    sheet.alpha_composite(fr,(i*160,0))
    bg=Image.new('RGB',fr.size,(27,30,36));bg.paste(fr,(0,0),fr)
    preview.append(bg.resize((480,768),Image.Resampling.NEAREST))
sheet.save(ROOT/'rat_run_up6.png')
preview[0].save(ROOT/'rat_run_up6.gif',save_all=True,append_images=preview[1:],duration=[100]*6,loop=0,disposal=2)
print('Six frames, 160x256, 10 fps, separate fore/hind reach.')
