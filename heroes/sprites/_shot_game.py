#!/usr/bin/env python3
"""Скриншот подземелья с героем: проверяем, как лист воина лёг в игру."""
import asyncio, sys
from playwright.async_api import async_playwright

URL = 'file:///home/user/index.html'
OUT = '/tmp/war_game_%s.png'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files'])
        pg = await b.new_page(viewport={'width': 1440, 'height': 810})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto(URL)
        await pg.wait_for_timeout(2500)
        # грузимся в подземелье и ставим героя в комнату с врагами
        ok = await pg.evaluate("""() => {
          try {
            startRaid();
            return true;
          } catch(e) { return String(e); }
        }""")
        await pg.wait_for_timeout(1200)
        # пробежимся вправо-влево, чтобы сменить кадры и направление
        for key, name in (('ArrowDown', 'down'), ('ArrowUp', 'up'),
                          ('ArrowRight', 'right'), ('ArrowLeft', 'left')):
            await pg.keyboard.down(key)
            await pg.wait_for_timeout(230)
            await pg.keyboard.up(key)
            await pg.wait_for_timeout(60)
            pos = await pg.evaluate("() => ({x: G.D.px, y: G.D.py, dir: G.D.dir})")
            await pg.screenshot(path=OUT % name)
            # кроп ровно вокруг героя: логические координаты -> экран (RS=3, +OY)
            cx, cy = pos['x'] * 3, (pos['y'] + 26) * 3
            await pg.screenshot(path='/tmp/zoom_%s.png' % name,
                                clip={'x': cx - 70, 'y': cy - 130, 'width': 140, 'height': 160})
            print(name, pos)
        await pg.screenshot(path='/tmp/war_game_crop_src.png')
        print('ok=', ok, 'errors=', errs[:5])
        await b.close()


asyncio.run(main())
