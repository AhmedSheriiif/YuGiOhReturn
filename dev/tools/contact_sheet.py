"""Make labeled contact sheets of images (bmp/png) under a folder."""
import sys, os
from PIL import Image, ImageDraw
src, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8
files = []
for root, _, fs in os.walk(src):
    for f in sorted(fs):
        if f.lower().endswith(('.bmp', '.png', '.jpg')): files.append(os.path.join(root, f))
T = 180
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * T, rows * (T + 28)), (60, 60, 60))
d = ImageDraw.Draw(sheet)
for k, p in enumerate(files):
    im = Image.open(p); w, h = im.size
    im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (60, 60, 60, 255)); bg.alpha_composite(im)
    bg.thumbnail((T - 6, T - 6))
    x, y = (k % cols) * T, (k // cols) * (T + 28)
    sheet.paste(bg.convert('RGB'), (x + 3, y + 3))
    d.text((x + 3, y + T), os.path.relpath(p, src)[-28:], fill=(255, 255, 0))
    d.text((x + 3, y + T + 12), '%dx%d' % (w, h), fill=(200, 200, 200))
sheet.save(out); print(out, len(files), sheet.size)
