import sys, pathlib
from playwright.sync_api import sync_playwright
SRC = pathlib.Path(__file__).resolve().parent
OUT = SRC.parent
WEIGHTS = ["400", "500", "600", "700", "800"]
names = sys.argv[1:] or ["thumbnail", "body-1", "body-2", "body-3", "body-4"]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
    for n in names:
        pg.goto((SRC / f"{n}.html").as_uri(), wait_until="networkidle")
        ok = pg.evaluate("""async (ws) => {
            await Promise.all(ws.map(w => document.fonts.load(w + ' 32px "Pretendard"', '가A')));
            await document.fonts.ready;
            return ws.map(w => document.fonts.check(w + ' 32px "Pretendard"', '가A'));
        }""", WEIGHTS)
        loaded = pg.evaluate("""() => [...document.fonts].filter(f => f.family.includes('Pretendard') && f.status==='loaded').map(f=>f.weight)""")
        if not all(ok) or not loaded:
            print(f"FONT FAIL {n}: check={ok} loaded={loaded}"); sys.exit(1)
        el = pg.locator("#cap")
        el.screenshot(path=str(OUT / f"{n}.png"))
        bb = el.bounding_box()
        print(n, int(bb["width"]), int(bb["height"]), "fonts", sorted(set(loaded)))
    b.close()
