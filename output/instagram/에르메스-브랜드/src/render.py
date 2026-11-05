"""에르메스 브랜드 소개 카드뉴스 렌더러 — 절제된 에디토리얼 테마.
실행: python src/render.py  (주제 폴더에서)
"""
import math
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT.parent / "_shared_fonts"
W, H, K = 1080, 1350, 2

IVORY = (243, 238, 230)
IVORY2 = (234, 227, 216)
CHAR = (42, 37, 32)
CHAR2 = (28, 24, 21)
SUB = (104, 96, 88)
SUB_D = (196, 186, 172)
ORANGE = (217, 102, 31)
WHITE = (255, 255, 255)
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
ACCOUNT = "@trend.zip.kr_"
CREDIT = "이미지 ⓒHermès (hermes.com)"


def k(v):
    return int(round(v * K))


def serif(s, bold=True):
    return ImageFont.truetype(str(FONTS / ("GowunBatang-Bold.ttf" if bold else "GowunBatang-Regular.ttf")), k(s))


def sd(s, w="semi"):
    return ImageFont.truetype(SD, k(s), index={"bold": 6, "semi": 4, "reg": 0, "med": 2}[w])


def tl(d, t, f):
    return d.textlength(t, font=f) / K


def text(d, x, y, t, f, fill, anchor="la", spacing=0):
    if spacing:
        cx = x
        if anchor[0] == "m":
            cx -= (sum(tl(d, c, f) for c in t) + spacing * (len(t) - 1)) / 2
        for c in t:
            d.text((k(cx), k(y)), c, font=f, fill=fill, anchor="l" + anchor[1])
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


def fit(path, w, h, vf=0.5, hf=0.5):
    img = Image.open(ROOT / path).convert("RGB")
    sc = max(k(w) / img.width, k(h) / img.height)
    img = img.resize((max(k(w), round(img.width * sc)), max(k(h), round(img.height * sc))), Image.LANCZOS)
    x = int((img.width - k(w)) * hf)
    y = int((img.height - k(h)) * vf)
    return img.crop((x, y, x + k(w), y + k(h)))


def canvas(bg=IVORY):
    return Image.new("RGB", (k(W), k(H)), bg)


def header(d, n, total, dark=False):
    col = SUB_D if dark else SUB
    text(d, 64, 56, ACCOUNT, sd(26, "semi"), col)
    text(d, W - 64, 56, f"{n} / {total}", sd(26, "semi"), col, anchor="ra")


def kicker(d, x, y, t, dark=False, center=False):
    f = serif(26, bold=True)
    col = ORANGE
    w = sum(tl(d, c, f) for c in t) + 5 * (len(t) - 1)
    x0 = x - w / 2 if center else x
    d.line([(k(x0), k(y + 15)), (k(x0 + 40), k(y + 15))], fill=ORANGE, width=k(2))
    text(d, x0 + 56, y, t, f, WHITE if dark else CHAR, spacing=5)


def credit(d, x, y, t=CREDIT, dark=False, anchor="ra"):
    text(d, x, y, t, serif(24, bold=False), SUB_D if dark else SUB, anchor=anchor)


def gradient_bottom(im, y0, color=CHAR2, alpha=235):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for y in range(k(y0), im.height):
        t = (y - k(y0)) / (im.height - k(y0))
        ld.line([(0, y), (im.width, y)], fill=color + (int(alpha * min(1, t * 1.4)),))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


TOTAL = 6


def p1():
    im = canvas()
    im.paste(fit("assets/official/ecole_t.jpg", W, H, vf=0.35), (0, 0))
    im = gradient_bottom(im, 640)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle((0, 0, im.width, k(110)), fill=(0, 0, 0, 120))
    im = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
    d = ImageDraw.Draw(im)
    header(d, 1, TOTAL, dark=True)
    kicker(d, 72, 900, "HERMÈS · BRAND STORY", dark=True)
    y = 960
    for t in ["에르메스의 시작은", "말안장 공방이었어요"]:
        text(d, 72, y, t, serif(88), WHITE)
        y += 112
    text(d, 74, y + 22, "1837년 파리, 마구 장인 티에리 에르메스의 작업장에서", sd(34, "semi"), SUB_D)
    credit(d, W - 64, H - 54, CREDIT + " · 에콜 에르메스 데 사부아르페르", dark=True)
    return im


def p2():
    im = canvas()
    d = ImageDraw.Draw(im)
    header(d, 2, TOTAL)
    kicker(d, 72, 128, "ORIGIN")
    y = 176
    for t in ["1837년, 파리의", "마구 공방에서"]:
        text(d, 72, y, t, serif(72), CHAR)
        y += 92
    ph_y = 380
    im.paste(fit("assets/official/thierry_t.jpg", 452, 560, vf=0.2), (k(72), k(ph_y)))
    im.paste(fit("assets/official/fbg24_t.jpg", 452, 560, vf=0.4), (k(556), k(ph_y)))
    d = ImageDraw.Draw(im)
    text(d, 72, ph_y + 574, "창업자 티에리 에르메스", sd(26, "semi"), SUB)
    text(d, 556, ph_y + 574, "포부르 생토노레 24번지 매장", sd(26, "semi"), SUB)
    y = 1010
    rows = [("1837", "티에리 에르메스가 파리에 마구 공방을 열어요"),
            ("1867", "파리 만국박람회에서 마구로 상을 받아요"),
            ("1880", "공방을 포부르 생토노레 24번지로 옮기고 매장을 열어요")]
    for yr, t in rows:
        d.line([(k(72), k(y - 14)), (k(W - 72), k(y - 14))], fill=(214, 204, 190), width=k(1))
        text(d, 72, y, yr, serif(40), ORANGE)
        text(d, 196, y + 4, t, sd(34, "semi"), CHAR)
        y += 76
    credit(d, W - 64, H - 54)
    return im


def p3():
    im = canvas(IVORY2)
    im.paste(fit("assets/official/carre_t.jpg", W, 720, vf=0.5), (0, 0))
    d = ImageDraw.Draw(im)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle((0, 0, im.width, k(110)), fill=(0, 0, 0, 130))
    im = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
    d = ImageDraw.Draw(im)
    header(d, 3, TOTAL, dark=True)
    credit(d, W - 64, 734, CREDIT + " · 사진 속 카레는 'Feux d'artifice'")
    kicker(d, 72, 800, "SILK · CARRÉ")
    y = 848
    for t in ["1937년, 첫 실크", "스카프 '카레'"]:
        text(d, 72, y, t, serif(72), CHAR)
        y += 92
    y = para(d, 72, y + 20, "첫 카레는 로베르 뒤마가 디자인한 'Jeu des omnibus et dames blanches'예요.", sd(36, "semi"), CHAR, W - 144, 52)
    para(d, 72, y + 10, "1925년 골프 재킷, 1927년 주얼리, 1928년 시계·샌들에 이어 공방의 영역이 실크까지 넓어졌어요.", sd(34, "reg"), SUB, W - 144, 50)
    return im


def p4():
    im = canvas(CHAR2)
    d = ImageDraw.Draw(im)
    header(d, 4, TOTAL, dark=True)
    kicker(d, 72, 128, "ICONIC BAGS", dark=True)
    y = 176
    for t in ["켈리는 1956년,", "버킨은 1984년"]:
        text(d, 72, y, t, serif(72), WHITE)
        y += 92
    im.paste(fit("assets/official/birkin_t.jpg", 600, 600, vf=0.5), (k(240), k(380)))
    d = ImageDraw.Draw(im)
    text(d, W / 2, 994, "사진: 버킨 백", sd(26, "reg"), SUB_D, anchor="ma")
    cols = [("1956 · 켈리", "1930년대 로베르 뒤마가 디자인했고, 1956년 그레이스 켈리가 든 사진이 실리며 유명해졌어요."),
            ("1984 · 버킨", "장루이 뒤마가 제인 버킨을 위해 디자인한 가방에서 시작했어요.")]
    x = 72
    for i, (h, t) in enumerate(cols):
        cx = 72 + i * 488
        if i:
            d.line([(k(cx - 24), k(1050)), (k(cx - 24), k(1250))], fill=(80, 72, 64), width=k(1))
        text(d, cx, 1050, h, serif(38), ORANGE)
        para(d, cx, 1106, t, sd(32, "semi"), (230, 222, 210), 440, 46)
    credit(d, W - 64, H - 54, dark=True)
    return im


def p5():
    im = canvas()
    im.paste(fit("assets/official/sellier_pantin_t.jpg", W, 660, vf=0.45), (0, 0))
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle((0, 0, im.width, k(110)), fill=(0, 0, 0, 130))
    im = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
    d = ImageDraw.Draw(im)
    header(d, 5, TOTAL, dark=True)
    credit(d, W - 64, 674, CREDIT + " · 팡탱 가죽 공방")
    kicker(d, 72, 730, "SAVOIR-FAIRE")
    y = 778
    for t in ["지금도", "장인의 손으로"]:
        text(d, 72, y, t, serif(72), CHAR)
        y += 92
    stats = [("16", "개 메티에(전문 분야)"), ("63", "곳 생산·교육 거점"), ("24번째", "프랑스 가죽 공방(2025)")]
    cw = (W - 144) / 3
    sy = 1000
    for i, (n, lab) in enumerate(stats):
        cx = 72 + i * cw
        if i:
            d.line([(k(cx - 4), k(sy + 6)), (k(cx - 4), k(sy + 130))], fill=(214, 204, 190), width=k(1))
        text(d, cx + 16 if i else cx, sy, n, serif(60), CHAR if i else ORANGE)
        para(d, cx + 16 if i else cx, sy + 86, lab, sd(30, "semi"), SUB, cw - 30, 40)
    para(d, 72, 1196, "2021년에는 장인을 기르는 학교 '에콜 에르메스 데 사부아르페르'를 세웠어요.", sd(32, "semi"), CHAR, W - 144, 46)
    return im


def p6():
    im = canvas()
    im.paste(fit("assets/official/new_workshop_t.jpg", W, 600, vf=0.55), (0, 0))
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle((0, 0, im.width, k(110)), fill=(0, 0, 0, 120))
    im = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
    d = ImageDraw.Draw(im)
    header(d, 6, TOTAL, dark=True)
    credit(d, W - 64, 614, CREDIT + " · 2025년 새 가죽 공방")
    kicker(d, 72, 668, "TODAY")
    y = 716
    for t in ["6대째 이어지는", "가족 기업"]:
        text(d, 72, y, t, serif(72), CHAR)
        y += 92
    rows = ["2013년부터 6대손 악셀 뒤마가 이끌고 있어요",
            "2006년 서울에 메종 에르메스가 문을 열었어요",
            "지금은 45개국에 약 300개 매장이 있어요"]
    y = 930
    for t in rows:
        d.ellipse((k(76), k(y + 16), k(86), k(y + 26)), fill=ORANGE)
        text(d, 104, y, t, sd(36, "semi"), CHAR)
        y += 62
    d.line([(k(72), k(1140)), (k(W - 72), k(1140))], fill=(214, 204, 190), width=k(1))
    text(d, 72, 1162, "다음 편에서 보고 싶은 에르메스 이야기를 댓글로 남겨 주세요", sd(30, "bold"), CHAR)
    text(d, 72, 1216, "출처: hermes.com 공식 연표·회사 소개 페이지 (2026.11.05 확인)", sd(25, "reg"), SUB)
    text(d, 72, 1254, "트렌드.zip의 브랜드 소개 콘텐츠로, 에르메스와 제휴·후원 관계가 아니에요.", sd(25, "reg"), SUB)
    return im


def main():
    out = []
    for i, fn in enumerate([p1, p2, p3, p4, p5, p6], 1):
        im = fn().resize((W, H), Image.LANCZOS)
        im.save(ROOT / f"{i:02d}.png")
        out.append(im)
    out[0].save(ROOT / "cover_preview.jpg", quality=92)
    a, b = int(W * 0.3), int(H * 0.3)
    sheet = Image.new("RGB", (3 * a + 4 * 12, 2 * b + 3 * 12), (225, 222, 216))
    for i, im in enumerate(out):
        sheet.paste(im.resize((a, b), Image.LANCZOS), (12 + (i % 3) * (a + 12), 12 + (i // 3) * (b + 12)))
    sheet.save(ROOT / "preview.jpg", quality=90)
    # 휴대폰 크기(가로 380px) 확인용
    ph = Image.new("RGB", (6 * 392, 475), (225, 222, 216))
    for i, im in enumerate(out):
        ph.paste(im.resize((380, 475), Image.LANCZOS), (i * 392, 0))
    ph.save(ROOT / "phone_check.jpg", quality=90)
    print("ok")


if __name__ == "__main__":
    main()
