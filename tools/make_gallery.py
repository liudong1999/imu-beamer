# Compose gallery/IMU.png from the compiled demo (title, TOC, content pages).
import fitz
from PIL import Image, ImageFilter, ImageDraw

PDF = 'build/pre-imu.pdf'
doc = fitz.open(PDF)


def page_img(i, width):
    pix = doc[i].get_pixmap(dpi=220)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    return im.resize((width, round(width * im.height / im.width)), Image.LANCZOS)


def shadowed(im, pad=22):
    w, h = im.size
    out = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad + 4, pad + 8, pad + w + 4, pad + h + 8], fill=(0, 0, 0, 60))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    out.paste(im, (pad, pad))
    return out


W, H = 2600, 1500
canvas = Image.new('RGB', (W, H), (244, 245, 247))
big = shadowed(page_img(0, 1270))
small = shadowed(page_img(1, 1080))
small2 = shadowed(page_img(3, 1080))
canvas.paste(big, (40, 150), big)
canvas.paste(small, (1370, 90), small)
canvas.paste(small2, (1370, 790), small2)
canvas.save('gallery/IMU.png')
print(canvas.size)
