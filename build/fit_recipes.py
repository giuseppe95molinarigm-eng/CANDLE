"""Choose the largest photo variant (l > m > s) that keeps each recipe on one page.

Writes build/variants.json. Recipes that do not fit even with 's' keep 's'
and run onto a second page with a 'continued' header.
"""
import json, logging, os, sys
import weasyprint
sys.path.insert(0, os.path.dirname(__file__))
import render_print as R

logging.getLogger('weasyprint').setLevel(logging.ERROR)
ROOT = R.ROOT
book = json.load(open(os.path.join(ROOT, 'build/book.json')))
recipes = [it for s in book['sections'] for it in s['items'] if it.get('type') == 'recipe']
out_dir = os.path.join(ROOT, 'work/fit')
os.makedirs(out_dir, exist_ok=True)
images = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'images/final')
placeholder = os.path.join(ROOT, 'images/final/001_classic_sea_salt_butter_candle.jpg')


def pages_per_recipe(variant):
    ctx = R.Ctx(images, out_dir)
    ctx.placeholder = os.path.relpath(placeholder, out_dir)
    ctx.variant = variant
    html = R.render(book, ctx, {'opener': 'Chapter 1: Butter Candle Classics', 'recipes': [r['num'] for r in recipes]})
    path = os.path.join(out_dir, 'fit.html')
    open(path, 'w').write(html)
    doc = weasyprint.HTML(path).render()
    res = {}
    for p in doc.pages:
        for a in p.anchors:
            if a.startswith('recipe-'):
                res[int(a[7:])] = res.get(int(a[7:]), 0) + 1
    return res


variant = {r['num']: 'l' for r in recipes}
for v in ('l', 'm', 's'):
    for n in [n for n in variant if variant[n] == v]:
        pass
    res = pages_per_recipe(variant)
    over = [n for n, c in res.items() if c > 1 and variant[n] == v]
    print(v, 'one-page:', sum(1 for c in res.values() if c == 1), 'overflow at this size:', len(over))
    if v == 's':
        break
    nxt = {'l': 'm', 'm': 's'}[v]
    for n in over:
        variant[n] = nxt
for n, c in pages_per_recipe(variant).items():
    if c > 1:
        variant[n] = '2p'
res = pages_per_recipe(variant)
print('final one-page', sum(1 for c in res.values() if c == 1), 'two-page', [n for n, c in res.items() if c > 1])
from collections import Counter
print(Counter(variant.values()))
json.dump({str(k): v for k, v in sorted(variant.items())}, open(os.path.join(ROOT, 'build/variants.json'), 'w'), indent=0)
