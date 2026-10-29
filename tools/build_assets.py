# Generate IMU assets for college-beamer.
# inputs: source/emblem.png (IMU emblem, blue ink on transparency),
#         source/lineart.png (IMU website line-art motif, opaque light lines)
# outputs: src/IMU/color-logo.png, trans-logo.png, background.png
import numpy as np
from PIL import Image, ImageDraw

MAIN = (0, 93, 140)                  # IMU blue, sampled from the emblem
CARD_W, CARD_H = 906, 1134           # size recommended by the repository guide
EMB_D, EMB_X, EMB_Y = 631, 137, 403  # circle geometry copied from src/OUC

# the emblem file is "blue ink on transparency", so its alpha channel is the
# ink mask: taking it over the main colour gives the white-on-blue knockout
emblem = Image.open('tools/source/emblem.png').convert('RGBA')
emblem = emblem.resize((EMB_D, EMB_D), Image.LANCZOS)
ink_mask = np.array(emblem)[..., 3]
white = np.zeros((EMB_D, EMB_D, 4), dtype=np.uint8)
white[..., :3] = 255
white[..., 3] = ink_mask
white = Image.fromarray(white)


def make_card(bg_rgba):
    canvas = Image.new('RGBA', (CARD_W, CARD_H), bg_rgba)
    canvas.alpha_composite(white, (EMB_X, EMB_Y))
    return canvas


make_card(MAIN + (255,)).convert('RGB').save('src/IMU/color-logo.png', optimize=True)
make_card((0, 0, 0, 0)).save('src/IMU/trans-logo.png', optimize=True)
print('logos done')

# title background: white page with the site line art on the right
W, H, ALPHA = 2560, 1440, 0.16
bg = np.full((H, W, 3), 255, dtype=np.uint8)
over = np.array(MAIN, dtype=np.float32)

lines = Image.open('tools/source/lineart.png').convert('RGBA')
lines = lines.resize((int(lines.width * H / lines.height), H), Image.LANCZOS)
la = np.array(lines)
alpha = (la[..., 3] / 255.0 * ALPHA)[..., None]
x0 = W - la.shape[1] - 60
reg = bg[:, x0:x0 + la.shape[1]].astype(np.float32)
bg[:, x0:x0 + la.shape[1]] = (over * alpha + reg * (1 - alpha)).astype(np.uint8)

# faint emblem ornament cropped into the lower-left corner of the title page
box, wx, wy, W_ALPHA = 660, -190, H - 170, 0.06
wm = np.array(Image.fromarray(ink_mask).convert('L').resize((box, box), Image.LANCZOS))
wa = (wm / 255.0 * W_ALPHA).astype(np.float32)[..., None]
y0, y1 = max(wy, 0), min(wy + box, H)
x0, x1 = max(wx, 0), min(wx + box, W)
sub = wa[y0 - wy:y1 - wy, x0 - wx:x1 - wx]
reg = bg[y0:y1, x0:x1].astype(np.float32)
bg[y0:y1, x0:x1] = (over * sub + reg * (1 - sub)).astype(np.uint8)

Image.fromarray(bg).save('src/IMU/background.png', optimize=True)
print('motif background done')

# title background, photo version: the main building duotoned to IMU blue,
# high key, with a white gradient on the left so the title block stays legible
KEY, FADE0, FADE1 = 0.32, 0.30, 0.65
photo = Image.open('tools/source/main-building.jpg').convert('RGB')
tw, th = photo.width, min(photo.height, round(photo.width * 9 / 16))
if th < round(tw * 9 / 16):
    tw = round(th * 16 / 9)
photo = photo.crop((photo.width - tw, 0, photo.width, th)).resize((W, H), Image.LANCZOS)
a = np.array(photo, dtype=np.float32)
lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0
t = np.clip((lum - 0.05) / 0.95, 0, 1)[..., None]
out = 255 * (1 - t) + MAIN * t
out = out * (1 - KEY) + 255 * KEY
gx = np.linspace(0, 1, W, dtype=np.float32)
fade = np.clip((gx - FADE0) / (FADE1 - FADE0), 0, 1)[None, :, None]
out = out * fade + 255 * (1 - fade)
# the picture is a smooth duotone, so a 24-colour palette is visually lossless
# here and cuts the file from ~2 MB to ~0.6 MB
bgimg = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
bgimg.quantize(colors=24, method=Image.MEDIANCUT, dither=Image.NONE).save(
    'src/IMU/background-photo.png', optimize=True)
print('photo background done')

# title background, drawing version: the main building reduced to an
# abstract line elevation - silhouette, dome contours, slab floor bands and
# the emblem roundel; no sky, no clouds, no window detail.
from scipy import ndimage

LINE_W, LINE_COL, LINE_ALPHA = 1450, 0, 0.62
crop = Image.open('tools/source/main-building.jpg').convert('RGB').crop((880, 0, 1920, 620))
px = crop.resize((1600, round(1600 * crop.height / crop.width)), Image.LANCZOS)
pa = np.array(px, dtype=np.float32)
pr, pb = pa[..., 0], pa[..., 2]
mass = (pr - pb) > 12                      # brick is red-dominant, sky is blue
mass = ndimage.binary_fill_holes(
    ndimage.binary_closing(ndimage.binary_opening(mass, np.ones((7, 7))), np.ones((21, 21))))
lbl, n = ndimage.label(mass)
sizes = ndimage.sum(mass, lbl, range(1, n + 1))
mass = np.isin(lbl, np.where(sizes > 20000)[0] + 1)
mass = ndimage.binary_fill_holes(
    ndimage.binary_closing(ndimage.binary_opening(mass, np.ones((9, 9))), np.ones((15, 15))))

draw = Image.new('L', (mass.shape[1], mass.shape[0]), 255)
dd = ImageDraw.Draw(draw)
outline = mass ^ ndimage.binary_erosion(mass, np.ones((4, 4)))
draw.paste(0, (0, 0), Image.fromarray((outline * 255).astype(np.uint8)))

width = mass.sum(axis=1)
slab = np.where(width > 0.75 * width.max())[0]
y0, y1 = int(slab.min()), int(slab.max())
for i in range(3, 11):
    y = int(y0 + (y1 - y0) * i / 11)
    xs = np.where(mass[y])[0]
    if xs.size:
        dd.line([(int(xs[0]) + 10, y), (int(xs[-1]) - 10, y)], fill=0, width=5)

dome = mass.copy()
dome[y0:, :] = False
for k, wd in ((12, 5), (30, 4)):
    er = ndimage.binary_erosion(dome, np.ones((3, 3)), iterations=k)
    ring = (er ^ ndimage.binary_erosion(er, np.ones((3, 3)))) & dome
    draw.paste(0, (0, 0), Image.fromarray(ring.astype(np.uint8) * 255))

lum = 0.299 * pr + 0.587 * pa[..., 1] + 0.114 * pb
tower = np.zeros_like(mass)
tower[:int(mass.shape[0] * 0.55), int(mass.shape[1] * 0.35):int(mass.shape[1] * 0.65)] = True
dark = (lum < 95) & tower
lbl, n = ndimage.label(ndimage.binary_closing(dark, np.ones((9, 9))))
if n:
    sizes = ndimage.sum(dark, lbl, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    cy, cx = ndimage.center_of_mass(lbl == k)
    r0 = np.sqrt(sizes[k - 1] / np.pi)
    rr, wd = r0 * 1.1, 5
    dd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=0, width=wd)

art = draw.resize((LINE_W, round(LINE_W * draw.height / draw.width)), Image.LANCZOS)
aa = np.array(art, dtype=np.float32) / 255.0                      # 0 = line
alpha = (1.0 - aa) * LINE_ALPHA
ramp = np.clip(np.linspace(0, 1, art.width) / 0.24, 0, 1)[None, :]  # fade the left edge
alpha = alpha * ramp
ax0, ay0 = W - art.width - 40, H - art.height + 150
canvas = np.full((H, W, 3), 255, dtype=np.float32)
sy0, sy1 = max(0, -ay0), min(art.height, H - ay0)
sx0, sx1 = max(0, -ax0), min(art.width, W - ax0)
dy0, dx0 = ay0 + sy0, ax0 + sx0
a_sub = alpha[sy0:sy1, sx0:sx1, None]
sub = canvas[dy0:dy0 + a_sub.shape[0], dx0:dx0 + a_sub.shape[1]]
canvas[dy0:dy0 + a_sub.shape[0], dx0:dx0 + a_sub.shape[1]] = (
    sub * (1 - a_sub) + np.array(LINE_COL, dtype=np.float32) * a_sub)
Image.fromarray(canvas.astype(np.uint8)).save('src/IMU/background-lines.png', optimize=True)
print('drawing background done')
