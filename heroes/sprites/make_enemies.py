"""Пиксельные враги в духе RotMG: 16x16, 3 кадра (idle + два шага), 3 направления.
Тело рисуется из символьной сетки, ноги — отдельным слоем с анимацией,
поэтому шаг видно так же чётко, как у Воина.
Лист 3x3: строки вниз / вверх / вправо, столбцы — кадры. «Влево» — зеркало.
"""
from PIL import Image, ImageDraw

W = H = 16

PAL = {
 'rat': {
   '.': None,
   'd': (26,20,15), 'b': (82,63,46), 'B': (116,92,68), 'D': (54,41,31),
   'n': (44,32,24), 'N': (104,48,40), 'e': (222,58,50), 'w': (238,230,214),
   't': (196,158,138), 'p': (86,66,54),
 },
 'cult': {
   '.': None,
   'd': (18,12,22), 'h': (46,34,54), 'H': (70,52,80), 'g': (198,160,58),
   'r': (58,27,32), 'R': (92,40,38), 's': (200,166,132), 'S': (152,118,90),
   'e': (228,76,42), 'k': (156,169,184), 'K': (104,114,126),
 },
 'skel': {
   '.': None,
   'd': (22,18,14), 'w': (221,216,201), 'W': (160,154,139), 'X': (122,116,102),
   'k': (14,11,9), 'r': (144,96,60), 'R': (98,64,38), 'b': (98,68,42),
   'B': (68,46,28), 'g': (168,134,58), 'c': (188,194,202), 'C': (116,122,132),
 },
}

def render(rows, pal):
    im = Image.new('RGBA', (W, H), (0,0,0,0))
    px = im.load()
    for y, row in enumerate(rows[:H]):
        for x, ch in enumerate(row[:W]):
            c = pal.get(ch)
            if c: px[x, y] = (c[0], c[1], c[2], 255)
    return im

# ============================================================ КРЫСА
RAT_DOWN = [
 '................',
 '................',
 '................',
 '................',
 '...d........d...',
 '..dbd......dbd..',
 '..dbbddddddbbd..',
 '..dbbbbbbbbbbd..',
 '..dbebbbbbbebd..',
 '..dbbbbbbbbbbd..',
 '..dbbbDnnDbbbd..',
 '...dbbwwwwbbd...',
 '....dbbbbbbd....',
 '................',
 '................',
 '................',
]
RAT_UP = [
 '................',
 '................',
 '................',
 '................',
 '...d........d...',
 '..dbd......dbd..',
 '..dbbddddddbbd..',
 '..dbbbbbbbbbbd..',
 '..dbbbbbbbbbbd..',
 '..dbbbbbbbbbbd..',
 '..dbBbbbbbbBbd..',
 '...dbbbbbbbbd...',
 '....dbbbbbbd....',
 '................',
 '................',
 '................',
]
RAT_SIDE = [
 '................',
 '................',
 '................',
 '................',
 '......dd........',
 '....ddbbdd......',
 '...dbbbbbbdd....',
 '..dbbbbbbbbbd...',
 '..dbbbbbbbbbbdd.',
 '..dbbbbbbebbnsd.',
 '..dbbbbbbbbbnwd.',
 '..dbbbbbbbbbbd..',
 '..dbbbbbbbbd....',
 '...dbbbbbbd.....',
 '................',
 '................',
]

# ============================================================ КУЛЬТИСТ
CULT_DOWN = [
 '................',
 '......dddd......',
 '.....dhhhhd.....',
 '....dhhhhhhd....',
 '....dhHHHHhd....',
 '....dhsesehd....',
 '....dhsssshd....',
 '.....dhsshd.....',
 '...dd#hhhh#dd...',
 '..dRRrrrrrrRRd..',
 '..dRrrggggrrRd..',
 '..dRrrRggRrrRd..',
 '..dRrrrrrrrrRd..',
 '...dRrrrrrrRd...',
 '................',
 '................',
]
CULT_UP = [
 '................',
 '......dddd......',
 '.....dhhhhd.....',
 '....dhhhhhhd....',
 '....dhHHHHhd....',
 '....dhhhhhhd....',
 '....dhhhhhhd....',
 '.....dhhhhd.....',
 '...dd#hhhh#dd...',
 '..dRRrrrrrrRRd..',
 '..dRrrggggrrRd..',
 '..dRrrrrrrrrRd..',
 '..dRrrrrrrrrRd..',
 '...dRrrrrrrRd...',
 '................',
 '................',
]
CULT_SIDE = [
 '................',
 '......dddd......',
 '.....dhhhhd.....',
 '....dhhhhhhd....',
 '....dhHHHHhd....',
 '....dhsssehd....',
 '....dhsssshd....',
 '.....dhhhsd.....',
 '....d#hhhh#.....',
 '...dRrrrrr#.....',
 '..dRrrggrrR#....',
 '..dRrrRgrrR#....',
 '..dRrrrrrrr#....',
 '...dRrrrrrd#....',
 '................',
 '................',
]

# ============================================================ СКЕЛЕТ
SKEL_DOWN = [
 '................',
 '.....dddddd.....',
 '....dwwwwwwd....',
 '....dwkwwkwd....',
 '....dwwwwwwd....',
 '....dWwwwwWd....',
 '.....dwkkwd.....',
 '.....dwwwwd.....',
 '...ddwwwwwwdd...',
 '..dwWwwwwwwWwd..',
 '..dwwkwkwkwwwd..',
 '..dWwwkwkwkWWd..',
 '...dwwwwwwwwd...',
 '................',
 '................',
 '................',
]
SKEL_UP = [
 '................',
 '.....dddddd.....',
 '....dwwwwwwd....',
 '....dwwwwwwd....',
 '....dWwwwwWd....',
 '....dWwwwwWd....',
 '.....dwwwwd.....',
 '.....dwwwwd.....',
 '...ddwwwwwwdd...',
 '..dwWwwwwwwWwd..',
 '..dwwkwkwkwwwd..',
 '..dWwwkwkwkWWd..',
 '...dwwwwwwwwd...',
 '................',
 '................',
 '................',
]
SKEL_SIDE = [
 '................',
 '.....dddddd.....',
 '....dwwwwwwd....',
 '....dwkwwkwd....',
 '....dwwwwwwd....',
 '....dWwwwwWd....',
 '.....dwwwwd.....',
 '.....dwwwwwd....',
 '...ddwwwwwwwd...',
 '..dwWwwwwwwwwd..',
 '..dwwkwkwkwwwd..',
 '..dWwwkwkwwWwd..',
 '...dwwwwwwwwd...',
 '................',
 '................',
 '................',
]

# ---------------------------------------------------------------- ноги
def draw_legs(im, kind, direction, frame):
    """Анимация шага: ноги/лапы переставляются, тело почти не смещается."""
    pal = PAL[kind]
    px = im.load()
    def put(x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            c = pal.get(ch)
            if c: px[x, y] = (c[0], c[1], c[2], 255)
    up = 1 if frame == 1 else 0      # левая нога поднята
    down = 1 if frame == 2 else 0    # правая нога поднята
    if kind == 'rat':
        # четыре лапы; в профиль — две
        if direction in ('down', 'up'):
            paws = [(3, 1), (6, 0), (9, 0), (12, 1)]
            for i, (x, ph) in enumerate(paws):
                lift = (frame == 1 and i % 2 == 0) or (frame == 2 and i % 2 == 1)
                y0 = 12 + (1 if lift else 0)
                put(x, y0, 'p'); put(x + 1, y0, 'p')
                put(x, y0 + 1, 'd')
            put(6, 13, 'd'); put(10, 13, 'd') if frame == 0 else None
        else:
            for i, x in enumerate((5, 9)):
                lift = (frame == 1 and i == 0) or (frame == 2 and i == 1)
                put(x, 12 + (1 if lift else 0), 'p')
                put(x, 13 + (0 if lift else 0), 'd')
            # хвост
            tail = [(1, 12), (0, 13), (0, 14)] if frame != 2 else [(1, 13), (0, 14), (0, 15)]
            for x, y in tail: put(x, y, 't')
    elif kind == 'cult':
        boots = (4, 10)
        for i, x in enumerate(boots):
            lift = (frame == 1 and i == 0) or (frame == 2 and i == 1)
            put(x, 13 + (1 if lift else 0), 'd')
            put(x + 1, 13 + (1 if lift else 0), 'd')
            put(x, 14, 'd') if not lift else None
            put(x + 1, 14, 'd') if not lift else None
    else:
        if direction in ('down', 'up'):
            for i, x in enumerate((5, 9)):
                lift = (frame == 1 and i == 0) or (frame == 2 and i == 1)
                y0 = 13 + (1 if lift else 0)
                put(x, y0, 'W'); put(x, y0 + 1, 'w')
                put(x + 1, y0, 'd')
        else:
            for i, x in enumerate((5, 8)):
                lift = (frame == 1 and i == 0) or (frame == 2 and i == 1)
                y0 = 13 + (1 if lift else 0)
                put(x, y0, 'W'); put(x, y0 + 1, 'w')
                put(x + 1, y0, 'd')

# ---------------------------------------------------------------- снаряжение
def add_gear(im, kind, direction):
    pal = PAL[kind]
    px = im.load()
    def put(x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            c = pal.get(ch)
            if c: px[x, y] = (c[0], c[1], c[2], 255)
    if kind == 'skel':
        if direction == 'down':
            for y in range(5, 10):           # клинок в левой руке (1 px)
                put(2, y, 'c')
            put(1, 10, 'g'); put(2, 10, 'd'); put(3, 10, 'g')   # гарда
            put(2, 11, 'R')                                      # рукоять
            for x, y in ((13,7),(14,7),(12,8),(13,8),(14,8),(15,8),
                         (12,9),(13,9),(14,9),(15,9),(12,10),(13,10),(14,10),(15,10),
                         (13,11),(14,11),(13,12)):
                put(x, y, 'b')                                   # щит
            put(13,7,'B'); put(12,8,'B'); put(15,8,'B'); put(12,10,'B'); put(15,10,'B'); put(13,12,'B')
            put(13,9,'g'); put(14,9,'g'); put(13,10,'B'); put(14,10,'B')
        elif direction == 'up':
            for y in range(5, 10):
                put(13, y, 'c')
            put(12, 10, 'g'); put(13, 10, 'd'); put(14, 10, 'g')
            put(13, 11, 'R')
            for x, y in ((2,7),(1,7),(0,8),(1,8),(2,8),(3,8),
                         (0,9),(1,9),(2,9),(3,9),(0,10),(1,10),(2,10),(3,10),
                         (1,11),(2,11),(1,12)):
                put(x, y, 'b')
            put(2,7,'B'); put(2,8,'B'); put(0,8,'B'); put(2,10,'B'); put(1,12,'B')
            put(1,9,'g'); put(2,9,'g')
        else:
            for i in range(5):               # меч вперёд по диагонали
                put(12 + i, 9 - i, 'c')
            put(11, 10, 'g'); put(10, 10, 'R'); put(11, 10, 'g')
            for x, y in ((0,8),(1,8),(0,9),(1,9),(0,10),(1,10),(1,11)):
                put(x, y, 'b')
            put(0,8,'B'); put(1,8,'B'); put(1,11,'B')
            put(1,9,'g'); put(1,10,'B')
    if kind == 'cult':
        if direction == 'down':
            for y in range(9, 13):
                put(14, y, 'K'); put(15, y, 'k')
            put(13, 8, 'g'); put(14, 8, 'g'); put(15, 8, 'g')
            put(3, 9, 'S'); put(3, 10, 'S'); put(2, 11, 's')
        elif direction == 'up':
            for y in range(9, 13):
                put(1, y, 'K'); put(0, y, 'k')
            put(2, 8, 'g'); put(1, 8, 'g'); put(0, 8, 'g')
            put(12, 9, 'S'); put(12, 10, 'S'); put(13, 11, 's')
        else:
            for i in range(5): put(14, 4 + i, 'k')
            put(13, 9, 'g'); put(14, 9, 'g')
            put(12, 10, 's'); put(13, 10, 'S')

def sheet_for(kind, down, up, side):
    sheet = Image.new('RGBA', (W * 3, H * 3), (0, 0, 0, 0))
    for r, (direction, rows) in enumerate((('down', down), ('up', up), ('right', side))):
        for f in (0, 1, 2):
            im = render(rows, PAL[kind])
            draw_legs(im, kind, direction, f)
            add_gear(im, kind, direction)
            sheet.alpha_composite(im, (f * W, r * H))
    return sheet

def make_all():
    return {
        'rat':  sheet_for('rat', RAT_DOWN, RAT_UP, RAT_SIDE),
        'cult': sheet_for('cult', CULT_DOWN, CULT_UP, CULT_SIDE),
        'skel': sheet_for('skel', SKEL_DOWN, SKEL_UP, SKEL_SIDE),
    }

if __name__ == '__main__':
    sheets = make_all()
    S = 8
    gap = 12
    total_w = 3 * (W * 3 * S + gap) + gap
    total_h = 3 * (H * S + gap) + gap + 10
    prev = Image.new('RGB', (total_w, total_h), (26, 28, 34))
    dr = ImageDraw.Draw(prev)
    for i, (name, sh) in enumerate(sheets.items()):
        big = sh.resize((W * 3 * S, H * 3 * S), Image.NEAREST)
        prev.paste(big, (gap + i * (W * 3 * S + gap), gap + 10), big)
        dr.text((gap + i * (W * 3 * S + gap), 2), name, fill=(200, 190, 160))
    prev.save('/home/user/heroes/sprites/enemies_preview.png')
    for name, sh in sheets.items():
        sh.save(f'/home/user/heroes/sprites/{name}_frames.png')
    print('ok')
