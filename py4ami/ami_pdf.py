""" Mainly for converting PDF to HTML and SVG """
import argparse
import copy
import logging
import os.path
import re
import statistics
import sys
import textwrap
import traceback
from io import BytesIO, StringIO
from pathlib import Path
from typing import Container

import lxml
import lxml.html
import numpy as np
import pdfplumber
from PIL import Image
from lxml import etree
from lxml.builder import E
from pdfminer.converter import TextConverter, XMLConverter, HTMLConverter
from pdfminer.image import ImageWriter
from pdfminer.layout import LAParams
from pdfminer.layout import LTImage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from sklearn.linear_model import LinearRegression

from py4ami.ami_html import H_SPAN, H_A, A_HREF, H_TR, H_TD, H_TABLE, H_THEAD, H_TBODY
from py4ami.ami_html import HtmlUtil, CSSStyle, HtmlTree, AmiSpan
from py4ami.ami_html import STYLE, BOLD, ITALIC, FONT_FAMILY, FONT_SIZE, FONT_WEIGHT, FONT_STYLE, STROKE, FILL, TIMES, \
    CALIBRI, FONT_FAMILIES, H_DIV, H_BODY
# local
from py4ami.bbox_copy import BBox  # this is horrid, but I don't have a library
from py4ami.util import Util, AbstractArgs

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
SCRIPT_FACT = 0.9  # should this be here

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

# character properties
P_FONTNAME = "fontname"
P_HEIGHT = "height"
P_STROKING_COLOR = "stroking_color"
P_NON_STROKING_COLOR = "non_stroking_color"

P_X0 = "x0"
P_X1 = "x1"
P_Y0 = "y0"
P_Y1 = "y1"
P_TEXT = "text"

# Unwanted sections
U_XPATH = "xpath"
U_REGEX = "regex"

IPCC_CHAP_TOP_REC = re.compile(""
                               "(Chapter\\s?\\d\\d?\\s?:.*$)|"
                               "(Table\\s?of Contents.*)|"
                               "(Executive [Ss]ummary.*)|"
                               "(Frequently [Aa]sked.*)|"
                               "(References)"
                               )
SECTIONS_DECIMAL_REC = re.compile("\\d+\\.\\d+$")
SUBSECTS_DECIMAL_REC = re.compile("\\d+\\.\\d+\\.\\d+$")

RECS_BY_SECTION = {
    HtmlTree.CHAP_TOP: IPCC_CHAP_TOP_REC,
    HtmlTree.CHAP_SECTIONS: SECTIONS_DECIMAL_REC,
    HtmlTree.CHAP_SUBSECTS: SUBSECTS_DECIMAL_REC,
}

# coordinates
X0 = 'x0'
Y1 = 'y1'
X1 = 'x1'
Y0 = 'y0'


class AmiPage:
    """Transformation of an SVG Page from PDFBox/Ami3
    consists of paragraphs, divs, textlines, etc.
    Used as a working container, utimately being merged with
    neighbouring documents into complete HTML document

    Now including HTML divs and spans from PDF
    MESSY (because PDF is horrible)
    """
    CONTENT_RANGES = [[56, 999], [45, 780]]
    DEFAULT_BBOX = BBox(xy_ranges=[[0, 9999], [0, 9999]])

    def __init__(self):
        # a mess because it started with SVG and new we are adding PDF
        # path of SVG page
        self.page_path = None
        # raw parsed SVG
        self.page_element = None
        # child elements of type <climate10_:text>
        self.text_elements = None
        # spans created from text_elements
        self.text_spans = []
        # bboxes of the spans
        self.bboxes = []
        # composite lines (i.e. with sub/superscripts, bold, italic
        self.composite_lines = []
        # paragraphs from inter-composite spacing
        self.paragraphs = []
        # AmiSpans built from characters from pdf
        self.ami_spans = []

    @classmethod
    def create_page_from_ami_spans_from_pdf(cls, ami_spans, bboxes=None):
        """
        create from raw AmiSpans (probably created from PDF)
        Tidying into divs, etc is done elsewhere
        :param ami_spans: list of AmiSpans possibly in document order
        :param bboxes: boxes within which spans must fit (if None accept everything)
        :return: AmiPage (containing AmiSpans) or None
        """
        ami_page = None
        if ami_spans:
            ami_page = AmiPage()
            for ami_span in ami_spans:
                ami_page.ami_spans.append(copy.deepcopy(ami_span))


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

    def create_text_spans(self, sort_axes=None, rotated_text=False, debug=False) -> list:
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
            if debug:
                print(f"======== {self.page_path} =========")

            if self.page_path:
                self.page_element = lxml.etree.parse(str(self.page_path))
            elif self.data:  # not sure if this is used
                self.page_element = lxml.etree.fromstring(self.data)
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
                if debug:
                    print(f"text_spans {axis}: {self.text_spans}")

        return self.text_spans

    def create_text_spans_from_text_elements(self, content_box, rotated_text):
        # USED
        self.text_spans = []
        for text_index, text_element in enumerate(self.text_elements):
            if text_element.attrib.get("rotateDegrees") and not rotated_text:
                continue
            svg_text = SvgText(text_element)
            text_span = svg_text.create_text_span()
            if not text_span:
                print(f"cannot create TextSpan")
                continue
            bbox = text_span.create_bbox()
            if not bbox.intersect(content_box):
                continue

            if text_span.has_empty_text_content():
                # test for whitespace content
                continue
            self.text_spans.append(text_span)

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

    # AmiPage

    def create_composite_lines(self) -> list:
        """overlaps textspans such as subscripts
        uses the bboxes
        will later create larger spans as union of any intersecting boxes
        not rigorous"""
        self.composite_lines = []
        self.create_text_spans(sort_axes=SORT_XY)
        if not self.text_spans:
            return self.composite_lines

        return self.create_composite_lines_from_text_spans()

    def create_composite_lines_from_text_spans(self):
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
                lines_for_deletion.append(last_composite_line)
                composite_line.merge(last_composite_line)
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
            paragraph = AmiParagraph()
            self.paragraphs.append(paragraph)
            for deltay, composite_line in zip(delta_ylist, self.composite_lines[1:]):
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
                    current = text_break
                    offset += 1
                    # TODO
                    text_elements.append()
                print(f"___ {text_content[current - offset:]}")
            else:
                # TODO
                new_text = TextSpan()
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

    # AmiPage

    @classmethod
    # TODO should be new class
    def chars_to_spans(cls, bbox, input_pdf, page_no):
        with pdfplumber.open(input_pdf) as pdf:
            pdf_page = pdf.pages[page_no]
            ami_page = AmiPage()
            # print(f"crop: {page0.cropbox} media {page0.mediabox}, bbox {page0.bbox}")
            # print(f"rotation: {page0.rotation} doctop {page0.initial_doctop}")
            # print(f"width {page0.width} height {page0.height}")
            # print(f"text {page0.extract_text()[:2]}")
            # print(f"words {page0.extract_words()[:3]}")
            #
            # print(f"char {page0.chars[:1]}")
            span = None
            span_list = []
            maxchars = 999999
            ndec_coord = 3  # decimals for coords
            ndec_fontsize = 2
            html = HtmlUtil.create_skeleton_html()
            top_div = lxml.etree.SubElement(html.xpath(H_BODY)[0], H_DIV)
            top_div.attrib["class"] = "top"
            for ch in pdf_page.chars[:maxchars]:
                if cls.skip_rotated_text(ch):
                    continue
                x0, x1, y0, y1 = cls.get_xy_tuple(ch, ndec_coord)
                if bbox and not bbox.contains_point((x0, y0)):
                    # print(f" outside box: {x0, y0}")
                    continue

                text_style = TextStyle()
                text_style.set_font_family(ch.get(P_FONTNAME))
                text_style.set_font_size(ch.get(P_HEIGHT), ndec=ndec_fontsize)
                text_style.stroke = ch.get(P_STROKING_COLOR)
                text_style.fill = ch.get(P_NON_STROKING_COLOR)

                # style or y0 changes
                if not span or not span.text_style or span.text_style != text_style or span.y0 != y0:
                    # cls.debug_span_changed(span, text_style, y0)
                    span = AmiSpan()
                    span_list.append(span)
                    span.text_style = text_style
                    span.y0 = y0
                    span.x0 = x0  # set left x
                span.x1 = x1  # update right x, including width
                span.string += ch.get(P_TEXT)

            # top_div = lxml.etree.Element(H_DIV)
            div = lxml.etree.SubElement(top_div, H_DIV)
            last_span = None
            for span in span_list:
                if last_span is None or last_span.y0 != span.y0:
                    div = lxml.etree.SubElement(top_div, H_DIV)
                last_span = span
                span.create_and_add_to(div)
        for ch in pdf_page.chars[:maxchars]:
            col = ch.get('non_stroking_color')
            if col:
                logging.debug(f"txt {ch.get('text')} : col {col}")
        # print(f"HTML {html}")
        return html

    @classmethod
    def debug_span_changed(cls, span, text_style, y0):
        if span:
            if span.text_style != text_style:
                print(f"{span.text_style.difference(text_style)} \n {span.string}")

            if span.y0 != y0:
                print(f""
                      f"Y {y0} != {span.y0}\n {span.string} {span.xx} ")

    @classmethod
    def get_xy_tuple(cls, ch, ndec_coord):
        x0 = round(ch.get(P_X0), ndec_coord)
        x1 = round(ch.get(P_X1), ndec_coord)
        y0 = round(ch.get(P_Y0), ndec_coord)
        y1 = round(ch.get(P_Y1), ndec_coord)
        return x0, x1, y0, y1

    @classmethod
    def skip_rotated_text(cls, ch):
        """is text rotated? uses matrix"""
        matrix = ch.get("matrix")
        return matrix and matrix[0:4] != (1, 0, 0, 1)

    @classmethod
    def create_page_from_pdf_html(cls, path):
        logging.error("NOT YET WRITTEN")

    @classmethod
    def create_html_pages(cls,
                          bbox=DEFAULT_BBOX,
                          input_pdf=None,
                          output_dir=None,
                          output_stem=None,
                          range_list=range(1,9999999)):
        """create HTML pages from PDF
        USED
        uses pdfminer routines (AmiPage.chars_to_spans)
        will need further tuning to generate structured HTML
        :param bbox: clip page (default is none)
        :param inout_pdf: required PDF
        :param output_dir: output dicrectory
        :param output_stem: output filestem
        :param page_nos: list of 2-tuples containing allowed ranges (e.g.  [(2,3), (5, 12)]
        """
        if not input_pdf or not Path(input_pdf).exists():
            logging.logger.error(f"must have not-null, existing pdf {input_pdf} ")

        if not Path(output_dir).exists():
            output_dir.mkdir()
        with pdfplumber.open(input_pdf) as pdf:
            page_count = len(pdf.pages)
        for page_no in range(page_count):  # 1-based page_no
            logging.debug(f"testing page {page_no}")
        # for page_no in page_nos:
            if not Util.range_list_contains_int(page_no + 1, range_list):
                continue
            logging.debug(f"accept page {page_no}")
            html = AmiPage.chars_to_spans(bbox, input_pdf, page_no)
            output_html = Path(output_dir, f"{output_stem}_{page_no}.html")
            with open(output_html, "wb") as f:
                f.write(lxml.etree.tostring(html))
                print(f" wrote html {output_html}")
                # assert output_html.exists()


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
                HtmlUtil.set_attrib(content, FONT_FAMILY, text_style._font_family)
                HtmlUtil.set_attrib(content, FONT_SIZE, str(text_style._font_size))
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
        font_size = self.text_style._font_size
        height = font_size
        width = self.end_x + last_width * font_size - self.start_x
        self.bbox = BBox.create_from_xy_w_h((self.start_x, self.y - height), width, height)
        return self.bbox

    def normalize_family_weight(self) -> None:
        """transforms font-family names into weights and styles
        Example: TimesRomanBoldItalic will set style=italic and weight=bold
        and reset family to TimesRoman

            """

        family = self.text_style._font_family
        if not family:
            print(f"no family: {self}")
            return
        family = family.lower()
        if family.find(ITALIC) != -1:
            self.text_style.font_style = ITALIC
        if family.find(BOLD) != -1:
            self.text_style.font_weight = BOLD
        if family.find(TIMES) != -1:
            self.text_style._font_family = TIMES
        if family.find(CALIBRI) != -1:
            self.text_style._font_family = CALIBRI
        if self.text_style._font_family not in FONT_FAMILIES:
            print(f"new font_family {self.text_style._font_family}")

    def has_empty_text_content(self) -> bool:
        return len("".join(self.text_content.split())) == 0


# arg_dict
DEFAULT_MAXPAGES = 100
DEFAULT_CONVERT = "html"

CONVERT = "convert"
FLOW = "flow"
FOOTER = "footer"
HEADER = "header"

INDIR = "indir"
INFORM = "inform"
INPATH = "inpath"
INSTEM = "instem"

ALL_PAGES = "all_pages"
MAXPAGE = "maxpage"

OUTDIR = "outdir"
OUTFORM = "outform"
OUTPATH = "outpath"
OUTSTEM = "outstem"

PAGES = "pages"
PDF2HTML = "pdf2html"

# FORMAT = "fmt"
IMAGEDIR = "imagedir"
RESOLUTION = "resolution"
TEMPLATE = "template"


class PDFArgs(AbstractArgs):
    """
    Holds argument values for py4ami PDF commands and runs conversions
    Also holds much of the document data

        self.convert = DEFAULT_CONVERT
        self.html = None

        self.footer = None
        self.header = None

        self.indir = None
        self.inform = 'PDF'
        self.inpath = None
        self.instem = 'fulltext'

        self.maxpage = DEFAULT_MAXPAGES

        self.outdir = None
        self.outform = DEFAULT_CONVERT
        self.outpath = None
        self.outstem = None

        self.pages = None

        self.pdf2html = None
        self.raw_html = None
        self.flow = None
        self.unwanteds = None

    """
    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()
        self.convert = DEFAULT_CONVERT
        self.html = None

        self.footer = None
        self.header = None

        self.indir = None
        self.inform = 'PDF'
        self.inpath = None
        self.instem = 'fulltext'

        self.maxpage = DEFAULT_MAXPAGES

        self.outdir = None
        self.outform = DEFAULT_CONVERT
        self.outpath = None
        self.outstem = None

        self.pages = None

        self.pdf2html = None
        self.raw_html = None
        self.flow = None
        self.unwanteds = None

    def add_arguments(self):
        """creates adds the arguments for pyami commandline

        """
        if self.parser is None:
            self.parser = argparse.ArgumentParser(
                usage="py4ami always uses subcommands (DICT,GUI,HTML,PDF,PROJECT)\n e.g. py4ami PDF --help"
            )

        self.parser.description = textwrap.dedent(
            'PDF tools. \n'
            '----------\n'                                                  
            'Typically reads one or more PDF files and converts to HTML\n'
            'can clip parts of page, select page ranges, etc.\n'
            '\nExamples:\n'
            '  * PDF --help\n'
        )
        self.parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # self.parser.add_argument("--convert", type=str, choices=[], help="conversions (NYI)")
        self.parser.add_argument("--debug", type=str, choices=DEBUG_OPTIONS, help="debug these during parsing (NYI)")
        self.parser.add_argument("--flow", type=bool, nargs=1, help="create flowing HTML, e.g. join l;ines, pages (heuristics)", default=True)
        self.parser.add_argument("--footer", type=float, nargs=1, help="top margin (clip everythimg above)", default=80)
        self.parser.add_argument("--header", type=float, nargs=1, help="bottom margin (clip everything below", default=80)
        self.parser.add_argument("--imagedir", type=str, nargs=1, help="output images to imagedir")

        self.parser.add_argument("--indir", type=str, nargs=1, help="input directory (might be calculated from inpath)")
        self.parser.add_argument("--inform", type=str, nargs="+", help="input formats (might be calculated from inpath)")
        self.parser.add_argument("--inpath", type=str, nargs=1, help="input file or (NYI) url; might be calculated from dir/stem/form")
        self.parser.add_argument("--instem", type=str, nargs=1, help="input stem (e.g. 'fulltext'); maybe calculated from 'inpath`")

        self.parser.add_argument("--maxpage", type=int, nargs=1, help="maximum number of pages (will be deprecated, use 'pages')", default=self.arg_dict.get(MAXPAGE))

        self.parser.add_argument("--outdir", type=str, nargs=1, help="output directory")
        self.parser.add_argument("--outpath", type=str, nargs=1, help="output path (can be calculated from dir/stem/form)")
        self.parser.add_argument("--outstem", type=str, nargs=1, help="output stem", default="fulltext.flow")
        self.parser.add_argument("--outform", type=str, nargs=1, help="output format ", default="html")

        self.parser.add_argument("--pdf2html", type=str, choices=['pdfminer', 'pdfplumber'], help="convert PDF to html", default='pdfminer')
        self.parser.add_argument("--pages", type=str, nargs="+", help="reads '_2 4_6 8 11_' as 1-2, 4-6, 8, 11-end ; all ranges inclusive (not yet debugged)", default=ALL_PAGES)
        self.parser.add_argument("--resolution", type=int, nargs=1, help="resolution of output images (if imagedir)", default=400)
        self.parser.add_argument("--template", type=str, nargs=1, help="file to parse specific type of document (NYI)")
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
#            logging.warning(f"ARG DICTXX {self.arg_dict}")
            self.read_from_arg_dict()

        if not self.check_input():
            print(f"no input given")
            return
        self.check_output()
        self.calculate_headers_footers()

        if self.pdf2html:
            self.check_output()
            # range_list = self.create_range_list()
            AmiPage.create_html_pages(
                          bbox=AmiPage.DEFAULT_BBOX,
                          input_pdf=self.inpath,
                          output_dir=self.outdir,
                          output_stem=self.outstem,
                          range_list=self.pages
            )

        # self.convert_write()

    def check_input(self):
        if not self.inpath:
            print(f"No input file, no action taken")
            return False
            # raise FileNotFoundError(f"input file not given")
        if not Path(self.inpath).exists():
            raise FileNotFoundError(f"input file does not exist: ({self.inpath}")
        self.indir = Path(self.inpath).parent
        return True

    def check_output(self):
        logging.warning(f" *** ARG_DICT {self.arg_dict}")
        self.arg_dict[OUTSTEM] = Path(f"{self.inpath}").stem
        self.arg_dict[OUTPATH] = Path(Path(self.inpath).parent, f"{self.arg_dict[OUTSTEM]}.{self.arg_dict[OUTFORM]}")
        if not self.outdir:
            self.outdir = self.arg_dict[OUTDIR]

        if not self.outpath:
            self.outpath = self.arg_dict.get(OUTPATH)
        # if no outdir , create from outpath
        if not self.outdir:
            if self.outpath:
                self.outdir = Path(self.outpath).parent
        if not self.outdir:
            if self.inpath:
                self.outdir = Path(self.inpath).parent
            else:
                raise FileNotFoundError(f"output dir not given and cannot be generated")
            self.outstem = self.arg_dict.get(OUTSTEM)
            if not self.outstem:
                raise FileNotFoundError(f"output file not given and cannot be generated")
            if not self.outform:
                raise FileNotFoundError(f"no output format given")
            self.outpath = Path(self.outdir, f"{self.outstem}.{self.outform}")
            logging.debug(f"outpath {self.outpath}")
        else:
            logging.debug(f"outdir {self.outdir}")
        if not Path(self.outdir).exists():
            Path(self.outdir).mkdir()
        elif not Path(self.outdir).is_dir():
            raise ValueError(f"output dir {self.outdir} is not a directory")
        else:
            logging.debug(f"output dir {self.outdir}")
        return True

    def read_from_arg_dict(self):
#        logging.warning(f"ARG DICT0 {self.arg_dict}")
        self.flow = self.arg_dict.get(FLOW) is not None

        self.footer = self.arg_dict.get(FOOTER)
        if not self.footer:
            self.footer = 80
        self.header = self.arg_dict.get(HEADER)
        if not self.header:
            self.header = 80

        self.indir = self.arg_dict.get(INDIR)
        self.inform = self.arg_dict.get(INFORM)
        self.inpath = self.arg_dict.get(INPATH)
        self.instem = self.arg_dict.get(INSTEM)

        self.maxpage = self.arg_dict.get(MAXPAGE)

        self.outdir = self.arg_dict.get(OUTDIR)
        self.outform = self.arg_dict.get(OUTFORM)
        self.outpath = self.arg_dict.get(OUTPATH)
        self.outstem = self.arg_dict.get(OUTSTEM)

#        logging.warning(f"ARG DICT {self.arg_dict}")
        pages = self.arg_dict.get(PAGES)
        self.pages = PDFArgs.make_page_ranges(pages)

        self.pdf2html = self.arg_dict.get(PDF2HTML)

            # self.convert_write(maxpage=maxpage, outdir=outdir, outstem=outstem, fmt=fmt, inpath=inpath, flow=True)

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
        """Uses PDFMiner library (I think) which omits coordinates"""
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
        device, interpreter, retstr = PDFArgs.create_pdf_interpreter(fmt)
        if not path:
            raise FileNotFoundError("no input file given)")
        try:
            fp = open(path, "rb")
        except FileNotFoundError as fnfe:
            raise Exception(f"No input file given {fnfe}")

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
        arg_dict[CONVERT] = "html"
        arg_dict[FLOW] = True
        arg_dict[FOOTER] = 80
        arg_dict[HEADER] = 80

        arg_dict[INDIR] = None
        arg_dict[INFORM] = None
        arg_dict[INPATH] = None
        arg_dict[INSTEM] = None

        arg_dict[MAXPAGE] = 5

        arg_dict[OUTDIR] = None
        arg_dict[OUTFORM] = "html"
        arg_dict[OUTPATH] = None
        arg_dict[OUTSTEM] = None

        arg_dict[PAGES] = None
        arg_dict[PDF2HTML] = None
        arg_dict[FLOW] = True
        return arg_dict

    @classmethod
    def create_pdf_interpreter(cls, fmt, codec: str = "UTF-8"):
        """Based on PDFMiner I think"""
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
            raise ValueError(f"format ({fmt}) is invalid, {converters.keys()}")
        device = converter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return device, interpreter, retstr

    # class PDFArgs:

    def calculate_headers_footers(self):
        # header_offset = -50
        self.header = 90
        # page_height = 892
        # page_height_cm = 29.7
        self.footer = 90

    def convert_write(self):
        """
        Convenience method to run PDFArgs.convert_pdf on self.inpath, self.outform, and self.maxpage
        writes output to self.outpath
        if self.flow runs self.tidy_flow
        :return: outpath
        """
        print(f"==============CONVERT================")
        self.process_args()
        self.raw_html = PDFArgs.convert_pdf(path=self.inpath, fmt=self.outform, maxpages=self.maxpage)

        if self.flow:
            self.html = self.tidy_flow()
            assert len(self.html) > 0
            print(f"flow {len(self.raw_html)}")
        if self.outpath is None:
            print(f"no outpath given")
            return None
        with open(str(self.outpath), "w") as f:
            f.write(self.html)
            print(f"wrote outpath {self.outpath}")
        return self.outpath

    def tidy_flow(self):
        tree = lxml.etree.parse(StringIO(self.raw_html), lxml.etree.HTMLParser())
        result_elem = tree.getroot()
        HtmlUtil.add_ids(result_elem)
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
        PDFUtil.remove_headers_and_footers(result_elem, pagesize, self.header, self.footer, marker_xpath)
        PDFUtil.remove_style_attribute(result_elem, "top")
        PDFUtil.remove_style(result_elem, ["left", "height"])
        PDFUtil.remove_unwanteds(result_elem, self.unwanteds)
        PDFUtil.remove_newlines(result_elem)
        self.markup_parentheses(result_elem)
        print(f"ref_counter {self.ref_counter}")
        HtmlTree.make_sections_and_output(result_elem, output_dir=self.outdir, recs_by_section=RECS_BY_SECTION)
        self.html = lxml.etree.tostring(result_elem).decode("UTF-8")
        return self.html

    # class PDFArgs:

    def markup_parentheses(self, result_elem):
        """iterate over parenthesised fields

        """
        xpath = ".//span"
        spans = result_elem.xpath(xpath)
        for span in spans:
            # self.extract_brackets(span)
            pass

    def extract_brackets(self, span):
        """extract (...) from text, and add hyperlinks for refs, NYI
        (IPCC 2018a)
        (Roy et al. 2018)
        (UNFCCC 2016a, 2021)
        (Bertram et al. 2015; Riahi et al. 2015)
        """
        text = ''.join(span.itertext())
        par = span.getparent()
        # (FooBar& Biff 2012a)
        refregex = r"(" \
                   r"[^\(]*" \
                   r"\(" \
                   r"(" \
                   r"[A-Z][^\)]{1,50}(20\d\d|19\d\d)" \
                   r")" \
                   r"\s*" \
                   r"\)" \
                   r"(.*)" \
                   r")"

        result = re.compile(refregex).search(text)
        if result:
            # print(f"matched: {result.group(1)} {result.group(2)}, {result.group(3)} {result.groups()}")
            elem0 = lxml.etree.SubElement(par, H_SPAN)
            elem0.text = result.group(1)
            for k, v in elem0.attrib.items():
                elem0.attrib[k] = v
            idx = par.index(span)
            span.addnext(elem0)
            current = elem0
            for ref in result.group(2).split(";"):  # e.g. in (Foo and Bar, 2018; Plugh 2020)
                ref = ref.strip()
                if not self.ref_counter[ref]:
                    self.ref_counter[ref] == 0
                self.ref_counter[ref] += 1
                a = lxml.etree.SubElement(par, H_A)
                for k, v in elem0.attrib.items():
                    a.attrib[k] = v
                a.attrib[A_HREF] = "https://github.com/petermr/discussions"
                a.text = "([" + ref + "])"
                current.addnext(a)
                current = a
            elem2 = lxml.etree.SubElement(par, H_SPAN)
            for k, v in elem0.attrib.items():
                elem2.attrib[k] = v
            elem2.text = result.group(3)

            par.remove(span)

            # print(f"par {lxml.etree.tostring(par)}")

    @property
    def module_stem(self):
        """name of module"""
        return Path(__file__).stem

    # def create_range_list(self):
    #     """makes list of ranges from pairs on numbers"""
    #     range_list = range(1,999)
    #     if type(self.pages) is list:
    #         range_list = []
    #         ll = list(map(int, self.pages))
    #         for i in range(0, len(ll), 2):
    #             range_list.append(ll[i:i + 2])
    #     return range_list

    @classmethod
    def make_page_ranges(cls, raw_pages):
        """expand pages arg to list of ranges
        typical input _2 4_5 8 9_11 13 16_
        These are *inclusive* so expand to
        range(1,3) range(4,6) range(8,9) range (9,12) range(13,14) range(16-maxint)
        converts raw_pages to page ranges
        uses 1-based pages
        """
        ranges = []
        if raw_pages == ALL_PAGES:
            raw_pages = "1_9999999"
        if raw_pages:
            logging.debug(f"**** raw pages: {raw_pages}")
            if not hasattr(raw_pages, "__iter__"):
                logging.error(f"{raw_pages} is not iterable {type(raw_pages)}")
                return
            for chunk in raw_pages:
                if not chunk == "":
                    chunk0 = chunk
                    try:
                        if chunk.startswith("_"):  # prepend 1
                            chunk = f"{1}{chunk}"
                        if chunk.endswith("_"):  # append Maxint
                            chunk = f"{chunk}{sys.maxsize}"
                        if not "_" in chunk: # expand n to n_n (inclusive)
                            chunk = f"{chunk}_{chunk}"
                        ints = chunk.split("_")
                        logging.debug(f"ints {ints}")
                        rangex = range(int(ints[0]), (int(ints[1]) + 1))  # convert to upper-exclusive
                        ranges.append(rangex)
                    except Exception as e:
                        raise ValueError(f"Cannot parse {chunk0} as int range {e}")
        return ranges


class PDFDebug:
    def __init__(self):
        self.max_table = 10
        self.max_curve = 10
        self.max_rect = 10
        self.image_coords_list = []
        self.image_dict = dict()

    def debug_page_properties(self, page, debug=None, outdir=None):
        """debug print selected DEBUG_OPTIONS
        :param debug: list of options (from DEBUG_OPTIONS)
        """
        if not debug:
            debug = []
            print(f"no options given, choose from: {DEBUG_OPTIONS}")
        if DEBUG_ALL in debug:
            debug = DEBUG_OPTIONS
        print(f"\n\n======page: {page.page_number} ===========")
        if WORDS in debug:
            self.print_words(page)
        if LINES in debug:
            self.print_lines(page)
        if RECTS in debug:
            self.print_rects(page, debug=False)
        if CURVES in debug:
            self.print_curves(page)
        if IMAGES in debug:
            self.print_images(page, outdir=outdir)
        if TABLES in debug:
            self.print_tables(page)
        if HYPERLINKS in debug:
            self.print_hyperlinks(page)
        if ANNOTS in debug:
            self.print_annots(page)

    def write_summary(self, outdir=None):
        if not outdir:
            return
        if not outdir.exists():
            outdir.mkdir()
        if self.image_coords_list:
            coord_file = Path(outdir, "image_coords.txt")
            with open(coord_file, "w") as f:
                f.write(f"{self.image_coords_list}")
            print(f"wrote image coords to {coord_file}")

    def print_words(self, page):
        print(f"words {len(page.extract_words())}", end=" | ")

    def print_lines(self, page):
        n_line = len(page.lines)
        if n_line > 0:
            print(f"lines {n_line}", end=" | ")

    def print_rects(self, page, debug=False):
        n_rect = len(page.rects)
        if n_rect > 0:
            print(f"rects {n_rect}", end=" | ")
            if debug:
                for rect in page.rects[:self.max_rect]:
                    print(f"rect (({rect['x0']},{rect['x1']}),({rect['y0']},{rect['y1']})) ")

    def print_curves(self, page):
        n_curve = len(page.curves)
        if n_curve > 0:
            print(f"curves {n_curve}", end=" | ")
            for curve in page.curves[:self.max_curve]:
                print(f"keys: {curve.keys()}")
                print(f"curve {curve['points']}")

    def print_images(self, page, maximage=10, outdir=None):
        maximage = 999

        write_image = False
        resolution = 400  # may be better
            # see https://github.com/euske/pdfminer/blob/master/pdfminer/pdftypes.py
        n_image = len(page.images)
        if n_image > 0:
            print(f"images {n_image}", end=" |\n")
            for i, image in enumerate(page.images[:maximage]):

                print(f"image: {type(image)}: {image.keys()} \n{image.values()}")
                print(f"stream {image['stream']}")
                print(f"xxyy {(image['x0'],image['x1']),(image['y0'],image['y1']),image['srcsize'],image['name'],image['page_number']}")
                stream = image['stream']
                width_height_bytes = ((image['srcsize']),image['stream']['Length'])
                page_coords = (image['page_number'], (image['x0'],image['x1']),(image['y0'],image['y1']))
                print(f"image:  {width_height_bytes} => {page_coords}")
                if (width_height_bytes) in self.image_dict:
                    print("clash: {(width_height_bytes)}")
                self.image_dict[width_height_bytes] = page_coords

                if not outdir:
                    pass
                elif not outdir.exists():
                    outdir.mkdir()
                if outdir and isinstance(image, LTImage):
                    imagewriter = ImageWriter(str(Path(outdir, f"image{i}.png")))
                    imagewriter.export_image(image)
                page_height = page.height
                image_bbox = (image[X0], page_height - image[Y1], image[X1], page_height - image[Y0])
                # print(f"image: {image_bbox}")

                coord_stem = f"image_{page.page_number}_{i}_{self.format_bbox(image_bbox)}"
                self.image_coords_list.append(coord_stem)

                if outdir and write_image:  # I think this is slow
                    coord_path = Path(outdir, f"{coord_stem}.png")
                    cropped_page = page.crop(image_bbox)  # crop screen display (may have overwriting text)
                    image_obj = cropped_page.to_image(resolution=resolution)
                    image_obj.save(coord_path)
                    print(f" wrote image {coord_path}")
                # continue

            # for p in pdf.pages:
            #     for obj in p.layout:
            #         if isinstance(obj, LTImage):
            #             imagewriter.export_image(obj)
        print(f"image_dict {self.image_dict}")

    def print_tables(self, page, odir=None):
        tables = page.find_tables()
        n_table = len(tables)
        if n_table > 0:
            print(f"tables {n_table}", end=" | ")
            print(f"table_dir {tables[0].__dir__()}")
            for i, table in enumerate(tables[:self.max_table]):
                h_table = self.create_table_element(table)
                table_file = Path(odir, f"table_{i + 1}.html")
                self.print_table_element(h_table, table_file)

    def print_table_element(self, h_table, table_file):
        h_str = lxml.etree.tostring(h_table, encoding='UTF-8', xml_declaration=False)
        with open(table_file, "wb") as f:
            f.write(h_str)
            print(f"wrote {table_file}")

    def create_table_element(self, table):
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

    def format_bbox(self, bbox: tuple):
        return f"{int(bbox[0])}_{int(bbox[2])}_{int(bbox[1])}_{int(bbox[3])}"

    def print_hyperlinks(self, page):
        n_hyper = len(page.hyperlinks)
        if n_hyper > 0:
            print(f"hyperlinks {n_hyper}", end=" | ")
            for hyperlink in page.hyperlinks:
                print(f"hyperlink {hyperlink.values()}")

    def print_annots(self, page):
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
        n_annot = len(page.annots)
        if n_annot > 0:
            print(f"annots {n_annot}", end=" | ")
            for annot in page.annots:
                print(f"annot: {annot.items()}")


class TextStyle:
    # try to map onto HTML italic/normal
    def __init__(self):
        # maybe should be dict
        self.font_style = None
        # height in pixels
        self._font_size = None
        self._font_family = None
        # try to map onto HTML bold/norma
        self.font_weight = None
        # fill colour of text
        self._color = None
        # stroke colour of text
        self.stroke = None

    def __str__(self) -> str:
        s = f"size {self._font_size} family {self._font_family}, style {self.font_style} weight {self.font_weight} fill {self._color} stroke {self.stroke}"
        return s

    def __eq__(self, other):
        if isinstance(other, TextStyle):
            # required attributes
            if self._font_family != other._font_family or self._font_size != other._font_size:
                return False
            # optional
            if TextStyle._not_equal(self.font_weight, other.font_weight):
                return False
            if TextStyle._not_equal(self._color, other._color):
                return False
            if TextStyle._not_equal(self.stroke, other.stroke):
                return False
            return True
        return False

    def create_css_string(self):
        """create CSS style from stored values
        currently font-size, font-family, fill and stroke"""
        css = ""
        if self._font_size:
            css += f"font-size: {self._font_size} px;"
        if self._font_family:
            css += f"font-family: {self._font_family};"
        if self._color:
            css += f"color: {self._color};"
        if self.stroke:
            css += f"stroke: {self.stroke};"
        return css

    def set_font_family(self, name):
        """trims [A-Z]{6}\+ from start of string"""
        if name and len(name) > 7 and name[6] == "+":
            name = name[7:]
        self._font_family = name
        if "Bold" in name or ".B" in name:
            self.font_weight = "bold"
        if "Italic" in name or ".I" in name:
            self.font_style = "italic"

    def set_font_size(self, size, ndec=None):
        """sets size and optionally rounds it
        :param size: font-size
        :param ndec: round to ndec places"""
        if ndec:
            size = round(size, ndec)
        self._font_size = size

    @property
    def font_size(self):
        return self._font_size

    @property
    def font_family(self):
        return self._font_family

    @classmethod
    def _not_equal(cls, selfx, otherx):
        """compares objects with None == None"""
        if not selfx and not otherx:
            return False
        return selfx != otherx

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
        s += self._difference("; fill", self._color, other._color)
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

    @classmethod
    def remove_unwanteds(cls, top_elem, unwanteds):
        if not unwanteds:
            print(f"no unwanteds to remove")
            return
        for key in unwanteds:
            unwanted = unwanteds[key]
            xpath = unwanted[U_XPATH]
            if xpath:
                regex = unwanted[U_REGEX]
                regex_comp = re.compile(regex) if regex else None
                elems = top_elem.xpath(xpath)
                for elem in elems:
                    text = ''.join(elem.itertext())
                    matched = regex_comp.search(text) if regex_comp else True
                    if matched:
                        # print(f"deleted {xpath} {text}")
                        cls.remove_elem_keep_tail(elem)

    @classmethod
    def remove_newlines(cls, elem):
        """remove \n"""
        for el in elem.xpath(".//*[not(*)]"):
            text = ''.join(el.itertext())
            text1 = text.replace('\n', '')
            if text1 != text:
                el.text = text1
                # print(f"\n[[{text} => {''.join(el.itertext())}]]\n")

class PDFImage:
    """utility class for tidying images from PDF
    """
    def __init__(self):
        pass

    def convert_all_suffixed_files_to_target(self, indir, suffixes, target_suffix, outdir=None):
        """convert all files with given suffixes to target_suffix type
        :param indir: directory with files
        :param suffixes: list of suffixes (WITH DOT), e.g. ['.bmp', '.jpg']
        :param target_suffix: target format (WITH DOT), e.g. ['.png']
        """
        image_files = os.listdir(indir)
        if not indir or not indir.exists():
            return
        if not suffixes or not '.' in suffixes[0] or not target_suffix or not '.' in target_suffix:
            return
        Path(outdir).mkdir(parents=True, exist_ok=True)
        for image_file in image_files:
            infile = Path(indir, image_file)
            stem = Path(infile).stem
            if infile.suffix in suffixes:
                # note ADDS suffix
                self.convert_image_file(infile, Path(outdir, stem + target_suffix))

    def convert_image_file(self, infile, outfile):
        """converts infile to outfile
        compounded suffixes"""
        print(f"saving to {outfile}")
        Image.open(infile).save(outfile)
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

    # SvgText

    def create_text_style(self) -> TextStyle:
        """create TextStyle from style attributes"""
        style = TextStyle()
        # style.y = self.get_y_coord()
        # style.x = self.get_x_coord()
        style._font_size = self.get_font_size()
        style._font_family = self.get_font_family()
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
        :returns: font-maily or None
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


def main(argv=None):
    """entry point for PDF conversiom
    typical:
    python -m py4ami.ami_pdf \
        --inpath /Users/pm286/workspace/pyami/test/resources/ipcc/Chapter06/fulltext.pdf \
        --outdir /Users/pm286/workspace/pyami/temp_oldx/pdf/chap6/
        --maxpage 100

    """
    print(f"running PDFArgs main")
    pdf_args = PDFArgs()
    parse_and_process_1(pdf_args)


def parse_and_process_1(pdf_args):
    """
    Convenience method to run pdf_args
    Runs pdf_args.parse_and_process()
        pdf_args.convert_write()
    :param pdf_args: previously populated args
    """
    try:
        pdf_args.parse_and_process()
        pdf_args.convert_write()
    except Exception as e:
        print(traceback.format_exc())
        print(f"***Cannot run pyami***; see output for errors: {e} ")


if __name__ == "__main__":
    main()
else:
    pass
