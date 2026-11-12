# HD-спрайты геймплея (×2–×3 по разрешению)

Задача: увеличить разрешение **всех** спрайтов игровой части в 2–3 раза.
Размер на экране при этом **не меняется** — растёт только плотность пикселей.

## Что стало чем

| Объект | Было | Стало | Пикселей | Файл-источник |
|---|---|---|---|---|
| Герой (8 направлений × 3 кадра) | 48×38 | **144×114** | ×3 | `heroes/sprites/make_warrior8_hd.py` → `warrior_frames8_hd.png` |
| Предметы (иконки) | 16 px | **64 px** | ×4 | `make_items.py::finish64()` → `item_*_64.png` |
| Враги (3 вида × 3 кадра × 3 направления) | 16×16 | **32×32** | ×2 | `heroes/sprites/make_enemies32.py` → `*_frames32.png` |

В игре всё рисуется в прежних экранных габаритах:

- герой: `HERO_CW/HERO_CH = 144×114`, `HERO_SDIV = 3` → на экране 48×38 логических;
- враги: клетка 32, `sc = 0.8 / 1` (было 16 при `sc = 1.6 / 2`);
- предметы: `drawIcon()` сам выбирает ступень по размеру пятна
  (≥15 → 64 px, ≥8 → 32 px, иначе 16 px), так что ни одна иконка не мылится.

## Почему это не просто апскейл

Герой и предметы собираются из **суперсэмплинга 8×**: фигура сначала
рендерится крупно, затем уменьшается блоками 8×8 с выбором цвета по моде
палитры (`block()` в `make_warrior8_hd.py`, `finish64()` в `make_items.py`).
Поэтому в 144×114 каждый пиксель — это осмысленный цвет из палитры, а не
растянутый втрое сосед. Видны заклёпки, кромки нагрудника, ремни, гарда меча.

Враги 32×32 получаются из тех же символьных сеток 16×16: каждый символ
превращается в блок 2×2 со светотенью (верхняя кромка светлее, низ темнее,
по контуру обводка в 1 настоящий пиксель). Силуэт и кадры анимации остались
ровно там же — игровая логика (строки листа, кадры, зеркало «влево») не менялась.

## Пересборка

```bash
python3 heroes/sprites/make_warrior8_hd.py     # лист героя (~30 с)
python3 heroes/sprites/make_enemies32.py       # листы врагов (~0.5 с)
python3 heroes/build_game_assets.py            # вшивает всё в index.html (~55 с)
```

`build_game_assets.py` вызывает `make_enemies32.py` сам, а герой собирается
через `import make_warrior8_hd as make_warrior8` (старый `make_warrior8.py`
остался как 48×38-версия).

## Правка после приёмки: кадр «вправо»

Первая версия `d2_right` в HD показала **три ноги** — артефакт генерации,
который на 48×38 маскировался шириной стойки. Кадр перегенерирован
(профиль + «ровно две ноги, два наколенника, два сапога»), плита под ногами
убрана третьим проходом. Исходник лежит в `d2_right_3legs_BAD.png`,
рабочий — `d2_right.png`. Остальные семь направлений проверены: ног по две.
Подробности — в `prompts_warrior8.md`, раздел «Брак d2 и как он правился».

## Скорость героя

`STEP_SPEED` в `index.html` (около `moveFree`) снижен со 150 до **52 px/сек**
(промежуточный вариант был 46 — по просьбе поднят до 52).
Монстры: скелет 20, культист 26, крыса 44. Герой быстрее самой быстрой твари
на 8 px/сек: отрыв растёт 8 px в секунду (за 2.6 с погони 15.7 → 32.0 px).
Клетка 16 px проходится за 0.31 с.

Замеры (Playwright, свободный коридор): 51.9–52.1 px/с без рывков на стыках
тайлов; погоня с крысой — дистанция устойчиво растёт, `errors []`.

## Проверки

- `node --check` для скрипта из `index.html` — OK;
- Playwright: `errors []`, 8 направлений на месте, fps 47–49 (до правок 43–42);
- инвентарь, лавки торговца/гильдии/алхимика — иконки 64 px читаются.

## Скриншоты

- `heroes/sprites/hd_hero_compare.png` — было/стало по 8 направлениям;
- `heroes/sprites/hd_items_compare.png` — 16 / 32 / 64 px для четырёх предметов;
- `heroes/sprites/hd_game_scene.png` — полный кадр подземелья;
- `heroes/sprites/hd_hero_closeup.png` — герой крупно в игре;
- `heroes/sprites/hd_dirs8.png` — все 8 направлений в игре.

## Откат

`heroes/backups/index_before_hd.html` — рабочая игра до перехода на HD.
`heroes/backups/make_items_ok.py`, `heroes/backups/build_game_assets_ok.py` —
скрипты до правок.

## Wall occlusion — 2026-11-06
- Brighter stone palette and vertical face gradient retained; ambient darkness retained.
- Hero occlusion now source-over stone at 0.70, restricted to actual sprite alpha and foreground wall polygons. Replaces multiply-only darkening, which left a dark sticker silhouette.
- Include all hero-hit wall tiles (not just floor-adjacent faces); reset heroVeilOK each frame to prevent stale masks in open areas.
- Browser smoke tests: (31,18), (31,6), (13,7), (18,23), (18,11), no JS errors; node syntax check passed. Screenshots in heroes/wall_*.png. No new FPS benchmark performed.
- Movement unchanged: STEP_SPEED = 52.

## Texture on south/right walls
- Both visible faces of every rendered wall block now receive masonry, edge highlights, and vertical shading. Removed floor-neighbor condition that left outside faces flat when adjacent tiles belonged to unrendered solid space.
- Clipped face gradients to their isometric polygons to avoid rectangular spill.
- Browser checks at (18,11), (13,7): no JS errors; screenshots walls_all_faces.png and walls_all_corner.png.
- Backup: heroes/backups/index_before_all_wall_faces.html.

## Six-frame rightward run
- Articulated from existing HD warrior artwork: six 144x114 frames in warrior_run_right6.png; repeatable build script make_run_right6.py; animated preview warrior_run_right6.gif.
- Integrated separate right-run sheet in index.html. 10 frames/sec, six-frame loop, original idle when stopped. Remaining directions unchanged; speed still 52 px/sec.
- Run phase uses accumulated delta time; no advancement when blocked. Same renderer is used for the foreground-wall silhouette mask.
- Browser: all six draw calls passed, sheet 864x114, no JS errors. Syntax check passed.

## Rightward sprint revision
- Replaced soft walk poses with explicit sprint: 15-degree forward lean, broad thigh swing, tucked recovery leg, lifted knees and airborne poses; 6 frames at 14 fps.
- Rebuilt and embedded right-run sheet in index.html. Translation remains 52 px/s. Other directions unchanged.
- JS syntax and browser rendering of all six frames passed without errors.

## Up run
- Six rear-view articulated frames from original HD direction 4; make_run_up6.py creates warrior_run_up6.png and GIF preview.
- Integrated screen-up/W (world direction 5) with shared 7 fps accumulated phase. Idle unchanged; speed 52 px/s.
- Syntax and all six browser draw calls passed. W input maps to grid (-1,-1).

## Rear run: narrower stride and visible heels
- Narrowed hips/foot tracks; removed outward-pointing toes from original standing pose.
- Added rear boot heels on planted feet and treaded soles on lifted feet (recovery frames).
- Rebuilt and embedded warrior_run_up6.png; six frames at 7 fps, movement unchanged. JS syntax check passed.

## Eight-direction sword strikes
- Generated full-body white-slash attack poses, transparent 256x256 cells, 2048x256 atlas in sprites/attacks/warrior_attacks8.png; metadata and source rebuild script retained.
- Embedded atlas in index.html. Each accepted attack displays its facing-locked pose for up to 0.22 seconds, including crate strikes; then returns to idle/run. Existing movement speed remains 52.
- Attack silhouette uses the actual attack bounding box and the same wall occlusion path as the hero.
- Damage projectiles now use normalized 8-direction grid vectors so direction matches the attack pose; speed/range/damage/cooldown unchanged. Projectile rendering now projects world positions through W2S.
- Tests: all 8 atlas frames load/render; facing holds when direction changes mid-strike; timer expires; idle restored; wall-area draw succeeds; no JS errors.

## Numeric health system
- Player state: hp/maxHp; warrior starts at 150/150, other former 3-heart heroes 150, barbarian 200.
- HUD uses a numeric health bar, no heart slots. Inventory, hero selection, church bonus and logs updated.
- Healing: 50/100 HP with cap; blessing +50 max HP. Legacy saved buffs.hearts converts once to maxHp at 50 per heart.
- Enemy damage: rat 10, cultist 15, skeleton 20; spikes/darts 20, boulder 40. Projectile damage values are passed through.
- Shield is numeric absorption: jacket 25, cuirass 50, stone skin +50; overflow hits HP. Armor block chance unchanged.
- tools/test_health.py: 14 checks passed, including damage, invulnerability, shield overflow, healing caps, potion consumption, floor transitions, save migration, death; no JS errors.

## Warrior melee and stone-skin mitigation
- Warrior attack is now a 140-degree local sweep, range 30 world pixels plus target radius; can hit multiple targets once per accepted attack. No projectile spawned. Walls, pillars, intervening crates and blocked diagonal corners stop the hit.
- Reach gives +25% melee range; Wind gives +20 degrees sweep. Other classes retain their existing ranged behavior. Damage, cooldown and eight-direction attack poses retained.
- Stone skin: incoming damage multiplier 0.15 for 60 seconds, rounded to integer minimum 1 for positive damage. Refreshes duration without stacking. No HP/shield increase. Reduction precedes equipment shield absorption; equipment block chance remains.
- HUD displays remaining stone-skin duration. tests/test: tools/test_melee.py passed 11 checks; health and attack-sprite tests updated and rerun.

## New rat runs integrated
- Embedded cleaned right/left/down/up six-frame sheets in index.html; 10 fps clock accumulates only during actual movement.
- Direction chosen from projected screen-space motion; stop/contact resets pose. Other enemies unchanged.
- Per-direction cell sizes and anchors retained, scale 0.16; actual sprite bounds used for wall occlusion. Red eye glow not quantized away.
- Rat stats remain speed 44, HP 5, damage 10. tools/embed_rat_runs.py updates embedded sheets after future asset edits.
- tools/test_rat_runs.py: 20 checks passed (four directions, all frames, loaded sheets, stats and stopped poses), no browser errors.
