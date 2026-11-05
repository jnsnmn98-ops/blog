"""제네시스 G90 카드 렌더러: _lux3_kit/render_lux.py를 불러 'genesis' 테마와 다크 표지(cover_band)를 더함."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / "Desktop/blog/output/instagram/_lux3_kit"))
import render_lux as L
from PIL import Image, ImageDraw

# 웜 그레이 + 차콜, 포인트는 코퍼(구릿빛) 한 색
L.THEMES["genesis"] = dict(bg=(243, 241, 237), ink=(22, 23, 26), sub=(98, 98, 102), line=(210, 206, 200),
                           accent=(168, 118, 80), dark=(17, 18, 21), dark_ink=(242, 240, 236), dark_sub=(158, 158, 162))


def c_cover_band(T, data, c, n, total, root):
    W, H, k = L.W, L.H, L.k
    im = Image.new("RGB", (k(W), k(H)), T["dark"])
    top, ph_h = c.get("top", 0), c.get("photo_h", 860)
    L.place(im, root, c["photo"], 0, top, W, ph_h)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    y0, y1 = k(top + ph_h - 300), k(top + ph_h)
    for y in range(y0, y1):
        ld.line([(0, y), (im.width, y)], fill=T["dark"] + (int(255 * ((y - y0) / (y1 - y0)) ** 1.3),))
    im = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
    im = L.header_band(im, 110)
    d = ImageDraw.Draw(im)
    L.header(d, T, n, total, True)
    y = c.get("text_y", 880)
    L.kicker(d, T, 72, y, c["kicker"], True)
    y = L.titles(d, T, c["title"], 72, y + 52, 88, True)
    L.text(d, 74, y + 16, c["sub"], L.sd(34, "semi"), T["dark_sub"])
    L.credit(d, T, data["credit"], W - 64, H - 54, True)
    return im


L.RENDER["cover_band"] = c_cover_band

if __name__ == "__main__":
    L.main(sys.argv[1])
