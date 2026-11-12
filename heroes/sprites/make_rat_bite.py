from pathlib import Path
from PIL import Image,ImageDraw
import math
R=Path(__file__).resolve().parent
for direction,w,h,nose,vec in [('right',256,128,(231,66),(1,0)),('down',192,256,(99,204),(0,1)),('up',160,256,(80,52),(0,-1))]:
 src=Image.open(R/f'rat_run_{direction}6.png').convert('RGBA').crop((0,0,w,h))
 sheet=Image.new('RGBA',(w*4,h));fx=Image.new('RGBA',sheet.size);pre=[]
 for i,shift in enumerate([-3,7,12,0]):
  fr=Image.new('RGBA',(w,h));dx,dy=vec[0]*shift,vec[1]*shift;fr.alpha_composite(src,(dx,dy))
  x,y=nose[0]+dx,nose[1]+dy;d=ImageDraw.Draw(fr)
  if i in (1,2) and direction!='up':
   if direction=='right':
    d.polygon([(x-13,y+2),(x+1,y+5),(x-10,y+12)],fill=(22,9,15,255))
    d.polygon([(x-10,y+3),(x-6,y+4),(x-8,y+9)],fill=(199,194,182,255))
   else:
    d.ellipse((x-7,y-4,x+7,y+4),fill=(22,9,15,255))
    for xx in (x-5,x+3):d.polygon([(xx,y-3),(xx+3,y-3),(xx+1,y+2)],fill=(199,194,182,255))
  ef=Image.new('RGBA',(w,h));ed=ImageDraw.Draw(ef)
  if i in (1,2):
   # A compact tapered slash, curved around the muzzle, not a light halo.
   vx,vy=vec;px,py=-vy,vx
   pts=[]
   for j in range(17):
    t=-1+j/8;forward=8+8*(1-t*t)
    pts.append((x+vx*forward+px*t*18,y+vy*forward+py*t*18))
   for j in range(15,-1,-1):
    t=-1+j/8;forward=8+8*(1-t*t)-4*(1-t*t)
    pts.append((x+vx*forward+px*t*18,y+vy*forward+py*t*18))
   ed.polygon(pts,fill=(242,241,235,230 if i==1 else 170))
  sheet.alpha_composite(fr,(i*w,0));fx.alpha_composite(ef,(i*w,0))
  fr.alpha_composite(ef);bg=Image.new('RGBA',(w,h),(27,30,36,255));bg.alpha_composite(fr);pre.append(bg.convert('RGB').resize((w*3,h*3)))
 sheet.save(R/f'rat_bite_{direction}4.png');fx.save(R/f'rat_bite_{direction}_fx4.png')
 pre[0].save(R/f'rat_bite_{direction}4.gif',save_all=True,append_images=pre[1:],duration=90,loop=0)
# Left is an exact frame-by-frame mirror.
for suffix in ['4','_fx4']:
 src=Image.open(R/f'rat_bite_right{suffix}.png');out=Image.new('RGBA',src.size)
 for i in range(4):out.paste(src.crop((i*256,0,(i+1)*256,128)).transpose(Image.Transpose.FLIP_LEFT_RIGHT),(i*256,0))
 out.save(R/f'rat_bite_left{suffix}.png')
