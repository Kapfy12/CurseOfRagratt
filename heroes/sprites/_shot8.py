#!/usr/bin/env python3
"""Скриншот героя в игре в 8 направлениях — проверка нового листа."""
import asyncio
import os

from playwright.async_api import async_playwright

URL = 'file:///home/user/index.html'
NAMES = ['down', 'down_right', 'right', 'up_right',
         'up', 'up_left', 'left', 'down_left']

async def main():
    os.makedirs('/tmp/z8', exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1440, 'height': 810})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto(URL)
        await pg.wait_for_timeout(2200)
        await pg.evaluate("() => { startRaid(); G.D.invuln = 9999; }")
        await pg.wait_for_timeout(1200)

        # простое «телепортирование» в центр большой комнаты и прокрутка dir
        await pg.evaluate("""() => {
            G.D.px = 296; G.D.py = 236; G.D.animT = 0;
        }""")
        await pg.wait_for_timeout(300)

        keys = {0: ('ArrowDown',), 1: ('ArrowDown', 'ArrowRight'),
                2: ('ArrowRight',), 3: ('ArrowUp', 'ArrowRight'),
                4: ('ArrowUp',), 5: ('ArrowUp', 'ArrowLeft'),
                6: ('ArrowLeft',), 7: ('ArrowDown', 'ArrowLeft')}

        res = []
        for d, ks in keys.items():
            for k in ks:
                await pg.keyboard.down(k)
            await pg.wait_for_timeout(400)
            st = await pg.evaluate("() => ({dir: G.D.dir, x: G.D.px, y: G.D.py})")
            await pg.screenshot(path='/tmp/z8/%s.png' % NAMES[d])
            for k in ks:
                await pg.keyboard.up(k)
            await pg.wait_for_timeout(120)
            await pg.evaluate("() => { G.D.px = 296; G.D.py = 236; }")
            await pg.wait_for_timeout(80)
            res.append((NAMES[d], st))

        # и общий кадр
        await pg.screenshot(path='/tmp/z8/full.png')
        for n, s in res:
            print(n, s)
        print('errors', errs[:5])
        await b.close()

asyncio.run(main())
