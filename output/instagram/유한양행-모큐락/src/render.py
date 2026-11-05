"""귀엽고 세련된 카드뉴스 렌더러 — 유한양행 모큐락.
실행: python src/render.py  (주제 폴더에서)
"""
import json
import math
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1350
IVORY1, IVORY2 = (249, 246, 239), (238, 232, 219)
GREEN = (14, 90, 69)
GREEN_D = (9, 60, 46)
MINT = (220, 238, 229)
GOLD = (194, 154, 78)
GOLD_L = (240, 225, 190)
TEXT = (47, 59, 53)
SUB = (110, 118, 112)
WHITE = (255, 255, 255)
GRAY = (196, 200, 196)

JUA = str(ROOT / "assets/fonts/Jua-Regular.ttf")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def jua(s):
    return ImageFont.truetype(JUA, s)


def sd(s, w="bold"):
    return ImageFont.truetype(SD, s, index={"bold": 6, "semi": 4, "reg": 0, "light": 2}[w])


def tw(d, t, f):
    b = d.textbbox((0, 0), t, font=f)
    return b[2] - b[0]


FALLBACK = set("·²“”×")


def runs(text):
    out = []
    for ch in text:
        fb = ch in FALLBACK
        if out and out[-1][0] == fb:
            out[-1][1] += ch
        else:
            out.append([fb, ch])
    return out


def jfont(size, fb):
    return sd(size) if fb else jua(size)


def jw(d, text, size):
    return sum(tw(d, t, jfont(size, fb)) for fb, t in runs(text))


def jtext(d, x, y, text, size, fill, anchor="la"):
    """Jua로 쓰고, Jua에 없는 글자만 산돌고딕으로 대신 그린다."""
    w = jw(d, text, size)
    if anchor[0] == "m":
        x -= w / 2
    elif anchor[0] == "r":
        x -= w
    base = y + jua(size).getmetrics()[0]
    for fb, t in runs(text):
        f = jfont(size, fb)
        d.text((x, base), t, font=f, fill=fill, anchor="ls")
        x += tw(d, t, f)
    return w


def background(seed):
    rnd = random.Random(seed)
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(IVORY1[i] + (IVORY2[i] - IVORY1[i]) * t) for i in range(3)))
    im = im.convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for _ in range(3):
        x, y, r = rnd.randint(-100, W + 100), rnd.randint(-100, H + 100), rnd.randint(160, 260)
        ld.ellipse((x - r, y - r, x + r, y + r), fill=MINT + (90,))
    lay = lay.filter(ImageFilter.GaussianBlur(40))
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    # 세련된 금색 얇은 테두리
    d.rounded_rectangle((28, 28, W - 28, H - 28), 40, outline=GOLD + (150,), width=2)
    return im


def sparkle(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.3
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color)


def mascot(size, wink=False):
    """캡슐 캐릭터 (직접 그린 장식)."""
    s = size * 4
    im = Image.new("RGBA", (s, int(s * 0.62)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    h = int(s * 0.5)
    y0 = int(s * 0.06)
    d.rounded_rectangle((int(s * 0.02), y0, s - int(s * 0.02), y0 + h), h // 2, fill=WHITE, outline=GREEN, width=int(s * 0.02))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((int(s * 0.02), y0, s - int(s * 0.02), y0 + h), h // 2, fill=255)
    mask_r = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask_r).rectangle((s // 2, 0, s, im.height), fill=255)
    mask_r = Image.composite(m, Image.new("L", im.size, 0), mask_r)
    im.paste(GREEN + (255,), (0, 0, s, im.height), mask_r)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((int(s * 0.02), y0, s - int(s * 0.02), y0 + h), h // 2, outline=GREEN, width=int(s * 0.02))
    cy = y0 + h * 0.5
    # 얼굴(흰 쪽)
    for ex in (s * 0.2, s * 0.38):
        if wink and ex > s * 0.3:
            d.arc((ex - s * 0.05, cy - s * 0.06, ex + s * 0.05, cy + s * 0.03), 200, 340, fill=GREEN_D, width=int(s * 0.02))
        else:
            d.ellipse((ex - s * 0.036, cy - s * 0.05, ex + s * 0.036, cy + s * 0.05), fill=GREEN_D)
            d.ellipse((ex - s * 0.012, cy - s * 0.035, ex + s * 0.008, cy - s * 0.012), fill=WHITE)
    for bx in (s * 0.12, s * 0.46):
        d.ellipse((bx - s * 0.05, cy + s * 0.05, bx + s * 0.05, cy + s * 0.1), fill=(255, 170, 170, 210))
    d.arc((s * 0.255, cy + s * 0.01, s * 0.325, cy + s * 0.08), 20, 160, fill=GREEN_D, width=int(s * 0.018))
    # 초록 쪽 윤기 하이라이트
    d.rounded_rectangle((s * 0.62, y0 + h * 0.18, s * 0.86, y0 + h * 0.3), h * 0.06, fill=(255, 255, 255, 110))
    return im.resize((size, int(size * 0.62)), Image.LANCZOS)


def fit(img, w, h, vfocus=0.5, hfocus=0.5):
    img = img.convert("RGB")
    sc = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * sc)), max(h, round(img.height * sc))), Image.LANCZOS)
    x = int((img.width - w) * hfocus)
    y = int((img.height - h) * vfocus)
    return img.crop((x, y, x + w, y + h))


def rmask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def photo(path, w, h, radius=44, vfocus=0.5, hfocus=0.5, ring=True):
    ph = fit(Image.open(ROOT / path), w, h, vfocus, hfocus)
    pad = 36
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 12, pad + w, pad + h + 12), radius, fill=(30, 60, 50, 60))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    out.paste(ph, (pad, pad), rmask(w, h, radius))
    if ring:
        ImageDraw.Draw(out).rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), radius, outline=GOLD, width=3)
    return out, pad


def put(im, path, x, y, w, h, **kw):
    obj, pad = photo(path, w, h, **kw)
    im.alpha_composite(obj, (x - pad, y - pad))


def pill(d, x, y, text, font, fill, color, padx=26, pady=12, center=False, outline=None):
    w = tw(d, text, font)
    b = d.textbbox((0, 0), text, font=font)
    h = b[3] - b[1]
    if center:
        x = x - (w + padx * 2) / 2
    d.rounded_rectangle((x, y, x + w + padx * 2, y + h + pady * 2), (h + pady * 2) / 2, fill=fill, outline=outline, width=2 if outline else 0)
    d.text((x + padx, y + pady - b[1]), text, font=font, fill=color)
    return x + w + padx * 2, y + h + pady * 2


def header(im, data, n, total):
    d = ImageDraw.Draw(im)
    x, _ = pill(d, 64, 56, data["ad_label"], sd(26), GREEN, WHITE, padx=20, pady=8)
    d.text((x + 16, 62), data["account"], font=sd(26, "semi"), fill=SUB)
    t = f"{n} / {total}"
    d.text((W - 64, 62), t, font=sd(26, "semi"), fill=GOLD, anchor="ra")


def dots(im, n, total):
    d = ImageDraw.Draw(im)
    gap = 24
    x0 = W / 2 - (total - 1) * gap / 2
    for i in range(total):
        if i == n - 1:
            d.rounded_rectangle((x0 + i * gap - 14, H - 62, x0 + i * gap + 14, H - 52), 5, fill=GREEN)
        else:
            d.ellipse((x0 + i * gap - 5, H - 62, x0 + i * gap + 5, H - 52), fill=GRAY)


def title(im, lines, y, size=88, accent=1, center=False, x=72):
    d = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        w = jw(d, line, size)
        lx = (W - w) / 2 if center else x
        if i == accent:
            d.rounded_rectangle((lx - 8, y + size * 0.6, lx + w + 8, y + size * 1.0), 14, fill=GOLD_L)
        jtext(d, lx, y, line, size, GREEN if i == accent else GREEN_D)
        y += int(size * 1.16)
    return y


def wrap_lines(d, text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(d, t, font) > maxw and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    return lines


def note(im, text, y_bottom=H - 100, size=25):
    d = ImageDraw.Draw(im)
    f = sd(size, "reg")
    lines = wrap_lines(d, text, f, W - 160)
    y = y_bottom - len(lines) * (size + 10)
    for ln in lines:
        d.text((80, y), ln, font=f, fill=SUB)
        y += size + 10


def credit(im, text, x, y, anchor="ra"):
    ImageDraw.Draw(im).text((x, y), text, font=sd(22, "reg"), fill=SUB, anchor=anchor)


# ---------------- 카드 ----------------
def cover(c, data, n, total):
    im = background(11)
    header(im, data, n, total)
    put(im, c["photo"], 80, 130, 920, 720, radius=56, vfocus=0.25)
    d = ImageDraw.Draw(im)
    # 가격 배지 (금색 원)
    bx, by, r = 900, 200, 112
    d.ellipse((bx - r, by - r, bx + r, by + r), fill=GREEN, outline=GOLD, width=5)
    d.text((bx, by - 34), c["price"][0], font=jua(34), fill=GOLD_L, anchor="mm")
    d.text((bx, by + 18), c["price"][1], font=jua(46), fill=WHITE, anchor="mm")
    im.alpha_composite(mascot(170, wink=True), (96, 760))
    credit(im, data["credit"], 992, 862)
    d = ImageDraw.Draw(im)
    # 키커 (자간 넓힌 영문)
    k = "  ".join(list(c["kicker"]))
    d.text((W / 2, 900), k, font=sd(28, "semi"), fill=GOLD, anchor="ma")
    d.line((300, 916, 390, 916), fill=GOLD, width=2)
    d.line((690, 916, 780, 916), fill=GOLD, width=2)
    pill(d, W / 2, 950, c["tag"], sd(30), MINT, GREEN, padx=28, pady=12, center=True)
    y = title(im, c["title"], 1026, size=92, accent=1, center=True)
    d.text((W / 2, y + 2), c["sub"], font=sd(30, "semi"), fill=TEXT, anchor="ma")
    dots(im, n, total)
    return im


def claim(c, data, n, total):
    im = background(12)
    header(im, data, n, total)
    title(im, c["title"], 140, size=90, accent=1)
    put(im, c["photo"], 80, 400, 380, 720, radius=48, vfocus=0.3)
    credit(im, data["credit"], 460, 1150)
    d = ImageDraw.Draw(im)
    x0, y0, x1 = 500, 420, 1008
    pill(d, x0, y0, c["label"], sd(28), GOLD, WHITE, padx=22, pady=10)
    d.rounded_rectangle((x0, y0 + 80, x1, y0 + 470), 40, fill=WHITE, outline=GOLD_L, width=3)
    d.text((x0 + 36, y0 + 100), "“", font=sd(120), fill=GOLD)
    y = y0 + 190
    for ln in c["quote"]:
        jtext(d, x0 + 40, y, ln, 50, GREEN_D)
        y += 66
    y = y0 + 510
    for t in c["chips"]:
        pill(d, x0, y, t, sd(28), MINT, GREEN, padx=24, pady=12)
        y += 70
    im.alpha_composite(mascot(150), (840, 230))
    note(im, c["note"] + " " + data["warning"])
    dots(im, n, total)
    return im


def evidence(c, data, n, total):
    im = background(13)
    header(im, data, n, total)
    title(im, c["title"], 130, size=84, accent=1)
    put(im, c["photo"], 80, 360, 920, 380, radius=44, vfocus=0.55)
    credit(im, "ⓒ유한양행 보도자료 이미지", 992, 760)
    d = ImageDraw.Draw(im)
    y = 800
    maxw = 470
    for b in c["bars"]:
        d.text((80, y), b["name"], font=sd(32), fill=GREEN_D)
        y += 50
        top = max(b["test"], b["ctrl"])
        for val, col, lab in ((b["test"], GREEN, c["legend"][0]), (b["ctrl"], GRAY, c["legend"][1])):
            d.text((80, y + 6), lab, font=sd(24, "semi"), fill=SUB)
            bw = max(24, int(maxw * val / top))
            d.rounded_rectangle((260, y, 260 + bw, y + 40), 20, fill=col)
            jtext(d, 260 + bw + 16, y + 2, f"+{val:g} {b['unit']}", 34, GREEN if col == GREEN else SUB)
            y += 54
        y += 18
    note(im, c["note"])
    dots(im, n, total)
    return im


def howto(c, data, n, total):
    im = background(14)
    header(im, data, n, total)
    title(im, c["title"], 140, size=90, accent=1)
    put(im, c["photo"], 520, 150, 480, 420, radius=44, vfocus=0.5, hfocus=0.6)
    credit(im, data["credit"], 992, 590)
    d = ImageDraw.Draw(im)
    y = 640
    for i, (a, b) in enumerate(c["steps"]):
        d.rounded_rectangle((80, y, W - 80, y + 120), 36, fill=WHITE, outline=GOLD_L, width=2)
        d.ellipse((108, y + 24, 180, y + 96), fill=GREEN if i < 2 else GOLD)
        d.text((144, y + 62), str(i + 1), font=jua(44), fill=WHITE, anchor="mm")
        d.text((208, y + 22), a, font=jua(44), fill=GREEN_D)
        d.text((208 + tw(d, a, jua(44)) + 18, y + 36), b, font=sd(32, "semi"), fill=TEXT)
        y += 140
    x = 80
    for t in c["chips"]:
        x, _ = pill(d, x, y + 6, t, sd(28), MINT, GREEN, padx=24, pady=12)
        x += 14
    im.alpha_composite(mascot(130, wink=True), (W - 80 - 130, y - 4))
    note(im, c["note"])
    dots(im, n, total)
    return im


def price(c, data, n, total):
    im = background(15)
    header(im, data, n, total)
    put(im, c["photo"], 80, 130, 920, 400, radius=48, vfocus=0.2)
    credit(im, data["credit"], 992, 552)
    d = ImageDraw.Draw(im)
    y = 600
    for i, r in enumerate(c["rows"]):
        d.rounded_rectangle((80, y, W - 80, y + 170), 40, fill=WHITE if i else GREEN, outline=GOLD, width=3)
        fg = WHITE if i == 0 else GREEN_D
        sub = GOLD_L if i == 0 else SUB
        d.text((120, y + 30), r["label"], font=sd(30, "semi"), fill=sub)
        lw = tw(d, r["list"], sd(28, "reg"))
        d.text((120, y + 84), r["list"], font=sd(28, "reg"), fill=sub)
        d.line((118, y + 102, 122 + lw, y + 102), fill=sub, width=2)
        d.text((W - 120, y + 52), r["sale"], font=jua(84), fill=fg, anchor="ra")
        pill(d, 120 + lw + 20, y + 76, r["off"], sd(26), GOLD, WHITE, padx=16, pady=6)
        y += 196
    d.text((W / 2, y + 4), c["deal_note"], font=sd(23, "reg"), fill=SUB, anchor="ma")
    jtext(d, W / 2, y + 62, c["cta"], 54, GREEN, anchor="ma")
    im.alpha_composite(mascot(110), (W - 80 - 110, 470))
    d = ImageDraw.Draw(im)
    d.text((W / 2, y + 150), data["warning"], font=sd(25, "semi"), fill=TEXT, anchor="ma")
    d.text((W / 2, y + 192), c["source"], font=sd(21, "reg"), fill=SUB, anchor="ma")
    dots(im, n, total)
    return im


RENDER = {"cover": cover, "claim": claim, "evidence": evidence, "howto": howto, "price": price}


def main():
    data = json.loads((ROOT / "src/cards.json").read_text())
    cards = data["cards"]
    out = []
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](c, data, i, len(cards)).convert("RGB")
        im.save(ROOT / f"{i:02d}.png")
        out.append(im)
    out[0].save(ROOT / "cover_preview.jpg", quality=90)
    cols, sc = 3, 0.34
    a, b = int(W * sc), int(H * sc)
    rows = math.ceil(len(out) / cols)
    sheet = Image.new("RGB", (cols * a + (cols + 1) * 16, rows * b + (rows + 1) * 16), (236, 238, 234))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (16 + (i % cols) * (a + 16), 16 + (i // cols) * (b + 16)))
    sheet.save(ROOT / "preview.jpg", quality=90)
    print("ok", len(out))


if __name__ == "__main__":
    main()
