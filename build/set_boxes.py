"""Set TrimBox/BleedBox for a KDP interior with 0.125in bleed on outside/top/bottom edges.
Recto (odd) pages: spine on the left; verso (even) pages: spine on the right."""
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
r = PdfReader(sys.argv[1]); w = PdfWriter(clone_from=r)
B = 9  # 0.125in in points
for i, p in enumerate(w.pages):
    W, H = float(p.mediabox.width), float(p.mediabox.height)
    if i % 2 == 0:   # page 1, 3, ... recto
        trim = RectangleObject([0, B, W - B, H - B])
    else:
        trim = RectangleObject([B, B, W, H - B])
    p.trimbox = trim
    p.bleedbox = RectangleObject([0, 0, W, H])
w.add_metadata({'/Title': 'The First-Try Edible Candle Cookbook', '/Author': 'Margot Ellery'})
w.write(sys.argv[2])
