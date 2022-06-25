"""Supports parsing, editing, markup, restructing of HTML"""

import lxml
import lxml.etree
# local
from py4ami.util import SScript
# from py4ami.ami_bib import Reference, Biblioref
from py4ami.ami_bib import Publication

# HTML
H_TABLE = "table"
H_THEAD = "thead"
H_TBODY = "tbody"
H_TR = "tr"
H_TH = "th"
H_TD = "td"
H_BODY = "body"
H_DIV = "div"
H_SPAN = "span"
H_A = "a"
H_P = "p"
H_HREF = "href"
A_ID = "id"


class AmiHtml:

    def __init__(self):
        pass


class HtmlUtil:

    SCRIPT_FACT = 0.9 # maybe sholdn't be here; avoid circular

    @classmethod
    def split_span_at_match(cls, span, re_compile, copy_atts=True, recurse=True):
        """splits a span into 3 components by regex match
        :param span: span to split
        :param re_compile: compiled regex to split span
        :param copy_atts: if True copy atts from span
        :param recurse: if True rests span to trailing span and reanlyses until no more match
        :return: list of 3 spans; if spans[2] is not None it's available for recursion)
        """
        assert span is not None and span.text
        match = re_compile.match(span.text)
        spans = [None, None, None]
        if match:
            assert len(match.groups()) == 3  # some may be empty strings
            if match.group(1) != "":  # don't add empty string
                span = HtmlUtil.add_sibling_after(H_SPAN, span, replace=True, copy_atts=copy_atts, text=match.group(1))
                spans[0] = span
            spans[1] = HtmlUtil.add_sibling_after(H_SPAN, span, copy_atts=copy_atts, text=match.group(2))
            if match.group(3) != "":  # don't add empty string
                spans[2] = HtmlUtil.add_sibling_after(H_SPAN, spans[1], copy_atts=copy_atts, text=match.group(3))
                if recurse:
                    HtmlUtil.split_span_at_match(spans[2], re_compile, copy_atts=copy_atts, recurse=recurse)
        return spans

    @classmethod
    def add_sibling_after(cls, tag, anchor_elem, replace=False, copy_atts=False, text=None):
        """adds new trailing sibling of anchor_elem with tag
        :param tag: tag for new elements
        :param anchor_elem: reference element, must have a parent
        :param replace: if True, remove anchor element
        :param copy_atts: copy attributes from anchor
        :param text: if not None add text to new element
        :return: new sibling with optional ayytributes and text



        """

        assert anchor_elem is not None
        assert tag
        parent = anchor_elem.getparent()
        assert parent, f"No parent for anchor_elem"
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
    def create_div_span(cls, text):
        """utilitymethodto create a div/span@text (probably mainly for testing)
        :param text: to add
        :return: the div"""
        div = lxml.etree.Element(H_DIV)
        span = lxml.etree.SubElement(div, H_SPAN)
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
        if this_font_size < HtmlUtil.SCRIPT_FACT * last_font_size:
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
    def add_ids(cls, root_elem):
        """adds IDs to all elements in document order
        :param root_elem: element defining tree of subelements"""
        xpath = "//*"
        elems = root_elem.xpath(xpath)
        for i, el in enumerate(elems):
            el.attrib[A_ID] = A_ID + str(i)
