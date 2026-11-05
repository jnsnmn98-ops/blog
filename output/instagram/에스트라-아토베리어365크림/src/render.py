"""귀여운 파스텔 카드뉴스 렌더러 — 에스트라 아토베리어365 크림.
실행: python src/render.py  (주제 폴더에서)
"""
import json
import math
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1350
SKY1, SKY2 = (238, 245, 255), (214, 230, 255)
NAVY = (38, 52, 128)
BLUE = (74, 96, 206)
PINK = (255, 126, 170)
PINK_L = (255, 214, 228)
TEXT = (52, 62, 98)
SUB = (106, 116, 150)
WHITE = (255, 255, 255)

JUA = str(ROOT / "assets/fonts/Jua-Regular.ttf")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def jua(size):
    return ImageFont.truetype(JUA, size)


def sd(size, weight="bold"):
    return ImageFont.truetype(SD, size, index={"bold": 6, "semi": 4, "reg": 0}[weight])


def background(seed):
    rnd = random.Random(seed)
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(SKY1[i] + (SKY2[i] - SKY1[i]) * t) for i in range(3)))
    im = im.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # 구름 같은 흰 원
    for _ in range(5):
        x, y, r = rnd.randint(-80, W), rnd.randint(-80, H), rnd.randint(90, 180)
        ld.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 70))
    # 물방울 점
    for _ in range(26):
        x, y, r = rnd.randint(20, W - 20), rnd.randint(20, H - 20), rnd.randint(4, 9)
        ld.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 150))
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    im.alpha_composite(layer)
    return im


def sparkle(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=color)


def mascot(size, mood="smile"):
    """물방울 캐릭터 (직접 그린 장식)."""
    s = size * 4
    im = Image.new("RGBA", (s, int(s * 1.25)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = (150, 196, 255, 255)
    cx, cy, r = s / 2, s * 0.78, s * 0.42
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=body)
    d.polygon([(cx, s * 0.05), (cx - r * 0.93, cy - r * 0.35), (cx + r * 0.93, cy - r * 0.35)], fill=body)
    d.ellipse((cx - r * 0.62, cy - r * 0.72, cx - r * 0.3, cy - r * 0.3), fill=(255, 255, 255, 200))
    ey = cy + r * 0.05
    for ex in (cx - r * 0.33, cx + r * 0.33):
        d.ellipse((ex - s * 0.035, ey - s * 0.05, ex + s * 0.035, ey + s * 0.05), fill=(40, 46, 80, 255))
    for bx in (cx - r * 0.58, cx + r * 0.58):
        d.ellipse((bx - s * 0.06, ey + s * 0.05, bx + s * 0.06, ey + s * 0.1), fill=(255, 150, 185, 220))
    d.arc((cx - s * 0.08, ey + s * 0.02, cx + s * 0.08, ey + s * 0.13), 20, 160, fill=(40, 46, 80, 255), width=int(s * 0.018))
    return im.resize((size, int(size * 1.25)), Image.LANCZOS)


def fit(img, w, h, vfocus=0.5):
    img = img.convert("RGB")
    sc = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * sc)), max(h, round(img.height * sc))), Image.LANCZOS)
    x = (img.width - w) // 2
    y = int((img.height - h) * vfocus)
    return img.crop((x, y, x + w, y + h))


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


def sticker(path, w, h, angle=0, border=14, radius=40, vfocus=0.5):
    """흰 테두리 + 그림자 + 살짝 기울인 사진 스티커."""
    ph = fit(Image.open(ROOT / path), w, h, vfocus)
    W2, H2 = w + border * 2, h + border * 2
    card = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    card.paste(Image.new("RGBA", (W2, H2), WHITE + (255,)), (0, 0), rounded_mask(W2, H2, radius + border))
    card.paste(ph, (border, border), rounded_mask(w, h, radius))
    pad = 40
    out = Image.new("RGBA", (W2 + pad * 2, H2 + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + W2, pad + H2 + 14), radius + border, fill=(60, 80, 160, 70))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    out.alpha_composite(card, (pad, pad))
    if angle:
        out = out.rotate(angle, resample=Image.BICUBIC, expand=True)
    return out


def paste_center(im, obj, cx, cy):
    im.alpha_composite(obj, (int(cx - obj.width / 2), int(cy - obj.height / 2)))


def tw(d, text, font):
    b = d.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def pill(d, x, y, text, font, fill, color, padx=26, pady=12, center=False):
    w = tw(d, text, font)
    b = d.textbbox((0, 0), text, font=font)
    h = b[3] - b[1]
    if center:
        x = x - (w + padx * 2) / 2
    d.rounded_rectangle((x, y, x + w + padx * 2, y + h + pady * 2), (h + pady * 2) / 2, fill=fill)
    d.text((x + padx, y + pady - b[1]), text, font=font, fill=color)
    return x + w + padx * 2, y + h + pady * 2


def header(im, data, n, total):
    d = ImageDraw.Draw(im)
    x, _ = pill(d, 56, 44, data["ad_label"], sd(26), PINK, WHITE, padx=20, pady=8)
    d.text((x + 16, 50), data["account"], font=sd(26, "semi"), fill=SUB)
    pill(d, W - 56 - 100, 44, f"{n} / {total}", sd(26, "semi"), (255, 255, 255, 230), SUB, padx=22, pady=8)


def dots(im, n, total):
    d = ImageDraw.Draw(im)
    gap = 26
    x0 = W / 2 - (total - 1) * gap / 2
    for i in range(total):
        r = 7 if i == n - 1 else 5
        c = BLUE if i == n - 1 else (180, 192, 230)
        d.ellipse((x0 + i * gap - r, H - 40 - r, x0 + i * gap + r, H - 40 + r), fill=c)


def title(im, lines, y, size=92, accent=1, center=False, x=72):
    d = ImageDraw.Draw(im)
    f = jua(size)
    for i, line in enumerate(lines):
        w = tw(d, line, f)
        lx = (W - w) / 2 if center else x
        if i == accent:
            # 형광펜 밑줄
            d.rounded_rectangle((lx - 10, y + size * 0.55, lx + w + 10, y + size * 1.02), 18, fill=PINK_L)
        d.text((lx, y), line, font=f, fill=NAVY if i != accent else BLUE)
        y += int(size * 1.18)
    return y


def note(im, text, y=None, size=26):
    d = ImageDraw.Draw(im)
    f = sd(size, "reg")
    y = y or H - 128
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tw(d, t, f) > W - 144:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    y -= (len(lines) - 1) * (size + 10)
    for ln in lines:
        d.text((72, y), ln, font=f, fill=SUB)
        y += size + 10


def credit(im, text, x, y):
    d = ImageDraw.Draw(im)
    d.text((x, y), text, font=sd(22, "reg"), fill=SUB, anchor="ra")


def deco(im, seed):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im)
    for _ in range(4):
        sparkle(d, rnd.randint(40, W - 40), rnd.randint(120, H - 160), rnd.randint(12, 22),
                rnd.choice([PINK, (255, 196, 120), BLUE, (255, 255, 255)]))


# ---------------- 카드 ----------------
def cover(c, data, n, total):
    im = background(1)
    d = ImageDraw.Draw(im)
    # 큰 흰 원 안에 제품
    cx, cy, r = 540, 520, 370
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - r, cy - r + 18, cx + r, cy + r + 18), fill=(60, 80, 160, 60))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE)
    prod = Image.open(ROOT / c["photo"]).convert("RGB").resize((660, 660), Image.LANCZOS)
    m = Image.new("L", prod.size, 0)
    ImageDraw.Draw(m).ellipse((10, 10, 650, 650), fill=255)
    im.paste(prod, (cx - 330, cy - 330), m)
    # 가격 배지
    badge = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    pts = []
    for i in range(32):
        ang = math.pi * 2 * i / 32
        rr = 138 if i % 2 == 0 else 124
        pts.append((150 + rr * math.cos(ang), 150 + rr * math.sin(ang)))
    bd.polygon(pts, fill=PINK)
    bd.text((150, 112), c["price"][0], font=jua(38), fill=WHITE, anchor="mm")
    bd.text((150, 168), c["price"][1], font=jua(56), fill=WHITE, anchor="mm")
    paste_center(im, badge.rotate(12, resample=Image.BICUBIC), 880, 250)
    paste_center(im, mascot(150), 190, 790)
    d = ImageDraw.Draw(im)
    sparkle(d, 150, 230, 26, (255, 196, 120))
    sparkle(d, 960, 760, 20, BLUE)
    sparkle(d, 930, 830, 12, PINK)
    header(im, data, n, total)
    pill(d, W / 2, 925, c["tag"], sd(32), BLUE, WHITE, padx=30, pady=12, center=True)
    y = title(im, c["title"], 1000, size=96, accent=1, center=True)
    d.text((W / 2, y + 6), c["sub"], font=sd(34, "semi"), fill=TEXT, anchor="ma")
    credit(im, data["credit"], W - 60, H - 66)
    dots(im, n, total)
    return im


def stats(c, data, n, total):
    im = background(2)
    header(im, data, n, total)
    title(im, c["title"], 130, size=88, accent=c["accent_line"])
    paste_center(im, sticker(c["photo"], 330, 650, angle=-3, radius=36, vfocus=0.3), 255, 760)
    d = ImageDraw.Draw(im)
    x0, y = 470, 420
    for i, (num, label) in enumerate(c["stats"]):
        d.rounded_rectangle((x0 + 8, y + 10, x0 + 548, y + 200), 44, fill=(160, 180, 235))
        d.rounded_rectangle((x0, y, x0 + 540, y + 190), 44, fill=WHITE)
        d.text((x0 + 40, y + 22), num, font=jua(84), fill=PINK if i == 0 else BLUE)
        d.text((x0 + 42, y + 128), label, font=sd(32, "semi"), fill=TEXT)
        y += 222
    sparkle(d, 1000, 400, 18, PINK)
    paste_center(im, mascot(110), 960, 1110)
    credit(im, data["credit"], 400, 1110)
    note(im, c["note"])
    dots(im, n, total)
    return im


def ingredient(c, data, n, total):
    im = background(3)
    header(im, data, n, total)
    title(im, c["title"], 130, size=88, accent=c["accent_line"])
    paste_center(im, sticker(c["photo"], 860, 480, angle=2, radius=44), 540, 660)
    d = ImageDraw.Draw(im)
    y = 950
    for ln in c["text"]:
        d.text((W / 2, y), ln, font=sd(38, "semi"), fill=TEXT, anchor="ma")
        y += 54
    f = sd(30)
    widths = [tw(d, t, f) + 56 for t in c["chips"]]
    x = (W - (sum(widths) + 18 * (len(widths) - 1))) / 2
    for t, w in zip(c["chips"], widths):
        pill(d, x, y + 26, t, f, WHITE, BLUE, padx=28, pady=14)
        x += w + 18
    paste_center(im, mascot(100), 120, 1010)
    sparkle(d, 990, 960, 18, PINK)
    credit(im, data["credit"], W - 60, 912)
    note(im, c["note"])
    dots(im, n, total)
    return im


def women(c, data, n, total):
    im = background(4)
    header(im, data, n, total)
    title(im, c["title"], 130, size=88, accent=c["accent_line"])
    paste_center(im, sticker(c["photos"][0], 420, 400, angle=-4, radius=36, vfocus=0.2), 300, 600)
    paste_center(im, sticker(c["photos"][1], 420, 400, angle=4, radius=36, vfocus=0.2), 780, 630)
    d = ImageDraw.Draw(im)
    for hx, hy in ((560, 420), (600, 455)):
        sparkle(d, hx, hy, 18, PINK)
    y = 880
    w, gap = 300, 24
    x = (W - (w * 3 + gap * 2)) / 2
    for i, (num, l1, l2) in enumerate(c["stats"]):
        d.rounded_rectangle((x + 6, y + 10, x + w + 6, y + 260), 48, fill=(160, 180, 235))
        d.rounded_rectangle((x, y, x + w, y + 250), 48, fill=WHITE)
        d.text((x + w / 2, y + 26), num, font=jua(84), fill=PINK if i < 2 else BLUE, anchor="ma")
        d.text((x + w / 2, y + 132), l1, font=sd(30, "semi"), fill=TEXT, anchor="ma")
        d.text((x + w / 2, y + 174), l2, font=sd(30, "semi"), fill=TEXT, anchor="ma")
        x += w + gap
    credit(im, data["credit"], W - 60, 852)
    note(im, c["note"])
    dots(im, n, total)
    return im


def howto(c, data, n, total):
    im = background(5)
    header(im, data, n, total)
    title(im, c["title"], 130, size=88, accent=c["accent_line"])
    paste_center(im, sticker(c["photo"], 380, 470, angle=3, radius=40, vfocus=0.4), 790, 640)
    d = ImageDraw.Draw(im)
    y = 430
    for i, (l1, l2) in enumerate(c["steps"]):
        d.ellipse((72, y, 152, y + 80), fill=PINK if i == 0 else BLUE)
        d.text((112, y + 42), str(i + 1), font=jua(52), fill=WHITE, anchor="mm")
        d.text((176, y + 2), l1, font=sd(34), fill=NAVY)
        d.text((176, y + 50), l2, font=sd(32, "semi"), fill=TEXT)
        y += 190
    paste_center(im, mascot(110), 150, 840)
    d.rounded_rectangle((72, 935, W - 72, 1150), 44, fill=WHITE)
    d.text((W / 2, 965), c["for_title"], font=jua(46), fill=BLUE, anchor="ma")
    f = sd(30)
    widths = [tw(d, t, f) + 56 for t in c["chips"]]
    x = (W - (sum(widths) + 16 * (len(widths) - 1))) / 2
    for t, w in zip(c["chips"], widths):
        pill(d, x, 1046, t, f, PINK_L, NAVY, padx=28, pady=14)
        x += w + 16
    credit(im, data["credit"], W - 60, 900)
    note(im, c["note"])
    dots(im, n, total)
    return im


def price(c, data, n, total):
    im = background(6)
    header(im, data, n, total)
    paste_center(im, sticker(c["photo"], 880, 440, angle=-2, radius=44, vfocus=0.95), 540, 400)
    d = ImageDraw.Draw(im)
    credit(im, data["credit"], W - 60, 646)
    # 가격표
    x0, y0, x1, y1 = 120, 690, 960, 1060
    d.rounded_rectangle((x0 + 8, y0 + 12, x1 + 8, y1 + 12), 56, fill=(160, 180, 235))
    d.rounded_rectangle((x0, y0, x1, y1), 56, fill=WHITE)
    d.ellipse((x0 + 40, y0 + 36, x0 + 72, y0 + 68), fill=SKY2)
    d.text((W / 2, y0 + 34), c["volume"], font=sd(32, "semi"), fill=SUB, anchor="ma")
    d.text((W / 2, y0 + 84), c["price"], font=jua(128), fill=NAVY, anchor="ma")
    pill(d, W / 2, y0 + 236, c["deal"], sd(32), PINK, WHITE, padx=30, pady=12, center=True)
    d.text((W / 2, y0 + 316), c["deal_date"] + " · " + c["deal_note"], font=sd(24, "reg"), fill=SUB, anchor="ma")
    paste_center(im, mascot(96), 1004, 1118)
    sparkle(d, 92, 700, 20, PINK)
    d.text((W / 2, 1110), c["cta"], font=jua(54), fill=BLUE, anchor="ma")
    d.text((W / 2, 1210), c["source"], font=sd(22, "reg"), fill=SUB, anchor="ma")
    dots(im, n, total)
    return im


RENDER = {"cover": cover, "stats": stats, "ingredient": ingredient, "women": women, "howto": howto, "price": price}


def main():
    data = json.loads((ROOT / "src/cards.json").read_text())
    cards = data["cards"]
    out = []
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](c, data, i, len(cards)).convert("RGB")
        p = ROOT / f"{i:02d}.png"
        im.save(p)
        out.append(im)
    im0 = out[0]
    im0.save(ROOT / "cover_preview.jpg", quality=90)
    cols, sc = 3, 0.34
    tw_, th_ = int(W * sc), int(H * sc)
    sheet = Image.new("RGB", (cols * tw_ + (cols + 1) * 16, 2 * th_ + 3 * 16), (240, 242, 248))
    for i, im in enumerate(out):
        sheet.paste(im.resize((tw_, th_), Image.LANCZOS), (16 + (i % cols) * (tw_ + 16), 16 + (i // cols) * (th_ + 16)))
    sheet.save(ROOT / "preview.jpg", quality=90)
    print("ok", len(out))


if __name__ == "__main__":
    main()
