import logging
from pyami.pdfreader import PdfReader

logger = logging.getLogger("test_pdf")

def test_read_pdf():
    pdfReader = PdfReader()
    pdfReader.read_and_convert("/Users/pm286/projects/openDiagram/physchem/liion/PMC7040616/fulltext.pdf");

