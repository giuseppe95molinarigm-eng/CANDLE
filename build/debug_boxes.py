import sys, weasyprint, logging
logging.getLogger('weasyprint').setLevel(logging.ERROR)
d = weasyprint.HTML(sys.argv[1]).render()
want = set(sys.argv[2].split(','))
def walk(b, page, seen):
    el = getattr(b, 'element', None)
    if el is not None and el.get('class') in want and id(el) not in seen:
        seen.add(id(el))
        print(page, el.get('class'), 'top %.2f h %.2f' % (b.position_y / 96, (b.margin_height() if hasattr(b,'margin_height') else 0) / 96))
    for c in getattr(b, 'children', []):
        walk(c, page, seen)
for i, p in enumerate(d.pages):
    print('-- page', i + 1, 'content bottom %.2f' % ((p._page_box.content_box_y() + p._page_box.height) / 96))
    walk(p._page_box, i + 1, set())
