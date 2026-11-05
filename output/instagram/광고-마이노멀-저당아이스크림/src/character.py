"""오리지널 아이스크림 캐릭터 '스쿱이' (와플콘 위 한 스쿱). Pillow로 직접 그림."""
from PIL import Image, ImageDraw, ImageFilter
import math

INK = (74, 52, 38)
FLAVORS = {
    "vanilla": ((250, 240, 214), (234, 214, 176)),
    "choco": ((140, 92, 66), (112, 70, 48)),
    "greentea": ((170, 196, 120), (140, 168, 92)),
    "strawberry": ((246, 184, 178), (226, 150, 146)),
}

def _dilate(m, r):
    """큰 반경 팽창: 블러 후 임계값(MaxFilter보다 훨씬 빠름)."""
    return m.filter(ImageFilter.GaussianBlur(r * 0.6)).point(lambda v: 255 if v > 8 else 0).filter(ImageFilter.GaussianBlur(1.2))

def _mask_scoop(S):
    m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m)
    cx, cy, r = S * 0.5, S * 0.40, S * 0.30
    d.ellipse([cx - r, cy - r * 0.92, cx + r, cy + r * 0.92], fill=255)
    # 아래쪽 흘러내리는 방울
    for i, (dx, rr, dy) in enumerate([(-0.27, 0.075, 0.24), (-0.13, 0.085, 0.27), (0.02, 0.08, 0.25), (0.16, 0.09, 0.28), (0.28, 0.065, 0.22)]):
        d.ellipse([cx + dx * S - rr * S, cy + dy * S - rr * S, cx + dx * S + rr * S, cy + dy * S + rr * S], fill=255)
    d.rounded_rectangle([cx - r * 0.98, cy, cx + r * 0.98, cy + S * 0.24], radius=int(S * 0.06), fill=255)
    return m

def _mask_cone(S):
    m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m)
    cx = S * 0.5
    d.polygon([(cx - S * 0.25, S * 0.60), (cx + S * 0.25, S * 0.60), (cx, S * 0.97)], fill=255)
    return m

def draw(size=400, flavor="vanilla", eyes="open", arms="wave", tilt=0, outline=True):
    S = size * 2
    base, shade = FLAVORS[flavor]
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cone, scoop = _mask_cone(S), _mask_scoop(S)
    allm = Image.composite(Image.new("L", (S, S), 255), cone, scoop)
    lw = int(S * 0.018)
    # 스티커 테두리(흰색) + 잉크 외곽선
    if outline:
        white = _dilate(allm, lw * 2)
        im.paste((255, 251, 244, 255), (0, 0), white)
        ink = _dilate(allm, lw)
        im.paste(INK + (255,), (0, 0), ink)
    # 콘
    cl = Image.new("RGBA", (S, S), (226, 172, 110, 255))
    cd = ImageDraw.Draw(cl)
    for i in range(-8, 9):
        x = S * 0.5 + i * S * 0.06
        cd.line([(x, S * 0.55), (x + S * 0.5, S * 1.05)], fill=(196, 138, 80, 255), width=int(S * 0.008))
        cd.line([(x, S * 0.55), (x - S * 0.5, S * 1.05)], fill=(196, 138, 80, 255), width=int(S * 0.008))
    im.paste(cl, (0, 0), cone)
    # 스쿱
    sl = Image.new("RGBA", (S, S), base + (255,))
    sd = ImageDraw.Draw(sl)
    sd.ellipse([S * 0.18, S * 0.42, S * 0.95, S * 0.75], fill=shade + (255,))
    sl = sl.filter(ImageFilter.GaussianBlur(S * 0.03))
    shine = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shine).ellipse([S * 0.30, S * 0.18, S * 0.38, S * 0.24], fill=(255, 255, 255, 120))
    sl.alpha_composite(shine.filter(ImageFilter.GaussianBlur(S * 0.01)))
    # 스프링클
    sp = ImageDraw.Draw(sl)
    for (x, y, a, c) in [(0.58, 0.20, 30, (240, 140, 140)), (0.66, 0.30, -40, (130, 190, 200)), (0.36, 0.33, 60, (250, 200, 90)), (0.70, 0.17, 80, (250, 200, 90)), (0.47, 0.15, -20, (130, 190, 200))]:
        L = S * 0.03; ang = math.radians(a)
        sp.line([(S * x - L * math.cos(ang), S * y - L * math.sin(ang)), (S * x + L * math.cos(ang), S * y + L * math.sin(ang))], fill=c + (255,), width=int(S * 0.016))
    im.paste(sl, (0, 0), scoop)
    d = ImageDraw.Draw(im)
    # 얼굴
    ey, ex1, ex2 = S * 0.43, S * 0.40, S * 0.60
    ew, eh = S * 0.035, S * 0.05
    face = INK if flavor != "choco" else (52, 32, 22)
    if eyes == "happy":
        for ex in (ex1, ex2):
            d.arc([ex - ew * 1.3, ey - eh * 0.6, ex + ew * 1.3, ey + eh * 1.2], 200, 340, fill=face, width=int(S * 0.016))
    elif eyes == "wink":
        d.ellipse([ex1 - ew, ey - eh, ex1 + ew, ey + eh], fill=face)
        d.ellipse([ex1 - ew * 0.2, ey - eh * 0.7, ex1 + ew * 0.5, ey - eh * 0.1], fill=(255, 255, 255))
        d.arc([ex2 - ew * 1.3, ey - eh * 0.6, ex2 + ew * 1.3, ey + eh * 1.2], 200, 340, fill=face, width=int(S * 0.016))
    else:
        for ex in (ex1, ex2):
            d.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=face)
            d.ellipse([ex - ew * 0.2, ey - eh * 0.7, ex + ew * 0.5, ey - eh * 0.1], fill=(255, 255, 255))
    # 볼터치
    for bx in (S * 0.33, S * 0.67):
        d.ellipse([bx - S * 0.04, S * 0.495, bx + S * 0.04, S * 0.53], fill=(242, 140, 130, 200))
    # 입
    d.arc([S * 0.46, S * 0.46, S * 0.54, S * 0.52], 10, 170, fill=face, width=int(S * 0.012))
    # 팔
    aw = int(S * 0.02)
    if arms == "wave":
        d.line([(S * 0.21, S * 0.50), (S * 0.12, S * 0.40), (S * 0.10, S * 0.31)], fill=INK, width=aw, joint="curve")
        d.line([(S * 0.79, S * 0.52), (S * 0.89, S * 0.58)], fill=INK, width=aw)
    elif arms == "up":
        d.line([(S * 0.21, S * 0.50), (S * 0.10, S * 0.36)], fill=INK, width=aw)
        d.line([(S * 0.79, S * 0.50), (S * 0.90, S * 0.36)], fill=INK, width=aw)
    else:
        d.line([(S * 0.21, S * 0.52), (S * 0.11, S * 0.58)], fill=INK, width=aw)
        d.line([(S * 0.79, S * 0.52), (S * 0.89, S * 0.58)], fill=INK, width=aw)
    for (x, y) in ([(S * 0.10, S * 0.31), (S * 0.89, S * 0.58)] if arms == "wave" else [(S * 0.10, S * 0.36), (S * 0.90, S * 0.36)] if arms == "up" else [(S * 0.11, S * 0.58), (S * 0.89, S * 0.58)]):
        d.ellipse([x - aw * 1.3, y - aw * 1.3, x + aw * 1.3, y + aw * 1.3], fill=INK)
    if tilt:
        im = im.rotate(tilt, resample=Image.BICUBIC, expand=False)
    return im.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    import sys
    sheet = Image.new("RGBA", (1600, 420), (244, 234, 219, 255))
    for i, (f, e, a) in enumerate([("vanilla", "open", "wave"), ("choco", "happy", "up"), ("greentea", "wink", "down"), ("strawberry", "open", "up")]):
        sheet.alpha_composite(draw(400, f, e, a, tilt=(-6, 5, -3, 6)[i]), (i * 400, 10))
    sheet.convert("RGB").save(sys.argv[1])
