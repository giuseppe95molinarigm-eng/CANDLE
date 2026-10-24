"""Render selected EPUB documents in Chromium at phone/tablet widths and several font sizes."""
import os, sys, zipfile, tempfile
from playwright.sync_api import sync_playwright
epub, outdir = sys.argv[1], sys.argv[2]
docs = sys.argv[3].split(',')
os.makedirs(outdir, exist_ok=True)
tmp = tempfile.mkdtemp()
zipfile.ZipFile(epub).extractall(tmp)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for w, h, label in [(390, 844, 'phone'), (800, 1280, 'tablet')]:
        for fs in (100, 160):
            pg = b.new_page(viewport={'width': w, 'height': h})
            for d in docs:
                pg.goto('file://' + os.path.join(tmp, 'OEBPS/text', d))
                pg.add_style_tag(content=f'html {{ font-size: {fs}% }}')
                pg.screenshot(path=os.path.join(outdir, f'{label}_{fs}_{d.replace(".xhtml","")}.png'), clip={'x': 0, 'y': 0, 'width': w, 'height': min(3 * h, pg.evaluate('document.body.scrollHeight'))}, full_page=True)
            pg.close()
    b.close()
print('ok')
