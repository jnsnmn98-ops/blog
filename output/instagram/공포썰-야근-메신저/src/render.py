"""공포썰 인스타툰 렌더러 — '야근하던 밤, 팀장님에게서 메신저가 왔다' (창작).
어두운 화면, 모니터 불빛 하나, 거친 선으로 직접 그린다. 2배로 그린 뒤 줄인다.
실행: python src/render.py  (주제 폴더에서)
"""
import json
import math
import pathlib
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1350
K = 2

BG = (10, 11, 15)
DARK = (20, 22, 30)
DARK2 = (30, 33, 44)
EDGE = (205, 205, 200)
PALE = (232, 232, 226)
GREY = (120, 122, 132)
GLOW = (150, 190, 255)
SCREEN = (196, 220, 255)
RED = (176, 24, 34)
RED_L = (230, 60, 60)
SICK = (170, 190, 170)

SERIF = str(ROOT / "assets/fonts/SongMyung-Regular.ttf")
HEAVY = str(ROOT / "assets/fonts/BlackHanSans-Regular.ttf")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def k(v):
    return int(round(v * K))


def serif(s):
    return ImageFont.truetype(SERIF, k(s))


def heavy(s):
    return ImageFont.truetype(HEAVY, k(s))


def sd(s, w="semi"):
    return ImageFont.truetype(SD, k(s), index={"bold": 6, "semi": 4, "reg": 0}[w])


def tlen(d, t, f):
    return d.textlength(t, font=f) / K


# ---------- 기본 도구 ----------
def rough_poly(pts, amp=2.2, seed=0):
    rnd = random.Random(seed)
    out = []
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 18))
        for j in range(n):
            t = j / n
            out.append((x0 + (x1 - x0) * t + rnd.uniform(-amp, amp), y0 + (y1 - y0) * t + rnd.uniform(-amp, amp)))
    return out


def poly(d, pts, fill=None, outline=None, lw=3):
    p = [(k(x), k(y)) for x, y in pts]
    if fill:
        d.polygon(p, fill=fill)
    if outline:
        d.line(p + [p[0]], fill=outline, width=k(lw), joint="curve")


def rect(d, x0, y0, x1, y1, fill=None, outline=None, lw=3, r=0):
    if r:
        d.rounded_rectangle((k(x0), k(y0), k(x1), k(y1)), k(r), fill=fill, outline=outline, width=k(lw) if outline else 0)
    else:
        d.rectangle((k(x0), k(y0), k(x1), k(y1)), fill=fill, outline=outline, width=k(lw) if outline else 0)


def ell(d, x0, y0, x1, y1, fill=None, outline=None, lw=3):
    d.ellipse((k(x0), k(y0), k(x1), k(y1)), fill=fill, outline=outline, width=k(lw) if outline else 0)


def glow(layer, cx, cy, rx, ry, color, strength=160, blur=60):
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((k(cx - rx), k(cy - ry), k(cx + rx), k(cy + ry)), fill=color + (strength,))
    g = g.filter(ImageFilter.GaussianBlur(k(blur)))
    layer.alpha_composite(g)


def grain(im, amount=26, seed=0):
    random.seed(seed)
    n = Image.effect_noise(im.size, 60).convert("L")
    n = n.point(lambda v: max(0, min(255, v)))
    noise = Image.merge("RGB", (n, n, n))
    return Image.blend(im, ImageChops.overlay(im, noise), amount / 100)


def vignette(im, strength=200):
    m = Image.new("L", im.size, 0)
    w, h = im.size
    ImageDraw.Draw(m).ellipse((-w * 0.15, -h * 0.1, w * 1.15, h * 1.1), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(w * 0.12))
    dark = Image.new("RGB", im.size, (0, 0, 0))
    inv = m.point(lambda v: int((255 - v) * strength / 255))
    return Image.composite(dark, im, inv)


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if tlen(d, t, f) > maxw and cur:
            out.append(cur)
            cur = word
        else:
            cur = t
    out.append(cur)
    return out


# ---------- 칸(패널) ----------
class Panel:
    def __init__(self, w, h, base=DARK):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (k(w), k(h)), base + (255,))
        self.d = ImageDraw.Draw(self.im)

    def paste_to(self, canvas, x, y, seed=0):
        pts = rough_poly([(0, 0), (self.w, 0), (self.w, self.h), (0, self.h)], amp=1.6, seed=seed)
        mask = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(mask).polygon([(k(px), k(py)) for px, py in pts], fill=255)
        canvas.paste(self.im.convert("RGB"), (k(x), k(y)), mask)
        cd = ImageDraw.Draw(canvas)
        p = [(k(x + px), k(y + py)) for px, py in pts]
        cd.line(p + [p[0]], fill=EDGE, width=k(3), joint="curve")


def room_bg(p, light=(0.5, 0.35), cool=True):
    """어두운 사무실 벽과 바닥, 빈 책상 실루엣."""
    d = p.d
    for y in range(0, p.im.height, 2):
        t = y / p.im.height
        c = tuple(int(DARK2[i] * (1 - t) + BG[i] * t) for i in range(3))
        d.line([(0, y), (p.im.width, y)], fill=c, width=2)
    # 창문(먼 도시 불빛)
    rnd = random.Random(3)
    for wx in range(30, int(p.w), 190):
        rect(d, wx, p.h * 0.08, wx + 150, p.h * 0.36, fill=(16, 20, 32), outline=(40, 44, 58), lw=2)
        for _ in range(9):
            x = wx + rnd.uniform(10, 140)
            y = p.h * rnd.uniform(0.2, 0.34)
            ell(d, x, y, x + 3, y + 3, fill=(120, 110, 80))
    # 빈 책상들
    for i, dx in enumerate(range(-40, int(p.w) + 100, 230)):
        yb = p.h * 0.52
        rect(d, dx, yb, dx + 170, yb + 16, fill=(26, 28, 36))
        rect(d, dx + 50, yb - 60, dx + 120, yb, fill=(22, 24, 30), outline=(34, 36, 46), lw=2)


def monitor(p, cx, cy, w, h, mode="doc", data=None, glow_on=True):
    d = p.d
    if glow_on and mode != "off":
        glow(p.im, cx, cy, w * 1.1, h * 1.2, GLOW, strength=110, blur=70)
        d = p.d = ImageDraw.Draw(p.im)
    rect(d, cx - w / 2 - 14, cy - h / 2 - 14, cx + w / 2 + 14, cy + h / 2 + 14, fill=(14, 15, 20), outline=(60, 62, 72), lw=3, r=10)
    rect(d, cx - 18, cy + h / 2 + 14, cx + 18, cy + h / 2 + 60, fill=(14, 15, 20))
    rect(d, cx - 80, cy + h / 2 + 56, cx + 80, cy + h / 2 + 70, fill=(14, 15, 20))
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    if mode == "off":
        rect(d, x0, y0, x1, y1, fill=(8, 9, 12))
        return (x0, y0, x1, y1)
    rect(d, x0, y0, x1, y1, fill=SCREEN)
    if mode == "doc":
        for j in range(int((h - 40) / 22)):
            lw_ = w * (0.55 + 0.35 * ((j * 37) % 10) / 10)
            rect(d, x0 + 24, y0 + 24 + j * 22, x0 + 24 + lw_ - 48, y0 + 32 + j * 22, fill=(150, 170, 205))
    return (x0, y0, x1, y1)


def worker_back(p, cx, by, s=1.0, rim=GLOW):
    """뒷모습 실루엣(머리와 어깨). by = 어깨 아래쪽 y."""
    d = p.d
    shoulders = [(cx - 230 * s, by), (cx - 200 * s, by - 120 * s), (cx - 90 * s, by - 170 * s), (cx + 90 * s, by - 170 * s),
                 (cx + 200 * s, by - 120 * s), (cx + 230 * s, by)]
    poly(d, rough_poly(shoulders + [(cx + 230 * s, by + 40), (cx - 230 * s, by + 40)], amp=1.5, seed=4), fill=(6, 6, 9))
    ell(d, cx - 78 * s, by - 330 * s, cx + 78 * s, by - 150 * s, fill=(6, 6, 9))
    # 모니터 빛에 비친 윤곽
    d.arc((k(cx - 78 * s), k(by - 330 * s), k(cx + 78 * s), k(by - 150 * s)), 200, 340, fill=rim, width=k(3))


def figure(p, cx, top, h, eyes=True, alpha=235):
    """그림자 형상: 길쭉한 머리와 늘어진 어깨."""
    lay = Image.new("RGBA", p.im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    w = h * 0.34
    body = [(cx - w * 0.2, top + h * 0.2), (cx - w * 0.55, top + h * 0.38), (cx - w * 0.62, top + h), (cx + w * 0.62, top + h),
            (cx + w * 0.55, top + h * 0.38), (cx + w * 0.2, top + h * 0.2)]
    d.polygon([(k(x), k(y)) for x, y in rough_poly(body, amp=4, seed=9)], fill=(0, 0, 0, alpha))
    d.ellipse((k(cx - w * 0.24), k(top), k(cx + w * 0.24), k(top + h * 0.26)), fill=(0, 0, 0, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(k(2.5)))
    p.im.alpha_composite(lay)
    if eyes:
        dd = ImageDraw.Draw(p.im)
        for sx in (-1, 1):
            ex = cx + sx * w * 0.09
            ey = top + h * 0.12
            dd.ellipse((k(ex - 5), k(ey - 3), k(ex + 5), k(ey + 3)), fill=(225, 225, 210))
    p.d = ImageDraw.Draw(p.im)


def chat(d, x0, y0, x1, y1, title, msgs, size=26):
    rect(d, x0, y0, x1, y1, fill=(240, 244, 250), outline=(120, 130, 150), lw=2, r=8)
    rect(d, x0, y0, x1, y0 + 46, fill=(70, 86, 120), r=8)
    rect(d, x0, y0 + 30, x1, y0 + 46, fill=(70, 86, 120))
    d.text((k(x0 + 18), k(y0 + 10)), title, font=sd(22, "bold"), fill=(240, 240, 245))
    y = y0 + 66
    for who, t in msgs:
        f = sd(size, "semi")
        tw = tlen(d, t, f)
        if who == "me":
            bx1 = x1 - 18
            bx0 = bx1 - tw - 32
            fill, col = (255, 230, 120), (40, 40, 40)
        else:
            bx0 = x0 + 18
            bx1 = bx0 + tw + 32
            fill, col = (255, 255, 255), (30, 30, 40)
        rect(d, bx0, y, bx1, y + size + 26, fill=fill, outline=(170, 176, 190), lw=2, r=14)
        d.text((k(bx0 + 16), k(y + 11)), t, font=f, fill=col)
        y += size + 44
    return y


def narr_box(canvas, x, y, lines, size=40, maxw=None, align="l", fill=(0, 0, 0), color=PALE):
    d = ImageDraw.Draw(canvas)
    f = serif(size)
    w = max(tlen(d, ln, f) for ln in lines) + 60
    h = len(lines) * (size + 18) + 34
    if align == "m":
        x -= w / 2
    pts = rough_poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], amp=1.5, seed=int(x + y))
    poly(d, pts, fill=fill, outline=(200, 200, 196), lw=2)
    yy = y + 18
    for ln in lines:
        d.text((k(x + 30), k(yy)), ln, font=f, fill=color)
        yy += size + 18
    return y + h


def header(canvas, data, n, total):
    d = ImageDraw.Draw(canvas)
    rect(d, 56, 48, 56 + 112, 92, fill=RED, r=8)
    d.text((k(56 + 56), k(70)), data["series"], font=sd(26, "bold"), fill=PALE, anchor="mm")
    rect(d, 178, 48, 178 + 76, 92, outline=GREY, lw=2, r=8)
    d.text((k(178 + 38), k(70)), data["label"], font=sd(24, "semi"), fill=GREY, anchor="mm")
    d.text((k(270), k(56)), data["account"], font=sd(24, "semi"), fill=GREY)
    d.text((k(W - 56), k(56)), f"{n} / {total}", font=sd(24, "semi"), fill=GREY, anchor="ra")


def dots(canvas, n, total):
    d = ImageDraw.Draw(canvas)
    gap = 24
    x0 = W / 2 - (total - 1) * gap / 2
    for i in range(total):
        if i == n - 1:
            rect(d, x0 + i * gap - 14, H - 56, x0 + i * gap + 14, H - 48, fill=RED, r=4)
        else:
            ell(d, x0 + i * gap - 4, H - 56, x0 + i * gap + 4, H - 48, fill=(70, 72, 80))


def new_canvas():
    return Image.new("RGB", (k(W), k(H)), BG)


def foot_text(canvas, text, y, size=40, color=PALE):
    d = ImageDraw.Draw(canvas)
    f = serif(size)
    for ln in wrap(d, text, f, W - 160):
        d.text((k(W / 2), k(y)), ln, font=f, fill=color, anchor="ma")
        y += size + 16
    return y


# ---------- 카드 ----------
def c_cover(c, data, n, total):
    cv = new_canvas()
    p = Panel(W, H, BG)
    room_bg(p)
    monitor(p, 540, 470, 420, 260, "doc")
    worker_back(p, 540, 980, s=1.35)
    # 시계(벽 디지털 시계)
    dd = p.d
    rect(dd, 800, 150, 990, 230, fill=(8, 8, 10), outline=(50, 50, 58), lw=2, r=8)
    dd.text((k(895), k(190)), c["clock"], font=heavy(54), fill=RED_L, anchor="mm")
    glow(p.im, 895, 190, 120, 60, RED, strength=60, blur=30)
    # 아래를 검게
    fade = Image.new("RGBA", p.im.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    for y in range(k(780), p.im.height, 2):
        a = int(255 * min(1, (y - k(780)) / k(330)))
        fd.line([(0, y), (p.im.width, y)], fill=(4, 4, 6, a), width=2)
    p.im.alpha_composite(fade)
    cv.paste(p.im.convert("RGB"), (0, 0))
    header(cv, data, n, total)
    d = ImageDraw.Draw(cv)
    d.text((k(W / 2), k(930)), c["kicker"], font=serif(40), fill=GREY, anchor="ma")
    y = 990
    for i, t in enumerate(c["title"]):
        f = heavy(104)
        col = PALE if i == 0 else RED_L
        d.text((k(W / 2 + 4), k(y + 4)), t, font=f, fill=(0, 0, 0), anchor="ma")
        d.text((k(W / 2), k(y)), t, font=f, fill=col, anchor="ma")
        y += 120
    d.text((k(W / 2), k(y + 14)), c["sub"], font=sd(28, "semi"), fill=GREY, anchor="ma")
    dots(cv, n, total)
    return cv


def c_alone(c, data, n, total):
    cv = new_canvas()
    header(cv, data, n, total)
    narr_box(cv, 64, 130, c["narr"], size=40)
    p = Panel(952, 900)
    room_bg(p)
    monitor(p, 476, 400, 360, 220, "doc")
    worker_back(p, 476, 880, s=1.05)
    # 넓은 어둠 강조: 왼쪽 위 비상구 불빛
    dd = p.d
    rect(dd, 40, 60, 150, 104, fill=(20, 70, 40), outline=(40, 120, 70), lw=2, r=4)
    glow(p.im, 95, 82, 90, 40, (40, 140, 80), strength=70, blur=25)
    p.d.text((k(476), k(830)), "", font=sd(10))
    p.paste_to(cv, 64, 290, seed=1)
    d = ImageDraw.Draw(cv)
    rect(d, 750, 1130, 1000, 1196, fill=(8, 8, 10), outline=(60, 60, 66), lw=2, r=8)
    d.text((k(875), k(1163)), c["clock"], font=heavy(46), fill=RED_L, anchor="mm")
    d.text((k(110), k(1150)), "째깍… 째깍…", font=serif(34), fill=GREY)
    dots(cv, n, total)
    return cv


def c_message(c, data, n, total):
    cv = new_canvas()
    header(cv, data, n, total)
    narr_box(cv, 64, 130, c["narr"], size=40)
    p = Panel(952, 760, (14, 16, 24))
    x0, y0, x1, y1 = monitor(p, 476, 360, 760, 520, "doc")
    glow(p.im, 476, 360, 500, 380, GLOW, strength=60, blur=80)
    p.d = ImageDraw.Draw(p.im)
    chat(p.d, x0 + 230, y0 + 120, x1 - 30, y1 - 30, c["from"], c["msgs"], size=28)
    # 알림 배지
    ell(p.d, x1 - 46, y0 + 104, x1 - 14, y0 + 136, fill=RED_L)
    p.paste_to(cv, 64, 250, seed=2)
    foot_text(cv, c["foot"], 1080, size=46)
    dots(cv, n, total)
    return cv


def c_reflection(c, data, n, total):
    cv = new_canvas()
    header(cv, data, n, total)
    narr_box(cv, 64, 130, c["narr"], size=40)
    # 위: 메시지 한 줄 클로즈업
    p1 = Panel(952, 230, (230, 236, 246))
    dd = p1.d
    rect(dd, 30, 40, 922, 190, fill=(255, 255, 255), outline=(150, 156, 170), lw=3, r=24)
    dd.text((k(70), k(78)), c["msg"], font=sd(44, "bold"), fill=(20, 20, 26))
    p1.paste_to(cv, 64, 260, seed=3)
    # 아래: 꺼진 화면에 비친 나와 뒤의 형상
    p2 = Panel(952, 600, (6, 7, 10))
    dd = p2.d
    rect(dd, 60, 40, 892, 560, fill=(10, 12, 16), outline=(60, 62, 72), lw=4, r=12)
    # 화면 반사광 사선
    for i in range(3):
        poly(dd, [(140 + i * 60, 50), (190 + i * 60, 50), (100 + i * 60, 550), (50 + i * 60, 550)], fill=(18, 22, 30))
    figure(p2, 620, 70, 470, eyes=True, alpha=250)
    worker_back(p2, 380, 600, s=0.8, rim=(70, 90, 120))
    p2.paste_to(cv, 64, 520, seed=4)
    foot_text(cv, c["foot"], 1160, size=40, color=SICK)
    dots(cv, n, total)
    return cv


def c_turn(c, data, n, total):
    cv = new_canvas()
    header(cv, data, n, total)
    narr_box(cv, 64, 130, c["narr"], size=40)
    p = Panel(952, 860, (8, 9, 12))
    d = p.d
    vx, vy = 520, 360
    # 바닥·천장 원근선
    for x in range(-400, 1400, 120):
        d.line([(k(vx), k(vy)), (k(x), k(860))], fill=(26, 28, 36), width=k(2))
    for i, t in enumerate([0.15, 0.3, 0.5, 0.75]):
        # 천장 형광등
        lw_ = 220 * (1 - t) + 30
        y = vy - 330 * (1 - t)
        cx = vx
        col = (210, 220, 230) if i != 2 else (60, 64, 70)
        rect(d, cx - lw_ / 2, y, cx + lw_ / 2, y + 14 * (1 - t) + 4, fill=col)
        if i != 2:
            glow(p.im, cx, y + 40, lw_, 70 * (1 - t) + 20, (180, 200, 220), strength=45, blur=30)
            d = p.d = ImageDraw.Draw(p.im)
    # 양옆 책상 줄
    for side in (-1, 1):
        for j, t in enumerate([0.0, 0.35, 0.6, 0.8]):
            s = 1 - t
            x = vx + side * (420 * s + 30)
            yb = vy + 420 * s
            rect(d, x - 120 * s, yb - 40 * s, x + 120 * s, yb, fill=(16, 17, 22), outline=(30, 32, 40), lw=2)
    # 복도 끝 문(조금 열림)
    rect(d, vx - 46, vy - 90, vx + 46, vy + 60, fill=(4, 4, 6), outline=(50, 52, 60), lw=3)
    poly(d, [(vx + 18, vy - 86), (vx + 30, vy - 86), (vx + 30, vy + 56), (vx + 18, vy + 56)], fill=(200, 200, 180))
    glow(p.im, vx + 24, vy, 50, 120, (220, 220, 190), strength=70, blur=20)
    p.d = ImageDraw.Draw(p.im)
    # 앞쪽: 돌아보는 내 어깨
    worker_back(p, 150, 900, s=0.9, rim=(90, 100, 120))
    p.paste_to(cv, 64, 260, seed=5)
    foot_text(cv, c["foot"], 1150, size=38)
    dots(cv, n, total)
    return cv


def c_phone(c, data, n, total):
    cv = new_canvas()
    header(cv, data, n, total)
    narr_box(cv, 64, 130, c["narr"], size=40)
    p = Panel(952, 820, (6, 7, 10))
    d = p.d
    glow(p.im, 476, 420, 360, 380, (120, 150, 210), strength=70, blur=80)
    d = p.d = ImageDraw.Draw(p.im)
    # 손(실루엣)과 휴대폰
    poly(d, rough_poly([(200, 820), (260, 560), (330, 520), (640, 520), (720, 600), (760, 820)], amp=3, seed=6), fill=(4, 4, 6))
    rect(d, 300, 90, 650, 760, fill=(14, 14, 18), outline=(70, 72, 82), lw=4, r=40)
    rect(d, 320, 120, 630, 730, fill=(236, 238, 244), r=26)
    rect(d, 320, 120, 630, 190, fill=(220, 224, 234), r=26)
    rect(d, 320, 160, 630, 190, fill=(220, 224, 234))
    d.text((k(475), k(155)), c["from"], font=sd(26, "bold"), fill=(30, 30, 40), anchor="mm")
    y = 230
    for t in c["sms"]:
        f = sd(25, "semi")
        lines = wrap(d, t, f, 230)
        h = len(lines) * 36 + 24
        rect(d, 340, y, 340 + max(tlen(d, l, f) for l in lines) + 32, y + h, fill=(255, 255, 255), outline=(190, 194, 204), lw=2, r=16)
        for j, ln in enumerate(lines):
            d.text((k(356), k(y + 12 + j * 36)), ln, font=f, fill=(30, 30, 40))
        y += h + 18
    # 엄지
    poly(d, rough_poly([(560, 820), (600, 640), (650, 610), (700, 640), (690, 820)], amp=2, seed=7), fill=(4, 4, 6))
    # 진동 표시
    for sx in (-1, 1):
        for j in range(3):
            x = 475 + sx * (230 + j * 24)
            d.line([(k(x), k(300 + j * 10)), (k(x + sx * 14), k(330 + j * 10)), (k(x), k(360 + j * 10))], fill=(160, 170, 190), width=k(3))
    p.paste_to(cv, 64, 260, seed=8)
    foot_text(cv, c["foot"] + "…", 1120, size=44, color=RED_L)
    dots(cv, n, total)
    return cv


def c_end(c, data, n, total):
    cv = new_canvas()
    p = Panel(W, 760, BG)
    x0, y0, x1, y1 = monitor(p, 540, 380, 640, 400, "off")
    d = p.d
    rect(d, x0, y0, x1, y1, fill=(6, 6, 8))
    glow(p.im, 540, 380, 380, 260, RED, strength=70, blur=60)
    d = p.d = ImageDraw.Draw(p.im)
    f = heavy(78)
    t = c["monitor"]
    d.text((k(540 - 4), k(380)), t, font=f, fill=(0, 200, 220), anchor="mm")
    d.text((k(540 + 4), k(380)), t, font=f, fill=(220, 0, 30), anchor="mm")
    d.text((k(540), k(380)), t, font=f, fill=(240, 230, 230), anchor="mm")
    # 깨진 주사선
    rnd = random.Random(11)
    for _ in range(14):
        yy = rnd.uniform(y0, y1)
        d.line([(k(x0), k(yy)), (k(x1), k(yy))], fill=(40, 10, 14), width=k(1))
    # 화면 앞 손자국
    for j in range(4):
        ell(d, 760 + j * 22, 300 + j * 30, 790 + j * 22, 340 + j * 30, fill=(30, 12, 14))
    cv.paste(p.im.convert("RGB"), (0, k(80)))
    header(cv, data, n, total)
    d = ImageDraw.Draw(cv)
    y = 880
    for i, t in enumerate(c["title"]):
        d.text((k(W / 2), k(y)), t, font=serif(58 if i else 48), fill=PALE if i else GREY, anchor="ma")
        y += 84
    rect(d, 140, y + 30, W - 140, y + 110, outline=(90, 90, 96), lw=2, r=40)
    d.text((k(W / 2), k(y + 70)), c["cta"], font=sd(30, "semi"), fill=PALE, anchor="mm")
    d.text((k(W / 2), k(1250)), c["note"], font=sd(21, "reg"), fill=GREY, anchor="ma")
    dots(cv, n, total)
    return cv


RENDER = {"cover": c_cover, "alone": c_alone, "message": c_message, "reflection": c_reflection,
          "turn": c_turn, "phone": c_phone, "end": c_end}


def main():
    data = json.loads((ROOT / "src/script.json").read_text())
    cards = data["cards"]
    out = []
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](c, data, i, len(cards)).resize((W, H), Image.LANCZOS)
        im = grain(vignette(im, 150), amount=18, seed=i)
        im.save(ROOT / f"{i:02d}.png")
        out.append(im)
    out[0].save(ROOT / "cover_preview.jpg", quality=92)
    cols, sc = 4, 0.3
    a, b = int(W * sc), int(H * sc)
    rows = math.ceil(len(out) / cols)
    sheet = Image.new("RGB", (cols * a + (cols + 1) * 14, rows * b + (rows + 1) * 14), (30, 30, 34))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (14 + (i % cols) * (a + 14), 14 + (i // cols) * (b + 14)))
    sheet.save(ROOT / "preview.jpg", quality=90)
    print("ok", len(out))


if __name__ == "__main__":
    main()
