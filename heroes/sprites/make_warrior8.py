#!/usr/bin/env python3
"""Сборка листа 8 направлений под изометрию: воин в широкой боевой стойке.

Источник: heroes/assets/warrior8/d0..d7_*.png — пре-рендеры, чистый белый фон.
Конвейер тот же, что в make_warrior_dirs.py (вырезание -> градация ->
жёсткая палитра -> блочный даунскейл -> контур), но с якорем по стопам:
в изометрии фигуру надо ставить на низ клетки, а не по центру габарита,
иначе меч, торчащий вбок, уводит тело из центра.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_warrior_dirs import (CW, CH, SS, PAL, cut_white, grade_hi, to_palette,
                               block_mode, add_outline, to_image)

# Тот же металл, но без «выжженного» белого: лезвие и наплечники не должны
# светиться ярче факелов на тёмном полу.
PAL8 = PAL.copy()
PAL8[8] = (150, 151, 147)     # было 200,200,194 — «белое» лезвие
PAL8[7] = (136, 137, 133)     # было 164,165,161

ROOT = '/home/user'
SRC = os.path.join(ROOT, 'heroes', 'assets', 'warrior8')
OUT = os.path.join(ROOT, 'heroes', 'sprites')

# порядок строк в листе: 0 вниз ... 7 вниз-влево (по часовой от «на игрока»)
ORDER = ['d0_down', 'd1_down_right', 'd2_right', 'd3_up_right',
         'd4_up', 'd5_up_left', 'd6_left', 'd7_down_left']

TARGET_H = 35      # высота фигуры в логических пикселях (клетка 38)


def darken(im):
    """Тёмный доспех: убрать «серебро», оставить блики на гранях."""
    r, g, b, a = im.split()
    arr = np.asarray(Image.merge('RGB', (r, g, b))).astype(np.float32) / 255.0
    arr = np.power(arr, 1.30)          # жёстче в тенях
    arr = arr * 0.88                   # ниже среднего уровня
    arr = np.clip(arr, 0, 1)
    # мелкая рябь от заклёпок на 16 px не читается — гасим медианой
    rgb = Image.fromarray((arr * 255).astype(np.uint8))
    rgb = rgb.filter(ImageFilter.MedianFilter(3))
    out = rgb.convert('RGBA')
    out.putalpha(a)
    return out


def to_palette_pal(im, pal):
    """Как to_palette, но с собственной палитрой (блик не уходит в белый)."""
    a = np.asarray(im).astype(np.float32)
    rgb = a[:, :, :3]
    d = ((rgb[:, :, None, :] - pal[None, None, :, :].astype(np.float32)) ** 2).sum(-1)
    return d.argmin(-1), a[:, :, 3]


def bbox(img):
    a = np.asarray(img)[:, :, 3]
    ys, xs = np.where(a > 40)
    return xs.min(), ys.min(), xs.max(), ys.max()


def load(key):
    p = os.path.join(SRC, key + '.png')
    if not os.path.exists(p):
        return None
    return cut_white(p)


def foot_anchor(xs, ys, y0, y1):
    """Центр по стопам: самый низ фигуры, а не габарит с мечом."""
    bot = ys >= (y1 - max(4, int((y1 - y0) * 0.06)))
    return float(np.mean(xs[bot]))


def shear(im, k):
    """Ложный поворот на 45°: сдвиг строк друг относительно друга.

    Прямой фронт при этом читается как «в три четверти» — дёшево и без
    артефактов генерации. k = +0.5 для вида вправо-вниз, -0.5 — влево-вниз.
    """
    w, h = im.size
    pad = int(abs(k) * h) + 2
    out = Image.new('RGBA', (w + pad * 2, h), (0, 0, 0, 0))
    for y in range(h):
        out.paste(im.crop((0, y, w, y + 1)), (pad + int(k * (y - h)), y))
    return out


def cell(img, scale):
    x0, y0, x1, y1 = bbox(img)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    a = np.asarray(img)[:, :, 3]
    ys, xs = np.where(a > 40)
    ax = foot_anchor(xs, ys, y0, y1)

    big = img.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                     Image.LANCZOS)
    bw, bh = big.size
    cw, ch = CW * SS, CH * SS
    foot_dx = (ax - x0) * scale          # стопы внутри кадра
    left = int(round(cw * 0.5 - foot_dx))
    left = max(-9999, min(left, cw - bw))
    top = ch - bh
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    canvas.paste(big, (left, top), big)

    idx, alpha = to_palette_pal(darken(grade_hi(canvas)), PAL8)
    small, oka = block_mode(idx, alpha)
    return add_outline(small, oka)


def build(keys=None):
    keys = keys or ORDER
    imgs = {k: load(k) for k in keys}

    # единый масштаб: медиана по всем кадрам, чтобы пропорции не гуляли
    scales = []
    for k, im in imgs.items():
        if im is None:
            continue
        _, y0, _, y1 = bbox(im)
        scales.append(TARGET_H * SS / (y1 - y0 + 1))
    scale = float(np.median(scales))

    sheet = Image.new('RGBA', (CW * 3, CH * 8), (0, 0, 0, 0))
    cells = {}
    for r, k in enumerate(ORDER):
        if imgs.get(k) is None:
            continue
        src = imgs[k]
        # «вниз-вправо» = зеркало «вниз-влево»: гарантирует симметрию диагоналей
        # и не зависит от того, повернёт ли модель фигуру в промпте
        if k == 'd1_down_right' and imgs.get('d7_down_left') is not None:
            src = imgs['d7_down_left'].transpose(Image.FLIP_LEFT_RIGHT)
        idx, ok = cell(src, scale)
        c = to_image(idx, ok)
        cells[k] = c
        for f in range(3):
            sheet.paste(c, (f * CW, r * CH), c)
    return sheet, cells


if __name__ == '__main__':
    from PIL import ImageDraw
    sheet, cells = build()
    miss = [k for k in ORDER if k not in cells]
    sheet.save('/tmp/warrior8_sheet.png')

    S = 6
    big = sheet.resize((sheet.width * S, sheet.height * S), Image.NEAREST)
    prev = Image.new('RGB', (big.width + 200, big.height + 20), (26, 24, 22))
    prev.paste(big, (10, 10), big)
    d = ImageDraw.Draw(prev)
    for r, k in enumerate(ORDER):
        d.text((big.width + 16, 12 + r * CH * S), k, fill=(190, 175, 140))
        if k in miss:
            d.text((10, 12 + r * CH * S), 'НЕТ', fill=(220, 70, 70))
    prev.save('/tmp/warrior8_preview.png')
    print('клетки:', sorted(cells))
    print('нет:', miss)
    print('/tmp/warrior8_preview.png')
