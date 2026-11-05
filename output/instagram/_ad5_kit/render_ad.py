"""광고 카드뉴스 5종 공용 렌더러.
사용: python render_ad.py <주제 폴더>   (폴더 안 src/cards.json 의 "theme"으로 디자인 결정)
테마: cute(귀여운·핑크) / sleek_red(세련된·버건디+골드) / grand(웅장한·각진) / wood(우드톤) / clinic(세련된·화이트+레드)
"""
import json
import math
import pathlib
import random
import re
import sys

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = pathlib.Path(__file__).resolve().parent.parent / "_shared_fonts"
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
W, H = 1080, 1350
K = 2

THEMES = {
    "cute": dict(bg=[(255, 228, 236), (255, 246, 249)], text=(92, 40, 58), sub=(150, 104, 120), accent=(232, 67, 90),
                 accent2=(255, 178, 196), panel=(255, 255, 255), line=(255, 205, 216), hl=(255, 214, 226),
                 title="Jua-Regular.ttf", num="Jua-Regular.ttf", radius=44, frame="sticker"),
    "sleek_red": dict(bg=[(30, 12, 14), (58, 18, 22)], text=(246, 236, 222), sub=(196, 172, 150), accent=(212, 170, 92),
                      accent2=(190, 30, 40), panel=(255, 250, 244), line=(212, 170, 92), hl=(110, 30, 36),
                      title="SongMyung-Regular.ttf", num="SongMyung-Regular.ttf", radius=6, frame="thin"),
    "grand": dict(bg=[(4, 6, 14), (14, 22, 44)], text=(238, 242, 250), sub=(150, 162, 190), accent=(150, 240, 210),
                  accent2=(120, 150, 255), panel=(18, 24, 44), line=(150, 240, 210), hl=(40, 60, 110),
                  title="BlackHanSans-Regular.ttf", num="DoHyeon-Regular.ttf", radius=0, frame="chamfer"),
    "wood": dict(bg=[(244, 234, 216), (232, 216, 190)], text=(74, 50, 30), sub=(130, 104, 78), accent=(150, 98, 52),
                 accent2=(104, 128, 84), panel=(252, 247, 238), line=(196, 160, 118), hl=(236, 214, 180),
                 title="GowunBatang-Bold.ttf", num="GowunBatang-Bold.ttf", radius=10, frame="wood"),
    "clinic": dict(bg=[(252, 252, 253), (240, 243, 247)], text=(30, 40, 60), sub=(110, 120, 140), accent=(206, 30, 42),
                   accent2=(30, 60, 110), panel=(255, 255, 255), line=(220, 226, 236), hl=(252, 226, 228),
                   title="BlackHanSans-Regular.ttf", num="BlackHanSans-Regular.ttf", radius=18, frame="clean"),
}

_cmaps = {}


def cmap(name):
    if name not in _cmaps:
        _cmaps[name] = TTFont(str(FONTS / name)).getBestCmap()
    return _cmaps[name]


def k(v):
    return int(round(v * K))


def ff(name, size):
    return ImageFont.truetype(str(FONTS / name), k(size))


def sd(size, w="semi"):
    return ImageFont.truetype(SD, k(size), index={"bold": 6, "semi": 4, "reg": 0}[w])


def tl(d, t, f):
    return d.textlength(t, font=f) / K


def runs(text, name):
    cm = cmap(name)
    out = []
    for ch in text:
        fb = ord(ch) not in cm and ch != " "
        if out and out[-1][0] == fb:
            out[-1][1] += ch
        else:
            out.append([fb, ch])
    return out


def dw(d, text, name, size):
    return sum(tl(d, t, sd(size, "bold") if fb else ff(name, size)) for fb, t in runs(text, name))


def dtext(d, x, y, text, name, size, fill, anchor="l"):
    """디스플레이 글꼴로 쓰되, 없는 글자만 산돌고딕으로 대신 그린다."""
    w = dw(d, text, name, size)
    if anchor == "m":
        x -= w / 2
    elif anchor == "r":
        x -= w
    base = y + ff(name, size).getmetrics()[0] / K
    for fb, t in runs(text, name):
        f = sd(size, "bold") if fb else ff(name, size)
        d.text((k(x), k(base)), t, font=f, fill=fill, anchor="ls")
        x += tl(d, t, f)
    return w


def stext(d, x, y, text, size, fill, w="semi", anchor="la"):
    d.text((k(x), k(y)), text, font=sd(size, w), fill=fill, anchor=anchor)


def wrap(d, text, font, maxw):
    out, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if tl(d, t, font) > maxw and cur:
            out.append(cur)
            cur = word
        else:
            cur = t
    out.append(cur)
    return out


def rr(d, x0, y0, x1, y1, r, fill=None, outline=None, lw=3):
    if r <= 0:
        d.rectangle((k(x0), k(y0), k(x1), k(y1)), fill=fill, outline=outline, width=k(lw) if outline else 0)
    else:
        d.rounded_rectangle((k(x0), k(y0), k(x1), k(y1)), k(r), fill=fill, outline=outline, width=k(lw) if outline else 0)


def chamfer_pts(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def panel(d, T, x0, y0, x1, y1, fill=None, outline=None, lw=3):
    fill = fill if fill is not None else T["panel"]
    if T["frame"] == "chamfer":
        pts = [(k(x), k(y)) for x, y in chamfer_pts(x0, y0, x1, y1, 28)]
        d.polygon(pts, fill=fill)
        if outline:
            d.line(pts + [pts[0]], fill=outline, width=k(lw))
    else:
        rr(d, x0, y0, x1, y1, max(T["radius"], 6) if T["frame"] != "thin" else 4, fill=fill, outline=outline, lw=lw)


def sparkle(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        q = r if i % 2 == 0 else r * 0.32
        pts.append((k(cx + q * math.cos(a)), k(cy + q * math.sin(a))))
    d.polygon(pts, fill=color)


def heart(d, cx, cy, s, color):
    pts = []
    for i in range(0, 360, 6):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((k(cx + x * s / 16), k(cy + y * s / 16)))
    d.polygon(pts, fill=color)


# ---------- 배경 ----------
def background(T, seed):
    im = Image.new("RGB", (k(W), k(H)))
    d = ImageDraw.Draw(im)
    a, b = T["bg"]
    for y in range(0, k(H), 2):
        t = y / k(H)
        d.line([(0, y), (k(W), y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)), width=2)
    rnd = random.Random(seed)
    th = T["name"]
    if th == "cute":
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for x in range(0, W + 60, 60):
            for y in range(0, H + 60, 60):
                ld.ellipse((k(x - 4), k(y - 4), k(x + 4), k(y + 4)), fill=(255, 255, 255, 140))
        im = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
        d = ImageDraw.Draw(im)
        for _ in range(7):
            sparkle(d, rnd.randint(40, W - 40), rnd.randint(120, H - 120), rnd.randint(9, 16), rnd.choice([(255, 255, 255), T["accent2"]]))
        for _ in range(4):
            heart(d, rnd.randint(40, W - 40), rnd.randint(140, H - 160), rnd.randint(10, 16), T["accent2"])
    elif th == "sleek_red":
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((k(W * 0.2), k(-200), k(W * 1.3), k(700)), fill=(150, 30, 40, 90))
        im = Image.alpha_composite(im.convert("RGBA"), g.filter(ImageFilter.GaussianBlur(k(120)))).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle((k(36), k(36), k(W - 36), k(H - 36)), outline=T["line"], width=k(1))
    elif th == "grand":
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse((k(W * 0.1), k(H * 0.05), k(W * 0.95), k(H * 0.6)), fill=(60, 90, 200, 110))
        gd.ellipse((k(W * 0.45), k(H * 0.2), k(W * 1.2), k(H * 0.7)), fill=(90, 220, 190, 60))
        im = Image.alpha_composite(im.convert("RGBA"), g.filter(ImageFilter.GaussianBlur(k(140)))).convert("RGB")
        d = ImageDraw.Draw(im)
        for i in range(-6, 14):
            x = i * 110
            d.line([(k(x), k(H)), (k(x + 500), 0)], fill=(30, 40, 70), width=k(1))
        for _ in range(60):
            x, y = rnd.randint(0, W), rnd.randint(0, H)
            d.ellipse((k(x), k(y), k(x + 2), k(y + 2)), fill=(180, 200, 255))
    elif th == "wood":
        for _ in range(140):
            y = rnd.uniform(0, H)
            amp = rnd.uniform(2, 8)
            col = tuple(max(0, c - rnd.randint(4, 16)) for c in a)
            pts = [(k(x), k(y + amp * math.sin(x / rnd.uniform(60, 160) + rnd.random() * 6))) for x in range(0, W + 20, 20)]
            d.line(pts, fill=col, width=k(rnd.uniform(0.6, 1.8)))
    elif th == "clinic":
        for x in range(0, W, 54):
            d.line([(k(x), 0), (k(x), k(H))], fill=(236, 240, 246), width=k(1))
        for y in range(0, H, 54):
            d.line([(0, k(y)), (k(W), k(y))], fill=(236, 240, 246), width=k(1))
        rr(d, 0, 0, W, 14, 0, fill=T["accent"])
    return im


# ---------- 사진 ----------
def fit(path, w, h, vfocus=0.5, hfocus=0.5, crop=None):
    img = Image.open(path).convert("RGB")
    if crop:
        img = img.crop(tuple(crop))
    sc = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * sc)), max(h, round(img.height * sc))), Image.LANCZOS)
    x = int((img.width - w) * hfocus)
    y = int((img.height - h) * vfocus)
    return img.crop((x, y, x + w, y + h))


def knockout(im, T, path, x, y, w, h, crop=None):
    """흰 배경 제품컷의 배경을 지우고 어두운 바탕 위에 빛과 함께 올린다."""
    img = Image.open(path).convert("RGB")
    if crop:
        img = img.crop(tuple(crop))
    g = img.convert("L")
    alpha = g.point(lambda v: 0 if v > 246 else 255).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    rgba = img.convert("RGBA")
    rgba.putalpha(alpha)
    bbox = alpha.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    sc = min(k(w) / rgba.width, k(h) / rgba.height)
    rgba = rgba.resize((int(rgba.width * sc), int(rgba.height * sc)), Image.LANCZOS)
    base = im.convert("RGBA")
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    cx, cy = k(x + w / 2), k(y + h / 2)
    ImageDraw.Draw(glow).ellipse((cx - rgba.width * 0.7, cy - rgba.height * 0.45, cx + rgba.width * 0.7, cy + rgba.height * 0.45),
                                 fill=T["accent2"] + (120,))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(k(80))))
    base.alpha_composite(rgba, (int(cx - rgba.width / 2), int(cy - rgba.height / 2)))
    return base.convert("RGB")


def photo(im, T, path, x, y, w, h, vfocus=0.5, hfocus=0.5, crop=None, angle=0, ko=False):
    if ko:
        return knockout(im, T, path, x, y, w, h, crop)
    ph = fit(path, k(w), k(h), vfocus, hfocus, crop)
    mask = Image.new("L", ph.size, 0)
    md = ImageDraw.Draw(mask)
    fr = T["frame"]
    if fr == "chamfer":
        md.polygon([(k(px), k(py)) for px, py in chamfer_pts(0, 0, w, h, 40)], fill=255)
    else:
        md.rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), k(T["radius"] if fr != "thin" else 4), fill=255)
    border = 12 if fr == "sticker" else 0
    pad = k(40)
    out = Image.new("RGBA", (ph.width + k(border * 2) + pad * 2, ph.height + k(border * 2) + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    shd = ImageDraw.Draw(sh)
    sc = (0, 0, 0, 110) if T["name"] in ("grand", "sleek_red") else (90, 60, 40, 60)
    shd.rounded_rectangle((pad, pad + k(14), out.width - pad, out.height - pad + k(14)), k(max(T["radius"], 4)), fill=sc)
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(k(16))))
    if border:
        bm = Image.new("L", (ph.width + k(border * 2), ph.height + k(border * 2)), 0)
        ImageDraw.Draw(bm).rounded_rectangle((0, 0, bm.width - 1, bm.height - 1), k(T["radius"] + border), fill=255)
        out.paste(Image.new("RGBA", bm.size, (255, 255, 255, 255)), (pad, pad), bm)
    out.paste(ph, (pad + k(border), pad + k(border)), mask)
    od = ImageDraw.Draw(out)
    if fr == "thin":
        od.rectangle((pad, pad, pad + ph.width - 1, pad + ph.height - 1), outline=T["line"], width=k(2))
    elif fr == "chamfer":
        pts = [(pad + k(px), pad + k(py)) for px, py in chamfer_pts(0, 0, w, h, 40)]
        od.line(pts + [pts[0]], fill=T["line"], width=k(3))
    elif fr == "wood":
        od.rounded_rectangle((pad, pad, pad + ph.width - 1, pad + ph.height - 1), k(T["radius"]), outline=T["line"], width=k(3))
    elif fr == "clean":
        od.rounded_rectangle((pad, pad, pad + ph.width - 1, pad + ph.height - 1), k(T["radius"]), outline=T["line"], width=k(2))
    if angle:
        out = out.rotate(angle, resample=Image.BICUBIC, expand=True)
    cx, cy = k(x + w / 2), k(y + h / 2)
    base = im.convert("RGBA")
    base.alpha_composite(out, (int(cx - out.width / 2), int(cy - out.height / 2)))
    return base.convert("RGB")


# ---------- 공통 요소 ----------
def header(d, T, data, n, total):
    lab = data.get("ad_label", "광고")
    w = tl(d, lab, sd(26, "bold")) + 40
    rr(d, 56, 50, 56 + w, 94, 22 if T["frame"] != "chamfer" else 0, fill=T["accent"])
    stext(d, 56 + w / 2, 72, lab, 26, (255, 255, 255) if T["name"] != "grand" else (8, 12, 24), "bold", anchor="mm")
    stext(d, 56 + w + 16, 58, data["account"], 25, T["sub"])
    stext(d, W - 56, 58, f"{n} / {total}", 25, T["sub"], anchor="ra")


def dots(d, T, n, total):
    gap = 24
    x0 = W / 2 - (total - 1) * gap / 2
    for i in range(total):
        cx = x0 + i * gap
        if i == n - 1:
            rr(d, cx - 14, H - 54, cx + 14, H - 44, 4, fill=T["accent"])
        else:
            d.ellipse((k(cx - 4), k(H - 53), k(cx + 4), k(H - 45)), fill=T["line"])


def title(d, T, lines, x, y, size, accent=1, center=False):
    name = T["title"]
    for i, ln in enumerate(lines):
        w = dw(d, ln, name, size)
        lx = (W - w) / 2 if center else x
        col = T["accent"] if i == accent else T["text"]
        if i == accent and T["name"] in ("cute", "wood", "clinic"):
            rr(d, lx - 8, y + size * 0.62, lx + w + 8, y + size * 1.02, 10 if T["name"] == "cute" else 0, fill=T["hl"])
        dtext(d, lx, y, ln, name, size, col)
        y += int(size * 1.2)
    return y


def credit(d, T, text, x, y, anchor="ra"):
    stext(d, x, y, text, 20, T["sub"], "reg", anchor=anchor)


def note(d, T, text, y_bottom=H - 92, size=22, x=72, maxw=W - 144):
    f = sd(size, "reg")
    lines = []
    for para in text.split("\n"):
        lines += wrap(d, para, f, maxw)
    y = y_bottom - len(lines) * (size + 9)
    for ln in lines:
        d.text((k(x), k(y)), ln, font=f, fill=T["sub"])
        y += size + 9
    return y


def price_badge(d, T, x, y, label, value):
    nm = T["num"]
    if T["name"] == "cute":
        r = 112
        pts = []
        for i in range(32):
            a = math.pi * 2 * i / 32
            q = r if i % 2 == 0 else r * 0.88
            pts.append((k(x + q * math.cos(a)), k(y + q * math.sin(a))))
        d.polygon(pts, fill=T["accent"])
        dtext(d, x, y - 48, label, nm, 32, (255, 255, 255), anchor="m")
        dtext(d, x, y - 6, value, nm, 44, (255, 255, 255), anchor="m")
    elif T["name"] == "grand":
        w = max(dw(d, value, nm, 52), dw(d, label, nm, 26)) + 60
        pts = [(k(px), k(py)) for px, py in chamfer_pts(x - w / 2, y - 62, x + w / 2, y + 62, 22)]
        d.polygon(pts, fill=(8, 12, 24))
        d.line(pts + [pts[0]], fill=T["accent"], width=k(3))
        dtext(d, x, y - 50, label, nm, 26, T["accent"], anchor="m")
        dtext(d, x, y - 14, value, nm, 52, T["text"], anchor="m")
    else:
        w = max(tl(d, value, sd(40, "bold")), tl(d, label, sd(22))) + 60
        fill = T["accent"] if T["name"] != "sleek_red" else (24, 10, 12)
        rr(d, x - w / 2, y - 58, x + w / 2, y + 58, 6 if T["name"] != "wood" else 58, fill=fill,
           outline=T["line"] if T["name"] == "sleek_red" else None, lw=2)
        tc = (255, 255, 255) if T["name"] != "sleek_red" else T["accent"]
        stext(d, x, y - 26, label, 22, tc, "semi", anchor="mm")
        stext(d, x, y + 16, value, 40, tc if T["name"] != "sleek_red" else T["text"], "bold", anchor="mm")


# ---------- 카드 종류 ----------
def card_cover(T, data, c, n, total, root):
    im = background(T, n)
    ph = c["photo"]
    im = photo(im, T, root / ph["file"], 64, 128, 952, ph.get("h", 700), ph.get("v", 0.5), ph.get("hf", 0.5), ph.get("crop"),
               angle=ph.get("angle", 0), ko=ph.get("ko", False))
    d = ImageDraw.Draw(im)
    header(d, T, data, n, total)
    py = 128 + ph.get("h", 700)
    credit(d, T, data["credit"], 1012, py + 10)
    if c.get("price"):
        price_badge(d, T, 870, 250, c["price"][0], c["price"][1])
    y = py + 50
    tag = c.get("tag")
    if tag:
        f = sd(28, "bold")
        w = tl(d, tag, f) + 44
        panel(d, T, 72, y, 72 + w, y + 50, fill=T["hl"] if T["name"] != "grand" else (20, 30, 60), outline=T["line"] if T["name"] in ("grand", "sleek_red") else None, lw=2)
        stext(d, 72 + w / 2, y + 25, tag, 28, T["accent"] if T["name"] != "sleek_red" else T["accent"], "bold", anchor="mm")
        y += 70
    y = title(d, T, c["title"], 72, y, c.get("size", 88), accent=c.get("accent", 1))
    if c.get("sub"):
        stext(d, 76, y + 2, c["sub"], 30, T["sub"], "semi")
    deco(d, T, n)
    dots(d, T, n, total)
    return im


def deco(d, T, seed):
    rnd = random.Random(seed * 7)
    if T["name"] == "cute":
        for _ in range(3):
            heart(d, rnd.randint(60, W - 60), rnd.randint(150, 400), rnd.randint(12, 20), (255, 255, 255))
    elif T["name"] == "grand":
        d.line([(k(72), k(H - 120)), (k(W - 72), k(H - 120))], fill=(40, 60, 100), width=k(1))


def card_points(T, data, c, n, total, root):
    """사진 + 제목 + 항목 목록."""
    im = background(T, n)
    d = ImageDraw.Draw(im)
    header(d, T, data, n, total)
    y = title(d, T, c["title"], 72, 120, c.get("size", 80), accent=c.get("accent", 1))
    ph = c["photo"]
    side = c.get("layout", "top")
    if side == "left":
        pw, phh = 400, ph.get("h", 640)
        im = photo(im, T, root / ph["file"], 64, y + 30, pw, phh, ph.get("v", 0.5), ph.get("hf", 0.5), ph.get("crop"), ko=ph.get("ko", False))
        d = ImageDraw.Draw(im)
        credit(d, T, data["credit"], 64 + pw, y + 40 + phh, anchor="ra")
        lx, ly, lw_ = 500, y + 30, W - 500 - 64
    else:
        phh = ph.get("h", 430)
        im = photo(im, T, root / ph["file"], 64, y + 24, 952, phh, ph.get("v", 0.5), ph.get("hf", 0.5), ph.get("crop"), ko=ph.get("ko", False))
        d = ImageDraw.Draw(im)
        credit(d, T, data["credit"], 1012, y + 34 + phh)
        lx, ly, lw_ = 64, y + 74 + phh, W - 128
    if c.get("quote"):
        q = c["quote"]
        f = ff(T["title"], 44)
        lines = []
        for para in q.split("\n"):
            lines += wrap(d, para, f, lw_ - 80)
        hh = len(lines) * 60 + 80
        panel(d, T, lx, ly, lx + lw_, ly + hh, fill=T["panel"] if T["name"] not in ("sleek_red", "grand") else T["hl"],
              outline=T["line"], lw=2)
        if c.get("quote_label"):
            stext(d, lx + 36, ly + 22, c["quote_label"], 24, T["accent"], "bold")
        yy = ly + 58
        col = T["text"] if T["name"] in ("sleek_red", "grand") else T["text"]
        for ln in lines:
            dtext(d, lx + 36, yy, ln, T["title"], 44, col)
            yy += 60
        ly += hh + 26
    for i, it in enumerate(c.get("items", [])):
        head, body = it[0], it[1] if len(it) > 1 else ""
        fb = sd(31, "bold")
        fr = sd(27, "reg")
        blines = wrap(d, body, fr, lw_ - 110) if body else []
        hh = 34 + 44 + len(blines) * 38 + 10
        panel(d, T, lx, ly, lx + lw_, ly + hh, outline=T["line"], lw=2)
        mark_c = T["accent"]
        if T["frame"] == "chamfer":
            d.polygon([(k(px), k(py)) for px, py in chamfer_pts(lx + 24, ly + 28, lx + 70, ly + 74, 10)], fill=mark_c)
            stext(d, lx + 47, ly + 51, str(i + 1), 26, (8, 12, 24), "bold", anchor="mm")
        else:
            d.ellipse((k(lx + 24), k(ly + 28), k(lx + 70), k(ly + 74)), fill=mark_c)
            stext(d, lx + 47, ly + 51, str(i + 1), 26, (255, 255, 255) if T["name"] != "sleek_red" else (24, 10, 12), "bold", anchor="mm")
        tcol = T["text"] if T["name"] not in ("sleek_red",) else (40, 20, 22)
        bcol = T["sub"] if T["name"] not in ("sleek_red",) else (110, 80, 70)
        if T["name"] == "grand":
            tcol, bcol = T["text"], T["sub"]
        d.text((k(lx + 92), k(ly + 30)), head, font=fb, fill=tcol)
        yy = ly + 78
        for bl in blines:
            d.text((k(lx + 92), k(yy)), bl, font=fr, fill=bcol)
            yy += 38
        ly += hh + 16
    if c.get("chips"):
        x = lx
        for t in c["chips"]:
            f = sd(26, "bold")
            w = tl(d, t, f) + 40
            if x + w > lx + lw_:
                x, ly = lx, ly + 62
            panel(d, T, x, ly, x + w, ly + 48, fill=T["hl"], outline=None)
            stext(d, x + w / 2, ly + 24, t, 26, T["accent"] if T["name"] != "sleek_red" else T["text"], "bold", anchor="mm")
            x += w + 12
    if c.get("note"):
        note(d, T, c["note"])
    deco(d, T, n)
    dots(d, T, n, total)
    return im


def card_stats(T, data, c, n, total, root):
    im = background(T, n)
    d = ImageDraw.Draw(im)
    header(d, T, data, n, total)
    y = title(d, T, c["title"], 72, 120, c.get("size", 80), accent=c.get("accent", 1))
    ph = c["photo"]
    phh = ph.get("h", 400)
    im = photo(im, T, root / ph["file"], 64, y + 24, 952, phh, ph.get("v", 0.5), ph.get("hf", 0.5), ph.get("crop"), ko=ph.get("ko", False))
    d = ImageDraw.Draw(im)
    credit(d, T, data["credit"], 1012, y + 34 + phh)
    sy = y + 80 + phh
    stats = c["stats"]
    cols = len(stats) if len(stats) <= 3 else 2
    gap = 18
    cw = (W - 128 - gap * (cols - 1)) / cols
    for i, (num, lab) in enumerate(stats):
        r, col = divmod(i, cols)
        x0 = 64 + col * (cw + gap)
        y0 = sy + r * 200
        panel(d, T, x0, y0, x0 + cw, y0 + 182, fill=T["panel"] if T["name"] not in ("grand",) else T["panel"], outline=T["line"], lw=2)
        ncol = T["accent"] if T["name"] != "sleek_red" else (150, 26, 34)
        size = c.get("num_size", 72 if cols < 3 else 58)
        dtext(d, x0 + cw / 2, y0 + 18, num, T["num"], size, ncol, anchor="m")
        lcol = T["sub"] if T["name"] != "sleek_red" else (100, 70, 60)
        f = sd(25, "semi")
        for j, ln in enumerate(wrap(d, lab, f, cw - 30)[:2]):
            d.text((k(x0 + cw / 2), k(y0 + 112 + j * 32)), ln, font=f, fill=lcol, anchor="ma")
    if c.get("note"):
        note(d, T, c["note"])
    deco(d, T, n)
    dots(d, T, n, total)
    return im


def card_price(T, data, c, n, total, root):
    im = background(T, n)
    ph = c["photo"]
    phh = ph.get("h", 420)
    im = photo(im, T, root / ph["file"], 64, 120, 952, phh, ph.get("v", 0.5), ph.get("hf", 0.5), ph.get("crop"), ko=ph.get("ko", False))
    d = ImageDraw.Draw(im)
    header(d, T, data, n, total)
    credit(d, T, data["credit"], 1012, 130 + phh)
    y = 170 + phh
    for i, row in enumerate(c["rows"]):
        lab, val = row[0], row[1]
        extra = row[2] if len(row) > 2 else ""
        hh = 120
        main = i == 0
        fill = T["accent"] if (main and T["name"] in ("cute", "clinic", "wood")) else T["panel"]
        if T["name"] == "sleek_red" and main:
            fill = (24, 10, 12)
        if T["name"] == "grand" and main:
            fill = (10, 16, 32)
        panel(d, T, 64, y, W - 64, y + hh, fill=fill, outline=T["line"], lw=2 if not main else 3)
        light = main and T["name"] in ("cute", "clinic", "wood")
        lc = (255, 255, 255) if light else (T["sub"] if T["name"] not in ("sleek_red",) or main else (110, 80, 70))
        vc = (255, 255, 255) if light else (T["text"] if T["name"] in ("grand",) or main else (40, 20, 22))
        if T["name"] == "sleek_red" and main:
            vc = T["accent"]
        stext(d, 100, y + 26, lab, 26, lc, "semi")
        if extra:
            stext(d, 100, y + 68, extra, 22, lc, "reg")
        dtext(d, W - 100, y + 22, val, T["num"], 64 if main else 52, vc, anchor="r")
        y += hh + 14
    y += 6
    if c.get("cta"):
        f = ff(T["title"], 44)
        dtext(d, W / 2, y, c["cta"], T["title"], 44, T["accent"], anchor="m")
        y += 70
    for ln in c.get("notices", []):
        f = sd(23, "bold")
        for wl in wrap(d, ln, f, W - 160):
            d.text((k(W / 2), k(y)), wl, font=f, fill=T["text"], anchor="ma")
            y += 32
    if c.get("note"):
        note(d, T, c["note"], size=20)
    dots(d, T, n, total)
    return im


RENDER = {"cover": card_cover, "points": card_points, "stats": card_stats, "price": card_price}


def main(folder):
    root = pathlib.Path(folder).resolve()
    data = json.loads((root / "src/cards.json").read_text())
    T = dict(THEMES[data["theme"]])
    T["name"] = data["theme"]
    out = []
    cards = data["cards"]
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](T, data, c, i, len(cards), root).resize((W, H), Image.LANCZOS)
        im.save(root / f"{i:02d}.png")
        out.append(im)
    out[0].save(root / "cover_preview.jpg", quality=92)
    cols, sc = len(out), 0.3
    a, b = int(W * sc), int(H * sc)
    sheet = Image.new("RGB", (cols * a + (cols + 1) * 12, b + 24), (230, 230, 230))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (12 + i * (a + 12), 12))
    sheet.save(root / "preview.jpg", quality=90)
    print("ok", root.name, len(out))


if __name__ == "__main__":
    for f in sys.argv[1:]:
        main(f)
