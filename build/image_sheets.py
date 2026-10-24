"""Tile generated images with their codes for visual QA."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
end = int(sys.argv[4]) if len(sys.argv) > 4 else 150
files = sorted(f for f in glob.glob(os.path.join(src, '*.*')) if start <= int(os.path.basename(f)[:3]) <= end)
W, H, cols = 520, 390, 4
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
rows = -(-len(files) // cols)
sheet = Image.new('RGB', (cols * (W + 8), rows * (H + 30)), 'white')
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB')
    im.thumbnail((W, H))
    x, y = (i % cols) * (W + 8), (i // cols) * (H + 30)
    sheet.paste(im, (x, y + 28))
    d.text((x + 2, y + 4), os.path.basename(f)[:46], fill='black', font=font)
sheet.save(out, quality=85)
print(len(files))
