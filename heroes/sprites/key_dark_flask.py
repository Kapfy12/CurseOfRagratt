from PIL import Image, ImageFilter
import numpy as np
from collections import deque, Counter

def key_on_black(path, thr=6, feather=0.8):
    """Кейинг на чёрном фоне. Полупрозрачное тёмное стекло остаётся телом,
    а «протекания» фона (мелкие дыры, где яркость 0-2) убираются:
    берём только крупные связные области объекта и заполняем дыры."""
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    lum = a @ np.array([0.299, 0.587, 0.114])

    solid = (lum > thr)
    # связные компоненты «не-фона»: объект почти наверняка самая большая
    lab = np.zeros((h, w), np.int32)
    best, best_area = 0, 0
    cur = 0
    for sy in range(0, h, 2):
        for sx in range(0, w, 2):
            if solid[sy, sx] and lab[sy, sx] == 0:
                cur += 1
                q = deque([(sx, sy)]); lab[sy, sx] = cur
                area = 0
                while q:
                    x, y = q.popleft(); area += 1
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if 0 <= nx < w and 0 <= ny < h and solid[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur; q.append((nx, ny))
                if area > best_area:
                    best_area, best = area, cur
    body = (lab == best)

    # дыры внутри силуэта: заливаем от рамки по «не-body», что не дотянулись
    inv = ~body
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h-1))
    for y in range(h):
        q.append((0, y)); q.append((w-1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y, x] or not inv[y, x]:
            continue
        seen[y, x] = True
        q.extend(((x+1,y),(x-1,y),(x,y+1),(x,y-1)))
    filled = ~seen                      # тело + внутренние дыры

    alpha = np.where(filled, 255, 0).astype(np.float32)
    al = Image.fromarray(alpha.astype(np.uint8)).filter(ImageFilter.GaussianBlur(feather))
    out = im.convert('RGBA'); out.putalpha(al)
    return out

if __name__ == '__main__':
    o = key_on_black('/home/user/heroes/props_src/flask_dark_raw.png')
    box = o.getbbox(); print('bbox', box)
    o = o.crop(box); print('size', o.size, 'aspect %.3f' % (o.width/o.height))
    o.save('/tmp/flask_dark_cut.png')
    bg = Image.new('RGB', (o.width+20, o.height+20), (70,62,48))
    bg.paste(o, (10,10), o)
    bg.resize((bg.width//2, bg.height//2), Image.LANCZOS).save('/tmp/fd_cut_view.png')
