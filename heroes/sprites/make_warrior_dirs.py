#!/usr/bin/env python3
"""Топ-даун спрайты воина в стиле Diablo 1 — 4 направления.

Стиль: пре-рендер (heroes/assets/warrior_dirs/) -> вырезание фона ->
фиксированная «жёсткая» палитра (как у D1) -> уменьшение по моде блока.
Никакого сглаженного даунскейла: цвет в каждом пикселе — из палитры,
поэтому силуэт получается крупным, плоским и «клеевым», а не мыльным.

Лист: строки = вниз(0)/вверх(1)/вправо(2)/влево(3), по 3 кадра в строке.
"""
import os
from collections import Counter, deque

import numpy as np
from PIL import Image, ImageEnhance

ROOT = '/home/user'
SRC = os.path.join(ROOT, 'heroes', 'assets', 'warrior_dirs')
OUT = os.path.join(ROOT, 'heroes', 'sprites')

CW, CH = 48, 38          # клетка кадра: камера 60° вниз — фигура шире, чем выше
SS = 8                   # суперсэмплинг: 1 логический пиксель = SS x SS
FRAMES = 3
# 8 направлений. Диагонали — зеркальные боковые ракурсы (в наборе рендеров
# их нет): для вида сверху 3/4 зеркало даёт корректный «вперёд-вправо» и
# «назад-вправо»; левые диагонали берутся из тех же клеток отражением при выводе.
ROWS8 = ('front', 'front_right', 'right', 'back_right',
         'back', 'back_left', 'left', 'front_left')
ROWS = ('front', 'back', 'right', 'left')   # старый порядок — для 4-направленного листа

PAL = np.array([
    (10, 9, 10), (24, 23, 24), (40, 39, 40), (58, 57, 58),
    (80, 79, 78), (104, 104, 102), (132, 132, 129), (164, 165, 161),
    (200, 200, 194), (26, 32, 40), (76, 46, 26), (130, 72, 30),
    (176, 98, 44), (114, 96, 58),
], dtype=np.int16)
OUTLINE_IDX = 0


# --------------------------------------------------------------- вырезание
def cut_white(path, thr=236):
    """Убрать студийно-белый фон: flood fill от краёв + замкнутые «дыры»."""
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    lum = a @ np.array([0.299, 0.587, 0.114])
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    bg = (lum > thr) & (sat < 0.10)

    def flood(mask, seeds):
        seen = np.zeros((h, w), bool)
        q = deque(seeds)
        while q:
            x, y = q.popleft()
            if x < 0 or y < 0 or x >= w or y >= h or seen[y, x] or not mask[y, x]:
                continue
            seen[y, x] = True
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        return seen

    seeds = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
    seeds += [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    alpha = np.where(flood(bg, seeds), 0, 255).astype(np.uint8)

    # замкнутые просветы между рукой и торсом — тоже фон (студия нейтральна)
    whiteish = (lum > 222) & (sat < 0.07) & (alpha > 0)
    for y0 in range(h):
        for x0 in range(w):
            if not whiteish[y0, x0]:
                continue
            comp = flood(whiteish, [(x0, y0)])
            ys, xs = np.where(comp)
            whiteish[ys, xs] = False
            if len(ys) >= 12:
                alpha[ys, xs] = 0

    # пылинки рендера
    solid = alpha > 0
    for y0 in range(h):
        for x0 in range(w):
            if not solid[y0, x0]:
                continue
            comp = flood(solid, [(x0, y0)])
            ys, xs = np.where(comp)
            solid[ys, xs] = False
            if len(ys) < 40:
                alpha[ys, xs] = 0

    alpha = np.where(alpha >= 110, 255, 0).astype(np.uint8)
    out = im.convert('RGBA')
    out.putalpha(Image.fromarray(alpha))
    box = out.getbbox()
    return out.crop(box) if box else out


# ---------------------------------------------------------------- отрисовка
def place_hi(im):
    """Крупный холст CW*SS x CH*SS, стопы на нижней границе, тело по центру.

    Вписываем по обоим измерениям: у вида сверху фигура шире, чем выше,
    и обрезка по высоте расплющивала бы её.
    """
    cw, ch = CW * SS, CH * SS
    k = min(cw / im.width, ch / im.height)
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    big = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(big)[:, :, 3]
    xs = np.where((a > 40).any(axis=0))[0]
    cx = int(round(np.median(xs))) if xs.size else w // 2
    left = cw // 2 - cx
    if xs.size:
        left = max(left, -int(xs.min()))
        left = min(left, cw - 1 - int(xs.max()))
    out = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    out.paste(big, (left, ch - h), big)
    return out


def grade_hi(im):
    """Поднять тени и медь: на тёмном полу ноги иначе растворяются."""
    r, g, b, a = im.split()
    arr = np.asarray(Image.merge('RGB', (r, g, b))).astype(np.float32) / 255.0
    arr = np.power(arr, 0.78)
    arr = np.clip((arr - 0.5) * 1.16 + 0.5, 0, 1)
    rgb = Image.fromarray((arr * 255).astype(np.uint8))
    rgb = ImageEnhance.Color(rgb).enhance(1.22)
    out = rgb.convert('RGBA')
    out.putalpha(a)
    return out


def to_palette(im):
    """Каждый пиксель — ближайший цвет фиксированной палитры."""
    a = np.asarray(im).astype(np.float32)
    rgb = a[:, :, :3]
    d = ((rgb[:, :, None, :] - PAL[None, None, :, :].astype(np.float32)) ** 2).sum(-1)
    idx = d.argmin(-1)
    return idx, a[:, :, 3]


def block_mode(idx, alpha):
    """Уменьшение: в каждом блоке SS x SS — самый частый индекс палитры."""
    h, w = idx.shape
    oh, ow = h // SS, w // SS
    out = np.zeros((oh, ow), np.int16)
    outa = np.zeros((oh, ow), bool)
    for y in range(oh):
        for x in range(ow):
            al = alpha[y*SS:(y+1)*SS, x*SS:(x+1)*SS]
            if al.size == 0 or (al > 110).mean() < 0.5:
                continue
            blk = idx[y*SS:(y+1)*SS, x*SS:(x+1)*SS][al > 110]
            if blk.size == 0:
                continue
            out[y, x] = Counter(blk.tolist()).most_common(1)[0][0]
            outa[y, x] = True
    return out, outa


def add_outline(idx, outa):
    """Жёсткий контур 1 px — силуэт отделяется от пола подземелья."""
    h, w = idx.shape
    res = idx.copy(); ok = outa.copy()
    for y in range(h):
        for x in range(w):
            if outa[y, x]:
                continue
            near = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and outa[ny, nx]:
                        near = True
            if near:
                res[y, x] = OUTLINE_IDX
                ok[y, x] = True
    return res, ok


def cell(key):
    base = cut_white(os.path.join(SRC, key + '.png'))
    hi = grade_hi(place_hi(base))
    idx, alpha = to_palette(hi)
    small, oka = block_mode(idx, alpha)
    return add_outline(small, oka)


def to_image(idx, ok):
    rgb = PAL[idx].astype(np.uint8)
    rgba = np.dstack([rgb, np.where(ok, 255, 0).astype(np.uint8)])
    return Image.fromarray(rgba, 'RGBA')


def spritesheet(rows=ROWS):
    sheet = Image.new('RGBA', (CW * FRAMES, CH * len(rows)), (0, 0, 0, 0))
    for r, key in enumerate(rows):
        img = to_image(*cell(key))
        for f in range(FRAMES):
            sheet.paste(img, (f * CW, r * CH), img)
    return sheet


def spritesheet8():
    """Лист на 8 направлений.

    Строки: 0 вниз, 1 вниз-вправо, 2 вправо, 3 вверх-вправо,
            4 вверх, 5 вверх-влево, 6 влево, 7 вниз-влево.
    Клетки 5 и 7 — отражение клеток 3 и 1 по горизонтали.
    """
    sheet = Image.new('RGBA', (CW * FRAMES, CH * 8), (0, 0, 0, 0))
    order = ('front', 'front_right', 'right', 'back_right', 'back')
    for r, key in enumerate(order):
        img = to_image(*cell(key))
        for f in range(FRAMES):
            sheet.paste(img, (f * CW, r * CH), img)
    # левые половины: отражение правых
    for dst, src in ((5, 3), (6, 2), (7, 1)):
        for f in range(FRAMES):
            cellimg = sheet.crop((f * CW, src * CH, (f + 1) * CW, (src + 1) * CH))
            sheet.paste(cellimg.transpose(Image.FLIP_LEFT_RIGHT), (f * CW, dst * CH))
    return sheet


if __name__ == '__main__':
    from PIL import ImageDraw
    sheet = spritesheet8()
    sheet.save(os.path.join(OUT, 'warrior_frames8.png'))
    print('лист 8 направлений', sheet.size)
    sheet4 = spritesheet()
    sheet4.save(os.path.join(OUT, 'warrior_frames.png'))
    print('лист 4 направлений', sheet4.size)

    S = 3
    big = sheet.resize((sheet.width * S, sheet.height * S), Image.NEAREST)
    prev = Image.new('RGB', (big.width + 24, big.height + 24), (26, 24, 22))
    prev.paste(big, (12, 12), big)
    d = ImageDraw.Draw(prev)
    for r, key in enumerate(ROWS):
        d.text((12, 12 + r * CH * S + 2), key, fill=(190, 175, 140))
    prev.save('/tmp/warrior_dirs_preview.png')
    print('превью /tmp/warrior_dirs_preview.png')
