"""生成 EraPuller 品牌图标（icon.ico + logo.png）"""

from PIL import Image, ImageDraw

CYAN = (0, 229, 255, 255)
MID1 = (60, 160, 255, 255)
MID2 = (80, 130, 255, 255)
VIOLET = (124, 77, 255, 255)
WHITE = (255, 255, 255, 255)


def make_logo(size: int) -> Image.Image:
    s = float(size)
    r = int(s * 0.24)

    # 对角渐变（2x2 双线性放大）
    tiny = Image.new("RGBA", (2, 2))
    t = tiny.load()
    t[0, 0] = CYAN
    t[1, 0] = MID1
    t[0, 1] = MID2
    t[1, 1] = VIOLET
    grad = tiny.resize((size, size), Image.Resampling.BILINEAR)

    # 圆角遮罩
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img = Image.composite(grad, img, mask)

    # 顶部高光（正常混合，不覆盖主体）
    hi = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    top_h = int(s * 0.55)
    for y in range(top_h):
        a = int(85 * (1 - y / top_h))
        hd.line([(0, y), (size, y)], fill=(255, 255, 255, a))
    img = Image.alpha_composite(img, hi)

    # 下载箭头
    lw = max(2, int(s * 0.055))
    arrow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arrow)
    cx = size / 2
    ad.line([(cx, s * 0.26), (cx, s * 0.60)], fill=WHITE, width=lw)
    ad.line([(cx - s * 0.14, s * 0.46), (cx, s * 0.60)], fill=WHITE, width=lw)
    ad.line([(cx + s * 0.14, s * 0.46), (cx, s * 0.60)], fill=WHITE, width=lw)
    ad.line([(s * 0.26, s * 0.72), (s * 0.74, s * 0.72)], fill=WHITE, width=lw)
    img = Image.alpha_composite(img, arrow)
    return img


if __name__ == "__main__":
    base = make_logo(512)
    base.save("logo.png")
    base.save(
        "icon.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("icon.ico + logo.png generated")
