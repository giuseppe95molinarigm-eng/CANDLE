"""Build the reflowable Kindle EPUB 3 from build/book.json.

Text is verbatim from the approved manuscript. No print-only references
(page numbers, "continued", column layouts) are used.
Usage: python3 build/render_epub.py --images images/final --out deliverables/...epub
"""
import argparse, html, io, json, os, re, uuid, zipfile, datetime
from PIL import Image

import render_print as R

ROOT = R.ROOT
esc = R.esc
runs_html = R.runs_html
TITLE = 'The First-Try Edible Candle Cookbook'
AUTHOR = 'Margot Ellery'
IMG_W = 800           # px; keeps the file small (Kindle 70% royalty delivery fee is per MB) while sharp on e-readers
IMG_Q = 78

CSS = """
@charset "utf-8";
body { font-family: serif; line-height: 1.45; margin: 0 2%; }
h1, h2, h3, h4 { font-family: serif; line-height: 1.2; page-break-after: avoid; break-after: avoid; }
h1 { font-size: 1.7em; color: #123327; text-align: center; margin: 1.2em 0 0.4em; }
h1.part-label, p.part-label { font-size: 0.85em; letter-spacing: 0.25em; text-transform: uppercase; color: #8a6418; text-align: center; margin: 2.5em 0 0.2em; }
.opener-intro { font-style: italic; text-align: center; margin: 1em 5%; }
.range { text-align: center; font-size: 0.8em; letter-spacing: 0.2em; text-transform: uppercase; color: #8a6418; }
hr.orn { border: none; border-top: 1px solid #b8862e; width: 30%; margin: 0.8em auto; }
h2 { font-size: 1.35em; color: #123327; margin: 1.4em 0 0.4em; }
h3 { font-size: 0.95em; letter-spacing: 0.12em; text-transform: uppercase; color: #8a6418; margin: 1.2em 0 0.4em; }
h4 { font-size: 0.9em; letter-spacing: 0.1em; text-transform: uppercase; color: #123327; margin: 1em 0 0.3em; }
p { margin: 0 0 0.6em; text-indent: 0; }
.callout, .tip { background-color: #fbf4e6; color: #2b2420; border-left: 4px solid #b8862e; padding: 0.5em 0.8em; margin: 1em 0; }
.callout-label { font-weight: bold; color: #8a6418; letter-spacing: 0.08em; font-size: 0.85em; }
table { border-collapse: collapse; width: 100%; font-size: 0.75em; margin: 0.8em 0; }
td, th { word-wrap: break-word; overflow-wrap: break-word; hyphens: auto; }
.label-p { font-weight: bold; letter-spacing: 0.08em; text-transform: uppercase; color: #123327; margin: 1em 0 0.3em; font-size: 0.9em; }
a.xref { color: inherit; }
th { background-color: #123327; color: #f5ead2; text-align: left; padding: 0.3em; }
td { border-bottom: 1px solid #e3d6bb; padding: 0.3em; vertical-align: top; }
.recipe { page-break-before: always; break-before: page; }
.kicker { font-size: 0.8em; letter-spacing: 0.25em; text-transform: uppercase; color: #8a6418; margin: 0; }
h2.recipe-title { margin-top: 0.2em; font-size: 1.6em; }
.photo { text-align: center; margin: 0.6em 0; }
.photo img { width: 100%; max-width: 100%; height: auto; }
.meta { font-size: 0.85em; background-color: #123327; color: #f1e8d4; padding: 0.4em 0.6em; }
.diets { font-size: 0.85em; font-weight: bold; color: #8a6418; }
.intro { font-style: italic; }
ul.ing { list-style-type: none; padding-left: 0; margin: 0 0 0.8em; }
ul.ing li { border-bottom: 1px dotted #d8c79f; padding: 0.25em 0; }
.ing-sub { font-style: italic; color: #8a6418; margin: 0.6em 0 0.2em; font-weight: bold; }
ol.steps { padding-left: 1.6em; margin: 0 0 0.8em; }
ol.steps li { margin-bottom: 0.5em; }
.serve p { margin: 0.3em 0; }
.serve-label { font-weight: bold; color: #5a3410; }
ol.flow, ul.flow { padding-left: 1.5em; }
ol.flow li, ul.flow li { margin-bottom: 0.35em; }
.signoff { text-align: right; font-style: italic; }
.toc p { margin: 0.2em 0; }
.toc .part { font-weight: bold; margin-top: 0.8em; }
.toc .sub { margin-left: 1.2em; }
.ix-letter { font-weight: bold; color: #8a6418; margin-top: 0.8em; }
.ix { margin: 0.15em 0; }
.title-page { text-align: center; }
.title-page .t { font-size: 2em; font-weight: bold; color: #123327; margin-top: 2em; }
.title-page .s { font-style: italic; margin: 1.2em 5%; }
.title-page .a { letter-spacing: 0.3em; text-transform: uppercase; margin-top: 2em; }
.copyright p { font-size: 0.85em; }
"""


def xhtml(title, body, lang='en'):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">
<head><meta charset="utf-8"/><title>{esc(title)}</title><link rel="stylesheet" type="text/css" href="../css/book.css"/></head>
<body>
{body}
</body></html>'''


class Book:
    def __init__(self, data, images_dir):
        self.data = data
        self.images_dir = images_dir
        self.files = []        # (id, href, title, xhtml)
        self.images = {}       # href -> bytes
        self.anchor_file = {}  # anchor id -> file href
        self.nav = []          # (title, href, children)
        self.ids = set()

    def anchor(self, text):
        a = R.slug(text)
        base, n = a, 2
        while a in self.ids:
            a = f'{base}-{n}'; n += 1
        self.ids.add(a)
        return a

    def link(self, anchor):
        f = self.anchor_file.get(anchor)
        return f'{os.path.basename(f)}#{anchor}' if f else '#'

    def add_image(self, code):
        for ext in ('.jpg', '.png'):
            p = os.path.join(self.images_dir, code + ext)
            if os.path.exists(p):
                im = Image.open(p).convert('RGB')
                if im.width > IMG_W:
                    im = im.resize((IMG_W, round(im.height * IMG_W / im.width)), Image.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, 'JPEG', quality=IMG_Q, optimize=True, progressive=False)
                href = f'images/{code}.jpg'
                self.images[href] = buf.getvalue()
                return href
        return None


# ------------------------------------------------------------------ content

def callout(p, cls='callout'):
    runs = p['runs']
    if runs and runs[0][1]:
        return f'<div class="{cls}"><p><span class="callout-label">{esc(runs[0][0].strip())}</span> {runs_html(runs[1:]).lstrip()}</p></div>'
    return f'<div class="{cls}"><p>{runs_html(runs)}</p></div>'


def table(t):
    out = ['<table>']
    for ri, row in enumerate(t['rows']):
        tag = 'th' if ri == 0 else 'td'
        cells = []
        for c in row:
            inner = '<br/>'.join(runs_html(p['runs']) for p in c if p['runs'])
            if ri == 0:
                inner = re.sub(r'</?strong>', '', inner)
            cells.append(f'<{tag}>{inner}</{tag}>')
        out.append('<tr>' + ''.join(cells) + '</tr>')
    out.append('</table>')
    return ''.join(out)


def finder_table(t):
    """Recipe Finder for small screens: the four check-mark diet columns become one 'Diet' column."""
    head = [' '.join(p['text'] for p in c).strip() for c in t['rows'][0]]
    out = ['<table><tr><th>' + '</th><th>'.join(esc(h) for h in head[:3]) + '</th><th>Diet</th></tr>']
    for row in t['rows'][1:]:
        c = [' '.join(p['text'] for p in cell).strip() for cell in row]
        diets = ' · '.join(h for h, v in zip(head[3:], c[3:]) if v)
        n = int(c[0])
        out.append(f'<tr><td>{esc(c[0])}</td><td><a class="xref" href="@@recipe-{n:03d}@@">{esc(c[1])}</a></td><td>{esc(c[2])}</td><td>{esc(diets)}</td></tr>')
    out.append('</table>')
    return ''.join(out)


def link_refs(body):
    """Turn '(recipe 132)' and '(Bread B3)' cross-references into links (text unchanged)."""
    body = re.sub(r'\((recipe (\d+))\)', lambda m: f'(<a class="xref" href="@@recipe-{int(m.group(2)):03d}@@">{m.group(1)}</a>)', body)
    body = re.sub(r'\((Bread (B\d))\)', lambda m: f'(<a class="xref" href="@@bread-{m.group(2)}@@">{m.group(1)}</a>)', body)
    return body


def flow(items, bk, section, file_href, nav_children):
    out = []
    i = 0
    after_heading = False
    while i < len(items):
        b = items[i]
        if b.get('type') == 'table':
            out.append(finder_table(b) if section == 'Recipe Finder' else table(b)); i += 1; continue
        if b.get('type') == 'recipe':
            out.append(recipe(b, bk, file_href, nav_children)); i += 1; continue
        if b.get('list'):
            kind, num = b['list'], b['num']
            lis = []
            while i < len(items) and items[i].get('list') == kind and items[i].get('num') == num:
                lis.append('<li>' + runs_html(items[i]['runs']) + '</li>')
                i += 1
            out.append(f'<{kind} class="flow">' + ''.join(lis) + f'</{kind}>')
            after_heading = False
            continue
        text = b.get('text', '')
        if not text.strip():
            i += 1; continue
        st = b.get('style')
        if st == 'Heading2':
            a = bk.anchor(text)
            bk.anchor_file[a] = file_href
            nav_children.append((text, f'{os.path.basename(file_href)}#{a}', []))
            out.append(f'<h2 id="{a}">{esc(text)}</h2>')
            after_heading = bool(re.match(r'(B\d\.|Plan \d+:) ', text))
            i += 1
            continue
        if st == 'Heading3':
            out.append(f'<h3>{esc(text)}</h3>')
        elif b.get('shd') == 'FBF1E2':
            out.append(callout(b))
        elif section == 'Recipe Index (A–Z)':
            if '\t' in text:
                name, ref = text.split('\t', 1)
                n = int(re.search(r'\d+', ref).group())
                out.append(f'<p class="ix">{esc(name)}&#8195;<a href="@@recipe-{n:03d}@@">{esc(ref)}</a></p>')
            else:
                out.append(f'<p class="ix-letter">{esc(text)}</p>')
        elif after_heading:
            out.append(f'<p><em>{runs_html(b["runs"])}</em></p>')
        elif b['runs'] and all(x[1] for x in b['runs']) and len(text) < 40:
            out.append(f'<p class="label-p">{esc(text)}</p>')
        else:
            out.append(f'<p>{runs_html(b["runs"])}</p>')
        after_heading = False
        i += 1
    html_out = '\n'.join(out)
    if section == 'A Note from Margot':
        parts = html_out.rsplit('<p>', 2)
        if len(parts) == 3:
            html_out = parts[0] + '<p class="signoff">' + parts[1] + '<p class="signoff">' + parts[2]
    return html_out


def recipe(r, bk, file_href, nav_children):
    num = r['num']
    a = f'recipe-{num:03d}'
    bk.anchor_file[a] = file_href
    nav_children.append((f'{num}. {r["title"]}', f'{os.path.basename(file_href)}#{a}', []))
    parts, diet = R.split_meta(r['meta'])
    img = bk.add_image(r['code'])
    ing = []
    for blk in r['ingredients']:
        lst = []
        for p in [p for c in blk['rows'][0] for p in c if p['runs']]:
            if all(x[1] for x in p['runs']):
                if lst:
                    ing.append('<ul class="ing">' + ''.join(lst) + '</ul>'); lst = []
                ing.append(f'<p class="ing-sub">{esc(p["text"])}</p>')
            else:
                lst.append('<li>' + runs_html(p['runs']) + '</li>')
        if lst:
            ing.append('<ul class="ing">' + ''.join(lst) + '</ul>')
    serve = []
    for f in r['footer']:
        label, body = None, []
        rows = []
        for t, b, i in f['runs']:
            if b and t.strip().endswith(':'):
                if label:
                    rows.append((label, body))
                label, body = t.strip(), []
            else:
                body.append((t, b, i))
        if label:
            rows.append((label, body))
        serve += [f'<p><span class="serve-label">{esc(l)}</span> {runs_html(bd).strip()}</p>' for l, bd in rows]
    img_html = f'<div class="photo"><img src="../{img}" alt="{esc(r["title"])}: {esc(r["image_brief"])}"/></div>' if img else ''
    return f'''<section class="recipe" id="{a}" epub:type="chapter">
<p class="kicker">Recipe {num:03d}</p>
<h2 class="recipe-title">{esc(r['title'])}</h2>
{img_html}
<p class="meta">{' · '.join(esc(p) for p in parts)}</p>
{f'<p class="diets">{" · ".join(esc(d) for d in diet)}</p>' if diet else ''}
<div class="intro">{''.join(f'<p>{runs_html(p["runs"])}</p>' for p in r['intro'])}</div>
<h3>Ingredients</h3>
{''.join(ing)}
<h3>Method</h3>
<ol class="steps">{''.join('<li>' + runs_html(m['runs']) + '</li>' for m in r['method'])}</ol>
{''.join(callout(t, 'tip') for t in r['tips'])}
<div class="serve">{''.join(serve)}</div>
</section>'''


def build(data, images_dir, out_path):
    bk = Book(data, images_dir)
    f = data['front']
    subtitle = f[1]['text']
    pages = []   # (href, title, body)

    pages.append(('text/cover.xhtml', 'Cover', '<div style="text-align:center"><img src="../images/cover.jpg" alt="Cover" style="max-width:100%; height:auto"/></div>'))
    pages.append(('text/title.xhtml', 'Title Page', f'''<div class="title-page"><p class="t">{esc(f[0]['text'])}</p>
<hr class="orn"/><p class="s">{esc(subtitle)}</p><p class="a">{esc(f[2]['text'])}</p></div>'''))
    cp = ''.join(f'<p>{runs_html(p["runs"])}</p>' for p in data['copyright'] if p.get('text', '').strip())
    pages.append(('text/copyright.xhtml', 'Copyright', f'<div class="copyright">{cp}</div>'))
    nav = []
    toc_section = None
    for k, s in enumerate(data['sections']):
        t = s['title']
        href = f'text/s{k:02d}.xhtml'
        children = []
        if t == 'Contents':
            toc_section = (href, s)
            pages.append((href, 'Contents', None))
            continue
        a = R.slug(re.sub(r'^(Part (One|Two|Three|Four)|Chapter \d+): ', '', t)) if re.match(r'(Part|Chapter) ', t) else R.slug(t)
        bk.ids.add(a)
        bk.anchor_file[a] = href
        m = re.match(r'(Part (?:One|Two|Three|Four)|Chapter \d+): (.*)', t)
        if m:
            intro, rest = R.split_intro(s['items'])
            nums = [it['num'] for it in s['items'] if it.get('type') == 'recipe']
            rng = f'<p class="range">Recipes {nums[0]}–{nums[-1]}</p>' if nums else ''
            head = (f'<p class="part-label">{esc(m.group(1))}</p><h1 id="{a}">{esc(m.group(2))}</h1><hr class="orn"/>'
                    f'<div class="opener-intro">{intro}</div>{rng}')
            body = head + flow(rest, bk, t, href, children)
        else:
            body = f'<h1 id="{a}">{esc(t)}</h1>' + flow(s['items'], bk, t, href, children)
        pages.append((href, t, body))
        nav.append((t, f'{os.path.basename(href)}#{a}', children))

    # contents page (links resolved now that all anchors are known)
    href, s = toc_section
    toc = ['<h1 id="contents">Contents</h1><div class="toc">']
    for b in s['items']:
        txt = (b.get('text') or '').strip()
        if not txt:
            continue
        label = re.sub(r'\s*Recipes\s+\d+.\d+$', '', txt)
        target = R.toc_target(txt)
        cls = 'part' if b['runs'] and all(x[1] for x in b['runs']) else 'sub'
        toc.append(f'<p class="{cls}"><a href="{bk.link(target)}">{esc(txt.replace(chr(9), " · "))}</a></p>')
    toc.append('</div>')
    pages = [(h, t, ''.join(toc) if b is None else b) for h, t, b in pages]

    # resolve recipe links in the index
    bread_anchor = {re.match(r'b(\d)-', a).group(1): a for a in bk.anchor_file if re.match(r'b\d-', a)}
    def fix(body):
        body = link_refs(body)
        body = re.sub(r'@@bread-B(\d)@@', lambda m: bk.link(bread_anchor[m.group(1)]), body)
        return re.sub(r'@@(recipe-\d{3})@@', lambda m: bk.link(m.group(1)), body)
    pages = [(h, t, fix(b)) for h, t, b in pages]

    # cover image
    cov = Image.open(os.path.join(ROOT, 'source/cover.jpg')).convert('RGB')
    buf = io.BytesIO(); cov.save(buf, 'JPEG', quality=88)
    bk.images['images/cover.jpg'] = buf.getvalue()

    write_epub(out_path, pages, nav, bk, subtitle)


def nav_xhtml(nav):
    def ol(items, depth=0):
        if not items:
            return ''
        return '<ol>' + ''.join(f'<li><a href="{h}">{esc(t)}</a>{ol(c, depth + 1)}</li>' for t, h, c in items) + '</ol>'
    body = f'''<nav epub:type="toc" id="toc"><h1>Contents</h1>{ol([('Contents', 's00.xhtml#contents', [])] + nav)}</nav>
<nav epub:type="landmarks" hidden=""><ol>
<li><a epub:type="cover" href="cover.xhtml">Cover</a></li>
<li><a epub:type="toc" href="s00.xhtml#contents">Contents</a></li>
<li><a epub:type="bodymatter" href="s01.xhtml">Start</a></li>
</ol></nav>'''
    return xhtml('Contents', body)


def ncx(nav, uid):
    n = [0]
    def pts(items):
        out = []
        for t, h, c in items:
            n[0] += 1
            out.append(f'<navPoint id="np{n[0]}" playOrder="{n[0]}"><navLabel><text>{esc(t)}</text></navLabel><content src="text/{h}"/>{pts(c)}</navPoint>')
        return ''.join(out)
    points = pts([('Contents', 's00.xhtml#contents', [])] + nav)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{uid}"/></head>
<docTitle><text>{esc(TITLE)}</text></docTitle><navMap>{points}</navMap></ncx>'''


def write_epub(out_path, pages, nav, bk, subtitle):
    uid = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'first-try-edible-candle-cookbook-margot-ellery'))
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    # the contents page from the manuscript is s00 (Contents is the first section)
    manifest, spine = [], []
    for i, (h, t, b) in enumerate(pages):
        pid = f'p{i:03d}'
        manifest.append(f'<item id="{pid}" href="{h}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{pid}"/>')
    for i, h in enumerate(sorted(bk.images)):
        props = ' properties="cover-image"' if h == 'images/cover.jpg' else ''
        manifest.append(f'<item id="img{i:03d}" href="{h}" media-type="image/jpeg"{props}/>')
    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{uid}</dc:identifier>
<dc:title id="t1">{esc(TITLE)}</dc:title>
<meta refines="#t1" property="title-type">main</meta>
<dc:title id="t2">{esc(subtitle)}</dc:title>
<meta refines="#t2" property="title-type">subtitle</meta>
<dc:creator id="a1">{esc(AUTHOR)}</dc:creator>
<meta refines="#a1" property="role" scheme="marc:relators">aut</meta>
<dc:language>en</dc:language>
<dc:rights>Copyright © 2026 Margot Ellery. All rights reserved.</dc:rights>
<meta property="dcterms:modified">{now}</meta>
<meta name="cover" content="img{sorted(bk.images).index('images/cover.jpg'):03d}"/>
</metadata>
<manifest>
<item id="nav" href="text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="css" href="css/book.css" media-type="text/css"/>
{chr(10).join(manifest)}
</manifest>
<spine toc="ncx">
{chr(10).join(spine)}
</spine>
<guide><reference type="cover" title="Cover" href="text/cover.xhtml"/><reference type="toc" title="Contents" href="text/s00.xhtml"/></guide>
</package>'''
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with zipfile.ZipFile(out_path, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>
<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>''', compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/content.opf', opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/toc.ncx', ncx(nav, uid), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/css/book.css', CSS, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr('OEBPS/text/nav.xhtml', nav_xhtml(nav), compress_type=zipfile.ZIP_DEFLATED)
        for h, t, b in pages:
            z.writestr('OEBPS/' + h, xhtml(t, b), compress_type=zipfile.ZIP_DEFLATED)
        for h, data in bk.images.items():
            z.writestr('OEBPS/' + h, data, compress_type=zipfile.ZIP_STORED)
    print('wrote', out_path, round(os.path.getsize(out_path) / 1e6, 1), 'MB', len(pages), 'files', len(bk.images), 'images')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', default=os.path.join(ROOT, 'images/final'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'work/epub/book.epub'))
    a = ap.parse_args()
    data = json.load(open(os.path.join(ROOT, 'build/book.json')))
    build(data, os.path.abspath(a.images), a.out)
