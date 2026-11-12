#!/usr/bin/env python3
"""Превью изометрии на ШТАТНОЙ карте: зал, коридор, толстая стена.
Врагов уводим за край, чтобы кадр был чистым.
Генерирует heroes/sprites/iso_hall.png, iso_fade.png, iso_fade_wide.png.
Запуск: LD_LIBRARY_PATH=/tmp/libs python3 heroes/sprites/shoot_iso.py
"""
import asyncio
from playwright.async_api import async_playwright

URL = 'file:///home/user/index.html'
OUT = '/home/user/heroes/sprites/'

CLEAR = """()=>{
  const S=curScreen();
  for(const e of S.enemies){ e.x=900; e.y=900; }
  S.items.length=0;                      // лут в кадре только мешает читать стены
  S.spikes.length=0; S.pillars.length=0;
  S.torches = S.torches.slice(0,1);
  G.D.invuln=9999; G.D.hearts=G.D.maxHearts;
}"""

# центральный зал (самая большая комната) — общий вид
HALL = """()=>{
  const S=curScreen();
  const r = S.rooms && S.rooms[0];
  if(!r) return null;
  // встаём у стены с настенным факелом: в кадре и кладка, и пятно света
  let best=null;
  for(const t of S.torches){
    if(!t.wall) continue;
    const tx=t.x/16, ty=t.y/16;
    if(tx>=r.x&&tx<r.x+r.w&&ty>=r.y&&ty<r.y+r.h){ best=t; break; }
  }
  if(best){
    const y=Math.min(best.y/16+2, GH-3);
    G.D.px=best.x; G.D.py=y*16+8;
    return [best.x/16, y, 'факел'];
  }
  const y = Math.min(r.y + r.h - 3, GH-3);
  G.D.px = (r.cx)*16+8; G.D.py = y*16+8;
  return [r.cx, y, r.w+'x'+r.h];
}"""

# коридор в один тайл: стены и спереди, и по бокам
FADE = """()=>{
  const S=curScreen();
  const isF=(x,y)=>x>=0&&y>=0&&x<GW&&y<GH&&S.g[y*GW+x]===1;
  for(let y=3;y<GH-3;y++)for(let x=3;x<GW-3;x++){
    if(!isF(x,y)) continue;
    if(isF(x-1,y)&&isF(x,y-1)&&!isF(x+1,y)&&!isF(x,y+1)&&!isF(x+2,y)&&!isF(x,y+2)){
      G.D.px=x*16+8; G.D.py=y*16+8; return [x,y];
    }
  }
  return null;
}"""

# толстая стена впереди (2+ тайла) — раньше эффект тут не срабатывал
FADE_WIDE = """()=>{
  const S=curScreen();
  const isF=(x,y)=>x>=0&&y>=0&&x<GW&&y<GH&&S.g[y*GW+x]===1;
  for(let y=3;y<GH-4;y++)for(let x=3;x<GW-4;x++){
    if(!isF(x,y)) continue;
    if(!isF(x+1,y)&&!isF(x+2,y)&&!isF(x,y+1)&&!isF(x,y+2)&&isF(x-1,y)&&isF(x,y-1)){
      G.D.px=x*16+8; G.D.py=y*16+8; return [x,y];
    }
  }
  return null;
}"""


# --- дополнительно: проверка, что герой читается за стеной, а враг за стеной скрыт ---
CHECK_JS = """()=>{
  const S=curScreen();
  const isF=(x,y)=>x>=0&&y>=0&&x<GW&&y<GH&&S.g[y*GW+x]===1;
  // ставим врага за стену от героя (в +x)
  let found=null;
  for(let y=4;y<GH-4&&!found;y++)for(let x=4;x<GW-4&&!found;x++){
    if(!isF(x,y)) continue;
    if(isF(x+1,y)&&isF(x+2,y)&&isF(x+3,y)) found=[x,y];
  }
  if(found){
    G.D.px=found[0]*16+8; G.D.py=found[1]*16+8;
    if(S.enemies[0]){ S.enemies[0].x=(found[0]+2)*16+8; S.enemies[0].y=found[1]*16+8; }
  }
  return found;
}"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1440, 'height': 810})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL)
        await pg.wait_for_timeout(1400)
        await pg.evaluate("startRaid()")
        await pg.wait_for_timeout(500)
        await pg.evaluate(CLEAR)
        for name, js in (('iso_hall', HALL), ('iso_fade', FADE), ('iso_fade_wide', FADE_WIDE)):
            pos = await pg.evaluate(js)
            await pg.wait_for_timeout(1300)
            await pg.screenshot(path=OUT + name + '.png')
            print(name, pos)
        # доп. сцена: враг за стеной
        pos = await pg.evaluate(CHECK_JS)
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=OUT + 'iso_occlusion.png')
        print('occlusion', pos)
        print('errors', errs[:3])
        await b.close()


asyncio.run(main())
