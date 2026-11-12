"""Спрайты-декорации лавок из сгенерированных картинок.

Каждая картинка сгенерирована отдельным объектом на белом фоне. Здесь:
  * вырезаем объект по яркости фона (как делали для NPC и замка);
  * убираем светлую кромку;
  * даунскейлим и прогоняем через палитровый фильтр игры,
    чтобы спрайт жил в общей мрачной палитре.
"""
import os
from PIL import Image, ImageFilter, ImageEnhance, ImageChops

ROOT = '/home/user'
SRC = os.path.join(ROOT, 'heroes', 'props_src')
OUT = os.path.join(ROOT, 'heroes', 'game_assets')


def cut_bg(im, lum_min=190, sat_max=0.10, keep_center=0.62):
    """Фон у сгенерированных картинок — светло-серая студия.
    Заливаем от рамки только серое/светлое, и НЕ даём заливке съесть центр
    кадра: тёмный объект (шкаф) остаётся целым, а не превращается в рамку."""
    from collections import deque
    rgba = im.convert('RGBA')
    w, h = rgba.size
    px = rgba.load()
    bg = bytearray(w * h)

    # границы «неприкосновенного» эллипса в центре
    cx0, cx1 = int(w * (0.5 - keep_center / 2)), int(w * (0.5 + keep_center / 2))
    cy0, cy1 = int(h * (0.02)), int(h * (0.98))

    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        i = y * w + x
        if bg[i]:
            continue
        r, g, b, _ = px[x, y]
        lum = (r * 299 + g * 587 + b * 114) // 1000
        mx, mn = max(r, g, b), min(r, g, b)
        sat = (mx - mn) / mx if mx else 0.0
        is_bg = (lum >= lum_min and sat <= sat_max)
        if not is_bg:
            continue
        if cx0 <= x <= cx1 and cy0 <= y <= cy1:
            # в центре кадра серое — это может быть тень или деталь объекта;
            # пропускаем только совсем светлое (студия)
            if lum < 195:
                continue
        bg[i] = 1
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    # второй проход: «студийные» светлые пятна, дотянувшиеся от фона
    # (белый овал под подставкой и подобное) — тоже убираем
    q = deque()
    for y in range(h):
        for x in range(w):
            if bg[y * w + x]:
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            j = ny * w + nx
            if bg[j]:
                continue
            r, g, b, _ = px[nx, ny]
            lum = (r * 299 + g * 587 + b * 114) // 1000
            mx, mn = max(r, g, b), min(r, g, b)
            sat = (mx - mn) / mx if mx else 0.0
            if lum >= 105 and sat <= 0.06:
                bg[j] = 1
                q.append((nx, ny))

    mask = Image.frombytes('L', (w, h), bytes(0 if v else 255 for v in bg))
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    rgba.putalpha(ImageChops.multiply(rgba.getchannel('A'), mask))
    return rgba


def retro_sprite(rgba, width, colors=150, dark=0.86, sat=0.86):
    """Даунскейл до игрового размера + общая палитра игры."""
    h = max(1, round(rgba.height * width / rgba.width))
    alpha = rgba.getchannel('A')
    small = rgba.convert('RGB').resize((width, h), Image.LANCZOS)
    small = ImageEnhance.Brightness(small).enhance(dark)
    small = ImageEnhance.Color(small).enhance(sat)
    small = ImageEnhance.Contrast(small).enhance(1.06)
    small = small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                           dither=Image.Dither.FLOYDSTEINBERG).convert('RGB')
    out = small.convert('RGBA')
    a = alpha.resize((width, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    out.putalpha(a)
    return out


def solidify(rgba, thresh=26):
    """Фоном считаем всё, что похоже на ровный светлый цвет по краям кадра:
    заливаем от рамки, а не по всему изображению — объект остаётся целым."""
    from collections import deque
    w, h = rgba.size
    px = rgba.load()
    seen = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y][x]:
            continue
        r, g, b, a = px[x, y]
        lum = (r * 299 + g * 587 + b * 114) // 1000
        if a < 8 and lum > 150:          # уже прозрачная «кайма»
            seen[y][x] = True
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
            continue
        if lum > 170:                    # светлый фон — съедаем
            seen[y][x] = True
            px[x, y] = (r, g, b, 0)
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def build(name, width, **kw):
    src = Image.open(os.path.join(SRC, f'{name}_raw.png'))
    rgba = cut_bg(src)
    box = rgba.getbbox()
    if box:
        rgba = rgba.crop(box)
    out = retro_sprite(rgba, width, **kw)
    out.save(os.path.join(OUT, f'prop_{name}.png'))
    prev = Image.new('RGB', (out.width + 20, out.height + 20), (34, 30, 25))
    prev.paste(out, (10, 10), out)
    prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST).save(f'/tmp/prev_{name}.png')
    print(f'  prop {name}', out.size)
    return out


# --- интерфейс для build_game_assets.py ---
def make_flask():
    """Колба алхимика: стекло на ТЁМНОМ фоне (в белой студии горлышко
    светилось белым), затем та же обработка, что у NPC-рендеров."""
    import key_dark_flask, glass_flask
    src = os.path.join(SRC, 'flask_dark_raw.png')
    rgba = key_dark_flask.key_on_black(src, thr=2)
    box = rgba.getbbox()
    if box:
        rgba = rgba.crop(box)
    out = glass_flask.npc_pipeline(rgba, TH=190, colors=210, blur=0.3)
    out.save(os.path.join(OUT, 'prop_flask.png'))
    prev = Image.new('RGB', (out.width + 12, out.height + 12), (38, 36, 30))
    prev.paste(out, (6, 6), out)
    prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST).save('/tmp/prev_flask.png')
    print('  prop flask (стекло, тёмный фон)', out.size)
    return out


def make_shelf():
    return build('shelf', 132, colors=160, dark=0.90, sat=0.84)


if __name__ == '__main__':
    make_flask()
    make_shelf()
