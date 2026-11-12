"""Предметы в стиле Diablo 1 (1996).

Иконки D1 — маленькие 3D-рендеры: объёмные формы, свет сверху-слева,
спекуляр на металле и стекле, тёплая приглушённая палитра, тёмный контур.
Здесь то же самое: рисуем в 4x (128x128), затем даунскейлим до 32 и 16.
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

S = 128
OUT32, OUT16 = 32, 16
OUT64 = 64            # HD: тот же 4x-рендер, даунскейл в 64 настоящих пикселя


# ------------------------------------------------------------------ базис
def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(stops, t):
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    x = t * n
    i = min(int(x), n - 1)
    return _lerp(stops[i], stops[i + 1], x - i)


def lerp_col(a, b, t):
    return _lerp(a, b, max(0.0, min(1.0, t)))


def lin_fill(mask, stops, p0, p1):
    """Линейный градиент вдоль p0->p1, обрезанный маской."""
    im = Image.new('RGB', (S, S))
    px = im.load()
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = (dx * dx + dy * dy) or 1
    for y in range(S):
        ty = y - y0
        for x in range(S):
            px[x, y] = ramp(stops, ((x - x0) * dx + ty * dy) / ln)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def sph_fill(mask, stops, cx, cy, r):
    """Радиальный «объём»: центр светлый, к краю темнеет."""
    im = Image.new('RGB', (S, S))
    px = im.load()
    for y in range(S):
        dy = y - cy
        for x in range(S):
            d = math.hypot(x - cx, y - cy) / r
            px[x, y] = ramp(stops, d * 0.5 + 0.5)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def add(im, layer):
    return Image.alpha_composite(im, layer)


def solid(mask, color, alpha=255):
    out = Image.new('RGBA', (S, S), color + (alpha,))
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    lay.paste(out, (0, 0), mask)
    return lay


# ------------------------------------------------------------------ маски
def m_poly(pts):
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def m_ell(box):
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return m


def m_rect(box, r=0):
    m = Image.new('L', (S, S), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle(box, radius=r, fill=255) if r else d.rectangle(box, fill=255)
    return m


def m_line(pts, w):
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).line(pts, fill=255, width=w, joint='curve')
    return m


def m_arc(box, a0, a1, w):
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).arc(box, a0, a1, fill=255, width=w)
    return m


def U(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def minus(a, b):
    return ImageChops.subtract(a, b)


def erode(m, r):
    # PIL требует размер ядра >= 3: MinFilter(1) роняет процесс
    size = max(3, r * 2 + 1)
    return m.filter(ImageFilter.MinFilter(size))


def dilate(m, r):
    size = max(3, r * 2 + 1)
    return m.filter(ImageFilter.MaxFilter(size))


def ring_edge(m, r=2):
    return minus(m, erode(m, r))


# ------------------------------------------------------------------ объём
def bevel(im, mask, light=(255, 244, 220), dark=(30, 20, 16), hi=150, lo=150, r=2, **kw):
    """Фаска: светлая кромка сверху-слева, тёмная внутри снизу-справа."""
    up_l = minus(mask, ImageChops.offset(mask, r, r))
    im = add(im, solid(up_l, light, hi))
    dn = minus(mask, ImageChops.offset(mask, -r, -r))
    im = add(im, solid(dn, dark, lo))
    return im


def spec(im, box, color=(255, 252, 244), alpha=200, blur=3):
    lay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse(box, fill=color + (alpha,))
    return add(im, lay.filter(ImageFilter.GaussianBlur(blur)))


def inner_shadow(im, mask, r=6, color=(12, 8, 8), alpha=120):
    """Мягкая тень по внутреннему краю формы — убирает «наклейку»."""
    edge = ring_edge(mask, r)
    edge = edge.filter(ImageFilter.GaussianBlur(3))
    return add(im, solid(edge, color, alpha))


def noise(im, amt=5):
    px = im.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            if not a:
                continue
            n = ((x * 37 + y * 91) % 13 - 6) * amt // 6
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)
    return im


def final_touch(im):
    """Мягкий тёплый rim и лёгкая виньетка по силуэту — как у рендеров D1."""
    alpha = im.getchannel('A')
    rim = minus(alpha.point(lambda v: 255 if v > 40 else 0), erode(alpha.point(lambda v: 255 if v > 40 else 0), 3))
    rim = rim.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.5))
    im = add(im, solid(rim, (255, 226, 180), 90))
    return noise(im, 5)


# ------------------------------------------------------------------ материалы
STEEL = [(20, 22, 26), (44, 50, 58), (78, 88, 100), (118, 130, 146), (166, 180, 198), (214, 226, 240)]
RUST = [(30, 20, 14), (58, 34, 20), (92, 54, 28), (130, 80, 42), (170, 112, 60), (204, 146, 88)]
IRON = [(18, 18, 20), (44, 46, 50), (74, 78, 84), (108, 112, 120), (146, 152, 160), (190, 196, 206)]
LEATHER = [(26, 17, 12), (50, 32, 20), (76, 48, 28), (106, 70, 42), (138, 96, 58), (172, 128, 84)]
BRASS = [(40, 26, 8), (74, 50, 12), (116, 82, 20), (162, 120, 34), (204, 164, 62), (240, 208, 120)]
BONE = [(46, 40, 32), (84, 76, 62), (124, 114, 96), (164, 152, 130), (200, 190, 166), (232, 224, 202)]
PARCH = [(58, 44, 28), (96, 76, 50), (136, 110, 76), (174, 146, 104), (206, 182, 138), (234, 214, 176)]
BLOOD = [(20, 6, 8), (48, 10, 12), (86, 16, 16), (128, 26, 24), (172, 44, 36), (212, 76, 60)]
MOSS = [(14, 24, 12), (28, 46, 20), (44, 70, 28), (66, 100, 40), (92, 130, 56), (124, 162, 78)]
PURPLE = [(22, 16, 30), (40, 28, 50), (62, 44, 74), (90, 68, 102), (120, 96, 134), (156, 132, 168)]
GLASS = [(22, 26, 30), (54, 62, 72), (94, 104, 118), (140, 152, 168), (188, 200, 216), (228, 238, 250)]


# ================================================================== ТЕСАК
def item_cleaver():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # рукоять из нижнего правого угла полотна
    grip = m_poly([(86, 66), (106, 74), (118, 116), (98, 124)])
    im = add(im, lin_fill(grip, LEATHER, (84, 64), (120, 124)))
    im = bevel(im, grip, light=(228, 182, 130), dark=(18, 11, 6), hi=170, lo=200)
    for k in range(4):
        im = add(im, solid(m_line([(92 + k * 3, 76 + k * 10), (110 + k * 3, 82 + k * 10)], 2), (28, 17, 10), 200))
    # латунная втулка в месте крепления
    fer = m_rect((78, 58, 112, 80), 6)
    im = add(im, lin_fill(fer, BRASS, (78, 56), (114, 82)))
    im = bevel(im, fer, light=(252, 222, 156), dark=(36, 24, 8), hi=190, lo=160)
    # ── полотно: высокий прямоугольник, скос к носку
    blade = m_poly([(8, 14), (100, 10), (110, 20), (110, 62), (26, 74), (8, 56)])
    im = add(im, lin_fill(blade, STEEL, (6, 8), (112, 78)))
    im = bevel(im, blade, light=(255, 255, 255), dark=(6, 8, 12), hi=240, lo=220, r=2)
    spine = ImageChops.multiply(minus(blade, ImageChops.offset(blade, 0, 10)), m_rect((0, 0, S, 30)))
    im = add(im, solid(spine, (38, 44, 52), 215))
    edge = ImageChops.multiply(minus(blade, ImageChops.offset(blade, 0, -12)), m_rect((0, 44, S, S)))
    im = add(im, solid(edge, (248, 253, 255), 240))
    for (bx, by, r, c) in ((30, 34, 13, (126, 70, 34)), (58, 42, 9, (110, 60, 28)), (84, 22, 8, (118, 64, 30))):
        im = add(im, solid(m_ell((bx - r, by - r, bx + r, by + r)).filter(ImageFilter.GaussianBlur(5)), c, 165))
    im = spec(im, (14, 18, 66, 26), (255, 255, 255), 240, 3)
    return final_touch(im)


# ================================================================ КОЧЕРГА
def item_poker():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # ручка внизу
    grip = m_poly([(14, 126), (40, 126), (52, 92), (28, 92)])
    im = add(im, lin_fill(grip, LEATHER, (12, 128), (54, 90)))
    im = bevel(im, grip, light=(228, 182, 130), dark=(16, 10, 6), hi=180, lo=200)
    for k in range(3):
        im = add(im, solid(m_line([(20 + k * 4, 120 - k * 4), (40 + k * 4, 108 - k * 4)], 3), (30, 18, 10), 200))
    # прут (толстый, стальной)
    rod = m_line([(38, 100), (76, 50)], 20)
    im = add(im, lin_fill(rod, STEEL, (30, 104), (84, 44)))
    im = bevel(im, rod, light=(255, 255, 255), dark=(10, 12, 16), hi=220, lo=200, r=2)
    # крюк сверху
    hook = m_arc((36, 0, 112, 72), 150, 30, 21)
    im = add(im, lin_fill(hook, STEEL, (36, 0), (112, 74)))
    im = bevel(im, hook, light=(255, 255, 255), dark=(10, 12, 16), hi=220, lo=190, r=2)
    im = add(im, solid(m_arc((44, 8, 104, 64), 156, 26, 5), (240, 248, 255), 180))
    im = spec(im, (48, 8, 84, 26), (255, 255, 250), 200, 5)
    return final_touch(im)


# =============================================================== КЛЕЙМОР
def item_claymore():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # широкий клинок с ромбическим сечением
    blade = m_poly([(50, 2), (78, 2), (84, 70), (64, 100), (44, 70)])
    im = add(im, lin_fill(blade, STEEL, (40, 4), (88, 100)))
    im = bevel(im, blade, light=(255, 255, 255), dark=(10, 12, 16), hi=210, lo=200, r=2)
    # дол — светлая канавка
    dol = m_poly([(60, 12), (68, 12), (70, 74), (64, 90), (58, 74)])
    im = add(im, solid(dol, (196, 212, 232), 150))
    im = add(im, solid(m_line([(58, 16), (56, 60)], 2), (250, 255, 255), 210))
    im = add(im, solid(m_line([(72, 20), (74, 58)], 2), (36, 42, 52), 120))
    # гарда — широкие плечи с загибом вниз
    guard = m_poly([(16, 78), (112, 78), (104, 94), (80, 88), (64, 98), (48, 88), (24, 94)])
    im = add(im, lin_fill(guard, BRASS, (16, 74), (112, 100)))
    im = bevel(im, guard, light=(255, 240, 176), dark=(34, 22, 6), hi=210, lo=170)
    im = spec(im, (24, 80, 56, 86), (255, 248, 206), 190, 2)
    # рукоять
    grip = m_rect((54, 92, 74, 112), 5)
    im = add(im, lin_fill(grip, LEATHER, (52, 90), (76, 114)))
    im = bevel(im, grip, light=(204, 156, 106), dark=(20, 12, 7), hi=140, lo=180)
    for y in range(94, 111, 4):
        im = add(im, solid(m_rect((55, y, 73, y + 1)), (26, 16, 9), 190))
    # навершие
    pom = m_ell((48, 104, 80, 126))
    im = add(im, sph_fill(pom, BRASS, 60, 110, 18))
    im = bevel(im, pom, light=(255, 244, 190), dark=(34, 22, 6), hi=180, lo=150)
    im = spec(im, (54, 108, 66, 116), (255, 250, 220), 230, 2)
    im = spec(im, (52, 6, 62, 30), (255, 255, 255), 190, 3)
    return final_touch(im)


# ================================================================= КУРТКА
def item_jacket():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    body = U(m_poly([(44, 24), (84, 24), (90, 46), (86, 112), (42, 112), (38, 46)]),
             m_ell((10, 30, 46, 72)), m_ell((82, 30, 118, 72)))
    # база с сильным перепадом света
    im = add(im, lin_fill(body, LEATHER, (10, 16), (112, 118)))
    # тени под рукавами — отделяют их от корпуса
    for x0 in (34, 94):
        sh = ImageChops.multiply(m_ell((x0 - 12, 44, x0 + 12, 78)), body)
        im = add(im, solid(sh.filter(ImageFilter.GaussianBlur(3)), (28, 17, 11), 210))
    # центральная тень корпуса
    im = add(im, solid(ImageChops.multiply(m_rect((58, 30, 92, 112)), body).filter(ImageFilter.GaussianBlur(4)), (34, 21, 13), 150))
    # светлая левая сторона
    im = add(im, solid(ImageChops.multiply(m_poly([(40, 26), (60, 30), (58, 108), (40, 108)]), body)
                       .filter(ImageFilter.GaussianBlur(3)), (188, 138, 88), 130))
    im = bevel(im, body, light=(232, 188, 136), dark=(16, 10, 6), hi=200, lo=210)
    # стёжка ромбами
    quilt = Image.new('L', (S, S), 0)
    dq = ImageDraw.Draw(quilt)
    for k in range(-6, 12):
        dq.line([(k * 18, 24), (k * 18 + 92, 114)], fill=255, width=2)
        dq.line([(k * 18, 114), (k * 18 + 92, 24)], fill=255, width=2)
    quilt = ImageChops.multiply(ImageChops.multiply(quilt, body), m_rect((40, 40, 90, 112)))
    im = add(im, solid(quilt.filter(ImageFilter.GaussianBlur(1)), (30, 19, 11), 120))
    # воротник
    collar = m_poly([(42, 24), (64, 40), (86, 24), (78, 8), (64, 26), (50, 8)])
    im = add(im, lin_fill(collar, LEATHER, (42, 6), (88, 42)))
    im = bevel(im, collar, light=(246, 208, 160), dark=(16, 10, 6), hi=210, lo=180)
    # центральный разрез
    im = add(im, solid(m_rect((62, 34, 68, 112)), (22, 13, 8), 220))
    # застёжки
    for y in range(44, 110, 14):
        btn = m_ell((58, y, 72, y + 12))
        im = add(im, sph_fill(btn, BRASS, 62, y + 3, 10))
        im = add(im, solid(ring_edge(btn, 2), (44, 30, 8), 210))
        im = spec(im, (60, y + 2, 67, y + 6), (255, 246, 206), 235, 1)
    return final_touch(im)


# ================================================================= КИРАСА
def item_cuirass():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # цельный силуэт: купол плеч → талия → остриё подола
    body = m_poly([(24, 40), (38, 26), (90, 26), (104, 40), (108, 64),
                   (90, 100), (64, 124), (38, 100), (20, 64)])
    im = add(im, lin_fill(body, STEEL, (22, 22), (104, 124)))
    # объём: светлая левая грудь, тёмный правый бок
    im = add(im, solid(ImageChops.multiply(m_ell((34, 34, 74, 92)), body).filter(ImageFilter.GaussianBlur(3)),
                       (224, 236, 252), 150))
    im = add(im, solid(ImageChops.multiply(m_ell((74, 40, 104, 96)), body).filter(ImageFilter.GaussianBlur(3)),
                       (40, 46, 56), 150))
    im = bevel(im, body, light=(255, 255, 255), dark=(6, 8, 12), hi=240, lo=225)
    # центральный гребень
    im = add(im, solid(ImageChops.multiply(m_poly([(60, 34), (68, 34), (70, 106), (64, 118), (58, 106)]), body),
                       (206, 220, 238), 120))
    # рёбра
    for x0, dx in ((46, -6), (82, 6)):
        im = add(im, solid(ImageChops.multiply(m_line([(x0, 44), (x0 + dx, 96)], 3), body), (48, 56, 68), 190))
    # горловина
    neck = m_ell((50, 22, 78, 40))
    im.putalpha(ImageChops.subtract(im.getchannel('A'), neck))
    im = add(im, solid(ImageChops.multiply(ring_edge(neck, 3), m_rect((0, 22, S, 44))), (8, 10, 14), 230))
    # золотая окантовка по всему краю (толстая, снизу)
    rim = ImageChops.multiply(ring_edge(body, 5), m_rect((0, 66, S, S)))
    im = add(im, solid(rim, (220, 180, 74), 230))
    rim2 = ImageChops.multiply(ring_edge(body, 2), m_rect((0, 0, S, 70)))
    im = add(im, solid(rim2, (196, 158, 62), 150))
    # тёмный пояс — разделяет грудь и подол
    belt = m_rect((40, 80, 88, 88), 3)
    im = add(im, solid(ImageChops.multiply(belt, body), (44, 32, 20), 190))
    # заклёпки на поясе
    for i2 in range(4):
        x = 44 + i2 * 14
        im = add(im, sph_fill(m_ell((x - 4, 80, x + 4, 88)), BRASS, x - 2, 81, 6))
        im = spec(im, (x - 3, 81, x, 84), (255, 250, 214), 240, 1)
    im = spec(im, (36, 36, 56, 58), (255, 255, 255), 180, 5)
    return final_touch(im)


# =================================================================== МОХ
def item_moss():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # камень-основание
    rock = m_poly([(38, 84), (52, 72), (86, 74), (102, 88), (92, 108), (46, 106)])
    im = add(im, lin_fill(rock, [(30, 28, 26), (64, 62, 58), (98, 96, 90), (132, 130, 122)], (34, 70), (104, 110)))
    im = bevel(im, rock, light=(196, 194, 186), dark=(18, 16, 14), hi=170, lo=190)
    # пучки мха — «кочки» с направлением роста
    tufts = [(40, 62, 16), (58, 46, 19), (80, 44, 18), (96, 62, 15), (68, 64, 20), (52, 78, 15), (84, 78, 14)]
    for (cx, cy, r) in tufts:
        m = U(m_ell((cx - r, cy - r, cx + r, cy + r)),
              m_poly([(cx - r, cy + 2), (cx, cy - r * 1.5), (cx + r, cy + 2)]))
        im = add(im, sph_fill(m, MOSS, cx - r * 0.4, cy - r * 0.6, r * 1.35))
        im = bevel(im, m, light=(184, 220, 132), dark=(8, 18, 6), hi=110, lo=170, r=1)
    # тёмные щели
    for (cx, cy, r) in ((50, 70, 5), (74, 70, 5), (88, 62, 4), (62, 84, 4)):
        im = add(im, solid(m_ell((cx - r, cy - r, cx + r, cy + r)).filter(ImageFilter.GaussianBlur(2)), (6, 14, 4), 200))
    # светлые кончики
    for (cx, cy, r) in ((50, 44, 7), (70, 36, 8), (88, 48, 6), (62, 58, 6), (42, 56, 5)):
        im = spec(im, (cx - r, cy - r, cx + r, cy + r), (196, 232, 140), 200, 2)
    # стебельки по краям
    for (x0, y0, x1, y1) in ((34, 58, 26, 44), (60, 32, 62, 16), (90, 38, 98, 24), (44, 82, 34, 92), (96, 80, 106, 90)):
        im = add(im, solid(m_line([(x0, y0), (x1, y1)], 3), (78, 116, 48), 235))
        im = add(im, solid(m_line([(x0, y0), (x1, y1)], 1), (156, 196, 100), 180))
    return final_touch(im)


# =================================================================== ГЛАЗ
def item_eye():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    flesh = m_poly([(26, 76), (40, 56), (88, 58), (110, 84), (74, 112), (38, 102)])
    im = add(im, lin_fill(flesh, BLOOD, (24, 54), (112, 114)))
    im = bevel(im, flesh, light=(228, 126, 104), dark=(16, 4, 6), hi=130, lo=180)
    # глазное яблоко
    ball = m_ell((30, 18, 98, 90))
    im = add(im, sph_fill(ball, BONE, 52, 36, 44))
    im = bevel(im, ball, light=(255, 255, 248), dark=(56, 48, 40), hi=220, lo=140)
    # верхнее веко — тёмная дуга, даёт «взгляд»
    lid = m_arc((28, 8, 100, 92), 178, 358, 9)
    lid = ImageChops.multiply(lid, m_rect((0, 0, S, 60)))
    im = add(im, solid(lid.filter(ImageFilter.GaussianBlur(1)), (86, 20, 18), 190))
    # радужка
    iris = m_ell((48, 34, 84, 76))
    im = add(im, sph_fill(iris, BLOOD, 62, 48, 20))
    im = add(im, solid(ring_edge(iris, 2), (60, 6, 8), 210))
    im = add(im, solid(m_ell((58, 44, 74, 66)), (6, 2, 4), 252))
    im = spec(im, (52, 30, 68, 44), (255, 255, 255), 252, 2)
    im = spec(im, (72, 60, 82, 70), (255, 242, 226), 170, 2)
    im = spec(im, (36, 30, 52, 48), (255, 254, 246), 130, 5)
    for a, b in (((34, 34), (46, 50)), ((94, 30), (82, 46)), ((40, 74), (52, 66))):
        im = add(im, solid(m_line([a, b], 2), (148, 40, 34), 170))
    im = spec(im, (48, 88, 80, 100), (236, 132, 108), 140, 6)
    return final_touch(im)


# ================================================================= ПЛЕСЕНЬ
def item_mold():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    base = m_poly([(28, 84), (48, 70), (82, 72), (102, 88), (86, 108), (42, 104)])
    im = add(im, lin_fill(base, LEATHER, (26, 68), (104, 110)))
    im = bevel(im, base, light=(180, 130, 84), dark=(20, 12, 8))
    cap = U(m_ell((32, 28, 98, 86)), m_ell((20, 42, 58, 80)), m_ell((72, 42, 112, 82)))
    im = add(im, sph_fill(cap, PURPLE, 58, 44, 52))
    im = bevel(im, cap, light=(196, 176, 214), dark=(16, 10, 22), hi=150, lo=170)
    # бархат: мягкие пятна и «пыльца»
    for (cx, cy, r) in ((34, 62, 8), (46, 42, 9), (68, 36, 10), (90, 46, 9), (102, 66, 8), (62, 74, 9)):
        im = add(im, solid(m_ell((cx - r, cy - r, cx + r, cy + r)).filter(ImageFilter.GaussianBlur(3)), (140, 114, 158), 80))
    for (cx, cy, r) in ((40, 54, 4), (58, 44, 5), (78, 52, 4), (92, 62, 4), (52, 68, 4)):
        im = spec(im, (cx - r, cy - r, cx + r, cy + r), (206, 188, 220), 190, 2)
    im = spec(im, (50, 32, 74, 46), (255, 252, 255), 120, 6)
    return final_touch(im)


# ================================================================ КОСТЬ+ПЫЛЬ
def item_dust():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # кость торчит вертикально из кучи — силуэт «столбик с головками»
    bone = U(m_poly([(52, 34), (78, 30), (82, 96), (48, 100)]),
             m_ell((34, 10, 72, 50)), m_ell((58, 6, 96, 46)))
    im = add(im, lin_fill(bone, BONE, (30, 6), (98, 104)))
    im = bevel(im, bone, light=(255, 255, 250), dark=(42, 36, 28), hi=240, lo=205, r=2)
    # тень между головками
    im = add(im, solid(m_ell((58, 18, 74, 44)).filter(ImageFilter.GaussianBlur(3)), (86, 76, 60), 150))
    im = add(im, solid(m_ell((40, 18, 60, 38)), (255, 255, 252), 230))
    im = add(im, solid(m_ell((68, 14, 88, 34)), (255, 255, 252), 200))
    # трещины на стержне
    im = add(im, solid(m_line([(66, 56), (60, 68)], 2), (104, 94, 78), 200))
    im = add(im, solid(m_line([(64, 76), (70, 86)], 2), (110, 100, 84), 180))
    # куча костяной пыли
    pile = m_poly([(8, 122), (18, 102), (42, 92), (76, 94), (102, 106), (120, 122)])
    im = add(im, sph_fill(pile, [(40, 34, 26), (84, 76, 62), (130, 120, 100), (174, 162, 138), (208, 196, 170)],
                          50, 100, 62))
    im = bevel(im, pile, light=(255, 250, 236), dark=(44, 38, 30), hi=180, lo=190)
    for (cx, cy, r, c) in ((26, 112, 5, (200, 188, 162)), (48, 104, 4, (178, 166, 142)),
                           (82, 106, 4, (192, 180, 154)), (100, 114, 4, (168, 156, 132))):
        im = add(im, sph_fill(m_ell((cx - r, cy - r, cx + r, cy + r)), [(90, 82, 66), c], cx - 1, cy - 1, r * 2))
    im = spec(im, (28, 100, 58, 110), (255, 252, 240), 150, 4)
    # немного пыли осело на кости
    im = add(im, solid(m_ell((44, 84, 62, 96)).filter(ImageFilter.GaussianBlur(2)), (206, 194, 168), 130))
    return final_touch(im)


# ================================================================ СГУСТОК
def item_blood():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # капля: круглый низ + узкий конус кверху
    drop = U(m_ell((26, 46, 102, 118)),
             m_poly([(54, 8), (66, 22), (86, 60), (36, 60)]))
    im = add(im, sph_fill(drop, BLOOD, 48, 48, 66))
    im = bevel(im, drop, light=(250, 176, 144), dark=(10, 2, 4), hi=225, lo=205)
    # запёкшаяся тёмная корка по низу
    crust = ImageChops.multiply(ring_edge(drop, 9), m_rect((0, 92, S, S)))
    im = add(im, solid(crust, (40, 5, 7), 210))
    # глянец
    im = spec(im, (38, 54, 60, 80), (255, 218, 200), 220, 3)
    im = spec(im, (42, 58, 49, 68), (255, 255, 255), 240, 1)
    im = spec(im, (74, 78, 88, 96), (255, 228, 210), 150, 3)
    # отражённый тёплый свет снизу
    im = spec(im, (56, 96, 78, 110), (196, 92, 74), 120, 4)
    # брызги
    for (cx, cy, r) in ((104, 34, 7), (96, 56, 5), (22, 30, 5)):
        d = m_ell((cx - r, cy - r, cx + r, cy + r))
        im = add(im, sph_fill(d, BLOOD, cx - r * .4, cy - r * .5, r * 1.5))
        im = bevel(im, d, light=(250, 176, 144), dark=(10, 2, 4), hi=180, lo=180, r=1)
        im = spec(im, (cx - r * .6, cy - r * .7, cx, cy - r * .1), (255, 230, 214), 210, 1)
    return final_touch(im)


# ================================================================= ЗЕЛЬЯ
def potion(liq, bright):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    body = U(m_ell((28, 44, 100, 116)), m_rect((54, 24, 74, 64), 4))
    # стекло
    im = add(im, lin_fill(body, GLASS, (26, 22), (104, 118)))
    im = bevel(im, body, light=(255, 255, 255), dark=(16, 18, 22), hi=200, lo=190, r=2)
    # жидкость: внутренний объём ниже уровня
    inner = erode(body, 4)
    level = 58
    liqmask = ImageChops.multiply(inner, m_rect((0, level, S, S)))
    im = add(im, solid(liqmask, (0, 0, 0), 0))
    im = add(im, lin_fill(liqmask, liq, (28, level), (100, 118)))
    # объём жидкости: светлый блик слева
    im = spec(im, (40, level + 8, 66, 104), bright, 150, 6)
    # поверхность
    im = add(im, solid(ImageChops.multiply(inner, m_rect((0, level, S, level + 3))), bright, 190))
    # горло и пробка
    neck = erode(m_rect((52, 18, 76, 62), 5), 4)
    cork = U(m_rect((50, 4, 78, 26), 5), m_rect((52, 0, 76, 10), 3))
    im = add(im, lin_fill(cork, LEATHER, (48, 0), (80, 28)))
    im = bevel(im, cork, light=(190, 146, 96), dark=(28, 16, 10))
    im = add(im, solid(m_rect((52, 2, 76, 5)), (130, 94, 58), 150))
    # блики на стекле
    im = spec(im, (38, 58, 50, 96), (255, 255, 255), 220, 3)
    im = spec(im, (40, 56, 46, 70), (255, 255, 255), 240, 2)
    im = spec(im, (78, 80, 90, 96), bright, 170, 4)
    im = add(im, solid(ring_edge(body, 2), (232, 244, 255), 90))
    return final_touch(im)


def item_heal1():
    return potion([(58, 10, 12), (120, 22, 22), (176, 46, 38), (208, 84, 62)], (232, 122, 92))


def item_heal2():
    return potion([(78, 6, 10), (150, 14, 20), (206, 40, 34), (238, 96, 70)], (255, 150, 110))


def item_skin():
    return potion([(14, 30, 62), (28, 62, 116), (62, 116, 176), (128, 178, 226)], (188, 220, 244))


def item_rage():
    return potion([(96, 54, 6), (156, 100, 12), (208, 156, 36), (240, 198, 84)], (255, 224, 136))


# ================================================================ СВИТОК
def scroll(seal=None):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    # лист
    sheet = m_poly([(36, 32), (92, 30), (96, 96), (32, 98)])
    im = add(im, lin_fill(sheet, PARCH, (30, 28), (100, 100)))
    im = bevel(im, sheet, light=(255, 248, 224), dark=(58, 44, 28), hi=150, lo=170)
    # строки текста
    for i in range(7):
        y = 42 + i * 7
        w = 44 if i % 3 else 32
        im = add(im, solid(m_rect((42, y, 42 + w, y + 2)), (88, 66, 44), 160))
        im = add(im, solid(m_rect((42, y, 42 + w, y + 1)), (162, 134, 96), 110))
    # вертикальные рулоны по краям
    for x0, x1 in ((12, 38), (90, 116)):
        roll = m_rect((x0, 20, x1, 110), 12)
        im = add(im, lin_fill(roll, PARCH, (x0 - 2, 18), (x1 + 2, 112)))
        im = bevel(im, roll, light=(255, 252, 232), dark=(50, 36, 20), hi=235, lo=195)
        # тёмная щель между листом и рулоном
        inner = m_rect((x0 + 6, 26, x1 - 6, 104), 8)
        im = add(im, solid(ImageChops.multiply(ring_edge(inner, 3), roll), (96, 74, 48), 130))
        # торцы-спирали сверху и снизу
        for cy in (30, 100):
            cap = m_ell((x0 + 2, cy - 12, x1 - 2, cy + 12))
            im = add(im, lin_fill(cap, [(96, 74, 48), (156, 132, 98), (204, 182, 144), (238, 220, 182)],
                                  (x0 + 2, cy - 12), (x1 - 2, cy + 12)))
            im = add(im, solid(ring_edge(cap, 2), (88, 68, 44), 190))
            im = add(im, solid(m_arc((x0 + 8, cy - 6, x1 - 8, cy + 6), 200, 340, 2), (122, 100, 70), 190))
    if seal:
        stops = [lerp_col((38, 5, 5), seal, t / 5) for t in range(6)]
        sm = m_ell((50, 68, 86, 102))
        im = add(im, sph_fill(sm, stops, 62, 76, 20))
        im = add(im, solid(ring_edge(sm, 2), (56, 8, 8), 200))
        im = spec(im, (56, 72, 68, 82), (255, 200, 180), 215, 2)
    im = spec(im, (40, 34, 70, 44), (255, 252, 236), 120, 5)
    return final_touch(im)


def item_scroll():
    return scroll()


def item_scrollR():
    return scroll(seal=(146, 30, 26))


# ================================================================== ЗОЛОТО
def item_gold():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    GOLD = [(52, 34, 6), (96, 66, 14), (144, 106, 26), (190, 148, 46), (224, 186, 86), (250, 222, 140)]
    # горка: нижний широкий слой, потом всё выше и уже
    layers = [(64, 108, 46, 12), (64, 96, 38, 11), (64, 86, 30, 10), (64, 76, 22, 9)]
    for (cx, cy, r, h) in layers:
        c = m_ell((cx - r, cy - h, cx + r, cy + h))
        im = add(im, lin_fill(c, GOLD, (cx - r, cy - h), (cx + r, cy + h)))
        im = bevel(im, c, light=(255, 250, 200), dark=(48, 32, 4), hi=200, lo=210, r=1)
    # отдельные монеты по краям
    for (cx, cy, r) in ((24, 112, 15), (104, 110, 14), (64, 118, 13), (84, 120, 10)):
        rim = m_ell((cx - r, cy - 7, cx + r, cy + 7))
        im = add(im, lin_fill(rim, GOLD, (cx - r, cy - 7), (cx + r, cy + 7)))
        face = m_ell((cx - r + 2, cy - 8, cx + r - 2, cy + 4))
        im = add(im, lin_fill(face, GOLD, (cx - r, cy - 9), (cx + r, cy + 5)))
        im = add(im, solid(ring_edge(face, 2), (104, 74, 14), 180))
        im = spec(im, (cx - r + 4, cy - 5, cx + 1, cy - 1), (255, 250, 214), 230, 2)
    im = spec(im, (46, 62, 70, 74), (255, 252, 216), 190, 4)
    return final_touch(im)


BUILDERS = {
    'cleaver': item_cleaver, 'poker': item_poker, 'claymore': item_claymore,
    'jacket': item_jacket, 'cuirass': item_cuirass,
    'moss': item_moss, 'eye': item_eye, 'mold': item_mold, 'dust': item_dust, 'blood': item_blood,
    'heal1': item_heal1, 'heal2': item_heal2, 'skin': item_skin, 'rage': item_rage,
    'scroll': item_scroll, 'scrollR': item_scrollR, 'gold': item_gold,
}

# ------------------------------------------------------------------ палитра
PALETTE = []
for r in (STEEL, RUST, IRON, LEATHER, BRASS, BONE, PARCH, BLOOD, MOSS, PURPLE, GLASS):
    PALETTE += [r[0], r[2], r[3], r[4]]
PALETTE += [(14, 10, 8), (22, 16, 12), (32, 24, 18), (44, 34, 26), (244, 240, 226)]
PALETTE = list(dict.fromkeys(PALETTE))


def snap(im):
    im = im.convert('RGBA')
    px = im.load()
    cache = {}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            key = (r, g, b)
            c = cache.get(key)
            if c is None:
                best, bd = PALETTE[0], 1e18
                for p in PALETTE:
                    dr, dg, db = r - p[0], g - p[1], b - p[2]
                    d = dr * dr * .30 + dg * dg * .59 + db * db * .11
                    if d < bd:
                        bd, best = d, p
                c = cache[key] = best
            px[x, y] = (c[0], c[1], c[2], a)
    return im


def outline(im, color=(20, 14, 11)):
    a = im.getchannel('A').point(lambda v: 255 if v > 50 else 0)
    ring = minus(a, erode(a, 1))
    out = im.copy()
    px, rp = out.load(), ring.load()
    for y in range(im.height):
        for x in range(im.width):
            if rp[x, y]:
                px[x, y] = color + (255,)
    return out


def finish(im):
    # выдержка/контраст как у пре-рендеров D1: иначе в 16px всё слипается в тёмное пятно
    im = ImageEnhance.Brightness(im).enhance(1.16)
    im = ImageEnhance.Contrast(im).enhance(1.10)
    big = outline(snap(im.resize((OUT32, OUT32), Image.LANCZOS)))
    small = outline(snap(im.resize((OUT16, OUT16), Image.LANCZOS)))
    return big, small


def finish64(im):
    """HD-версия: 64x64 из того же 128-суперсэмпла. Контур тоньше (1 px на
    вдвое большем полотне = вдвое тоньше относительно фигуры), палитра та же."""
    im = ImageEnhance.Brightness(im).enhance(1.16)
    im = ImageEnhance.Contrast(im).enhance(1.10)
    return outline(snap(im.resize((OUT64, OUT64), Image.LANCZOS)))


def make_all():
    big, small, hd = {}, {}, {}
    for name, fn in BUILDERS.items():
        im = fn()
        b, s = finish(im)
        big[name], small[name] = b, s
        hd[name] = finish64(im)
    return {'32': big, '16': small, '64': hd}


def make_all_retro():
    return make_all()['16']


if __name__ == '__main__':
    sheets = make_all()
    names = list(BUILDERS.keys())
    Z = 6
    cols = 6
    cell = OUT32 * Z + 18
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell + 18, rows * (cell + 18) + 18), (24, 22, 20))
    dr = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x = 18 + (i % cols) * cell
        y = 18 + (i // cols) * (cell + 18)
        big = sheets['32'][n].resize((OUT32 * Z, OUT32 * Z), Image.NEAREST)
        sheet.paste(big, (x, y + 14), big)
        sm = sheets['16'][n].resize((OUT16 * 4, OUT16 * 4), Image.NEAREST)
        sheet.paste(sm, (x + OUT32 * Z - OUT16 * 4, y + 14 + OUT32 * Z - OUT16 * 4), sm)
        dr.text((x, y), n, fill=(198, 182, 150))
    sheet.save('/home/user/heroes/sprites/items_preview.png')
    for n in names:
        sheets['32'][n].save(f'/home/user/heroes/sprites/item_{n}_32.png')
        sheets['16'][n].save(f'/home/user/heroes/sprites/item_{n}.png')
    print('ok', len(names))
