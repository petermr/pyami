import argparse
import lxml
import lxml.html
from lxml import etree
from lxml.builder import E
import statistics
from enum import Enum
from pathlib import Path
from typing import Container
from io import BytesIO, StringIO
import sys
import re
from pdfminer.converter import TextConverter, XMLConverter, HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
import numpy as np
from sklearn.linear_model import LinearRegression

# local
from py4ami.bbox_copy import BBox  # this is horrid, but I don't have a library
from py4ami.util import Util

# text attributes
FACT = 2.8
SVG_NS = "http://www.w3.org/2000/svg"
SVGX_NS = "http://www.xml-cml.org/schema/svgx"

# coordinates
X = "x"
Y = "y"
SORT_Y = "y"  # for sorting
SORT_YX = "yx"  # for sorting
SORT_XY = "xy"  # for sorting
WIDTH = "width"


BBOX = "bbox"

# to link up text spans
X_MARGIN = 20

# paragraph spacing
INTERPARA_FACT = 1.5

# SCRIPTS
SCRIPT_FACT = 0.9

# style bundle
STYLE = "style"
ITALIC = "italic"
BOLD = "bold"
TIMES = "times"
CALIBRI = "calibri"
FONT_FAMILIES = [TIMES, CALIBRI]

# style attributes
FONT_SIZE = "font-size"
FONT_STYLE = "font-style"
FONT_WEIGHT = "font-weight"
FONT_FAMILY = "font-family"
FILL = "fill"
STROKE = "stroke"

STYLES = [
    FONT_SIZE,
    FONT_STYLE,
    FONT_FAMILY,
    FONT_WEIGHT,
    FILL,
    STROKE,
]

CHAPTER = "Chapter"
TECHNICAL_SUMMARY = "Technical Summary"

# debug
WORDS = "words"
LINES = "lines"
RECTS = "rects"
CURVES = "curves"
IMAGES = "images"
TABLES = "tables"
HYPERLINKS = "hyperlinks"
ANNOTS = "annots"
DEBUG_OPTIONS = [WORDS, LINES, RECTS, CURVES, IMAGES, TABLES, HYPERLINKS, ANNOTS]
DEBUG_ALL = "debug_all"

# regular expressions for (sub)sections
# markers = ["Chapter",
#            # "Table of Contents",
#            "Table of",  # one is concatenated (Chapter01) so abbreviate, unweighted Chap16
#            # "Executive Summary",
#            "Executive",  # case variation
#            # "Frequently Asked Questions", # not in Chapter01
#            "Frequently",  # case variation
#            "References",
#            ]

CHAP_TOP = re.compile(""
                      "(Chapter\\s?\\d\\d?\\s?\\:.*$)|"
                      "(Table\\s?of Contents.*)|"
                      "(Executive [Ss]ummary.*)|"
                      "(Frequently [Aa]sked.*)|"
                      "(References)"
                      )
CHAP_SECTIONS_RE = re.compile("\\d+\\.\\d+$")
CHAP_SUBSECTS_RE = re.compile("\\d+\\.\\d+\\.\\d+$")

MARKER = "marker"

# HTML
H_TABLE = "table"
H_THEAD = "thead"
H_TBODY = "tbody"
H_TR = "tr"
H_TH = "th"
H_TD = "td"

# Chapter
TREE_ROOT = "tree_root"
CLASS = "class"
PRE_CHAPSEC = "pre_chapsec"

# XPaths
ALL_DIV_XPATHS = ".//div"

# coordinates
X0 = 'x0'
Y1 = 'y1'
X1 = 'x1'
Y0 = 'y0'


def add_ids(root_elem):
    """adds IDs to all elements in document order
    :param root_elem: element defining tree of subelements"""
    xpath = "//*"
    elems = root_elem.xpath(xpath)
    for i, el in enumerate(elems):
        el.attrib["id"] = "id" + str(i)


# sub/Super

class SScript(Enum):
    SUB = 1
    SUP = 2


class AmiPage:
    """Transformation of an SVG Page from PDFBox/Ami3
    consists of paragraphs, divs, textlines, etc.
    Used as a working container, utimately being merged with
    neighbouring documents into complete HTML document
    """
    CONTENT_RANGES = [[56, 999], [45, 780]]

    def __init__(self):
        # path of SVG page
        self.page_path = None
        # raw parsed SVG
        self.page_element = None
        # child elements of type <climate10_:text>
        self.text_elements = None
        # spans created from tex_elements
        self.text_spans = []
        # bboxes of the spans
        self.bboxes = []
        # composite lines (i.e. with sub/superscripts, bold, italic
        self.composite_lines = []
        # paragraphs from inter-composite spacing
        self.paragraphs = []

    @classmethod
    def create_page_from_svg(cls, svg_path, rotated_text=False):
        """Initial parse of SVG and creation of AmiPage
        :param svg_path: path of SVG file
        :param rotated_text: if false (default) ignore text with @rotateDegrees
        """
        ami_page = AmiPage()
        ami_page.page_path = svg_path
        ami_page.create_text_spans(sort_axes=SORT_XY, rotated_text=rotated_text)
        return ami_page

    # AmiPage

    def create_text_spans(self, sort_axes=None, rotated_text=False) -> list:
        """create text spans, from SVG element for page
        :param sort_axes: by X and/or Y
        :param rotated_text: iclude rotated text
        :return: self.text_spans
        """
        # remove line numbers and headers and footers
        # USED
        content_box = BBox(xy_ranges=self.CONTENT_RANGES)
        if not sort_axes:
            sort_axes = []
        # dot_len = 10 # in case we need dots in output
        if not self.text_spans or self.text_spans is not list:
            print(f"======== {self.page_path} =========")

            if self.page_path:
                self.page_element = lxml.etree.parse(str(self.page_path))
            elif self.data:
                self.page_element = lxml.etree.toxml(self.data)
            else:
                self.logger.warning("no svg file or data")
                return
            self.text_elements = self.page_element.findall(f"//{{{SVG_NS}}}text")
            self.create_text_spans_from_text_elements(content_box, rotated_text)
            for axis in sort_axes:
                if axis == X:
                    self.text_spans = sorted(self.text_spans, key=lambda span: span.start_x)
                if axis == Y:
                    self.text_spans = sorted(self.text_spans, key=lambda span: span.y)

                print(f"text_spans {axis}: {self.text_spans}")

        return self.text_spans

    def create_text_spans_from_text_elements(self, content_box, rotated_text):
        # USED
        self.text_spans = []
        for text_index, text_element in enumerate(self.text_elements):
            if text_element.attrib.get("rotateDegrees") and not rotated_text:
                # print(f"rotated text")
                continue
            svg_text = SvgText(text_element)
            text_span = svg_text.create_text_span()
            if not text_span:
                print(f"cannot create TextSpan")
                continue
            bbox = text_span.create_bbox()
            if not bbox.intersect(content_box):
                # print(f"outside content_box")
                continue

            if text_span.has_empty_text_content():
                # test for whitespace content
                # print(f"whitespace element skipped")
                continue
            # if (len(self.text_spans) % dot_len) == 0:
            #     print(".", end="")
            self.text_spans.append(text_span)
        print(f"no. text_spans {len(self.text_spans)}")

    # AmiPage

    def get_svg_text(self, index):
        """gets raw SvgText element (e.g. <climate10_:text>)"""
        if not self.text_elements or index < 0 or index >= len(self.text_elements):
            return None
        return SvgText(self.text_elements[index])

    def get_bounding_boxes(self) -> list:
        """get/create bounding boxes
        sort by XY
        """
        if not self.bboxes:
            self.bboxes = []
            self.create_text_spans(sort_axes=SORT_XY)
            for text_span in self.text_spans:
                bbox = text_span.create_bbox()
                self.bboxes.append(bbox)
        return self.bboxes

    def create_composite_lines(self) -> list:
        """overlaps textspans such as subscripts
        uses the bboxes
        will later create larger spans as union of any intersecting boxes
        not rigorous"""
        self.composite_lines = []
        self.create_text_spans(sort_axes=SORT_XY)
        if not self.text_spans:
            return []
        span0 = self.text_spans[0]
        composite_line = CompositeLine(bbox=span0.bbox)
        composite_line.text_spans.append(span0)
        self.composite_lines.append(composite_line)

        for text_span in self.text_spans[1:]:
            bbox = text_span.create_bbox().copy()
            bbox.expand_by_margin([X_MARGIN, 0])
            intersect_box = composite_line.bbox.intersect(bbox)
            if intersect_box:
                composite_line.bbox = composite_line.bbox.union(bbox)
            else:
                composite_line = CompositeLine(bbox=bbox)
                self.composite_lines.append(composite_line)
                composite_line.bbox = bbox.copy()

            composite_line.text_spans.append(text_span)

        change = True
        while change:
            change = self.merge_composite_lines()
        # print(f"merged")

        return self.composite_lines

    def merge_composite_lines(self):
        """tidy remaining overlapping composite_lines
        """
        last_composite_line = self.composite_lines[0]
        lines_for_deletion = []
        change = False
        for composite_line in self.composite_lines[1:]:
            overlap_box = last_composite_line.bbox.intersect(composite_line.bbox)
            if overlap_box:
                # print(f"overlap {overlap_box}")
                lines_for_deletion.append(last_composite_line)
                # print(f"composite_line {composite_line} last_composite {last_composite_line} before merge")
                composite_line.merge(last_composite_line)
                # print(f"composite_line {composite_line} after merge")
                composite_line.sort_spans(axis=X)
                change = True
            last_composite_line = composite_line
        # delete merged lien
        for composite_line in lines_for_deletion:
            self.composite_lines.remove(composite_line)
        return change

    def create_html(self, use_lines=False) -> E.html:
        """simple html with <p> children (will change later)"""
        self.get_bounding_boxes()
        self.create_composite_lines()
        html = E.html()
        body = E.body()
        html.append(body)
        if not use_lines or True:
            self.create_paragraphs()
            for paragraph in self.paragraphs:
                body.append(paragraph.create_html_p())
            return html
        for composite_line in self.composite_lines:
            text_spans = composite_line.create_sub_super_i_b_spans()
            if use_lines:
                h_p = E.p()
                for text_span in text_spans:
                    h_p.append(text_span)
                    body.append(h_p)
            else:
                for text_span in text_spans:
                    body.append(text_span)
        return html

    def create_paragraphs(self):
        """ """
        delta_ylist = self.get_inter_composite_spacings()
        if len(delta_ylist) > 0:
            mode = statistics.mode(delta_ylist)
            # print(f"mode {mode}")
            paragraph = AmiParagraph()
            self.paragraphs.append(paragraph)
            for deltay, composite_line in zip(delta_ylist, self.composite_lines[1:]):
                # print(f"{deltay} {composite_line}")
                if deltay > mode * INTERPARA_FACT:
                    paragraph = AmiParagraph()
                    self.paragraphs.append(paragraph)
                paragraph.composite_lines.append(composite_line)

    def get_inter_composite_spacings(self) -> list:
        """
        :return: list of interline spacings"""
        delta_y_list = []
        if self.composite_lines:
            last_line = self.composite_lines[0]
            for composite_line in self.composite_lines[1:]:
                delta_y = composite_line.bbox.get_yrange()[0] - last_line.bbox.get_yrange()[0]
                delta_y_list.append(delta_y)
                last_line = composite_line
        return delta_y_list

    # AmiPage

    # needs integrating
    def find_text_breaks_in_pagex(self, sortedq=None) -> dict:
        """create text spans, including

        """

        print(f"======== {self.page_path} =========")
        page_element = lxml.etree.parse(str(self.page_path))
        text_elements = page_element.findall(f"//{{{SVG_NS}}}text")
        print(f"no. texts {len(text_elements)}")
        text_breaks_by_line_dict = dict()
        for text_index, text_element in enumerate(text_elements):
            ami_text = SvgText(text_element)
            style_dict, text_break_list = ami_text.find_breaks_in_text(text_element)

            text_content = ami_text.get_text_content()
            if text_break_list:
                text_breaks_by_line_dict[text_index] = text_break_list
                current = 0
                offset = 0
                print(f"{text_index}: ", end='')
                for text_break in text_break_list:
                    # print(f"text_break: {text_break}")
                    print(f"{text_content[current:text_break - offset]}___", end='')
                    current = text_break
                    offset += 1
                    # TODO
                    text_elements.append()
                print(f"___ {text_content[current - offset:]}")
            else:
                # TODO
                new_text = TextSpan()
                # new_texts.append(tex)
        return text_breaks_by_line_dict

    # AmiPage

    # needs integrating
    def find_breaks_in_text(self, text_element):
        ami_text = SvgText(text_element)
        widths = ami_text.get_widths()
        x_coords = ami_text.get_x_coords()
        y_coord = ami_text.get_y_coord()
        text_content = ami_text.get_text_content()
        font_size = ami_text.get_font_size()
        pointer = 0
        breaks = []
        # this algorithm for breaks in line probably needs tuning
        for col in range(len(x_coords) - 1):
            deltax = float(int(100 * (x_coords[col + 1] - x_coords[col]))) / 100
            if deltax > FACT * widths[col] * font_size:
                if text_content[pointer:]:
                    breaks.append(col)
            else:
                pointer += 1
        style_dict = ami_text.extract_style_dict_from_svg()
        return style_dict, breaks

    def write_html(self, html_path: str, pretty_print: bool = False, use_lines: bool = False) -> None:
        """convenience method to create and write HTML
        :param html_path: path to write to
        :param pretty_print: pretty print HTML (may introduce spurious whitespace) default= False
        :param use_lines: retain PDF lines (mainly for debugging) default= False
        """

        # USED
        html = self.create_html(use_lines=use_lines)
        parent_dir = Path(html_path).parent
        if not parent_dir.exists():
            parent_dir.mkdir()
        with open(html_path, "wb") as f:
            et = lxml.etree.ElementTree(html)
            et.write(f, pretty_print=pretty_print)


class AmiSect:
    """Transformation of an Html Page to sections
    NOT Yet tested
    """

    def __init__(self):
        pass


class AmiParagraph:
    """holds a list of CompositeLines
    """

    def __init__(self):
        self.composite_lines = []

    def create_html_p(self):
        h_p = E.p()
        for composite_line in self.composite_lines:
            text_spans = composite_line.create_sub_super_i_b_spans()
            for span in text_spans:
                h_p.append(span)
        return h_p


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
        """create CSSStyle object from elem
        :param elem:
        """
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
        result = (self.BOLD in fontname) or (fontname.endswith(self.DOT_B)) if fontname else False
        return result

    def obeys(self, condition):
        """test if style obeys a (simple) condition
        (I'll write a DSL later)
        :param condition: (name, operator, value), e.g. "font-size>10
        :return: test of condition

        """
        result = False
        if condition:
            ss = re.split('(>|<|==|!=)', condition)
            if len(ss) != 3:
                print(f"Cannot parse as condition {condition}")
            else:
                lhs = ss[0].strip()
                rhs = ss[2].strip()

                # print(f"condition: {ss}")
                if lhs not in self.name_value_dict:
                    return False
                value1 = self.name_value_dict.get(lhs)
                if not value1:
                    print(f"{lhs} not in style attribute {self.name_value_dict}")
                    return False
                if value1.endswith("px"):
                    value1 = value1[:-2]
                try:
                    value1 = float(value1)
                except Exception:
                    print(f"not a number {value1}")
                    return False

                if rhs.endswith("px"):
                    rhs = rhs[:-2]
                try:
                    value2 = float(rhs)
                except Exception:
                    print(f"not a number {rhs}")
                    return False
                oper = ss[1]
                if oper == ">":
                    result = value1 > value2
                elif oper == "<":
                    result = value1 < value2
                elif oper == "!=":
                    result = value1 != value2
                elif oper == "==":
                    result = (value1 == value2)
                else:
                    raise ValueError(f"bad operator: {oper}")
                if result:
                    # print(f"condition TRUE {condition}")
                    pass
        return result


class CompositeLine:
    """holds text spans which touch or intersect and overall bbox"""

    def __init__(self, bbox=None):
        """constructs empty CompositeLine
        :param bbox: copies bbox if not None
        """
        self.bbox = bbox.copy() if bbox else None
        self.text_spans = []

    def __str__(self) -> str:
        s = f" spans: {len(self.text_spans)}:"
        for span in self.text_spans:
            s += f"__{span}"
        return s

    def sort_spans(self, axis=X) -> list:
        """sort spans by coordinate
        :param axis: X or Y
        :return: text_spans
        """
        self.text_spans = sorted(self.text_spans, key=lambda span: span.start_x)
        return self.text_spans

    def create_sub_super_i_b_spans(self) -> list:
        """creates a <p> with <span> or other inline children"""
        self.sort_spans(X)
        self.normalize_text_spans()

        last_span = None
        new_text_spans = []
        for text_span in self.text_spans:
            text_style = text_span.text_style
            content = text_span.text_content
            if not content:
                continue
            # bold/italic can be nested
            if text_style.font_weight == BOLD:
                content = E.b(content)
            if text_style.font_style == ITALIC:
                content = E.i(content)
            # super/subscripts wrap what has been created
            if HtmlUtil.is_superscript(last_span, text_span):
                content = E.sup(content)
            elif HtmlUtil.is_subscript(last_span, text_span):
                content = E.sub(content)
            else:
                content = E.span(content)
                HtmlUtil.set_attrib(content, FONT_FAMILY, text_style.font_family)
                HtmlUtil.set_attrib(content, FONT_SIZE, str(text_style.font_size))
                HtmlUtil.set_attrib(content, FILL, text_style.fill)
                HtmlUtil.set_attrib(content, Y, text_span.y)
                HtmlUtil.set_attrib(content, BBOX, text_span.bbox)
            new_text_spans.append(content)
            last_span = text_span
        self.text_spans = new_text_spans
        return self.text_spans

    def normalize_text_spans(self) -> None:
        """iterate over text_spans applying normalize_family_weight"""
        for text_span in self.text_spans:
            if Util.is_whitespace(text_span.text_content):
                print(f"whitespace")
            text_span.normalize_family_weight()

    def merge(self, other_line):
        self.bbox = other_line.bbox.union(self.bbox)
        self.text_spans.extend(other_line.text_spans)


class TextSpan:
    """holds text content and attributes
    can be transformed into HTML. Later in the conversion than AmiText
    """

    def __init__(self):
        self.y = None
        self.start_x = None
        self.end_x = None
        self.text_style = None
        self.text_content = ""
        self.bbox = None
        self.ami_text = None

    def __str__(self) -> str:
        s = self.xy + ": " + (self.text_content[:10] + "... " if self.text_content is not None else "")
        return s

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def xy(self) -> str:
        """convenience to return (x, y) as str"""
        return "(" + str(self.start_x) + "," + str(self.y) + ")" if (self.start_x and self.y) else ""

    # TextSpan

    def create_bbox(self) -> BBox:
        """bbox based on font-size and character position/width

        text goes in negative directiom as y is down the page
        """
        last_width = self.ami_text.get_last_width()
        if last_width is None:
            print(f"No widths???")
            last_width = 0.0
        font_size = self.text_style.font_size
        height = font_size
        width = self.end_x + last_width * font_size - self.start_x
        self.bbox = BBox.create_from_xy_w_h((self.start_x, self.y - height), width, height)
        return self.bbox

    def normalize_family_weight(self) -> None:
        """transforms font-family names into weights and styles
        Example: TimesRomanBoldItalic will set style=italic and weight=bold
        and reset family to TimesRoman

            """

        family = self.text_style.font_family
        if not family:
            print(f"no family: {self}")
            return
        family = family.lower()
        if family.find(ITALIC) != -1:
            self.text_style.font_style = ITALIC
        if family.find(BOLD) != -1:
            self.text_style.font_weight = BOLD
        if family.find(TIMES) != -1:
            self.text_style.font_family = TIMES
        if family.find(CALIBRI) != -1:
            self.text_style.font_family = CALIBRI
        if self.text_style.font_family not in FONT_FAMILIES:
            print(f"new font_family {self.text_style.font_family}")

    def has_empty_text_content(self) -> bool:
        return len("".join(self.text_content.split())) == 0


# arg_dict
MAXPAGE = "maxpage"
INDIR = "indir"
INPATH = "inpath"
OUTDIR = "outdir"
OUTFORM = "outform"
OUTSTEM = "outstem"
FLOW = "flow"
# FORMAT = "fmt"
IMAGEDIR = "imagedir"
RESOLUTION = "resolution"
TEMPLATE = "template"


class PDFArgs:
    def __init__(self):
        """arg_dict is set to default"""
        self.parser = None
        self.parsed_args = None
        self.arg_dict = self.create_default_arg_dict()

    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline

        """
        self.parser = argparse.ArgumentParser(description='PDF parsing')
        self.parser.add_argument("--maxpage", type=int, nargs=1, help="maximum number of pages", default=10)
        self.parser.add_argument("--indir", type=str, nargs=1, help="input directory")
        self.parser.add_argument("--inpath", type=str, nargs=1, help="input file")
        self.parser.add_argument("--outdir", type=str, nargs=1, help="output directory")
        self.parser.add_argument("--outform", type=str, nargs=1, help="output format ", default="html")
        self.parser.add_argument("--flow", type=bool, nargs=1, help="create flowing HTML (heuristics)", default=True)
        self.parser.add_argument("--imagedir", type=str, nargs=1, help="output images to imagedir")
        self.parser.add_argument("--resolution", type=int, nargs=1, help="resolution of output images (if imagedir)",
                                 default=400)
        self.parser.add_argument("--template", type=str, nargs=1, help="file to parse specific type of document (NYI)")
        self.parser.add_argument("--debug", type=str, choices=DEBUG_OPTIONS, help="debug these during parsing (NYI)")
        return self.parser

    # class PDFArgs:
    def process_args(self):
        """runs parsed args
        :return:
  --maxpage MAXPAGE     maximum number of pages
  --indir INDIR         input directory
  --infile INFILE [INFILE ...]
                        input file
  --outdir OUTDIR       output directory
  --outform OUTFORM     output format
  --flow FLOW           create flowing HTML (heuristics)
  --images IMAGES       output images
  --resolution RESOLUTION
                        resolution of output images
  --template TEMPLATE   file to parse specific type of document"""

        if self.arg_dict:
            fmt = self.arg_dict.get(OUTFORM)
            print(f"fmt: {fmt}")
            maxpage = self.arg_dict.get(MAXPAGE)
            indir = self.arg_dict.get(INDIR)
            inpath = self.arg_dict.get(INPATH)
            outdir = self.arg_dict.get(OUTDIR)
            outstem = self.arg_dict.get(OUTSTEM)
            flow = self.arg_dict.get(FLOW) is not None
            self.convert_write(maxpage=maxpage, outdir=outdir, outstem=outstem, fmt=fmt, inpath=inpath, flow=True)

    def create_arg_dict(self):
        print(f"PARSED_ARGS {self.parsed_args}")
        if not self.parsed_args:
            return None
        arg_vars = vars(self.parsed_args)
        self.arg_dict = dict()
        for item in arg_vars.items():
            key = item[0]
            if item[1] is None:
                pass
            elif type(item[1]) is list and len(item[1]) == 1:
                self.arg_dict[key] = item[1][0]
            else:
                self.arg_dict[key] = item[1]

        return self.arg_dict

    # class PDFArgs:
    @classmethod
    def convert_pdf(cls,
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
        device, interpreter, retstr = PDFArgs.create_interpreter(fmt)

        fp = open(path, "rb")
        print(f"maxpages: {maxpages}")
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

    # class PDFArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[OUTFORM] = "html.flow"
        arg_dict[MAXPAGE] = 5
        arg_dict[INDIR] = None
        arg_dict[INPATH] = None
        arg_dict[OUTDIR] = None
        arg_dict[OUTSTEM] = None
        arg_dict[FLOW] = True
        return arg_dict

    @classmethod
    def create_interpreter(cls, fmt, codec: str = "UTF-8"):
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
        converters = {"text": TextConverter, "html": HTMLConverter, "flow.html": HTMLConverter, "xml": XMLConverter}
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

    # class PDFArgs:

    def convert_write(self, fmt=None, maxpage=999999, outdir=None, outstem=None, inpath=None, flow=False):
        """
        create HTML (absolute or flowing) or XML
        The preferred method is to use arg_dict
        :param fmt: format html/xml/text
        :param maxpage: if 0, writes all else staops at maxpages
        :param outdir: output dir
        :param outstem: stem of output file
        :param inpath: input file
        :param flow: remove absolute position so text can flow
        """
        if self.arg_dict:
            maxp = self.arg_dict.get(MAXPAGE)
            maxpage = int(maxp) if maxp else maxpage
            outd = self.arg_dict.get(OUTDIR)
            outdir = outd if outd else outdir
            outs = self.arg_dict.get(OUTSTEM)
            outdir = outs if outs else outstem
            inp = self.arg_dict.get(INPATH)
            inpath = inp if inp else inpath
            if fm := self.arg_dict.get(OUTFORM):
                fmt = fm
            if fl := self.arg_dict.get(FLOW):
                flow = fl

            # header_offset = -50
            header_height = 90
            # page_height = 892
            # page_height_cm = 29.7
            footer_height = 90

        print(f"==============CONVERT================")
        if fmt == "html.flow":
            fmt = "html"
            flow = True
        result = PDFArgs.convert_pdf(path=inpath, fmt=fmt, maxpages=maxpage)

        if flow:
            tree = lxml.etree.parse(StringIO(result), lxml.etree.HTMLParser())
            result_elem = tree.getroot()
            add_ids(result_elem)
            # this is slightly tacky
            PDFUtil.remove_descendant_elements_by_tag("br", result_elem)
            PDFUtil.remove_style(result_elem, [
                "position",
                # "left",
                "border",
                "writing-mode",
                "width",  # this disables flowing text
            ])
            PDFUtil.remove_empty_elements(result_elem, ["span"])
            PDFUtil.remove_empty_elements(result_elem, ["div"])
            PDFUtil.remove_lh_line_numbers(result_elem)
            PDFUtil.remove_large_fonted_elements(result_elem)
            marker_xpath = ".//div[a[@name]]"
            offset, pagesize, page_coords = PDFUtil.find_constant_coordinate_markers(result_elem, marker_xpath)
            PDFUtil.remove_headers_and_footers(result_elem, pagesize, header_height, footer_height, marker_xpath)
            PDFUtil.remove_style_attribute(result_elem, "top")
            PDFUtil.remove_style(result_elem, ["left", "height"])
            HtmlTree.make_tree(result_elem, output_dir=outd)

            result = lxml.etree.tostring(result_elem).decode("UTF-8")
            fmt = "flow.html"
        if not outdir:
            indir = Path(inpath).parent
            outdir = indir
            print(f"no outdir given, taking input {indir}")
            outstem = Path(inpath).stem
            outfile = Path(outdir, f"{outstem}.{fmt}")
        print(f"outfile {outfile}")
        with open(str(outfile), "w") as f:
            f.write(result)
            print(f"wrote {f.name}")

    # class PDFArgs:
    def process1_args(self):
        self.create_arg_parser()
        if len(sys.argv) == 1:  # no args, print help
            self.parser.print_help()
        else:
            self.parsed_args = self.parser.parse_args(sys.argv[1:])
            self.arg_dict = self.create_arg_dict()
            self.process_args()


class HtmlTree:
    """builds a tree from a flat set of Html elemnets"""

    @classmethod
    def make_tree(cls, elem, output_dir):
        """find decimal number for tree"""
        markers = ["Chapter",
                   # "Table of Contents",
                   "Table of",  # one is concatenated (Chapter01) so abbreviate, unweighted Chap16
                   # "Executive Summary",
                   "Executive",  # case variation
                   # "Frequently Asked Questions", # not in Chapter01
                   "Frequently",  # case variation
                   "References",
                   ]
        is_bold = True
        font_size_range = (12, 999)
        for marker in markers:
            marked_div, divs = cls.get_div_span_starting_with(elem, marker, is_bold, font_size_range=font_size_range)
            if not marked_div:
                l = len(divs) if divs else 0
                print(f"Cannot find marker {marker} found {l} markers")
        decimal_divs = cls.get_div_spans_with_decimals(elem, is_bold, font_size_range=font_size_range)
        print(f"d_divs {len(decimal_divs)}")
        if output_dir:
            if not output_dir.exists():
                output_dir.mkdir()
            for i, child_div in enumerate(decimal_divs):
                cls.remove_div(child_div)
                marker = child_div.attrib["marker"].strip().replace(" ", "_").lower() # name from text content
                path = Path(output_dir, f"{marker}.html")
                with open(path, "wb") as f:
                    f.write(lxml.etree.tostring(child_div, pretty_print=True))
            print(f"decimals: {len(decimal_divs)}")

    @classmethod
    def get_div_span_starting_with(cls, elem, strg, is_bold=False, font_size_range=None):
        result = None
        xpath = f".//div[span[starts-with(.,'{strg}')]]"
        print(f"xpath {xpath}")
        divs = elem.xpath(xpath)
        if len(divs) == 0:
            print(f"No divs with {strg}")
            return result, None
        print(f"found divs {len(divs)}")
        new_divs = []
        for div in divs:
            spans = div.xpath("./span")
            if spans:
                css_style = CSSStyle.create_css_style(spans[0])
                if not (is_bold and css_style.is_bold_name()):
                    continue
                if not (font_size_range and cls.in_range(css_style.font_size, font_size_range)):
                    continue
                new_divs.append(div)
                pass
        divs = new_divs
        # also test font here NYI
        if len(divs) == 0:
            print(f"cannot find div: len={len(divs)}")
        elif len(divs) > 1:
            print(f"too many divs: len={len(divs)}")
        else:
            result = divs[0]
            print(f"marked with {strg} : {''.join(result.itertext())}")
            result.attrib["marker"] = strg
        return (result, divs)

    @classmethod
    def get_div_spans_with_decimals(cls, elem, is_bold=None, font_size_range=None):
        """Matches div/span starting with a decimal index
        d.d or d.d.d
        """
        result = None
        # first add all matching numbered divs to pre_chapsec
        H_DIV = "div"
        top_div = lxml.etree.SubElement(elem, H_DIV)
        top_div.attrib[CLASS] = TREE_ROOT
        pre_chapsec = lxml.etree.SubElement(top_div, H_DIV)
        pre_chapsec.attrib[CLASS] = PRE_CHAPSEC
        current_div = pre_chapsec

        # iterate over all divs, only append those with decimal
        divs = elem.xpath(ALL_DIV_XPATHS)
        print(f"found divs {len(divs)}")
        decimal_count = 0
        texts = [] # just a check at present
        section_re = CHAP_TOP
        # section_re = CHAP_SECTIONS_RE
        # section_re = CHAP_SUBSECTS_RE
        for div in divs:
            spans = div.xpath("./span")
            if not spans:
                # no spans, concatenate with siblings
                current_div.append(div)
                continue
            css_style = CSSStyle.create_css_style(spans[0])  # normally comes first
            # check weight, if none append to siblings
            if not (is_bold and css_style.is_bold_name()):
                current_div.append(div)
                continue
            # check font-size, if none append to siblings
            if not (font_size_range and cls.in_range(css_style.font_size, font_size_range)):
                current_div.append(div)
                continue
            # span content
            text = ''.join(spans[0].itertext())
            matched = False
            if section_re.match(text):
                top_div.append(current_div)
                texts.append(text)
                div.attrib[MARKER] = text
                current_div = div
                decimal_count += 1
            else:
                current_div.append(div)
        print(f"{CHAP_SECTIONS_RE}: {decimal_count} {len(top_div.xpath('./*'))} {texts}")
        return top_div

    @classmethod
    def in_range(cls, num, num_range):
        """is a number in a numeric range"""
        assert num_range or len(num_range) == 2, f"range must have 2 elements"
        assert num_range[0] <= num_range[1], f"font_size_range must be (lower,higher)"
        assert float(num_range[0])
        result = num_range[0] <= num <= num_range[1]
        return result

    @classmethod
    def remove_div(cls, child_div):
        text_re = re.compile(""
            "(Final Government Distribution)|"
            # "(Chapter\\s*\\d+\\s*)|"
            # "(Page\s*\d+\s*)|"
            "(IPCC WGIII AR6)",
                             )
        xml = lxml.etree.tostring(child_div)
        print(f"xml {xml[:100]}")
        spans = child_div.xpath("./div/span")
        if len(spans) > 0:
            text = ''.join(spans[0].itertext()).strip()
            print(f"text {text}")
            if text_re.search(text):
                print(f"{text}")


class PDFDebug:
    @classmethod
    def debug_page_properties(cls, page, debug=None):
        """debug print selected DEBUG_OPTIONS
        :param debug: list of options (from DEBUG_OPTIONS)
        """
        if not debug:
            debug = []
            print(f"no optiomns given, choose from: {DEBUG_OPTIONS}")
        if DEBUG_ALL in debug:
            debug = DEBUG_OPTIONS
        print(f"\n\n======page: {page.page_number} ===========")
        if WORDS in debug:
            cls.print_words(page)
        if LINES in debug:
            cls.print_lines(page)
        if RECTS in debug:
            cls.print_rects(page, debug=False)
        if CURVES in debug:
            cls.print_curves(page)
        if IMAGES in debug:
            cls.print_images(page)
        if TABLES in debug:
            cls.print_tables(page)
        if HYPERLINKS in debug:
            cls.print_hyperlinks(page)
        if ANNOTS in debug:
            cls.print_annots(page)

    @classmethod
    def print_words(cls, page):
        print(f"words {len(page.extract_words())}", end=" | ")

    @classmethod
    def print_lines(cls, page):
        if (n_line := len(page.lines)) > 0:
            print(f"lines {n_line}", end=" | ")

    @classmethod
    def print_rects(cls, page, debug=False):
        if n_rect := len(page.rects) > 0:
            print(f"rects {n_rect}", end=" | ")
            if debug:
                for rect in page.rects[:PDFDebug.MAX_RECT]:
                    print(f"rect (({rect['x0']},{rect['x1']}),({rect['y0']},{rect['y1']})) ")

    @classmethod
    def print_curves(cls, page):
        if n_curve := len(page.curves) > 0:
            print(f"curves {n_curve}", end=" | ")
            for curve in page.curves[:PDFDebug.MAX_CURVE]:
                print(f"keys: {curve.keys()}")
                print(f"curve {curve['points']}")

    @classmethod
    def print_images(cls, page, maximage=10, outdir=None):
        write_image = True
        resolution = 400  # may be better
        from pdfminer.image import ImageWriter
        from pdfminer.layout import LTImage
        if not outdir:
            print(f"no output dir given")
            return
        if n_image := len(page.images) > 0:
            print(f"images {n_image}", end=" | ")
            for i, image in enumerate(page.images[:maximage]):
                print(f"image: {type(image)}: {image.values()}")

                path = Path(outdir, "images")
                if not path.exists():
                    path.mkdir()
                if isinstance(image, LTImage):
                    imagewriter = ImageWriter(str(Path(path, f"image{i}.png")))
                    imagewriter.export_image(image)
                page_height = page.height
                image_bbox = (image[X0], page_height - image[Y1], image[X1], page_height - image[Y0])
                print(f"image: {image_bbox}")

                cropped_page = page.crop(image_bbox)  # crop screen display (may have overwriting text)
                image_obj = cropped_page.to_image(resolution=resolution)
                path1 = Path(path, f"image_{page.page_number}_{i}_{cls.format_bbox(image_bbox)}.png")
                if write_image:
                    image_obj.save(path1)
                    print(f" wrote image {path1}")
                continue

                # for p in pdf.pages:
                #     for obj in p.layout:
                #         if isinstance(obj, LTImage):
                #             imagewriter.export_image(obj)

    @classmethod
    def print_tables(cls, page, odir=None):
        tables = page.find_tables()

        if n_table := len(tables) > 0:
            print(f"tables {n_table}", end=" | ")
            print(f"table_dir {tables[0].__dir__()}")
            for i, table in enumerate(tables[:PDFDebug.MAX_TABLE]):
                h_table = cls.create_table_element(table)
                table_file = Path(odir, f"table_{i + 1}.html")
                cls.print_table_element(h_table, table_file)

    @classmethod
    def print_table_element(cls, h_table, table_file):
        h_str = lxml.etree.tostring(h_table, encoding='UTF-8', xml_declaration=False)
        with open(table_file, "wb") as f:
            f.write(h_str)
            print(f"wrote {table_file}")

    @classmethod
    def create_table_element(cls, table):
        h_table = lxml.etree.Element(H_TABLE)
        h_thead = lxml.etree.SubElement(h_table, H_THEAD)
        h_tbody = lxml.etree.SubElement(h_table, H_TBODY)
        table_lists = table.extract()  # essentially a list of lists
        for table_row in table_lists:
            h_row = lxml.etree.SubElement(h_tbody, H_TR)
            for cell_value in table_row:
                h_td = lxml.etree.SubElement(h_row, H_TD)
                h_td.text = str(cell_value)
        return h_table

    @classmethod
    def format_bbox(cls, bbox: tuple):
        return f"{int(bbox[0])}_{int(bbox[2])}_{int(bbox[1])}_{int(bbox[3])}"

    @classmethod
    def print_hyperlinks(cls, page):
        if n_hyper := len(page.hyperlinks) > 0:
            print(f"hyperlinks {n_hyper}", end=" | ")
            for hyperlink in page.hyperlinks:
                print(f"hyperlink {hyperlink.values()}")

    @classmethod
    def print_annots(cls, page):
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


class TextStyle:
    # try to map onto HTML italic/normal
    def __init__(self):
        # maybe should be dict
        self.font_style = None
        # height in pixels
        self.font_size = None
        self.font_family = None
        # try to map onto HTML bold/norma
        self.font_weight = None
        # fill colour of text
        self.fill = None
        # stroke colour of text
        self.stroke = None

    def __str__(self) -> str:
        s = f"size {self.font_size} family {self.font_family}, style {self.font_style} weight {self.font_weight} fill {self.fill} stroke {self.stroke}"
        return s

    def difference(self, other) -> str:
        """difference between two TextStyles (self and other)
        :param other: style to compare to self
        :return: string representation of differences (or "")
        """

        if other is None:
            return "none"
        s = ""
        s += self._difference("font-size", self.font_size, other.font_size)
        s += self._difference("; font-style", self.font_style, other.font_style)
        s += self._difference("; font-family", self.font_family, other.font_family)
        s += self._difference("; font-weight", self.font_weight, other.font_weight)
        s += self._difference("; fill", self.fill, other.fill)
        s += self._difference("; stroke", self.stroke, other.stroke)
        return s

    @classmethod
    def _difference(cls, name, val1, val2) -> str:
        s = ""
        if not val1 and not val2:
            pass
        elif not val1 or not val2 or val1 != val2:
            s = f"{name}: {val1} => {val2}"
        return s


class PDFParser:
    def __init__(self):
        self.indir = None
        self.infile = None
        self.outdir = None
        self.outform = "html"
        self.flow = True
        self.maxpage = 9999999
        self.resolution = 400
        self.template = None
        self.images = None

    @classmethod
    def create_from_argparse(cls, parser):
        pdf_parser = PDFParser()
        print(f"NYI, create from arg_parse")
        return pdf_parser


class PDFUtil:
    """utility routieses which need extracting into classes"""

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
    def remove_descendant_elements_by_tag(cls, tag, result_elem):
        lxml.etree.strip_tags(result_elem, tag)

    @classmethod
    def remove_style(cls, xpath_root_elem, names):
        """removes name-value pairs from css-style and reapply to xpath'ed elements"""
        xpath = f".//*[@style]"
        # print(f"xpath: {xpath}")
        try:
            styled_elems = xpath_root_elem.xpath(xpath)
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
            if condition:
                if css_style.obeys(condition):
                    # print(f"{elem} obeys {condition}")
                    if remove:
                        cls.remove_elem_keep_tail(el)

    @classmethod
    def remove_headers_and_footers(cls, ref_elem, pagesize, header_height, footer_height, marker_xpath):
        elems = ref_elem.xpath(marker_xpath)

        for elem in ref_elem.xpath("//*[@style]"):
            top = CSSStyle.create_css_style(elem).get_numeric_attval("top")  # the y-coordinate
            if top:
                top = top % pagesize
                if top < header_height or top > pagesize - footer_height:
                    cls.remove_elem_keep_tail(elem)

    @classmethod
    def remove_lh_line_numbers(cls, ref_elem):
        cls.find_elements_with_style(ref_elem, ".//*[@style]", "left<49", remove=True)

    @classmethod
    def remove_style_attribute(cls, ref_elem, style_name):
        elems = ref_elem.xpath(".//*")
        for el in elems:
            css_style = CSSStyle.create_css_style(el)
            if css_style.name_value_dict.get(style_name):
                css_style.name_value_dict.pop(style_name)
                css_style.apply_to(el)

    @classmethod
    def remove_large_fonted_elements(cls, ref_elem):
        cls.find_elements_with_style(ref_elem, ".//*[@style]", "font-size>30", remove=True)

    @classmethod
    def find_constant_coordinate_markers(cls, ref_elem, xpath, style="top"):
        """
        finds a line with constant difference from top of page
<div style="top: 50px;"><a name="1">Page 1</a></div>
        """

        elems = ref_elem.xpath(xpath)
        coords = []
        for elem in elems:
            css_style = CSSStyle.create_css_style(elem)
            coord = css_style.name_value_dict.get(style)
            if coord:
                try:
                    coords.append(float(coord[:-2]))
                except Exception:
                    print(f"cannot parse {coord} for {style}")
        np_coords = np.array(coords)
        x = np.array(range(np_coords.size)).reshape((-1, 1))
        # print(x, coords)
        model = LinearRegression().fit(x, coords)
        r_sq = model.score(x, coords)
        # print(f"coefficient of determination: {r_sq} intercept {model.intercept_} slope {model.coef_}")
        if r_sq < 0.98:
            print(f"cannot calculate offset reliably")
        return model.intercept_, model.coef_, np_coords


class SvgText:
    """wrapper for svg_text elemeent.
    creates TextStyle, TextSpan, coordinates, etc.
    Only used in transformations
    heuristic
    """

    def __init__(self, svg_text_elem):
        """create from svg_text"""
        self.svg_text_elem = svg_text_elem
        self.text_span = None
        self.create_text_span()

    def create_text_span(self) -> TextSpan:
        """create TextSpan from style, coords and text_content
        :return: TextSpan or None"""
        if self.text_span is None:
            self.text_span = TextSpan()
            self.text_span.ami_text = self
            self.text_span.text_style = self.create_text_style()
            self.text_span.text_content = self.get_text_content()
            self.text_span.start_x = self.get_x_coord()
            self.text_span.end_x = self.get_x_coords()[-1]
            self.text_span.y = self.get_y_coord()
            self.text_span.widths = self.get_widths()
            self.text_span.create_bbox()
        return self.text_span

    # AmiText

    def create_text_style(self) -> TextStyle:
        """create TextStyle from style attributes"""
        style = TextStyle()
        # style.y = self.get_y_coord()
        # style.x = self.get_x_coord()
        style.font_size = self.get_font_size()
        style.font_family = self.get_font_family()
        style.font_style = self.get_font_style()
        style.font_weight = self.get_font_weight()
        style.fill = self.get_fill()
        style.stroke = self.get_stroke()
        return style

    def get_fill(self) -> str:
        """get fill colour
        :return: colour (unnormalized)"""
        return self.svg_text_elem.attrib.get(FILL)

    def get_x_coords(self) -> list:
        """get list of x-coords from SVG"""
        return self.get_float_vals(X)

    def get_x_coord(self) -> float:
        """get first X-coord
        :return: first x_coord in list or None"""
        x_coords = self.get_x_coords()
        return x_coords[0] if x_coords else None

    def get_y_coord(self) -> float:
        """get single Y-coord"""
        return self.get_float_val(Y)

    # AmiText

    def get_widths(self) -> list:
        """list of character widths
        These are provided by the PDF or other document. They are
        fractions of pixel size (i.e. font-size = 12 and width=0.8
        gives screen width of 9.6px
        """

        return self.get_float_vals(f"{{{SVGX_NS}}}{WIDTH}")

    def get_last_width(self):
        """width of last character
        needed for bbox calculation.
        The x-extent of array of coordinates is last_coord + last_width*font-size
        :return: last width or 0.0 if none
        """
        widths = self.get_widths()
        return 0.0 if widths is None or len(widths) == 0 else widths[-1]

    def extract_style_dict_from_svg(self) -> dict:
        """translates climate10_ style attribute into dictionary
        names are whatever are contained in the SVG and not checked
        SVG format is name1:val1;name2:val2 ... and these are translated
        literally into a dict()
        """
        style_dict = dict()
        style = self.svg_text_elem.attrib.get(STYLE)
        styles = style.split(';')
        for s in styles:
            if len(s) > 0:
                ss = s.split(":")
                style_dict[ss[0]] = ss[1]
        return style_dict

    # AmiText

    def get_font_family(self) -> str:
        """get font-family from SVG style
        No checking on values
        """

        sd = self.extract_style_dict_from_svg()
        fs = sd.get(FONT_FAMILY)
        return fs

    def get_font_size(self) -> float:
        """font-size from SVG style attribute
        :return: size without "px" units"""
        sd = self.extract_style_dict_from_svg()
        fs = sd.get(FONT_SIZE)
        fs = fs[:-2]
        return float(fs)

    def get_font_weight(self) -> str:
        """font weight as string
        No checking on values (normally "bold" or None)
        :return: weight"""
        sd = self.extract_style_dict_from_svg()
        return sd.get(FONT_WEIGHT)

    def get_font_style(self) -> str:
        """font style as string
        :return: normallu "italic" or None
        """
        sd = self.extract_style_dict_from_svg()
        return sd.get(FONT_STYLE)

    def get_stroke(self) -> str:
        """stroke for character
        rarely used?
        :return: stroke normallyn as rgb?"""

        return self.extract_style_dict_from_svg().get(STROKE)

    def get_text_content(self) -> str:
        """convenience to get text content
        (saves me remembering the code with join())
        :return: "" is empty else content"""
        return ''.join(self.svg_text_elem.itertext())

    # AmiText

    def get_float_vals(self, attname) -> list:
        """gets list of floats if possible, else Exception
        :param attname:
        :return: list of floats
        :except: ValueError if any conversion fails"""
        attval = self.svg_text_elem.attrib.get(attname)
        if attval:
            ss = attval.split(',')
            try:
                vals = [float(s) for s in ss]
            except Exception as e:
                raise ValueError("cannot convert to floats", e)
            return vals
        return []

    def get_float_val(self, attname) -> float:
        """gets float value of attribute
        :param attname: attribute name
        :return: f;oat value or None if not possible"""
        attval = self.svg_text_elem.attrib.get(attname)
        try:
            return float(attval)
        except Exception as e:
            pass


class HtmlUtil:
    """utilities for Html (lxml)
    """

    @classmethod
    def is_subscript(cls, last_span, this_span) -> bool:
        """is this_span a subscript?
        uses heuristics in is_script_type
        :param last_span: preceding span (if None returns False)
        :param this_span: span to test
        :return: True if this span is smaller and "lower" than last"""
        return cls.is_script_type(last_span, this_span, script_type=SScript.SUB)

    @classmethod
    def is_superscript(cls, last_span, this_span) -> bool:
        """is this_span a superscript?
        uses heuristics in is_script_type
        :param last_span: preceding span (if None returns False)
        :param this_span: span to test
        :return: True if this span is smaller and "higher" than last"""
        return cls.is_script_type(last_span, this_span, script_type=SScript.SUP)

    @classmethod
    def is_script_type(cls, last_span, this_span, script_type) -> bool:
        """heuristc to determine whether this_span is a sub/superscript of last_span
        NOTE: as Y is DOWN the page, a superscript has SMALLER y-value, etc.
        :param last_span: if None, returns false
        :param this_span: if not smaller by SCRIPT_FACT return False
        :param script_type: SUB or SUP
        :return: True if smaller and moved in right y-direction
        """
        if last_span is None:
            return False
        last_font_size = last_span.text_style.font_size
        this_font_size = this_span.text_style.font_size
        # is it smaller?
        if this_font_size < SCRIPT_FACT * last_font_size:
            last_y = last_span.y
            this_y = this_span.y
            if script_type == SScript.SUB:
                # is it lowered? Y DOWN
                return last_y < this_y
            elif script_type == SScript.SUP:
                # is it raised? Y DOWN
                return last_y > this_y
            else:
                raise ValueError("bad script type ", script_type)
        else:
            return False

    @classmethod
    def set_attrib(cls, element, attname, attvalue):
        """convenience method to set attribute value
        """
        if element is None:
            raise ValueError("element is None")
        if attname and attvalue:
            element.set(attname, str(attvalue))

    @classmethod
    def get_text_content(cls, elem):
        return ''.join(elem.itertext())

    @classmethod
    def is_chapter_or_tech_summary(cls, span_text):
        return span_text.startswith(CHAPTER) or span_text.startswith(TECHNICAL_SUMMARY)
