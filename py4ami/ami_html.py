"""Supports parsing, editing, markup, restructing of HTML
Should have relatively few dependencies"""

import lxml
import lxml.etree
import re
from pathlib import Path
# local
from py4ami.util import SScript

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
H_B = "b"
H_P = "p"
H_HREF = "href"
A_ID = "id"

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

class AmiSpan:
    def __init__(self):
        self.text_style = None
        self.string = ""
        self.xx = []
        self.y0 = None
        # self.adv = None

    def create_and_add_to(self, div):
        html_span = None
        if div is not None:
            html_span = lxml.etree.SubElement(div, "span")
            html_span.text = self.string
            html_span.attrib["style"] = self.text_style.create_css_string()
            if len(self.xx) > 0:
                html_span.attrib["x"] = self.xx[0]
            html_span.attrib["y"] = str(self.y0)
        return html_span


class AmiHtml:

    def __init__(self):
        pass


class HtmlUtil:
    SCRIPT_FACT = 0.9  # maybe sholdn't be here; avoid circular
    MARKER = "marker"

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
                    _, id_counter = HtmlUtil.split_span_at_match(spans[2], re_compile, copy_atts=copy_atts,
                                                                 recurse=recurse, id_root=id_root,
                                                                 id_counter=id_counter)
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
        last_font_size = last_span.text_style._font_size
        this_font_size = this_span.text_style._font_size
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
    def make_tree(cls, elem, output_dir, recs_by_section=None):
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
                ld = len(divs) if divs else 0
                print(f"Cannot find marker {marker} found {ld} markers")

        class_dict = {cls.CHAPSEC: cls.PRE_CHAPSEC,
                      cls.TOP_DIV: cls.TREE_ROOT, }
        rec = recs_by_section.get(cls.CHAP_TOP)
        assert rec, f"wanted {cls.CHAP_TOP} rec"
        print(f"using rec {rec}")
        decimal_divs = cls.get_div_spans_with_decimals(elem, is_bold, font_size_range=font_size_range,
                                                       section_rec=rec, class_dict=class_dict)
        print(f"d_divs {len(decimal_divs)}")
        if output_dir:
            if not output_dir.exists():
                output_dir.mkdir()
            for i, child_div in enumerate(decimal_divs):
                marker = child_div.attrib[HtmlUtil.MARKER].strip().replace(" ", "_").lower()  # name from text content
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
        print(f"class_div for annotating sections/divs with @class")
        # top_div/pre_chapsec collect the relevant divs (I think)
        top_div = lxml.etree.SubElement(elem, H_DIV)
        top_div.attrib[cls.CLASS] = class_dict.get(HtmlTree.TOP_DIV)
        pre_chapsec = lxml.etree.SubElement(top_div, H_DIV)
        pre_chapsec.attrib[cls.CLASS] = class_dict.get(HtmlTree.CHAPSEC)
        current_div = pre_chapsec

        # iterate over all divs, only append those with decimal
        divs = elem.xpath(cls.ALL_DIV_XPATHS)
        print(f"found divs {len(divs)}")
        decimal_count = 0
        texts = []  # just a check at present
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

    @classmethod
    def cmyk_to_rgb(cls, c, m, y, k):

        rgb_scale = 255
        # cmyk_scale = 100
        cmyk_scale = 1.0
        r = rgb_scale*(1.0-(c+k)/float(cmyk_scale))
        g = rgb_scale*(1.0-(m+k)/float(cmyk_scale))
        b = rgb_scale*(1.0-(y+k)/float(cmyk_scale))

        return r,g,b

    @classmethod
    def cmky_to_rgb(cls, c, m, k, y):
        return cls.cmyk_to_rgb(c, m, y, k)

