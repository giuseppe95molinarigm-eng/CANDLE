"""Content-preservation checks.

1. Every manuscript paragraph / table cell (except the [IMAGE nnn] placeholders,
   which are replaced by photographs) occurs verbatim in the rendered HTML text
   (print) and in the EPUB text.
2. Word-count check on the PDF: every manuscript word occurs in the PDF at least
   as many times as in the manuscript (order-independent, so multi-column
   layouts do not matter).
Usage: verify_text.py manuscript.docx book.html book.pdf [book.epub]
"""
import collections, html as H, re, subprocess, sys, zipfile
import docx
from docx.oxml.ns import qn


def norm(s):
    s = H.unescape(s)
    s = s.replace('­', '').replace('\t', ' ').replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def strip_tags(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'</(p|li|div|h\d|td|th|dt|dd|span|section|a|aside|figure|header)>', lambda m: ' ' if m.group(1) in ('p', 'li', 'div', 'td', 'th', 'dt', 'dd', 'section', 'aside') or m.group(1).startswith('h') else '', s)
    s = re.sub(r'<[^>]+>', '', s)
    return norm(s)


d = docx.Document(sys.argv[1])
paras = []
for el in d.element.body.iterchildren():
    for p in (el.iter(qn('w:p')) if el.tag == qn('w:tbl') else [el]):
        t = norm(''.join((x.text or '') if x.tag == qn('w:t') else ' ' for x in p.iter() if x.tag in (qn('w:t'), qn('w:tab'))))
        if t and not re.match(r'\[IMAGE \d{3}\]', t):
            paras.append(t)


def check(name, text):
    flat = re.sub(r'\s+', '', text).lower()
    miss = []
    for p in paras:
        key = re.sub(r'\s+', '', p).lower()
        # labels the layout splits off (e.g. "Pair:" rows, "RECIPE 001", "Recipes 1–15") are checked piecewise
        if key in flat:
            continue
        pieces = [re.sub(r'\s+', '', x).lower() for x in re.split(r'(?:Pair:|Serve:|Make ahead:|\s{2,}|·)', p) if x.strip()]
        if pieces and all(x in flat for x in pieces):
            continue
        miss.append(p)
    print(f'{name}: {len(paras) - len(miss)}/{len(paras)} manuscript paragraphs found verbatim')
    for m in miss[:30]:
        print('   MISSING:', m[:160])
    return miss


html_text = strip_tags(open(sys.argv[2]).read())
check('print HTML', html_text)

if len(sys.argv) > 4:
    z = zipfile.ZipFile(sys.argv[4])
    et = ' '.join(strip_tags(z.read(n).decode()) for n in z.namelist() if n.endswith('.xhtml') and not n.endswith('nav.xhtml'))
    check('EPUB', et)

pdf = subprocess.run(['pdftotext', sys.argv[3], '-'], capture_output=True, text=True).stdout
def words(s):
    s = s.replace('­', '').lower()
    return re.findall(r"[a-z0-9½¼¾⅓⅔⅛]+", s)
mc = collections.Counter(w for p in paras for w in words(p))
pc = collections.Counter(words(pdf))
short = {w: (c, pc[w]) for w, c in mc.items() if pc[w] < c}
print(f'PDF word check: {len(mc)} distinct manuscript words, {len(short)} under-represented')
for w, (a, b) in sorted(short.items(), key=lambda kv: kv[1][1] - kv[1][0])[:40]:
    print(f'   {w}: manuscript {a}, pdf {b}')
