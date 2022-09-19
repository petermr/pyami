"""Supports parsing, editing, markup, restructing of HTML
Should have relatively few dependencies"""
import argparse
import logging
import lxml
import lxml.etree
import re
from pathlib import Path
# local
# from py4ami.ami_dict import AmiDictionary
from py4ami.util import SScript, AbstractArgs

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
            html_span.attrib["style"] = self.text_style.create_css_string()
            if len(self.xx) > 0:
                html_span.attrib["x"] = self.xx[0]
            if self.x0:
                # print(f"x0 {self.x0}")
                html_span.attrib["x0"] = str(self.x0)
            if self.x1:
                html_span.attrib["x1"] = str(self.x1)
            html_span.attrib["y"] = str(self.y0)
        return html_span


class AmiHtml:

    def __init__(self):
        pass


class HtmlUtil:
    SCRIPT_FACT = 0.9  # maybe sholdn't be here; avoid circular
    MARKER = "marker"

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
        textx = ''.join(elemx.itertext())
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
            # print(f" match 2 {match.group(2)}")
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
        """joint <span>...</span><span>...</span> into <span>...</span> recursively
        this structure arises when PDF or images is parsed and spans have the same styles (size/style/weight) and can be merged
        :param div: contains the sibling spans
        """
        print(f" NYI")

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
            output_dir = Path(output_dir)
            if not output_dir.exists():
                output_dir.mkdir()
            for i, child_div in enumerate(decimal_divs):
                if HtmlUtil.MARKER in child_div.attrib:
                    marker = child_div.attrib[HtmlUtil.MARKER].strip().replace(" ",
                                                                               "_").lower()  # name from text content
                    marker.replace(":", "")  # BUG, extend this to all punctuation
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
                if div == current_div:
                    print("f cannot append div {div} to itself")
                else:
                    try:
                        current_div.append(div)
                    except ValueError as ve:
                        print(f"Error {ve}")
                try:
                    current_div.append(div)
                except Exception as e:
                    print(f"BUG skipped")
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
            print(f"no arg_dict given, no action")
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
        print(f"dictfile {self.dictfile}")
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

    WEIGHT_RE = "([-.]?Bold|[.][Bb]$)"
    STYLE_RE = "([-.]?Ital(:?ic)|[-.]?Oblique|[.][Ii]$)"

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
        r = rgb_scale * (1.0 - (c + k) / float(cmyk_scale))
        g = rgb_scale * (1.0 - (m + k) / float(cmyk_scale))
        b = rgb_scale * (1.0 - (y + k) / float(cmyk_scale))

        return r, g, b

    @classmethod
    def cmky_to_rgb(cls, c, m, k, y):
        return cls.cmyk_to_rgb(c, m, y, k)

    def extract_bold_italic_from_font_family(self, overwrite_bold=False, overwrite_style=False, overwrite_family=True,
                                             style_regex=STYLE_RE, weight_regex=WEIGHT_RE):
        """heuristics to find bold and italic in font names and try to normalise
        e.g.
        font-family: TimesNewRomanPS-BoldMT; => font-family: TimesNewRomanPSMT; font_weight: bold
        font-family: TimesNewRomanPS-ItalicMT; => font-family: TimesNewRomanPSMT; font_style: italic
        the overwrite_* determine whetehr existing components will be overwritten
        :param overwrite_weight: create font_weight:bold regardless of previous weight
        :param overwrite_style: create font_style:bold regardless of previous style
        :param overwrite_family: edit font-family to remove style/weight info (hacky)
        :param style_regex=

        """
        family = self.font_family
        if not family:
            return
        family, value1 = self.match_weight_style(family, style_regex, value="I", mark="SS")
        family, value2 = self.match_weight_style(family, weight_regex, value="B", mark="WW")
        print(f"{family} {value1} {value2}")

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
