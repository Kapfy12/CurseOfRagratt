# Промпты: воин, изометрия, 8 направлений

Схема одна и та же для всех восьми кадров:
**БАЗОВЫЙ ПРОМПТ** (не меняется ни на слово) + **одна строчка направления**.
Всё остальное — «тот же самый персонаж», «та же самая стойка», «та же самая камера».

Почему так: модель срывается, если переписывать промпт целиком — начинают гулять
доспех, пропорции и масштаб. Одна неизменная база + подмена только направления
держит силуэт и стойку стыкуемыми.

---

## БАЗОВЫЙ ПРОМПТ

```
Pre-rendered 3D game sprite for a dark fantasy dungeon crawler, Diablo 1 style.
A single knight in blackened steel plate armour, full body from helmet to boots.

WIDE BRACED COMBAT STANCE: feet planted far apart, about two shoulder widths,
knees bent outward, hips low and weight centred, torso squared to the target,
longsword gripped in the right hand with the blade angled forward at chest
height, left hand raised open in guard in front of the chest.

Closed great-helm with a narrow horizontal eye slit, heavy layered pauldrons,
segmented cuisses and greaves, copper-bronze trim and rivets on every plate
edge, weathered scratched steel with dark grime in the recesses, dark leather
belt with hanging tassets. No shield, no cape, no plume.

ORTHOGRAPHIC ISOMETRIC CAMERA, fixed, 35 degrees above the horizon, looking
down at the figure. → DIRECTION.

Figure centred in a square frame, full body with a small empty margin around it,
consistent scale. Soft neutral studio light from the upper left, cool steel
highlights, no coloured rim light, no strong cast shadow.

Background: perfectly flat pure white, completely empty — no ground, no shadow
under the feet, no props, no text, no logo, no border, no frame.

Crisp readable silhouette, clean hard edges, low-poly gritty realism.
```

---

## ВОСЕМЬ НАПРАВЛЕНИЙ

Подставляется вместо `→ DIRECTION`. Всё остальное — дословно из базы.

| # | Файл | Направление в игре | Строчка направления |
|---|------|--------------------|---------------------|
| 0 | `d0_down.png` | вниз (на игрока) | `THE FIGURE FACES THE BOTTOM OF THE FRAME, directly toward the camera. Same character, same armour, same stance, same scale as the base.` |
| 1 | `d1_down_right.png` | вниз-вправо | `THE FIGURE IS TURNED TO FACE THE BOTTOM-RIGHT CORNER OF THE FRAME, 45 degrees clockwise from facing the camera. The camera does not move. Same character, same armour, same stance, same scale as the base.` |
| 2 | `d2_right.png` | вправо | `THE FIGURE IS TURNED TO FACE THE RIGHT EDGE OF THE FRAME, 90 degrees clockwise from facing the camera, seen in profile. The camera does not move. Same character, same armour, same stance, same scale as the base.` |
| 3 | `d3_up_right.png` | вверх-вправо | `THE FIGURE IS TURNED TO FACE THE TOP-RIGHT CORNER OF THE FRAME, 135 degrees clockwise from facing the camera, seen from behind on his left side. The camera does not move. Same character, same armour, same stance, same scale as the base.` |
| 4 | `d4_up.png` | вверх (от игрока) | `THE FIGURE IS TURNED AWAY AND FACES THE TOP OF THE FRAME, his back to the camera, 180 degrees. The camera does not move. Same character, same armour, same stance, same scale as the base.` |
| 5 | `d5_up_left.png` | вверх-влево | `THE FIGURE IS TURNED TO FACE THE TOP-LEFT CORNER OF THE FRAME, 225 degrees clockwise from facing the camera, seen from behind on his right side. The camera does not move. Same character, same armour, same stance, same scale as the base.` |
| 6 | `d6_left.png` | влево | `THE FIGURE IS TURNED TO FACE THE LEFT EDGE OF THE FRAME, 270 degrees clockwise from facing the camera, seen in profile on his other side. The camera does not move. Same character, same armour, same stance, same scale as the base.` |
| 7 | `d7_down_left.png` | вниз-влево | `THE FIGURE IS TURNED TO FACE THE BOTTOM-LEFT CORNER OF THE FRAME, 315 degrees clockwise from facing the camera. The camera does not move. Same character, same armour, same stance, same scale as the base.` |

---

## Как это снято (порядок работы)

1. Кадр `d0_down.png` — чистая база.
2. Остальные кадры — тот же базовый промпт, где меняется **только** строчка
   направления. Референс `d0_down.png` подавать **бесполезно**: модель не
   поворачивает фигуру, а лишь перекрашивает ту же фронтальную позу (проверено,
   bbox кадров совпадал до пикселя). Поэтому все 8 кадров — чистый text-to-image
   от одной базы.
3. Без референса поза «плывёт» сильнее всего на диагоналях: `d1_down_right` и
   `d7_down_left` первая генерация вернула фронтом. Помогает явное описание
   ракурса («far left pauldron is partly hidden», «helmet crest runs diagonally»),
   но приём «поверни тело» работает через раз.
3. Белый фон (`#FFFFFF`) вырезается порогом, кадр сажается в сетку 48×38,
   квантуется в жёсткую палитру Diablo и собирается в лист `warrior_frames8.png`
   (8 строк × 3 кадра).
4. Лист подставляется в `index.html` вместо старого.

Скрипт сборки: `heroes/sprites/make_warrior8.py`.


---

## Итог по направлениям (что реально легло в игру)

| # | Источник | Как получен |
|---|----------|-------------|
| 0 | `d0_down.png` | база, чистый фронт |
| 1 | `d1_down_right.png` | **зеркало `d7` по горизонтали** (в сборке, `make_warrior8.py`) |
| 2 | `d2_right.png` | **перегенерация** (1-я версия была с тремя ногами), строгий профиль |
| 3 | `d3_up_right.png` | генерация, три четверти со спины |
| 4 | `d4_up.png` | генерация, спина 180° |
| 5 | `d5_up_left.png` | генерация, три четверти со спины (зеркальная сторона) |
| 6 | `d6_left.png` | генерация, строгий профиль с другой стороны |
| 7 | `d7_down_left.png` | генерация, три четверти налево (третья попытка) |

### Брак d2 и как он правился

Первая версия `d2_right.png` содержала **три ноги**: у героя читались два
наколенника спереди и третий сапог между ними. На 48×38 это маскировалось
шириной стойки, но в HD (144×114) стало очевидным. Кадр перегенерирован
двумя добавками к базе:

1. `EXACTLY TWO LEGS, TWO KNEE COPES AND TWO BOOTS — one leg per side of the
   hips, no third limb, no extra knee, no extra foot anywhere in the frame.`
2. явное описание ракурса: `STRICT SIDE PROFILE VIEW, as if the knight were
   standing on a turntable turned exactly 90 degrees… chest, visor slit and
   the toes of both boots point to the RIGHT EDGE of the frame.`

Вторая попытка дала верный профиль, но с каменной плитой под ногами — её убрал
третьим проходом (image-to-image: «remove the stone platform, background pure
white everywhere, keep the knight pixel-for-pixel identical»). Итог — `d2_right_fix3.png`,
он и лежит теперь как `d2_right.png`. Битый исходник сохранён как
`d2_right_3legs_BAD.png`.

Остальные семь кадров проверены по нижней трети: у каждого ровно две ноги.

Почему d1 — зеркало: генератор трижды выдавал «вниз-вправо» фронтальной
позой (bbox совпадал с базой). Зеркало даёт идеальную симметрию диагоналей,
а асимметрия оружия на 16 px не читается. Все левые ракурсы (5, 6) сгенерированы
отдельно, а не отражены — чтобы доспех не выглядел «одним и тем же боком».
