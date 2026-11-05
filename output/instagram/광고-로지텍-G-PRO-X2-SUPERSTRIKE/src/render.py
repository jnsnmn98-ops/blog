"""로지텍 G PRO X2 SUPERSTRIKE 광고 카드 렌더러 (Grand Arena 테마). 2배로 그린 뒤 1080x1350으로 축소."""
import json, sys, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

K = 2
W, H = 1080 * K, 1350 * K
FD = Path.home() / "Desktop/blog/output/instagram/_shared_fonts"
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
BG = (5, 7, 12)
G = (60, 255, 160)
TXT = (240, 244, 248)
SUB = (160, 172, 186)
LINE = (60, 255, 160, 120)

def k(v): return int(v * K)
def bh(s): return ImageFont.truetype(str(FD / "BlackHanSans-Regular.ttf"), k(s))
def sd(s, w="semi"): return ImageFont.truetype(SD, k(s), index={"bold": 6, "semi": 4, "reg": 0}[w])

def fit(path, w, h, v=0.5, hf=0.5, zoom=1.0):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int((im.width - w) * hf); y = int((im.height - h) * v)
    return im.crop((x, y, x + w, y + h))

def knockout(path, maxw, maxh):
    """흰 배경을 가장자리 flood-fill로 투명 처리."""
    im = Image.open(path).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L").point(lambda p: 255 if p > 6 else 0).getbbox()
    im = im.crop(bb)
    mask = Image.new("L", im.size, 255)
    tmp = im.copy()
    for pt in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]:
        ImageDraw.floodfill(tmp, pt, (255, 0, 255), thresh=10)
    px = tmp.load(); mp = mask.load()
    for yy in range(im.height):
        for xx in range(im.width):
            if px[xx, yy] == (255, 0, 255): mp[xx, yy] = 0
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    im.putalpha(mask)
    s = min(maxw / im.width, maxh / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)

def grad_overlay(base, top=0.0, bottom=1.0, start=0.35, color=BG, strength=1.0):
    ov = Image.new("RGBA", base.size, color + (0,))
    a = Image.new("L", (1, base.height))
    for y in range(base.height):
        t = y / base.height
        if t < start: v = top * (1 - t / start) if start else 0
        else: v = ((t - start) / (1 - start)) ** 1.4 * bottom
        a.putpixel((0, y), int(255 * min(1, max(v, 0)) * strength))
    ov.putalpha(a.resize(base.size))
    return Image.alpha_composite(base.convert("RGBA"), ov)

def chamfer(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]

def panel(d, x0, y0, x1, y1, fill=(10, 16, 22, 215), outline=LINE, lw=2, c=22):
    d.polygon(chamfer(k(x0), k(y0), k(x1), k(y1), k(c)), fill=fill)
    pts = chamfer(k(x0), k(y0), k(x1), k(y1), k(c)); pts.append(pts[0])
    d.line(pts, fill=outline, width=k(lw))

def brackets(d, x0, y0, x1, y1, L=46, lw=4, col=G):
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(k(x), k(y + sy * L)), (k(x), k(y)), (k(x + sx * L), k(y))], fill=col, width=k(lw))

def glow_text(im, xy, text, font, fill, glow=G, radius=14, anchor="la", alpha=150):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=glow + (alpha,), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(k(radius)))
    im.alpha_composite(layer)
    ImageDraw.Draw(im).text(xy, text, font=font, fill=fill, anchor=anchor)

def wrap(d, text, font, maxw):
    out, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= k(maxw): cur = t
        else: out.append(cur); cur = word
    if cur: out.append(cur)
    return out

def hud(im, n, total):
    d = ImageDraw.Draw(im)
    # 광고 배지
    panel(d, 56, 52, 56 + 92, 52 + 46, fill=G + (255,), outline=G + (255,), lw=1, c=10)
    d.text((k(56 + 46), k(52 + 23)), "광고", font=sd(25, "bold"), fill=BG, anchor="mm")
    d.text((k(168), k(75)), "LOGITECH G  ·  PRO X2 SUPERSTRIKE", font=sd(23, "bold"), fill=TXT + (230,), anchor="lm")
    d.text((k(1024), k(75)), f"{n:02d} / {total:02d}", font=sd(23, "bold"), fill=G, anchor="rm")
    d.line([(k(56), k(118)), (k(1024), k(118))], fill=(255, 255, 255, 40), width=k(1))
    d.line([(k(56), k(118)), (k(56 + 960 * n / total), k(118))], fill=G, width=k(3))

def credit(d, text="ⓒLogitech G · logitechg.com 공식 이미지", y=1318):
    d.text((k(1024), k(y)), text, font=sd(19, "reg"), fill=(200, 208, 216, 170), anchor="rs")

def title_block(im, lines, x, y, size, accent_idx=None, anchor="la", glow=True):
    d = ImageDraw.Draw(im)
    f = bh(size)
    for i, ln in enumerate(lines):
        col = G if i == accent_idx else TXT
        if glow and i == accent_idx:
            glow_text(im, (k(x), k(y)), ln, f, col, anchor=anchor, radius=16, alpha=130)
        else:
            d.text((k(x), k(y)), ln, font=f, fill=col, anchor=anchor)
        y += size * 1.16
    return y

def note(d, text, y_bottom, size=27, x=72, maxw=936, col=SUB):
    f = sd(size, "reg")
    lines = wrap(d, text, f, maxw)
    y = y_bottom - len(lines) * size * 1.45
    for ln in lines:
        d.text((k(x), k(y)), ln, font=f, fill=col); y += size * 1.45

def base():
    return Image.new("RGBA", (W, H), BG + (255,))

def rays(im, cx, cy, n=18, length=1200, spread=1.0, seed=3):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    for i in range(n):
        a = -math.pi / 2 + (i - n / 2) / n * math.pi * spread + rnd.uniform(-0.05, 0.05)
        w = rnd.uniform(0.015, 0.045)
        p1 = (k(cx + math.cos(a - w) * length), k(cy + math.sin(a - w) * length))
        p2 = (k(cx + math.cos(a + w) * length), k(cy + math.sin(a + w) * length))
        d.polygon([(k(cx), k(cy)), p1, p2], fill=G + (rnd.randint(18, 40),))
    layer = layer.filter(ImageFilter.GaussianBlur(k(6)))
    im.alpha_composite(layer)
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([k(cx - 300), k(cy - 220), k(cx + 300), k(cy + 220)], fill=G + (70,))
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(k(90))))

def grid_floor(im, y0, col=G):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    cx = 540
    for i in range(-12, 13):
        d.line([(k(cx), k(y0 - 60)), (k(cx + i * 140), k(1350))], fill=col + (34,), width=k(2))
    y = y0; step = 14
    while y < 1350:
        d.line([(0, k(y)), (W, k(y))], fill=col + (30,), width=k(2)); step *= 1.35; y += step
    mask = Image.new("L", im.size, 0); md = ImageDraw.Draw(mask)
    for yy in range(k(y0), H, 4):
        md.line([(0, yy), (W, yy)], fill=int(255 * min(1, (yy - k(y0)) / k(260))), width=4)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    im.alpha_composite(layer)

# ---------- 카드 ----------
def card_cover(c, root, n, total):
    im = base()
    ph = fit(root / c["photo"], W, k(980), v=c.get("v", 0.5), hf=c.get("hf", 0.5), zoom=c.get("zoom", 1.0))
    im.paste(ph, (0, k(140)))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(k(860), H):
        t = min(1, (y - k(860)) / k(260))
        od.line([(0, y), (W, y)], fill=BG + (int(255 * t ** 1.1),))
    im.alpha_composite(ov)
    # 위쪽 진하게
    top = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(top)
    for y in range(k(330)):
        td.line([(0, y), (W, y)], fill=BG + (int(255 * (1 - y / k(330)) ** 1.2),))
    im.alpha_composite(top)
    d = ImageDraw.Draw(im)
    bx = c.get("box", [250, 330, 830, 830])
    brackets(d, *bx, L=60, lw=5)
    d.text((k(72), k(930)), c["kicker"], font=sd(28, "bold"), fill=G)
    title_block(im, c["title"], 68, 975, 104, accent_idx=1)
    d = ImageDraw.Draw(im)
    d.text((k(72), k(1230)), c["sub"], font=sd(34, "semi"), fill=TXT)
    hud(im, n, total); credit(d)
    return im

def card_feature(c, root, n, total):
    """사진 위 + 아래 텍스트/행"""
    im = base()
    ph_h = c.get("ph_h", 640)
    ph = fit(root / c["photo"], W, k(ph_h), v=c.get("v", 0.5), hf=c.get("hf", 0.5), zoom=c.get("zoom", 1.0))
    im.paste(ph, (0, k(130)))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(k(240)):
        od.line([(0, k(130 + ph_h) - y), (W, k(130 + ph_h) - y)], fill=BG + (int(255 * (1 - y / k(240)) ** 1.3),))
    for y in range(k(90)):
        od.line([(0, k(130) + y), (W, k(130) + y)], fill=BG + (int(200 * (1 - y / k(90))),))
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    if c.get("box"): brackets(d, *c["box"], L=44, lw=4)
    y = 130 + ph_h - 70
    d.text((k(72), k(y)), c["kicker"], font=sd(28, "bold"), fill=G); y += 46
    y = title_block(im, c["title"], 68, y, c.get("tsize", 76), accent_idx=c.get("accent"))
    d = ImageDraw.Draw(im)
    y += 18
    if c.get("text"):
        f = sd(36, "reg")
        for ln in wrap(d, c["text"], f, 936):
            d.text((k(72), k(y)), ln, font=f, fill=TXT); y += 36 * 1.5
        y += 16
    for lab, val in c.get("rows", []):
        f = sd(34, "reg")
        lines = wrap(d, val, f, 690)
        hh = max(1, len(lines)) * 34 * 1.45 + 40
        panel(d, 72, y, 1008, y + hh, c=18)
        d.text((k(102), k(y + hh / 2)), lab, font=bh(36), fill=G, anchor="lm")
        yy = y + 20
        for ln in lines:
            d.text((k(300), k(yy)), ln, font=f, fill=TXT); yy += 34 * 1.45
        y += hh + 14
    if c.get("note"): note(d, c["note"], 1290)
    hud(im, n, total); credit(d)
    return im

def card_stats(c, root, n, total):
    im = base()
    ph = fit(root / c["photo"], W, k(560), v=c.get("v", 0.5), hf=c.get("hf", 0.5), zoom=c.get("zoom", 1.0))
    im.paste(ph, (0, k(130)))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(k(220)):
        od.line([(0, k(690) - y), (W, k(690) - y)], fill=BG + (int(255 * (1 - y / k(220)) ** 1.3),))
    for y in range(k(80)):
        od.line([(0, k(130) + y), (W, k(130) + y)], fill=BG + (int(200 * (1 - y / k(80))),))
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    if c.get("box"): brackets(d, *c["box"], L=44, lw=4)
    y = 600
    d.text((k(72), k(y)), c["kicker"], font=sd(28, "bold"), fill=G); y += 46
    y = title_block(im, c["title"], 68, y, c.get("tsize", 76), accent_idx=c.get("accent"))
    d = ImageDraw.Draw(im)
    y += 22
    stats = c["stats"]; cols = c.get("cols", 2)
    rows = math.ceil(len(stats) / cols)
    gap = 18; cw = (936 - gap * (cols - 1)) / cols; chh = c.get("cell_h", 176)
    for i, (big, small) in enumerate(stats):
        r, cc = divmod(i, cols)
        x0 = 72 + cc * (cw + gap); y0 = y + r * (chh + gap)
        panel(d, x0, y0, x0 + cw, y0 + chh, c=20)
        glow_text(im, (k(x0 + 30), k(y0 + 26)), big, bh(c.get("bsize", 66)), G, radius=12, alpha=90)
        d = ImageDraw.Draw(im)
        f = sd(30, "semi")
        yy = y0 + 26 + c.get("bsize", 66) * 1.12
        for ln in wrap(d, small, f, cw - 60):
            d.text((k(x0 + 30), k(yy)), ln, font=f, fill=TXT); yy += 30 * 1.35
    if c.get("note"): note(d, c["note"], 1290, size=26)
    hud(im, n, total); credit(d)
    return im

def card_body(c, root, n, total):
    im = base()
    grid_floor(im, 690)
    halo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([k(160), k(380), k(920), k(720)], fill=G + (46,))
    im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(k(80))))
    pr = knockout(root / c["photo"], k(c.get("pw", 900)), k(c.get("ph", 420)))
    px = (W - pr.width) // 2; py = k(c.get("py", 300))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([px + pr.width * 0.1, py + pr.height * 0.86, px + pr.width * 0.9, py + pr.height * 1.04], fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(k(16))))
    im.alpha_composite(pr, (px, py))
    d = ImageDraw.Draw(im)
    d.text((k(72), k(160)), c["kicker"], font=sd(28, "bold"), fill=G)
    title_block(im, c["title"], 68, 204, c.get("tsize", 76), accent_idx=c.get("accent"))
    d = ImageDraw.Draw(im)
    y = 790
    specs = c["specs"]
    gap = 16; cw = (936 - gap) / 2; ch = 150
    for i, (big, small) in enumerate(specs):
        r, cc = divmod(i, 2)
        x0 = 72 + cc * (cw + gap); y0 = y + r * (ch + gap)
        panel(d, x0, y0, x0 + cw, y0 + ch, c=18)
        d.text((k(x0 + 28), k(y0 + 24)), big, font=bh(c.get("bsize", 54)), fill=G)
        d.text((k(x0 + 28), k(y0 + 98)), small, font=sd(28, "semi"), fill=TXT)
    if c.get("note"): note(d, c["note"], 1290, size=26)
    hud(im, n, total); credit(d)
    return im

def card_price(c, root, n, total):
    im = base()
    rays(im, 540, 560, n=22, length=1100, spread=1.15)
    grid_floor(im, 720)
    pr = knockout(root / c["photo"], k(c.get("pw", 520)), k(c.get("ph", 470)))
    px = (W - pr.width) // 2; py = k(c.get("py", 300))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([px + pr.width * 0.12, py + pr.height * 0.9, px + pr.width * 0.88, py + pr.height * 1.06], fill=(0, 0, 0, 210))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(k(18))))
    im.alpha_composite(pr, (px, py))
    d = ImageDraw.Draw(im)
    d.text((k(540), k(162)), c["kicker"], font=sd(28, "bold"), fill=G, anchor="mt")
    title_block(im, c["title"], 540, 206, c.get("tsize", 70), accent_idx=None, anchor="mt", glow=False)
    d = ImageDraw.Draw(im)
    y = 820
    panel(d, 72, y, 1008, y + 196, fill=(8, 20, 16, 235), outline=G + (255,), lw=3, c=26)
    d.text((k(110), k(y + 34)), c["price_label"], font=sd(30, "semi"), fill=TXT)
    glow_text(im, (k(110), k(y + 80)), c["price"], bh(84), G, radius=14, alpha=110)
    d = ImageDraw.Draw(im)
    d.text((k(972), k(y + 158)), c["price_sub"], font=sd(26, "reg"), fill=SUB, anchor="rs")
    y += 222
    for t in c.get("notes", []):
        f = sd(28, "reg")
        for ln in wrap(d, "· " + t, f, 936):
            d.text((k(72), k(y)), ln, font=f, fill=SUB); y += 28 * 1.45
        y += 6
    # CTA
    f = sd(34, "bold"); tw = d.textlength(c["cta"], font=f) / K
    cy = 1214
    panel(d, 540 - tw / 2 - 40, cy, 540 + tw / 2 + 40, cy + 66, fill=G + (255,), outline=G + (255,), lw=1, c=16)
    d.text((k(540), k(cy + 33)), c["cta"], font=f, fill=BG, anchor="mm")
    hud(im, n, total); credit(d, y=1330)
    return im

KIND = dict(cover=card_cover, feature=card_feature, stats=card_stats, body=card_body, price=card_price)

def main(folder):
    root = Path(folder)
    data = json.loads((root / "src/cards.json").read_text())
    cards = data["cards"]; total = len(cards)
    outs = []
    for i, c in enumerate(cards, 1):
        im = KIND[c["type"]](c, root, i, total).convert("RGB").resize((1080, 1350), Image.LANCZOS)
        p = root / f"{i:02d}.png"; im.save(p, optimize=True); outs.append(im)
        print("saved", p.name)
    cols = 3; rows = math.ceil(total / cols); tw, th = 360, 450
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (24, 24, 28))
    for i, im in enumerate(outs):
        r, c = divmod(i, cols)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (12 + c * (tw + 12), 12 + r * (th + 12)))
    sheet.save(root / "preview.jpg", quality=90)
    outs[0].resize((540, 675), Image.LANCZOS).save(root / "cover_preview.jpg", quality=90)

if __name__ == "__main__":
    main(sys.argv[1])
