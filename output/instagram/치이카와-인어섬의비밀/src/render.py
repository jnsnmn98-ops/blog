"""밝고 발랄한 카드뉴스 렌더러 — 극장판 치이카와: 인어 섬의 비밀.
공식 스틸·포스터를 크게 쓰고, 하늘·바다·모래 색 장식은 직접 그린다(캐릭터는 그리지 않음).
실행: python src/render.py  (주제 폴더에서)
"""
import json
import math
import pathlib
import random
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1350
K = 2

SKY1 = (205, 236, 255)
SKY2 = (255, 247, 222)
SEA = (88, 176, 236)
SEA_L = (170, 220, 250)
NAVY = (36, 62, 112)
TEXT = (52, 66, 98)
SUB = (110, 124, 150)
CORAL = (255, 126, 150)
PINK_L = (255, 216, 226)
YELLOW = (255, 214, 86)
YELLOW_L = (255, 238, 170)
WHITE = (255, 255, 255)

JUA = str(ROOT / "assets/fonts/Jua-Regular.ttf")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FALLBACK = set("·℃~…“”'")


def k(v):
    return int(round(v * K))


def jua(s):
    return ImageFont.truetype(JUA, k(s))


def sd(s, w="semi"):
    return ImageFont.truetype(SD, k(s), index={"bold": 6, "semi": 4, "reg": 0}[w])


def runs(text):
    out = []
    for ch in text:
        fb = ch in FALLBACK
        if out and out[-1][0] == fb:
            out[-1][1] += ch
        else:
            out.append([fb, ch])
    return out


def tl(d, t, f):
    return d.textlength(t, font=f) / K


def jw(d, text, size):
    return sum(tl(d, t, sd(size, "bold") if fb else jua(size)) for fb, t in runs(text))


def jtext(d, x, y, text, size, fill, anchor="l"):
    w = jw(d, text, size)
    if anchor == "m":
        x -= w / 2
    elif anchor == "r":
        x -= w
    base = y + jua(size).getmetrics()[0] / K
    for fb, t in runs(text):
        f = sd(size, "bold") if fb else jua(size)
        d.text((k(x), k(base)), t, font=f, fill=fill, anchor="ls")
        x += tl(d, t, f)
    return w


def rr(d, x0, y0, x1, y1, r, fill=None, outline=None, lw=4):
    d.rounded_rectangle((k(x0), k(y0), k(x1), k(y1)), k(r), fill=fill, outline=outline, width=k(lw) if outline else 0)


def circle(d, cx, cy, r, fill, outline=None, lw=3):
    d.ellipse((k(cx - r), k(cy - r), k(cx + r), k(cy + r)), fill=fill, outline=outline, width=k(lw) if outline else 0)


def sparkle(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr_ = r if i % 2 == 0 else r * 0.32
        pts.append((k(cx + rr_ * math.cos(a)), k(cy + rr_ * math.sin(a))))
    d.polygon(pts, fill=color)


def burst(d, cx, cy, r, fill, lines, size=36, color=NAVY, angle=0):
    pts = []
    n = 16
    for i in range(n * 2):
        a = math.pi * i / n + angle
        rr_ = r if i % 2 == 0 else r * 0.82
        pts.append((k(cx + rr_ * math.cos(a)), k(cy + rr_ * math.sin(a))))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=WHITE, width=k(5), joint="curve")
    y = cy - (len(lines) * (size + 6)) / 2
    for ln in lines:
        jtext(d, cx, y, ln, size, color, anchor="m")
        y += size + 6


def waves(d, y, color, amp=16, length=120, phase=0):
    pts = [(0, k(H))]
    for x in range(0, W + 10, 6):
        pts.append((k(x), k(y + amp * math.sin((x + phase) / length * 2 * math.pi))))
    pts.append((k(W), k(H)))
    d.polygon(pts, fill=color)


def background(seed, sea=True):
    im = Image.new("RGB", (k(W), k(H)))
    d = ImageDraw.Draw(im)
    for y in range(0, k(H), 2):
        t = y / k(H)
        d.line([(0, y), (k(W), y)], fill=tuple(int(SKY1[i] + (SKY2[i] - SKY1[i]) * t) for i in range(3)), width=2)
    rnd = random.Random(seed)
    # 구름
    for _ in range(3):
        cx, cy = rnd.randint(60, W - 60), rnd.randint(120, 520)
        for dx, dy, r in ((-40, 10, 34), (0, 0, 46), (44, 10, 34)):
            circle(d, cx + dx, cy + dy, r, (255, 255, 255))
    if sea:
        waves(d, H - 150, SEA_L, amp=14, length=160, phase=seed * 40)
        waves(d, H - 110, SEA, amp=12, length=120, phase=seed * 70)
    # 반짝이·물방울
    for _ in range(8):
        sparkle(d, rnd.randint(40, W - 40), rnd.randint(110, H - 220), rnd.randint(8, 16), rnd.choice([YELLOW, WHITE, PINK_L]))
    return im, d


def fit(path, w, h, vfocus=0.5, hfocus=0.5):
    img = Image.open(ROOT / path).convert("RGB")
    sc = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * sc)), max(h, round(img.height * sc))), Image.LANCZOS)
    x = int((img.width - w) * hfocus)
    y = int((img.height - h) * vfocus)
    return img.crop((x, y, x + w, y + h))


def photo(im, path, x, y, w, h, angle=0, radius=40, border=12, vfocus=0.5, hfocus=0.5):
    ph = fit(path, k(w), k(h), vfocus, hfocus)
    W2, H2 = k(w + border * 2), k(h + border * 2)
    card = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    m = Image.new("L", (W2, H2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, W2 - 1, H2 - 1), k(radius + border), fill=255)
    card.paste(Image.new("RGBA", (W2, H2), WHITE + (255,)), (0, 0), m)
    m2 = Image.new("L", ph.size, 0)
    ImageDraw.Draw(m2).rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), k(radius), fill=255)
    card.paste(ph, (k(border), k(border)), m2)
    pad = k(40)
    out = Image.new("RGBA", (W2 + pad * 2, H2 + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + k(14), pad + W2, pad + H2 + k(14)), k(radius + border), fill=(40, 90, 150, 70))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(k(14))))
    out.alpha_composite(card, (pad, pad))
    if angle:
        out = out.rotate(angle, resample=Image.BICUBIC, expand=True)
    cx, cy = k(x + w / 2), k(y + h / 2)
    base = im.convert("RGBA")
    base.alpha_composite(out, (int(cx - out.width / 2), int(cy - out.height / 2)))
    return base.convert("RGB")


def header(d, data, n, total):
    rr(d, 56, 48, 56 + 150, 94, 23, fill=CORAL)
    jtext(d, 56 + 75, 52, "애니 소식", 30, WHITE, anchor="m")
    d.text((k(222), k(58)), data["account"], font=sd(26), fill=SUB)
    d.text((k(W - 56), k(58)), f"{n} / {total}", font=sd(26), fill=SUB, anchor="ra")


def dots(d, n, total):
    gap = 24
    x0 = W / 2 - (total - 1) * gap / 2
    for i in range(total):
        if i == n - 1:
            rr(d, x0 + i * gap - 14, H - 52, x0 + i * gap + 14, H - 42, 5, fill=WHITE)
        else:
            circle(d, x0 + i * gap, H - 47, 5, (210, 235, 252))


def credit(d, data, x, y, anchor="ra", color=SUB):
    d.text((k(x), k(y)), data["credit"], font=sd(20, "reg"), fill=color, anchor=anchor)


def title(d, lines, y, size=86, accent=1, center=False, x=72):
    for i, line in enumerate(lines):
        w = jw(d, line, size)
        lx = (W - w) / 2 if center else x
        if i == accent:
            rr(d, lx - 10, y + size * 0.55, lx + w + 10, y + size * 1.0, 16, fill=YELLOW_L)
        jtext(d, lx, y, line, size, CORAL if i == accent else NAVY)
        y += int(size * 1.16)
    return y


def flow(d, text, x, y, maxw, size=36, color=TEXT, hl=CORAL):
    """**강조** 지원 줄바꿈."""
    tokens = []
    for part in re.split(r"(\*\*.+?\*\*)", text):
        if not part:
            continue
        em = part.startswith("**")
        for wd in part.strip("*").split(" "):
            if wd:
                tokens.append((wd, em))
    f, fb = sd(size, "semi"), sd(size, "bold")
    cx, cy = x, y
    for wd, em in tokens:
        font = fb if em else f
        w = tl(d, wd + " ", font)
        if cx + w - x > maxw:
            cx, cy = x, cy + size + 18
        d.text((k(cx), k(cy)), wd, font=font, fill=hl if em else color)
        cx += w
    return cy + size + 18


# ---------------- 카드 ----------------
def c_cover(c, data, n, total):
    im, d = background(1, sea=True)
    im = photo(im, c["photo"], 70, 130, 940, 600, angle=-2, radius=44, vfocus=0.4)
    d = ImageDraw.Draw(im)
    header(d, data, n, total)
    credit(d, data, 1000, 752)
    burst(d, 880, 690, 120, YELLOW, c["burst"], size=36, angle=0.2)
    x = 72
    for t in c["tags"]:
        w = jw(d, t, 30) + 44
        rr(d, x, 800, x + w, 850, 25, fill=WHITE, outline=SEA, lw=3)
        jtext(d, x + w / 2, 806, t, 30, SEA, anchor="m")
        x += w + 12
    y = title(d, c["title"], 870, size=96, accent=1)
    jtext(d, 76, y + 4, c["sub"], 38, TEXT)
    dots(d, n, total)
    return im


def c_info(c, data, n, total):
    im, d = background(2, sea=True)
    header(d, data, n, total)
    title(d, c["title"], 130, size=84, accent=1)
    im = photo(im, c["photo"], 80, 370, 400, 570, angle=-3, radius=30, vfocus=0.0)
    d = ImageDraw.Draw(im)
    credit(d, data, 500, 985)
    y = 380
    for i, (a, b) in enumerate(c["rows"]):
        rr(d, 540, y, 1010, y + 130, 30, fill=WHITE, outline=(214, 236, 252), lw=3)
        rr(d, 566, y + 22, 566 + jw(d, a, 28) + 36, y + 64, 21, fill=[CORAL, SEA, YELLOW, CORAL][i])
        jtext(d, 566 + (jw(d, a, 28) + 36) / 2, y + 25, a, 28, WHITE if i != 2 else NAVY, anchor="m")
        jtext(d, 570, y + 76, b, 34, NAVY)
        y += 146
    d.text((k(W / 2), k(1040)), c["note"], font=sd(25, "semi"), fill=TEXT, anchor="ma")
    dots(d, n, total)
    return im


def c_story(c, data, n, total):
    im, d = background(3, sea=True)
    im = photo(im, c["photo"], 70, 130, 940, 520, angle=1.5, radius=44, vfocus=0.5)
    d = ImageDraw.Draw(im)
    header(d, data, n, total)
    credit(d, data, 1000, 680)
    rr(d, 72, 720, 72 + 150, 768, 24, fill=SEA)
    jtext(d, 72 + 75, 724, c["no"], 30, WHITE, anchor="m")
    y = title(d, c["title"], 784, size=80, accent=1)
    flow(d, c["text"], 76, y + 10, 930, size=36)
    burst(d, 930, 800, 92, PINK_L, c["badge"], size=30, color=CORAL, angle=0.1)
    dots(d, n, total)
    return im


def c_friends(c, data, n, total):
    im, d = background(4, sea=True)
    header(d, data, n, total)
    title(d, c["title"], 130, size=84, accent=1)
    im = photo(im, c["photo"], 70, 370, 940, 500, angle=-1.5, radius=44, vfocus=0.5)
    d = ImageDraw.Draw(im)
    credit(d, data, 1000, 900)
    x, y = 72, 940
    cols = [CORAL, SEA, YELLOW]
    for i, t in enumerate(c["chips"]):
        w = jw(d, t, 32) + 48
        if x + w > W - 72:
            x, y = 72, y + 66
        col = cols[i % 3]
        rr(d, x, y, x + w, y + 54, 27, fill=col)
        jtext(d, x + w / 2, y + 9, t, 32, WHITE if col != YELLOW else NAVY, anchor="m")
        x += w + 12
    flow(d, c["text"], 76, y + 82, 930, size=32, color=TEXT)
    dots(d, n, total)
    return im


def c_box(c, data, n, total):
    im, d = background(5, sea=True)
    header(d, data, n, total)
    title(d, c["title"], 130, size=84, accent=1)
    im = photo(im, c["photo"], 600, 360, 410, 300, angle=4, radius=36, vfocus=0.5, hfocus=0.55)
    d = ImageDraw.Draw(im)
    credit(d, data, 1000, 700)
    y = 380
    for i, (a, b) in enumerate(c["stats"]):
        w = 500 if i < 2 else 940
        x0 = 72
        if i == 2:
            y = 730
        rr(d, x0, y, x0 + w, y + 150, 36, fill=WHITE, outline=[CORAL, SEA, YELLOW][i], lw=5)
        jtext(d, x0 + 32, y + 18, a, 66, [CORAL, SEA, NAVY][i])
        d.text((k(x0 + 34), k(y + 104)), b, font=sd(28, "semi"), fill=TEXT)
        y += 172
    sparkle(d, 560, 400, 18, YELLOW)
    d.text((k(W / 2), k(1060)), c["note"], font=sd(23, "reg"), fill=TEXT, anchor="ma")
    dots(d, n, total)
    return im


def c_end(c, data, n, total):
    im, d = background(6, sea=True)
    header(d, data, n, total)
    im = photo(im, c["photo"], 320, 120, 440, 620, angle=2, radius=30, vfocus=0.0)
    d = ImageDraw.Draw(im)
    credit(d, data, W / 2, 784, anchor="ma")
    sparkle(d, 220, 300, 26, YELLOW)
    sparkle(d, 880, 520, 22, CORAL)
    sparkle(d, 200, 600, 16, SEA)
    y = title(d, c["title"], 818, size=80, accent=1, center=True)
    rr(d, 150, y + 10, W - 150, y + 82, 36, fill=CORAL)
    jtext(d, W / 2, y + 22, c["cta"], 34, WHITE, anchor="m")
    d.text((k(W / 2), k(y + 104)), c["note"], font=sd(24, "semi"), fill=TEXT, anchor="ma")
    d.text((k(W / 2), k(y + 142)), c["source"], font=sd(19, "reg"), fill=SUB, anchor="ma")
    dots(d, n, total)
    return im


RENDER = {"cover": c_cover, "info": c_info, "story": c_story, "friends": c_friends, "boxoffice": c_box, "end": c_end}


def main():
    data = json.loads((ROOT / "src/cards.json").read_text())
    cards = data["cards"]
    out = []
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](c, data, i, len(cards)).resize((W, H), Image.LANCZOS)
        im.save(ROOT / f"{i:02d}.png")
        out.append(im)
    out[0].save(ROOT / "cover_preview.jpg", quality=92)
    cols, sc = 3, 0.34
    a, b = int(W * sc), int(H * sc)
    rows = math.ceil(len(out) / cols)
    sheet = Image.new("RGB", (cols * a + (cols + 1) * 14, rows * b + (rows + 1) * 14), (230, 240, 250))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (14 + (i % cols) * (a + 14), 14 + (i // cols) * (b + 14)))
    sheet.save(ROOT / "preview.jpg", quality=90)
    print("ok", len(out))


if __name__ == "__main__":
    main()
