import os
import pprint
import sys
import unittest
from collections import Counter
from pathlib import Path

import lxml
import lxml.etree
import lxml.html

import test.test_all

"""NOTE REQUIRES LATEST pdfplumber"""
import pdfplumber
from PIL import Image
# local
from py4ami.ami_bib import Publication

from py4ami.ami_pdf import SVG_NS, SVGX_NS, CSSStyle, PDFArgs, PDFDebug
from py4ami.ami_pdf import AmiPage, X, Y, SORT_XY, PDFImage
from py4ami.ami_pdf import WORDS, IMAGES, ANNOTS
from py4ami.ami_html import HtmlUtil, STYLE, FILL, STROKE, FONT_FAMILY, FONT_SIZE
from py4ami.ami_html import H_SPAN, H_BODY, H_P
from py4ami.pyamix import PyAMI
from py4ami.bbox_copy import BBox
from test.resources import Resources
from test.test_all import AmiAnyTest

# class PDFTest:

FINAL_DRAFT_DIR = "/Users/pm286/projects/readable_climate_reports/ipcc/dup/finalDraft/svg"  # PMR only
PAGE_9 = Path(Resources.CLIMATE_10_SVG_DIR, "fulltext-page.9.svg")
PAGE_6 = Path(Resources.CLIMATE_10_SVG_DIR, "fulltext-page.6.svg")
CURRENT_RANGE = range(1, 20)
# CHAPTER_RANGE = range(1, 200)
CLIMATE_10_HTML_DIR = Path(Resources.TEMP_CLIMATE_10_PROJ_DIR, "html")

PMC1421 = Path(Resources.RESOURCES_DIR, "projects", "liion4", "PMC4391421", "fulltext.pdf")

IPCC_DIR = Path(Resources.TEST_RESOURCES_DIR, "ipcc")
IPCC_GLOSS_DIR = Path(IPCC_DIR, "glossary")
IPCC_GLOSSARY = Path(IPCC_GLOSS_DIR, "IPCC_AR6_WGIII_Annex-I.pdf")
IPCC_CHAP6_DIR = Path(IPCC_DIR, "Chapter06")
IPCC_CHAP6_PDF = Path(IPCC_CHAP6_DIR, "fulltext.pdf")

# arg_dict

INDIR = "indir"
INPATH = "inpath"
MAXPAGE = "maxpage"
PAGES = "pages"
OUTDIR = "outdir"
OUTFORM = "outform"
OUTPATH = "outpath"
OUTSTEM = "outstem"
FLOW = "flow"
# FORMAT = "fmt"
IMAGEDIR = "imagedir"
RESOLUTION = "resolution"
TEMPLATE = "template"


# ==============================

def make_full_chap_10_draft_html_from_svg(pretty_print, use_lines, rotated_text=False):
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


def make_html_dir():
    html_dir = Path(Resources.TEMP_DIR, "html")
    if not html_dir.exists():
        html_dir.mkdir()
    return html_dir


class PDFTest(test.test_all.AmiAnyTest):
    MAX_PAGE = 5
    MAX_ITER = 20

    # all are skipUnless
    ADMIN = True and AmiAnyTest.ADMIN
    CMD = True and AmiAnyTest.CMD
    DEBUG = True and AmiAnyTest.DEBUG
    LONG = True and AmiAnyTest.LONG
    NET = True and AmiAnyTest.NET
    OLD = True and AmiAnyTest.OLD
    NYI = True and AmiAnyTest.NYI
    USER = True and AmiAnyTest.USER

    VERYLONG = False or AmiAnyTest.VERYLONG

    # local
    HTML = True
    SVG = True

    # old tests
    OLD = False

    @unittest.skipUnless("enviroment", ADMIN)
    def test_pdfbox_output_exists(self):
        """check CLIMATE dir exists
        """
        # assert str(Resources.CLIMATE_10_DIR) == "/Users/pm286/workspace/pyami/test/resources/svg", f"resources {Resources.CLIMATE_10_DIR}"
        assert Resources.CLIMATE_10_PROJ_DIR.exists(), f"{Resources.CLIMATE_10_PROJ_DIR} should exist"

    @unittest.skipUnless("enviroment", ADMIN)
    def test_findall_svg_and_find_texts(self):
        """find climate10_:text elements
        """
        assert PAGE_9.exists(), f"{PAGE_9} should exist"
        page9_elem = lxml.etree.parse(str(PAGE_9))
        texts = page9_elem.findall(f"//{{{SVG_NS}}}text")
        assert len(texts) == 108

    @unittest.skipUnless(SVG, "svg")
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

    @unittest.skipUnless(SVG, "svg")
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

    @unittest.skipUnless(SVG, "svg")
    def test_create_text_lines_page6(self):
        """creation of AmiPage from SVG page and creation of text spans"""
        page = AmiPage.create_page_from_svg(PAGE_6)
        page.create_text_spans(sort_axes=SORT_XY)
        assert 70 >= len(page.text_spans) >= 60

    @unittest.skipUnless(SVG, "svg")
    def test_create_html_from_svg(self):
        """
        Test 10 pages
        """
        pretty_print = True
        use_lines = True
        svg_dir = Resources.CLIMATE_10_SVG_DIR
        html_dir = Resources.CLIMATE_10_HTML_TEMP_DIR
        for page_index in range(1, 9):
            page_path = Path(svg_dir, f"fulltext-page.{page_index}.svg")
            html_path = Path(html_dir, f"page.{page_index}.html")
            if not html_dir.exists():
                html_dir.mkdir()
            ami_page = AmiPage.create_page_from_svg(page_path)
            ami_page.write_html(html_path, pretty_print, use_lines)
            assert html_path.exists(), f"{html_path} exists"

    @unittest.skipUnless(SVG, "svg")
    def test_create_html_in_selection_from_svg(self):
        """
        Test 10 pages
        """
        pretty_print = True
        use_lines = True
        # selection = range(1, 2912)
        page_selection = range(1, 50)
        counter = 0
        counter_tick = 20
        html_out_dir = Resources.CLIMATE_10_HTML_TEMP_DIR
        for page_index in page_selection:
            if counter % counter_tick == 0:
                print(f".", end="")
            page_path = Path(FINAL_DRAFT_DIR, f"fulltext-page.{page_index}.svg")
            html_path = Path(html_out_dir, f"page.{page_index}.html")
            if not html_out_dir.exists():
                html_out_dir.mkdir()
            ami_page = AmiPage.create_page_from_svg(page_path, rotated_text=False)
            ami_page.write_html(html_path, pretty_print, use_lines)
            counter += 1
            assert html_path.exists(), f"{html_path} exists"

    @unittest.skipUnless(SVG, "svg")
    def test_create_chapters_through_svg(self):
        pretty_print = True
        use_lines = True
        make_full_chap_10_draft_html_from_svg(pretty_print, use_lines)
        selection = CURRENT_RANGE
        temp_dir = Resources.CLIMATE_10_HTML_TEMP_DIR
        for page_index in selection:
            html_path = Path(temp_dir, f"page.{page_index}.html")
            with open(html_path, "r") as h:
                xml = h.read()
            root = lxml.etree.fromstring(xml)
            spans = root.findall(f"./{H_BODY}/{H_P}/{H_SPAN}")
            assert type(spans[0]) is lxml.etree._Element, f"expected str got {type(spans[0])}"
            assert len(HtmlUtil.get_text_content(spans[0])) > 0
            span = None
            chapter = ""
            # bug in parsing line 0
            if Publication.is_chapter_or_tech_summary(HtmlUtil.get_text_content(spans[0])):
                span = spans[0]
            if span is None and Publication.is_chapter_or_tech_summary(HtmlUtil.get_text_content(spans[1])):
                span = spans[1]
            if span is None:
                print(f"p:{page_index}, {HtmlUtil.get_text_content(spans[0])}, {HtmlUtil.get_text_content(spans[1])}")
            else:
                chapter = HtmlUtil.get_text_content(span)
                print("CHAP ", chapter)

    @unittest.skip("obsolete")
    @unittest.skipUnless(SVG, "svg")
    @unittest.skipUnless(CMD, "command")
    def test_svg2page(self):
        proj = Resources.CLIMATE_10_PROJ_DIR
        args = f"--proj {proj} --apply svg2page"
        PyAMI().run_command(args)

    @unittest.skipIf(NYI, "page2sect")
    def test_page2chap(self):
        proj = Resources.CLIMATE_10_PROJ_DIR
        args = f"--proj {proj} --apply page2sect"
        PyAMI().run_command(args)

    @unittest.skipUnless(USER, "page2sect")
    def test_make_ami_pages_with_spans_from_charstream_ipcc_chap6(self):
        """The central AMI method to make HTML from PDF characters
        """
        output_stem = "chap6"
        page_nos = range(3, 13)
        # page_nos = [3 4 5 8 ]
        input_pdf = Path(IPCC_CHAP6_PDF)
        assert input_pdf.exists(), f"{input_pdf} should exist"
        bbox = BBox(xy_ranges=[[60, 999], [60, 790]])
        output_dir = Path(Resources.TEMP_DIR, "pdf")
        AmiPage.create_html_pages(bbox=bbox, input_pdf=input_pdf, output_dir=output_dir, output_stem=output_stem,
                                  range_list=[range(3, 8), range(129, 131)])
        assert output_dir.exists()
        assert Path(output_dir, f"{output_stem}_{5}.html").exists()

    def test_pdfplumber_full_page_info(self):
        """The definitive catalog of all objects on a page"""
        assert PMC1421.exists(), f"{PMC1421} should exist"

        # also ['_text', 'matrix', 'fontname', 'ncs', 'graphicstate', 'adv', 'upright', 'x0', 'y0', 'x1', 'y1',
        # 'width', 'height', 'bbox', 'size', 'get_text',
        # 'is_compatible', 'set_bbox', 'is_empty', 'is_hoverlap',
        # 'hdistance', 'hoverlap', 'is_voverlap', 'vdistance', 'voverlap', 'analyze', ']
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
            assert len(first_page.objects) == 2
            assert type(first_page.objects) is dict
            assert list(first_page.objects.keys()) == ['char', 'line']
            assert len(first_page.objects['char']) == 4411
            assert first_page.objects['char'][:2] == [
                {'matrix': (9, 0, 0, 9, 319.74, 797.4203),
                 'fontname': 'KAAHHD+Calibri,Italic',
                 'adv': 0.319,
                 'upright': True,
                 'x0': 319.74, 'y0': 795.1703, 'x1': 322.611, 'y1': 804.1703,
                 'width': 2.870999999999981, 'height': 9.0, 'size': 9.0,
                 'object_type': 'char', 'page_number': 1,
                 'text': 'J', 'stroking_color': None, 'non_stroking_color': (0.86667, 0.26667, 1, 0.15294),
                 'top': 37.8297, 'bottom': 46.8297, 'doctop': 37.8297
                 },
                {'matrix': (9, 0, 0, 9, 322.6092, 797.4203), 'fontname': 'KAAHHD+Calibri,Italic', 'adv': 0.513,
                 'upright': True,
                 'x0': 322.6092, 'y0': 795.1703, 'x1': 327.2262, 'y1': 804.1703, 'width': 4.617000000000019,
                 'height': 9.0, 'size': 9.0,
                 'object_type': 'char', 'page_number': 1, 'text': 'o', 'stroking_color': None,
                 'non_stroking_color': (0.86667, 0.26667, 1, 0.15294),
                 'top': 37.8297, 'bottom': 46.8297, 'doctop': 37.8297},
            ], f"first_page.objects['char'][0]  {first_page.objects['char'][0]}"
            assert len(first_page.objects['line']) == 1, f" len(first_page.objects['line'])"
            assert first_page.objects['line'][0] == {
                'bottom': 48.24000000000001,
                'doctop': 48.24000000000001,
                'evenodd': False,
                'fill': False,
                'height': 0.0,
                'linewidth': 1,
                'non_stroking_color': 0,
                'object_type': 'line',
                'page_number': 1,
                'pts': [(56.7, 793.76), (542.76, 793.76)],
                'stroke': True,
                'stroking_color': (0.3098, 0.24706, 0.2549, 0),
                'top': 48.24000000000001,
                'width': 486.06,
                'x0': 56.7,
                'x1': 542.76,
                'y0': 793.76,
                'y1': 793.76
            }, f"first_page.objects['line'][0]  {first_page.objects['line'][0]}"
            # assert first_page.process_object(obj) == [], f"process_object (LTItem) {first_page.process_object()}"

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
            assert len(first_page.chars) == 4411  # same as first_page.objects['char'] I think
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
            """first_page.objects['char']"""
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

    def test_debug_page_properties_chap6(self):
        """debug the PDF objects (crude)
        outputs wordcount for page, and any image data.
        Would ber better if we knew hoe to read PDFStream"""
        maxpage = 9  # images on page 8, and 9
        # maxpage = 9999 # image is on page 8
        path = Path(Resources.TEMP_DIR, "pdf")
        path.mkdir(exist_ok=True)
        outdir = Path(path, "chap6")
        outdir.mkdir(exist_ok=True)
        pdf_debug = PDFDebug()

        with pdfplumber.open(IPCC_CHAP6_PDF) as pdf:
            pages = list(pdf.pages)
            for page in pages[:maxpage]:
                pdf_debug.debug_page_properties(page, debug=[WORDS, IMAGES], outdir=outdir)
        pdf_debug.write_summary(outdir=outdir)
        print(f"pdf_debug {pdf_debug.image_dict}")
        assert maxpage != 9 or pdf_debug.image_dict == {
            ((1397, 779), 143448): (8, (72.0, 523.3), (412.99, 664.64)),
            ((1466, 655), 122016): (8, (72.0, 523.3), (203.73, 405.38)),
            ((1634, 854), 204349): (9, (80.9, 514.25), (543.43, 769.92))
        }

    @unittest.skip("LONG; other methods may be better")
    def test_pdfminer_images(self):
        import pdfminer
        from pdfminer.image import ImageWriter
        from pdfminer.high_level import extract_pages

        path = Path(IPCC_CHAP6_PDF)
        pages = list(extract_pages(path))
        page = pages[10]

        def get_image(layout_object):
            if isinstance(layout_object, pdfminer.layout.LTImage):
                print(f"LTImage {layout_object.__dir__()}")
                return layout_object
            if isinstance(layout_object, pdfminer.layout.LTContainer):
                for child in layout_object:
                    return get_image(child)
            else:
                return None

        def save_images_from_page(page: pdfminer.layout.LTPage):
            images = list(filter(bool, map(get_image, page)))
            outdir = Path(Resources.TEMP_DIR, "pdf", "chap6", "pdf miner")
            iw = ImageWriter(str(outdir))
            for image in images:
                iw.export_image(image)
                print(f" image {image}")

        save_images_from_page(page)

    def test_debug_page_properties(self):
        """ high-level debug the PDF objects (crude) uses PDFDebug on 5-page document
        finds WORDS (count) and IMAGE details
        """

        p = Path(Resources.TEMP_DIR, "pdf")
        p.mkdir(exist_ok=True)
        outdir = Path(p, "pmc1421")
        if not outdir.exists():
            outdir.mkdir()
        with pdfplumber.open(PMC1421) as pdf:
            pages = list(pdf.pages)
            assert len(pages) == 5
            pdf_debug = PDFDebug()
            if not outdir:
                print(f"no output dir given")
                return
            path = Path(outdir, "images")
            if not path.exists():
                path.mkdir()

            for page in pages:
                pdf_debug.debug_page_properties(page, debug=[WORDS, IMAGES])
            print(f"images: {pdf_debug.image_dict.keys()}")

    def test_bmp_png_to_png(self):
        """
        convert bmp, jpgs, etc to PNG
        results in temp_oldx/ipcc_chap6/png/
        checks existence on created PNG
        uses: pdf_image.convert_all_suffixed_files_to_target(dirx, [".bmp", ".jpg"], ".png", outdir=outdir)
        USEFUL

        """
        dirx = Path(Resources.IPCC_CHAP06, "image_bmp_jpg")
        outdir = Path(Resources.TEMP_DIR, "ipcc_chap6", "png")
        if not dirx.exists():
            print(f"no directory {dirx}")
            return
        pdf_image = PDFImage()
        pdf_image.convert_all_suffixed_files_to_target(dirx, [".bmp", ".jpg"], ".png", outdir=outdir)
        pngs = [
            "Im1.png", "Im0.1.png", "Im0.2.png", "Im1.4.png", "Im1.5.png", "Im0.1.png",
            "Im0.0.png", "Im1.png", "Im3.png", "Im0.2.png", "Im0.3.png", "Im2.png",
        ]
        for png in pngs:
            assert Path(outdir, png).exists()

    def test_merge_pdf2txt_bmp_jpg_with_coords(self):
        """
        creates coordinate data for images (20 pp doc) and also reads existing coord data from file
        (? from AMI3-java or previous run) and tries to match them
        """
        png_dir = Path(Resources.IPCC_CHAP06, "images")
        bmp_jpg_dir = Path(Resources.IPCC_CHAP06, "image_bmp_jpg")
        coord_file = Path(Resources.IPCC_CHAP06, "image_coords.txt")
        print(f"input {coord_file}")
        outdir = Path(Resources.IPCC_CHAP06, "images_new")
        if not outdir.exists():
            outdir.mkdir()
        with open(coord_file, "r") as f:
            coord_list = f.readlines()
        assert len(coord_list) == 14

        coord_list = [c.strip() for c in coord_list]
        wh_counter = Counter()
        coords_by_width_height = dict()
        for coord in coord_list:
            # image_9_0_80_514_72_298
            coords = coord.split("_")
            assert len(coords) == 7
            bbox = BBox(xy_ranges=[[coords[3], coords[4]], [coords[5], coords[6]]])
            print(f"coord {coord} {bbox} {bbox.width},{bbox.height}")
            wh_tuple = bbox.width, bbox.height
            print(f"wh {wh_tuple}")
            wh_counter[wh_tuple] += 1
            if coords_by_width_height.get(wh_tuple) is None:
                coords_by_width_height[wh_tuple] = [coord]
            else:
                coords_by_width_height.get(wh_tuple).append(coord)
        print(f"counter {wh_counter}")
        print(f"coords_by_wh {coords_by_width_height}")

        bmp_jpg_images = os.listdir(bmp_jpg_dir)
        for bmp_jpg_image in bmp_jpg_images:
            if Path(bmp_jpg_image).suffix == ".png":
                print(f"png {bmp_jpg_image}")
                with Image.open(str(Path(bmp_jpg_dir, bmp_jpg_image))) as image:
                    wh_tuple = image.width, image.height
                    print(f"wh ... {wh_tuple}")
                    print(f"coords {coords_by_width_height.get(wh_tuple)}")

    # See https://pypi.org/project/depdf/0.2.2/ for paragraphs?

    # https://towardsdatascience.com/pdf-text-extraction-in-python-5b6ab9e92dd

    def test_pdfminer_debug_LTTextLine_LTTextBox_PMC1421(self):
        """read PDF and chunk into text_lines and text_boxes
        Keeps box coordinates but loses style"""
        from pdfminer.layout import LTTextLineHorizontal, LTTextBoxHorizontal
        # need to pass in laparams, otherwise pdfplumber page would not
        # have high level pdfminer layout objects, only LTChars.
        pdf = pdfplumber.open(PMC1421, laparams={})
        page = pdf.pages[0].layout
        for element in page:
            if isinstance(element, LTTextLineHorizontal):
                # currently only seems to detect newline
                print(f"textlinehorizontal: ({element.bbox}):{element.get_text()}:", end="")
            if isinstance(element, LTTextBoxHorizontal):
                print(f">>start_text_box")
                for text_line in element:
                    # print(f"dir: {text_line.__dir__()}")
                    # print(f"....textboxhorizontal: ({text_line.bbox}): {text_line.get_text()}", end="")
                    pass
                print(f"<<end_text_box")

    # https://stackoverflow.com/questions/34606382/pdfminer-extract-text-with-its-font-information

    @unittest.skipUnless(DEBUG, "too much output")
    def test_pdfminer_font_and_character_output(self):
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

        # recursive
        def show_ltitem_hierarchy(o: Any, depth=0):
            """Show location and text of LTItem and all its descendants"""
            debug = False
            debug = True
            if depth == 0:
                print('element                        fontname             text')
                print('------------------------------ -------------------- -----')

            name = get_indented_name(o, depth)
            print(f"name: {name}")
            if debug or name.strip() == "LTTextLineHorizontal":
                print(
                    f'{name :<30.30s} '
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
            name = o.__class__.__name__
            if hasattr(o, 'fontname') and hasattr(o, 'size'):
                if name == "LTChar":
                    dummy = ['_text', 'matrix', 'fontname', 'ncs', 'graphicstate', 'adv', 'upright', 'x0', 'y0', 'x1',
                             'y1',
                             'width', 'height', 'bbox', 'size', '__module__', '__doc__', '__init__', '__repr__',
                             'get_text',
                             'is_compatible', '__lt__', '__le__', '__gt__', '__ge__', 'set_bbox', 'is_empty',
                             'is_hoverlap',
                             'hdistance', 'hoverlap', 'is_voverlap', 'vdistance', 'voverlap', 'analyze', '__dict__',
                             '__weakref__', '__hash__', '__str__', '__getattribute__', '__setattr__', '__delattr__',
                             '__eq__',
                             '__ne__', '__new__', '__reduce_ex__', '__reduce__', '__subclasshook__',
                             '__init_subclass__',
                             '__format__', '__sizeof__', '__dir__', '__class__']
                    print(f"LTChar {o.__dir__()}")
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
        # max_page = 999999
        options = [WORDS, ANNOTS]
        # max_page = 100  # increase this if yu want more output

        for (pdf_file, page_count) in [
            # (IPCC_GLOSSARY, 51),
            (IPCC_CHAP6_PDF, 219)
        ]:
            pdf_debug = PDFDebug()
            with pdfplumber.open(pdf_file) as pdf:
                print(f"file {pdf_file}")
                pages = list(pdf.pages)
                assert len(pages) == page_count
                for page in pages[:max_page]:
                    pdf_debug.debug_page_properties(page, debug=options)

    def test_make_structured_html_MAIN(self):
        """structures the flat HTML from pdfplumber, but no coordinates
        Can still be used for word frequency, etc."""

        print(f" converting {IPCC_CHAP6_PDF}")
        assert IPCC_CHAP6_PDF.exists(), f"chap6 {IPCC_CHAP6_PDF}"
        pdf_args = PDFArgs()
        pdf_args.arg_dict[INPATH] = IPCC_CHAP6_PDF
        pdf_args.arg_dict[MAXPAGE] = 10

        print(f"arg_dict {pdf_args.arg_dict}")
        outfile = pdf_args.convert_write()
        if not outfile:
            print(f"no file written")
        else:
            print(f"check {outfile} exists")
            assert outfile.exists(), f"outfile {outfile} should exist"

    @unittest.skipUnless(HTML, "create running text")
    @unittest.skipUnless(USER, "develop for commandline")
    def test_make_structured_html_pages_MAIN(self):
        """structures the flat HTML from pdfplumber into a running stream, but no coordinates
        Can still be used for word frequency, etc.

Uses:
    self.raw_html = PDFArgs.convert_pdf(path=self.inpath, fmt=self.outform, maxpages=self.maxpage)

    if self.flow:
        self.html = self.tidy_flow()

        """

        # print(f" converting {IPCC_CHAP6_PDF}")
        assert IPCC_CHAP6_PDF.exists(), f"chap6 {IPCC_CHAP6_PDF}"
        pdf_args = PDFArgs()
        pdf_args.arg_dict[MAXPAGE] = 4
        pdf_args.arg_dict[INPATH] = IPCC_CHAP6_PDF
        pdf_args.arg_dict[OUTPATH] = Path(Resources.TEMP_DIR,  "ipcc_chap6", "flow.test.html")

        pprint.pprint(pdf_args.arg_dict)
        # pdf_args.arg_dict[PAGES] = [(1,3), (5,10)]

        print(f"arg_dict {pdf_args.arg_dict}")
        outfile = Path(pdf_args.convert_write())
        if not outfile:
            print(f"no file written")
        else:
            print(f"check {outfile.absolute()} exists")
            assert outfile.exists(), f"outfile {outfile} should exist"

    @unittest.skipIf(NYI, "no code yet")
    def test_make_structured_html_cmdline_DEBUG(self):
        """
        Previous one gives:
        arg_dict {'convert': 'html', 'flow': True, 'footer': 80, 'header': 80, 'indir': None,
        'inpath': PosixPath('/Users/pm286/workspace/pyami/test/resources/ipcc/Chapter06/fulltext.pdf'),
        'maxpage': 10, 'outdir': None, 'outform': 'html', 'outstem': 'fulltext'}

        Tried to run:
        python -m py4ami.ami_pdf
        --inpath /Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/fulltext.pdf
        --maxpage 88 --outdir /Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/

        which didn't give flow html, but sections.
        Its debug

        Namespace(convert=None, debug=None, flow=True, footer=80, header=80, imagedir=None,
        indir=None, inpath=['/Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/fulltext.pdf'],
         maxpage=[88], outdir=['/Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/'],
         outform='html', outstem='fulltext.flow', resolution=400, template=None)"""

    def test_make_ipcc_html_spans(self):
        """uses PDFMiner library (no coordinates I think)"""
        sem_clim_dir = Path("/users/pm286", "projects", "semanticClimate")
        if not sem_clim_dir.exists():
            print(f"no ipcc dir {sem_clim_dir}, so skipping")
            return
        ipcc_dir = Path(sem_clim_dir, "ipcc", "ar6", "wg3")
        assert ipcc_dir.exists(), f"ipcc_dir {ipcc_dir} does not exist"
        chapter = "Chapter04"
        print(f"Converting chapter: {chapter}")
        pdf_args = PDFArgs()
        chapter_dir = Path(ipcc_dir, chapter)
        pdf_args.arg_dict[INDIR] = chapter_dir
        assert pdf_args.arg_dict[INDIR].exists(), f"dir does not exist {chapter_dir}"
        inpath = Path(chapter, "fulltext.pdf")
        pdf_args.arg_dict[INPATH] = Path(chapter_dir, "fulltext.pdf")
        assert pdf_args.arg_dict[INPATH].exists(), f"file does not exist {inpath}"
        pdf_args.arg_dict[MAXPAGE] = 20
        pdf_args.arg_dict[OUTFORM] = "flow.html"
        outdir = Path(Resources.TEMP_DIR, "ipcc_html")
        if not outdir.exists():
            outdir.mkdir()
        pdf_args.arg_dict[OUTDIR] = outdir
        print(f"arg_dict {pdf_args.arg_dict}")

        pdf_args.unwanteds = {
            "chapter": {
                "xpath": ".//div/span",
                "regex": "^Chapter\\s+\\d+\\s*$"
            },
            "final_gov": {
                "xpath": ".//div/span",
                "regex": "^\\s*Final Government Distribution\\s*$"
            },
            "page": {
                "xpath": ".//div/a",
                "regex": "^\\s*Page\\s*\\d+\\s*$",
            },
            "wg3": {
                "xpath": ".//div/span",
                "regex": "^\\s*(IPCC AR6 WGIII)|(IPCC WGIII AR6)\\s*$",
            },
        }
        pdf_args.convert_write()

    @unittest.skipUnless(VERYLONG, "processes Chapters 04, 05, 16, 17")
    def test_make_ipcc_html(self):
        """
        """
        sem_clim_dir = Path("/users/pm286", "projects", "semanticClimate")
        if not sem_clim_dir.exists():
            print(f"no ipcc dir {sem_clim_dir}, so skipping")
            return
        ipcc_dir = Path(sem_clim_dir, "ipcc", "ar6", "wg3")
        assert ipcc_dir.exists(), f"ipcc_dir {ipcc_dir} does not exist"
        chapters = [
            # "Chapter01",
            "Chapter04",
            # "Chapter06",
            # "Chapter07",
            # "Chapter15",
            # "Chapter16",
        ]
        for chapter in chapters:
            print(f"Converting chapter: {chapter}")
            pdf_args = PDFArgs()
            chapter_dir = Path(ipcc_dir, chapter)
            pdf_args.arg_dict[INDIR] = chapter_dir
            assert pdf_args.arg_dict[INDIR].exists(), f"dir does not exist {chapter_dir}"
            inpath = Path(chapter, "fulltext.pdf")
            pdf_args.arg_dict[INPATH] = Path(chapter_dir, "fulltext.pdf")
            assert pdf_args.arg_dict[INPATH].exists(), f"file does not exist {inpath}"
            pdf_args.arg_dict[MAXPAGE] = 200
            pdf_args.arg_dict[OUTFORM] = "flow.html"
            outdir = Path(Resources.TEMP_DIR, "ipcc_html")
            if not outdir.exists():
                outdir.mkdir()
            pdf_args.arg_dict[OUTDIR] = outdir
            print(f"arg_dict {pdf_args.arg_dict}")

            unwanteds = {
                "chapter": {
                    "xpath": ".//div/span",
                    "regex": "^Chapter\\s+\\d+\\s*$"
                },
                "final_gov": {
                    "xpath": ".//div/span",
                    "regex": "^\\s*Final Government Distribution\\s*$"
                },
                "page": {
                    "xpath": ".//div/a",
                    "regex": "^\\s*Page\\s*\\d+\\s*$",
                },
                "wg3": {
                    "xpath": ".//div/span",
                    "regex": "^\\s*(IPCC AR6 WGIII)|(IPCC WGIII AR6)\\s*$",
                },
            }
            pdf_args.convert_write(
                # unwanteds=unwanteds
            )

    def test_pdfminer_text_html_xml(self):
        # Use `pip3 install pdfminer.six` for python3
        """runs pdfinterpreter/converter over 5-page article and creates html and xml versions"""
        fmt = "html"
        maxpages = 0
        path = Path(PMC1421)
        result = PDFArgs.convert_pdf(
            path=str(path),
            fmt=fmt,
            maxpages=maxpages
        )
        html_dir = make_html_dir()
        with open(Path(html_dir, f"pmc4121.{fmt}"), "w") as f:
            f.write(result)
            print(f"wrote {f.name}")

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

    def test_convert_pdf_to_html_and_save(self):
        """Uses PDFArgs.convert_pdf to convert PDF to HTML and save
        to temp_oldx (/Users/pm286/workspace/pyami/temp_oldx/html/pmc4121.xml)
        This is raw output with <br> between lines and mirrors the layout of 
        """
        # Use `pip3 install pdfminer.six` for python3

        """reading py4ami/resources/projects/liion4/PMC4391421/fulltext.pdf"""
        pathx = Path(PMC1421)

        # convert PDF to html
        result = PDFArgs.convert_pdf(
            path=str(pathx),
            fmt="html",
            caching=True,
        )
        # output dir
        html_dir = Path(Resources.TEMP_DIR, "html")
        if not html_dir.exists():
            html_dir.mkdir()
        # ouytput file
        path = Path(html_dir, "pmc4121.xml")
        # clean because text requires new file
        if path.exists():
            os.remove(path)
        with open(path, "w") as f:
            f.write(result)
            print(f"wrote {f}")
        assert path.exists(), f"should output html to {path}"
        assert 76000 < os.path.getsize(path) < 77000, f"size should be in range , was {os.path.getsize(path)}"

    def test_make_composite_lines_from_pdf_chap_6_3_toc(self):
        path = Path(Resources.IPCC_CHAP06, "html", "chap6_3.html")
        assert path.exists(), f"path exists {path}"
        AmiPage.create_page_from_pdf_html(path)

    def test_main_help(self):
        sys.argv = []
        sys.argv.append("--help")
        try:
            main()
        except SystemExit:
            pass

    def test_subcommands(self):
        # run args
        inpath = Path(Resources.PDFS_DIR, "1758-2946-3-44.pdf")
        outdir = Path(Resources.TEMP_DIR, "pdf", "1758-2946-3-44")
        PyAMI().run_command(
            ['PDF', '--inpath', str(inpath), '--outdir', str(outdir), '--pages', '_2', '4', '6_8', '11_'])

    def test_subcommands_maxpage(self):
        # run args
        inpath = Path(Resources.PDFS_DIR, "1758-2946-3-44.pdf")
        outdir = Path(Resources.TEMP_DIR, "pdf", "1758-2946-3-44")
        PyAMI().run_command(
            ['PDF', '--inpath', str(inpath), '--outdir', str(outdir), "--maxpage", "3"])

    #    @unittest.skipUnless("old test", self.admin)
    def test_cannot_iterate(self):
        """
        Test that 'PDF' subcomand works without errors
        """

        PyAMI().run_command(
            ['PDF'])
        PyAMI().run_command(
            ['PDF', '--help'])

    # =====================================================================================================
    # =====================================================================================================

    MAX_RECT = 5
    MAX_CURVE = 5
    MAX_TABLE = 5
    MAX_ROW = 10
    MAX_IMAGE = 5


#     def find_chapter_title(cls, elem):
#         """<div style="" id="id296"><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 15px;" id="id297">Chapter 6:</span></div>
# <div style="" id="id300"><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 15px;" id="id301">Energy Systems
# </span></div>
#         """
#         result = cls.get_div_span_starting_with(elem, "Chapter")
#         return result


def main(argv=None):
    print(f"running PDFArgs main")
    pdf_args = PDFArgs()
    try:
        pdf_args.parse_and_process()
    except Exception as e:
        print(f"***Cannot run pyami***; see output for errors: {e}")


if __name__ == "__main__":
    main()
else:
    pass
