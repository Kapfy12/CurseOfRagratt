#!/usr/bin/env python3
"""Превью листа 8 направлений: как в игре (1:1 и x4) + подписи."""
import os

from PIL import Image, ImageDraw

SPR = '/home/user/heroes/sprites'
sheet = Image.open(os.path.join(SPR, 'warrior_frames8.png')).convert('RGBA')
CW, CH = 48, 38
NAMES = ['вниз', 'вниз-вправо', 'вправо', 'вверх-вправо',
         'вверх', 'вверх-влево', 'влево', 'вниз-влево']

S = 5
pad = 16
cols = 2
cellw = CW * S + pad
cellh = CH * S + pad

W = cols * cellw + pad * 2 + 260
H = 4 * cellh + pad * 2 + 40
out = Image.new('RGB', (W, H), (30, 28, 26))
d = ImageDraw.Draw(out)
d.text((pad, 12), 'warrior_frames8.png — 8 направлений, изометрия', fill=(210, 190, 150))

for r in range(8):
    src = sheet.crop((0, r * CH, CW, (r + 1) * CH))
    big = src.resize((CW * S, CH * S), Image.NEAREST)
    # фон-плитка под клетку
    bx = pad + (r % cols) * cellw
    by = pad + 24 + (r // cols) * cellh
    d.rectangle([bx, by, bx + CW * S, by + CH * S], fill=(52, 54, 60))
    out.paste(big, (bx, by), big)
    d.text((bx, by + CH * S + 2), f'{r}  {NAMES[r]}', fill=(170, 160, 140))

    # 1:1 как в игре
    x1 = pad + cols * cellw + 12
    y1 = by + CH * S // 2 - CH // 2
    tile = Image.new('RGB', (CW, CH), (52, 54, 60))
    tile.paste(src, (0, 0), src)
    out.paste(tile, (x1, y1))
    d.text((x1 + CW + 10, y1 + 12), '1:1', fill=(120, 118, 112))

out.save(os.path.join(SPR, 'warrior8_preview.png'))
print(os.path.join(SPR, 'warrior8_preview.png'), out.size)
