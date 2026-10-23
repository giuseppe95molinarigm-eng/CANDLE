"""Parse the approved manuscript (.docx) into a structured JSON book model.

Text is copied verbatim from the manuscript runs; only bold/italic are mapped
to <strong>/<em>. Nothing is rewritten.
"""
import html, json, re, sys
import docx
from docx.oxml.ns import qn

W = lambda t: qn('w:' + t)


def run_html(r):
    t = ''.join((x.text or '') if x.tag == W('t') else ('\t' if x.tag == W('tab') else ('\n' if x.tag == W('br') and x.get(W('type')) != 'page' else ''))
                for x in r.iter() if x.tag in (W('t'), W('tab'), W('br')))
    if not t:
        return '', False, False
    rpr = r.find(W('rPr'))
    b = i = False
    if rpr is not None:
        bb = rpr.find(W('b'))
        b = bb is not None and bb.get(W('val')) not in ('0', 'false')
        ii = rpr.find(W('i'))
        i = ii is not None and ii.get(W('val')) not in ('0', 'false')
    return t, b, i


def para(el):
    runs = []
    for r in el.iter(W('r')):
        t, b, i = run_html(r)
        if t:
            runs.append((t, b, i))
    # merge adjacent runs with same formatting
    merged = []
    for t, b, i in runs:
        if merged and merged[-1][1] == b and merged[-1][2] == i:
            merged[-1] = (merged[-1][0] + t, b, i)
        else:
            merged.append((t, b, i))
    out = []
    for t, b, i in merged:
        h = html.escape(t, quote=False)
        if i:
            h = '<em>' + h + '</em>'
        if b:
            h = '<strong>' + h + '</strong>'
        out.append(h)
    ppr = el.find(W('pPr'))
    d = {'type': 'p', 'style': '', 'shd': None, 'num': None}
    if ppr is not None:
        s = ppr.find(W('pStyle'))
        if s is not None:
            d['style'] = s.get(W('val'))
        n = ppr.find(W('numPr'))
        if n is not None:
            d['num'] = int(n.find(W('numId')).get(W('val')))
        sh = ppr.find(W('shd'))
        if sh is not None:
            d['shd'] = sh.get(W('fill'))
    d['runs'] = merged
    d['html'] = ''.join(out)
    d['text'] = ''.join(t for t, _, _ in merged)
    d['pagebreak'] = any(b.get(W('type')) == 'page' for b in el.iter(W('br')))
    return d


def numbering_formats(document):
    part = document.part.numbering_part
    root = part.element
    abstract = {}
    for a in root.findall(W('abstractNum')):
        lvl = a.find(W('lvl'))
        fmt = lvl.find(W('numFmt')).get(W('val')) if lvl is not None and lvl.find(W('numFmt')) is not None else 'bullet'
        abstract[a.get(W('abstractNumId'))] = fmt
    nums = {}
    for n in root.findall(W('num')):
        nums[int(n.get(W('numId')))] = abstract.get(n.find(W('abstractNumId')).get(W('val')), 'bullet')
    return nums


def parse(path):
    d = docx.Document(path)
    fmts = numbering_formats(d)
    blocks = []
    for el in d.element.body.iterchildren():
        if el.tag == W('p'):
            p = para(el)
            if p['num'] is not None:
                p['list'] = 'ol' if fmts.get(p['num']) == 'decimal' else 'ul'
            blocks.append(p)
        elif el.tag == W('tbl'):
            rows = []
            for tr in el.findall(W('tr')):
                cells = []
                for tc in tr.findall(W('tc')):
                    cells.append([para(p) for p in tc.findall(W('p'))])
                rows.append(cells)
            blocks.append({'type': 'table', 'rows': rows})
    return blocks


SLUG = re.compile(r'[^a-z0-9]+')


def slug(s):
    s = s.lower().replace('&', 'and').replace("'", '').replace('’', '')
    s = (s.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('â', 'a')
         .replace('ô', 'o').replace('ñ', 'n').replace('ü', 'u').replace('ç', 'c').replace('î', 'i'))
    return SLUG.sub('_', s).strip('_')


def structure(blocks):
    """Group blocks into book sections. Recipes become dedicated records."""
    book = {'front': [], 'sections': []}
    cur = None
    i = 0
    # title page = blocks before first page break
    while not blocks[i].get('pagebreak'):
        book['front'].append(blocks[i]); i += 1
    i += 1
    copyright_blocks = []
    while not (blocks[i].get('style') == 'Heading1'):
        copyright_blocks.append(blocks[i]); i += 1
    book['copyright'] = copyright_blocks
    recipes = []
    while i < len(blocks):
        b = blocks[i]
        if b.get('style') == 'Heading1':
            cur = {'title': b['text'], 'items': []}
            book['sections'].append(cur)
            i += 1
            continue
        if b['type'] == 'p' and re.fullmatch(r'RECIPE \d{3}', b['text'].strip()):
            num = int(b['text'].split()[1])
            r = {'type': 'recipe', 'num': num}
            i += 1
            assert blocks[i]['style'] == 'Heading2', blocks[i]
            r['title'] = blocks[i]['text']; i += 1
            r['meta'] = blocks[i]['text']; i += 1
            assert blocks[i]['text'].startswith('[IMAGE %03d]' % num), (num, blocks[i]['text'][:40])
            r['image_brief'] = blocks[i]['text'][len('[IMAGE 000] '):]; i += 1
            r['intro'] = []
            while blocks[i].get('text') != 'INGREDIENTS':
                r['intro'].append(blocks[i]); i += 1
            i += 1
            r['ingredients'] = []
            # ingredient blocks: table(s) and/or sub-heading paragraphs until METHOD
            while not (blocks[i]['type'] == 'p' and blocks[i]['text'] == 'METHOD'):
                r['ingredients'].append(blocks[i]); i += 1
            i += 1
            r['method'] = []
            r['tips'] = []
            r['footer'] = []
            while i < len(blocks):
                b = blocks[i]
                if b['type'] == 'p' and (re.fullmatch(r'RECIPE \d{3}', b['text'].strip()) or b.get('style') == 'Heading1'):
                    break
                if b['type'] == 'p' and b.get('shd') == 'FBF1E2':
                    r['tips'].append(b)
                elif b['type'] == 'p' and b['text'].startswith('Pair:'):
                    r['footer'].append(b)
                elif not r['tips'] and not r['footer']:
                    r['method'].append(b)
                else:
                    r.setdefault('extra', []).append(b)
                i += 1
            r['code'] = '%03d_%s' % (num, slug(r['title']))
            cur['items'].append(r)
            recipes.append(r)
            continue
        cur['items'].append(b)
        i += 1
    book['recipe_count'] = len(recipes)
    return book


if __name__ == '__main__':
    blocks = parse(sys.argv[1])
    book = structure(blocks)
    json.dump(book, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    rs = [it for s in book['sections'] for it in s['items'] if it.get('type') == 'recipe']
    print('recipes', len(rs), 'nums ok', [r['num'] for r in rs] == list(range(1, 151)))
    print('with extra:', [r['num'] for r in rs if r.get('extra')])
    print('ingredient shapes:', sorted(set(tuple(b['type'] for b in r['ingredients']) for r in rs)))
    print('tips count:', sorted(set(len(r['tips']) for r in rs)), 'footer', sorted(set(len(r['footer']) for r in rs)))
