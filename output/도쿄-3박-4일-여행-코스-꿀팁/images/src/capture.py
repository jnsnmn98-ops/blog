"""images/src의 HTML을 Playwright로 열어 #canvas 요소만 PNG로 캡처합니다.

사용법: python capture.py [이름 ...]   (이름을 생략하면 전체 캡처)
Pretendard가 적용되지 않으면 캡처하지 않고 종료합니다.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
ALL = ["thumbnail", "body-1", "body-2", "body-3", "body-4"]
WEIGHTS = [500, 600, 700, 800]

CHECK_FONTS = """
async (weights) => {
  const out = [];
  for (const w of weights) {
    const spec = `${w} 32px Pretendard`;
    const faces = await document.fonts.load(spec, '도쿄가나Aa1');
    out.push({
      weight: w,
      loaded: faces.length > 0 && faces.every(f => f.status === 'loaded'),
      check: document.fonts.check(spec, '도쿄가나Aa1'),
    });
  }
  await document.fonts.ready;
  return out;
}
"""

# 잘림과 넘침을 눈으로 보기 전에 한 번 더 걸러 냅니다.
CHECK_OVERFLOW = """
() => {
  const bad = [];
  const canvas = document.querySelector('#canvas').getBoundingClientRect();
  for (const el of document.querySelectorAll('#canvas *')) {
    if (el.closest('svg')) continue;
    const r = el.getBoundingClientRect();
    if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).display !== 'inline')
      bad.push(['scroll', el.className || el.tagName, el.textContent.trim().slice(0, 24)]);
    if (r.right > canvas.right + 1 || r.bottom > canvas.bottom + 1 || r.left < canvas.left - 1)
      bad.push(['outside', el.className || el.tagName, el.textContent.trim().slice(0, 24)]);
  }
  return bad;
}
"""


def main() -> int:
    names = sys.argv[1:] or ALL
    status = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1080, "height": 1080}, device_scale_factor=1
        )
        for name in names:
            page.goto((SRC / f"{name}.html").as_uri(), wait_until="networkidle")
            fonts = page.evaluate(CHECK_FONTS, WEIGHTS)
            failed = [f for f in fonts if not (f["loaded"] and f["check"])]
            if failed:
                print(f"FONT FAIL {name}: {failed}")
                browser.close()
                return 2
            target = page.locator("#canvas")
            box = target.bounding_box()
            target.screenshot(path=str(OUT / f"{name}.png"))
            problems = page.evaluate(CHECK_OVERFLOW)
            print(f"{name}.png {int(box['width'])}x{int(box['height'])} overflow={problems}")
            if problems:
                status = 1
        browser.close()
    return status


if __name__ == "__main__":
    sys.exit(main())
