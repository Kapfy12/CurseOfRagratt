import sys
sys.path.insert(0,'/home/user/heroes/sprites')
from PIL import Image, ImageFilter
import numpy as np
from make_props import cut_bg

def drop_studio_shadow(rgba):
    """Студийная тень под подставкой — нейтрально-серая и полупрозрачная.
    В игре она читается как светлое пятно на столе, поэтому убираем её:
    своя тень рисуется в drawAlchemist."""
    a = np.array(rgba).astype(np.int32)
    px = a[...,:3]
    mx, mn = px.max(axis=2), px.min(axis=2)
    sat = (mx-mn)/np.maximum(mx,1)
    lum = (a[...,0]*299+a[...,1]*587+a[...,2]*114)//1000
    h = a.shape[0]
    zone = np.zeros_like(sat, dtype=bool)
    zone[int(h*0.885):, :] = True           # только под подставкой, не трогаем блики стекла
    grey = (sat < 0.12) & (lum > 35) & zone
    a[...,3] = np.where(grey, 0, a[...,3])
    return Image.fromarray(a.astype(np.uint8),'RGBA')

def clean_studio_glow(rgba):
    """cut_bg иногда оставляет студийную подсветку/овал под подставкой:
    это единственное светлое и почти нейтральное пятно в кадре — гасим."""
    a = np.array(rgba).astype(np.int32)
    r,g,b,al = a[...,0],a[...,1],a[...,2],a[...,3]
    lum = (r*299+g*587+b*114)//1000
    sat = (a[...,:3].max(axis=2)-a[...,:3].min(axis=2))/np.maximum(a[...,:3].max(axis=2),1)
    glow = (lum>120) & (sat<0.14)
    al = np.where(glow, 0, al)
    a[...,3] = al
    return Image.fromarray(a.astype(np.uint8),'RGBA')

def npc_pipeline(rgba, TH=190, colors=210, blur=0.3):
    tw = max(1, round(rgba.width*TH/rgba.height))
    small = rgba.resize((tw, TH), Image.LANCZOS)
    rgb = small.convert('RGB').filter(ImageFilter.GaussianBlur(blur))
    rgb = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                       dither=Image.Dither.FLOYDSTEINBERG).convert('RGB')
    out = rgb.convert('RGBA')
    al = rgba.getchannel('A').resize((tw,TH), Image.LANCZOS).filter(ImageFilter.MinFilter(3))
    out.putalpha(al)
    return out

if __name__ == '__main__':
    rgba = cut_bg(Image.open('/home/user/heroes/props_src/flask_raw.png'))
    rgba = rgba.crop(rgba.getbbox())
    rgba = drop_studio_shadow(clean_studio_glow(rgba))
    rgba.save('/tmp/flask_glass_cut.png')
    prev = Image.new('RGB',(760,320),(38,36,30)); x=6
    for TH in (190,200,210):
        im = npc_pipeline(rgba, TH=TH)
        print(TH, im.size)
        prev.paste(im,(x,6),im); x+=im.width+10
    prev.paste(Image.open('/home/user/heroes/game_assets/npc_alchemist.png'),(x,6),
               Image.open('/home/user/heroes/game_assets/npc_alchemist.png'))
    prev.resize((prev.width*2,prev.height*2),Image.NEAREST).save('/tmp/glass_var2.png')

def grade_liquid(rgba, vk=0.60, sk=0.50, tint=(1.10, 1.0, 0.66)):
    """Приглушает неоновую зелень жидкости до оливково-изумрудного тона
    колбы в руке алхимика (медиана 61,84,40). Стекло, пробка и дерево
    не затрагиваются — правится только насыщенно-зелёное."""
    src = rgba.convert('RGB')
    hsv = np.array(src.convert('HSV')).astype(np.float32)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    green = (H > 50) & (H < 130) & (S > 70)
    V = np.where(green, V * vk, V)
    S = np.where(green, S * sk, S)
    out = Image.fromarray(np.dstack([H, S, V]).astype(np.uint8), 'HSV').convert('RGB')
    a = np.array(out).astype(np.float32)
    a = np.where(green[..., None], a * np.array(tint), a)
    res = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')
    res.putalpha(rgba.getchannel('A'))
    return res
