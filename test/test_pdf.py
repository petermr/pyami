import argparse
import unittest
import sys
from io import BytesIO, StringIO
from pathlib import Path
from typing import Container

import lxml
import lxml.etree
import lxml.html
from pdfminer.converter import TextConverter, XMLConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

"""NOTE REQUIRES LATEST pdfplumber"""
import pdfplumber

# local
from py4ami.ami_pdf import SVG_NS, SVGX_NS
from py4ami.ami_pdf import STYLE, AmiPage, X, Y, FILL, STROKE, FONT_FAMILY, FONT_SIZE, HtmlUtil, SORT_XY
from test.resources import Resources
from py4ami.pyamix import PyAMI

H_TABLE = "table"
H_THEAD = "thead"
H_TBODY = "tbody"
H_TR = "tr"
H_TH = "th"
H_TD = "td"

# class PDFTest:

FINAL_DRAFT_DIR = "/Users/pm286/projects/readable_climate_reports/ipcc/dup/finalDraft/svg"  # PMR only
PAGE_9 = Path(Resources.CLIMATE_10_SVG_DIR, "fulltext-page.9.svg")
PAGE_6 = Path(Resources.CLIMATE_10_SVG_DIR, "fulltext-page.6.svg")
CURRENT_RANGE = range(1, 20)
# CHAPTER_RANGE = range(1, 200)
CLIMATE_10_HTML_DIR = Path(Resources.TEMP_CLIMATE_10_PROJ_DIR, "html")

# FULL_TEMP_DIR = Path(Path(__file__).parent.parent, "temp", "full")

PMC1421 = Path(Resources.RESOURCES_DIR, "projects", "liion4", "PMC4391421", "fulltext.pdf")

IPCC_DIR = Path(Resources.TEST_RESOURCES_DIR, "ipcc")
IPCC_GLOSS_DIR = Path(IPCC_DIR, "glossary")
IPCC_GLOSSARY = Path(IPCC_GLOSS_DIR, "IPCC_AR6_WGIII_Annex-I.pdf")
IPCC_CHAP6_DIR = Path(IPCC_DIR, "Chapter06")
IPCC_CHAP6_PDF = Path(IPCC_CHAP6_DIR, "fulltext.pdf")


def debug_page_properties(page):
    print(f"\n\n======page: {page.page_number} ===========")
    print_words(page)
    print_lines(page)
    print_rects(page, debug=False)
    print_curves(page)
    print_images(page)
    print_tables(page)
    print_hyperlinks(page)
    print_annots(page)


def print_words(page):
    print(f"words {len(page.extract_words())}", end=" | ")


def print_lines(page):
    if (n_line := len(page.lines)) > 0:
        print(f"lines {n_line}", end=" | ")


def print_rects(page, debug=False):
    if n_rect := len(page.rects) > 0:
        print(f"rects {n_rect}", end=" | ")
        if debug:
            for rect in page.rects[:PDFTest.MAX_RECT]:
                print(f"rect (({rect['x0']},{rect['x1']}),({rect['y0']},{rect['y1']})) ")


def print_curves(page):
    if n_curve := len(page.curves) > 0:
        print(f"curves {n_curve}", end=" | ")
        for curve in page.curves[:PDFTest.MAX_CURVE]:
            print(f"keys: {curve.keys()}")
            print(f"curve {curve['points']}")


def print_images(page):
    write_image = True
    resolution = 400  # may be better
    from pdfminer.image import ImageWriter
    from pdfminer.layout import LTImage
    if n_image := len(page.images) > 0:
        print(f"images {n_image}", end=" | ")
        for i, image in enumerate(page.images[:PDFTest.MAX_IMAGE]):
            print(f"image: {type(image)}: {image.values()}")

            path = Path(Resources.TEMP_DIR, "images")
            if not path.exists():
                path.mkdir()
            if isinstance(image, LTImage):
                imagewriter = ImageWriter(Path(path, f"image{i}.png"))
                imagewriter.export_image(image)
            page_height = page.height
            image_bbox = (image['x0'], page_height - image['y1'], image['x1'], page_height - image['y0'])
            print(f"image: {image_bbox}")

            cropped_page = page.crop(image_bbox)  # crop screen display (may have overwriting text)
            image_obj = cropped_page.to_image(resolution=resolution)
            path1 = Path(path, f"image_{page.page_number}_{i}_{format_bbox(image_bbox)}.png")
            if write_image:
                image_obj.save(path1)
                print(f" wrote image {path1}")
            continue

            # for p in pdf.pages:
            #     for obj in p.layout:
            #         if isinstance(obj, LTImage):
            #             imagewriter.export_image(obj)


def format_bbox(bbox: tuple):
    return f"{int(bbox[0])}_{int(bbox[2])}_{int(bbox[1])}_{int(bbox[3])}"


def print_hyperlinks(page):
    if n_hyper := len(page.hyperlinks) > 0:
        print(f"hyperlinks {n_hyper}", end=" | ")
        for hyperlink in page.hyperlinks:
            print(f"hyperlink {hyperlink.values()}")


def print_annots(page):
    """Prints annots

    Here's the output of one (it's a hyperlink)
    annot: dict_items(
[
    ('page_number', 4),
    ('object_type', 'annot'),
    ('x0', 80.75),
    ('y0', 698.85),
    ('x1', 525.05),
    ('y1', 718.77),
    ('doctop', 2648.91),
    ('top', 123.14999999999998),
    ('bottom', 143.06999999999994),
    ('width', 444.29999999999995),
    ('height', 19.91999999999996),
    ('uri', None),
    ('title', None),
    ('contents', None),
    ('data',
        {'BS': {'W': 0},
         'Dest': [<PDFObjRef:7>, /'XYZ', 69, 769, 0],
         'F': 4,
         'Rect': [80.75, 698.85, 525.05, 718.77],
         'StructParent': 3,
         'Subtype': /'Link'
         }
    )
]
)
    and there are 34 (in a TableOfContents) and they work

    """
    if n_annot := len(page.annots) > 0:
        print(f"annots {n_annot}", end=" | ")
        for annot in page.annots:
            print(f"annot: {annot.items()}")



# ==============================

def make_full_draft_html(pretty_print, use_lines, rotated_text=False):
    """
    reads SVG output from ami3/pdfbox and converts to HTML
    used by several tests at present and will be intergrated
    :param pretty_print: pretty print the HTML. Warning may introduce whitespace
    :param use_lines: output is CompositeLines. Not converted into running text (check)
    :param rotated_text: include/ignore tex# ts with non-zero @rotateDegress attribute
    """
    if not Path(FINAL_DRAFT_DIR, f"fulltext-page.2912.svg").exists():
        raise Exception("must have SVG from ami3")
    for page_index in CURRENT_RANGE:
        page_path = Path(FINAL_DRAFT_DIR, f"fulltext-page.{page_index}.svg")
        html_path = Path(Resources.CLIMATE_10_HTML_TEMP_DIR, f"page.{page_index}.html")
        if not Resources.CLIMATE_10_HTML_TEMP_DIR.exists():
            Resources.CLIMATE_10_HTML_TEMP_DIR.mkdir()
        ami_page = AmiPage.create_page_from_svg(page_path, rotated_text=rotated_text)
        ami_page.write_html(html_path, pretty_print, use_lines)


def convert_pdf(
        path: str,
        fmt: str = "text",
        codec: str = "utf-8",
        password: str = "",
        maxpages: int = 0,
        caching: bool = True,
        pagenos: Container[int] = set(),
) -> str:
    """Summary
    Parameters
    ----------
    path : str
        Path to the pdf file
    fmt : str, optional
        Format of output, must be one of: "text", "html", "xml".
        By default, "text" format is used
    codec : str, optional
        Encoding. By default "utf-8" is used
    password : str, optional
        Password
    maxpages : int, optional
        Max number of pages to convert. By default is 0, i.e. reads all pages.
    caching : bool, optional
        Caching. By default is True
    pagenos : Container[int], optional
        Provide a list with numbers of pages to convert
    Returns
    -------
    str
        Converted pdf file
    """
    """from pdfminer/pdfplumber"""
    device, interpreter, retstr = create_interpreter(fmt)

    fp = open(path, "rb")
    for page in PDFPage.get_pages(
            fp,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True,
    ):
        interpreter.process_page(page)

    text = retstr.getvalue().decode()
    fp.close()
    device.close()
    retstr.close()
    return text


def create_interpreter(fmt, codec: str = "UTF-8"):
    """creates a PDFPageInterpreter
    :format: "text, "xml", "html"
    :codec: default UTF-8
    :return: (device, interpreter, retstr) device must be closed after reading, retstr
    contains resultant str

    Typical use:
    device, interpreter, retstr = create_interpreter(format)

    fp = open(path, "rb")
    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)

    text = retstr.getvalue().decode()
    fp.close()
    device.close()
    retstr.close()
    return text

    TODO convert to context manager?
    """
    rsrcmgr = PDFResourceManager()
    retstr = BytesIO()
    laparams = LAParams()
    converters = {"text": TextConverter, "html": HTMLConverter, "xml": XMLConverter}
    converter = converters.get(fmt)
    if not converter:
        raise ValueError(f"provide format, {converters.keys()}")
    device = converter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # if format == "text":
    #     device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # elif format == "html":
    #     device = HTMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # elif format == "xml":
    #     device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # else:
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    return device, interpreter, retstr


def make_html_dir():
    html_dir = Path(Resources.TEMP_DIR, "html")
    if not html_dir.exists():
        html_dir.mkdir()
    return html_dir


def print_tables(page, odir=Resources.TEMP_DIR):
    tables = page.find_tables()

    if n_table := len(tables) > 0:
        print(f"tables {n_table}", end=" | ")
        print(f"table_dir {tables[0].__dir__()}")
        for i, table in enumerate(tables[:PDFTest.MAX_TABLE]):
            h_table = lxml.etree.Element(H_TABLE)
            h_thead = lxml.etree.SubElement(h_table, H_THEAD)
            h_tbody = lxml.etree.SubElement(h_table, H_TBODY)
            table_lists = table.extract()  # essentially a list of lists
            for table_row in table_lists:
                h_row = lxml.etree.SubElement(h_tbody, H_TR)
                for cell_value in table_row:
                    h_td = lxml.etree.SubElement(h_row, H_TD)
                    h_td.text = str(cell_value)
            h_str = lxml.etree.tostring(h_table, encoding='UTF-8', xml_declaration=False)
            table_file = Path(odir, f"table_{i + 1}.html")
            with open(table_file, "wb") as f:
                f.write(h_str)
                print(f"wrote {table_file}")

            # print(f"table: rows: {len(table.rows)}")
            # for row in table.rows[:PDFTest.MAX_ROW]:
            #     # print("row/cells: ", end="")
            #     print(f"row {row}")
            #     # cell is a tuple (x, y) - where is the content?
            #     # print(f"cell {type(row.cells[0])}, end="")
            #     # for cell in row.cells:
            #     #     print(f"[{cell}]", end="")
            #     # print("")


# def print_hyperlinks(page):
#     if n_hyper := len(page.hyperlinks) > 0:
#         print(f"hyperlinks {n_hyper}", end=" | ")
#         for hyperlink in page.hyperlinks:
#             print(f"hyperlink {hyperlink.values()}")
#
#
# def print_annots(page):
#     if n_annot := len(page.annots) > 0:
#         print(f"annots {n_annot}", end=" | ")
#

class CSSStyle:
    BOLD = "Bold"
    BOTTOM = "bottom"
    DOT_B = ".B"
    FONT_FAMILY = "font-family"
    FONT_SIZE = "font-size"
    LEFT = "left"
    PX = "px"
    STYLE = "style"
    TOP = "top"
    WIDTH = "width"

    def __init__(self):
        self.name_value_dict = dict()

    def __str__(self):
        s = ""
        for k, v in self.name_value_dict.items():
            s += f"{k}:{v}; "
        s = s.strip()
        return s

    @classmethod
    def create_css_style(cls, elem):
        css_style = CSSStyle()
        style_attval = elem.get(CSSStyle.STYLE)
        css_style.name_value_dict = cls.create_dict_from_string(style_attval)
        return css_style

    @classmethod
    def create_dict_from_string(cls, style_attval):
        name_value_dict = dict()
        if style_attval:
            styles = style_attval.split(";")
            for style in styles:
                if len(style.strip()) > 0:
                    ss = style.split(":")
                    name = ss[0].strip()
                    if name in name_value_dict:
                        raise KeyError(f"{name} duplicated in CSS: {style_attval}")
                    name_value_dict[name] = ss[1].strip()
        return name_value_dict

    def remove(self, name):
        if type(name) is list:
            for n in name:
                self.remove(n)
        elif name in self.name_value_dict:
            self.name_value_dict.pop(name, None)

    def apply_to(self, elem):
        css_str = self.generate_css_value()
        elem.attrib["style"] = css_str

    def generate_css_value(self):
        s = ""
        for key in self.name_value_dict:
            val = self.name_value_dict[key]
            s += key + ": " + val + "; "
        return s.strip()

    def attval(self, name):
        return self.name_value_dict.get(name) if self.name_value_dict else None

    @property
    def font_family(self):
        return self.attval(CSSStyle.FONT_FAMILY)

    @property
    def top(self):
        return self.get_numeric_attval(CSSStyle.TOP)

    @property
    def font_size(self):
        size = self.get_numeric_attval(CSSStyle.FONT_SIZE)
        return size

    @property
    def bottom(self):
        return self.get_numeric_attval(CSSStyle.BOTTOM)

    @property
    def left(self):
        return self.get_numeric_attval(CSSStyle.LEFT)

    @property
    def width(self):
        return self.get_numeric_attval(CSSStyle.WIDTH)

    def get_numeric_attval(self, name):
        value = self.attval(name)
        if not value:
            return None
        value = value[:-2] if value.endswith(CSSStyle.PX) else value
        try:
            return float(value)
        except Exception:
            return None

    def is_bold_name(self):
        """Heuristic using font-name
        :return: True if name contains "Bold" or ".B" or .."""
        fontname = self.font_family
        return self.BOLD in fontname or fontname.endswith(self.DOT_B) if fontname else False

class PDFTest(unittest.TestCase):
    MAX_PAGE = 5
    MAX_ITER = 20

    def test_pdfbox_output_exists(self):
        """check CLIMATE dir exists
        """
        # assert str(Resources.CLIMATE_10_DIR) == "/Users/pm286/workspace/pyami/test/resources/svg", f"resources {Resources.CLIMATE_10_DIR}"
        assert Resources.CLIMATE_10_PROJ_DIR.exists(), f"{Resources.CLIMATE_10_PROJ_DIR} should exist"

    def test_findall_svg_and_find_texts(self):
        """find climate10_:text elements
        """
        assert PAGE_9.exists(), f"{PAGE_9} should exist"
        page9_elem = lxml.etree.parse(str(PAGE_9))
        texts = page9_elem.findall(f"//{{{SVG_NS}}}text")
        assert len(texts) == 108

    def test_get_text_attribs(self):
        """find various SVG attributes, including 'style'
        """
        ami_page = AmiPage.create_page_from_svg(PAGE_9)
        # <climate10_:text> element
        text0 = ami_page.get_svg_text(0)
        assert text0.svg_text_elem.tag == f"{{{SVG_NS}}}text"
        # single Y-coord
        assert text0.svg_text_elem.attrib.get(Y) == '44.76'
        # list of X-coords
        assert text0.svg_text_elem.attrib.get(X) == \
               '72.0,79.201,84.721,90.241,96.961,104.162,111.363,117.482,124.798,127.288,258.242,263.762,268.' \
               '802,276.601,284.401,288.841,292.202,297.241,299.761,303.001,308.041,311.402,313.921,319.441,' \
               '324.481,327.241,330.001,334.441,339.481,347.28,351.601,356.641,361.081,364.442,368.28,370.77,' \
               '448.08,451.439,456.96,463.563,470.167,472.687,480.006,486.61,491.651,494.171,503.533,510.718,' \
               '513.238,516.594,519.951,523.307'
        # list of character-widths (from publisher) (multiply by font-size to get pixels)
        assert text0.svg_text_elem.attrib.get(f"{{{SVGX_NS}}}width") == \
               '0.72,0.56,0.56,0.67,0.72,0.72,0.61,0.72,0.25,0.55,0.56,0.5,0.78,0.78,0.44,0.33,0.5,0.25,0.33,' \
               '0.5,0.33,0.25,0.56,0.5,0.28,0.28,0.44,0.5,0.78,0.44,0.5,0.44,0.33,0.39,0.25,0.55,0.33,0.56,' \
               '0.67,0.67,0.25,0.72,0.67,0.5,0.25,0.94,0.72,0.25,0.33,0.33,0.33,0.25'
        # style (dict-like collection of name-value pairs
        assert text0.svg_text_elem.get(STYLE) == \
               'fill:rgb(0,0,0);font-family:TimesNewRomanPSMT;font-size:9.96px;stroke:none;'
        # text-content without tags
        text_content = text0.get_text_content()
        assert text_content == "APPROVED Summary for Policymakers IPCC AR6 WG III "
        assert len(text_content) == 50  # some spaces have been elided??

    def test_get_text_attrib_vals(self):
        """more attributes and convenience methods"""
        ami_page = AmiPage.create_page_from_svg(PAGE_9)
        # <climate10_:text> element
        ami_text0 = ami_page.get_svg_text(0)
        x_coords = ami_text0.get_x_coords()
        assert x_coords == [
            72.0, 79.201, 84.721, 90.241,
            96.961, 104.162, 111.363, 117.482, 124.798, 127.288, 258.242, 263.762, 268.802,
            276.601, 284.401, 288.841, 292.202, 297.241, 299.761,
            303.001, 308.041, 311.402, 313.921, 319.441, 324.481, 327.241, 330.001,
            334.441, 339.481, 347.28, 351.601, 356.641, 361.081, 364.442,
            368.28, 370.77, 448.08, 451.439, 456.96, 463.563, 470.167,
            472.687, 480.006, 486.61, 491.651, 494.171, 503.533, 510.718, 513.238, 516.594, 519.951, 523.307]
        assert len(x_coords) == 52

        widths = ami_text0.get_widths()
        assert widths == [
            0.72, 0.56, 0.56, 0.67, 0.72, 0.72, 0.61,
            0.72, 0.25, 0.55, 0.56, 0.5, 0.78, 0.78, 0.44, 0.33, 0.5, 0.25, 0.33, 0.5, 0.33,
            0.25, 0.56, 0.5, 0.28, 0.28, 0.44, 0.5, 0.78, 0.44, 0.5, 0.44, 0.33,
            0.39, 0.25, 0.55, 0.33, 0.56, 0.67, 0.67, 0.25, 0.72, 0.67, 0.5, 0.25, 0.94, 0.72, 0.25, 0.33, 0.33,
            0.33, 0.25
        ]
        assert len(widths) == 52

        # SVG style dict from SVG@style attribute
        style_dict = ami_text0.extract_style_dict_from_svg()
        # assert style_dict == {'fill': 'rgb(0,0,0)',\n 'font-family': 'TimesNewRomanPSMT',\n 'font-size': '9.96px',\n 'stroke': 'none'}
        assert style_dict[FILL] == 'rgb(0,0,0)'
        assert style_dict[FONT_FAMILY] == 'TimesNewRomanPSMT'
        assert style_dict[FONT_SIZE] == '9.96px'
        assert style_dict[STROKE] == 'none'
        assert ami_text0.get_font_size() == 9.96

    def test_create_text_lines_page6(self):
        """creation of AmiPage from SVG page and creation of text spans"""
        page = AmiPage.create_page_from_svg(PAGE_6)
        page.create_text_spans(sort_axes=SORT_XY)
        assert 70 >= len(page.text_spans) >= 60

    def test_create_html(self):
        """
        Test 10 pages
        """
        pretty_print = True
        use_lines = True
        for page_index in range(1, 9):
            page_path = Path(Resources.CLIMATE_10_SVG_DIR, f"fulltext-page.{page_index}.svg")
            html_path = Path(Resources.CLIMATE_10_HTML_TEMP_DIR, f"page.{page_index}.html")
            if not Resources.CLIMATE_10_HTML_TEMP_DIR.exists():
                Resources.CLIMATE_10_HTML_TEMP_DIR.mkdir()
            ami_page = AmiPage.create_page_from_svg(page_path)
            ami_page.write_html(html_path, pretty_print, use_lines)
            assert html_path.exists(), f"{html_path} exists"

    def test_create_html_in_selection(self):
        """
        Test 10 pages
        """
        pretty_print = True
        use_lines = True
        # selection = range(1, 2912)
        page_selection = range(1, 50)
        counter = 0
        counter_tick = 20
        for page_index in page_selection:
            if counter % counter_tick == 0:
                print(f".", end="")
            page_path = Path(FINAL_DRAFT_DIR, f"fulltext-page.{page_index}.svg")
            html_path = Path(Resources.CLIMATE_10_HTML_TEMP_DIR, f"page.{page_index}.html")
            if not Resources.CLIMATE_10_HTML_TEMP_DIR.exists():
                Resources.CLIMATE_10_HTML_TEMP_DIR.mkdir()
            ami_page = AmiPage.create_page_from_svg(page_path, rotated_text=False)
            ami_page.write_html(html_path, pretty_print, use_lines)
            counter += 1
            assert html_path.exists(), f"{html_path} exists"

    def test_create_chapters(self):
        pretty_print = True
        use_lines = True
        make_full_draft_html(pretty_print, use_lines)
        selection = CURRENT_RANGE
        for page_index in selection:
            html_path = Path(Resources.CLIMATE_10_HTML_TEMP_DIR, f"page.{page_index}.html")
            with open(html_path, "r") as h:
                xml = h.read()
            root = lxml.etree.fromstring(xml)
            spans = root.findall("./body/p/span")
            assert type(spans[0]) is lxml.etree._Element, f"expected str got {type(spans[0])}"
            assert len(HtmlUtil.get_text_content(spans[0])) > 0
            span = None
            chapter = ""
            # bug in parsing line 0
            if HtmlUtil.is_chapter_or_tech_summary(HtmlUtil.get_text_content(spans[0])):
                span = spans[0]
            if span is None and HtmlUtil.is_chapter_or_tech_summary(HtmlUtil.get_text_content(spans[1])):
                span = spans[1]
            if span is None:
                print(f"p:{page_index}, {HtmlUtil.get_text_content(spans[0])}, {HtmlUtil.get_text_content(spans[1])}")
            else:
                chapter = HtmlUtil.get_text_content(span)
                print("CHAP ", chapter)

    def test_svg2page(self):
        proj = Resources.CLIMATE_10_PROJ_DIR
        args = f"--proj {proj} --apply svg2page"
        PyAMI().run_command(args)

    @unittest.skip("Needs debugging")
    def test_page2chap(self):
        proj = Resources.CLIMATE_10_PROJ_DIR
        args = f"--proj {proj} --apply page2sect"
        PyAMI().run_command(args)

    def test_pdfplumber(self):
        assert PMC1421.exists(), f"{PMC1421} should exist"

        with pdfplumber.open(PMC1421) as pdf:
            first_page = pdf.pages[0]
            # print(type(first_page), first_page.__dir__())
            """
            dir: ['pdf', 'root_page', 'page_obj', 'page_number', 'rotation', 'initial_doctop', 'cropbox', 'mediabox', 
            'bbox', 'cached_properties', 'is_original', 'pages', 'width', 
            'height', 'layout', 'annots', 'hyperlinks', 'objects', 'process_object', 'iter_layout_objects', 'parse_objects', 
            'debug_tablefinder', 'find_tables', 'extract_tables', 'extract_table', 'get_text_layout', 'search', 'extract_text',
             'extract_words', 'crop', 'within_bbox', 'filter', 'dedupe_chars', 'to_image', 'to_dict', 
             'flush_cache', 'rects', 'lines', 'curves', 'images', 'chars', 'textboxverticals', 'textboxhorizontals', 
             'textlineverticals', 'textlinehorizontals', 'rect_edges', 'edges', 'horizontal_edges', 'vertical_edges', 'to_json',
              'to_csv', ]
            """
            assert first_page.page_number == 1
            assert first_page.rotation == 0
            assert first_page.initial_doctop == 0
            assert first_page.cropbox == [0, 0, 595.22, 842]
            assert first_page.mediabox == [0, 0, 595.22, 842]
            assert first_page.bbox == (0, 0, 595.22, 842)
            assert first_page.rotation == 0
            assert first_page.initial_doctop == 0
            assert first_page.cached_properties == ['_rect_edges', '_edges', '_objects', '_layout']
            assert first_page.is_original
            assert first_page.pages is None
            assert first_page.width == 595.22
            assert first_page.height == 842
            # assert first_page.layout: < LTPage(1)
            # 0.000, 0.000, 595.220, 842.000
            # rotate = 0 >
            assert first_page.annots == []
            assert first_page.hyperlinks == []
            assert first_page.find_tables() == []
            assert first_page.extract_tables() == []
            assert first_page.extract_text()[:20] == "Journal of Medicine "
            assert first_page.extract_words()[:3] == [
                {'text': 'Journal', 'x0': 319.74, 'x1': 346.2432, 'top': 37.8297, 'doctop': 37.8297, 'bottom': 46.8297,
                 'upright': True, 'direction': 1},
                {'text': 'of', 'x0': 348.2808, 'x1': 355.641, 'top': 37.8297, 'doctop': 37.8297, 'bottom': 46.8297,
                 'upright': True, 'direction': 1},
                {'text': 'Medicine', 'x0': 357.6786, 'x1': 391.08299999999997, 'top': 37.8297, 'doctop': 37.8297,
                 'bottom': 46.8297, 'upright': True, 'direction': 1}]
            assert first_page.rects == []
            assert first_page.lines == [
                {'x0': 56.7, 'y0': 793.76, 'x1': 542.76, 'y1': 793.76, 'width': 486.06, 'height': 0.0,
                 'pts': [(56.7, 793.76), (542.76, 793.76)], 'linewidth': 1, 'stroke': True, 'fill': False,
                 'evenodd': False, 'stroking_color': (0.3098, 0.24706, 0.2549, 0), 'non_stroking_color': 0,
                 'object_type': 'line', 'page_number': 1, 'top': 48.24000000000001, 'bottom': 48.24000000000001,
                 'doctop': 48.24000000000001}]

            assert first_page.curves == []
            assert first_page.images == []
            assert first_page.chars[:1] == [
                {'adv': 0.319,
                 'bottom': 46.8297,
                 'doctop': 37.8297,
                 'fontname': 'KAAHHD+Calibri,Italic',
                 'height': 9.0,
                 'matrix': (9, 0, 0, 9, 319.74, 797.4203),
                 'non_stroking_color': (0.86667, 0.26667, 1, 0.15294),
                 'object_type': 'char',
                 'page_number': 1,
                 'size': 9.0,
                 'stroking_color': None,
                 'text': 'J',
                 'top': 37.8297,
                 'upright': True,
                 'width': 2.870999999999981,
                 'x0': 319.74,
                 'x1': 322.611,
                 'y0': 795.1703,
                 'y1': 804.1703
                 },
            ]
            assert first_page.chars[0] == {'matrix': (9, 0, 0, 9, 319.74, 797.4203),
                                           'fontname': 'KAAHHD+Calibri,Italic', 'adv': 0.319,
                                           'upright': True, 'x0': 319.74, 'y0': 795.1703, 'x1': 322.611, 'y1': 804.1703,
                                           'width': 2.870999999999981, 'height': 9.0, 'size': 9.0,
                                           'object_type': 'char', 'page_number': 1,
                                           'text': 'J', 'stroking_color': None,
                                           'non_stroking_color': (0.86667, 0.26667, 1, 0.15294),
                                           'top': 37.8297, 'bottom': 46.8297, 'doctop': 37.8297}
            first_100 = first_page.extract_text()[:100]
            assert first_100.startswith("Journal of Medicine and Life Volume 7, Special Issue 3")
            assert 612 < len(first_page.extract_words()) < 616
            word0 = first_page.extract_words()[0]
            assert list(word0.keys()) == ['text', 'x0', 'x1', 'top', 'doctop', 'bottom', 'upright', 'direction']

            # too fragile
            assert first_page.edges == [
                {'x0': 56.7, 'y0': 793.76, 'x1': 542.76, 'y1': 793.76, 'width': 486.06, 'height': 0.0,
                 'pts': [(56.7, 793.76), (542.76, 793.76)], 'linewidth': 1, 'stroke': True, 'fill': False,
                 'evenodd': False, 'stroking_color': (0.3098, 0.24706, 0.2549, 0), 'non_stroking_color': 0,
                 'object_type': 'line', 'page_number': 1, 'top': 48.24000000000001, 'bottom': 48.24000000000001,
                 'doctop': 48.24000000000001, 'orientation': 'h'}]
            assert first_page.horizontal_edges == [
                {'x0': 56.7, 'y0': 793.76, 'x1': 542.76, 'y1': 793.76, 'width': 486.06, 'height': 0.0,
                 'pts': [(56.7, 793.76), (542.76, 793.76)], 'linewidth': 1, 'stroke': True, 'fill': False,
                 'evenodd': False, 'stroking_color': (0.3098, 0.24706, 0.2549, 0), 'non_stroking_color': 0,
                 'object_type': 'line', 'page_number': 1, 'top': 48.24000000000001, 'bottom': 48.24000000000001,
                 'doctop': 48.24000000000001, 'orientation': 'h'}]
            assert first_page.vertical_edges == []
            assert first_page.textboxverticals == []
            assert first_page.textboxhorizontals == []
            assert first_page.textlineverticals == []
            assert first_page.textlinehorizontals == []

            # CSV
            csv = first_page.to_csv()
            assert type(csv) is str
            rows = csv.split("\r")
            assert len(rows) == 4414
            assert rows[
                       0] == "object_type,page_number,x0,x1,y0,y1,doctop,top,bottom,width,height,adv,evenodd,fill,fontname,linewidth,matrix,non_stroking_color,pts,size,stroke,stroking_color,text,upright"
            assert rows[0].split() == [
                'object_type,page_number,x0,x1,y0,y1,doctop,top,bottom,width,height,adv,evenodd,fill,fontname,linewidth,matrix,non_stroking_color,pts,size,stroke,stroking_color,text,upright']
            assert rows[1].split() == [
                'char,1,319.74,322.611,795.1703,804.1703,37.8297,37.8297,46.8297,2.870999999999981,9.0,0.319,,,"KAAHHD+Calibri,Italic",,"(9,',
                '0,', '0,', '9,', '319.74,', '797.4203)","(0.86667,', '0.26667,', '1,', '0.15294)",,9.0,,,J,1']

            #        assert rows[1] == 'char,1,319.74,322.611,795.1703,804.1703,37.8297,37.8297,46.8297,2.870999999999981,9.0,0.319,,,"KAAHHD+Calibri,Italic",,"(9, '\n '0, 0, 9, 319.74, 797.4203)","(0.86667, 0.26667, 1, 0.15294)",,9.0,,,J,1'

            assert first_page.chars[0:1] == [
                {'adv': 0.319, 'bottom': 46.8297, 'doctop': 37.8297, 'fontname': 'KAAHHD+Calibri,Italic', 'height': 9.0,
                 'matrix': (9, 0, 0, 9, 319.74, 797.4203), 'non_stroking_color': (0.86667, 0.26667, 1, 0.15294),
                 'object_type': 'char',
                 'page_number': 1, 'size': 9.0, 'stroking_color': None, 'text': 'J', 'top': 37.8297, 'upright': True,
                 'width': 2.870999999999981, 'x0': 319.74, 'x1': 322.611, 'y0': 795.1703, 'y1': 804.1703}]

            assert type(first_page.extract_text()) is str
            for ch in first_page.chars:  # prints all text as a single line
                print(ch.get("text"), end="")

    def test_scan_document(self):
        with pdfplumber.open(PMC1421) as pdf:
            pages = list(pdf.pages)
            assert len(pages) == 5
            for page in pages:
                debug_page_properties(page)

    # See https://pypi.org/project/depdf/0.2.2/ for paragraphs?

    # https://towardsdatascience.com/pdf-text-extraction-in-python-5b6ab9e92dd

    def test_pdfminer_layout(self):
        from pdfminer.layout import LTTextLineHorizontal, LTTextBoxHorizontal
        # need to pass in laparams, otherwise pdfplumber page would not
        # have high level pdfminer layout objects, only LTChars.
        pdf = pdfplumber.open(PMC1421, laparams={})
        page = pdf.pages[0].layout
        for element in page:
            if isinstance(element, LTTextLineHorizontal):
                print(f"textlinehorizontal: ({element.bbox}): {element.get_text()}", end="")
            if isinstance(element, LTTextBoxHorizontal):
                print(f">>start_text_box")
                for text_line in element:
                    print(f"dir: {text_line.__dir__()}")
                    print(f"....textboxhorizontal: ({text_line.bbox}): {text_line.get_text()}", end="")
                print(f"<<end_text_box")

    # https://stackoverflow.com/questions/34606382/pdfminer-extract-text-with-its-font-information

    def test_pdfminer_font(self):
        """Examines every character and annotates it
        Typical:
LTPage
  LTTextBoxHorizontal                               Journal of Medicine and Life Volume 7, Special Issue 3, 2014
    LTTextLineHorizontal                            Journal of Medicine and Life Volume 7, Special Issue 3, 2014
      LTChar                   KAAHHD+Calibri,Itali J
      LTChar                   KAAHHD+Calibri,Itali o
      LTChar                   KAAHHD+Calibri,Itali u
        """
        from pathlib import Path
        from typing import Iterable, Any

        from pdfminer.high_level import extract_pages

        def show_ltitem_hierarchy(o: Any, depth=0):
            """Show location and text of LTItem and all its descendants"""
            if depth == 0:
                print('element                        fontname             text')
                print('------------------------------ -------------------- -----')

            print(
                f'{get_indented_name(o, depth):<30.30s} '
                f'{get_optional_fontinfo(o):<20.20s} '
                f'{get_optional_text(o)}'
            )

            if isinstance(o, Iterable):
                for i in o:
                    show_ltitem_hierarchy(i, depth=depth + 1)

        def get_indented_name(o: Any, depth: int) -> str:
            """Indented name of class"""
            return '  ' * depth + o.__class__.__name__

        def get_optional_fontinfo(o: Any) -> str:
            """Font info of LTChar if available, otherwise empty string"""
            if hasattr(o, 'fontname') and hasattr(o, 'size'):
                return f'{o.fontname} {round(o.size)}pt'
            return ''

        def get_optional_text(o: Any) -> str:
            """Text of LTItem if available, otherwise empty string"""
            if hasattr(o, 'get_text'):
                return o.get_text().strip()
            return ''

        path = Path(PMC1421)
        pages = list(extract_pages(path))
        # this next debugs the character_stream
        show_ltitem_hierarchy(pages[0])

    def test_read_ipcc_chapter(self):
        """read multipage document and extract properties

        """
        assert IPCC_GLOSSARY.exists(), f"{IPCC_GLOSSARY} should exist"
        max_page = PDFTest.MAX_PAGE
        # max_page = 100  # increase this if yiu want more output

        for (pdf_file, page_count) in [
            # (IPCC_GLOSSARY, 51),
            (IPCC_CHAP6_PDF, 219)
        ]:
            with pdfplumber.open(pdf_file) as pdf:
                print(f"file {pdf_file}")
                pages = list(pdf.pages)
                assert len(pages) == page_count
                for page in pages[:max_page]:
                    debug_page_properties(page)

    def test_pdfminer_html_xml_article(self):
        """runs pdfinterpreter/converter over 5-page article and creates html and xml versions"""
        maxpages = 0
        in_path = Path(PMC1421)
        outf = "pmc4121"
        out_dir = make_html_dir()

        self.convert_write("html", maxpages, out_dir, outf, in_path)
        self.convert_write("xml", maxpages, out_dir, outf, in_path)

    def test_pdfminer_html_xml_climate(self):
        """runs pdfinterpreter/converter over climate chapter and creates html and xml versions"""
        output_xml = False
        maxpages = 20
        in_path = Path(IPCC_CHAP6_PDF)
        outf = "chap6"
        out_dir = make_html_dir()

        self.convert_write("html", maxpages, out_dir, outf, in_path)
        self.convert_write("html", maxpages, out_dir, outf, in_path, flow=True)
        if output_xml:
            self.convert_write("xml", maxpages, out_dir, outf, in_path)

    def test_pdfminer_text_html_xml(self):
        # Use `pip3 install pdfminer.six` for python3
        """runs pdfinterpreter/converter over 5-page article and creates html and xml versions"""
        fmt = "html"
        maxpages = 0
        path = Path(PMC1421)
        result = convert_pdf(
            path=path,
            fmt=fmt,
            maxpages=maxpages
        )
        html_dir = make_html_dir()
        with open(Path(html_dir, f"pmc4121.{fmt}"), "w") as f:
            f.write(result)
            print(f"wrote {f.name}")

    # ==============================
    MAX_RECT = 5
    MAX_CURVE = 5
    MAX_TABLE = 5
    MAX_ROW = 10
    MAX_IMAGE = 5

    def convert_write(self, fmt, maxpages, out_dir, out_stem, in_path, flow=False):
        """
        create HTML (absolute or flowing) or XML
        :param fmt: format html/xml/text
        :param maxpages: if 0, writes all else staops at maxpages
        :param out_dir: output dir
        :param out_stem: stem of output file
        :param in_path: input file
        :param flow: remover absolute positin so text can flow
        """
        cls = PDFTest
        result = convert_pdf(path=in_path, fmt=fmt, maxpages=maxpages)
        if flow:
            tree = lxml.etree.parse(StringIO(result), lxml.etree.HTMLParser())
            result_elem = tree.getroot()
            # this is slightly tacky
            cls.remove_elem("br", result_elem)
            cls.remove_style(result_elem, [
                "position",
                # "left",
                "border",
                "writing-mode",
                "width",  # this disables flowing text
            ])
            cls.remove_empty_elements(result_elem, ["span"])
            cls.find_elements_with_style(result_elem, ".//*[@style]", "_font_size > 30", remove=True)
            result = lxml.etree.tostring(result_elem).decode("UTF-8")
            fmt = "flow.html"
        with open(Path(out_dir, f"{out_stem}.{fmt}"), "w") as f:
            f.write(result)
            print(f"wrote {f.name}")

    @classmethod
    def remove_empty_elements(cls, elem, tag):
        if tag:
            if type(tag) is list:
                for t in tag:
                    cls.remove_empty_elements(elem, t)
            else:
                xp = f".//{tag}[normalize-space(.)='' and count({tag}/*) = 0]"
                elems = elem.xpath(xp)
                for el in elems:
                    cls.remove_elem_keep_tail(el)

    @classmethod
    def remove_elem_keep_tail(cls, el):
        parent = el.getparent()
        tail = el.tail
        if tail is not None and len(tail.strip()) > 0:
            prev = el.getprevious()
            if prev is not None:
                prev.tail = (prev.tail or '') + el.tail
            else:
                parent.text = (parent.text or '') + el.tail

        parent.remove(el)

    @classmethod
    def remove_elem(cls, tag, result_elem):
        lxml.etree.strip_tags(result_elem, tag)

    @classmethod
    def remove_style(cls, elem, names):
        xpath = f".//*[@style]"
        print(f"xpath: {xpath}")
        try:
            styled_elems = elem.xpath(xpath)
        except lxml.etree.XPathEvalError as xpee:
            raise ValueError(f"Bad xpath {xpath}")

        print(f"styles {len(styled_elems)}")
        for styled_elem in styled_elems:
            css_style = CSSStyle.create_css_style(styled_elem)
            css_style.remove(names)
            css_style.apply_to(styled_elem)
            style = styled_elem.attrib["style"]

    @classmethod
    def find_elements_with_style(cls, elem, xpath, condition=None, remove=False):
        """remove all elements with style fulfilling condition
        :param elem: root element for xpath
        :param xpath: elements to scan , should normally contain the @style condition
                          if None uses
        :param condition: style condition primitive at present
                          (variable, or variable  operator value (eval is evil)
                          example "_font-size > 30" or "_position" (means has position)
        :param remove: remove these elements (not their tail)
        """
        assert elem is not None, f"must have elem"
        if xpath:
            els = elem.xpath(xpath)
        else:
            els = [elem]
        elems = []
        for el in els:
            css_style = CSSStyle.create_css_style(el)

    def test_pdfminer_style(self):
        """Examines every character and annotates it
        Typical:
LTPage
  LTTextBoxHorizontal                               Journal of Medicine and Life Volume 7, Special Issue 3, 2014
    LTTextLineHorizontal                            Journal of Medicine and Life Volume 7, Special Issue 3, 2014
      LTChar                   KAAHHD+Calibri,Itali J
      LTChar                   KAAHHD+Calibri,Itali o
      LTChar                   KAAHHD+Calibri,Itali u
        """
        from pathlib import Path
        from typing import Iterable, Any

        from pdfminer.high_level import extract_pages

        def show_ltitem_hierarchy(o: Any, depth=0):
            """Show location and text of LTItem and all its descendants"""
            if depth == 0:
                print('element                        fontname             text')
                print('------------------------------ -------------------- -----')

            print(
                f'{get_indented_name(o, depth):<30.30s} '
                f'{get_optional_fontinfo(o):<20.20s} '
                f'{get_optional_text(o)}'
            )

            if isinstance(o, Iterable):
                for i in o:
                    show_ltitem_hierarchy(i, depth=depth + 1)

        def get_indented_name(o: Any, depth: int) -> str:
            """Indented name of class"""
            return '  ' * depth + o.__class__.__name__

        def get_optional_fontinfo(o: Any) -> str:
            """Font info of LTChar if available, otherwise empty string"""
            if hasattr(o, 'fontname') and hasattr(o, 'size'):
                return f'{o.fontname} {round(o.size)}pt'
            return ''

        def get_optional_text(o: Any) -> str:
            """Text of LTItem if available, otherwise empty string"""
            if hasattr(o, 'get_text'):
                return o.get_text().strip()
            return ''

        path = Path(PMC1421)
        pages = list(extract_pages(path))
        # this next debugs the character_stream
        show_ltitem_hierarchy(pages[0])

    def test_css_parse(self):
        css_str = "height: 22; width: 34;"
        css_style = CSSStyle.create_dict_from_string(css_str)
        assert css_style
        assert "height" in css_style
        assert css_style.get("height") == "22"
        assert "width" in css_style
        assert css_style.get("width") == "34"

    def test_pdfminer_html(self):
        # Use `pip3 install pdfminer.six` for python3

        from typing import Container
        from io import BytesIO
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.converter import TextConverter, XMLConverter, HTMLConverter
        from pdfminer.layout import LAParams
        from pdfminer.pdfpage import PDFPage


        pathx = Path(PMC1421)

        result = convert_pdf(
            path=pathx,
            fmt="html",
            caching=True,
        )
        # print(f"result {result}")
        html_dir = Path(Resources.TEMP_DIR, "html")
        if not html_dir.exists():
            html_dir.mkdir()
        with open(Path(html_dir, "pmc4121.xml"), "w") as f:
            f.write(result)
            print(f"wrote {f}")

    # ==============================

def main(argv=None):
    print(f"running PDFTest main")
    print(f"argv {sys.argv}")
    if not sys.argv:
        print(f"test_pdf: [test_chap6]")
    elif "test_chap6" in sys.argv:
        print("test_chap6")

        PDFTest().test_pdfminer_html_xml_climate()
        print("end")
    else:
        print(f"cannot parse args {argv}")
    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline
        """
        parser = argparse.ArgumentParser(
            description='Search sections with dictionaries and patterns')
        # apply_choices = [self.PDF2TXT, self.PDF2SVG, self.SVG2XML, self.TXT2SENT, self.XML2HTML, self.XML2TXT]
        parser.add_argument('--assert', nargs="+",
                            help='assertions; failure gives error message (prototype)')
        parser.add_argument('--combine', nargs=1,
                            help='operation to combine files into final object (e.g. concat text or CSV path')
        parser.add_argument('--config', '-c', nargs="+",
                            help='path (e.g. ~/pyami/config.ini.master) with list of config path(s) or config vars;'
                                 ' "symbols": gives symbols')
        return parser


if __name__ == "__main__":
    main()
else:
    pass

