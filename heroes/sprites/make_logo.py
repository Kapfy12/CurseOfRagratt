#!/usr/bin/env python3
"""Логотип «Проклятие замка Раргратт» в духе The Elder Scrolls II: Daggerfall.

Что берём от оригинала:
  • сверху — узкая строка с большим трекингом («Проклятие замка»);
  • снизу — огромные узкие «готические» буквы «РАРГРАТТ» по дуге;
  • багровое тело, чёрный внутренний кант, толстый золотой контур с бликом;
  • заглавная буква уходит вниз кинжалом, у стоек — острые шипы.

Основа — остроконечный кириллический шрифт Ruslan Display: буквы сжимаем
по горизонтали и сильно тянем по вертикали, получая готические пропорции,
затем дорисовываем шипы и кинжал.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = '/home/user'
SPR = os.path.join(ROOT, 'heroes', 'sprites')
FONTS = os.path.join(ROOT, 'heroes', 'fonts')
os.makedirs(SPR, exist_ok=True)

F_MAIN = os.path.join(FONTS, 'RuslanDisplay.ttf')
F_TOP = os.path.join(FONTS, 'CormorantUnicase-Bold.ttf')

SIZE = 420           # кегль основы
CX, SY = 0.56, 2.05  # сжатие по X и растяжение по Y (готические пропорции)
PAD = 260            # запас холста под шипы и кинжал


def glyph(ch):
    """Буква как маска, готических пропорций, с запасом холста."""
    f = ImageFont.truetype(F_MAIN, SIZE)
    im = Image.new('L', (SIZE * 3, SIZE * 3), 0)
    d = ImageDraw.Draw(im)
    d.text((SIZE, SIZE // 2), ch, font=f, fill=255)
    bb = im.getbbox()
    im = im.crop(bb)
    im = im.resize((max(1, int(im.width * CX)), max(1, int(im.height * SY))), Image.LANCZOS)
    out = Image.new('L', (im.width + PAD * 2, im.height + PAD * 2), 0)
    out.paste(im, (PAD, PAD))
    return out, im.width, im.height


def add_spike(mask, gx, gw, gh, fx, length, wfrac=0.30, dirx=0.0):
    """Шип из верхней части буквы: треугольник, слитый с силуэтом."""
    x = gx + gw * fx
    y = gh * 0.16 + PAD
    bw = max(4, gw * wfrac)
    d = ImageDraw.Draw(mask)
    d.polygon([(x - bw / 2, y), (x + bw / 2, y), (x + dirx * bw, y - length)], fill=255)


def add_dagger(mask, gx, gw, gh, fx, length):
    """Кинжал под заглавной буквой: клинок, гарда, навершие."""
    cx = gx + gw * fx
    base = PAD + gh * 0.97
    bw = max(5, gw * 0.075)
    d = ImageDraw.Draw(mask)
    d.polygon([(cx - bw, base), (cx + bw, base),
               (cx + bw * 0.35, base + length), (cx - bw * 0.35, base + length)], fill=255)
    d.polygon([(cx - bw * 3.4, base - gh * 0.04), (cx + bw * 3.4, base - gh * 0.04),
               (cx, base + gh * 0.10)], fill=255)


def build_word(word, track, arch, jitter, rot, spikes, dagger=None):
    glyphs, dims = [], []
    for ch in word:
        m, gw, gh = glyph(ch)
        glyphs.append(m)
        dims.append((gw, gh))

    # шипы и кинжал рисуем внутри холста каждой буквы
    for i, spec in enumerate(spikes):
        if not spec:
            continue
        gw, gh = dims[i]
        for (fx, ln, dx) in spec:
            add_spike(glyphs[i], PAD, gw, gh, fx, SIZE * ln, 0.30, dx)
    if dagger:
        gw, gh = dims[0]
        add_dagger(glyphs[0], PAD, gw, gh, dagger[0], SIZE * dagger[1])

    gap = int(SIZE * track)
    total = sum(dims[i][0] for i in range(len(word))) + gap * (len(word) - 1)
    W = total + PAD * 2 + SIZE
    H = int(SIZE * (SY + 2.4))
    out = Image.new('L', (W, H), 0)
    x = PAD + SIZE // 2
    base = int(H * 0.62)
    for i, m in enumerate(glyphs):
        t = i / max(1, len(word) - 1)
        dx = (t - 0.5) * 2
        curve = int((1 - dx * dx) * arch * SIZE)
        jit = int(jitter[i % len(jitter)] * SIZE)
        if rot:
            m = m.rotate(rot[i % len(rot)], resample=Image.BICUBIC, expand=True, fillcolor=0)
        y = base - (PAD + dims[i][1]) + curve - jit
        out.paste(255, (int(x - PAD), int(y)), m)
        x += dims[i][0] + gap
    bb = out.getbbox()
    return out.crop((bb[0] - 8, bb[1] - 8, bb[2] + 8, bb[3] + 8))


def erode(m, px):
    """Эрозия MinFilter(3) в цикле: MinFilter(1) роняет ядро (Floating point exception)."""
    for _ in range(int(px)):
        m = m.filter(ImageFilter.MinFilter(3))
    return m


def ring(m, px):
    return ImageChops.subtract(m, erode(m, px))


def paint(mask, body_top, body_bot, rim, rim_lit, rim_dark,
          outline=(10, 5, 4), rim_px_scale=1.0):
    """Окраска силуэта: тёмная обводка -> золото -> чёрный кант -> багровое тело."""
    w, h = mask.size
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    def band(m, color, alpha=255):
        img.paste(Image.new('RGBA', (w, h), tuple(color) + (alpha,)), (0, 0), m)

    GOLD = max(4, int(5 * rim_px_scale))     # толщина золотого контура
    band(ring(mask, GOLD + 2), outline)                        # внешняя тёмная обводка
    gold = ring(mask, GOLD)
    band(gold, rim)
    band(ImageChops.subtract(gold, ImageChops.offset(gold, 0, GOLD)), rim_lit)   # блик сверху
    band(ImageChops.subtract(gold, ImageChops.offset(gold, 0, -GOLD)), rim_dark)  # тень снизу

    band(ImageChops.subtract(erode(mask, GOLD), erode(mask, GOLD + 2)), (26, 6, 5))  # чёрный кант
    body = erode(mask, GOLD + 2)
    grad = Image.new('RGBA', (w, h))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        t = min(1.0, max(0.0, (y / max(1, h - 1) - 0.02) / 0.9))
        c = tuple(int(body_top[i] + (body_bot[i] - body_top[i]) * t) for i in range(3))
        gd.line([(0, y), (w, y)], fill=c + (255,))
    img.paste(grad, (0, 0), body)

    # объём: тень по нижней-правой кромке, блик по верхней-левой
    sh = ImageChops.multiply(ImageChops.offset(ring(body, 8), 3, 4), body)
    band(sh, (46, 0, 0), 205)
    hl = ImageChops.multiply(ImageChops.offset(ring(body, 5), -2, -2), body)
    band(hl, (255, 176, 120), 85)
    return img


def top_line(text, size=104, track=30):
    f = ImageFont.truetype(F_TOP, size)
    tmp = Image.new('L', (10, 10)); d = ImageDraw.Draw(tmp)
    widths = [d.textbbox((0, 0), ch, font=f)[2] for ch in text]
    W = sum(widths) + track * (len(widths) - 1) + 30
    im = Image.new('L', (W, int(size * 1.8)), 0); d = ImageDraw.Draw(im)
    x = 15
    for ch, cw in zip(text, widths):
        d.text((x, size * 0.25), ch, font=f, fill=255); x += cw + track
    bb = im.getbbox()
    return im.crop(bb)


def build():
    word = build_word(
        'РАРГРАТТ', track=0.05, arch=0.15,
        jitter=[0.015, -0.008, 0.008, -0.015, 0.0, -0.008, 0.012],
        rot=[-2, 1, -1, 2, 0, -1, 1],
        spikes=[],
        dagger=(0.30, 0.34))
    word_img = paint(word, (232, 62, 30), (128, 10, 10),
                     rim=(252, 196, 78), rim_lit=(255, 250, 212), rim_dark=(126, 74, 20),
                     rim_px_scale=1.0)

    tm = top_line('ПРОКЛЯТИЕ ЗАМКА')
    top_img = paint(tm, (252, 226, 158), (182, 128, 52),
                    rim=(140, 96, 34), rim_lit=(255, 252, 226), rim_dark=(96, 62, 22),
                    outline=(16, 8, 6), rim_px_scale=0.8)

    pad = 26
    W2 = max(word_img.width, top_img.width) + pad * 2
    H2 = top_img.height + 24 + word_img.height + pad
    full = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    full.alpha_composite(top_img, ((W2 - top_img.width) // 2, pad // 2))
    full.alpha_composite(word_img, ((W2 - word_img.width) // 2, pad // 2 + top_img.height + 16))

    # ореол: у Daggerfall надпись «горит» на чёрном
    glow = full.filter(ImageFilter.GaussianBlur(16))
    glow.putalpha(glow.split()[3].point(lambda v: int(v * 0.45)))
    out = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(full)

    out.save(os.path.join(SPR, 'logo_rargratt_hi.png'))
    out.resize((out.width // 2, out.height // 2), Image.LANCZOS).save(os.path.join(SPR, 'logo_rargratt_2x.png'))
    out.resize((out.width // 4, out.height // 4), Image.LANCZOS).save(os.path.join(SPR, 'logo_rargratt_1x.png'))
    print('logo', out.size)
    return out


if __name__ == '__main__':
    build()
