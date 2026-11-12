"""Пиксельные спрайты воина в духе RotMG: 16x16, 4 направления, 3 кадра."""
from PIL import Image, ImageDraw

W = H = 16
K=(12,14,17); H1=(196,206,219); H2=(126,136,149)
C=(176,50,38); SK=(214,160,113); SK2=(166,112,70)
A=(140,149,160); A2=(84,91,100)
T=(161,50,41);  T2=(106,27,21)
BL=(230,237,246); BL2=(150,163,177)
G=(199,160,37); L=(72,56,34); L2=(46,35,21)

def warrior(direction, frame):
    im = Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    bob = 1 if frame==2 else 0
    if direction in ('down','up'):
        # шлем
        d.rectangle([4,2+bob,11,6+bob], fill=K)
        d.rectangle([5,3+bob,10,5+bob], fill=H1)
        d.rectangle([6,3+bob,9,3+bob],  fill=H2)
        # гребень
        d.rectangle([7,0+bob,8,1+bob], fill=C)
        d.rectangle([6,1+bob,9,1+bob], fill=C)
        # лицо / затылок
        if direction=='down':
            d.rectangle([5,5+bob,10,6+bob], fill=SK)
            d.point((6,5+bob), fill=K); d.point((9,5+bob), fill=K)
        else:
            d.rectangle([5,5+bob,10,6+bob], fill=H2)
        # торс
        d.rectangle([3,7+bob,12,12+bob], fill=K)
        d.rectangle([4,8+bob,11,11+bob], fill=A)
        d.rectangle([4,11+bob,11,11+bob], fill=A2)
        # наплечники
        d.rectangle([2,8+bob,3,10+bob], fill=H2)
        d.rectangle([12,8+bob,13,10+bob], fill=H2)
        # табард
        d.rectangle([6,8+bob,9,13+bob], fill=T)
        d.rectangle([7,9+bob,8,11+bob], fill=G)
        d.rectangle([6,12+bob,9,13+bob], fill=T2)
        # руки
        d.point((3,11+bob), fill=SK2); d.point((12,11+bob), fill=SK2)
        # ноги
        off = 1 if frame==1 else (-1 if frame==2 else 0)
        d.rectangle([4+off,13,6+off,15], fill=L)
        d.rectangle([9-off,13,11-off,15], fill=L2)
        d.point((4+off,15), fill=K); d.point((11-off,15), fill=K)
        # меч справа
        d.rectangle([14,3,14,9], fill=BL)
        d.rectangle([15,4,15,9], fill=BL2)
        d.rectangle([13,10,15,10], fill=G)
        d.point((14,11), fill=SK2)
        d.point((15,11), fill=SK2)
    else:  # профиль вправо
        d.rectangle([4,2+bob,10,6+bob], fill=K)
        d.rectangle([5,3+bob,9,5+bob], fill=H1)
        d.rectangle([8,3+bob,9,3+bob], fill=H2)
        d.rectangle([8,0+bob,9,1+bob], fill=C)
        d.rectangle([9,1+bob,10,1+bob], fill=C)
        # лицо вправо (нос на x=11)
        d.rectangle([8,4+bob,10,6+bob], fill=SK)
        d.point((8,5+bob), fill=K)
        d.point((10,5+bob), fill=SK2)
        # торс
        d.rectangle([3,7+bob,10,12+bob], fill=K)
        d.rectangle([4,8+bob,9,11+bob], fill=A)
        d.rectangle([4,11+bob,9,11+bob], fill=A2)
        d.point((3,8+bob), fill=H2); d.point((3,9+bob), fill=H2)
        # табард сбоку
        d.rectangle([6,8+bob,9,13+bob], fill=T)
        d.rectangle([6,12+bob,9,13+bob], fill=T2)
        # рука с мечом вперёд
        d.rectangle([9,10+bob,10,11+bob], fill=SK2)
        d.rectangle([11,9+bob,12,10+bob], fill=SK)
        for i in range(4):
            d.point((12+i, 8-i), fill=BL if i<3 else G)
            d.point((13+i, 8-i), fill=BL2 if i<3 else G)
        d.rectangle([11,10,11,10], fill=G)
        # ноги
        off = 1 if frame==1 else (-1 if frame==2 else 0)
        d.rectangle([4+off,13,6+off,15], fill=L)
        d.rectangle([8-off,13,10-off,15], fill=L2)
        d.point((4+off,15), fill=K); d.point((10-off,15), fill=K)
    return im

def mirror(im): return im.transpose(Image.FLIP_LEFT_RIGHT)

def spritesheet():
    # 3 строки (вниз/вверх/вправо) x 3 кадра, слева — idle
    sheet = Image.new('RGBA', (16*3, 16*3), (0,0,0,0))
    for r,direction in enumerate(('down','up','right')):
        for f in (0,1,2):
            sheet.alpha_composite(warrior(direction,f), (f*16, r*16))
    return sheet

if __name__=='__main__':
    rows=[('down',None),('up',None),('right',None)]
    S=10
    sheet=Image.new('RGBA',(9*(W*S+10)+10, 3*(H*S+26)+10),(20,22,26,255))
    dr=ImageDraw.Draw(sheet)
    for r,(direction,_) in enumerate(rows):
        for f in (0,1,2):
            base=warrior(direction,f); mir=mirror(base)
            for k,im in enumerate((base,mir)):
                x=10+(f+k*3)*(W*S+10); y=10+r*(H*S+26)+16
                sheet.alpha_composite(im.resize((W*S,H*S),Image.NEAREST),(x,y))
                dr.text((x,y-12), f'{direction}_{f}'+(' L' if k else ''), fill=(203,185,143))
    sheet.save('/home/user/heroes/sprites/preview.png')
    spritesheet().save('/home/user/heroes/sprites/warrior_frames.png')
    print('ok')
