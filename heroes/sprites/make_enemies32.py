#!/usr/bin/env python3
"""Враги в 32x32: та же анатомия и та же анимация шага, но вдвое плотнее.

Раньше лист собирался из символьных сеток 16x16: один символ = один
экранный пиксель, деталей на тело почти не оставалось. Здесь каждая
клетка сетки превращается в блок 2x2, а внутри блока рисуется светотень
(верхняя кромка светлеет, нижняя уходит в тень, силуэт получает обводку
в 1 настоящий пиксель). Поэтому меч, рёбра, капюшон и лапы читаются
вдвое подробнее, а силуэты и кадры шага остаются ровно там же, где были:
игровая логика (строки, кадры, зеркало) не меняется вообще.

Лист: 3 кадра x 3 направления, клетка 32x32.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_enemies as E  # noqa: E402

OUT = os.path.join('/home/user', 'heroes', 'sprites')


def palette_for(kind):
    """Палитра существа плюс её световые ступени: 5 тонов на цвет."""
    base = [c for c in E.PAL[kind].values() if c]
    ramp = []
    for c in base:
        for k in (0.62, 0.80, 1.0, 1.20, 1.42):
            ramp.append(tuple(min(255, max(0, int(v * k))) for v in c))
    return np.array(sorted(set(ramp)), dtype=np.int32)


def snap(rgb, pal):
    """Ближайший цвет палитры — как в спрайтах героя."""
    flat = rgb.reshape(-1, 3).astype(np.int32)
    d = ((flat[:, None, :] - pal[None, :, :].astype(np.int32)) ** 2).sum(-1)
    return pal[d.argmin(-1)].reshape(rgb.shape).astype(np.uint8)


def upscale2(im, kind):
    """16x16 -> 32x32: блоки 2x2 + светотень по соседям + обводка."""
    a = np.asarray(im).astype(np.int16)
    src = a[:, :, :3].astype(np.float32)
    alpha = a[:, :, 3] > 40
    h, w = alpha.shape

    out = np.zeros((h * 2, w * 2, 3), np.float32)
    oa = np.zeros((h * 2, w * 2), bool)

    def opaque(x, y):
        return 0 <= x < w and 0 <= y < h and alpha[y, x]

    for y in range(h):
        for x in range(w):
            if not alpha[y, x]:
                continue
            c = src[y, x]
            up, dn = not opaque(x, y - 1), not opaque(x, y + 1)
            lf, rt = not opaque(x - 1, y), not opaque(x + 1, y)
            # четыре настоящих пикселя внутри блока 2x2
            for j in (0, 1):
                for i in (0, 1):
                    k = 1.0
                    if up and j == 0:
                        k *= 1.26                       # верхняя кромка ловит свет
                    elif dn and j == 1:
                        k *= 0.74                       # низ уходит в тень
                    else:
                        k *= 1.06 if j == 0 else 0.92   # объём внутри блока
                    if lf and i == 0:
                        k *= 1.05
                    elif rt and i == 1:
                        k *= 0.90
                    yy, xx = y * 2 + j, x * 2 + i
                    out[yy, xx] = np.clip(c * k, 0, 255)
                    oa[yy, xx] = True

    # обводка в 1 настоящий пиксель: тёмный контур вокруг силуэта
    dark = np.clip(src.mean(axis=2).mean() * 0.16, 8, 30)
    ring = np.zeros_like(oa)
    for y in range(oa.shape[0]):
        for x in range(oa.shape[1]):
            if oa[y, x]:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < oa.shape[0] and 0 <= nx < oa.shape[1] and oa[ny, nx]:
                        ring[y, x] = True
                        break
                if ring[y, x]:
                    break
    out[ring] = np.array([dark, dark * 0.92, dark * 0.86])

    rgb = snap(np.clip(out, 0, 255).astype(np.uint8), palette_for(kind))
    out_alpha = np.where(oa | ring, 255, 0).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, out_alpha]), 'RGBA')


def sheet_for(kind, down, up, side):
    cell = 32
    sheet = Image.new('RGBA', (cell * 3, cell * 3), (0, 0, 0, 0))
    for r, (direction, rows) in enumerate((('down', down), ('up', up), ('right', side))):
        for f in (0, 1, 2):
            im = E.render(rows, E.PAL[kind])
            E.draw_legs(im, kind, direction, f)
            E.add_gear(im, kind, direction)
            sheet.alpha_composite(upscale2(im, kind), (f * cell, r * cell))
    return sheet


def make_all():
    return {
        'rat':  sheet_for('rat',  E.RAT_DOWN,  E.RAT_UP,  E.RAT_SIDE),
        'cult': sheet_for('cult', E.CULT_DOWN, E.CULT_UP, E.CULT_SIDE),
        'skel': sheet_for('skel', E.SKEL_DOWN, E.SKEL_UP, E.SKEL_SIDE),
    }


if __name__ == '__main__':
    from PIL import ImageDraw
    sheets = make_all()
    Z = 6
    prev = Image.new('RGB', ((96 * Z + 20) * 3 + 20, 96 * Z + 60), (24, 22, 20))
    d = ImageDraw.Draw(prev)
    for i, (k, im) in enumerate(sheets.items()):
        im.save(os.path.join(OUT, f'{k}_frames32.png'))
        big = im.resize((96 * Z, 96 * Z), Image.NEAREST)
        prev.paste(big, (20 + i * (96 * Z + 20), 40), big)
        d.text((20 + i * (96 * Z + 20), 12), k + ' 32x32', fill=(198, 182, 150))
    prev.save(os.path.join(OUT, 'enemies32_preview.png'))
    print('ok', {k: v.size for k, v in sheets.items()})
