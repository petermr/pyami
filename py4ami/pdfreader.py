import logging

from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from pdfminer3.image import ImageWriter
import io

from pathlib import Path

logging.debug("loading pdfreader.py")


# https://stackoverflow.com/questions/56494070/how-to-use-pdfminer-six-with-python-3

class PdfReader:
    """not fully implemented or tested"""
    logger = logging.getLogger("pdfreader")

    def __init__(self):
        self.text = None

    @classmethod
    def read_and_convert(cls, file):
        """ converst a PDF path (to text)

        Args:
            file ([str]): filename
         """

        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        image_dir = Path('/Users/pm286/misc/images')
        image_writer = ImageWriter(image_dir)
        layout_params = LAParams()
        converter = TextConverter(resource_manager, fake_file_handle,
                                  codec='utf-8',
                                  laparams=layout_params,
                                  imagewriter=image_writer)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        print(f" ====== PDF FILE {file} =====")
        with open(file, 'rb') as fh:
            for i, page in enumerate(PDFPage.get_pages(fh,
                                                       caching=True,
                                                       check_extractable=True)):
                page_interpreter.process_page(page)
                print(f"=================== page {i + 1}=================")

            text = fake_file_handle.getvalue()

        # close open handles
        converter.close()
        fake_file_handle.close()

        """
        > pdf2txt.py [-P password] [-o output] [-t text|html|xml|tag]
             [-O output_dir] [-c encoding] [-s scale] [-R rotation]
             [-Y normal|loose|exact] [-p pagenos] [-m maxpages]
             [-S] [-C] [-n] [-A] [-V]
             [-M char_margin] [-L line_margin] [-W word_margin]
             [-F boxes_flow] [-d]
             input.pdf ...
-P password : PDF password.
-o output : Output path name.
-t text|html|xml|tag : Output type. (default: automatically inferred from the output path name.)
-O output_dir : Output directory for extracted images.
-c encoding : Output encoding. (default: utf-8)
-s scale : Output scale.
-R rotation : Rotates the page in degree.
-Y normal|loose|exact : Specifies the layout mode. (only for HTML output.)
-p pagenos : Processes certain pages only.
-m maxpages : Limits the number of maximum pages to process.
-S : Strips control characters.
-C : Disables resource caching.
-n : Disables layout analysis.
-A : Applies layout analysis for all texts including figures.
-V : Automatically detects vertical writing.
-M char_margin : Speficies the char margin.
-W word_margin : Speficies the word margin.
-L line_margin : Speficies the line margin.
-F boxes_flow : Speficies the box flow ratio.
-d : Turns on Debug output.

        """
        print(f"\n......\n{text[:100]}\n...\n{text[-100:]}\n......\n")
        return text


def main():
    """[main usually for testing
    """
    pass


if __name__ == "__main__":
    main()


# this may be obsolete
def temp():
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open('/storage/emulated/0/Download/Rick-Riordan-The-Tyrants-Tomb-The-Trials-of-Apollo-4.pdf', 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()

    print(text)

    pdf_resource_manager = PDFResourceManager()
    converted_text = io.StringIO()
    layout_params = LAParams()
    imageWriter = ImageWriter('pathToSaveImages/..')
    converter = TextConverter(pdf_resource_manager, converted_text, codec='utf-8', laparams=layout_params,
                              imagewriter=imageWriter)
class Pdf2SvgReader:
    logger = logging.getLogger("pdf2svgreader")

    def __init__(self):
        self.text = None

    @classmethod
    def read_and_convert(cls, file):
        """ converst a PDF path (to text)

        needs ami3 jar installed
        Args:
            file ([str]): filename
         """

        # run ami3 here
        raise Exception("ami3 must be installed")

