"""converters between data types
"""
import os.path
from abc import ABC, abstractmethod
from enum import Enum
import glob
import logging
from pathlib import Path

# local
from py4ami.ami_gui import Gutil
from py4ami.ami_pdf import AmiPage
from py4ami.ami_project import CProject

logger = logging.getLogger(os.path.basename(__file__))


# apply methods 1:1 input-output
class ConvType(Enum):
    PDF2TXT = "pdf2txt"
    PDF2SVG = "pdf2svg"
    SVG2PAGE = "svg2page"
    TXT2PARA = "txt2para"
    TXT2SENT = "txt2sent"
    XML2HTML = "xml2html"
    XML2SECT = "xml2sect"
    XML2TXT = "xml2txt"

    @classmethod
    def list_values(cls):
        """These are the string values used in our programs"""
        return list(map(lambda c: c.value, cls))

    @classmethod
    def list_names(cls):
        return list(map(lambda c: c.name, cls))


class IOArity(Enum):
    A1_1 = "1_1"
    A1_N = "1_n"
    AN_1 = "n_1"


class AmiConverter(ABC):

    def __init__(self, infile_type=None, outfile_type=None, ctree_indir=None, ctree_outdir=None, io_arity=IOArity.A1_1,
                 cproject=None):
        self.infile_type = infile_type
        self.ctree_indir = ctree_indir
        self.outfile_type = outfile_type
        self.ctree_outdir = ctree_outdir
        self.io_arity = io_arity

        self.cproject = cproject
        self.current_ctree = None

    def iterate_cproject(self, cproject=None):
        if cproject:
            self.cproject = CProject(cproject)
            ctrees = self.cproject.get_ctrees()
            for ctree in ctrees:
                print(f"ctree {ctree}")
                self.current_ctree = ctree
                self.read_and_convert()

    def create_infile_list(self, infile):
        infiles = []
        if not infile:
            if self.current_ctree:
                indir = Path(self.current_ctree.dirx, self.ctree_indir)
                # this is a hack because root_dir is only Python 3.10
                infiles = glob.glob(f"{indir}/{self.infile_type}", recursive=False)
        else:
            infiles = [infile]

        return infiles

    def read_and_convert(self, infile=None, outfile=None):

        pretty_print = True
        use_lines = True
        rotated_text = False

        infiles = self.create_infile_list(infile)

        for infile in infiles:
            outfile = self.make_outfile_name(infile)
            print(f" in {infile} out {outfile}")
            self.read_write_file(infile, outfile, pretty_print=pretty_print, rotated_text=rotated_text,
                                 use_lines=use_lines)

        self.read_write_file(infile, outfile, pretty_print=pretty_print, rotated_text=rotated_text, use_lines=use_lines)

    @abstractmethod
    def read_write_file(self, infile, outfile, **flags):
        pass

    def make_outfile_name(self, infile):
        """creates outfile name from infile using per-converter flags
        possible approaches are:
        * outfile in same directory
        * outfile in sibling directory of parent (e.g. svg/foo1.svg => html/foo1.html
        * child directory bar/foo.pdf => bar/pdf/foo1.svg, foo2.svg

        Currently only siblings are supported
        infile_type="svg", outfile_type="html", ctree_indir="svg", ctree_outdir="html ==>
        infile_type is in_suffix
        outfile_type is out_suffix
        ctree_indir is parent stem of infile
        ctree_outdir is parent stem of outfile

        """
        # sibling directories
        if self.ctree_indir and self.ctree_outdir:
            outdir = Path(Path(infile).parent.parent, self.ctree_outdir)
            outfile = Path(outdir, Path(infile).stem + "." + self.outfile_type)
            print(f"out {outfile}")
        else:
            raise ValueError(f"Cannot create outfile name for {infile}")
        return outfile

    @classmethod
    def get_converter(cls, name: ConvType):
        pass


class Pdf2SvgConverter(AmiConverter):

    def __init__(self):
        super().__init__(infile_type="pdf", outfile_type="svg", ctree_indir=".", ctree_outdir="svg_dir",
                         io_arity=IOArity.A1_N)

    def read_write_file(self, infile, outfile, **flags):

        """ converts PDF to SVG

         """

        input_dir = "foo"
        inputname = "fulltext.pdf"
        args = ["ami", "-p", input_dir, "--inputname", inputname, "pdfbox"]
        try:
            stdout_lines, _ = Gutil.run_subprocess_get_lines(args)
        except Exception as e:
            raise Exception(f"{e} ami3 must be installed")


class Page2SectConverter(AmiConverter):

    def __init__(self):
        super().__init__(infile_type="*.html", outfile_type="html", ctree_indir="page", ctree_outdir="sect",
                         io_arity=IOArity.A1_1)

    def read_write_file(self, infile, outfile, pretty_print=True, rotated_text=False, use_lines=False):
        try:
            # ami_page = AmiPage.create_page_from_svg(infile, rotated_text=rotated_text)
            ami_sect = AmiSect.create_sect_from_page(infile)
            ami_sect.write_html(outfile)
        except Exception as e:
            raise Exception(f'failed to convert because {e}')


class Svg2PageConverter(AmiConverter):

    def __init__(self):
        super().__init__(infile_type="*.svg", outfile_type="html", ctree_indir="svg", ctree_outdir="page",
                         io_arity=IOArity.A1_1)

    def read_write_file(self, infile, outfile, pretty_print=True, rotated_text=False, use_lines=False):
        try:
            ami_page = AmiPage.create_page_from_svg(infile, rotated_text=rotated_text)
            ami_page.write_html(outfile, pretty_print=pretty_print, use_lines=use_lines)
        except Exception as e:
            raise Exception(f'failed to convert because {e}')


class Xml2HtmlConverter(AmiConverter):

    def __init__(self):
        super().__init__(infile_type="svg", outfile_type="html", ctree_indir="svg", ctree_outdir="html")

    def read_write_file(self, infile, outfile, **flags):
        raise NotImplementedError("Xml2Html NYI")


class Converters:
    converter_dict = {
        ConvType.PDF2TXT.value: None,
        ConvType.PDF2SVG.value: Pdf2SvgConverter,
        ConvType.SVG2PAGE.value: Svg2PageConverter,
        ConvType.TXT2PARA.value: None,
        ConvType.TXT2SENT.value: None,
        ConvType.XML2HTML.value: Xml2HtmlConverter,
        ConvType.XML2SECT.value: None,
        ConvType.XML2TXT.value: None,

    }

    @classmethod
    def get_converter(cls, value):
        return cls.converter_dict.get(value)
