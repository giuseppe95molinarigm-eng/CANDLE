"""Render PDF pages to thumbnails and tile them into contact sheets for visual review."""
import glob, os, subprocess, sys
from PIL import Image, ImageDraw
pdf, outdir = sys.argv[1], sys.argv[2]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 24
dpi = sys.argv[4] if len(sys.argv) > 4 else '30'
os.makedirs(outdir, exist_ok=True)
for f in glob.glob(os.path.join(outdir, 't-*.png')) + glob.glob(os.path.join(outdir, 'sheet_*.png')):
    os.remove(f)
subprocess.run(['pdftoppm', '-r', dpi, '-png', pdf, os.path.join(outdir, 't')], check=True)
files = sorted(glob.glob(os.path.join(outdir, 't-*.png')), key=lambda f: int(f.rsplit('-', 1)[1][:-4]))
cols = 8
for k in range(0, len(files), per):
    chunk = files[k:k + per]
    ims = [Image.open(f) for f in chunk]
    w, h = ims[0].size
    rows = -(-len(ims) // cols)
    sheet = Image.new('RGB', (cols * (w + 6), rows * (h + 18)), (90, 90, 90))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x, y = (i % cols) * (w + 6), (i // cols) * (h + 18)
        sheet.paste(im, (x, y + 16))
        d.text((x + 2, y + 2), str(k + i + 1), fill=(255, 255, 0))
    sheet.save(os.path.join(outdir, f'sheet_{k // per + 1:02d}.png'))
print(len(files), 'pages')
