"""명품 뷰티 카드뉴스 3종 공용 렌더러 — 절제된 에디토리얼 테마.
사용: python render_lux.py <주제 폴더> ...   (폴더 안 src/cards.json의 theme 사용)
공통: 계정명·쪽수 위치, 영문 키커 + 오렌지/브랜드색 선, 명조 제목(고운바탕) + 고딕 본문, 사진 테두리·그림자 없음.
"""
import json
import pathlib
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

FONTS = pathlib.Path(__file__).resolve().parent.parent / "_shared_fonts"
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
W, H, K = 1080, 1350, 2
ACCOUNT = "@trend.zip.kr_"

THEMES = {
    # 샤넬: 흑백 모노크롬 + 앰버(N°5 향수색) 포인트
    "chanel": dict(bg=(246, 244, 240), ink=(18, 18, 18), sub=(96, 92, 86), line=(206, 200, 190), accent=(176, 128, 52),
                   dark=(14, 14, 14), dark_ink=(242, 238, 230), dark_sub=(170, 164, 154)),
    # 에르메스 뷰티: 아이보리 + 에르메스 오렌지
    "hermes": dict(bg=(244, 240, 233), ink=(40, 35, 30), sub=(104, 96, 88), line=(214, 204, 190), accent=(217, 102, 31),
                   dark=(32, 28, 24), dark_ink=(244, 238, 228), dark_sub=(190, 180, 166)),
    # 설화수: 따뜻한 아이보리 + 설화수 오렌지
    "sulwhasoo": dict(bg=(246, 240, 230), ink=(52, 36, 26), sub=(112, 96, 84), line=(220, 204, 184), accent=(214, 92, 30),
                      dark=(58, 30, 16), dark_ink=(250, 240, 228), dark_sub=(214, 190, 168)),
}


def k(v):
    return int(round(v * K))


def serif(s, bold=True):
    return ImageFont.truetype(str(FONTS / ("GowunBatang-Bold.ttf" if bold else "GowunBatang-Regular.ttf")), k(s))


def sd(s, w="semi"):
    return ImageFont.truetype(SD, k(s), index={"bold": 6, "semi": 4, "reg": 0}[w])


def tl(d, t, f):
    return d.textlength(t, font=f) / K


def text(d, x, y, t, f, fill, anchor="la", spacing=0):
    if spacing:
        cx = x
        for c in t:
            d.text((k(cx), k(y)), c, font=f, fill=fill, anchor=anchor)
            cx += tl(d, c, f) + spacing
        return
    d.text((k(x), k(y)), t, font=f, fill=fill, anchor=anchor)


def wrap(d, t, f, maxw):
    out, cur = [], ""
    for w in t.split(" "):
        s = (cur + " " + w).strip()
        if tl(d, s, f) > maxw and cur:
            out.append(cur)
            cur = w
        else:
            cur = s
    out.append(cur)
    return out


def para(d, x, y, t, f, fill, maxw, lh):
    for ln in wrap(d, t, f, maxw):
        d.text((k(x), k(y)), ln, font=f, fill=fill)
        y += lh
    return y


def load(root, ph):
    img = Image.open(root / ph["file"]).convert("RGB")
    if ph.get("crop"):
        img = img.crop(tuple(ph["crop"]))
    if ph.get("trim"):
        bg = Image.new("RGB", img.size, img.getpixel((2, 2)))
        bb = ImageChops.difference(img, bg).convert("L").point(lambda v: 255 if v > 14 else 0).getbbox()
        if bb:
            img = img.crop(bb)
    return img


def fit(img, w, h, vf=0.5, hf=0.5, zoom=1.0):
    sc = max(k(w) / img.width, k(h) / img.height) * zoom
    img = img.resize((max(k(w), round(img.width * sc)), max(k(h), round(img.height * sc))), Image.LANCZOS)
    x = int((img.width - k(w)) * hf)
    y = int((img.height - k(h)) * vf)
    return img.crop((x, y, x + k(w), y + k(h)))


def place(im, root, ph, x, y, w, h):
    img = fit(load(root, ph), w, h, ph.get("v", 0.5), ph.get("hf", 0.5), ph.get("zoom", 1.0))
    im.paste(img, (k(x), k(y)))


def header_band(im, alpha=120):
    """위쪽만 살짝 어둡게(계정명 가독성). 평평한 회색 띠 대신 그라데이션."""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    hh = k(150)
    for y in range(hh):
        ld.line([(0, y), (im.width, y)], fill=(0, 0, 0, int(alpha * (1 - y / hh) ** 1.6)))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


def bottom_fade(im, y0, color, alpha=240):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for y in range(k(y0), im.height):
        t = (y - k(y0)) / (im.height - k(y0))
        ld.line([(0, y), (im.width, y)], fill=color + (int(alpha * min(1, t * 1.5)),))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


def header(d, T, n, total, dark):
    col = T["dark_sub"] if dark else T["sub"]
    text(d, 64, 56, ACCOUNT, sd(26, "semi"), col)
    text(d, W - 64, 56, f"{n} / {total}", sd(26, "semi"), col, anchor="ra")


def kicker(d, T, x, y, t, dark):
    d.line([(k(x), k(y + 15)), (k(x + 40), k(y + 15))], fill=T["accent"], width=k(2))
    text(d, x + 56, y, t, serif(26), T["dark_ink"] if dark else T["ink"], spacing=5)


def credit(d, T, s, x, y, dark, anchor="ra"):
    text(d, x, y, s, serif(24, bold=False), T["dark_sub"] if dark else T["sub"], anchor=anchor)


def titles(d, T, lines, x, y, size, dark, accent_last=False):
    for i, ln in enumerate(lines):
        col = T["dark_ink"] if dark else T["ink"]
        text(d, x, y, ln, serif(size), col)
        y += int(size * 1.26)
    return y


# ---------------- 카드 ----------------
def c_cover(T, data, c, n, total, root):
    im = Image.new("RGB", (k(W), k(H)), T["bg"])
    place(im, root, c["photo"], 0, 0, W, H)
    im = bottom_fade(im, c.get("fade", 640), T["dark"])
    im = header_band(im, 110)
    d = ImageDraw.Draw(im)
    header(d, T, n, total, True)
    kicker(d, T, 72, 880, c["kicker"], True)
    y = titles(d, T, c["title"], 72, 936, 88, True)
    text(d, 74, y + 18, c["sub"], sd(34, "semi"), T["dark_sub"])
    credit(d, T, data["credit"], W - 64, H - 54, True)
    return im


def c_split(T, data, c, n, total, root):
    dark = c.get("dark", False)
    im = Image.new("RGB", (k(W), k(H)), T["dark"] if dark else T["bg"])
    ph_h = c.get("photo_h", 640)
    place(im, root, c["photo"], 0, 0, W, ph_h)
    im = header_band(im, 120)
    d = ImageDraw.Draw(im)
    header(d, T, n, total, True)
    credit(d, T, c.get("credit", data["credit"]), W - 64, ph_h + 14, dark)
    y = ph_h + 66
    kicker(d, T, 72, y, c["kicker"], dark)
    y = titles(d, T, c["title"], 72, y + 46, 70, dark)
    ink = T["dark_ink"] if dark else T["ink"]
    sub = T["dark_sub"] if dark else T["sub"]
    y += 14
    if c.get("text"):
        y = para(d, 72, y, c["text"], sd(36, "semi"), ink, W - 144, 52) + 8
    for row in c.get("rows", []):
        lab, val = row
        d.line([(k(72), k(y)), (k(W - 72), k(y))], fill=(80, 72, 64) if dark else T["line"], width=k(1))
        text(d, 72, y + 16, lab, serif(34), T["accent"])
        para(d, 240, y + 18, val, sd(32, "semi"), ink, W - 240 - 72, 44)
        y += 76 if tl(d, val, sd(32, "semi")) < W - 312 else 120
    if c.get("note"):
        para(d, 72, max(y + 10, H - 120 - 34 * (1 + len(c["note"]) // 52)), c["note"], sd(26, "reg"), sub, W - 144, 36)
    return im


def c_stats(T, data, c, n, total, root):
    dark = c.get("dark", False)
    im = Image.new("RGB", (k(W), k(H)), T["dark"] if dark else T["bg"])
    ph_h = c.get("photo_h", 560)
    place(im, root, c["photo"], 0, 0, W, ph_h)
    im = header_band(im, 120)
    d = ImageDraw.Draw(im)
    header(d, T, n, total, True)
    credit(d, T, c.get("credit", data["credit"]), W - 64, ph_h + 14, dark)
    ink = T["dark_ink"] if dark else T["ink"]
    sub = T["dark_sub"] if dark else T["sub"]
    y = ph_h + 66
    kicker(d, T, 72, y, c["kicker"], dark)
    y = titles(d, T, c["title"], 72, y + 46, 66, dark)
    stats = c["stats"]
    cols = min(len(stats), 4) if len(stats) != 4 else 2
    cols = c.get("cols", cols)
    cw = (W - 144) / cols
    rows = (len(stats) + cols - 1) // cols
    sy = y + 24
    for i, (num, lab) in enumerate(stats):
        r, ci = divmod(i, cols)
        x = 72 + ci * cw
        yy = sy + r * 150
        if ci:
            d.line([(k(x), k(yy + 6)), (k(x), k(yy + 118))], fill=(80, 72, 64) if dark else T["line"], width=k(1))
        tx = x + (20 if ci else 0)
        text(d, tx, yy, num, serif(56), T["accent"] if i == 0 else ink)
        para(d, tx, yy + 78, lab, sd(28, "semi"), sub, cw - 34, 36)
    para(d, 72, H - 64 - 36 * len(wrap(d, c["note"], sd(25, "reg"), W - 144)), c["note"], sd(25, "reg"), sub, W - 144, 36)
    return im


def c_price(T, data, c, n, total, root):
    im = Image.new("RGB", (k(W), k(H)), T["bg"])
    ph_h = c.get("photo_h", 560)
    place(im, root, c["photo"], 0, 0, W, ph_h)
    im = header_band(im, 120)
    d = ImageDraw.Draw(im)
    header(d, T, n, total, True)
    credit(d, T, c.get("credit", data["credit"]), W - 64, ph_h + 14, False)
    y = ph_h + 66
    kicker(d, T, 72, y, c["kicker"], False)
    y = titles(d, T, c["title"], 72, y + 46, 66, False) + 10
    for lab, val, extra in c["rows"]:
        d.line([(k(72), k(y)), (k(W - 72), k(y))], fill=T["line"], width=k(1))
        text(d, 72, y + 20, lab, sd(32, "semi"), T["ink"])
        if extra:
            text(d, 72, y + 64, extra, sd(26, "reg"), T["sub"])
        text(d, W - 72, y + 14, val, serif(52), T["ink"], anchor="ra")
        y += 116
    d.line([(k(72), k(y)), (k(W - 72), k(y))], fill=T["line"], width=k(1))
    y += 26
    for ln in c.get("notes", []):
        y = para(d, 72, y, ln, sd(27, "reg"), T["sub"], W - 144, 38) + 4
    text(d, 72, H - 96, c["cta"], sd(30, "bold"), T["ink"])
    text(d, 72, H - 54, c["source"], sd(23, "reg"), T["sub"])
    return im


RENDER = {"cover": c_cover, "split": c_split, "stats": c_stats, "price": c_price}


def main(folder):
    root = pathlib.Path(folder).resolve()
    data = json.loads((root / "src/cards.json").read_text())
    T = THEMES[data["theme"]]
    out = []
    cards = data["cards"]
    for i, c in enumerate(cards, 1):
        im = RENDER[c["type"]](T, data, c, i, len(cards), root).resize((W, H), Image.LANCZOS)
        im.save(root / f"{i:02d}.png")
        out.append(im)
    out[0].save(root / "cover_preview.jpg", quality=92)
    a, b = int(W * 0.3), int(H * 0.3)
    sheet = Image.new("RGB", (len(out) * (a + 12) + 12, b + 24), (225, 222, 216))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (12 + i * (a + 12), 12))
    sheet.save(root / "preview.jpg", quality=90)
    ph = Image.new("RGB", (len(out) * 392, 475), (225, 222, 216))
    for i, im in enumerate(out):
        ph.paste(im.resize((380, 475), Image.LANCZOS), (i * 392, 0))
    ph.save(root / "phone_check.jpg", quality=90)
    print("ok", root.name, len(out))


if __name__ == "__main__":
    for f in sys.argv[1:]:
        main(f)
