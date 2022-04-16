from pathlib import Path
# import lxml.etree as etree
import lxml
from lxml import etree
# class PDFTest:

RESOURCES = Path(Path(__file__).parent, "resources") # only works for PMR
CLIMATE = Path(RESOURCES, "climate")
PAGE_9 = Path(CLIMATE, "fulltext-page.9.svg")
PAGE_6 = Path(CLIMATE, "fulltext-page.6.svg")
FACT = 2.8
SVG_NS = "http://www.w3.org/2000/svg"


def test_pdfbox_output_exists():
    assert str(CLIMATE) == "/Users/pm286/workspace/pyami/test/resources/climate", f"resources {CLIMATE}"
    assert CLIMATE.exists(), f"{CLIMATE} should exist"

def test_findall_svg():
    assert PAGE_9.exists(), f"{PAGE_9} should exist"
    PAGE9_ELEM = lxml.etree.parse(str(PAGE_9))
    texts = PAGE9_ELEM.findall("//{http://www.w3.org/2000/svg}text")
    assert len(texts) == 108

def test_get_text_attribs():
    page = lxml.etree.parse(str(PAGE_9))
    text0 = page.findall("//{http://www.w3.org/2000/svg}text")[0]
    assert text0.tag == "{http://www.w3.org/2000/svg}text"
    assert text0.attrib.get("y") == '44.76'
    assert text0.attrib.get("x") == '72.0,79.201,84.721,90.241,96.961,104.162,111.363,117.482,124.798,127.288,258.242,263.762,268.802,276.601,284.401,288.841,292.202,297.241,299.761,303.001,308.041,311.402,313.921,319.441,324.481,327.241,330.001,334.441,339.481,347.28,351.601,356.641,361.081,364.442,368.28,370.77,448.08,451.439,456.96,463.563,470.167,472.687,480.006,486.61,491.651,494.171,503.533,510.718,513.238,516.594,519.951,523.307'
    assert text0.attrib.get("{http://www.xml-cml.org/schema/svgx}width") == '0.72,0.56,0.56,0.67,0.72,0.72,0.61,0.72,0.25,0.55,0.56,0.5,0.78,0.78,0.44,0.33,0.5,0.25,0.33,0.5,0.33,0.25,0.56,0.5,0.28,0.28,0.44,0.5,0.78,0.44,0.5,0.44,0.33,0.39,0.25,0.55,0.33,0.56,0.67,0.67,0.25,0.72,0.67,0.5,0.25,0.94,0.72,0.25,0.33,0.33,0.33,0.25'
    assert text0.attrib.get("style") == 'fill:rgb(0,0,0);font-family:TimesNewRomanPSMT;font-size:9.96px;stroke:none;'
    text_content = ''.join(text0.itertext())
    assert text_content == "APPROVED Summary for Policymakers IPCC AR6 WG III "
    assert len(text_content) == 50 # some spaces have been elided??


def test_get_text_attrib_vals():
    page = lxml.etree.parse(str(PAGE_9))
    text0 = page.findall("//{http://www.w3.org/2000/svg}text")[0]
    x_coords = get_x_coords(text0)
    assert x_coords == [
 72.0, 79.201, 84.721, 90.241,
 96.961, 104.162, 111.363, 117.482, 124.798, 127.288, 258.242, 263.762, 268.802,
 276.601, 284.401, 288.841, 292.202, 297.241, 299.761,
 303.001, 308.041, 311.402, 313.921, 319.441, 324.481, 327.241, 330.001,
 334.441, 339.481, 347.28, 351.601, 356.641, 361.081, 364.442,
 368.28, 370.77, 448.08, 451.439, 456.96, 463.563, 470.167,
 472.687, 480.006, 486.61, 491.651, 494.171, 503.533, 510.718, 513.238, 516.594, 519.951, 523.307]
    assert len(x_coords) == 52

    widths = get_widths(text0)
    assert widths == [
 0.72, 0.56, 0.56, 0.67, 0.72, 0.72, 0.61,
 0.72, 0.25, 0.55, 0.56, 0.5, 0.78, 0.78, 0.44, 0.33, 0.5, 0.25, 0.33, 0.5, 0.33,
 0.25, 0.56, 0.5, 0.28, 0.28, 0.44, 0.5, 0.78, 0.44, 0.5, 0.44, 0.33,
 0.39, 0.25, 0.55, 0.33, 0.56, 0.67, 0.67, 0.25, 0.72, 0.67, 0.5, 0.25, 0.94, 0.72, 0.25, 0.33, 0.33,
 0.33, 0.25
    ]
    assert len(widths) == 52

    style_dict, breaks = find_breaks_in_text(text0)
    # assert style_dict == {'fill': 'rgb(0,0,0)',\n 'font-family': 'TimesNewRomanPSMT',\n 'font-size': '9.96px',\n 'stroke': 'none'}
    assert style_dict["fill"] == 'rgb(0,0,0)'
    assert style_dict["font-family"] == 'TimesNewRomanPSMT'
    assert style_dict["font-size"] == '9.96px'
    assert style_dict["stroke"] == 'none'
    assert get_font_size(text0) == 9.96

def test_find_breaks_page6():
    find_text_breaks_in_page(PAGE_6)

def test_find_breaks_in_pages():
    """
    Test 10 pages
    """
    for page in range(9):
        print(f"page{page}===================")
        page_i = Path(CLIMATE, f"fulltext-page.{page}.svg")
        breaks_by_line = find_text_breaks_in_page(page_i)


# /Users/pm286/projects/readable_climate_reports/ipcc/dup/finalDraft/svg
def test_find_breaks_in_many_pages():
    """test hundreds if pages"""
    numpages = 500
    for page in range(numpages):
        print(f"=========== page{page}  ===================")
        page_path = Path("/Users/pm286/projects/readable_climate_reports/ipcc/dup/finalDraft/svg", f"fulltext-page.{page}.svg")
        breaks_by_line = find_text_breaks_in_page(page_path)
        if breaks_by_line:
            # print(f"breaks by line {breaks_by_line}")
            pass


## ==============================

def find_text_breaks_in_page(page_path):
    page_element = lxml.etree.parse(str(page_path))
    text_elements = page_element.findall(f"//{{{SVG_NS}}}text")
    print(f"texts {len(text_elements)}")
    text_breaks_by_line = dict()
    for text_index, text_element in enumerate(text_elements):
        style_dict, text_break_list = find_breaks_in_text(text_element)
        print(f"style {style_dict}")

        if text_break_list:
            text_breaks_by_line[text_index] = text_break_list
            current = 0
            text_content = get_text_content(text_element)
            offset = 0
            print(f"{text_index}: ", end='')
            for text_break in text_break_list:
                # print(f"text_break: {text_break}")
                print(f"{text_content[current:text_break - offset]}___", end='')
                current = text_break
                offset += 1
            print(f"{text_content[current - offset:]}")
    return text_breaks_by_line

def find_breaks_in_text(text):
    widths = get_widths(text)
    x_coords = get_x_coords(text)
    y_coord = get_y_coord(text)
    text_content = get_text_content(text)
    font_size = get_font_size(text)
    pointer = 0
    breaks =  []
    # this algorithm for breaks in line probably needs tuning
    for col in range(len(x_coords) - 1):
        deltax = float(int(100 * (x_coords[col + 1] - x_coords[col]))) / 100
        if deltax > FACT * widths[col] * font_size:
            if text_content[pointer:]:
                breaks.append(col)
        else:
            pointer += 1
    style_dict = get_style_dict(text)
    return style_dict, breaks


def get_text_content(text):
    return ''.join(text.itertext())


def get_float_vals(elem, attname):
    attval = elem.attrib.get(attname)
    if attval:
        ss = attval.split(',')
        vals = [float(s) for s in ss]
        return vals
    return []

def get_float_val(elem, attname):
    attval = elem.attrib.get(attname)
    return float(attval) if attval else None

def get_x_coords(elem):
    return get_float_vals(elem, "x")

def get_y_coord(elem):
    return get_float_val(elem, "y")

def get_widths(elem):
    return get_float_vals(elem, "{http://www.xml-cml.org/schema/svgx}width")

def get_style_dict(elem):
    style_dict = dict()
    style = elem.attrib.get("style")
    styles = style.split(';')
    for s in styles:
        if len(s) > 0:
            ss = s.split(":")
            style_dict[ss[0]] = ss[1]
    y = get_y_coord(elem)
    if y:
        style_dict["y"] = y
    return style_dict

def get_font_size(text):
    sd = get_style_dict(text)
    fs = sd.get("font-size")
    fs = fs[:-2]
    return float(fs)



