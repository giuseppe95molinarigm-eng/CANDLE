"""Convert approved raw generations into print-ready JPEGs named by recipe code.

images/final/<code>.jpg : sRGB, quality 92, 4:4:4, tagged 300 dpi (effective ppi
in the layout is higher; see report). Also prints a mapping check.
"""
import glob, json, os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'work/raw/nanobananapro')
dst = os.path.join(ROOT, 'images/final')
os.makedirs(dst, exist_ok=True)
book = json.load(open(os.path.join(ROOT, 'build/book.json')))
codes = [it['code'] for s in book['sections'] for it in s['items'] if it.get('type') == 'recipe']
done = 0
for f in sorted(glob.glob(os.path.join(src, '*.png'))):
    code = os.path.splitext(os.path.basename(f))[0]
    if code not in codes:
        print('unknown code', code); continue
    out = os.path.join(dst, code + '.jpg')
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(f):
        continue
    Image.open(f).convert('RGB').save(out, 'JPEG', quality=92, subsampling=0, dpi=(300, 300))
    done += 1
have = {os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(dst, '*.jpg'))}
print('converted', done, '| final images', len(have), '| missing', [c for c in codes if c not in have][:200] if len(have) < 150 else 'none',
      '| extra', sorted(have - set(codes)))
