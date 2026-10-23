"""HTML -> PDF with WeasyPrint (fonts embedded/subset, no crop marks)."""
import logging, sys
import weasyprint
logging.getLogger('weasyprint').setLevel(logging.ERROR)
logging.getLogger('fontTools').setLevel(logging.ERROR)
src, dst = sys.argv[1], sys.argv[2]
doc = weasyprint.HTML(src).render()
print('pages', len(doc.pages))
doc.write_pdf(dst, pdf_variant=None)
