from PIL import Image, ImageFilter
import numpy as np
from collections import deque

def key_glass(path, white=232, sat_max=0.10):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = (mx-mn)/np.maximum(mx, 1)
    lum = a @ np.array([0.299, 0.587, 0.114])

    bg = ((lum > white) & (sat < sat_max)).astype(np.uint8)
    # заливка от рамки — светлые блики ВНУТРИ стекла не выедаются
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h-1))
    for y in range(h):
        q.append((0, y)); q.append((w-1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y, x] or not bg[y, x]:
            continue
        seen[y, x] = True
        q.extend(((x+1, y), (x-1, y), (x, y+1), (x, y-1)))

    # второй проход по нижней четверти: там светлый пол студии (~220-235),
    # который при пороге 232 остаётся непрозрачным
    bg2 = ((lum > 150) & (sat < 0.10)).astype(np.uint8)
    bg2[:int(h*0.86), :] = 0
    q = deque()
    for x in range(w):
        q.append((x, h-1))
    for y in range(int(h*0.86), h):
        q.append((0, y)); q.append((w-1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y, x] or not (bg[y, x] or bg2[y, x]):
            continue
        seen[y, x] = True
        q.extend(((x+1, y), (x-1, y), (x, y+1), (x, y-1)))

    alpha = np.where(seen, 0, 255).astype(np.uint8)
    # студийная тень/овал внизу: серое и светлое, привязанное к фону
    zone = np.zeros((h, w), bool); zone[int(h*0.80):, :] = True
    shadow = zone & (sat < 0.10) & (lum > 70) & (lum < white+8)
    # тень трогаем только если она дотягивается до прозрачных пикселей
    near = np.asarray(Image.fromarray((alpha == 0).astype(np.uint8)*255)
                      .filter(ImageFilter.MaxFilter(9))) > 0
    shadow = shadow & near
    alpha[shadow] = 0
    # «студийный пол» под подставкой: светлая нейтральная масса, которая
    # дотягивается до прозрачного края — в игре это читается как белое пятно
    low = np.zeros((h, w), bool); low[int(h*0.86):, :] = True
    floorish = (sat < 0.16) & (lum > 42)
    kill = low & floorish & (alpha > 0) & near
    # и то же по цвету: дорисовываем прозрачность, пока фронт «пола» не встанет
    for _ in range(40):
        frontier = np.asarray(Image.fromarray((kill*255).astype(np.uint8))
                              .filter(ImageFilter.MaxFilter(3))) > 0
        add = low & floorish & (alpha > 0) & (frontier | (np.asarray(
            Image.fromarray(((alpha == 0)*255).astype(np.uint8))
            .filter(ImageFilter.MaxFilter(3))) > 0))
        if not (add & ~kill).any():
            break
        kill |= add
    alpha[kill] = 0
    # мягкая кромка 1 px
    al = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.6))
    out = im.convert('RGBA'); out.putalpha(al)
    return out

if __name__ == '__main__':
    out = key_glass('/home/user/heroes/props_src/flask_green_raw2.png')
    box = out.getbbox(); print('bbox', box)
    out = out.crop(box); print('size', out.size, 'aspect %.3f' % (out.width/out.height))
    out.save('/tmp/flask_green_cut.png')
    a = np.asarray(out.split()[3])
    H, W = a.shape
    for y in range(0, H, max(1, H//60)):
        print('%4d %s' % (y, ''.join('#' if a[y, x] > 140 else ('+' if a[y, x] > 40 else '.') for x in range(0, W, max(1, W//60)))))
