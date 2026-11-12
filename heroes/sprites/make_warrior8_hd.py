#!/usr/bin/env python3
"""Воин 8 направлений, HD-версия: тот же силуэт на экране, втрое больше
настоящих пикселей.

Обычная сборка (make_warrior8.py) делает клетку 48x38 логических пикселей,
и каждый такой пиксель на экране растягивается в 3 x 3. Здесь всё то же
самое, но в SUP=3 раза плотнее: холст 144x114, блок-мода работает по блокам
1x1 (то есть пиксель в пиксель), поэтому ремешки, заклёпки и кромки доспеха
не схлопываются в один квадрат.

Итог: лист 432x912 = 8 строк по 3 кадра; в игре он рисуется в 1/3
логического масштаба — герой занимает те же 42x33 логических пикселя,
но каждый из них составлен из трёх настоящих пикселей по каждой оси.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_warrior_dirs import PAL, cut_white, grade_hi, to_image  # noqa: E402
from make_warrior8 import PAL8, ORDER, darken, to_palette_pal, bbox, load, foot_anchor  # noqa: E402

ROOT = '/home/user'
OUT = os.path.join(ROOT, 'heroes', 'sprites')

CW, CH = 48, 38          # логическая клетка (как в игре)
SUP = 3                  # плотность: настоящих пикселей на логический
H = 35                   # высота фигуры в ЛОГИЧЕСКИХ пикселях (как было)
SS = 8                   # суперсэмплинг исходного пре-рендера перед палитрой


def block(idx, alpha):
    """Уменьшение блоками SS x SS: 1152x912 -> 144x114. Каждый настоящий
    пиксель HD-кадра — это блок 8x8 суперсэмпла, цвет берётся по моде
    палитры, поэтому края остаются жёсткими."""
    h, w = idx.shape
    oh, ow = h // SS, w // SS
    res = np.zeros((oh, ow), np.int16)
    oka = np.zeros((oh, ow), bool)
    for y in range(oh):
        for x in range(ow):
            al = alpha[y * SS:(y + 1) * SS, x * SS:(x + 1) * SS]
            if (al > 110).mean() < 0.5:
                continue
            blk = idx[y * SS:(y + 1) * SS, x * SS:(x + 1) * SS][al > 110]
            if blk.size:
                vals, cnt = np.unique(blk, return_counts=True)
                res[y, x] = vals[cnt.argmax()]
                oka[y, x] = True
    return res, oka


def outline(idx, oka):
    """Мягкий контур: тёмный ободок по краю силуэта, но только там, где
    пиксель и правда граничит с фоном. На плотном холсте он может быть
    тоньше, чем раньше, поэтому берём его же палитровый нулевой индекс."""
    h, w = idx.shape
    res = idx.copy()
    ok = oka.copy()
    for y in range(h):
        for x in range(w):
            if oka[y, x]:
                continue
            near = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and oka[ny, nx]:
                        near = True
                        break
                if near:
                    break
            if near:
                res[y, x] = 0
                ok[y, x] = True
    return res, ok


def cell(img):
    """Один кадр: пре-рендер -> холст 144x114 -> палитра -> плотные пиксели."""
    x0, y0, x1, y1 = bbox(img)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    a = np.asarray(img)[:, :, 3]
    ys, xs = np.where(a > 40)
    ax = foot_anchor(xs, ys, y0, y1)          # центр по стопам, а не по мечу

    # холст в суперсэмплинге: 144x114 настоящих = 1152x912 до блок-моды
    cw, ch = CW * SUP * SS, CH * SUP * SS
    # фигура занимает H*SUP настоящих пикселей по высоте
    scale = (H * SUP * SS) / h
    bw, bh = max(1, round(w * scale)), max(1, round(h * scale))
    big = img.resize((bw, bh), Image.LANCZOS)
    foot_dx = (ax - x0) * scale
    left = int(round(cw * 0.5 - foot_dx))
    left = max(-9999, min(left, cw - bw))
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    canvas.paste(big, (left, ch - bh), big)

    idx, alpha = to_palette_pal(darken(grade_hi(canvas)), PAL8)
    small, oka = block(idx, alpha)
    return outline(small, oka)


def idle_frames(c0):
    """Второй и третий кадры шага: сдвиг по вертикали на 1 и 2 настоящих
    пикселя (в игре это 1/3 и 2/3 логического — мягче прежнего «дёрга»)."""
    out = [c0]
    for dy in (1, 2):
        out.append(np.roll(c0, -dy, axis=0))   # подъём корпуса = сдвиг вверх
    return out


def build():
    imgs = {k: load(k) for k in ORDER}
    cells = {}
    for k in ORDER:
        src = imgs.get(k)
        if src is None:
            continue
        if k == 'd1_down_right' and imgs.get('d7_down_left') is not None:
            src = imgs['d7_down_left'].transpose(Image.FLIP_LEFT_RIGHT)
        idx, ok = cell(src)
        cells[k] = (idx, ok)

    # общий низ кадра: все кадры стоят на одной линии стоп
    sheet = Image.new('RGBA', (CW * SUP * 3, CH * SUP * 8), (0, 0, 0, 0))
    for r, k in enumerate(ORDER):
        if k not in cells:
            continue
        idx, ok = cells[k]
        for f, arr in enumerate(idle_frames(idx)):
            fr = np.zeros_like(idx)
            fr[:] = arr
            frame_img = to_image(fr, ok)
            sheet.paste(frame_img, (f * CW * SUP, r * CH * SUP), frame_img)
    return sheet, cells


if __name__ == '__main__':
    sheet, cells = build()
    sheet.save(os.path.join(OUT, 'warrior_frames8_hd.png'))
    print('HD-лист', sheet.size, 'клетка', CW * SUP, 'x', CH * SUP)
    print('нет:', [k for k in ORDER if k not in cells])

    # превью: 8 направлений x 3 кадра, апскейл x2 чтобы разглядеть пиксели
    Z = 2
    prev = Image.new('RGB', (sheet.width * Z + 170, sheet.height * Z + 20), (26, 24, 22))
    prev.paste(sheet.resize((sheet.width * Z, sheet.height * Z), Image.NEAREST), (10, 10),
               sheet.resize((sheet.width * Z, sheet.height * Z), Image.NEAREST))
    d = ImageDraw.Draw(prev)
    for r, k in enumerate(ORDER):
        d.text((sheet.width * Z + 18, 12 + r * CH * SUP * Z), k, fill=(190, 175, 140))
    prev.save(os.path.join(OUT, 'warrior8_hd_preview.png'))
    print('превью:', os.path.join(OUT, 'warrior8_hd_preview.png'))
