"""Supports parsing, editing, markup, restructing of HTML
Should have relatively few dependencies"""
import argparse
import copy
from collections import defaultdict
from io import StringIO
import logging
import lxml
import lxml.etree
from lxml.etree import _Element
import numpy as np
import re
from pathlib import Path
from sklearn.linear_model import LinearRegression
from collections import defaultdict

# local
# from py4ami.ami_dict import AmiDictionary
from py4ami.bbox_copy import BBox
from py4ami.xml_lib import XmlLib
from py4ami.util import SScript, AbstractArgs, Util

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
FILL = "fill"
STROKE = "stroke"

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
                html_span.attrib["x"] = self.xx[0]
            if self.x0:
                html_span.attrib["x0"] = str(self.x0)
            if self.x1:
                html_span.attrib["x1"] = str(self.x1)
            html_span.attrib["y"] = str(self.y0)
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
        n = page_div.xpath("./a/@name")
        n = n[0] if len(n) == 1 else None
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

        self.remove_attributes_and_elements()
        pagesize = None
        if self.marker_xpath:
            offset, pagesize, page_coords = HtmlUtil.find_constant_coordinate_markers(self.raw_elem, self.marker_xpath)
            HtmlUtil.remove_headers_and_footers_using_pdfminer_coords(self.raw_elem, pagesize, self.header, self.footer,
                                                                      self.marker_xpath)
        for att in self.style_attributes_to_remove:
            HtmlUtil.remove_style_attribute(self.raw_elem, att)
        HtmlUtil.remove_unwanteds(self.raw_elem, self.unwanteds)
        HtmlUtil.remove_newlines(self.raw_elem)
        HtmlTree.make_sections_and_output(self.raw_elem, output_dir=self.outdir, recs_by_section=RECS_BY_SECTION)
        htmlstr = lxml.etree.tostring(self.raw_elem).decode("UTF-8")
        return htmlstr

    def remove_attributes_and_elements(self):
        """
        remove objects if flags have been set in self
        """
        if self.add_id:
            HtmlUtil.add_ids(self.raw_elem)
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
            css_style = CSSStyle.create_css_style(style_span)
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
            css = CSSStyle.create_css_style(getparent)
            prev_elem = getparent.getprevious()
            height = -1 if css_last is None else css.top - css_last.top
            prev_style = CSSStyle.create_css_style(prev_elem)
            if not prev_style:
                logging.warning(f" no previous style")
            bbox = None if prev_style is None else prev_style.create_bbox()
            css_last = css
        return elem_with_pagenos

        """
<br></span><span style="font-family: Calibri; font-size:10px"> *** THIS SPAN WRAPS ALL REMAMING PAGERS???
<br><span style="position:absolute; border: gray 1px solid; left:0px; top:941px; width:595px; height:841px;"></span>
        """

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
        htmls = html_elem.xpath("/html")
        if len(htmls) == 0:
            logging.warning("wrapping in <html>")
            html_root = lxml.etree.Element("html")
            html_root.insert(0, html_elem)
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
            HtmlStyle.set_style(span, css_style.generate_css_value())
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
        if last_span is None:
            return False
        last_font_size = last_span.text_style._font_size
        this_font_size = this_span.text_style._font_size
        # is it smaller?
        if this_font_size < HtmlUtil.SCRIPT_FACT * last_font_size:
            last_y = last_span.y
            this_y = this_span.y
            if script_type == SScript.SUB:
                # is it lowered? Y DOWN
                return ydown and (last_y < this_y)
            elif script_type == SScript.SUP:
                # is it raised? Y DOWN
                return ydown and (last_y > this_y)
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
        """
        convenience method; avoids having to remember join/itertext
        """
        return ''.join(elem.itertext())

    @classmethod
    def add_ids(cls, root_elem):
        """adds IDs to all elements in document order
        :param root_elem: element defining tree of subelements"""
        xpath = "//*"
        elems = root_elem.xpath(xpath)
        for i, el in enumerate(elems):
            el.attrib[A_ID] = A_ID + str(i)

    def join_spans_in_div(self, html):
        """
        NYI
        joint <span>...</span><span>...</span> into <span>...</span> recursively
        this structure arises when PDF or images is parsed and spans have the same styles (size/style/weight) and can be merged
        :param html: contains the sibling spans
        """
        logging.warning(f"join_spans_in_div NYI")

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
            css_style = CSSStyle.create_css_style(el)
            if condition:
                if css_style.obeys(condition):
                    if remove:
                        cls.remove_elem_keep_tail(el)

    @classmethod
    def remove_headers_and_footers_using_pdfminer_coords(cls, ref_elem, pagesize, header_height, footer_height,
                                                         marker_xpath):
        """
        NOT COMPLETE - there are no footers because of the coordinate system.

        Maybe move to HTMLTidy

        the @top represents the y-coordinate from the start of the document (pdfminer?).
        this means we have to subtract pagesizes from it.
        """

        elems = ref_elem.xpath(marker_xpath)

        for elem in ref_elem.xpath("//*[@style]"):
            top = CSSStyle.create_css_style(elem).get_numeric_attval("top")  # the y-coordinate
            if top:
                top = top % pagesize
                if top < header_height or top > pagesize - footer_height:
                    text = XmlLib.get_text(elem)
                    if len(text.strip()) > 0:
                        logging.warning(f"removing top text {text}")
                    cls.remove_elem_keep_tail(elem)

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
            css_style = CSSStyle.create_css_style(el)
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
            css_style = CSSStyle.create_css_style(elem)
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
            css_style = CSSStyle.create_css_style(styled_elem)
            css_style.remove(names)
            css_style.apply_to(styled_elem)
            style = HtmlStyle.get_style(styled_elem)

class HtmlStyle:
    """
    methods to process style attributes and <style> elements
    """

    @classmethod
    def get_style(cls, elem):
        """
        convenience method to get element style
        :param elem: to get style from
        :return: style or None
        """
        return elem.attrib.get("style")

    @classmethod
    def set_style(cls, elem, value):
        """
        convenience method to set style on element
        :param elem:element to set style on
        :param value: css string; if "" or None remlves attribute
        """
        if elem is not None:
            XmlLib.set_attname_value(elem, "style", value)

    @classmethod
    def extract_all_text_styles_to_head(cls, html_elem):
        """
        Finds all elements with @style attribute and extacts the tdxt styles to <head>
        :param html_elem: total html object to normalize. Must have <head> and <body>
        """
        HtmlStyle.remove_empty_styles(html_elem)
        styled_elems = html_elem.xpath(".//*[@style]")
        for i, styled_elem in enumerate(styled_elems):
            classref = f"s{i}"
            HtmlStyle.add_element_with_style(classref, html_elem, styled_elem)

    @classmethod
    def add_element_with_style(cls, classref, html_elem, styled_elem):
        """
        adds
        """
        head = html_elem.xpath("/html/head")[0]
        elem_style = HtmlStyle.get_style(styled_elem)
        if elem_style is None or elem_style == "":
            return
        css = CSSStyle.create_css_style_from_css_string(elem_style)

        extracted_style_elem, remaining_style, new_class = css.extract_text_styles_into_class(classref)
        HtmlStyle.set_style(styled_elem, remaining_style)
        HtmlClass.set_class_on_element(styled_elem, classref, replace=False)
        head.append(extracted_style_elem)

    @classmethod
    def remove_empty_styles(cls, html_elem):
        """
        removes all empty style attributes (style="")
        """
        empty_styled_elems = html_elem.xpath(".//*[normalize-space(@style)='']")
        for elem in empty_styled_elems:
            HtmlStyle.delete_style(elem)

    @classmethod
    def delete_style(cls, elem):
        """
        conveniennce method to delete style attribute
        """
        XmlLib.remove_attribute(elem, "style")

    # THESE CAN BECOME INSTANCE METHODS

    @classmethod
    def normalize_head_styles(cls, elem):
        """
        creates multidict fot head styles
        :param elem: document to analyse
        :return: dict of classref_sets indexed by style strings

        e.g. item {font-family: TimesNewRomanPSMT; font-size: 6px;}: ['.s17', '.s19', '.s21', '.s27', '.s5', '.s7']
        """
        style_to_classref_set = defaultdict(set)
        head_styles = elem.xpath("/html/head/style")
        for style in head_styles:
            style_s = style.text.strip();
            classref = style_s.split()[0]
            value = style_s[len(classref):].strip()
            style.attrib[CLASSREF] = classref
            style_to_classref_set[value].add(classref)
        return style_to_classref_set

    @classmethod
    def extract_styles_and_normalize_classrefs(cls, html_elem):
        """
        Extract styles from document
        move to head and normalize classrefs
        delete redundant classrefs and styles
        map document instamces of styles onto normalized classrefs
        :param html_elem: html document to normalize

        Should be in an object


        """
        cls.extract_all_text_styles_to_head(html_elem)
        style_to_classref_set = cls.normalize_head_styles(html_elem)
        classref_index = cls.create_classref_index(style_to_classref_set)
        deletable_classrefs = cls.get_redundant_classrefs(classref_index)
        cls.delete_redundant_styles(deletable_classrefs, html_elem)
        cls.normalize_classrefs_on_elements(html_elem, classref_index)

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


class HtmlClass:
    """
    methods to process class attributes and sync with style
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

    @classmethod
    def create_from_classed_element(cls, elem):
        """
        get class value from element and ccreate HtmlClass
        :param elem: elements with @class attribute
        :return: HtmlClass element or None
        """
        clazz = HtmlClass.get_class_string_on_element(elem)
        return None if not clazz else HtmlClass(clazz)

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

    def has_class(self, clazz):
        """
        does class exist in classes
        :param clazz:
        """
        return clazz in self.classes

    def replace_class(self, clazz_old, clazz=None):
        """
        remove clazz_old ; if clazz is not None add it
        (if clazz is already present, no-op)
        """
        if clazz_old in self.classes:
            self.remove(clazz_old)
            if clazz:
                self.add_class(clazz)

    def remove(self, clazz):
        """
        remove class from string
        :param clazz: class string to remove
        if  not present, no-op
        """
        if clazz in self.classes:
            self.classes.remove(clazz)

    @classmethod
    def get_class_string_on_element(cls, elem):
        """
        convenience method to get element style
        :param elem: to get style from
        :return: style or None
        """

        return elem.attrib.get("class") if type(elem) is _Element else None

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

    def create_classref(self):
        """
        create classref string (prepend ".")
        """
        return "." + self.class_string

    @classmethod
    def remove_dot(self, string):
        """
        remove dot (".")
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

    @classmethod
    def make_sections_and_output(cls, elem, output_dir, recs_by_section=None):
        """find decimal number for tree
        ThiS is HEAVILY based on IPCC
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
        decimal_divs = cls.get_div_spans_with_decimals(elem, is_bold, font_size_range=font_size_range,
                                                       section_rec=rec, class_dict=class_dict)
        cls.create_filename_and_output(decimal_divs, output_dir)

    @classmethod
    def create_filename_and_output(cls, decimal_divs, output_dir,
                                   orig=" !\"#$%&'()*+,/:;<=>?@[\]^`{|}~", rep="_"):
        """
        create filename from section name, replace punct characters
        """
        if output_dir:
            output_dir = Path(output_dir)
            if not output_dir.exists():
                output_dir.mkdir()

            punct_mask = Util.make_translate_mask_to_char(orig, rep)
            for i, child_div in enumerate(decimal_divs):
                cls.create_filename_remove_punct_and_output(child_div, output_dir, punct_mask)

    @classmethod
    def create_filename_remove_punct_and_output(cls, child_div, output_dir, punct_mask):
        if HtmlUtil.MARKER in child_div.attrib:
            marker = child_div.attrib[HtmlUtil.MARKER]
            marker = marker.strip().lower()  # name from text content
            marker.translate(punct_mask)
            path = Path(output_dir, f"{marker}.html")
            with open(path, "wb") as f:
                f.write(lxml.etree.tostring(child_div, pretty_print=True))

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
            logging.warning(f"cannot find div: len={len(divs)}")
        elif len(divs) > 1:
            logging.warning(f"too many divs: len={len(divs)}")
        else:
            result = divs[0]
            result.attrib["marker"] = strg
        return result, divs

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

    @classmethod
    def in_range(cls, num, num_range):
        """is a number in a numeric range"""
        assert num_range or len(num_range) == 2, f"range must have 2 elements"
        assert num_range[0] <= num_range[1], f"font_size_range must be (lower,higher)"
        assert float(num_range[0])
        result = num_range[0] <= num <= num_range[1]
        return result

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

    def set_unmatched(self, unmatched):
        """
        set UNMATCHED boolean. If true adds all unmatched values to dict under UNMATCHED
        :param unmatched: acts on current nodeset
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
        if not self.outdir.exists():
            self.outdir.mkdir()

        self.ami_dict = AmiDictionary.create_from_xml_file(self.dictfile)
        self.ami_dict.markup_html_from_dictionary(self.inpath, self.outpath, self.color)


class CSSStyle:
    """
    common subset of CSS styles/commands
    """
    BOLD = "Bold"
    BORDER = "border"
    BOTTOM = "bottom"
    COLOR = "color"
    DOT_B = ".B"
    FONT_FAMILY = "font-family"
    FONT_SIZE = "font-size"
    FONT_STYLE = "font-style"
    FONT_WEIGHT = "font-weight"
    HEIGHT = "height"
    LEFT = "left"
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

    @classmethod
    def create_css_style(cls, elem):
        """create CSSStyle object from elem
        :param elem:
        """
        if elem is None:
            return None
        assert type(elem) is _Element, f"found {type(elem)}"
        css_style = CSSStyle()
        style_attval = elem.get(CSSStyle.STYLE)
        css_style.name_value_dict = cls.create_dict_from_string(style_attval)
        return css_style

    @classmethod
    def create_dict_from_string(cls, style_attval):
        name_value_dict = dict()
        if style_attval:
            style_attval = style_attval.strip()
            styles = style_attval.split(";")
            for style in styles:
                style = style.strip()
                if len(style) > 0:
                    ss = style.split(":")
                    if len(ss) != 2:
                        raise KeyError(f"bad style {style} in CSS: {style_attval}")
                    name = ss[0].strip()
                    if name in name_value_dict:
                        raise KeyError(f"{name} duplicated in CSS: {style_attval}")
                    name_value_dict[name] = ss[1].strip()
        return name_value_dict

    @classmethod
    def create_css_style_from_css_string(cls, css_string):
        """creates CSSStyle object from CSS string"""
        css_style = None
        if css_string:
            css_style = CSSStyle()
            css_style.name_value_dict = cls.create_dict_from_string(css_string)
        return css_style

    def __eq__(self, other):
        """
        tests whether self and other have equal dictionaries
        """
        if type(other) is CSSStyle:
            return self.name_value_dict == other.name_value_dict
        return False

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
        css_str = self.generate_css_value()
        elem.attrib[CSSStyle.STYLE] = css_str

    def generate_css_value(self):
        """
        generates css string without quoted names and values
        """
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

    @property
    def height(self):
        return self.get_numeric_attval(CSSStyle.HEIGHT)

    @classmethod
    def add_name_value(cls, elem, css_name, css_value):
        """updates style on element
        :param css_name: name of property
        :param css_value: value of property
        """
        css_style = cls.create_css_style(elem)
        css_style.name_value_dict[css_name] = css_value
        css_style.apply_to(elem)

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

    @classmethod
    def cmyk_to_rgb(cls, c, m, y, k):

        rgb_scale = 255
        # cmyk_scale = 100
        cmyk_scale = 1.0
        r = rgb_scale * (1.0 - (c + k) / float(cmyk_scale))
        g = rgb_scale * (1.0 - (m + k) / float(cmyk_scale))
        b = rgb_scale * (1.0 - (y + k) / float(cmyk_scale))

        return r, g, b

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
        family, value1 = self.match_weight_style(family, style_regex, value="I", mark="SS")
        family, value2 = self.match_weight_style(family, weight_regex, value="B", mark="WW")

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

    def create_bbox(self):
        """
        create bounding box from left, width, top, height
        :return: None if any attributes missing
        """
        bbox = None
        if self.top is not None and self.height is not None and self.left is not None and self.width is not None:
            bbox = BBox(xy_ranges=[[self.left, self.left + self.width], [self.top, self.top + self.height]])
        return bbox

    def extract_substyles(self, css_names):
        """
        Create 2 new CSSSstyles , the first with names in "styles" and the second the rest.
            if None, retruns None,None
        :param css_names: list of CSS names (e.g. "font-family"). If na name not found, no action
        :return 2-tuple of 1) CSSStyle object with extracted names 2) CSSStyle of the remainder;
            either/both may be empty CSSStyle.
        """
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

    def create_html_style_element(self, html_class):
        """
        Creates string for HTML style
        """
        DOT = "."
        s = DOT + html_class + " " + "{" + self.generate_css_value().strip() + "}"
        elem = lxml.etree.Element(CSSStyle.STYLE)
        elem.text = s
        return elem

    def extract_text_styles(self):
        """
        extract text components from style (font-*, color, etc) into new style, returning tuple of
        new style and style from remaining components
        """
        (extracted_style, retained) = font_style, rest_style = self.extract_substyles(
            CSSStyle.TEXT_STYLE_COMPONENTS
        )
        return (extracted_style, retained)

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
        extracted_html_style_element = extracted_style.create_html_style_element(class_name)
        retained_style_attval = retained_style.generate_css_value()
        html_class_val = CSSStyle.create_html_class_val(class_name, old_class_val=old_classstr)
        return extracted_html_style_element, retained_style_attval, html_class_val


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


