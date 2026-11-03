"""이미지 HTML을 PNG로 캡처합니다.

사용법: python capture.py            전체 캡처
        python capture.py body-2     지정한 이미지만 캡처
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
NAMES = ["thumbnail", "body-1", "body-2", "body-3", "body-4", "body-5"]
FIXED_SIZE = {"thumbnail": (1080, 1080), "body-1": (1080, 1080)}

WAIT_FONTS = """
async () => {
  await document.fonts.ready;
  const weights = [...new Set([...document.querySelectorAll('#canvas, #canvas *')]
    .map((el) => getComputedStyle(el).fontWeight))];
  const results = [];
  for (const w of weights) {
    const spec = `${w} 32px Pretendard`;
    const loaded = await document.fonts.load(spec, '클로드 코드 CLAUDE.md 0123');
    results.push({
      weight: w,
      check: document.fonts.check(spec, '클로드 코드 CLAUDE.md 0123'),
      faces: loaded.filter((f) => f.family.replace(/["']/g, '') === 'Pretendard'
                                  && f.status === 'loaded').length,
    });
  }
  return results;
}
"""

FIND_OVERFLOW = """
() => {
  const canvas = document.querySelector('#canvas');
  const box = canvas.getBoundingClientRect();
  const issues = [];
  if (canvas.scrollHeight > canvas.clientHeight || canvas.scrollWidth > canvas.clientWidth) {
    issues.push(`canvas scroll ${canvas.scrollWidth}x${canvas.scrollHeight} > ${canvas.clientWidth}x${canvas.clientHeight}`);
  }
  for (const el of canvas.querySelectorAll('*')) {
    if (el.closest('svg')) continue;
    const r = el.getBoundingClientRect();
    if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).display !== 'inline') {
      issues.push(`inner overflow: ${el.className || el.tagName}`);
    }
    if (r.left < box.left || r.right > box.right || r.bottom > box.bottom) {
      issues.push(`outside canvas: ${el.className || el.tagName}`);
    }
  }
  return issues;
}
"""


def main():
    targets = sys.argv[1:] or NAMES
    failed = False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1080, "height": 1080}, device_scale_factor=1
        )
        for name in targets:
            page.goto((SRC / f"{name}.html").as_uri(), wait_until="networkidle")
            fonts = page.evaluate(WAIT_FONTS)
            bad = [f for f in fonts if not f["check"] or f["faces"] == 0]
            if not fonts or bad:
                print(f"FONT FAIL {name}: {fonts}")
                failed = True
                break
            canvas = page.locator("#canvas")
            box = canvas.bounding_box()
            if name in FIXED_SIZE and (box["width"], box["height"]) != FIXED_SIZE[name]:
                print(f"SIZE FAIL {name}: {box}")
                failed = True
            issues = page.evaluate(FIND_OVERFLOW)
            canvas.screenshot(path=str(OUT / f"{name}.png"))
            weights = ",".join(f["weight"] for f in fonts)
            print(f"OK {name} {box['width']:.0f}x{box['height']:.0f} weights={weights} issues={issues}")
        browser.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
