"""Render the print interior (8.5 x 11 in, full colour, with bleed) as HTML for WeasyPrint.

Text comes verbatim from build/book.json (parsed from the approved manuscript).
Usage:
  python3 build/render_print.py --images images/final --out work/print/book.html [--sample]
"""
import argparse, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = 'The First-Try Edible Candle Cookbook'
AUTHOR = 'Margot Ellery'

ORDINALS = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4}


def esc(s):
    return html.escape(s, quote=True)


def slug(s):
    s = s.lower().replace('&', 'and')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


# ---------------------------------------------------------------- inline helpers

def runs_html(runs):
    out = []
    for t, b, i in runs:
        h = esc(t).replace('\t', ' ')
        if i:
            h = '<em>' + h + '</em>'
        if b:
            h = '<strong>' + h + '</strong>'
        out.append(h)
    return ''.join(out)


def callout(p, cls='callout'):
    """Shaded manuscript boxes: first bold run is the label (e.g. FIRST-TRY TIP)."""
    runs = p['runs']
    if runs and runs[0][1]:
        label = runs[0][0].strip()
        body = runs_html(runs[1:]).lstrip()
        return f'<aside class="{cls}"><span class="callout-label">{esc(label)}</span> {body}</aside>'
    return f'<aside class="{cls}">{runs_html(runs)}</aside>'


def table_html(t, cls='data'):
    rows = t['rows']
    out = [f'<table class="{cls}">']
    for ri, row in enumerate(rows):
        tag = 'th' if ri == 0 else 'td'
        if ri == 0:
            out.append('<thead>')
        out.append('<tr>')
        for c in row:
            inner = '<br/>'.join(runs_html(p['runs']) for p in c if p['runs'])
            if ri == 0:
                inner = re.sub(r'</?strong>', '', inner)
            out.append(f'<{tag}>{inner}</{tag}>')
        out.append('</tr>')
        if ri == 0:
            out.append('</thead><tbody>')
    out.append('</tbody></table>')
    return ''.join(out)


def blocks_html(items, ctx, section=''):
    """Generic flow content (front matter, parts, plans, references)."""
    out = []
    i = 0
    group = None          # open wrapper for a bread recipe or a party plan
    after_heading = False
    while i < len(items):
        b = items[i]
        if b.get('type') == 'table':
            out.append(table_html(b, 'data finder' if section == 'Recipe Finder' else 'data'))
            i += 1
            continue
        if b.get('type') == 'recipe':
            if group:
                out.append('</div>'); group = None
            out.append(recipe_html(b, ctx))
            i += 1
            continue
        if b.get('list'):
            kind, num = b['list'], b['num']
            lis = []
            while i < len(items) and items[i].get('list') == kind and items[i].get('num') == num:
                lis.append('<li>' + runs_html(items[i]['runs']) + '</li>')
                i += 1
            cls = 'flow'
            if group == 'bread' and kind == 'ul':
                cls = 'flow bread-ing'
            out.append(f'<{kind} class="{cls}">' + ''.join(lis) + f'</{kind}>')
            after_heading = False
            continue
        st = b.get('style')
        text = b.get('text', '')
        if not text.strip():
            i += 1
            continue
        if st == 'Heading2':
            if group:
                out.append('</div>'); group = None
            hid = ctx.anchor(text)
            if re.match(r'B\d\. ', text):
                group = 'bread'
                out.append(f'<div class="bread"><h2 class="bread-title" id="{hid}">{esc(text)}</h2>')
            elif re.match(r'Plan \d+: ', text):
                first = 'plan' not in ''.join(out)
                group = 'plan'
                out.append(f'<div class="plan{" first" if first else ""}"><h2 class="plan-title" id="{hid}">{esc(text)}</h2>')
            else:
                out.append(f'<h2 id="{hid}">{esc(text)}</h2>')
            after_heading = True
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
                out.append(f'<div class="ix"><a href="#recipe-{n:03d}">{esc(name)}<span class="ix-ref">{esc(ref)}</span></a></div>')
            else:
                out.append(f'<div class="ix-letter">{esc(text)}</div>')
        elif after_heading and group:
            out.append(f'<p class="sub-meta">{runs_html(b["runs"])}</p>')
        elif b['runs'] and all(x[1] for x in b['runs']) and len(text) < 40:
            out.append(f'<h4 class="minor">{esc(text)}</h4>')
        else:
            out.append(f'<p>{runs_html(b["runs"])}</p>')
        after_heading = False
        i += 1
    if group:
        out.append('</div>')
    html_out = '\n'.join(out)
    if section == 'A Note from Margot':
        # sign-off: the last two paragraphs of the letter
        parts = html_out.rsplit('<p>', 2)
        if len(parts) == 3:
            html_out = parts[0] + '<p class="signoff">' + parts[1] + '<p class="signoff">' + parts[2]
    if section == 'Recipe Index (A–Z)':
        html_out = '<div class="index-cols">' + html_out + '</div>'
    return html_out


def runs_html_plain(b):
    return esc(b['text'])


# ---------------------------------------------------------------- recipe

def split_meta(meta):
    meta = meta.strip()
    diet = ''
    m = re.match(r'^(.*?)\s{3,}([A-Z]{1,2}(?:\s·\s[A-Z]{1,2})*)$', meta)
    if m:
        meta, diet = m.group(1), m.group(2)
    parts = [p.strip() for p in re.split(r'\s+·\s+', meta) if p.strip()]
    return parts, [d.strip() for d in diet.split('·') if d.strip()]


def ingredients_html(r):
    out = []
    for blk in r['ingredients']:
        cols = blk['rows'][0]
        items = [p for c in cols for p in c if p['runs']]
        out_list = []
        for p in items:
            if all(x[1] for x in p['runs']):
                if out_list:
                    out.append('<ul class="ing">' + ''.join(out_list) + '</ul>')
                    out_list = []
                out.append(f'<h4 class="ing-sub">{esc(p["text"])}</h4>')
            else:
                out_list.append('<li>' + runs_html(p['runs']) + '</li>')
        if out_list:
            out.append('<ul class="ing">' + ''.join(out_list) + '</ul>')
    return ''.join(out)


def footer_html(p):
    rows = []
    label, body = None, []
    for t, b, i in p['runs']:
        if b and t.strip().endswith(':'):
            if label:
                rows.append((label, body))
            label, body = t.strip()[:-1], []
        else:
            body.append((t, b, i))
    if label:
        rows.append((label, body))
    out = ['<dl class="serve">']
    for lab, body in rows:
        out.append(f'<div class="serve-row"><dt>{esc(lab)}</dt><dd>{runs_html(body).strip()}</dd></div>')
    out.append('</dl>')
    return ''.join(out)


def recipe_html(r, ctx):
    num = r['num']
    parts, diet = split_meta(r['meta'])
    img = ctx.image_for(r)
    meta_html = ''.join(f'<span class="m">{esc(p)}</span>' for p in parts)
    diet_html = ''.join(f'<span class="diet">{esc(d)}</span>' for d in diet)
    intro = ''.join(f'<p>{runs_html(p["runs"])}</p>' for p in r['intro'])
    method = ''.join('<li>' + runs_html(m['runs']) + '</li>' for m in r['method'])
    tips = ''.join(callout(t, 'tip') for t in r['tips'])
    foot = ''.join(footer_html(f) for f in r['footer'])
    title = esc(r['title'])
    return f'''
<article class="recipe v-{ctx.variant.get(num, 'l')}" id="recipe-{num:03d}" data-code="{r['code']}">
  <div class="rt-set" data-title="Recipe {num} · {title}"></div>
  <header class="recipe-head">
    <div class="kicker">Recipe {num:03d}<span class="diets">{diet_html}</span></div>
    <h2 class="recipe-title">{title}</h2>
  </header>
  <div class="meta">{meta_html}</div>
  <div class="intro">{intro}</div>
  <div class="row">
    <figure class="hero"><img src="{img}" alt="{title}"/></figure>
    <section class="ingredients"><h3 class="label">Ingredients</h3>{ingredients_html(r)}</section>
  </div>
  <section class="method"><h3 class="label">Method</h3><ol class="steps">{method}</ol>{tips}</section>
  {foot}
  <div class="rt-end"></div>
</article>'''


# ---------------------------------------------------------------- page furniture

def opener(kind, label, title, intro_html, extra='', chapter_string=''):
    return f'''
<section class="opener {kind}"><div class="op-reset"></div>{chapter_string}
  <div class="op-inner">
    <div class="op-label">{esc(label)}</div>
    <div class="op-rule"><span></span><i></i><span></span></div>
    <h1 class="op-title" id="{slug(title)}">{esc(title)}</h1>
    <div class="op-rule"><span></span><i></i><span></span></div>
    <div class="op-intro">{intro_html}</div>
    {extra}
  </div>
</section>'''


class Ctx:
    def __init__(self, images_dir, out_dir):
        self.images_dir = images_dir
        self.out_dir = out_dir
        self.ids = set()
        self.variant = {}
        self.placeholder = None

    def anchor(self, text):
        a = slug(text)
        base, n = a, 2
        while a in self.ids:
            a = f'{base}-{n}'; n += 1
        self.ids.add(a)
        return a

    def image_for(self, r):
        for ext in ('.jpg', '.jpeg', '.png'):
            p = os.path.join(self.images_dir, r['code'] + ext)
            if os.path.exists(p):
                return os.path.relpath(p, self.out_dir)
        return self.placeholder or ''


def chapter_range(book, title):
    for s in book['sections']:
        if s['title'] == title:
            nums = [it['num'] for it in s['items'] if it.get('type') == 'recipe']
            return nums
    return []


def render(book, ctx, sample=None):
    css_href = os.path.relpath(os.path.join(ROOT, 'build/print.css'), ctx.out_dir)
    body = []
    if sample:
        # client sample: one chapter opener followed by selected recipes
        first = next(s for s in book['sections'] if s['title'] == sample['opener'])
        body.append(section_html(book, first, ctx, recipe_filter=set()))
        recs = {it['num']: (s, it) for s in book['sections'] for it in s['items'] if it.get('type') == 'recipe'}
        for n in sample['recipes']:
            s, r = recs[n]
            chap = re.sub(r'^Chapter \d+: ', '', s['title'])
            body.append(recipe_html(r, ctx).replace('<header class="recipe-head">', f'<div class="chapter-string" data-chapter="{esc(chap)}"></div><header class="recipe-head">', 1))
    else:
        body.append(frontmatter_html(book, ctx))
        for s in book['sections']:
            body.append(section_html(book, s, ctx))
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>{TITLE}</title>
<meta name="author" content="{AUTHOR}"/>
<link rel="stylesheet" href="{css_href}"/></head>
<body>
<div class="string-book">{TITLE}</div>
{''.join(body)}
</body></html>'''


def section_html(book, s, ctx, recipe_filter=None):
    t = s['title']
    items = s['items']
    if recipe_filter is not None:
        items = [it for it in items if it.get('type') != 'recipe' or it['num'] in recipe_filter]
    m = re.match(r'Part (One|Two|Three|Four): (.*)', t)
    if m:
        # intro paragraphs (before first heading) go on the opener
        intro, rest = split_intro(items)
        return (opener('part', f'Part {m.group(1)}', m.group(2), intro,
                       chapter_string=f'<div class="chapter-string" data-chapter="{esc(m.group(2))}"></div>') +
                f'<div class="flow-section">{blocks_html(rest, ctx, t)}</div>')
    m = re.match(r'Chapter (\d+): (.*)', t)
    if m:
        intro, rest = split_intro(items)
        nums = chapter_range(book, t)
        rng = f'<div class="op-range">Recipes {nums[0]}&#8211;{nums[-1]}</div>' if nums else ''
        return (opener('chapter', f'Chapter {m.group(1)}', m.group(2), intro, rng,
                       f'<div class="chapter-string" data-chapter="{esc(m.group(2))}"></div>') +
                (f'<div class="chapter-body">{blocks_html(rest, ctx, t)}</div>' if rest else ''))
    if t == 'Contents':
        return contents_html(book, s)
    return (f'<section class="plain-section" id="{slug(t)}"><div class="chapter-string" data-chapter="{esc(t)}"></div>'
            f'<h1 class="sec-title">{esc(t)}</h1>{blocks_html(items, ctx, t)}</section>')


def split_intro(items):
    intro, i = [], 0
    while i < len(items) and items[i].get('type') == 'p' and not items[i].get('style') and not items[i].get('shd') and not items[i].get('list'):
        if items[i]['text'].strip():
            intro.append(f'<p>{runs_html(items[i]["runs"])}</p>')
        i += 1
    return ''.join(intro), items[i:]


def frontmatter_html(book, ctx):
    f = book['front']
    title, subtitle, author = f[0]['text'], f[1]['text'], f[2]['text']
    cp = ''.join(f'<p>{runs_html(p["runs"])}</p>' for p in book['copyright'] if p.get('text', '').strip())
    return f'''
<section class="title-page">
  <div class="tp-rule"><span></span><i></i><span></span></div>
  <h1 class="tp-title"><span class="tp-small">The First-Try</span><span class="tp-big">Edible Candle</span><span class="tp-small2">Cookbook</span></h1>
  <div class="tp-rule"><span></span><i></i><span></span></div>
  <p class="tp-sub">{esc(subtitle)}</p>
  <p class="tp-author">{esc(author)}</p>
</section>
<section class="copyright-page">{cp}</section>'''


def contents_html(book, s):
    out = ['<section class="contents" id="contents"><h1 class="sec-title">Contents</h1><div class="toc">']
    for b in s['items']:
        txt = (b.get('text') or '').strip()
        if not txt:
            continue
        target = toc_target(txt)
        if b['runs'] and all(x[1] for x in b['runs']):
            out.append(f'<div class="toc-part"><a href="#{target}">{esc(txt)}</a></div>')
        else:
            label = re.sub(r'\s*Recipes\s+\d+.\d+$', '', txt)
            rng = txt[len(label):].strip()
            rng_html = f' <span class="toc-range">{esc(rng)}</span>' if rng else ''
            out.append(f'<div class="toc-entry"><a href="#{target}">{esc(label)}{rng_html}</a></div>')
    out.append('</div></section>')
    return ''.join(out)


def toc_target(txt):
    m = re.match(r'Part (One|Two|Three|Four): (.*)', txt)
    if m:
        return slug(m.group(2))
    m = re.match(r'(Chapter \d+): (.*?)(\s*Recipes\s+\d+.\d+)?$', txt)
    if m:
        return slug(m.group(2))
    if txt == 'Reference':
        return 'conversion-charts'
    return slug(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', default='images/final')
    ap.add_argument('--out', default='work/print/book.html')
    ap.add_argument('--sample', action='store_true')
    ap.add_argument('--sample-recipes', default='1,45,103')
    a = ap.parse_args()
    book = json.load(open(os.path.join(ROOT, 'build/book.json')))
    out_dir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(out_dir, exist_ok=True)
    ctx = Ctx(os.path.abspath(a.images), out_dir)
    vpath = os.path.join(ROOT, 'build/variants.json')
    if os.path.exists(vpath):
        ctx.variant = {int(k): v for k, v in json.load(open(vpath)).items()}
    sample = None
    if a.sample:
        sample = {'opener': 'Chapter 1: Butter Candle Classics', 'recipes': [int(x) for x in a.sample_recipes.split(',')]}
    open(a.out, 'w').write(render(book, ctx, sample))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
