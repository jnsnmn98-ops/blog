"""인스타툰 렌더러 — 환절기 주의사항 (캐릭터 '콩이'를 직접 그림).
2배 크기로 그린 뒤 줄여서 선을 부드럽게 만든다.
실행: python src/render.py  (주제 폴더에서)
"""
import json
import math
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1350
K = 2  # 슈퍼샘플링 배율

OUT = (62, 48, 42)
CREAM = (255, 249, 238)
CREAM2 = (252, 240, 222)
WHITE = (255, 255, 255)
BODY = (255, 253, 247)
BLUSH = (255, 168, 178)
PINK = (255, 196, 205)
CORAL = (255, 122, 96)
SKY = (205, 228, 255)
NIGHT = (176, 196, 238)
SUN = (255, 211, 110)
MINT = (204, 238, 216)
GREEN = (98, 170, 120)
LEAF = (236, 150, 80)
BLUE = (110, 160, 230)
TEXT = (70, 58, 52)
SUB = (140, 124, 112)
HL = (255, 226, 140)

JUA = str(ROOT / "assets/fonts/Jua-Regular.ttf")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FALLBACK = set("·℃~…“”")


def k(v):
    return v * K


def jua(s):
    return ImageFont.truetype(JUA, int(s * K))


def sd(s, w="bold"):
    return ImageFont.truetype(SD, int(s * K), index={"bold": 6, "semi": 4, "reg": 0}[w])


# ---------- 글자 ----------
def runs(text):
    out = []
    for ch in text:
        fb = ch in FALLBACK
        if out and out[-1][0] == fb:
            out[-1][1] += ch
        else:
            out.append([fb, ch])
    return out


def width(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return (b[2] - b[0]) / K


def jw(d, text, size):
    return sum(width(d, t, sd(size) if fb else jua(size)) for fb, t in runs(text))


def jtext(d, x, y, text, size, fill, anchor="l"):
    w = jw(d, text, size)
    if anchor == "m":
        x -= w / 2
    elif anchor == "r":
        x -= w
    base = y + jua(size).getmetrics()[0] / K
    for fb, t in runs(text):
        f = sd(size) if fb else jua(size)
        d.text((k(x), k(base)), t, font=f, fill=fill, anchor="ls")
        x += width(d, t, f)
    return w


def stext(d, x, y, text, size, fill, w="semi", anchor="la"):
    d.text((k(x), k(y)), text, font=sd(size, w), fill=fill, anchor=anchor)


# ---------- 도형 ----------
def wobble_ellipse(d, cx, cy, rx, ry, fill, outline=OUT, lw=5, seed=0, amp=0.018):
    pts = []
    n = 90
    for i in range(n):
        t = 2 * math.pi * i / n
        r = 1 + amp * math.sin(3 * t + seed) + amp * 0.6 * math.sin(5 * t + seed * 1.7)
        pts.append((k(cx + rx * r * math.cos(t)), k(cy + ry * r * math.sin(t))))
    d.polygon(pts, fill=fill)
    if outline:
        d.line(pts + [pts[0]], fill=outline, width=k(lw), joint="curve")


def rrect(d, x0, y0, x1, y1, r, fill=None, outline=OUT, lw=5):
    d.rounded_rectangle((k(x0), k(y0), k(x1), k(y1)), k(r), fill=fill, outline=outline, width=k(lw) if outline else 0)


def line(d, pts, fill=OUT, lw=5):
    d.line([(k(x), k(y)) for x, y in pts], fill=fill, width=k(lw), joint="curve")


def arc(d, box, a0, a1, fill=OUT, lw=5):
    d.arc(tuple(k(v) for v in box), a0, a1, fill=fill, width=k(lw))


def circle(d, cx, cy, r, fill, outline=None, lw=4):
    d.ellipse((k(cx - r), k(cy - r), k(cx + r), k(cy + r)), fill=fill, outline=outline, width=k(lw) if outline else 0)


def sparkle(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((k(cx + rr * math.cos(a)), k(cy + rr * math.sin(a))))
    d.polygon(pts, fill=color)


def drop(d, cx, cy, r, color=BLUE):
    pts = [(k(cx), k(cy - r * 1.8))]
    for i in range(0, 181, 10):
        a = math.radians(i - 180 + 180)
        pts.append((k(cx + r * math.cos(math.radians(i))), k(cy + r * math.sin(math.radians(i)))))
    d.polygon(pts, fill=color)


def leaf(d, cx, cy, s, ang, color=LEAF):
    pts = []
    for i in range(0, 361, 15):
        t = math.radians(i)
        x, y = s * math.cos(t), s * 0.45 * math.sin(t) * (1 if i <= 180 else 1)
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append((k(cx + x * ca - y * sa), k(cy + x * sa + y * ca)))
    d.polygon(pts, fill=color)
    ca, sa = math.cos(ang), math.sin(ang)
    line(d, [(cx - s * ca, cy - s * sa), (cx + s * ca, cy + s * sa)], fill=(200, 110, 60), lw=2)


# ---------- 말풍선 ----------
def bubble(d, x, y, text, size=44, tail=(0, 60), fill=WHITE, center=True):
    """(x, y)는 말풍선 가운데. tail은 꼬리 끝의 상대 위치."""
    tw_ = jw(d, text, size)
    w, h = tw_ + 64, size + 44
    x0, y0 = x - w / 2, y - h / 2
    tx, ty = x + tail[0], y + tail[1]
    if tail[1] > 0:
        ty = max(ty, y0 + h + 42)
    else:
        ty = min(ty, y0 - 42)
    base = 22
    bx = max(x0 + 40, min(x0 + w - 40, x + tail[0] * 0.4))
    by = y0 + h if tail[1] > 0 else y0
    d.polygon([(k(bx - base / 2), k(by)), (k(bx + base / 2), k(by)), (k(tx), k(ty))], fill=fill)
    line(d, [(bx - base / 2, by), (tx, ty), (bx + base / 2, by)], lw=4)
    rrect(d, x0, y0, x0 + w, y0 + h, h / 2, fill=fill, lw=4)
    d.polygon([(k(bx - base / 2 + 3), k(by - (3 if tail[1] > 0 else -3))), (k(bx + base / 2 - 3), k(by - (3 if tail[1] > 0 else -3))),
               (k(bx), k(by + (8 if tail[1] > 0 else -8)))], fill=fill)
    jtext(d, x, y - size * 0.58, text, size, TEXT, anchor="m")


def shout(d, x, y, text, size=56, r=110, fill=HL):
    pts = []
    n = 22
    for i in range(n * 2):
        a = math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.78
        pts.append((k(x + rr * 1.25 * math.cos(a)), k(y + rr * 0.85 * math.sin(a))))
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=OUT, width=k(4), joint="curve")
    jtext(d, x, y - size * 0.6, text, size, TEXT, anchor="m")


# ---------- 캐릭터 '콩이' ----------
def kongi(d, cx, cy, s=1.0, mood="smile", arms="down", scarf=None, seed=1, blush=True):
    rx, ry = 120 * s, 105 * s
    # 발
    for fx in (-0.45, 0.45):
        wobble_ellipse(d, cx + rx * fx, cy + ry * 0.95, 30 * s, 18 * s, BODY, lw=4, seed=seed + fx)
    # 팔(몸 뒤)
    if arms == "up":
        for sx in (-1, 1):
            wobble_ellipse(d, cx + sx * rx * 0.98, cy - ry * 0.45, 22 * s, 34 * s, BODY, lw=4, seed=seed + sx)
    wobble_ellipse(d, cx, cy, rx, ry, BODY, lw=5, seed=seed)
    if scarf:
        d.chord((k(cx - rx * 0.98), k(cy + ry * 0.05), k(cx + rx * 0.98), k(cy + ry * 0.5)), 0, 180, fill=scarf)
        rrect(d, cx + rx * 0.25, cy + ry * 0.2, cx + rx * 0.55, cy + ry * 0.85, 10 * s, fill=scarf, lw=4)
        arc(d, (cx - rx * 0.98, cy - ry * 0.1, cx + rx * 0.98, cy + ry * 0.36), 15, 165, lw=4)
        arc(d, (cx - rx * 0.98, cy + ry * 0.12, cx + rx * 0.98, cy + ry * 0.58), 15, 165, lw=4)
    if arms == "down":
        for sx in (-1, 1):
            wobble_ellipse(d, cx + sx * rx * 0.92, cy + ry * 0.25, 20 * s, 30 * s, BODY, lw=4, seed=seed + 2 * sx)
    ey = cy - ry * 0.18
    ex = rx * 0.34
    # 눈
    if mood in ("happy", "proud"):
        for sx in (-1, 1):
            arc(d, (cx + sx * ex - 16 * s, ey - 10 * s, cx + sx * ex + 16 * s, ey + 18 * s), 200, 340, lw=5)
    elif mood == "sneeze":
        for sx in (-1, 1):
            line(d, [(cx + sx * ex + 12 * s * sx, ey - 11 * s), (cx + sx * ex - 10 * s * sx, ey), (cx + sx * ex + 12 * s * sx, ey + 11 * s)], lw=5)
    else:
        for sx in (-1, 1):
            circle(d, cx + sx * ex, ey, 10 * s, OUT)
            circle(d, cx + sx * ex - 3 * s, ey - 4 * s, 3.5 * s, WHITE)
    if blush:
        for sx in (-1, 1):
            d.ellipse((k(cx + sx * ex * 1.55 - 18 * s), k(ey + 16 * s), k(cx + sx * ex * 1.55 + 18 * s), k(ey + 30 * s)), fill=BLUSH)
    my = ey + 26 * s
    if mood in ("smile", "happy", "proud"):
        arc(d, (cx - 14 * s, my - 10 * s, cx + 14 * s, my + 12 * s), 20, 160, lw=5)
    elif mood == "shiver":
        pts = [(cx - 22 * s + i * 7 * s, my + (5 * s if i % 2 else -2 * s)) for i in range(7)]
        line(d, pts, lw=4)
    elif mood == "hot":
        d.ellipse((k(cx - 14 * s), k(my - 4 * s), k(cx + 14 * s), k(my + 18 * s)), fill=(214, 96, 96), outline=OUT, width=k(4))
    elif mood == "sneeze":
        d.ellipse((k(cx - 16 * s), k(my - 6 * s), k(cx + 16 * s), k(my + 22 * s)), fill=(214, 96, 96), outline=OUT, width=k(4))
    elif mood == "o":
        circle(d, cx, my + 4 * s, 8 * s, OUT)


def shiver_lines(d, cx, cy, s=1.0):
    for sx in (-1, 1):
        for j in range(3):
            x = cx + sx * (150 + j * 14) * s
            line(d, [(x, cy - 40 * s + j * 30 * s), (x + sx * 10 * s, cy - 30 * s + j * 30 * s), (x, cy - 20 * s + j * 30 * s)], lw=4)


# ---------- 공통 틀 ----------
def background():
    im = Image.new("RGB", (k(W), k(H)), CREAM)
    d = ImageDraw.Draw(im)
    for y in range(0, k(H), 2):
        t = y / k(H)
        c = tuple(int(CREAM[i] + (CREAM2[i] - CREAM[i]) * t) for i in range(3))
        d.line([(0, y), (k(W), y)], fill=c, width=2)
    # 모눈 점
    for gx in range(60, W, 60):
        for gy in range(60, H, 60):
            circle(d, gx, gy, 1.6, (238, 224, 204))
    return im, d


def header(d, data, n, total):
    rrect(d, 56, 50, 56 + 118, 96, 23, fill=CORAL, outline=None)
    jtext(d, 56 + 59, 55, data["series"], 30, WHITE, anchor="m")
    stext(d, 190, 58, data["account"], 26, SUB)
    stext(d, W - 56, 58, f"{n} / {total}", 26, SUB, anchor="ra")


def ep_title(d, ep, title, y=120):
    rrect(d, 64, y + 8, 64 + 110, y + 58, 25, fill=OUT, outline=None)
    jtext(d, 64 + 55, y + 11, ep, 32, WHITE, anchor="m")
    w = jw(d, title, 62)
    d.rounded_rectangle((k(196), k(y + 40), k(196 + w + 12), k(y + 70)), k(12), fill=HL)
    jtext(d, 200, y, title, 62, TEXT)


def panel(d, x0, y0, x1, y1, fill=WHITE, label=None):
    rrect(d, x0 + 6, y0 + 8, x1 + 6, y1 + 8, 36, fill=(230, 214, 192), outline=None)
    rrect(d, x0, y0, x1, y1, 36, fill=fill, lw=5)
    if label:
        w = jw(d, label, 30) + 36
        rrect(d, x0 + 24, y0 + 22, x0 + 24 + w, y0 + 66, 22, fill=WHITE, lw=3)
        jtext(d, x0 + 24 + w / 2, y0 + 26, label, 30, TEXT, anchor="m")


def tip(d, lines_, y=1030):
    rrect(d, 64, y, W - 64, y + 175, 34, fill=WHITE, lw=4)
    rrect(d, 96, y - 24, 96 + 168, y + 22, 23, fill=GREEN, outline=OUT, lw=3)
    jtext(d, 96 + 84, y - 21, "콩이's TIP", 30, WHITE, anchor="m")
    yy = y + 40
    for ln in lines_:
        circle(d, 108, yy + 20, 7, CORAL)
        stext(d, 130, yy, ln, 34, TEXT, "bold")
        yy += 58


def source(d, text, y=1236):
    stext(d, W / 2, y, "출처: " + text if not text.startswith("출처") else text, 22, SUB, "reg", anchor="ma")


def dots(d, n, total):
    gap = 24
    x0 = W / 2 - (total - 1) * gap / 2
    for i in range(total):
        if i == n - 1:
            rrect(d, x0 + i * gap - 14, H - 62, x0 + i * gap + 14, H - 52, 5, fill=CORAL, outline=None)
        else:
            circle(d, x0 + i * gap, H - 57, 5, (220, 204, 184))


# ---------- 소품 ----------
def sun(d, cx, cy, r):
    for i in range(10):
        a = math.pi * 2 * i / 10
        line(d, [(cx + (r + 10) * math.cos(a), cy + (r + 10) * math.sin(a)), (cx + (r + 30) * math.cos(a), cy + (r + 30) * math.sin(a))], fill=(240, 170, 60), lw=6)
    wobble_ellipse(d, cx, cy, r, r, SUN, lw=4, seed=3)


def moon(d, cx, cy, r, bg):
    circle(d, cx, cy, r, (255, 236, 160), outline=OUT, lw=4)
    circle(d, cx + r * 0.45, cy - r * 0.25, r * 0.85, bg)


def coat(d, cx, cy, s=1.0, color=(150, 120, 200)):
    pts = [(cx - 50 * s, cy - 50 * s), (cx + 50 * s, cy - 50 * s), (cx + 62 * s, cy + 60 * s), (cx - 62 * s, cy + 60 * s)]
    d.polygon([(k(x), k(y)) for x, y in pts], fill=color)
    line(d, pts + [pts[0]], lw=4)
    line(d, [(cx, cy - 50 * s), (cx, cy + 60 * s)], lw=3)
    for j in range(3):
        circle(d, cx + 10 * s, cy - 20 * s + j * 28 * s, 4 * s, OUT)


def sink(d, cx, cy):
    rrect(d, cx - 170, cy, cx + 170, cy + 90, 30, fill=(225, 238, 250), lw=5)
    fx = cx + 120
    rrect(d, fx - 16, cy - 130, fx + 16, cy - 4, 10, fill=(200, 210, 222), lw=4)
    rrect(d, fx - 90, cy - 130, fx + 16, cy - 100, 10, fill=(200, 210, 222), lw=4)
    for j in range(3):
        line(d, [(fx - 76, cy - 88 + j * 22), (fx - 76, cy - 74 + j * 22)], fill=BLUE, lw=6)


def bubbles_fx(d, pts):
    for x, y, r in pts:
        circle(d, x, y, r, (235, 245, 255), outline=BLUE, lw=3)
        circle(d, x - r * 0.35, y - r * 0.35, r * 0.2, WHITE)


def timer(d, cx, cy, text):
    circle(d, cx, cy, 58, WHITE, outline=OUT, lw=5)
    d.pieslice((k(cx - 46), k(cy - 46), k(cx + 46), k(cy + 46)), -90, 200, fill=MINT)
    jtext(d, cx, cy - 22, text, 40, TEXT, anchor="m")
    rrect(d, cx - 12, cy - 78, cx + 12, cy - 60, 5, fill=OUT, outline=None)


def humidifier(d, cx, cy):
    wobble_ellipse(d, cx, cy, 70, 95, (215, 236, 252), lw=5, seed=5)
    rrect(d, cx - 40, cy - 30, cx + 40, cy + 10, 16, fill=WHITE, lw=3)
    circle(d, cx, cy + 50, 12, BLUE)
    for j in range(3):
        x = cx - 20 + j * 20
        arc(d, (x - 14, cy - 190 + j * 6, x + 14, cy - 150 + j * 6), 90, 270, fill=(150, 190, 235), lw=5)
        arc(d, (x - 14, cy - 150 + j * 6, x + 14, cy - 110 + j * 6), 270, 90, fill=(150, 190, 235), lw=5)


def meter(d, x0, y0, vals):
    rrect(d, x0, y0, x0 + 230, y0 + 190, 28, fill=WHITE, lw=5)
    rrect(d, x0 + 20, y0 + 20, x0 + 210, y0 + 170, 18, fill=(225, 244, 232), lw=3)
    jtext(d, x0 + 115, y0 + 26, vals[0], 58, TEXT, anchor="m")
    jtext(d, x0 + 115, y0 + 96, vals[1], 58, BLUE, anchor="m")


def window(d, x0, y0, w, h):
    rrect(d, x0, y0, x0 + w, y0 + h, 18, fill=SKY, lw=5)
    line(d, [(x0 + w / 2, y0), (x0 + w / 2, y0 + h)], lw=5)
    line(d, [(x0, y0 + h / 2), (x0 + w, y0 + h / 2)], lw=5)
    for j in range(3):
        y = y0 + 40 + j * 45
        arc(d, (x0 + w + 10, y, x0 + w + 110, y + 40), 200, 340, fill=(140, 180, 230), lw=5)


def mug(d, cx, cy, color=CORAL):
    rrect(d, cx - 55, cy - 50, cx + 55, cy + 60, 22, fill=color, lw=5)
    arc(d, (cx + 35, cy - 25, cx + 90, cy + 35), 270, 90, lw=6)
    for j in range(3):
        x = cx - 30 + j * 30
        arc(d, (x - 10, cy - 120, x + 10, cy - 90), 90, 270, fill=(200, 180, 170), lw=4)
        arc(d, (x - 10, cy - 90, x + 10, cy - 60), 270, 90, fill=(200, 180, 170), lw=4)


def fruit(d, cx, cy, r, color, leafc=GREEN):
    wobble_ellipse(d, cx, cy, r, r * 0.92, color, lw=4, seed=cx)
    leaf(d, cx + r * 0.3, cy - r * 0.95, r * 0.35, -0.5, leafc)


def calendar(d, x0, y0, lines_):
    rrect(d, x0, y0, x0 + 280, y0 + 230, 26, fill=WHITE, lw=5)
    d.rounded_rectangle((k(x0), k(y0), k(x0 + 280), k(y0 + 64)), k(26), fill=CORAL)
    d.rectangle((k(x0), k(y0 + 40), k(x0 + 280), k(y0 + 64)), fill=CORAL)
    rrect(d, x0, y0, x0 + 280, y0 + 230, 26, fill=None, lw=5)
    for sx in (70, 210):
        rrect(d, x0 + sx - 8, y0 - 20, x0 + sx + 8, y0 + 20, 6, fill=OUT, outline=None)
    jtext(d, x0 + 140, y0 + 90, lines_[0], 40, TEXT, anchor="m")
    jtext(d, x0 + 140, y0 + 146, lines_[1], 40, CORAL, anchor="m")


def bandage(d, cx, cy, ang=-0.5):
    w, h = 70, 26
    ca, sa = math.cos(ang), math.sin(ang)
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    d.polygon([(k(x), k(y)) for x, y in pts], fill=(250, 210, 170))
    line(d, pts + [pts[0]], lw=3)
    circle(d, cx, cy, 8, (240, 180, 140))


# ---------- 카드 ----------
def card_cover(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    # 낙엽
    for x, y, s, a in ((140, 230, 26, 0.6), (930, 300, 30, -0.4), (860, 170, 20, 1.2), (220, 660, 22, -0.9), (900, 640, 24, 0.3)):
        leaf(d, x, y, s, a, LEAF if x % 2 else (240, 190, 90))
    # 큰 원 무대
    wobble_ellipse(d, 540, 520, 330, 300, (255, 236, 214), outline=None, seed=2)
    kongi(d, 540, 560, s=1.55, mood="sneeze", arms="down", scarf=(255, 150, 140), seed=4)
    shout(d, 790, 300, c["bubble"], size=60, r=105)
    for j in range(3):
        circle(d, 690 + j * 22, 650 - j * 14, 6 - j, (190, 210, 240))
    jtext(d, W / 2, 830, c["kicker"], 36, CORAL, anchor="m")
    y = 885
    for i, t in enumerate(c["title"]):
        w = jw(d, t, 92)
        if i == 1:
            d.rounded_rectangle((k(W / 2 - w / 2 - 10), k(y + 56), k(W / 2 + w / 2 + 10), k(y + 100)), k(16), fill=HL)
        jtext(d, W / 2, y, t, 92, TEXT, anchor="m")
        y += 112
    rrect(d, W / 2 - 230, y + 18, W / 2 + 230, y + 78, 30, fill=WHITE, lw=4)
    jtext(d, W / 2, y + 26, c["sub"], 36, TEXT, anchor="m")
    dots(d, n, total)
    return im


def card_temp(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    ep_title(d, c["ep"], c["title"])
    panel(d, 64, 250, 530, 990, fill=NIGHT, label=c["left"]["label"])
    panel(d, 550, 250, 1016, 990, fill=(255, 236, 196), label=c["right"]["label"])
    moon(d, 440, 360, 46, NIGHT)
    for x, y in ((150, 420), (380, 460), (260, 380)):
        sparkle(d, x, y, 12, WHITE)
    kongi(d, 297, 760, s=1.0, mood="shiver", arms="down", scarf=(255, 150, 140), seed=7)
    shiver_lines(d, 297, 760)
    bubble(d, 297, 560, c["left"]["say"], 48, tail=(-20, 80))
    sun(d, 920, 370, 50)
    kongi(d, 783, 780, s=1.0, mood="hot", arms="up", seed=9)
    coat(d, 900, 860, s=0.7)
    drop(d, 690, 690, 12)
    drop(d, 880, 700, 10)
    bubble(d, 760, 560, c["right"]["say"], 48, tail=(20, 80))
    tip(d, c["tip"])
    source(d, c["src"])
    dots(d, n, total)
    return im


def card_hands(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    ep_title(d, c["ep"], c["title"])
    panel(d, 64, 250, 1016, 620, fill=(232, 244, 255))
    kongi(d, 250, 440, s=0.8, mood="happy", arms="none", seed=11)
    sink(d, 330, 470)
    # 손(거품 속에서 비비는 중)
    for hx in (300, 350):
        wobble_ellipse(d, hx, 452, 24, 20, BODY, lw=4, seed=hx)
    bubbles_fx(d, [(300, 420, 16), (345, 410, 13), (380, 440, 10), (150, 330, 18), (210, 300, 10), (420, 330, 12)])
    timer(d, 640, 430, "30초")
    bubble(d, 850, 380, c["say1"], 42, tail=(-80, 60))
    panel(d, 64, 650, 1016, 990, fill=(255, 238, 230))
    kongi(d, 360, 850, s=0.85, mood="sneeze", arms="none", seed=13)
    # 옷소매로 입 가리기: 몸 옆에서 입 앞까지 굽힌 팔
    sleeve = (150, 120, 200)
    wobble_ellipse(d, 360 + 88, 850 + 50, 30, 40, sleeve, lw=4, seed=2)
    wobble_ellipse(d, 360 + 34, 850 + 34, 66, 24, sleeve, lw=4, seed=3)
    wobble_ellipse(d, 360 - 26, 850 + 32, 18, 24, (120, 92, 175), lw=4, seed=4)
    for j in range(3):
        circle(d, 540 + j * 26, 800 + (j % 2) * 16, 7, (200, 190, 230))
    jtext(d, 470, 700, "에취!", 40, CORAL)
    bubble(d, 770, 780, c["say2"], 44, tail=(-90, 50))
    tip(d, c["tip"])
    source(d, c["src"])
    dots(d, n, total)
    return im


def card_room(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    ep_title(d, c["ep"], c["title"])
    panel(d, 64, 250, 1016, 990, fill=(240, 250, 244))
    window(d, 100, 300, 260, 230)
    jtext(d, 470, 330, c["wind"], 40, BLUE)
    humidifier(d, 200, 860)
    kongi(d, 520, 820, s=1.05, mood="happy", arms="up", seed=15)
    meter(d, 740, 640, c["display"])
    bubble(d, 560, 590, c["say"], 46, tail=(-20, 90))
    sparkle(d, 860, 600, 16, HL)
    sparkle(d, 990 - 20, 900, 12, PINK)
    tip(d, c["tip"])
    source(d, c["src"])
    dots(d, n, total)
    return im


def card_water(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    ep_title(d, c["ep"], c["title"])
    panel(d, 64, 250, 1016, 990, fill=(255, 243, 228))
    kongi(d, 400, 720, s=1.3, mood="happy", arms="none", seed=17)
    mug(d, 400 + 10, 820, CORAL)
    for sx in (-1, 1):
        wobble_ellipse(d, 410 + sx * 62, 830, 22, 26, BODY, lw=4, seed=sx)
    bubble(d, 330, 420, c["say"], 48, tail=(40, 90))
    # 과일 접시
    wobble_ellipse(d, 800, 860, 160, 50, WHITE, lw=5, seed=8)
    fruit(d, 740, 800, 46, (255, 160, 60))
    fruit(d, 840, 795, 44, (230, 70, 70))
    fruit(d, 800, 760, 38, (255, 200, 80))
    bubble(d, 800, 620, c["say2"], 44, tail=(0, 90))
    sparkle(d, 950, 420, 16, HL)
    tip(d, c["tip"])
    source(d, c["src"])
    dots(d, n, total)
    return im


def card_vaccine(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    ep_title(d, c["ep"], c["title"])
    panel(d, 64, 250, 1016, 990, fill=(236, 246, 255))
    kongi(d, 360, 760, s=1.3, mood="proud", arms="up", seed=19)
    bandage(d, 360 - 128, 640)
    shout(d, 360, 420, c["say"], size=52, r=100, fill=(255, 236, 160))
    calendar(d, 660, 500, c["calendar"])
    for x, y in ((620, 360), (960, 380), (980, 820)):
        sparkle(d, x, y, 16, HL)
    tip(d, c["tip"])
    source(d, c["src"])
    dots(d, n, total)
    return im


def card_end(c, data, n, total):
    im, d = background()
    header(d, data, n, total)
    y = 130
    for i, t in enumerate(c["title"]):
        w = jw(d, t, 84)
        if i == 1:
            d.rounded_rectangle((k(W / 2 - w / 2 - 10), k(y + 50), k(W / 2 + w / 2 + 10), k(y + 92)), k(16), fill=HL)
        jtext(d, W / 2, y, t, 84, TEXT, anchor="m")
        y += 104
    # 담요 덮은 콩이
    wobble_ellipse(d, 540, 560, 300, 200, (255, 236, 214), outline=None, seed=6)
    kongi(d, 540, 560, s=1.25, mood="happy", arms="none", seed=21)
    # 담요: 어깨부터 덮은 체크무늬 천
    bl = (170, 200, 240)
    top = 560 + 20
    pts = []
    for i in range(0, 41):
        x = 540 - 210 + 420 * i / 40
        pts.append((x, top + 10 * math.sin(i * 0.9)))
    pts += [(540 + 235, 560 + 190), (540 - 235, 560 + 190)]
    d.polygon([(k(x), k(y)) for x, y in pts], fill=bl)
    line(d, pts + [pts[0]], lw=5)
    for x in range(540 - 160, 540 + 200, 80):
        line(d, [(x, top + 14), (x + (x - 540) * 0.08, 560 + 186)], fill=(140, 172, 222), lw=4)
    for yy in (560 + 80, 560 + 140):
        line(d, [(540 - 225, yy), (540 + 225, yy)], fill=(140, 172, 222), lw=4)
    mug(d, 540 + 150, 560 + 60, CORAL)
    bubble(d, 830, 400, c["say"], 40, tail=(-120, 70))
    # 체크리스트
    y = 820
    rrect(d, 64, y, W - 64, y + 300, 34, fill=WHITE, lw=4)
    cols = len(c["checks"])
    cw = (W - 128) / cols
    for i, t in enumerate(c["checks"]):
        cx = 64 + cw * i + cw / 2
        circle(d, cx, y + 95, 44, MINT, outline=OUT, lw=4)
        line(d, [(cx - 20, y + 95), (cx - 4, y + 112), (cx + 22, y + 78)], fill=GREEN, lw=8)
        jtext(d, cx, y + 160, t, 34, TEXT, anchor="m")
        jtext(d, cx, y + 214, f"EP.{i + 1}", 26, SUB, anchor="m")
    stext(d, W / 2, 1160, c["src"], 22, SUB, "reg", anchor="ma")
    dots(d, n, total)
    return im


RENDER = {"cover": card_cover, "ep_temp": card_temp, "ep_hands": card_hands, "ep_room": card_room,
          "ep_water": card_water, "ep_vaccine": card_vaccine, "end": card_end}


def main():
    data = json.loads((ROOT / "src/script.json").read_text())
    cards = data["cards"]
    out = []
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](c, data, i, len(cards)).resize((W, H), Image.LANCZOS)
        im.save(ROOT / f"{i:02d}.png")
        out.append(im)
    out[0].save(ROOT / "cover_preview.jpg", quality=92)
    cols, sc = 4, 0.3
    a, b = int(W * sc), int(H * sc)
    rows = math.ceil(len(out) / cols)
    sheet = Image.new("RGB", (cols * a + (cols + 1) * 14, rows * b + (rows + 1) * 14), (240, 232, 220))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (14 + (i % cols) * (a + 14), 14 + (i // cols) * (b + 14)))
    sheet.save(ROOT / "preview.jpg", quality=90)
    print("ok", len(out))


if __name__ == "__main__":
    main()
