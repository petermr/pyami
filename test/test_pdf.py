from pathlib import Path

import lxml
import lxml.etree
import lxml.html
import unittest

# local
from py4ami.ami_pdf import SVG_NS, SVGX_NS
from py4ami.ami_pdf import STYLE, AmiPage, X, Y, FILL, STROKE, FONT_FAMILY, FONT_SIZE, HtmlUtil, SORT_XY
from test.resources import Resources
from py4ami.pyamix import PyAMI

# class PDFTest:

FINAL_DRAFT_DIR = "/Users/pm286/projects/readable_climate_reports/ipcc/dup/finalDraft/svg"  # PMR only
PAGE_9 = Path(Resources.CLIMATE_10_SVG_DIR, "fulltext-page.9.svg")
PAGE_6 = Path(Resources.CLIMATE_10_SVG_DIR, "fulltext-page.6.svg")
CURRENT_RANGE = range(1, 20)
# CHAPTER_RANGE = range(1, 200)
CLIMATE_10_HTML_DIR = Path(Resources.TEMP_CLIMATE_10_PROJ_DIR, "html")


# FULL_TEMP_DIR = Path(Path(__file__).parent.parent, "temp", "full")


def test_pdfbox_output_exists():
    """check CLIMATE dir exists
    """
    # assert str(Resources.CLIMATE_10_DIR) == "/Users/pm286/workspace/pyami/test/resources/svg", f"resources {Resources.CLIMATE_10_DIR}"
    assert Resources.CLIMATE_10_PROJ_DIR.exists(), f"{Resources.CLIMATE_10_PROJ_DIR} should exist"


def test_findall_svg_and_find_texts():
    """find climate10_:text elements
    """
    assert PAGE_9.exists(), f"{PAGE_9} should exist"
    page9_elem = lxml.etree.parse(str(PAGE_9))
    texts = page9_elem.findall(f"//{{{SVG_NS}}}text")
    assert len(texts) == 108


def test_get_text_attribs():
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


def test_get_text_attrib_vals():
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


def test_create_text_lines_page6():
    """creation of AmiPage from SVG page and creation of text spans"""
    page = AmiPage.create_page_from_svg(PAGE_6)
    page.create_text_spans(sort_axes=SORT_XY)
    assert 70 >= len(page.text_spans) >= 60


def test_create_html():
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
        assert (html_path.exists(), f"{html_path} exists")


def test_create_html_in_selection():
    """
    Test 10 pages
    """
    pretty_print = True
    use_lines = True
    # selection = range(1, 2912)
    selection = range(1, 50)
    counter = 0
    counter_tick = 20
    for page_index in selection:
        if counter % counter_tick == 0:
            print(f".", end="")
        page_path = Path(FINAL_DRAFT_DIR, f"fulltext-page.{page_index}.svg")
        html_path = Path(Resources.CLIMATE_10_HTML_TEMP_DIR, f"page.{page_index}.html")
        if not Resources.CLIMATE_10_HTML_TEMP_DIR.exists():
            Resources.CLIMATE_10_HTML_TEMP_DIR.mkdir()
        ami_page = AmiPage.create_page_from_svg(page_path, rotated_text=False)
        ami_page.write_html(html_path, pretty_print, use_lines)
        counter += 1
        assert (html_path.exists(), f"{html_path} exists")


def test_create_chapters():
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

def test_svg2page():
    proj = Resources.CLIMATE_10_PROJ_DIR
    args = f"--proj {proj} --apply svg2page"
    PyAMI().run_command(args)

@unittest.skip("Needs debugging")
def test_page2chap():
    proj = Resources.CLIMATE_10_PROJ_DIR
    args = f"--proj {proj} --apply page2sect"
    PyAMI().run_command(args)

# ==============================

def make_full_draft_html(pretty_print, use_lines, rotated_text=False):
    """reads SVG output from ami3/pdfbox and converts to HTML
    used by several tests at present and will be intergrated
    :param pretty_print: pretty print the HTML. Warning may introduce whitespace
    :param use_lines: output is CompositeLines. Not converted into running text (check)
    :param rotated_text: include/ignore texts with non-zero @rotateDegress attribute
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

