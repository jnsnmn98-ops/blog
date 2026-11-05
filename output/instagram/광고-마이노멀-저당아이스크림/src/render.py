"""마이노멀 저당 아이스크림 광고 카드 — 베이지 무드 + 아이스크림 캐릭터. 2배로 그린 뒤 축소."""
import json, sys, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, str(Path(__file__).parent))
import character as CH

K = 2
W, H = 1080 * K, 1350 * K
FD = Path.home() / "Desktop/blog/output/instagram/_shared_fonts"
SDF = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
BG1, BG2 = (246, 238, 225), (234, 219, 198)
INK = (74, 52, 38)
SUB = (128, 104, 86)
ACC = (214, 120, 98)      # 딸기 코랄
CARA = (201, 146, 88)     # 캐러멜
CARD = (255, 251, 244)

def k(v): return int(round(v * K))
def jua(s): return ImageFont.truetype(str(FD / "Jua-Regular.ttf"), k(s))
def sd(s, w="semi"): return ImageFont.truetype(SDF, k(s), index={"bold": 6, "semi": 4, "reg": 0}[w])
def tl(d, t, f): return d.textlength(t, font=f) / K

def wrap(d, t, f, maxw):
    out, cur = [], ""
    for w in t.split(" "):
        s = (cur + " " + w).strip()
        if tl(d, s, f) > maxw and cur: out.append(cur); cur = w
        else: cur = s
    out.append(cur); return out

def background(seed):
    im = Image.new("RGB", (W, H), BG1)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(BG1[i] * (1 - t) + BG2[i] * t) for i in range(3)))
    im = im.convert("RGBA")
    # 따뜻한 빛(분위기): 왼쪽 위 은은한 광원
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([k(-300), k(-300), k(700), k(600)], fill=(255, 246, 228, 150))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(k(160))))
    # 비네트
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([k(-200), k(-150), k(1280), k(1500)], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(k(160)))
    dark = Image.new("RGBA", (W, H), (120, 84, 56, 60))
    dark.putalpha(Image.eval(vig, lambda v: int((255 - v) * 0.30)))
    im.alpha_composite(dark)
    # 종이 결
    rnd = random.Random(seed)
    noise = Image.effect_noise((W // 4, H // 4), 18).resize((W, H)).convert("L")
    grain = Image.new("RGBA", (W, H), (90, 60, 40, 0)); grain.putalpha(Image.eval(noise, lambda v: max(0, v - 120) // 6))
    im.alpha_composite(grain)
    return im

def shadow_paste(im, piece, x, y, blur=22, off=(0, 16), alpha=70):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    a = piece.getchannel("A").point(lambda v: int(v * alpha / 255))
    s = Image.new("RGBA", piece.size, (90, 60, 40, 0)); s.putalpha(a)
    sh.paste(s, (x + k(off[0]), y + k(off[1])), s)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(k(blur))))
    im.alpha_composite(piece, (x, y))

def photo_frame(root, ph, w, h, r=44, border=14, tilt=0):
    img = Image.open(root / ph["file"]).convert("RGB")
    if ph.get("crop"): img = img.crop(tuple(ph["crop"]))
    W2, H2 = k(w - 2 * border), k(h - 2 * border)
    sc = max(W2 / img.width, H2 / img.height) * ph.get("zoom", 1.0)
    img = img.resize((round(img.width * sc), round(img.height * sc)), Image.LANCZOS)
    x = int((img.width - W2) * ph.get("hf", 0.5)); y = int((img.height - H2) * ph.get("v", 0.5))
    img = img.crop((x, y, x + W2, y + H2))
    fr = Image.new("RGBA", (k(w), k(h)), (0, 0, 0, 0))
    m = Image.new("L", (k(w), k(h)), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, k(w) - 1, k(h) - 1], radius=k(r), fill=255)
    fr.paste(CARD + (255,), (0, 0), m)
    mi = Image.new("L", (W2, H2), 0); ImageDraw.Draw(mi).rounded_rectangle([0, 0, W2 - 1, H2 - 1], radius=k(r - border * 0.6), fill=255)
    fr.paste(img, (k(border), k(border)), mi)
    if tilt: fr = fr.rotate(tilt, resample=Image.BICUBIC, expand=True)
    return fr

def chip(d, x, y, text, fill=INK, col=CARD, size=26, pad=18, font=None):
    f = font or sd(size, "bold"); w = tl(d, text, f) + pad * 2; h = size + 22
    d.rounded_rectangle([k(x), k(y), k(x + w), k(y + h)], radius=k(h / 2), fill=fill)
    d.text((k(x + w / 2), k(y + h / 2)), text, font=f, fill=col, anchor="mm")
    return x + w

def header(d, n, total):
    nx = chip(d, 56, 48, "광고", fill=INK, col=CARD, size=26)
    d.text((k(nx + 16), k(48 + 24)), "마이노멀 저당 아이스크림", font=sd(25, "semi"), fill=SUB, anchor="lm")
    # 쪽수: 작은 동그라미 스쿱
    x0 = 1024 - (total - 1) * 22
    for i in range(total):
        cx = x0 + i * 22; r = 8 if i + 1 == n else 5
        d.ellipse([k(cx - r), k(72 - r), k(cx + r), k(72 + r)], fill=ACC if i + 1 == n else (214, 196, 172))

def bubble(im, x, y, text, size=34, tail="left", fill=CARD):
    d = ImageDraw.Draw(im); f = jua(size)
    lines = text.split("\n")
    w = max(tl(d, l, f) for l in lines) + 56; h = len(lines) * size * 1.25 + 34
    piece = Image.new("RGBA", (k(w + 40), k(h + 40)), (0, 0, 0, 0)); pd = ImageDraw.Draw(piece)
    pd.rounded_rectangle([k(4), k(4), k(w), k(h)], radius=k(min(36, h / 2)), fill=fill, outline=INK, width=k(3))
    tx = 40 if tail == "left" else w - 60
    pd.polygon([(k(tx), k(h - 2)), (k(tx + 30), k(h - 2)), (k(tx + (0 if tail == "left" else 34)), k(h + 30))], fill=fill)
    pd.line([(k(tx), k(h)), (k(tx + (0 if tail == "left" else 34)), k(h + 30)), (k(tx + 30), k(h))], fill=INK, width=k(3), joint="curve")
    yy = 4 + 17
    for l in lines:
        pd.text((k(4 + (w - 4) / 2), k(yy + size * 0.62)), l, font=f, fill=INK, anchor="mm"); yy += size * 1.25
    shadow_paste(im, piece, k(x), k(y), blur=10, off=(0, 6), alpha=40)
    return w, h

def title(im, lines, x, y, size, accent=None, anchor="la"):
    d = ImageDraw.Draw(im); f = jua(size)
    for i, ln in enumerate(lines):
        if i == accent:
            w = tl(d, ln, f)
            x0 = x - w / 2 if anchor == "ma" else x
            d.rounded_rectangle([k(x0 - 10), k(y + size * 0.52), k(x0 + w + 10), k(y + size * 1.02)], radius=k(16), fill=(246, 200, 180))
        d.text((k(x), k(y)), ln, font=f, fill=INK, anchor=anchor)
        y += size * 1.18
    return y

def char(im, spec, x, y):
    c = CH.draw(k(spec.get("size", 260)), spec.get("flavor", "vanilla"), spec.get("eyes", "open"), spec.get("arms", "wave"), tilt=spec.get("tilt", 0))
    im.alpha_composite(c, (k(x), k(y)))

def credit(d, text="사진 ⓒ마이노멀 공식몰 · 캐릭터 일러스트는 자체 제작", y=1318):
    d.text((k(540), k(y)), text, font=sd(19, "reg"), fill=SUB, anchor="ms")

def panel(im, x0, y0, x1, y1, r=36):
    piece = Image.new("RGBA", (k(x1 - x0), k(y1 - y0)), (0, 0, 0, 0))
    ImageDraw.Draw(piece).rounded_rectangle([0, 0, k(x1 - x0) - 1, k(y1 - y0) - 1], radius=k(r), fill=CARD + (238,))
    shadow_paste(im, piece, k(x0), k(y0), blur=18, off=(0, 10), alpha=40)

def rows_block(im, rows, x0, y, x1, lab_w=190):
    d = ImageDraw.Draw(im)
    for i, (lab, val) in enumerate(rows):
        f = sd(33, "semi"); lines = wrap(d, val, f, x1 - x0 - lab_w)
        if i: d.line([(k(x0), k(y - 16)), (k(x1), k(y - 16))], fill=(230, 214, 194), width=k(2))
        d.text((k(x0), k(y)), lab, font=jua(36), fill=ACC)
        yy = y + 2
        for ln in lines: d.text((k(x0 + lab_w), k(yy)), ln, font=f, fill=INK); yy += 33 * 1.45
        y = max(y + 52, yy) + 30
    return y

def note(d, text, y_bottom, size=26, x=72, maxw=936):
    lines = wrap(d, text, sd(size, "reg"), maxw); y = y_bottom - len(lines) * size * 1.45
    for ln in lines: d.text((k(x), k(y)), ln, font=sd(size, "reg"), fill=SUB); y += size * 1.45

# ---------------- 카드 ----------------
def c_cover(c, root, n, total):
    im = background(n)
    fr = photo_frame(root, c["photo"], 860, 720, tilt=-2.5)
    shadow_paste(im, fr, k(110), k(140))
    char(im, c["char"], 660, 580)
    bubble(im, 500, 560, c["bubble"], size=36, tail="right")
    d = ImageDraw.Draw(im)
    y = title(im, c["title"], 72, 945, 100, accent=c.get("accent"))
    d.text((k(76), k(y + 14)), c["sub"], font=sd(34, "semi"), fill=SUB)
    header(d, n, total); credit(d)
    return im

def c_feature(c, root, n, total):
    im = background(n)
    d = ImageDraw.Draw(im)
    chip(d, 72, 140, c["kicker"], fill=CARA, col=CARD, size=26)
    y = title(im, c["title"], 72, 200, c.get("tsize", 80), accent=c.get("accent"))
    ph_y = y + 20; ph_h = c.get("ph_h", 470)
    fr = photo_frame(root, c["photo"], 936, ph_h, tilt=c.get("tilt", 1.5))
    shadow_paste(im, fr, k(60), k(ph_y))
    cs = c["char"]; char(im, cs, cs.get("x", 800), ph_y + ph_h - cs.get("size", 230) * 0.62)
    if c.get("bubble"): bubble(im, cs.get("bx", 520), ph_y + ph_h - cs.get("size", 230) * 0.62 - 40, c["bubble"], size=32, tail="right")
    py = ph_y + ph_h + 70
    panel(im, 60, py, 1020, 1270)
    yy = py + 40
    d = ImageDraw.Draw(im)
    if c.get("text"):
        for ln in wrap(d, c["text"], sd(36, "semi"), 860):
            d.text((k(100), k(yy)), ln, font=sd(36, "semi"), fill=INK); yy += 36 * 1.5
        yy += 20
    if c.get("rows"): yy = rows_block(im, c["rows"], 100, yy, 980)
    if c.get("note"): note(d, c["note"], 1250, size=26, x=100, maxw=880)
    header(d, n, total); credit(d)
    return im

def c_price(c, root, n, total):
    im = background(n)
    d = ImageDraw.Draw(im)
    chip(d, 72, 140, c["kicker"], fill=CARA, col=CARD, size=26)
    title(im, c["title"], 72, 200, 80, accent=c.get("accent"))
    fr = photo_frame(root, c["photo"], 400, 420, tilt=-3)
    shadow_paste(im, fr, k(600), k(130))
    panel(im, 60, 590, 1020, 1040)
    y = 628
    for i, (lab, sub_, price, old) in enumerate(c["rows"]):
        if i: d.line([(k(100), k(y - 18)), (k(980), k(y - 18))], fill=(230, 214, 194), width=k(2))
        d.text((k(100), k(y)), lab, font=jua(42), fill=INK)
        d.text((k(100), k(y + 54)), sub_, font=sd(26, "reg"), fill=SUB)
        d.text((k(980), k(y + 2)), price, font=jua(58), fill=ACC, anchor="ra")
        if old:
            f = sd(26, "reg"); w = tl(d, old, f)
            d.text((k(980), k(y + 74)), old, font=f, fill=SUB, anchor="ra")
            d.line([(k(980 - w), k(y + 74 + 15)), (k(980), k(y + 74 + 15))], fill=SUB, width=k(2))
        y += 136
    cs = c["char"]; char(im, cs, 800, 1040)
    d = ImageDraw.Draw(im)
    yb = 1086
    for t in c.get("notes", []):
        for ln in wrap(d, "· " + t, sd(27, "reg"), 700):
            d.text((k(72), k(yb)), ln, font=sd(27, "reg"), fill=SUB); yb += 40
    d.text((k(72), k(yb + 20)), c["cta"], font=jua(40), fill=INK)
    header(d, n, total); credit(d, y=1336)
    return im

def c_flavors(c, root, n, total):
    im = background(n)
    d = ImageDraw.Draw(im)
    chip(d, 72, 140, c["kicker"], fill=CARA, col=CARD, size=26)
    y = title(im, c["title"], 72, 200, 80, accent=c.get("accent"))
    fr = photo_frame(root, c["photo"], 936, 470, tilt=-1.2)
    shadow_paste(im, fr, k(68), k(y + 16))
    py = y + 16 + 470 + 40
    for i, (flv, name, desc) in enumerate(c["rows"]):
        cx = 72 + i * 316
        panel(im, cx, py, cx + 300, 1275, r=32)
        char(im, {"size": 200, "flavor": flv, "eyes": ["open", "happy", "wink"][i], "arms": ["wave", "up", "down"][i], "tilt": [-5, 4, -3][i]}, cx + 50, py - 110)
        d = ImageDraw.Draw(im)
        d.text((k(cx + 150), k(py + 96)), name, font=jua(40), fill=INK, anchor="ma")
        yy = py + 150
        for ln in wrap(d, desc, sd(27, "semi"), 250):
            d.text((k(cx + 150), k(yy)), ln, font=sd(27, "semi"), fill=SUB, anchor="ma"); yy += 27 * 1.45
    header(d, n, total); credit(d)
    return im

def c_closing(c, root, n, total):
    im = background(n)
    fr = photo_frame(root, c["photo"], 900, 760, tilt=2)
    shadow_paste(im, fr, k(80), k(130))
    char(im, c["char"], 10, 600)
    bubble(im, 320, 620, c["bubble"], size=36, tail="left")
    d = ImageDraw.Draw(im)
    y = title(im, c["title"], 540, 960, 92, accent=c.get("accent"), anchor="ma")
    f = jua(38); w = tl(d, c["cta"], f) + 80
    d.rounded_rectangle([k(540 - w / 2), k(y + 26), k(540 + w / 2), k(y + 26 + 76)], radius=k(38), fill=INK)
    d.text((k(540), k(y + 26 + 38)), c["cta"], font=f, fill=CARD, anchor="mm")
    header(d, n, total); credit(d)
    return im

KIND = dict(cover=c_cover, feature=c_feature, price=c_price, flavors=c_flavors, closing=c_closing)

def main(folder):
    root = Path(folder)
    cards = json.loads((root / "src/cards.json").read_text())["cards"]
    outs = []
    for i, c in enumerate(cards, 1):
        im = KIND[c["type"]](c, root, i, len(cards)).convert("RGB").resize((1080, 1350), Image.LANCZOS)
        im.save(root / f"{i:02d}.png", optimize=True); outs.append(im)
    cols = 4; rows = math.ceil(len(outs) / cols); tw, th = 300, 375
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (230, 218, 200))
    for i, im in enumerate(outs):
        r, cc = divmod(i, cols); sheet.paste(im.resize((tw, th), Image.LANCZOS), (12 + cc * (tw + 12), 12 + r * (th + 12)))
    sheet.save(root / "preview.jpg", quality=90)
    outs[0].resize((540, 675), Image.LANCZOS).save(root / "cover_preview.jpg", quality=90)
    ph = Image.new("RGB", (len(outs) * 392, 475), (230, 218, 200))
    for i, im in enumerate(outs): ph.paste(im.resize((380, 475), Image.LANCZOS), (i * 392, 0))
    ph.save(root / "phone_check.jpg", quality=88)
    print("ok", len(outs))

if __name__ == "__main__":
    main(sys.argv[1])
