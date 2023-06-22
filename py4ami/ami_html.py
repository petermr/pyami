"""Supports parsing, editing, markup, restructing of HTML
Should have relatively few dependencies"""
import argparse
import copy
import logging
import re
import time
from collections import defaultdict, Counter
from enum import Enum
from io import StringIO
from pathlib import Path

import lxml
import lxml.etree
import numpy as np
import pandas as pd
from lxml.etree import Element, _Element, _ElementTree
from sklearn.linear_model import LinearRegression

# local
# from py4ami.ami_dict import AmiDictionary
# from py4ami.ami_pdf import AmiPDFPlumber
from py4ami.bbox_copy import BBox
from py4ami.util import SScript, AbstractArgs, Util, AmiLogger
from py4ami.xml_lib import XmlLib, HtmlLib

logger = AmiLogger.create_named_logger(__file__)

# HTML
H_HTML = "html"
H_HEAD = "head"
H_META = "meta"
H_STYLE = "style"
H_BODY = "body"
H_TABLE = "table"
H_THEAD = "thead"
H_TBODY = "tbody"
H_TR = "tr"
H_TH = "th"
H_TD = "td"
H_DIV = "div"
H_SPAN = "span"
H_UL = "ul"
H_LI = "li"
H_A = "a"
H_B = "b"
H_P = "p"

X = "x"
Y = "y"
X0 = "x0"
X1 = "x1"

A_HREF = "href"
A_NAME = "name"
A_TERM = "term"
A_TITLE = "title"
A_ID = "id"
A_CLASS = "class"

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
FONT_FONT = "font"
FONT_NAME = "font-name"
FONT_STRETCHED = "font-stretched"
FILL = "fill"
STROKE = "stroke"

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

STYLES = [
    FONT_SIZE,
    FONT_STYLE,
    FONT_FAMILY,
    FONT_WEIGHT,
    FILL,
    STROKE,
]

# commandline
ANNOTATE = "annotate"
COLOR = "color"
DICT = "dict"
INPATH = "inpath"
OUTDIR = "outdir"
OUTPATH = "outpath"

IPCC_CHAP_TOP_REC = re.compile(""
                               "(Chapter\\s?\\d\\d?\\s?:.*$)|"
                               "(Table\\s?of Contents.*)|"
                               "(Executive [Ss]ummary.*)|"
                               "(Frequently [Aa]sked.*)|"
                               "(References)"
                               )
SECTIONS_DECIMAL_REC = re.compile("\\d+\\.\\d+$")
SUBSECTS_DECIMAL_REC = re.compile("\\d+\\.\\d+\\.\\d+$")

CLASSREF = "classref"

STYLE_XPATH = "/html/head/style"

"""
NOTE. the use of classname, classref and similar is inconsistent. We want to have:
s1  to mean class name (classname)
.s1 to mean a reference to a classname (only used in <style> elements but involved in conversions
"""


class AmiSpan:
    def __init__(self):
        self.text_style = None
        self.string = ""
        self.xx = []
        self.x0 = None
        self.x1 = None
        self.y0 = None
        # self.adv = None

    def create_and_add_to(self, div):
        html_span = None
        if div is not None:
            html_span = lxml.etree.SubElement(div, "span")
            html_span.text = self.string
            HtmlStyle.set_style(html_span, self.text_style.create_css_string())
            if len(self.xx) > 0:
                html_span.attrib[X] = self.xx[0]
            if self.x0:
                html_span.attrib[X0] = str(self.x0)
            if self.x1:
                html_span.attrib[X1] = str(self.x1)
            html_span.attrib[Y] = str(self.y0)
        return html_span


# should maybe be in PDF
class PageBox:  # defined by pdfminer I think

    """
<br><span style="position:absolute; border: gray 1px solid; left:0px; top:941px; width:595px; height:841px;"></span>
<div style="position:absolute; top:941px;"><a name="2">Page 2</a></div>

for IPCC top(Page1) = 50
top(Pagen) = 50 + (n - 1) * (841 + 47)

    """

    def __init__(self, css_style=None):
        self.css_style = css_style
        self.bbox = BBox()  # uninitialised
        if self.css_style:
            top = self.css_style.top
            left = self.css_style.left
            width = self.css_style.width
            height = self.css_style.height
            self.bbox.xy_ranges = [[left, left + width], [top, top + height]]
        self.elem = None
        self.int_number = None  # pdfplumber integer page (1-based)
        self.p_num_str = None  # pdfplumber "Page 12"

    @property
    def page_number(self):
        if not self.int_number:
            self.int_number = None if self.elem is None else PageBox.extract_page_number_from_pdf_html(self.elem)
        return self.int_number

    @classmethod
    def extract_page_number_from_pdf_html(cls, elem):
        """
        some elements ?spans) from pdf parsing have the form:
        <div ...><a name="2">Page 2</a>

        :param elem: contains page number
        :return: page number or none
        """
        if elem is None:
            return None
        xpathx = ".//a/@name"
        aname = elem.xpath(xpathx)
        return aname

    def add_style_span_and_page_number(self, elem):
        """
        add style span  and also get pagenumber from next element

        typical trailing element
        <div style="position:absolute; top:10753px;"><a name="13">Page 13</a></div>
        """
        self.elem = elem
        page_div = elem.getnext()
        if page_div is not None:
            n = page_div.xpath("./a/@name")
            n = n[0] if len(n) == 1 else None
            if n:
                self.int_number = int(n)

            p = page_div.xpath("./a[@name and contains(., 'Page')]")
            self.p_num_str = p[0] if len(p) == 1 else None


class HtmlTidy:
    """for tidying PDF / SVG/ OCR parsing
    takes raw HTML (probably scattered words or lines , possibly with coordinates and creates
    flowing styled HTML with subscripts, font styles, etc.
    """

    MIN_PAGE_BOX_HEIGHT = 300  # allows for landscape
    HEAD_ELEMS_IN_XPATH = "meta | title | script | style"

    def __init__(self):
        self.unwanteds = []  # not sure what this is
        self.empty_elements_to_remove = []
        self.styles_to_remove = []
        self.descendants_to_remove = []
        self.remove_lh_line_numbers = True
        self.remove_large_fonted_elements = True
        self.style_attributes_to_remove = []
        self.marker_xpath = None
        self.style_attributes_to_remove = []

        self.add_id = True
        self.header = 80
        self.footer = 80
        self.page_tops = None
        self.page_boxes = []
        self.raw_elem = None
        self.outdir = None

    def tidy_flow(self, raw_html):
        """
        Need to capture page information to compute page coordinates, not document coordinates
        converts raw html to tidy
        """

        # TODO check and move to instance of HtmlTidy

        if raw_html is None:
            raise ValueError("No HTML")
        raw_tree = lxml.etree.parse(StringIO(raw_html), lxml.etree.HTMLParser())
        self.raw_elem = raw_tree.getroot()
        self.extract_page_boxes()

        self.add_element(self.raw_elem)

        # this is set by user
        self.set_remove_flags()

        self.remove_unwanted_attributes_and_elements()
        pagesize = None
        if self.marker_xpath:
            offset, pagesize, page_coords = HtmlUtil.find_constant_coordinate_markers(self.raw_elem, self.marker_xpath)
            HtmlUtil.remove_headers_and_footers_using_pdfminer_coords(
                self.raw_elem,
                pagesize,
                self.header,
                self.footer,
                self.marker_xpath,
                page_tops=self.page_tops,
            )
        for att in self.style_attributes_to_remove:
            HtmlUtil.remove_style_attribute(self.raw_elem, att)
        HtmlUtil.remove_unwanteds(self.raw_elem, self.unwanteds)
        HtmlUtil.remove_newlines(self.raw_elem)
        HtmlTree.make_sections_and_output(self.raw_elem, output_dir=self.outdir, recs_by_section=RECS_BY_SECTION)
        htmlstr = lxml.etree.tostring(self.raw_elem, encoding='UTF-8').decode()
        return htmlstr

    def remove_unwanted_attributes_and_elements(self):
        """
        remove objects if flags have been set in self
        """
        if self.add_id:
            HtmlUtil.add_generated_ids(self.raw_elem)
        for tag in self.descendants_to_remove:
            lxml.etree.strip_tags(self.raw_elem, [tag])
        if self.remove_lh_line_numbers:
            HtmlUtil.remove_lh_line_numbers(self.raw_elem)
        if self.remove_large_fonted_elements:
            HtmlUtil.remove_large_fonted_elements(self.raw_elem)
        for tag in self.empty_elements_to_remove:
            HtmlUtil.remove_empty_elements(self.raw_elem, [tag])
        for style in self.styles_to_remove:
            HtmlUtil.remove_style(self.raw_elem, [style])

    def set_remove_flags(self):
        """
        set flags which direct removal of elements/attributes
        normally under user control
        """
        self.add_descendant_element_to_remove(["br"])
        self.add_styles_to_remove(
            [
                "position",
                # "left",
                "border",
                "writing-mode",
                "width",  # this disables flowing text
            ]
        )
        self.add_id = True
        self.add_empty_elements_to_remove(["span", "div"])
        self.remove_lh_line_numbers = True  # x
        self.remove_large_fonted_elements = True
        self.style_attributes_to_remove = ["top"]
        self.marker_xpath = ".//div[a[@name]]"
        self.style_attributes_to_remove = ["left", "height"]

    def extract_page_boxes(self, ranges=None):
        """
        Based on pdfplumber output
        """
        self.page_boxes = []  # pageBox may merge with AmiPage

        if self.raw_elem is None:
            return
        style_spans = self.raw_elem.xpath("//span[contains(@style,'position:absolute')]")
        for style_span in style_spans:
            css_style = CSSStyle.create_css_style_from_attribute_of_body_element(style_span)
            if css_style.height > self.MIN_PAGE_BOX_HEIGHT:
                page_box = PageBox(css_style=css_style)
                page_box.add_style_span_and_page_number(style_span)
                self.page_boxes.append(page_box)

        self.extract_page_numbers()

    def extract_page_numbers(self):
        pageno_xpath = "//span/div/a[@name]"  # page number boxes; the parent span is horrid
        elem_with_pagenos = self.raw_elem.xpath(pageno_xpath)
        css_last = None
        """<br></span><span style="font-family: Calibri; font-size:10px"> 
                <br><span style="position:absolute; border: gray 1px solid; left:0px; top:941px; width:595px; height:841px;"></span>
                
                <div style="position:absolute; top:941px;"><a name="2">Page 2</a></div>
                """
        for elem_with_pageno in elem_with_pagenos:
            getparent = elem_with_pageno.getparent()
            css = CSSStyle.create_css_style_from_attribute_of_body_element(getparent)
            prev_elem = getparent.getprevious()
            height = -1 if css_last is None else css.top - css_last.top
            prev_style = CSSStyle.create_css_style_from_attribute_of_body_element(prev_elem)
            if not prev_style:
                logging.warning(f" no previous style")
            bbox = None if prev_style is None else prev_style.create_bbox()
            css_last = css
        return elem_with_pagenos


    def print_pages_div(self, ranges=None):
        """
        maybe just a debugger
        """

        if ranges:
            HtmlTidy.debug_by_xpath(self.raw_elem, "/html/body/span", title="direct spans under body ",
                                    range=ranges[0]),
            HtmlTidy.debug_by_xpath(self.raw_elem, "/html/body/span[div]", title="top-level spans with divs?",
                                    range=ranges[1])
            HtmlTidy.debug_by_xpath(self.raw_elem, "/html/body/span/div", title="the divs in stop-level spans",
                                    range=ranges[2])
            """
                <div style="position:absolute; top:4509px;"><a name="6">Page 6</a></div>
            """
            HtmlTidy.debug_by_xpath(self.raw_elem, "/html/body/div[@style and a]", title="page number boxes under body",
                                    range=ranges[3])
            HtmlTidy.debug_by_xpath(self.raw_elem, "/html/body//div[@style and a[contains(., 'Page')]]",
                                    title="page number boxes under body/span", range=ranges[4])

    @classmethod
    def debug_by_xpath(cls, elem, xpath, title=None, range=None) -> int:
        """
        applies xpath and prints debug9
        assert
        :param elem: to debug
        :param xpath: to debug with
        :return: xpath count
        """
        spans = elem.xpath(xpath)
        if range:
            assert range[0] <= len(spans) <= range[1], f"{'' if not title else title}: found: {len(spans)}"
        return len(spans)

    def add_element(self, elem):
        self.element = elem

    def add_descendant_element_to_remove(self, descendant_elem):
        HtmlTidy.add_elements_to_store(descendant_elem, self.descendants_to_remove)

    def add_styles_to_remove(self, style):
        self.styles_to_remove.append(style)

    def add_empty_elements_to_remove(self, elems_to_remove):
        HtmlTidy.add_elements_to_store(elems_to_remove, self.empty_elements_to_remove)

    @classmethod
    def add_elements_to_store(cls, elems_to_store, elem_storage):
        if elems_to_store is not None:
            if not type(elems_to_store) is list:
                elems_to_store = list(elems_to_store)
            elem_storage.extend(elems_to_store)

    @classmethod
    def ensure_html_head_body(cls, html_elem):
        """
        adds <html>, <head>, <body> if not present
        Move to HTMLTidy
        """
        html_elem = cls._ensure_html_root(html_elem)
        html_with_head = cls._ensure_headbody(html_elem, "head", 0)
        html_with_head_body = cls._ensure_headbody(html_with_head, "body", 1)
        html_ideal = cls._tidy_non_head_body_children(html_with_head_body)
        return html_ideal

    @classmethod
    def _ensure_headbody(cls, html_root, tag, pos):
        descends = len(html_root.xpath(f".//{tag}"))
        if descends > 1:
            logging.warning(f"more than 1 {tag}; cannot process")
        elif descends == 1:
            # one tag, ok
            pass
        elif descends == 0:
            head = lxml.etree.Element(tag)
            html_root.insert(pos, head)
        return html_root

    @classmethod
    def _ensure_html_root(cls, html_elem):
        """
        if root element is not <html> creates one and transfers children
        :param html_elem: old ElementTree or root Element
        """
        old_root = html_elem.getroot() if type(html_elem) is _ElementTree else html_elem
        htmls = html_elem.xpath("/html")
        if len(htmls) == 0:
            html_root = lxml.etree.Element("html")
            html_root.insert(0, old_root)
            return html_root
        return html_elem

    @classmethod
    def _tidy_non_head_body_children(cls, html_with_head_body):

        head_elems = html_with_head_body.xpath(HtmlTidy.HEAD_ELEMS_IN_XPATH)
        head = html_with_head_body.xpath("head")[0]
        for elem in head_elems:
            head.append(elem)
        rest_elems = html_with_head_body.xpath("*[not(name()='head') and not(name()='body')]")
        body = html_with_head_body.xpath("body")[0]
        for elem in rest_elems:
            body.append(elem)
        return html_with_head_body

    @classmethod
    def concatenate_spans_with_identical_styles(cls, elem, addspace=True):

        """
        Sometimes unnecessary spans are created (e.g.
        <span class='s1'>foo</span><spane class="s1">bar</span>
        creates <span class="s1">foo bar</span>
        :param elem: probably a div with child spans
        :param addspace: insert space
        """
        spans = elem.xpath("./span[@class]")
        last_span = None
        spaces = "" if not addspace else " "
        for span in spans:
            if last_span is not None and last_span.attrib["class"] == span.attrib["class"]:
                last_span.text = last_span.text + spaces + span.text
                elem.remove(span)
            else:
                last_span = span


def get_target_href(target_id):
    re_target = re.compile("\s*(?P<report>WGI|WGII|WGIII|SRCCL|SROCC|SR15|SYR)\s+(?P<chapter>SPM|TS)\s+(?P<section>[A-G]\.?\d+(?:\.\d+)*)")
    github_base = "https://htmlpreview.github.io/?https://github.com"
    working_url = "https://htmlpreview.github.io/?https://github.com/petermr/semanticClimate/blob/main/test.html"
    report_dict = {
        "wgi" : "wg1",
        "wgii": "wg2",
        "wgiii": "wg3",
    }
    href = ""
    match = re_target.match(target_id)
    if match:
        report = match.group("report").lower()
        report1 = report_dict.get(report)
        report = report1 if report1 else report
        chapter = match.group("chapter").lower()
        section = match.group("section").lower()
        href = f"{github_base}/petermr/semanticClimate/blob/main/ipcc/ar6/{report}/{chapter}/html/fulltext/groups_groups.html#{section}"

    return href


class HtmlGroup:
    """groups siblings into divs"""

    DEFAULT_STYLES = [
        (".section_title", [("color", "red;")]),
        (".sub_section_title", [("color", "blue;")]),
        (".sub_sub_section_title", [("color", "green;")]),
        (".confidence", [("color", "orange;")]),
        (".probability", [("color", "#8888ff;")]),
        (".superscript", [("color", "magenta;"), ("background", "yellow;")]),
        (".chunk", [("background", "cyan;")]),
        (".targets", [("background", "#88ff88;")]),
        (".start", [("background", "gray;")]),
        (".end", [("background", "yellow;")]),
        (".page", [("background", "magenta;")]),
        (".statement", [("background", "#ddddff;")]),
        (".level1", [("background", "#ffffdd;")]),
        (".level2", [("background", "#ddffff;")]),
        (".level3", [("background", "#ddffdd;")]),
        (".footnote", [("background", "#ffddff;")]),
    ]

    @classmethod
    def generate_lowercase_letter_id(cls, i):
        "make id of form a,b,c, ... aa, ab, ac ... ba, bb, ... zz , @.str(i)"
        abc = "abcdefghijklmnopqrstuvwxyz"
        ii = i % 26
        jj = i // 26
        if i >= 16 * 16:
            return "@." + str(i)
        s = "" if jj == 0 else abc[jj - 1]
        return s + abc[ii]



    @classmethod
    def group_siblings(cls, html_elem, locator=None, parent_locator=None, style=None, debug=False):
        """evrything starts as a sibling!"""
        sections = html_elem.xpath(f".//span[starts-with(@class, '{locator}')]")
        fenceposts = html_elem.xpath(f".//span[starts-with(@class,'{parent_locator}')]")
        if len(sections) > 0:
            parent = sections[0].getparent()
            for section in sections:
                cls.group_siblings_between_fenceposts(fenceposts, style=style, debug=debug)

    @classmethod
    def group_siblings_between_fenceposts(cls, fenceposts, style=None, debug=False):
        for i, fencepost in enumerate(fenceposts):
            fencepost_followers = fencepost.xpath("following-sibling::div[span]")
            container_div = lxml.etree.Element("div")
            container_div.attrib["style"] = style
            fencepost.addprevious(container_div)
            container_div.append(fencepost)
            title = fencepost.xpath("span")[0].attrib.get("id")
            if title:
                container_div.attrib["title"] = title
            for follower in fencepost_followers:
                if follower in fenceposts:
                    id = follower.xpath("./span")[0].attrib.get("id")
                    if debug:
                        print(f" id: {id}")
                    break
                else:
                    if debug:
                        print(f"moved follower {follower} to {container_div.attrib.get('title')}")
                    container_div.append(follower)

        """I'm working with lxml in Python and wish to group a flat set of <div> elements into a tree based on their class attributes
I have a set of sections <div> that are all children of <body> which must be arranged in a tree structure. Some of the divs contain just a title-string (title-divs) indicating the level in tree; this is indicated by a class attribute of "section", "sub_section", "sub_sub_section", etc. Any divs following title-divs belong to the same level, until a following title-div is reached. Please create code that:
* creates a new hierarchy of divs representing the tree structure
* adds the title-divs and their following non-title-divs to the appropriate position in the hierarchy.

Here is a typical input:

<html>
  <head>...</head>
  <body>
    <div class="section_title">Section 1</div>
    <div>stuff a</div>
    <div class="subsection_title">Section 1.1</div>
    <div>stuff b</div>
    <div>stuff bx</div>
    <div class="subsubsection_title">Section 1.1.1</div>
    <div>stuff z</div>
    <div>stuff zz</div>
    <div class="subsubsection_title">Section 1.1.2</div>
    <div>stuff x</div>
    <div>stuff xx</div>
    <div>stuff xxx</div>
    <div class="subsection_title">Section 1.2</div>
  </body>
</html>

   and desired output
<html>
  <head>...</head>
  <body>
    <div class="section">
      <div class="section_title">Section 1</div>
      <div>stuff a</div>
	  <div class="subsection">
        <div class="subsection_title">Section 1.1</div>
        <div>stuff b</div>
        <div>stuff bx</div>
		<div class="subsubsection">
          <div class="subsubsection_title">Section 1.1.1</div>
          <div>stuff z</div>
          <div>stuff zz</div>
		</div>
		<div class="subsubsection">
          <div class="subsubsection_title">Section 1.1.2</div>
          <div>stuff x</div>
          <div>stuff xx</div>
          <div>stuff xxx</div>
		</div>
	  </div>
	</div>
    <div class="section">
      <div class="section_title">Section 2</div>
	</div>
  </body>
</html>

ChatGPT
To achieve the desired output, you can use the following Python code to parse the HTML using lxml and restructure the <div> elements into a tree structure based on their class attributes:

python
Copy code
from lxml import etree

def group_divs_into_tree(html):
    # Parse the HTML
    tree = etree.HTML(html)

    # Find all <div> elements within the <body> tag
    div_elements = tree.xpath("//body/div")

    # Create a new root <div> element to hold the tree structure
    root = etree.Element("div")

    # Initialize variables to keep track of the current parent <div> and its level
    current_parent = root
    current_level = 0

    for div in div_elements:
        # Check if the current <div> has a class attribute
        if "class" in div.attrib:
            class_value = div.attrib["class"]

            # Determine the level based on the class attribute
            if class_value.startswith("section_title"):
                level = 0
            elif class_value.startswith("subsection_title"):
                level = 1
            elif class_value.startswith("subsubsection_title"):
                level = 2
            else:
                continue  # Skip <div> elements without title classes

            # Create a new <div> element and set its class attribute
            new_div = etree.SubElement(current_parent, "div")
            new_div.attrib["class"] = "section" * (level + 1)  # Add appropriate class based on level

            # Add the current <div> to the new <div> element
            new_div.append(div)

            # Update the current parent and level
            current_parent = new_div
            current_level = level
        else:
            # Add non-title <div> elements to the current parent
            current_parent.append(div)

    # Return the modified HTML as a string
    return etree.tostring(tree, encoding="unicode")

# Example usage
html = '''
<html>
  <head>...</head>
  <body>
    <div class="section_title">Section 1</div>
    <div>stuff a</div>
    <div class="subsection_title">Section 1.1</div>
    <div>stuff b</div>
    <div>stuff bx</div>
    <div class="subsubsection_title">Section 1.1.1</div>
    <div>stuff z</div>
    <div>stuff zz</div>
    <div class="subsubsection_title">Section 1.1.2</div>
    <div>stuff x</div>
    <div>stuff xx</div>
    <div>stuff xxx</div>
    <div class="subsection_title">Section 1.2</div>
  </body>
</html>
'''

output_html = group_divs_into_tree(html)
print(output_html)
The code will parse the HTML, identify the title <div> elements based on their class attributes, create a new hierarchy of <div> elements, and add the title <div>s and their following non-title <div>s to the appropriate position in the hierarchy. Finally, it will return the modified HTML as a string.

Please note that the code assumes that the class values for the title <div> elements follow the pattern "section_title", "subsection_title", "subsubsection_title", and so on. If your actual class names differ, you may need to modify the code accordingly.





Regenerate response
Send a message.

Free Research Preview. ChatGPT may produce inaccurate information about people, places, or facts. ChatGPT May 12 Version"""
    @classmethod
    def group_divs_into_tree(cls, body):
        """Peter Murray-Rust"""
        END = "[END"
        START = "[START"
        FLOAT = "float"

        skip_res = [
            re.compile("Adopted.*"),
            re.compile("Subject to Copy")
        ]


        div_styles = ["border: #8888ff solid 3px;",
                      "border: cyan dashed 2.5px;",
                      "border: green dashed 2px;",
                      ]

        # Find all <div> elements within the <body> tag
        div_elements = body.xpath("./div")

        # Create a new root <div> element to hold the tree structure
        root_div = lxml.etree.Element("div")
        root_div.attrib["class"] = "root"
        root_div.attrib["title"] = "root"

        # Initialize variables to keep track of the current parent <div> and its level
        current_parent = root_div
        current_level = 0

        parents = [root_div, None, None, None]
        start_ends = []
        parent = root_div
        for div in div_elements:
            # Check if the current <div> has a class attribute
            text = ''.join(div.itertext())
            if "class" in div.attrib:
                parent = cls.process_class_div(div, div_styles, parent, parents, text)

            elif text.startswith(START):
                parent = cls.process_ipcc_start(FLOAT, START, parent, start_ends, text)

            elif text.startswith(END):
                parent = cls.process_ipcc_end(END, START, parent, start_ends, text)

            elif cls.skip_content(text, skip_res):
                print(f"skipped {text[:50]}")

            # elif cls.is_footnote(span):
            #     print(f"skipped {text[:50]}")
            #
            else:
                parent.append(div)

        return root_div

    @classmethod
    def process_ipcc_end(cls, END, START, parent, start_ends, text):
        end_str = text[len(END):]
        if start_ends:
            # sometimes unbalanced in document
            start_str = start_ends.pop()
            if start_str != end_str:
                logger.warning(f"unbalanced: {START + start_str} and {END + end_str}")
            else:
                parent = parent.getparent()
        return parent

    @classmethod
    def process_ipcc_start(cls, FLOAT, START, parent, start_ends, text):
        start_str = text[len(START):]
        start_ends.append(start_str)
        sub_div = lxml.etree.SubElement(parent, "div")
        sub_div.attrib["class"] = FLOAT
        sub_div.attrib["title"] = text
        sub_div.attrib["style"] = "border: dashed blue 3px;"
        parent = sub_div
        return parent

    @classmethod
    def process_class_div(cls, div, div_styles, parent, parents, text):
        class_value = div.attrib["class"]
        # Determine the level based on the class attribute
        if class_value.startswith("section"):
            level = 1
        elif class_value.startswith("sub_section"):
            level = 2
        elif class_value.startswith("sub_sub_section"):
            level = 3
        else:
            level = None
            # continue  # Skip <div> elements without title classes
        if level:
            stack_parent = parents[level - 1]
            if stack_parent is not None:
                new_div = lxml.etree.SubElement(stack_parent, "div")
                new_div.attrib["title"] = text[:50]
                new_div.attrib["style"] = div_styles[level - 1]

                parent = new_div
                parents[level] = new_div
            else:
                logger.info(f"no parent on stack level {level}")



        parent.append(div)
        return parent

    @classmethod
    def skip_content(cls, text, skip_res):
        for skip_re in skip_res:
            if skip_re.match(text):
                return True
        return False

    def match_regex(div, regex, section_class, text):
        try:
            reg = re.compile(regex)
        except Exception as e:
            raise ValueError(f"BAD REGEX {regex} because {e}")
        match = reg.match(text)
        if match:
            try:
                id = match.group('id')
                div.attrib["title"] = id
            except Exception as e:
                print(f"failed to match id in {regex}")
            div.attrib["class"] = section_class


    @classmethod
    def annotate_title_sections(cls, html_elem, section_regexes=None):
        if section_regexes is None:
            raise ValueError("must have section_regexes argument")
            # this only works for IPCC draft
            # section_regexes = [
            #     ("section", "Section\s*(?P<id>\d):\s+.*"),
            #     ("sub_section", "(?P<id>\d+\.\d+)\s.*"),
            #     ("sub_sub_section", "(?P<id>\d+\.\d+\.\d+)\s.*")
            # ]

        body = HtmlLib.get_body(html_elem)
        for div in body.xpath(".//div"):
            text = ''.join(div.itertext())

            for section_regex in section_regexes:
                section_class = section_regex[0]
                regex = section_regex[1]
                if not regex:
                    raise ValueError(f"******None: regex in section_regex {section_regex}")
                cls.match_regex(div, regex, section_class, text)

    @classmethod
    def collect_floats_to_back(cls, html_elem):
        back = HtmlGroup.get_back_div(html_elem)
        floats = html_elem.xpath(".//div[@class='float']")
        logger.debug(f"floats {len(floats)}")
        for float in floats:
            back.append(float)

    @classmethod
    def create_back_div(cls, html_elem):
        back = lxml.etree.SubElement(HtmlLib.get_body(html_elem), "div")
        back.attrib["class"] = "back"
        back.attrib["title"] = "back matter"
        back.attrib["style"] = "background: #ffffdd; border: solid purple 1.5px; margin: 2px;"
        back_title = lxml.etree.SubElement(back, "div")
        back_title.text = "Back Matter, Footnotes, Figures, Tables, Boxes"
        back_title.attrib["style"] = "font-size: 20px; font-family: sanserif;"
        return back

    @classmethod
    def get_back_div(cls, html_elem):
        """get or create body/div[@class='back']"""
        backs = HtmlLib.get_body(html_elem).xpath("./div[class='back']")
        return backs[0] if len(backs) > 0 else HtmlGroup.create_back_div(html_elem)

    @classmethod
    def create_head_style_elem(cls, new_html, tail="ZZZ"):
        style = lxml.etree.SubElement(HtmlLib.get_head(new_html), CSSStyle.STYLE)
        if tail:
            style.tail = tail
        # basic styling to show divs and spans
        style.text = """
        div {border: red solid 1px; margin: 1px;}
        span {background: #eeeeee; margin: 1px;}
        div.float {background: #ddffff;}
                     """
        return style

    @classmethod
    def extract_footnotes_to_back(cls, html_elem):
        HtmlUtil.extract_footnotes(html_elem, "font-size: 6.0")

    @classmethod
    def remove_empty_divs(cls, elem):
        divs = elem.xpath(".//div")
        for div in divs:
            text = ''.join(div.itertext())
            if not text:
                div.getparent().remove(div)

    @classmethod
    def join_split_divs(cls, top_div):
        divs = top_div.xpath(".//div")
        for i, div in enumerate(divs):
            if i > 0:
                div0 = divs[i - 1]
                span0 = HtmlGroup.get_last_span(div0)
                span1 = HtmlGroup.get_first_span(div)
                if span0 is not None and span1 is not None:
                    style0 = CSSStyle.create_css_style_from_attribute_of_body_element(span0)
                    style1 = CSSStyle.create_css_style_from_attribute_of_body_element(span0)
                    if style0 == style1:
                        if span1 is not None and len(span1.text) > 0 and span1.text[0].islower():
                            # print(f" joined second_span {span1.text}")
                            HtmlUtil.join_spans_in_same_div(span0, span1)
                            for span in div.xpath("./span"):
                                div0.append(span)
                            div.getparent().remove(div)


    @classmethod
    def get_last_span(cls, div):
        spans = div.xpath("./span")
        return spans[-1] if len(spans) > 0 else None

    @classmethod
    def get_first_span(cls, div):
        spans = div.xpath("./span")
        return spans[0] if len(spans) > 0 else None

    @classmethod
    def add_paragraph_ids(cls, top_div):
        """adds sequential paragraph numbering (e.g. 1.2.3 => 1.2.3.a, 1.2.3.b etc"""
        title_para_divs = top_div.xpath(".//div[@title and contains(@class, 'section')]")
        for title_para_div in title_para_divs:
            logger.debug(f"title para divs {len(title_para_divs)}")
            title_id = title_para_div.attrib.get('title')
            if not title_id:
                continue
            followers = title_para_div.xpath("following-sibling::div")
            for i, follower in enumerate(followers):
                letter = HtmlGroup.generate_lowercase_letter_id(i)
                id = title_id + "." + letter
                span = lxml.etree.Element("span")
                span.attrib["style"] = "background: #ffffdd; font-size: 8px"
                span.text = id
                span.attrib["id"] = id
                follower.insert(0, span)

    @classmethod
    def make_hierarchical_sections_KEY(cls, html_elem, stem, section_regexes=None, outdir=None, debug=False):
        """Key formatting routine
        """
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem, outdir=outdir)
        if outdir:
            HtmlLib.write_html_file(html_elem, Path(outdir, f"{stem}_styles.html"), debug=True)
        HtmlGroup.annotate_title_sections(html_elem, section_regexes=section_regexes)
        HtmlGroup.extract_footnotes_to_back(html_elem)
        new_div = HtmlGroup.group_divs_into_tree(HtmlLib.get_body(html_elem))
        HtmlGroup.remove_empty_divs(new_div)
        HtmlGroup.join_split_divs(new_div)
        HtmlGroup.add_paragraph_ids(new_div)
        # transfer to new element (may not be necessary?)
        new_html = HtmlLib.create_html_with_empty_head_body()
        HtmlLib.get_body(new_html).append(new_div)
        HtmlStyle.transfer_head_styles(html_elem, new_html)
        HtmlGroup.collect_floats_to_back(new_html)
        HtmlGroup.annotate_ipcc_target_ids(new_html)
        if outdir:
            HtmlLib.write_html_file(new_html, Path(outdir, f"{stem}_groups.html"), debug=True)
        split_span_regex = "(?P<pre>.*(?:high|medium|low)\s*(confidence))(?P<post>.*)"
        HtmlGroup.split_spans(new_html, split_span_regex)
        if outdir:
            HtmlLib.write_html_file(new_html, Path(outdir, f"{stem}_statements.html"), debug=True)

        return new_html

    @classmethod
    def group_nested_siblings(cls, html_elem, styles=None):
        if styles is None:
            styles = [
            "border : solid purple 2px; margin:2px;",
            "border : dashed green 1.5px; margin:1.5px;",
            "border : dotted blue 1px; margin:1px;",
            ]

        HtmlGroup.group_siblings(html_elem, locator="section", style=styles[0])
        HtmlGroup.group_siblings(html_elem, locator="sub_section", style=styles[1], debug=True)
        HtmlGroup.group_siblings(html_elem, locator="sub_sub_section", style=styles[2])

    @classmethod
    def annotate_ipcc_target_ids(cls, html_elem):
        """finds sections of form {target_id, target_id...} and adds class=targets
        This is better done in the annotator workflow where it works. This is a hack for
        files which have been missed"""
        re_curly = re.compile(r"(?P<pre>.*){(?P<body>[^}]+)}(?P<post>.*)")
        TARGETS = "targets"
        curly_spans = html_elem.xpath(f".//span[contains(., '{{') and contains(., '}}')]")
        logger.debug(f"found curlies {len(curly_spans)}")
        for span in curly_spans:
            parent = span.getparent()
            match = re_curly.match(span.text)
            if match:
                for gp in ["pre", "body", "post"]:
                    t = match.group(gp)
                    if len(t) > 0:
                        if gp == "body":
                            target_ids = re.split("[,;]", t)
                            for target_id in target_ids:
                                a = lxml.etree.SubElement(parent, "a")
                                span.addprevious(a)
                                a.text = target_id
                                a.attrib["href"] = get_target_href(t)
                            # parent.remove(span)
                        else:
                            spanx = lxml.etree.SubElement(parent, "span")
                            spanx.text = t
                            for att in span.attrib:
                                spanx.attrib[att] = span.attrib[att]
                            span.addprevious(spanx)
                            spanx.attrib["anchor"] = gp

                parent.remove(span)




            span.attrib["class"] = TARGETS




    @classmethod
    def extract_section_ids(cls, html_elem, xpaths=[".//div", "./span"], regexes=None):
        """
        extracts sections and possibly subsections from compound elements (e.g. div)
        :param html_elem: compound element
        :param xpaths: list of xpath for section, optional subsection, currently len 1 or 2,
          single xpath is then wrapped to list; default [".//div", "./span"]
        :param regexes: list of regexes for each descent; single is wrapped to list ; if none given
          accepts all descendants from xpath
        """
        if not xpaths:
            return None
        if not type(xpaths) is list:
            xpaths = [xpaths]
        assert 0 < len(xpaths) <= 2, f"no xpaths given"

        if not regexes:
            regexes = []
        if not type(regexes) is list:
            regexes = [regexes]

        divs = html_elem.xpath(xpaths[0])
        sections = []
        subsections = []
        for div in divs:
            if len(regexes) > 0 and regexes[0]:
                section_id = HtmlUtil.extract_substrings(div, xpath=xpaths[0], regex=regexes[0])
                if section_id:
                    sections.append(section_id)
                    continue
            if len (regexes) > 1 and regexes[1]:
                subsection_id = HtmlUtil.extract_substrings(div, xpath=xpaths[1],
                                                            regex=regexes[1],
                                                            remove=False)
                if subsection_id:
                    subsections.append(subsection_id)
        return sections, subsections

    @classmethod
    def annotate_div_spans_write_final_html(cls, input_html, outfile, styles=None):
        if not styles:
            styles = HtmlGroup.DEFAULT_STYLES
        html_elem = lxml.etree.parse(str(input_html)).getroot()
        annotator = HtmlAnnotator.create_ipcc_annotator()
        HtmlStyle.add_head_styles(html_elem, styles)
        spans = html_elem.xpath(".//span")
        for span in spans:
            annotator.run_commands(span)
        HtmlGroup.group_nested_siblings(html_elem, styles=None)
        HtmlLib.write_html_file(html_elem, outfile, debug=True)

    @classmethod
    def split_spans(cls, html, split_span_regex):
        re_split = re.compile(split_span_regex)
        spans = html.xpath("//span")
        nspans = len(spans)

        cls.scan_remaining_spans(re_split, spans)

    @classmethod
    def scan_remaining_spans(cls, re_split, spans):
        div = None
        while len(spans) > 0:
            for i, span in enumerate(spans):
                if div is not None:
                    div.append(span)
                match = re_split.match(span.text)
                if match:
                    pre = match.group("pre")
                    post = match.group("post")
                    span.text = pre
                    parent_div = span.getparent()
                    next_span = lxml.etree.SubElement(parent_div, "span")
                    for att in span.attrib:
                        next_span.attrib[att[0]] = att[1]
                        span.addnext(next_span)
                    spans = spans[i + 1:]
                    div = lxml.etree.SubElement(parent_div.getparent(), "div")

                    break
                if i == len(spans) - 1:
                    spans = []



class HtmlUtil:
    SCRIPT_FACT = 0.9  # maybe sholdn't be here; avoid circular
    MARKER = "marker"


    @classmethod
    def remove_empty_elements(cls, elem, tag):
        """
        Maybe move to HTMLTidy
        """
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
        """
        Maybe move to HTMLTidy
        """
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
    def split_span_at_match(cls, elemx, regex, copy_atts=True, recurse=True, id_root=None, id_counter=0,
                            new_tags=None):
        """splits an elem (normally span) into 3 components by regex match
        :param elemx: elem to split (normally has a parent (e.g. div)
        :param regex: regex to split elem (of form (pre)(match)(post)
        :param copy_atts: if True copy atts from elem
        :param recurse: if True, resets elem to trailing elem and reanlyses until no more match
        :param id_root: auto-generate ids building on id_root
        :param id_counter: counter for ids
        :param new_tags: new_element tags (default span, span, span)
        :return: list of 3 elems; if new_elems[2] is not None it's available for recursion)
        """
        if not new_tags:
            new_tags = [H_SPAN, H_SPAN, H_SPAN]
        assert elemx is not None
        textx = HtmlUtil.get_text_content(elemx)
        rec = re.compile(regex)
        match = rec.match(textx)
        new_elems = [None, None, None]
        if match:
            parent = elemx.getparent()
            if len(match.groups()) != 3:  # some may be empty strings
                logging.warning(f"Cannot match {textx} against {regex}")
                return new_elems, id_counter
            group1 = match.group(1)
            if group1 != "":  # don't add empty string
                elemx = HtmlUtil.add_sibling_after(elemx, new_tags[0], replace=True, copy_atts=copy_atts,
                                                   text=group1)
                new_elems[0] = elemx
                new_elems[0].attrib["class"] = "re_pref"
                id_counter = cls.add_id_increment_counter(id_counter, id_root, elemx)
            new_elems[1] = HtmlUtil.add_sibling_after(elemx, new_tags[1], copy_atts=copy_atts, text=match.group(2))
            new_elems[1].attrib["class"] = "re_match"
            id_counter = cls.add_id_increment_counter(id_counter, id_root, new_elems[1])
            if match.group(3) != "":  # don't add empty string
                new_elems[2] = HtmlUtil.add_sibling_after(new_elems[1], new_tags[2], copy_atts=copy_atts,
                                                          text=match.group(3))
                new_elems[2].attrib["class"] = "re_post"

                id_counter = cls.add_id_increment_counter(id_counter, id_root, new_elems[2])
                if recurse:
                    _, id_counter = HtmlUtil.split_span_at_match(new_elems[2], regex, copy_atts=copy_atts,
                                                                 recurse=recurse, id_root=id_root,
                                                                 id_counter=id_counter)
        return new_elems, id_counter

    @classmethod
    def add_id_increment_counter(cls, id_counter, id_root, html_elem):
        if id_root:
            html_elem.attrib[A_ID] = id_root + str(id_counter)
            id_counter += 1
        return id_counter

    @classmethod
    def add_sibling_after(cls, anchor_elem, tag, replace=False, copy_atts=False, text=None):
        """adds new trailing sibling of anchor_elem with tag
        :param tag: tag for new element
        :param anchor_elem: reference element, must have a parent
        :param replace: if True, remove anchor element
        :param copy_atts: copy attributes from anchor
        :param text: if not None add text to new element
        :return: new sibling with optional ayytributes and text



        """

        assert anchor_elem is not None
        assert tag
        parent = anchor_elem.getparent()
        assert parent is not None, f"No parent for anchor_elem"
        sibling = lxml.etree.SubElement(parent, tag)
        if copy_atts:
            for k, v in anchor_elem.attrib.items():
                sibling.attrib[k] = v
        anchor_elem.addnext(sibling)
        if text:
            sibling.text = text
        if replace:
            parent.remove(anchor_elem)
        return sibling

    @classmethod
    def create_div_span(cls, text, style=None):
        """utility method to create a div/span@text (probably mainly for testing)
        :param text: to add
        :return: the div"""
        div = lxml.etree.Element(H_DIV)
        span = lxml.etree.SubElement(div, H_SPAN)
        if style:
            css_style = CSSStyle.create_css_style_from_css_string("font-size:12; font-weight: bold;")
            HtmlStyle.set_style(span, css_style.get_css_value())
        span.text = text
        return div, span

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
    def is_script_type(cls, last_span, this_span, script_type, ydown=True) -> bool:
        """heuristc to determine whether this_span is a sub/superscript of last_span
        NOTE: IF Y is DOWN the page, a superscript has SMALLER y-value, etc. (logic reversed if not ydown)
        :param last_span: if None, returns false
        :param this_span: if not smaller by SCRIPT_FACT return False
        :param script_type: SScript.SUB or SScript.SUP
        :param ydown: True if y increases down thr page (e.g. SVG) (DEFAULT) else False
        :return: True if smaller and moved in right y-direction
        """
        if this_span is None:
            return False
        # try to find missing last_span
        if last_span is None:
            last_span = this_span.xpath("preceding::span")
            if len(last_span) == 0:
                return False
            last_span = last_span[0]
        try:
            last_font_size = None
            this_font_size = None
            last_font_size = last_span.text_style._font_size
            this_font_size = this_span.text_style._font_size
        except Exception as e:
            pass
            # no font style
        is_script = cls.is_required_script_type(script_type, last_font_size, last_span, this_font_size, this_span,
                                            ydown)
        return is_script

    @classmethod
    def is_required_script_type(cls, script_type, last_font_size, last_span, this_font_size, this_span, ydown=True, ):
        """old approach with AmiSpan
        This is not right!"""
        YFACTOR = 3 # pixels
        is_script = False
        script_factor = HtmlUtil.SCRIPT_FACT
        # if font sizes not given assume they don't matter
        if last_font_size and this_font_size:
            passed_font_size_change = this_font_size < script_factor * last_font_size
        else:
            passed_font_size_change = True
        # use y coords
        if passed_font_size_change:
            try:
                last_y = last_span.y
                this_y = this_span.y
            except Exception as e:
                last_y = HtmlUtil.get_float(last_span, "y0")
                this_y = HtmlUtil.get_float(this_span, "y0")
            try:
                last_x = last_span.x
                this_x = this_span.x
            except Exception as e:
                last_x = HtmlUtil.get_float(last_span, "x0")
                this_x = HtmlUtil.get_float(this_span, "x0")
            if script_type == SScript.SUB:
                # is it lowered? Y DOWN
                is_script = ydown and (last_y < this_y)
            elif script_type == SScript.SUP:
                # is it raised? Y DOWN
                is_script = ydown and (last_y - this_y) > YFACTOR
            else:
                raise ValueError("bad script type ", script_type)
            if False:
                if is_script and last_x and this_x:
                    is_script = last_x < this_x
        return is_script

    @classmethod
    def extract_footnotes(cls, html_elem, font_size_condition, title="Footnotes"):
        divs = html_elem.xpath(f"//div[span[contains(@style, '{font_size_condition}') and number(.)=number(.)]]")
        footnote_div = HtmlGroup.get_back_div(html_elem)
        footnote_title = lxml.etree.SubElement(footnote_div, "div")
        footnote_title.text = title
        ul = lxml.etree.SubElement(footnote_div, "ul")
        current_li = None
        for div in divs:
            spans = div.xpath("./span")
            for i, span in enumerate(spans):
                if XmlLib.is_integer(span) and (i == 0 or HtmlUtil.is_superscript(spans[i - 1], span)):
                    current_li = lxml.etree.SubElement(ul, "li")
                if current_li is not None:
                    current_li.append(span)


    @classmethod
    def annotate_script_type(cls, span, script_type, script_factor=None, last_span=None, ydown=True):
        """is a span a sub or superscript?
        :param span: to test
        :param script_type: SScript.SUB or SScript.SUPER
        :param script_factor: if None, defaults to HtmlUtil.SCRIPT_FACT
        :param last_span: preceding span; if None tries xpath("preceding::span")
        :param ydown: is y running donw the page?
        """
        if span is None or not script_type:
            return None
        if not script_factor:
            script_factor = HtmlUtil.SCRIPT_FACT
        if not last_span:
            last_span = span.xpath("preceding::span")
            if len(last_span) == 0:
                return None
            last_span = last_span[-1]
        csss = CSSStyle.create_css_style_from_attribute_of_body_element(span)
        last_csss = CSSStyle.create_css_style_from_attribute_of_body_element(last_span)
        font_size = csss.font_size
        last_font_size = last_csss.font_size
        is_script = None
        if font_size and font_size < script_factor * last_font_size:
            last_y = CSSStyle.get_y0(last_span)
            this_y = CSSStyle.get_y0(span)
            if script_type == SScript.SUB:
                # is it lowered? Y DOWN
                is_script = ydown == (last_y < this_y)
            elif script_type == SScript.SUP:
                # is it raised? Y DOWN
                is_script = ydown == (last_y > this_y)
            if is_script:
                pass
        return is_script


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
        """
        convenience method; avoids having to remember join/itertext
        """
        return ''.join(elem.itertext())

    @classmethod
    def add_generated_ids(cls, root_elem):
        """adds IDs to all elements in document order
        :param root_elem: element defining tree of subelements"""
        xpath = "//*"
        elems = root_elem.xpath(xpath)
        for i, el in enumerate(elems):
            el.attrib[A_ID] = A_ID + str(i)
    @classmethod
    def join_spans_in_same_div(cls, span0, span1, addspace=True, remove=True):
        """
        joint <span>...</span><span>...</span> into <span>...</span>
        this structure arises when PDF or images is parsed and spans have the same styles (size/style/weight) and can be merged
        we assume that style and geometry cheking has been done
        :param span0: first <span>, text will be increased from span1
        :param span1: text will be appended to span0 text
        :param remove: remove span1 (default)
        """
        if HtmlUtil.check_tag(span0, "span") and HtmlUtil.check_tag(span1, "span"):
            parent1 = span1.getparent()
            if addspace:
                span0_not_end_space = len(span0) > 0 and span0[-1] != " "
                span1_not_start_space = len(span1) > 0 and span1[-1] != " "
                if span0_not_end_space and span1_not_start_space:
                    span0.text += " "
            span0.text += span1.text
            if remove:
                parent1.remove(span1)




    @classmethod
    def create_skeleton_html(cls):
        """create empty html tree
        html
            head
                meta
                # style
            body

        :return: this html
        """

        html = lxml.etree.Element(H_HTML)
        head = lxml.etree.Element(H_HEAD)
        html.append(head)
        meta = lxml.etree.Element(H_META)
        head.append(meta)
        style = lxml.etree.Element(H_STYLE)  # empty <style> means no display
        # head.append(style)
        body = lxml.etree.Element(H_BODY)
        html.append(body)
        return html

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
        """
        Maybe move to HTMLTidy
        """
        assert elem is not None, f"must have elem"
        if xpath:
            els = elem.xpath(xpath)
        else:
            els = [elem]
        elems = []
        for el in els:
            css_style = CSSStyle.create_css_style_from_attribute_of_body_element(el)
            if condition:
                if css_style.obeys(condition):
                    if remove:
                        cls.remove_elem_keep_tail(el)

    @classmethod
    def remove_headers_and_footers_using_pdfminer_coords(cls, ref_elem, pagesize, header_height, footer_height,
                                                         marker_xpath, page_tops=None):
        """
        NOT COMPLETE - there are no footers because of the coordinate system.

        Maybe move to HTMLTidy

        the @top represents the y-coordinate from the start of the document (pdfminer?).
        this means we have to subtract pagesizes from it.
        """
        debug = False
        elems = ref_elem.xpath(marker_xpath)

        last_top = 0
        for elem in ref_elem.xpath("//*[@style]"):
            ycoord0 = HtmlUtil.get_y0(elem)
            if not ycoord0:
                continue
            text = XmlLib.get_text(elem).strip()
            page_top_y = HtmlUtil.get_largest_coord_less_than(page_tops, ycoord0)
            if page_top_y is None:
                print(f"cannot find page top {ycoord0}")
                continue
            page_top_y = float(page_top_y)
            ycoord = ycoord0 - page_top_y

            # print(f"TOP {ycoord0} {ycoord} {pagesize} {ycoord % pagesize}")
            in_top = ycoord < header_height
            if in_top:
                if debug:
                    print(f"TOP  {text}")
            in_bottom = ycoord > pagesize[0] - footer_height
            if in_bottom:
                if debug:
                    print(f"BOTTOM  {text}")
            if in_top or in_bottom:
                if len(text.strip()) > 0:
                    logging.warning(f"removing top text {text}")
                cls.remove_elem_keep_tail(elem)
            else:
                # skipped
                pass

    @classmethod
    def get_largest_coord_less_than(cls, page_tops, coord):
        """
        iterate through sorted list of page_tops and find the largest less than coord
        :param page_tops: sorted increasing list of page tops
        :param coord: actual coordinate
        """
        if page_tops is None or coord is None:
            return None
        for i, page_top in enumerate(page_tops):
            if float(page_top) > float(coord):
                if i == 0:
                    return None
                return page_tops[i - 1]
        return None

    @classmethod
    def remove_lh_line_numbers(cls, ref_elem):
        cls.find_elements_with_style(ref_elem, ".//*[@style]", "left<49", remove=True)
        """
        Maybe move to HTMLTidy
        """

    @classmethod
    def remove_style_attribute(cls, ref_elem, style_name):
        """
        Maybe move to HTMLTidy
        """

        elems = ref_elem.xpath(".//*")
        for el in elems:
            css_style = CSSStyle.create_css_style_from_attribute_of_body_element(el)
            if css_style.name_value_dict.get(style_name):
                css_style.name_value_dict.pop(style_name)
                css_style.apply_to(el)

    @classmethod
    def remove_large_fonted_elements(cls, ref_elem):
        """
        Maybe move to HTMLTidy
        """
        cls.find_elements_with_style(ref_elem, ".//*[@style]", "font-size>30", remove=True)

    @classmethod
    def find_constant_coordinate_markers(cls, ref_elem, xpath, style="top"):
        """
        finds a line with constant difference from top of page
<div style="top: 50px;"><a name="1">Page 1</a></div>
        """
        """
        Maybe move to HTMLTidy
        """

        elems = ref_elem.xpath(xpath)
        coords = []
        for elem in elems:
            css_style = CSSStyle.create_css_style_from_attribute_of_body_element(elem)
            coord = css_style.name_value_dict.get(style)
            if coord:
                try:
                    coords.append(float(coord[:-2]))
                except Exception:
                    logging.warning(f"cannot parse {coord} for {style}")
        if not coords:
            return None, None, []
        np_coords = np.array(coords)

        x = np.array(range(np_coords.size)).reshape((-1, 1))
        model = LinearRegression().fit(x, coords)
        r_sq = model.score(x, coords)
        if r_sq < 0.98:
            logging.warning(f"cannot calculate offset reliably")
        return model.intercept_, model.coef_, np_coords

    @classmethod
    def remove_unwanteds(cls, top_elem, unwanteds):
        """
        Maybe move to HTMLTidy
        """
        if not unwanteds:
            logging.warning(f"no unwanteds to remove")
            return
        for key in unwanteds:
            unwanted = unwanteds[key]
            xpath = unwanted[U_XPATH]
            if xpath:
                regex = unwanted[U_REGEX]
                regex_comp = re.compile(regex) if regex else None
                elems = top_elem.xpath(xpath)
                for elem in elems:
                    text = HtmlUtil.get_text_content(elem)
                    matched = regex_comp.search(text) if regex_comp else True
                    if matched:
                        cls.remove_elem_keep_tail(elem)

    @classmethod
    def remove_newlines(cls, elem):
        """remove \n"""
        """
        Maybe move to HTMLTidy
        """

        for el in elem.xpath(".//*[not(*)]"):
            text = HtmlUtil.get_text_content(el)
            text1 = text.replace('\n', '')
            if text1 != text:
                el.text = text1

    @classmethod
    def remove_style(cls, xpath_root_elem, names):
        """
        removes name-value pairs from css-style and reapply to xpath'ed elements"""
        """
        Maybe move to HTMLTidy
        """

        xpath = f".//*[@style]"
        try:
            styled_elems = xpath_root_elem.xpath(xpath)
        except lxml.etree.XPathEvalError as xpee:
            raise ValueError(f"Bad xpath {xpath}")

        for styled_elem in styled_elems:
            css_style = CSSStyle.create_css_style_from_attribute_of_body_element(styled_elem)
            css_style.remove(names)
            css_style.apply_to(styled_elem)
            style = HtmlStyle.get_cssstyle_string(styled_elem)

    @classmethod
    def extract_substrings(cls, elem, xpath=None, regex=None, remove=False, include_none=False, add_id=False):
        """gets substring from body of text in elem
        regex of form (?P<pre>)(?P<body>)(?P<post>)
        pre and or post can be missing
        (There will be better ways of doing this!)
        :param elem:to query
        :param xpath: to find descendant subelement
        :param regex: to find string in subelement (must have 3 capture groups)
        :param remove: removes body text and joins pre to post (use with care, default False)
        :param include_none: If true include failed matches as None; default False
        :param_add_id: add extracted text as attribute on subelement
        if pre and tail are present, elem.text =< pre+post
        if pre is missing elem.text => post
        if tail is missing elem.text => pre
        if both are missing no removal
        :return: regex.match.groupindex(?P<body>) if matched else None
        """
        sub_elems = elem.xpath(xpath)
        sub_elem = sub_elems[0] if len(sub_elems) > 0 else None
        substrings = []
        re0 = re.compile(regex)
        for sub_elem in sub_elems:
            substring = cls.extract_substring(re0, remove, sub_elem)
            if substring and add_id:
                sub_elem.attrib["id"] = substring
            if substring or include_none:
                substrings.append(substring)
        return substrings

    @classmethod
    def extract_substring(cls, re0, remove, sub_elem):
        match = re0.match(sub_elem.text)
        substring = None
        if match:
            substring = match.group("body")
            if remove:
                try:
                    pre = match.group("pre")
                    post = match.group("post")
                    sub_elem.text = pre + post
                except:
                    pass
        return substring

    @classmethod
    def get_float(cls, elem, attrib_name):
        try:
            val = elem.attrib[attrib_name]
            return float(val)
        except Exception as e:
            return None

    @classmethod
    def check_tag(cls, elem, tag):
        """checks that elem is an Element with given tag"""
        return type(elem) is lxml.etree._Element and elem.tag == tag

    @classmethod
    def get_id(cls, div):
        """gets value of "id" attribute
        """
        return None if div is None else div.attrib.get("id")



class HtmlAnnotator:
    """inline annotator for HTML elements
    stores and runs AnnotatorCommands

    annotator = Annotator()
    command = AnnotatorCommand(html_class="section_title", regex="Section\s+(?P<id>\d+):\s+(?P<title>.*)", add_id=True, add_title=True)
    annotator.add_command(command)
    annotator.run_commands(elem)

    """

    def __init__(self):
        self.commands = []

    def add_command(self, command):
        if command:
            self.commands.append(command)

    def run_commands(self, target_elem):
        """
        iterate commands (order is order of their addition
        """
        for command in self.commands:
            command.run_command(target_elem)

    @classmethod
    def create_ipcc_annotator(cls):
        """a set of general operations for IPCC"""
        annotator = HtmlAnnotator()
        annotator.add_command(
            AnnotatorCommand(html_class="section_title", regex="Section\s+(?P<id>\d+):\s+(?P<title>.*)",
                             add_id="section_|", add_title="|", style="{color : blue; background : pink;}",
                            desc="add id and title for 'Section: ...'")
        )
        annotator.add_command(
            AnnotatorCommand(html_class="sub_section_title", regex="\s*(?P<id>\d+\.\d+)\s+(?P<title>.*)",
                             add_id="subsection_|", add_title="|", style="{color : green; background : yellow;}"))
        annotator.add_command(
            AnnotatorCommand(html_class="sub_sub_section_title", regex="^\s*(?P<id>\d+\.\d+\.\d+)\s+(?P<title>.*)",
                             add_id="subsection_|", add_title="|", style="{color : black; background : #dddddd;}"))
        annotator.add_command(
            AnnotatorCommand(html_class="confidence",
                             regex="^\s*\(?(?P<title>(very high|high|medium|low) confidence)\)?",
                             add_id="confidence_|", add_title="|", style="{color : black; background : #dd88dd;}"))
        annotator.add_command(
            AnnotatorCommand(html_class="probability",
                             regex="^\s*\(?(?P<title>(likely|very likely|extremely likely|virtually certain))\)?",
                             add_id="probability_|", add_title="|", style="{color : cyan; background : #dd8888;}"))
        annotator.add_command(
            AnnotatorCommand(html_class="superscript", script="super", add_id="super_|", add_title="|",
                             style="{color : blue; backgroound: yellow}"))
        annotator.add_command(
            AnnotatorCommand(html_class="start", regex="\s*\[?START\s*(?P<title>FIGURE|TABLE)\s*(?P<id>\d+\.\d+)\s*(HERE)?\]?",
                             add_id="start_|", add_title="start_|", style="{color : green; background: pink}"))
        annotator.add_command(
            AnnotatorCommand(html_class="end", regex="\s*\[?END\s*(?P<title>FIGURE|TABLE)\s*(?P<id>\d+\.\d+)\s*(HERE)?\]?",
                             add_id="end_|", add_title="end_|", style="{color : green; background: blue}"))
        annotator.add_command(
            AnnotatorCommand(html_class="targets", regex=".*\{(?P<title>.+)\}.*",
                             add_id="chunk_|", add_title="|", style="{color : green; background: orange}",
                            desc="IPCC target IDs in curly brackets {WG1 SPM A.1.2, WGII SPM B.2.3}"))
        annotator.add_command(
            AnnotatorCommand(html_class="cruft", regex="^.*(Subject to Copy Edit |Adopted Longer Report IPCC AR6 SYR).*$",
                             add_id="cruft_|", add_title="|", delete=True, style="{color : green; background: black}"))
        annotator.add_command(
            AnnotatorCommand(html_class="page", regex="^(?P<title>p\.\d+)",
                              add_title="|", style="{color : purple}"))
        annotator.add_command(
            AnnotatorCommand(html_class="fact", xpath="self::span[contains(@class, 'confidence')]/preceding-sibling::span[1]",
                              style="{color : purple}"))
        annotator.add_command(
            AnnotatorCommand(html_class="group", group_xpath="div[span[contains(@class, 'start')]]",
                             end_xpath="self::div[span[contains(text(),'END')]]",
                            desc="?extracts groups and mmoves to end"))
        annotator.add_command(
            AnnotatorCommand(html_class="subsubsection", group_xpath="div[span[contains(@class, 'subsubsection_title')]]",
                             end_xpath="self::div[span[contains(text(),'section_title')]]"))
        annotator.add_command(
            AnnotatorCommand(html_class="footnote", xpath="//div[span[contains(@style, 'font-size: 6.0') and number(.)=number(.)]]",
                             desc="horrible hack testing font-size"))


        return annotator


ANN_SPLIT = "|"
LEN_TITLE = 50
class AnnotatorCommand:
    """an annotation command
    e.g.
    command = AnnotatorCommand(html_class="section_title", regex="Section\s+(?P<id>\d+):\s+(?P<title>.*)", add_id=True, add_title=True)
    annotator.add_command(command)
    annotator.run_commands

    """

    def __init__(self, html_class=None, regex=None, add_id=None, add_title=None, script=None, style=None,
                 delete=False, xpath=None, group_xpath=None, end_xpath=None, desc=None):
        self.html_class = html_class
        self.re = None
        if regex:
            try:
                self.re = re.compile(regex)
            except Exception as e:
                raise ValueError(f"Cannot compile regex {regex} because {e}")

        # add_id and add_title are of form foo|bar where extracted id replaces |
        if add_id:
            add_id = add_id.split(ANN_SPLIT)
        self.add_id = None if not add_id or len(add_id) != 2 else add_id
        if add_title:
            add_title = add_title.split(ANN_SPLIT)
        self.add_title= None if not add_title or len(add_title) != 2 else add_title

        self.html_class = html_class
        self.script = script
        self.style = style
        self.delete = delete
        self.xpath = xpath
        self.group_xpath = group_xpath
        self.end_xpath = end_xpath
        self.desc = desc

# class AnnotatorCommand

    def run_command(self, elem):
        # print(f"run_command , tag, {elem.tag} parent: {elem.getparent()}")
        if self.re:
            self.run_regex(elem)
        # elif self.extract:
        #     self.run_extract(elem)
        elif self.xpath :
            self.run_xpath(elem)
        elif self.script == "sub":
            self.run_subscript(elem)
        elif self.script == "super":
            self.run_superscript(elem)
        elif self.group_xpath is not None:
            self.run_group_xpath(elem)

    # class AnnotatorCommand

    def run_regex(self, elem):
        text = elem.text
        if text is None:
            print(f"regex: None text in {elem} {elem.tag}")
            return
        match = None
        try:
            match = self.re.match(text)
        except Exception as e:
            print(f"match fail {e}")
            return
        if match:
            if self.delete:
                self.remove_elem(elem)
                return
            if self.add_id and "id" in match.groupdict():
                elem.attrib["id"] = self.add_id[0] + match.group("id") + self.add_id[1]
            if self.add_title and "title" in match.groupdict():
                elem.attrib["title"] = self.add_title[0] + match.group("title") + self.add_title[1][:LEN_TITLE]
            if self.html_class:
                self.update_class(elem, self.html_class)

    # class AnnotatorCommand

    def run_xpath(self, elem):
        xp_elems = elem.xpath(self.xpath)
        if not xp_elems:
            return
        for xp_elem in xp_elems:
            if self.delete:
                xp_elem.getparent().remove(xp_elem)
                return
            if self.html_class:
                self.update_class(xp_elem, self.html_class)
                tostring = lxml.etree.tostring(xp_elem)
                pass

    # class AnnotatorCommand

    def update_class(self, elem, html_class):
        classes = []
        HtmlClass.set_class_on_element(elem, html_class)
        if False:
            if elem.attrib.get("class"):
                classes = elem.attrib["class"].split(" ")
            if html_class not in classes:
                classes.append(html_class)
                elem.attrib["class"] = " ".join(classes)

    def run_subscript(self, span):
        is_sub = HtmlUtil.annotate_script_type(span, SScript.SUB, ydown=False)
        if is_sub:
            span.attrib["title"] = "subscript_{span.text}"
            print(f"SUB {span.text}")

    # class AnnotatorCommand

    def run_superscript(self, span):
        is_super = HtmlUtil.annotate_script_type(span, SScript.SUP, ydown=False)
        if is_super:
            span.attrib["title"] = f"superscript_{span.text}"

    # class AnnotatorCommand

    def run_group_xpath(self, child_elem):
        """group following siblings of elem"""

        result = None
        if child_elem is None:
            return None
        parent_elem = child_elem.getparent()
        if parent_elem is None:
            return None
        group_leads = parent_elem.xpath(self.group_xpath)
        if len(group_leads) > 0:
            print(f"group lead count {len(group_leads)} {self.group_xpath}")
        else:
            pass
        for i, group_lead in enumerate(group_leads):
            # print(f"group lead {lxml.etree.tostring(group_lead)}")
            # end_grouo = group_leads[i + 1] if i < len(group_leads) - 1 else None
            self.make_group(parent_elem, group_lead)

    # class AnnotatorCommand

    def make_group(self, elem, group_lead, end_group=None):
        parent = XmlLib.getparent(elem, debug=True)
        if parent is None:
            raise ValueError("null parent")
        siblings = group_lead.xpath("following-sibling::*")
        if len(siblings) == 0:
            print(f"no siblings: {group_lead.text}")
            pass
        else:
            print(f"siblings {len(siblings)}!!!")
        div = lxml.etree.SubElement(parent, "div")
        div.append(group_lead)
        div.attrib["title"] = group_lead.text if group_lead.text else "?"
        div.attrib["style"] = "border:black dashed 2px;"
        xp = self.end_xpath
        xp = "self::div[span[contains(text(),'END')]]"
        # print(f"end_xpath {xp}")
        for sibling in siblings:
            print(f"sibling: {''.join(sibling.itertext())}")
            end_sib = None
            try:
                end_sib = sibling.xpath(xp)
            except Exception as e:
                print(f"failed xpath {xp} {e}")
            if end_sib and len(end_sib) > 0:
            # if sibling != end_group:
            #     print(f"sibling {sibling}")
                break
            div.append(sibling)
        return div

    # class AnnotatorCommand

    def run_extract(self, elem):

        """extract group. optinally write to file. currently NO-OP"""
        print(f"run_extract is NO-OP")
        return None

    # class AnnotatorCommand

    def remove_elem(self, elem, debug=False):
        if elem is None:
            return
        parent = elem.getparent()
        if parent is None:
            if debug:
                print(f"element {elem} has no parent")
            return
        parent.remove(elem)



STYLE_CURLY_RE = re.compile("(?P<pre>.*){(?P<value>[^}]*)}(?P<post>.*)")
class HtmlStyle:
    """
    methods to process style attributes and <style> elements
    no instance data
    """

    @classmethod
    def get_cssstyle_string(cls, elem):
        """
        convenience method to get element style
        :param elem: to get style from
        :return: style or None
        """
        return elem.attrib.get("style")

# class HtmlStyle

    @classmethod
    def set_style(cls, elem, value):
        """
        convenience method to set style on element
        :param elem:element to set style on
        :param value: css string; if "" or None remlves attribute
        """
        if elem is not None:
            XmlLib.set_attname_value(elem, "style", value)

    # class HtmlStyle

    @classmethod
    def extract_all_style_attributes_to_head(cls, html_elem):
        """
        Finds all elements with @style attribute and extacts the tdxt styles to <head>
        Also sets body styles to normal
        :param html_elem: total html object to normalize. Must have <head> and <body>
        """
        HtmlStyle.remove_empty_styles(html_elem)
        styled_elems = html_elem.xpath(".//*[@style]")
        for i, styled_elem in enumerate(styled_elems):
            classref = f"s{i}"
            HtmlStyle.add_element_with_style(classref, html_elem, styled_elem)
        # does this do anything???
        body = html_elem.xpath("/html/body")
        if len(body) != 1:
            raise ValueError(f"document should have exactly 1 body tag")
        style = CSSStyle()
        style.create_css_style_from_css_string(
            "font-style: normal; "
            "font-weight: normal; "
            "font-stretched: normal; "
            "opacity: 1; "
            "color: black;"
        )

    # class HtmlStyle

    @classmethod
    def add_element_with_style(cls, classref, html_elem, styled_elem):
        """
        adds
        """
        head = html_elem.xpath("/html/head")[0]
        elem_style = HtmlStyle.get_cssstyle_string(styled_elem)
        if elem_style is None or elem_style == "":
            return
        css = CSSStyle.create_css_style_from_css_string(elem_style)
        if css is None:
            raise ValueError(f"css is None")

        extracted_style_elem, remaining_style, new_class = css.extract_text_styles_into_class(classref)
        if extracted_style_elem is not None:
            HtmlStyle.set_style(styled_elem, remaining_style)
            HtmlClass.set_class_on_element(styled_elem, classref, replace=False)
            head.append(extracted_style_elem)

    # class HtmlStyle

    @classmethod
    def remove_empty_styles(cls, html_elem):
        """
        removes all empty style attributes (style="")
        """
        empty_styled_elems = html_elem.xpath(".//*[normalize-space(@style)='']")
        for elem in empty_styled_elems:
            HtmlStyle.delete_style(elem)

    # class HtmlStyle

    @classmethod
    def delete_style(cls, elem):
        """
        conveniennce method to delete style attribute
        """
        XmlLib.remove_attribute(elem, "style")

    # THESE CAN BECOME INSTANCE METHODS

    # class HtmlStyle

    @classmethod
    def normalize_head_styles(cls, elem, italic_bold=True, outdir=None):
        """
        creates multidict fot head styles
        :param elem: document to analyse
        :return: dict of classref_sets indexed by style strings

        e.g. item {font-family: TimesNewRomanPSMT; font-size: 6px;}: ['.s17', '.s19', '.s21', '.s27', '.s5', '.s7']
        """
        style_to_classref_set = defaultdict(set)
        head_styles = elem.xpath("/html/head/style")
        # we use one classref - style per HTML style
        for html_style in head_styles:
            # consists of classref snd style_string
            classref, style_s = cls.extract_classref_and_cssstring_from_html_style(html_style)
            style_value = style_s
            if italic_bold:
                new_css_s = AmiFont.create_font_edited_style_from_css_style_object(style_s)
                css_style = CSSStyle.create_css_style_from_css_string(new_css_s)
                if css_style is not None:
                    css_style.extract_bold_italic_from_font_family()
                    style_value = css_style.get_css_value(wrap_with_curly=True)
                    HtmlStyle.replace_curly(html_style, style_value)
            html_style.attrib[CLASSREF] = classref
            style_to_classref_set[style_value].add(classref)
        if outdir:
            HtmlLib.write_html_file(elem, Path(outdir, "normalized.html"))
        return style_to_classref_set

    @classmethod
    def extract_classref_and_cssstring_from_style_text(cls, html_style_string):
        """parses text in html <style> into classref and cssstring
        only one style per html element
        :param html_style_string: of form <selector> {<value>}
        :return selector , value
        """

        style_re = re.compile("\s*(?P<classref>[^\s]*)\s+{\s*(?P<cssstring>.*)}\s*")
        match = style_re.match(html_style_string)
        if not match:
            return None, None
        return match.group("classref"), match.group("cssstring")

    # class HtmlStyle

    @classmethod
    def extract_styles_and_normalize_classrefs(cls, html_elem, outdir=None):
        """
        Extract styles from document
        move to head and normalize classrefs
        delete redundant classrefs and styles
        map document instamces of styles onto normalized classrefs
        :param html_elem: html document to normalize

        Should be in an object


        """
        # html_elem = html_elem.xpath("/*")[0] if type(html_elem) is _ElementTree else html_elem
        cls.extract_all_style_attributes_to_head(html_elem)
        if outdir:
            HtmlLib.write_html_file(html_elem, Path(outdir, "styles1.html"), debug=True)
        style_to_classref_set = cls.normalize_head_styles(html_elem, outdir=outdir)
        classref_index = cls.create_classref_index(style_to_classref_set)
        deletable_classrefs = cls.get_redundant_classrefs(classref_index)
        cls.delete_redundant_styles(deletable_classrefs, html_elem)
        cls.normalize_classrefs_on_elements(html_elem, classref_index)

    # class HtmlStyle

    @classmethod
    def normalize_classrefs_on_elements(cls, html_elem, classref_index):
        """
        Finds all elments with @class attribute and normalize to minimal set
        """
        classed_elems = html_elem.xpath("//*[@class]")
        for classed_elem in classed_elems:
            html_class = HtmlClass.create_from_classed_element(classed_elem)
            classref = html_class.create_classref()
            normalized_classref = HtmlClass.remove_dot(classref_index.get(classref))
            classref = HtmlClass.remove_dot(classref)
            if normalized_classref != classref:
                html_class.replace_class(classref, normalized_classref)
                if html_class.class_string:
                    HtmlClass.set_class_on_element(classed_elem, html_class.class_string)

    # class HtmlStyle

    @classmethod
    def delete_redundant_styles(cls, deletable_classrefs, html_elem):
        """
        deletes redundant <style>s in head
        """
        styles_with_classrefs = html_elem.xpath("/html/head/style[@classref]")
        for style in styles_with_classrefs:
            classref = style.attrib.get(CLASSREF)
            if classref in deletable_classrefs:
                XmlLib.remove_element(style)

    # class HtmlStyle

    @classmethod
    def get_redundant_classrefs(cls, classref_index):
        """
        makes list of redundant classrefs
        :param classref_index: dictionary mapping classrefs onto normalized classref
        :return: list of redundant classrefs
        """
        redundant_classrefs = []
        for item in classref_index.items():
            if item[0] != item[1]:
                redundant_classrefs.append(item[0])
        return redundant_classrefs

    # class HtmlStyle

    @classmethod
    def create_classref_index(cls, style_to_classref_set):
        """
        maps all items in classref sets onto (arbitrarily) the first
        :param style_to_classref_set: classref_sets mmapped by style value
        :return:dict mapping redundant classrefs onto normalized classref
        May benefit from being in a class
        """
        classref_index = dict()
        for item in style_to_classref_set.items():
            classref_list = list(sorted(item[1]))
            classref0 = list(classref_list)[0]
            for classref in classref_list:
                classref_index[classref] = classref0
        return classref_index

    # class HtmlStyle

    @classmethod
    def add_head_styles(cls, html_elem, styles, normalize_font=True):
        """
        this is crude
        'style of form
            "div", [("border", "red solid 0.5px"), ("background", "yellow)])
        """
        for style in styles:
            # print(f"style {style}")
            HtmlLib.add_head_style(html_elem, style[0], style[1])

# TODO
# create_font_edited_style_from_css_style_object

    @classmethod
    def transfer_head_styles(cls, html_elem, new_html):
        """copies html/head/"""
        new_style_elem = HtmlGroup.create_head_style_elem(new_html, tail="\n")
        styles = html_elem.xpath("/html/head/style")
        for style in styles:
            new_style_elem.getparent().append(copy.deepcopy(style))

    @classmethod
    def extract_classref_and_cssstring_from_html_style(cls, html_style_elem):
        if html_style_elem is None:
            return None, None
        return cls.extract_classref_and_cssstring_from_style_text(html_style_elem.text)

    @classmethod
    def create_classref_cssstring_table(cls, html_styles):
        table = []
        for html_style in html_styles:
            table.append(HtmlStyle.extract_classref_and_cssstring_from_html_style(html_style))
        return table

    @classmethod
    def replace_curly(cls, elem, new_curly):
        """
        replace contents of {...}
        :param elem: html <style> element
        :param elem: new content
        """

        if elem is not None:
            match = STYLE_CURLY_RE.match(elem.text)
            if match:
                new_text = match.group("pre") + new_curly + match.group("post")
                elem.text = new_text

    @classmethod
    def lookup_head_style_by_classref(cls, elem):
        """
        :param elem: elements with @class attribute
        :return: CSSStyle object with HtmlStyle
        """
        clazz = elem.get("class")
        css_style = HtmlStyle.lookup_head_style_by_class(elem, clazz)
        return css_style

    @classmethod
    def lookup_head_style_by_class(cls, html, clazz):
        """
        :param html: HTML element with head/style
        :param clazz: class to retirve style element
        """
        styles = html.xpath(f"/html/head/style[contains(.,'.{clazz} ')]")
        if len(styles) == 0:
            print(f"no styles for {clazz}")
            return None
        head_style = styles[0]
        _, css_style = CSSStyle.create_css_style_from_html_head_style_elem(head_style)
        return css_style

    @classmethod
    def is_bold(cls, elem):
        """
        finds @class in elem and looks up style in html/head
        """
        if elem is None:
            return False
        css_style = HtmlStyle.lookup_head_style_by_classref(elem)
        if not css_style:
            print(f"no style resolved for {lxml.etree.tostring(elem)}")
            return False
        return css_style.is_bold

    @classmethod
    def is_italic(cls, elem):
        """
        finds @class in elem and looks up style in html/head
        """
        if elem is None:
            return False
        css_style = HtmlStyle.lookup_head_style_by_classref(elem)
        if not css_style:
            print(f"no style resolved for {lxml.etree.tostring(elem)}")
            return False
        return css_style.is_italic


class HtmlClass:
    """
    methods to process class *attributes* on HTML elemnts and sync with style
    Initially mainly @classmethod but adding instamces to manage editing
    the @class attribute
    """

    def __init__(self, classstr=None):

        self.classes = set()
        if classstr:
            if type(classstr) is str:
                self.classes.update(classstr.split())
            else:
                raise ValueError(f"can only create HtmlClass from strings, found {type(classstr)} : {classstr}")

# class HtmlClass:

    @classmethod
    def create_from_classed_element(cls, elem):
        """
        get class value from element and ccreate HtmlClass
        :param elem: elements with @class attribute
        :return: HtmlClass element or None
        """
        clazz = HtmlClass.get_class_string_on_element(elem)
        return None if not clazz else HtmlClass(clazz)

    # class HtmlClass:

    @property
    def class_string(self):
        """
        return the class_string (creates from latest self.classes)
        :return: string of alphabeticcally sorted spece-separated classes
        """
        return "" if not self.classes else " ".join(sorted(list(self.classes)))

    def add_class(self, clazz):
        """
        add class to class_string
        :param clazz: class to add (must be non-empty string
        if clazz is
        """
        if clazz and len(clazz.strip()) > 0 and clazz not in self.classes:
            self.classes.add(clazz.strip())

    # class HtmlClass:

    def has_class(self, clazz):
        """
        does class exist in classes
        :param clazz:
        """
        return clazz in self.classes

    # class HtmlClass:

    def replace_class(self, clazz_old, clazz=None):
        """
        remove clazz_old ; if clazz is not None add it as new class
        (if clazz is already present, no-op)
        """
        if clazz_old in self.classes:
            self.remove(clazz_old)
            if clazz:
                self.add_class(clazz)

    # class HtmlClass:

    def remove(self, clazz):
        """
        remove class from string
        :param clazz: class string to remove
        if  not present, no-op
        """
        if clazz in self.classes:
            self.classes.remove(clazz)

    # class HtmlClass:

    @classmethod
    def get_class_string_on_element(cls, elem):
        """
        convenience method to get element style
        :param elem: to get style from
        :return: style or None
        """

        return elem.attrib.get("class") if type(elem) is _Element else None

    # class HtmlClass:

    @classmethod
    def set_class_on_element(cls, elem, value, replace=True):
        """
        convenience method to set class on element
        :param elem:element to set class on
        :param value: html class
        :param replace:if True replace, else add to existing attribute
        """
        if elem is not None and value:
            if not replace:
                old_class = HtmlClass.get_class_string_on_element(elem)
                if old_class:
                    if value not in old_class:
                        old_class += " " + value
            else:
                old_class = value
            elem.attrib["class"] = value

    # class HtmlClass:

    def create_classref(self):
        """
        create classref string (prepend ".")
        """
        return "." + self.class_string

    # class HtmlClass:

    @classmethod
    def remove_dot(self, string):
        """
        remove dot (".") - in html/head/style element
        """
        return string[1:] if string and string[:1] == "." else string


class HtmlTree:
    """builds a tree from a flat set of Html elemnets"""

    # for the section_recs
    CHAP_TOP = "CHAP_TOP"
    CHAP_SECTIONS = "CHAP_SECTIONS"
    CHAP_SUBSECTS = "CHAP_SUBSECTS"

    # Chapter
    TREE_ROOT = "tree_root"
    CLASS = "class"
    PRE_CHAPSEC = "pre_chapsec"

    # sections
    CHAPSEC = "chapsec"
    TOP_DIV = "top_div"

    # XPaths
    ALL_DIV_XPATHS = ".//div"

# class HtmlTree

    @classmethod
    def make_sections_and_output(cls, elem, output_dir, recs_by_section=None):
        """find decimal number for tree
        ThiS is HEAVILY based on IPCC
        currently called in tidy_flow()
        """
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
            if marked_div is not None:
                ld = len(divs) if divs else 0
                logging.warning(f"Cannot find marker [{marker}] found {ld} markers")

        class_dict = {cls.CHAPSEC: cls.PRE_CHAPSEC,
                      cls.TOP_DIV: cls.TREE_ROOT, }
        rec = recs_by_section.get(cls.CHAP_TOP)
        assert rec, f"wanted {cls.CHAP_TOP} rec"
        decimal_divs = cls.get_div_spans_with_decimals(elem,
                                                       is_bold,
                                                       font_size_range=font_size_range,
                                                       section_rec=rec, class_dict=class_dict)
        cls.create_filename_and_output(decimal_divs, output_dir)

    # class HtmlTree

    @classmethod
    def create_filename_and_output(cls, decimal_divs, output_dir,
                                   orig=" !\"#$%&'()*+,/:;<=>?@[\]^`{|}~", rep="_"):
        """
        create filename from section name, replace punct characters
        """
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)

            punct_mask = Util.make_translate_mask_to_char(orig, rep)
            for i, child_div in enumerate(decimal_divs):
                cls.create_filename_remove_punct_and_output(child_div, output_dir, punct_mask)

    # class HtmlTree

    @classmethod
    def create_filename_remove_punct_and_output(cls, child_div, output_dir, punct_mask):
        if HtmlUtil.MARKER in child_div.attrib:
            marker = child_div.attrib[HtmlUtil.MARKER]
            marker = marker.strip().lower()  # name from text content
            marker.translate(punct_mask)
            path = Path(output_dir, f"{marker}.html")
            with open(path, "wb") as f:
                f.write(lxml.etree.tostring(child_div, pretty_print=True))

    # class HtmlTree

    @classmethod
    def get_div_span_starting_with(cls, elem, strg, is_bold=False, font_size_range=None):
        result = None
        xpath = f".//div[span[starts-with(.,'{strg}')]]"
        divs = elem.xpath(xpath)
        if len(divs) == 0:
            logging.warning(f"No divs with {strg}")
            return result, None
        new_divs = []
        for div in divs:
            spans = div.xpath("./span")
            if spans:
                css_style = CSSStyle.create_css_style_from_attribute_of_body_element(spans[0])
                if not (is_bold and css_style.is_bold_name()):
                    continue
                if not (font_size_range and cls.in_range(css_style.font_size, font_size_range)):
                    continue
                new_divs.append(div)
                pass
        divs = new_divs
        # also test font here NYI
        if len(divs) == 0:
            logging.warning(f"cannot find div: len={len(divs)}")
        elif len(divs) > 1:
            logging.warning(f"too many divs: len={len(divs)}")
        else:
            result = divs[0]
            result.attrib["marker"] = strg
        return result, divs

    # class HtmlTree

    @classmethod
    def get_div_spans_with_decimals(cls, elem, is_bold=None, font_size_range=None, class_dict=None, section_rec=None):
        """Matches div/span starting with a decimal index
        d.d or d.d.d
        """
        result = None
        # first add all matching numbered divs to pre_chapsec
        if not class_dict:
            raise ValueError(f"missing class_dict")
        top_div = lxml.etree.SubElement(elem, H_DIV)
        top_div.attrib[cls.CLASS] = class_dict.get(HtmlTree.TOP_DIV)
        pre_chapsec = lxml.etree.SubElement(top_div, H_DIV)
        pre_chapsec.attrib[cls.CLASS] = class_dict.get(HtmlTree.CHAPSEC)
        current_div = pre_chapsec

        # iterate over all divs, only append those with decimal
        divs = elem.xpath(cls.ALL_DIV_XPATHS)
        decimal_count = 0
        texts = []  # just a check at present
        for div in divs:
            spans = div.xpath("./span")
            if not spans:
                # no spans, concatenate with siblings
                if div == current_div:
                    logging.warning("f cannot append div {div} to itself")
                else:
                    try:
                        current_div.append(div)
                    except ValueError as ve:
                        logging.error(f"Error {ve}")
                try:
                    current_div.append(div)
                except Exception as e:
                    logging.error(f"BUG skipped")
                continue
            css_style = CSSStyle.create_css_style_from_attribute_of_body_element(spans[0])  # normally comes first
            # check weight, if none append to siblings
            if not (is_bold and css_style.is_bold_name()):
                current_div.append(div)
                continue
            # check font-size, if none append to siblings
            if not (font_size_range and cls.in_range(css_style.font_size, font_size_range)):
                current_div.append(div)
                continue
            # span content
            text = HtmlUtil.get_text_content(spans[0])
            matched = False
            if section_rec.match(text):
                top_div.append(current_div)
                texts.append(text)
                div.attrib[HtmlUtil.MARKER] = text
                current_div = div
                decimal_count += 1
            else:
                current_div.append(div)
        return top_div

    # class HtmlTree

    @classmethod
    def in_range(cls, num, num_range):
        """is a number in a numeric range"""
        assert num_range or len(num_range) == 2, f"range must have 2 elements"
        assert num_range[0] <= num_range[1], f"font_size_range must be (lower,higher)"
        assert float(num_range[0])
        result = num_range[0] <= num <= num_range[1]
        return result

    # class HtmlTree

    @classmethod
    def get_decimal_sections(cls, html_elem, xpath=None, regex=None):
        """
        gets decimal sections in elems of form 1.2, etc
        :param html_elem: element to search for sections
        :param xpath: sectins may have been labelled with @class or similar
        :param regex: sections may be discoverable by regex+content
        :return: list of sections (may be empty) or None
        It is likely that a combination of xpath and regex will be used as xpath
        may not have regex
        """
        if html_elem is None:
            return None
        sections = []
        if xpath:
            sections = html_elem.xpath(xpath)
        if regex:
            logging.warning(f"regex not yet developed for sections")
        return sections


RECS_BY_SECTION = {
    HtmlTree.CHAP_TOP: IPCC_CHAP_TOP_REC,
    HtmlTree.CHAP_SECTIONS: SECTIONS_DECIMAL_REC,
    HtmlTree.CHAP_SUBSECTS: SUBSECTS_DECIMAL_REC,
}


class HTMLSearcher:
    """
    I think this duplicates some of NodeExtractor.
    """
    """
    methods for finding chunks and strings in HTML elements

    Example text:
    <span>observed increases in the most recent years (Minx et al., 2021; UNEP, 2020a).
    2019 GHG emissions levels were higher compared to 10 and 30 years ago (high confidence): about 12% (6.5 GtCO2eq)
    higher than in 2010 (53±5.7 GtCO2eq) (AR5 reference year) and about 54% (21 GtCO2eq) higher than in 1990
    (38±4.8 GtCO2eq) (Kyoto Protocol reference year and frequent NDC reference)</span>
    """
    """
    """

    # for text search
    DEFAULT_XPATH = "//text()"
    CHUNK_RE = "chunk_re"  # finds text chunks in text
    SPLITTER_RE = "splitter_re"  # splits those chunks (e,g, comma-separated lists
    SUBNODE_RE = "sub_node_re_list"  # matches the components of the split lists
    UNMATCHED = "unmatched"  # adds unmatched nodes
    XPATH = "xpath"

    def __init__(self, xpath_dict=None, dictx=None):
        self.chunk_node_dict = dict()
        self.xpath_dict = dict() if xpath_dict is None else copy.deepcopy(xpath_dict)
        self.chunk_dict = dict()
        self.splitter_dict = dict()
        self.subnode_dict = dict()
        self.dictx = dict() if dictx is None else copy.deepcopy(dictx)

    def search_path_chunk_node(self, html_path):
        assert html_path.exists(), f"{html_path} should exist"
        tree = lxml.etree.parse(str(html_path))

        self.xpaths = self.xpath_dict.get(self.XPATH)
        if not self.xpaths:
            raise ValueError(f"ERROR must give xpath")
        for xpath in self.xpaths:
            try:
                match_elements = tree.xpath(xpath)
            except Exception as e:
                raise ValueError(f"ERROR xpath {xpath} {e}")

        self.element_list = list()
        for xpath in self.xpaths:
            match_elements = tree.xpath(xpath)
            for match_element in match_elements:
                t = type(match_element)
                if t is not _Element:
                    raise ValueError(f"not an element {t} {match_element}")
                self.element_list.append(match_element)

        for element in self.element_list:
            for text in element.xpath("./text()"):
                pass
                # nodestr = self.select_chunks_subchunks_nodes(text)

    def select_chunks_subchunks_nodes(self, text, splitter_re=None, node_re=None):
        # chunk_re, splitter_re, node_re_liat, add_unmatched = False):
        """
        Move to a class and refactor to use dictionary
        NOT YET USED
        :param splitter_re: regex for splitting smaller chunks
        :param node_re: regex to find hypernodes
        """

        chunk_res = self.chunk_dict.get(self.CHUNK_RE)
        splitter_res = self.splitter_dict.get(self.SPLITTER_RE)
        node_res = self.chunk_node_dict.get(self.SUBNODE_RE)

        add_unmatched = self.chunk_node_dict.get(self.UNMATCHED)
        ptr = 0
        while True:
            for chunk_re in chunk_res:
                match = re.search(chunk_re, text[ptr:])
                if not match:
                    break
                ptr += match.span()[1]
                nodestr = match.group(1)

                nodes = re.split(splitter_re, nodestr)
                node_dict = defaultdict(list)
                for node in nodes:
                    m = re.search(node_re, node)
                    if m:
                        node_dict[node_re].append(node)
                    if not m and add_unmatched:
                        node_dict[self.UNMATCHED].append(node)
                for item in node_dict.items():
                    # print(f"item {item}")
                    pass

    def add_xpath(self, title, xpath):
        """
        set xpath for extracting HTML nodes.
        :param title: title of xpath
        :param xpath: acts on current nodeset
        """
        XmlLib.validate_xpath(xpath)
        self.add_item_to_array_dict(self.xpath_dict, title, xpath)

    def validate_xpath(self, xpath):
        """
        crude syntax validation of xpath string.
        tests xpath on a trivial element
        :param xpath:
        """
        tree = lxml.etree.fromstring("<foo/>")
        try:
            tree.xpath(xpath)
        except lxml.etree.XPathEvalError as e:
            logging.error(f"bad XPath {xpath}, {e}")
            raise e

    def add_chunk_re(self, chunk_re):
        """
        add chunk regex for extracting chunks.
        :param chunk_re: acts on current nodeset
        """
        self.add_item_to_array_dict(self.chunk_dict, self.CHUNK_RE, chunk_re)
        self.validate_re(chunk_re)

    def add_splitter_re(self, splitter_re):
        """
        add splitter regex for extracting lists in chunks.
        :param splitter_re: acts on current nodeset
        """
        self.add_item_to_array_dict(self.splitter_dict, self.SPLITTER_RE, splitter_re)
        self.validate_re(splitter_re)

    def add_subnode_key_re(self, name, subnode_re):
        """
        add named subnode regex for parsing list items from splitting
        :param name: name of re in dict
        :param subnode_re: regex to store
        """
        self.add_named_value(name, subnode_re)

    def add_named_value(self, name, subnode_re):
        self.add_item_to_array_dict(self.chunk_dict, name, subnode_re)
        self.validate_re(subnode_re)

    def set_unmatched_flag(self, unmatched):
        """
        set UNMATCHED boolean. If true adds all unmatched values to dict under UNMATCHED
        :param unmatched: acts on current nodeset
        :param match_type: additional debug to name
        """
        self.chunk_dict[self.UNMATCHED] = unmatched

    def validate_re(self, regex):
        """
        :param regex: regex to be validated
        :except: throws Exception for bad regex
        """
        try:
            re.compile(regex)
        except Exception as e:
            logging.error(f"bad regex {regex}")
            raise e

    def add_item_to_array_dict(self, the_dict, key, value):
        if not the_dict.get(key):
            the_dict[key] = []
        the_dict[key].append(value)


class HTMLArgs(AbstractArgs):
    """Parse args to analyze, edit and annotate HTML"""

    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()
        self.dictfile = None
        self.inpath = None
        self.outpath = None
        self.outstem = None
        self.outdir = None
        self.arg_dict = None

    def add_arguments(self):
        if self.parser is None:
            self.parser = argparse.ArgumentParser()
        """adds arguments to a parser or subparser"""
        self.parser.description = 'HTML editing analysing annotation'
        self.parser.add_argument(f"--{ANNOTATE}", action="store_true",
                                 help="annotate HTML file with dictionary")
        self.parser.add_argument(f"--{COLOR}", type=str, nargs=1,
                                 help="colour for annotation")
        self.parser.add_argument(f"--{DICT}", type=str, nargs=1,
                                 help="dictionary for annotation")
        self.parser.add_argument(f"--{INPATH}", type=str, nargs=1,
                                 help="input html file")
        self.parser.add_argument(f"--{OUTPATH}", type=str, nargs=1,
                                 help="output html file")
        self.parser.add_argument(f"--{OUTDIR}", type=str, nargs=1,
                                 help="output directory")
        self.parser.epilog = "==============="

    """python -m py4ami.pyamix HTML --annotate 
     --dict /Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/dict/emissions_abbreviations.xml
     --inpath /Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/fulltext.html
     --outpsth /Users/pm286/projects/semanticClimate/ipcc/ar6/wg3/Chapter02/annotated/fulltext_emissions.html
     --color pink
     """

    # class AmiDictArgs:
    def process_args(self):
        """runs parsed args
        :return:
        """

        if not self.arg_dict:
            logging.warning(f"no arg_dict given, no action")
            return

        self.annotate = self.arg_dict.get(ANNOTATE)
        self.color = self.arg_dict.get(COLOR)
        self.dictfile = self.arg_dict.get(DICT)
        self.inpath = self.arg_dict.get(INPATH)
        self.outdir = self.arg_dict.get(OUTDIR)
        self.outpath = self.arg_dict.get(OUTPATH)

        if self.annotate:
            self.annotate_with_dict()

    # class AmiDictArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[DICT] = None
        return arg_dict

    @property
    def module_stem(self):
        """name of module"""
        return Path(__file__).stem

    def annotate_with_dict(self):
        """uses dictionary to annotate words and phrases in HTML file"""
        from py4ami.ami_dict import AmiDictionary  # horrible

        if not self.dictfile:
            logging.error(f"no dictionary given")
            return
        if not self.inpath:
            logging.error(f"no input file to annotate given")
            return
        if not self.outpath:
            logging.error(f"no output file given")
            return
        if not self.outdir:
            self.outdir = Path(self.outpath).parent
        self.outdir = Path(self.outdir)
        self.outdir.mkdir(exist_ok=True)

        self.ami_dict = AmiDictionary.create_from_xml_file(self.dictfile)
        self.ami_dict.markup_html_from_dictionary(self.inpath, self.outpath, self.color)


class URLCache:
    def __init__(self):
        self.url_dict = dict()

    def read_xml_element_from_github(self, github_url, delay=1):
        """retrieves and parses content of URL. Caches it if found
        returns a deepcopy as elemnt is likely to be edited"""
        html_elem = self.url_dict.get(github_url)
        if html_elem is None:
            try:
                html_elem = XmlLib.read_xml_element_from_github(github_url=github_url)
                time.sleep(delay)
            except Exception as e:
                print(f"cannot read {github_url} because {e}")
                return None
            self.url_dict[github_url] = html_elem
        else:
            # print(f" found in cache!")
            pass
        return copy.deepcopy(html_elem)


ID = "id"
OBJECT ="object"
STARTEND = "start_end"

class FloatBoundaryDict:

    def __init__(self, html_elem, outdir=None):
        self.float_boundary_dict = defaultdict(list)
        self.html_elem = html_elem
        self.outdir = outdir

    def add_object(self, float_boundary):
        key = float_boundary.key
        self.float_boundary_dict[key].append(float_boundary)

    def add_float_boundaries(self, float_boundaries):
        for float_boundary in float_boundaries:
            self.add_object(float_boundary)

    def extract_contents_of_bracketed_boundaries_and_write(self):
        for fb_list in self.float_boundary_dict.values():
            if len(fb_list) == 2:
                # print(f"FB {fb_list} {fb_list[0].div_id} {fb_list[1].div_id}")
                new_div = self.delete_between(fb_list[0].div_id, fb_list[1].div_id)
                float_name = fb_list[0].key
                new_div.attrib["name"] = float_name
                new_html_elem = HtmlLib.create_new_html_with_old_styles(self.html_elem)
                HtmlLib.get_body(new_html_elem).append(new_div)
                if self.outdir:
                    Path(self.outdir).mkdir(exist_ok=True, parents=False)
                    file_stem = float_name.lower().replace("\s*", "")
                    XmlLib.write_xml(new_html_elem, Path(self.outdir, file_stem + ".html"))

    def delete_between(self, div_id0, div_id1):
        elem0 = self.html_elem.xpath(f".//div[@id='{div_id0}']")[0]
        elem1 = self.html_elem.xpath(f".//div[@id='{div_id1}']")[0]
        following = elem0.xpath("following::*")
        new_div = lxml.etree.Element("div")
        new_div.attrib["id"] = div_id0
        for follow in following:
            id_ = follow.attrib['id']
            new_div.append(follow)
            # follow.getparent().remove(follow)
            if id_ == div_id1:
                print("EXIT")
                break
        return new_div



class FloatBoundary:
    """
    Holds
    """
    IPCC_BOUNDARY = "\[?" \
            f"(?P<{STARTEND}>START|END)\s*" \
            f"(?P<{OBJECT}>.*BOX|FIGURE|TABLE)\s*" \
            f"(?P<{ID}>(?:(?:[A-Z0-9]+|\d+)?(?:\.\d+)*))\s*(?:HERE)\]?"

    # [START CROSS-SECTION BOX.1 HERE]

    def __init__(self):
        self.group_dict = dict()
        self.start = None
        self.end = None
        self.div_id = None

    def __str__(self):
        return self.group_dict.get(STARTEND) + ";" +  self.group_dict.get(OBJECT) + ";" +  self.group_dict.get(ID)

    def __repr__(self):
        return self.__str__()

    def add(self, name, value):
        self.group_dict[name] = value

    @property
    def key(self):
        return str(self.group_dict[OBJECT]) + str(self.group_dict[ID])

    @property
    def start_end(self):
        return self.group_dict[STARTEND]

    @classmethod
    def extract_floats_and_boundaries(cls, html_elem, package, outdir=None):
        regex = FloatBoundary.IPCC_BOUNDARY
        float_boundaries = FloatExtractor().extract_float_boundaries(html_elem, regex)
        float_boundary_dict = FloatBoundaryDict(html_elem, outdir=outdir)
        float_boundary_dict.add_float_boundaries(float_boundaries)
        float_boundary_dict.extract_contents_of_bracketed_boundaries_and_write()
        return html_elem


class FloatExtractor:
    """extracts floats (boxes, figures, etc.) using start/end regexes
    """

    def __init__(self, regex=None):
        self.regex = regex

    def extract_float_boundaries(self, html_elem, regex_str):
        float_boundaries = []
        regex = re.compile(regex_str)
        # print(f" regex {regex}")
        divs = html_elem.xpath(".//div")
        for div in divs:
            spans = div.xpath("./span")
            for span in spans:
                match = re.search(regex, span.text)
                if match:
                    float_boundary = FloatBoundary()
                    float_boundary.div_id = div.attrib["id"]
                    for field in [STARTEND, OBJECT, ID]:
                        float_boundary.add(field, match.group(field))
                    float_boundaries.append(float_boundary)
        return float_boundaries



class CSSStyle:
    """
    common subset of CSS styles/commands
    """
    # all are lowercase
    BOLD = "bold"
    BORDER = "border"
    BOTTOM = "bottom"
    COLOR = "color"
    DOT_B = ".B"
    FILL = "fill"
    STROKE = "stroke"
    FONT_FAMILY = "font-family"
    FONT_SIZE = "font-size"
    FONT_STYLE = "font-style"
    FONT_STRETCHED = "font-stretched"
    FONT_WEIGHT = "font-weight"
    HEIGHT = "height"
    ITALIC = "italic"
    LEFT = "left"
    LIGHT = "light"
    NORMAL = "normal"
    OPACITY = "opacity"
    POSITION = "position"
    PX = "px"
    STYLE = "style"
    TOP = "top"
    WIDTH = "width"

    WEIGHT_RE = "([-.]?Bold|[.][Bb]$)"
    STYLE_RE = "([-.]?Ital(:?ic)|[-.]?Oblique|[.][Ii]$)"

    TEXT_STYLE_COMPONENTS = [FONT_STYLE, FONT_WEIGHT, FONT_FAMILY, FONT_SIZE, COLOR, OPACITY]

    def __init__(self):
        self.name_value_dict = dict()

    def __str__(self):
        s = ""
        for k, v in self.name_value_dict.items():
            s += f"{k}:{v}; "
        s = s.strip()
        return s

    def __repr__(self):
        return f"{self.name_value_dict}"

#    class CSSStyle:

    @classmethod
    def create_css_style_from_attribute_of_body_element(cls, elem):
        """create CSSStyle object from elem
        :param elem:
        """
        if elem is None:
            return None
        assert type(elem) is _Element, f"found {type(elem)}"
        css_style = CSSStyle()
        style_attval = elem.get(CSSStyle.STYLE)
        css_style.name_value_dict = cls.create_dict_from_name_value_array_string(style_attval)
        return css_style

    #    class CSSStyle:

    @classmethod
    def create_dict_from_name_value_array_string(cls, style_str, remove_curly=True):
        """
        assumes string of type "a: b; c: d;" optionally enclosed in {...}
        :param style_str: 
        """
        re_str = "(?P<pre>.*){(?P<curly>.*)}(?P<post>.*)"
        curly_re = re.compile(re_str)
        name_value_dict = dict()
        if type(style_str) is CSSStyle:
            style_str = style_str.get_css_value(style_str)
        if style_str:
            if remove_curly:
                match = curly_re.match(style_str)
                if match:
                    style_str = match.group("curly")
            name_value_dict = cls.create_name_value_dict(style_str)
        return name_value_dict

    @classmethod
    def create_name_value_dict(cls, style_str):
        name_value_dict = dict()
        style_str = style_str.strip()
        styles = style_str.split(";")
        for style in styles:
            style = style.strip()
            if len(style) > 0:
                ss = style.split(":")
                if len(ss) != 2:
                    raise KeyError(f"bad style {style} in CSS: {style_str}")
                name = ss[0].strip()
                if name in name_value_dict:
                    raise KeyError(f"{name} duplicated in CSS: {style_str}")
                name_value_dict[name] = ss[1].strip()
        return name_value_dict

    #    class CSSStyle:

    @classmethod
    def create_css_style_from_css_string(cls, css_string, remove_prefix=True):
        """creates CSSStyle object from CSS string"""
        css_style = None
        if css_string:
            css_style = CSSStyle()
            css_style.name_value_dict = cls.create_dict_from_name_value_array_string(css_string)
            if remove_prefix:
                font_family = css_style.name_value_dict.get(CSSStyle.FONT_FAMILY)
                font_family1 = AmiFont.trim_pdf_prefix(font_family)
                if font_family1 and font_family1 != font_family:
                    css_style.name_value_dict[CSSStyle.FONT_FAMILY] = font_family1
        return css_style

    def __eq__(self, other):
        """
        tests whether self and other have equal dictionaries
        """
        if type(other) is CSSStyle:
            return self.name_value_dict == other.name_value_dict
        return False


    def set_attribute(self, property, value):
        """
        sets name-value pair in CSSStyle
        ignores empty values or None
        """
        if value and len(str(value)) > 0:
            self.name_value_dict[property] = value

    def set_family(self, family):
        if family:
            self.set_attribute(CSSStyle.FONT_FAMILY, family)

    def set_font_weight(self, weight):
        weight = weight.lower()
        if weight:
            if weight == CSSStyle.NORMAL:
                self.set_attribute(CSSStyle.FONT_WEIGHT, CSSStyle.NORMAL)
            if weight == CSSStyle.BOLD:
                self.set_attribute(CSSStyle.FONT_WEIGHT, CSSStyle.BOLD)
            if weight == CSSStyle.LIGHT:
                self.set_attribute(CSSStyle.FONT_WEIGHT, CSSStyle.LIGHT)

    def set_font_style(self, style):
        if style:
            if style.lower() == CSSStyle.NORMAL.lower():
                self.set_attribute(CSSStyle.FONT_STYLE, CSSStyle.NORMAL)
            if style.lower() == CSSStyle.ITALIC.lower():
                self.set_attribute(CSSStyle.FONT_STYLE, CSSStyle.ITALIC)

    def get_attribute(self, property):
        """
        gets value for name in CSSStyle
        ignores empty values or None
        """
        return self.name_value_dict and self.name_value_dict.get(property)

    #    class CSSStyle:

    def get_font_style_attributes(self):
        """
        gets tuple of 4 font attributes (size, nonstroke, stroke, fontname)
        """

        if self.name_value_dict is None:
            return (None, None, None, None, None)
        return (
            # self.name_value_dict.get(CSSStyle.WIDTH),
            self.get_attribute(CSSStyle.FONT_SIZE),
            self.get_attribute(CSSStyle.FILL),
            self.get_attribute(CSSStyle.STROKE),
            self.get_attribute(CSSStyle.FONT_FAMILY)
        )

    #    class CSSStyle:

    def remove(self, name):
        """
        removes named item from CSSStyle
        """
        if type(name) is list:
            for n in name:
                self.remove(n)
        elif name in self.name_value_dict:
            self.name_value_dict.pop(name, None)

    def apply_to(self, elem):
        """

        """
        css_str = self.get_css_value()
        elem.attrib[CSSStyle.STYLE] = css_str

    #    class CSSStyle:

    def get_css_value(self, wrap_with_curly=False):
        """
        generates css string without quoted names and values
        :param wrap_with_curly: if true enclose string in "{" ... "}"
        """
        s = ""
        for key in self.name_value_dict:
            val = self.name_value_dict[key]
            s += key + ": " + str(val) + "; "
        s = s.strip()
        return "{" + s + "}" if wrap_with_curly else s

    def attval(self, name):
        return self.name_value_dict.get(name) if self.name_value_dict else None

    #    class CSSStyle:

    @property
    def font_family(self):
        return self.attval(CSSStyle.FONT_FAMILY)

    @property
    def top(self):
        return self.get_numeric_attval(CSSStyle.TOP)

    @property
    def font_size(self):
        return self.get_numeric_attval(CSSStyle.FONT_SIZE)

    @property
    def is_bold(self):
        weight = self.attval(CSSStyle.FONT_WEIGHT)
        return weight is not None and weight.lower() == CSSStyle.BOLD.lower()

    @property
    def is_italic(self):
        style = self.attval(CSSStyle.FONT_STYLE)
        return style is not None and style.lower() == CSSStyle.ITALIC.lower()

    @property
    def bottom(self):
        return self.get_numeric_attval(CSSStyle.BOTTOM)

    @property
    def left(self):
        return self.get_numeric_attval(CSSStyle.LEFT)

    #    class CSSStyle:

    @property
    def width(self):
        return self.get_numeric_attval(CSSStyle.WIDTH)

    @property
    def height(self):
        return self.get_numeric_attval(CSSStyle.HEIGHT)

    #    class CSSStyle:

    @classmethod
    def add_name_value(cls, elem, css_name, css_value):
        """updates style on element
        :param css_name: name of property
        :param css_value: value of property
        """
        css_style = cls.create_css_style_from_attribute_of_body_element(elem)
        css_style.name_value_dict[css_name] = css_value
        css_style.apply_to(elem)

    def get_numeric_attval(self, name, decimal=1):
        """
        gets float value, rounded to demical plabes
        :param name: of parameter
        :param round: number of decimal places (default 2)
        """
        value = self.attval(name)
        if not value:
            return None
        if type(value) is str:
            value = value[:-2] if value.endswith(CSSStyle.PX) else value
            value = float(value)

        fs = round(float(value), decimal)
        return fs

    #    class CSSStyle:

    def is_bold_name(self):
        """Heuristic using font-name
        :return: True if name contains "Bold" or ".B" or .."""
        fontname = self.font_family
        result = (self.BOLD in fontname) or (fontname.endswith(self.DOT_B)) if fontname else False
        return result

    #    class CSSStyle:

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
                logging.warning(f"Cannot parse as condition {condition}")
            else:
                lhs = ss[0].strip()
                rhs = ss[2].strip()

                if lhs not in self.name_value_dict:
                    return False
                value1 = self.name_value_dict.get(lhs)
                if not value1:
                    logging.warning(f"{lhs} not in style attribute {self.name_value_dict}")
                    return False
                if value1.endswith(CSSStyle.PX):
                    value1 = value1[:-2]
                try:
                    value1 = float(value1)
                except Exception:
                    logging.warning(f"not a number {value1}")
                    return False

                if rhs.endswith(CSSStyle.PX):
                    rhs = rhs[:-2]
                try:
                    value2 = float(rhs)
                except Exception:
                    logging.warning(f"not a number {rhs}")
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
                    pass
        return result

    #    class CSSStyle:

    @classmethod
    def cmyk_to_rgb(cls, c, m, y, k):

        rgb_scale = 255
        # cmyk_scale = 100
        cmyk_scale = 1.0
        r = rgb_scale * (1.0 - (c + k) / float(cmyk_scale))
        g = rgb_scale * (1.0 - (m + k) / float(cmyk_scale))
        b = rgb_scale * (1.0 - (y + k) / float(cmyk_scale))

        return r, g, b

    #    class CSSStyle:

    @classmethod
    def cmky_to_rgb(cls, c, m, k, y):
        return cls.cmyk_to_rgb(c, m, y, k)

    def extract_bold_italic_from_font_family(
            self,
            overwrite_bold=False,
            overwrite_style=False,
            overwrite_family=True,
            style_regex=STYLE_RE,
            weight_regex=WEIGHT_RE):
        """
        heuristics to find bold and italic in font names and try to normalise
        e.g.
        font-family: TimesNewRomanPS-BoldMT; => font-family: TimesNewRomanPSMT; font_weight: bold
        font-family: TimesNewRomanPS-ItalicMT; => font-family: TimesNewRomanPSMT; font_style: italic
        the overwrite_* determine whetehr existing components will be overwritten
        :param overwrite_bold: create font_weight:bold regardless of previous weight
        :param overwrite_style: create font_style:bold regardless of previous style
        :param overwrite_family: edit font-family to remove style/weight info (hacky)
        :param style_regex=

        """
        family = self.font_family
        if not family:
            return
        family_style, style = self.match_weight_style(family, style_regex, value="I", mark="SS")
        family_weight, weight = self.match_weight_style(family, weight_regex, value="B", mark="WW")
        # print(f"family: {family}; style: {style}; weight: {weight};")
        if family_weight and overwrite_family:
            self.set_family(family_weight)
        if weight and overwrite_bold:
            self.set_font_weight(weight)
        if style and overwrite_style:
            self.set_font_style(style)
        # if style and overwrite_stretched:
        #     self.set_font_stretched(style)
        # print(f"new style {self}")


    #    class CSSStyle:

    def match_weight_style(self, family, weight_regex, value=None, mark=None):
        weight_rec = re.compile(weight_regex) if weight_regex else None
        match = weight_rec.search(family)
        if match:
            value = family[match.start():match.end()]
            value = value.replace("-", "").replace(".", "")
            family = family[:match.start()] + family[match.end():]
        else:
            value = None
        return family, value

    #    class CSSStyle:

    def create_bbox(self):
        """
        create bounding box from left, width, top, height
        :return: None if any attributes missing
        """
        bbox = None
        if self.top is not None and self.height is not None and self.left is not None and self.width is not None:
            bbox = BBox(xy_ranges=[[self.left, self.left + self.width], [self.top, self.top + self.height]])
        return bbox

    #    class CSSStyle:

    def extract_substyles(self, css_names):
        """
        Create 2 new CSSSstyles , the first with names in "styles" and the second the rest.
            if None, retruns None,None
        :param css_names: list of CSS names (e.g. "font-family"). If na name not found, no action
        :return 2-tuple of 1) CSSStyle object with extracted names 2) CSSStyle of the remainder;
            either/both may be empty CSSStyle.
        """
        if not self.name_value_dict:
            raise ValueError(f"name_value_dict is None")
        if css_names is None:
            return None, None
        css_retained = copy.deepcopy(self)
        css_found = CSSStyle()

        keys = css_retained.name_value_dict.keys()
        for name in css_names:
            if name in css_retained.name_value_dict:
                value = css_retained.name_value_dict.pop(name)
                if value:  # transfer item over
                    css_found.name_value_dict[name] = value
        return (css_found, css_retained)

    #    class CSSStyle:

    def create_html_style_element(self, html_class):
        """
        Creates string for HTML style
        """
        DOT = "."
        s = DOT + html_class + " " + self.get_css_value(wrap_with_curly=True)
        elem = lxml.etree.Element(CSSStyle.STYLE)
        elem.text = s
        return elem

    #    class CSSStyle:

    def extract_text_styles(self):
        """
        extract text components from style (font-*, color, etc) into new style, returning tuple of
        new style and style from remaining components
        """
        (extracted_style, retained) = font_style, rest_style = self.extract_substyles(
            CSSStyle.TEXT_STYLE_COMPONENTS
        )
        return (extracted_style, retained)

    #    class CSSStyle:

    def extract_text_styles_into_class(self, class_name, old_classstr=""):
        """
        extracts text class name-value into new CSSStyle, and creates updated class_string
        Example:
            element has style attribute with several text components (e.g. font-weight, font-size)
            This creates a new <style> Element (extracted) with just these components
                and puts the unextracted style componeents into new style space-separated string (remainned)
            It uses the class_name to update the old_classstr string
                e.g. class_name="s1" and old_classstr="foo bar" => "foo bar s1"
        :param class_name: name oif new class (author must ensure uniqueness)
        :param old_classstr: old classname (defaults to "")
        :return: 3-tuple of (extracted_style_element, retained_style_string, new classs_string)
        """
        extracted_style, retained_style = self.extract_text_styles()

        if not extracted_style:
            raise ValueError("extracted style is None")
        extracted_style1 = CSSStyle.extract_bold_italic_from_font_family_for_style(extracted_style) if extracted_style else None
        extracted_html_style_element = extracted_style1.create_html_style_element(class_name) if extracted_style1 is not None else None

        retained_style_attval = retained_style.get_css_value() if retained_style else None
        html_class_val = CSSStyle.create_html_class_val(class_name, old_class_val=old_classstr)
        return extracted_html_style_element, retained_style_attval, html_class_val

    #    class CSSStyle:

    @classmethod
    def create_html_class_val(cls, new_class, old_class_val=None):
        """
        creates or edits a class string to accept a new value
        no-op if new_class is already in old_class_val
        e.g. None + "foo" => "foo"
        "foo" + "bar plugh" => "bar plugh foo"
        "foo" + "bar foo plugh" => "bar foo plugh"
        :param new_class: class to add
        :param old_class_val: space-separated list of existing classes
        :return: new class string
        """
        old_classes = [] if not old_class_val else old_class_val.split()
        if new_class not in old_classes:
            old_classes.append(new_class)
        return Util.create_string_separated_list(old_classes)

    #    class CSSStyle:

    @classmethod
    def create_style_dict_from_styles(cls, style_elems=None, validate=True):
        """
        convert list of CSSStyles (as HTML strings) to dict
        if duplicate stylerefs raise Exception if validate else take first
        Typical style:
        <style ...>.s0 {font-size: 14.px;}</style>
        :param style_elems: list of lxml _Elements
        :param validate: check whether CSS value is conformant or duplicate style_refs
        :return: dict of form ref: style
        :except: If element has wrong syntax; if css fierld is malfotmed; if ref is duplicated
        """
        css_re = re.compile("\s*(\..*)\s+{(.*)}\s*")
        if style_elems is None:
            styles = []
        style_dict = dict()
        for style_elem in style_elems:
            style_text = style_elem.text.strip()
            match = css_re.match(style_text)
            if not match:
                raise ValueError(f"BAD head_style {style_text}")
            ref = match.group(1)
            css_string = match.group(2)
            if css_string == "":
                # this occurs when the style attributes are positional
                continue
            if validate:
                css_style = CSSStyle.create_css_style_from_css_string(css_string)
                if css_style is None:
                    raise ValueError(f"bad CSSStyle {css_style}")
            if ref in style_dict:
                if validate:
                    raise ValueError(f"duplicate style ref {style_text}")
            else:
                style_dict[ref] = css_string
        return style_dict

    #    class CSSStyle:

    @classmethod
    def extract_styles_from_html_string(cls, html_str):
        """
        extract styles from head of html file
        :param html_str: string of form <html><head><style ...></style><style ...></style></head> ... </html>
        :return: list of _Elements (<style...> ...</style>) or []
        """
        return cls.extract_styles_from_html_head_element(lxml.etree.fromstring(html_str))

    #    class CSSStyle:

    @classmethod
    def extract_styles_from_html_head_element(cls, html_elem):
        """
        extract styles from head of html file
        :param html_elem: element of form <html><head><style ...></style><style ...></style></head> ... </html>
        :return: list of _Elements (<style...> ...</style>) or []
        """
        return [] if html_elem is None else html_elem.xpath(STYLE_XPATH)

    @classmethod
    def create_css_style_from_html_head_style_elem(cls, style_elem):
        """
        extracts CSSStyle elemnt from HTML <style>.foo {a:b; c:d;} element
        :param style_elem:
        :return: tuple(symbol ref, new CSSStyle)
        """
        style_re = re.compile("\s*([^\s]*)\s+{(.*)}\s*")
        symbol_ref = None
        css_style_obj = None
        if type(style_elem) is _Element:
            text = XmlLib.get_text(style_elem)
            match = style_re.match(text)
            if match:
                symbol_ref = match.group(1)
                css_style_obj = CSSStyle.create_css_style_from_css_string(match.group(2))
        return symbol_ref, css_style_obj

    @classmethod
    def replace_css_style_name_values_with_normalized_font(cls, style_elem):
        """
        if style_elem contains a font in the CSS values, normalizes it if possible
        (e.g. font-family: ArialBold; => font-family:Arial; font-weight: bold;
        edits the style_elem
        :param style_elem: element to be edited (NOT copied)
        """
        symbol_ref, new_cssstyle = AmiFont.create_font_edited_style_from_css_style_object(style_elem)
        if new_cssstyle is not None:
            style_elem.text = f"{symbol_ref} {{{new_cssstyle}}}"

    @classmethod
    def normalize_styles_in_fonts_in_html_head(cls, html_elem):
        """
        normalizes all fonts to expose font weights and styles
        :param html_elem: HTML (root) element (html/head/style*)
        """
        style_elems = CSSStyle.extract_styles_from_html_head_element(html_elem)
        for style_elem in style_elems:
            CSSStyle.replace_css_style_name_values_with_normalized_font(style_elem)

    @property
    def short_style(self):
        short_style = self.font_family.lower()[:3]
        short_style += str(self.font_size).replace(".", "_")
        if self.is_bold:
            short_style += "b"
        if self.is_italic:
            short_style += "i"
        return short_style

    def get_font_attributes(self):
        """
        sets 4 font attributes (width, size, nonstroke, stroke, fontname
        """

        if self.name_value_dict is None:
            return (None, None, None, None, None)
        return (
            # self.name_value_dict.get(CSSStyle.WIDTH),
            self.get_attribute(CSSStyle.FONT_SIZE),
            self.get_attribute(CSSStyle.FILL),
            self.get_attribute(CSSStyle.STROKE),
            self.get_attribute(CSSStyle.FONT_FAMILY)
        )

    @classmethod
    def get_coords(cls, elem):
        """
        :return: x0, x1, y0, y1
        """
        csss = cls.create_css_style_from_attribute_of_body_element(elem)
        x0 = csss.get_numeric_attval("x0")
        x1 = csss.get_numeric_attval("x1")
        y0 = csss.get_numeric_attval("y0")
        y1 = csss.get_numeric_attval("y1")
        return (x0, y0, x1, y1)

    @classmethod
    def get_x0(cls, elem):
        return cls.get_coords(elem)[0]

    @classmethod
    def get_y0(cls, elem):
        return cls.get_coords(elem)[1]

    @classmethod
    def get_x1(cls, elem):
        return cls.get_coords(elem)[2]

    @classmethod
    def get_y1(cls, elem):
        return cls.get_coords(elem)[3]

    @classmethod
    def extract_coords_and_font_properties(cls, span):
        csss = CSSStyle.create_css_style_from_attribute_of_body_element(span)
        font_size = csss.get_numeric_attval(CSSStyle.FONT_SIZE)
        y0 = csss.get_numeric_attval("y0")
        y1 = csss.get_numeric_attval("y1")
        x1 = csss.get_numeric_attval("x1")
        return font_size, y0, y1

    @classmethod
    def extract_bold_italic_from_font_family_for_styles(cls, styles):
        """
        :styles: list of CSSStyle objects to normalize

        """
        extracted = []
        for style in styles:
            if style:
                extracted.append(cls.extract_bold_italic_from_font_family_for_style(style))
        return extracted

    @classmethod
    def extract_bold_italic_from_font_family_for_style(cls, style_s):
        if not style_s:
            raise ValueError("style_s is None")
        css_style = CSSStyle.create_css_style_from_css_string(str(style_s))
        if css_style:
            css_style.extract_bold_italic_from_font_family(
                overwrite_family=True, overwrite_bold=True, overwrite_style=True)
        return css_style


class CSSConverter:
    """
    turns CCS styles into html classes
    """

    def __init__(self):
        pass

    def read_html_element(self, html_elem):
        """
        reads and converts html element.
        adds <html> as root if not present
        """
        self.html_elem = html_elem
        self.html_elem = HtmlTidy.ensure_html_head_body(self.html_elem)
        return self.html_elem

class FontProperty(Enum):
    """
    ArialNarrow
    ArialNarrow-Bold
    Calibri
    FrutigerLTPro-BlackCn
    FrutigerLTPro-BoldCn
    FrutigerLTPro-BoldCnIta
    FrutigerLTPro-Condensed
    FrutigerLTPro-CondensedIta
    FrutigerLTPro-Light
    FrutigerLTPro-LightCn
    FrutigerLTPro-LightCnIta
    FrutigerLTPro-Roman
    """
    #
    NORMAL = ""

    NARROW = "narrow"
    WIDE = "wide"

    LIGHT = "light"
    BOLD = "bold"

    ITALIC = "italic"

    SANS = "sans"
    SERIF = "serif"
    SYMBOL = "symbol"
    MONOSPACE = "sonospace"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

# strips prefix off font-names
RE_PREF = re.compile("[A-Z]{6}\+(?P<name>[^\s]+)\s*")
class AmiFont:
    """
    empirical normalization of fonts. Tries to convert all to the
    base
    font-family: serif/sans-serif/monospace
    font-stretch: (condensed/normal/expanded)
    forn-weight: normal/bold
    font-style: normal/italic
    """


    # empirical conversions; will need to be updated frequently
    conversion_dict = {
        "Arial": FontProperty.SANS,
        "Calibri": FontProperty.SANS,
        "Frutiger": FontProperty.SANS,
        "Helvetica": FontProperty.SANS,

        "Times": FontProperty.SERIF,

        "Courier": FontProperty.MONOSPACE,

        "Symbol": FontProperty.SYMBOL,
    }

    cond_regex = re.compile("(.*)(Condensed|Cn|Narrow)(.*)")
    wide_regex = re.compile("(.*)(Wide)(.*)")

    light_regex = re.compile("(.*)(Light|Thin)(.*)")
    bold_regex = re.compile("(.*)(Bold|Heavyweight|Black)(.*)")

    style_regex = re.compile("(.*)(Italic|Ita|Oblique)(.*)")

#    class AmiFont:

    def __init__(self):
        self.name = None
        self.family = None
        self.weight = str(FontProperty.NORMAL)
        self.style = str(FontProperty.NORMAL)
        self.stretched = str(FontProperty.NORMAL)
        self.font = str(FontProperty.SANS)

    #    class AmiFont:

    def __str__(self):
        s = f"name:{self.name};family:{self.family};weight:{self.weight};style:{self.style};stretched:{self.stretched};font:{self.font}"
        return s

    @classmethod
    def extract_name_weight_style_stretched_as_font(cls, name0):

        font = AmiFont()
        name = AmiFont.trim_pdf_prefix(name0)

        while True:
            name, match = cls.extract_enumerated_styles(font, name)
            if not match:
                break

        name = name.replace("-","")

        font.family = name
        font.name = name0
        return font

    @classmethod
    def extract_enumerated_styles(cls, font, name):

        name, match = cls.match_font_property(name, AmiFont.cond_regex)
        if match:
            font.stretched = FontProperty.NARROW
            return name, match
        name, match = cls.match_font_property(name, AmiFont.wide_regex)
        if match:
            font.stretched = FontProperty.WIDE
            return name, match
        name, match = cls.match_font_property(name, AmiFont.light_regex)
        if match:
            font.weight = FontProperty.LIGHT
            return name, match
        name, match = cls.match_font_property(name, AmiFont.bold_regex)
        if match:
            font.weight = FontProperty.BOLD
            return name, match

        name, match = cls.match_font_property(name, AmiFont.style_regex)
        if match:
            font.style = FontProperty.ITALIC
            return name, match

        return name, None

    #    class AmiFont:

    """
    Bold Fonts: 1. Arial
    Calibri
    Century Gothic
     Bold 4. 
     Franklin Gothic 
     Bold 5. 
     Futura Bold 6. 
     Gill Sans Bold 7. 
    Helvetica Bold 8. 
    Impact Bold 9.
    Lucida Sans Bold 10. 
    Myriad Pro Bold 11. Open Sans Bold 12. Palatino Bold 13. Rockwell Bold 14. 
    Segoe UI Bold 15. Times New Roman Bold 16. Univers Bold 17. Verdana Bold 18. Avenir Bold 19. Baskerville Bold 20. Clarendon Bold 21. C
    opperplate Bold 22. Didot Bold 23. Eurostile Bold 24. Frutiger Bold 25. Garamond Bold 26. Georgia Bold 27. Gotham Bold 28. 
    Hoefler Text Bold 29. ITC Avant Garde Gothic Bold 30. ITC Franklin Gothic Bold 31. ITC Lubalin Graph Bold 32. 
    ITC Officina Sans Bold 33. ITC Stone Sans Bold 34. Minion Pro Bold 35. Museo Sans Bold 36. Neutraface Bold 37. 
    Optima Bold 38. Proxima Nova Bold 39. Roboto Bold 40. Sabon Bold 41. Trade Gothic Bold 42. 
    Trebuchet MS Bold 43. 
    Ubuntu Bold 44. 
    VAG Rounded Bold 45. 
    Whitney Bold 46. 
    Xits Bold 47. 
    Yanone Kaffeesatz Bold 48. 
    Zilla Slab
    Zona
    Zurich 
    """

    #    class AmiFont:

    @classmethod
    def match_font_property(cls, name, regex):
        match = regex.match(name)
        if match:
            name = match.group(1) + match.group(3) # chop out match
        return name, match

    @classmethod
    def convert_common_fonts(cls):
        pass

    #    class AmiFont:

    @classmethod
    def create_font_edited_style_from_head_style(cls, style_elem):
        """
        empirically create standard fonts and attributes from font names
        :param css_style: CSSStyle Object or HTML head/style with unknown font-family
        :return: tuple (symbol_ref, new css_style object with standard font and maybe new weight or style)
        """
        if not type(style_elem) is _Element:
            return None, None
        symbol_ref, css_style = CSSStyle.create_css_style_from_html_head_style_elem(style_elem)
        if css_style is not None:
            font_family = css_style.font_family
            ami_font = AmiFont.extract_name_weight_style_stretched_as_font(font_family)
            new_css_style = CSSStyle()
            for item in css_style.name_value_dict:
                new_css_style.name_value_dict[item[0]] = item[1]
            new_css_style.set_attribute(FONT_FAMILY, ami_font.family)
            new_css_style.set_attribute(FONT_WEIGHT, ami_font.weight)
            new_css_style.set_attribute(FONT_STYLE, ami_font.style)
            new_css_style.set_attribute(FONT_STRETCHED, ami_font.stretched)
        return symbol_ref, new_css_style

    @classmethod
    def create_font_edited_style_from_css_style_object(cls, css_style):
        """
        empirically create standard fonts and attributes from font names
        :param css_style: CSSStyle Object or HTML head/style with unknown font-family
        :return: tuple (symbol_ref, new css_style object with standard font and maybe new weight or style)
        """

        if css_style is None:
            return None
        if type(css_style) is lxml.etree._Element:
            print (f"element {lxml.etree.tostring(css_style)}")
        if type(css_style) is str:
            css_style = CSSStyle.create_css_style_from_css_string(css_style)
        if css_style is None:
            return None
        assert type(css_style) is CSSStyle, f"found {type(css_style)}"
        if not css_style.font_family:
            return css_style
        ami_font = AmiFont.extract_name_weight_style_stretched_as_font(css_style.font_family)
        new_css_style = CSSStyle()
        for item in css_style.name_value_dict.items():
            new_css_style.name_value_dict[item[0]] = item[1]
        new_css_style.set_attribute(FONT_NAME, str(ami_font.name))
        new_css_style.set_attribute(FONT_FONT, str(ami_font.font))
        new_css_style.set_attribute(FONT_FAMILY, str(ami_font.family))
        new_css_style.set_attribute(FONT_WEIGHT, str(ami_font.weight).lower())
        new_css_style.set_attribute(FONT_STYLE, str(ami_font.style).lower())
        new_css_style.set_attribute(FONT_STRETCHED, str(ami_font.stretched).lower())
        return new_css_style

    #    class AmiFont:

    @property
    def is_bold(self):
        return str(FontProperty.BOLD) == self.weight

    @property
    def is_italic(self):
        return str(FontProperty.ITALIC) == self.style

    @classmethod
    def trim_pdf_prefix(cls, name):
        """removes the ABCDEF+ prefix from font-name
        This prefix serves no useful purpose for text analysis and is discarded"""
        if name:
            match = RE_PREF.match(name)
            if match:
                name = match.group("name")
        return name


class SectionHierarchy:
    """
    builds and queries hierarchical sections
    """

    ID = "id"
    CLASS = 'class'
    DOT = "."
    MISSING = "missing"
    SECT = "sect"

    def __init__(self):
        pass

    def add_sections(self, decimal_sections, top=None, poplist=None):
        if not poplist:
            poplist = []
        sections_by_level = self.create_sections_by_level(decimal_sections)
        parent_dict = self.create_parent_dict(sections_by_level)
        for pop in poplist:
            try:
                parent_dict.pop(pop)  # remove non-numeric item
            except:
                print("Cannot pop {pop}")

        root = Element(self.SECT)
        root.attrib[self.ID] = "4"
        for sect_id in parent_dict.keys():
            self.ensure_element(root, sect_id, parent_dict)

    def create_parent_dict(self, sections_by_level):
        parent_dict = dict()
        for level in sections_by_level.keys():
            sect_ids = self.add_parents(level, sections_by_level, parent_dict)
        return parent_dict

    def create_sections_by_level(self, decimal_sections):
        sections_by_level = defaultdict(list)
        for section in decimal_sections:
            level = section.attrib.get(self.CLASS).split()[1]
            sections_by_level[level].append(section.text)
        return sections_by_level

    def add_parents(self, level, multidict, parent_dict):
        level_sects = multidict[level]
        for level_sect in level_sects:
            parent = self.get_parent(level_sect)
            parent_dict[level_sect] = parent

    def get_parent(self, level_sect):
        bits = level_sect.split(".")
        parent = None if len(bits) == 1 else self.DOT.join(bits[:-1])
        return parent

    def ensure_element(self, root, sect_id, parent_dict):
        if sect_id == "":
            print(f"RAN OFF TOP")
            return None
        xpath = f"//{self.SECT}[@id='{sect_id}']"
        elems = root.xpath(xpath)
        if len(elems) == 0:
            parent_id = parent_dict.get(sect_id)
            missing = False
            if parent_id is None:
                print(f" missing parent section {sect_id}")
                missing = True
                spl = sect_id.split(self.DOT)
                split_ = spl[:-1]
                parent_id = self.DOT.join(split_)
            if parent_id == "":
                print(f" skip root...")
            elem = self.ensure_element(root, parent_id, parent_dict)
            if elem is not None:
                sect_xml = lxml.etree.SubElement(elem, self.SECT)
                sect_xml.attrib[self.ID] = sect_id
                if missing:
                    sect_xml.attrib[self.MISSING] = "Y"
                return sect_xml
        elif len(elems) > 1:
            print(f" duplicate ids: {sect_id}")
            return None
        else:
            return elems[0]

    def sort_sections(self):
        print("sort sections NYI")
        pass

    @classmethod
    def sort_ids(cls):
        pass

class Footnote:
    """extracts footnotes by size and style and perhaps positiom
    """

    @classmethod
    def extract_footnotes(cls, fn_xpath, footnote_text_classes, html_elem):
        new_html_elem = HtmlLib.create_new_html_with_old_styles(html_elem)
        footnote_number_font_elems = html_elem.xpath(fn_xpath)
        last_footnum = 0
        ul = lxml.etree.Element("ul")
        HtmlLib.get_body(new_html_elem).append(ul)
        # messy, need a Footnote object here
        for footnote_number_elem in footnote_number_font_elems:
            last_footnum, li = Footnote.extract_footnote_and_save(
                footnote_number_elem, footnote_text_classes, last_footnum)
            if li is not None:
                ul.append(li)
        return new_html_elem

    @classmethod
    def is_footnote_font(cls, footnote_number_elem):
        """
        font size alone does not distinguish, so use neighbouring text
        """
        next = XmlLib.get_next_element(footnote_number_elem)
        text = footnote_number_elem.text
        if next is None:
            print(f"NO following elem")
            return False
        # folloed by small font?
        next_class = next.attrib["class"]
        if next_class == "s1045":
            return True
        return False


# Footnote

    @classmethod
    def extract_footnote_and_save(cls, footnote_number_elem, footnote_text_classes, last_footnum):
        text = footnote_number_elem.text
        footnote_number = -1
        ignore = False
        if not cls.is_footnote_font(footnote_number_elem):
            ignore = True
        try:
            footnote_number = int(text)
        except Exception:
            ignore = True
        li = None
        if not ignore and 5 > (footnote_number - last_footnum) >= 0:
            last_footnum, li = cls.delete_footnote_number_and_following_text__and_add_to_list(
                footnote_text_classes, footnote_number,
                footnote_number_elem)
        return last_footnum, li

    # Footnote

    @classmethod
    def create_footnote_number_xpath(cls, footnote_number_classes):
        xpath0 = ""
        for i, fnc in enumerate(footnote_number_classes):
            xpath0 += "" if i == 0 else " or "
            xpath0 += f"'{fnc}'"
        fn_xpath = f".//span[{xpath0}]"
        return fn_xpath

    # Footnote

    @classmethod
    def delete_footnote_number_and_following_text__and_add_to_list(
            cls, classes, footnote_number, footnote_number_elem):
        li = lxml.etree.Element("li")
        li.append(copy.deepcopy(footnote_number_elem))
        footnote_followers = XmlLib.get_following_elements(footnote_number_elem)
        # add one span(ends after font chamge)
        cls.iterate_until_unacceptable_font_class(footnote_followers, li=li, fn_classes=classes)
        last_footnum = footnote_number
        XmlLib.remove_element(footnote_number_elem)
        return last_footnum, li

    # Footnote

    @classmethod
    def iterate_until_unacceptable_font_class(cls, followers, li=None, fn_classes=None, debug=False):
        """iterates over elemts following a footnote number until an incompatible
        class style is found, when break"""
        for follower in followers:
            clazz = follower.attrib["class"]
            if clazz in fn_classes:
                li.append(copy.deepcopy(follower))
                XmlLib.remove_element(follower)
            else:
                if debug:
                    print(f"broke out of footnote at {clazz}")
                break


