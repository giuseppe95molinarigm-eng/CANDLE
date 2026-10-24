"""Derive print copies (max 2200 px wide, JPEG q88, 4:4:4) from images/final.
2200 px keeps >= 300 ppi at the widest placement (7.025 in full-width photo)."""
import glob, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(ROOT, 'work/print_img'); os.makedirs(out, exist_ok=True)
for f in sorted(glob.glob(os.path.join(ROOT, 'images/final/*.jpg'))):
    im = Image.open(f).convert('RGB')
    if im.width > 2200:
        im = im.resize((2200, round(im.height * 2200 / im.width)), Image.LANCZOS)
    im.save(os.path.join(out, os.path.basename(f)), 'JPEG', quality=88, subsampling=0, dpi=(300, 300))
print(len(os.listdir(out)))
