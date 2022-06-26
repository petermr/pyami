"""Supports parsing, editing, markup, restructing of HTML"""

import lxml
import lxml.etree
import re
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
    def split_span_at_match(cls, span, re_compile, copy_atts=True, recurse=True, id_root=None, id_counter=0):
        """splits a span into 3 components by regex match
        :param span: span to split
        :param re_compile: compiled regex to split span
        :param copy_atts: if True copy atts from span
        :param recurse: if True rests span to trailing span and reanlyses until no more match
        :param id_root: auto-generate ids building on id_root
        :param id_counter: counter for ids
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
                spans[0].attrib["class"] = "re_pref"
                id_counter = cls.add_id_increment_counter(id_counter, id_root, span)
            spans[1] = HtmlUtil.add_sibling_after(H_SPAN, span, copy_atts=copy_atts, text=match.group(2))
            spans[1].attrib["class"] = "re_match"
            id_counter = cls.add_id_increment_counter(id_counter, id_root, spans[1])
            if match.group(3) != "":  # don't add empty string
                spans[2] = HtmlUtil.add_sibling_after(H_SPAN, spans[1], copy_atts=copy_atts, text=match.group(3))
                spans[2].attrib["class"] = "re_post"
                id_counter = cls.add_id_increment_counter(id_counter, id_root, spans[2])
                if recurse:
                    _,id_counter = HtmlUtil.split_span_at_match(spans[2], re_compile, copy_atts=copy_atts, recurse=recurse, id_root=id_root, id_counter=id_counter)
        return spans, id_counter

    @classmethod
    def add_id_increment_counter(cls, id_counter, id_root, html_elem):
        if id_root:
            html_elem.attrib[A_ID] = id_root + str(id_counter)
            id_counter += 1
        return id_counter

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
    def create_div_span(cls, text, style=None):
        """utilitymethodto create a div/span@text (probably mainly for testing)
        :param text: to add
        :return: the div"""
        div = lxml.etree.Element(H_DIV)
        span = lxml.etree.SubElement(div, H_SPAN)
        if style:
            css_style = CSSStyle.create_css_style_from_css_string("font-size:12; font-weight: bold;")
            span.attrib["style"] = css_style.generate_css_value()
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

    @classmethod
    def create_css_style_from_css_string(cls, css_string):
        """creates CSSStyle object from CSS string"""
        css_style = None
        if css_string:
            css_style = CSSStyle()
            css_style.name_value_dict = cls.create_dict_from_string(css_string)
        return css_style

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

