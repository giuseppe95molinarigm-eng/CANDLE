"""Layout QA on the WeasyPrint render: overflow beyond the live area, headings
stranded at the bottom of a page, missing/duplicate images, recipes/page map."""
import json, logging, os, sys, collections
import weasyprint
logging.getLogger('weasyprint').setLevel(logging.ERROR)
html = sys.argv[1]
doc = weasyprint.HTML(html).render()
issues = []
img_use = collections.Counter()
recipe_pages = collections.defaultdict(list)

def walk(box, fn):
    fn(box)
    for c in getattr(box, 'children', []) or []:
        walk(c, fn)

for pno, page in enumerate(doc.pages, 1):
    pb = page._page_box
    top = pb.content_box_y(); bottom = top + pb.height
    left = pb.content_box_x(); right = left + pb.width
    full_bleed = pb.margin_top == 0
    def check(b):
        el = getattr(b, 'element', None)
        tag = getattr(b, 'element_tag', '')
        if el is None or full_bleed:
            return
        cls = el.get('class') or ''
        if b.height and b.position_y + b.margin_top + b.border_height() > bottom + 2 and tag not in ('html', 'body'):
            if not any(k in cls for k in ('opener',)):
                issues.append((pno, 'overflow-bottom', tag, cls, round((b.position_y + b.margin_top + b.border_height() - bottom) / 96, 3)))
        if b.width and b.position_x + b.margin_left + b.border_width() > right + 2 and tag not in ('html', 'body'):
            issues.append((pno, 'overflow-right', tag, cls, round((b.position_x + b.margin_left + b.border_width() - right) / 96, 3)))
        if tag == 'img':
            img_use[el.get('src')] += 1
            if not el.get('src'):
                issues.append((pno, 'missing-image', tag, el.get('alt'), 0))
        if tag in ('h2', 'h3', 'h4') and b.position_y + b.margin_top + b.border_height() > bottom - 0.45 * 96:
            issues.append((pno, 'heading-near-bottom', tag, (el.text or '')[:40], 0))
    walk(pb, check)
    for a in page.anchors:
        if a.startswith('recipe-') and a[7:].isdigit():
            recipe_pages[int(a[7:])].append(pno)

# de-duplicate nested reports
seen, uniq = set(), []
for i in issues:
    k = (i[0], i[1], i[3])
    if k not in seen:
        seen.add(k); uniq.append(i)
print('pages', len(doc.pages))
print('issues', len(uniq))
for i in uniq[:60]:
    print('  ', i)
dups = {k: v for k, v in img_use.items() if v > 1 and k}
print('images used', len(img_use), 'duplicates', dups)
print('recipes placed', len(recipe_pages), 'multi-page', {k: v for k, v in recipe_pages.items() if len(v) > 1})
json.dump({str(k): v for k, v in recipe_pages.items()}, open(os.path.join(os.path.dirname(html), 'recipe_pages.json'), 'w'))
