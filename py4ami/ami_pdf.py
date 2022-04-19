import lxml
from lxml import etree
# local
from py4ami.bbox_copy import BBox  # this is horrid, but I don't have a library

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

# to link up text spans
X_MARGIN = 20

# style bundle
STYLE = "style"
ITALIC = "italic"
BOLD = "bold"
TIMES = "times"
CALIBRI = "calibri"
FONT_FAMILIES = [TIMES, CALIBRI]

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

    def __str__(self):
        s = f"size {self.font_size} family {self.font_family}, style {self.font_style} weight {self.font_weight} fill {self.fill} stroke {self.stroke}"
        return s

    def difference(self, other):
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
    def _difference(cls, name, val1, val2):
        s = ""
        if not val1 and not val2:
            pass
        elif not val1 or not val2 or val1 != val2:
            s = f"{name}: {val1} => {val2}"
        return s

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

    def __str__(self):
        s = self.xy + ": " + (self.text_content[:10] + "... " if self.text_content is not None else "")
        return s

    def __repr__(self):
        return self.__str__()

    @property
    def xy(self):
        return "(" + str(self.start_x) + "," + str(self.y) + ")" if (self.start_x and self.y) else ""

    # TextSpan

    def create_bbox(self):
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

    def normalize_family_weight(self):
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
        if not self.text_style.font_family in FONT_FAMILIES:
            print(f"new font_family {self.text_style.font_family}")

class AmiPage:

    def __init__(self):
        self.page_path = None
        self.page_element = None
        self.text_elements = None
        self.text_spans = []
        self.bboxes = []

    @classmethod
    def create_page_from_SVG(cls, svg_path):
        ami_page = AmiPage()
        ami_page.page_path = svg_path
        ami_page.create_text_lines()
        return ami_page

# AmiPage

    def create_text_lines(self):
        self.create_text_spans(sort_axes=SORT_XY)
        self.create_spans_from_long_whitespace()

    def create_text_spans(self, sort_axes=None):
        """create text spans, including

        """
        if not sort_axes:
            sort_axes = []
        if not self.text_spans:
            print(f"======== {self.page_path} =========")
            self.page_element = lxml.etree.parse(str(self.page_path))
            self.text_elements = self.page_element.findall(f"//{{{SVG_NS}}}text")
            # print(f"texts {len(self.text_elements)}")
            self.text_spans = []
            for text_index, text_element in enumerate(self.text_elements):
                ami_text = AmiText(text_element)
                text_span = ami_text.create_text_span()
                if not text_span:
                    print(f"cannot create TextSpan")
                    continue

                if len("".join(text_span.text_content.split())) == 0:
                    # test for whitespace content
                    # print(f"whitespace element skipped")
                    continue

                self.text_spans.append(text_span)
            print(f"no. text_spans {len(self.text_spans)}")
            for axis in sort_axes:
                if axis == X:
                    self.text_spans = sorted(self.text_spans, key=lambda span: span.start_x)
                if axis == Y:
                    self.text_spans = sorted(self.text_spans, key=lambda span: span.y)

                print(f"text_spans {axis}: {self.text_spans}")

        return self.text_spans

    # AmiPage

    def get_ami_text(self, index):
        if not self.text_elements or index < 0 or index >= len(self.text_elements):
            return None
        return AmiText(self.text_elements[index])

    def create_spans_from_long_whitespace(self):
        pass

    def get_bounding_boxes(self):
        if not self.bboxes:
            self.bboxes = []
            self.create_text_spans(sort_axes=SORT_XY)
            for text_span in self.text_spans:
                bbox = text_span.create_bbox()
                self.bboxes.append(bbox)
        return self.bboxes

    def find_text_span_overlaps(self):
        """overlaps textspans such as subscripts
        uses the bboxes
        will later creates larger spans as union of any intersecting boxes
        not rigorous"""
        self.create_text_spans(sort_axes=SORT_XY)
        self.composite_lines = []
        span0 = self.text_spans[0]
        composite_line = CompositeLine(bbox=span0.bbox)
        composite_line.text_spans.append(span0)
        self.composite_lines.append(composite_line)

        for i in range(1, len(self.text_spans)):
            text_span = self.text_spans[i]
            bbox = text_span.create_bbox().copy()
            bbox.expand_by_margin([X_MARGIN,0])
            # print(f" current {current_composite_line.bbox} box {bbox}")
            intersect_box = composite_line.bbox.intersect(bbox)
            if intersect_box:
                # print(f"intersect")
                mode = ""
                if composite_line.bbox.xy_ranges[1] == bbox.xy_ranges[1]:
                    # print(f"X-intersect {current_composite_line.bbox} + {bbox}")
                    mode = X
                    pass
                else:
                    # print(f"Y-intersect {current_composite_line.bbox} + {bbox} {text_span} ... {self.text_spans[i-1]}")
                    mode = Y
                    pass

                union_box = composite_line.bbox.union(bbox)
                # print(f" {mode} bbox {composite_line.bbox} => union {union_box}")
                composite_line.bbox = union_box
                composite_line.text_spans.append(text_span)
                if mode == Y:
                    print(f"{bbox.xy_ranges[1]} SCRIPT")
            else:
                composite_line = CompositeLine(bbox=bbox)
                self.composite_lines.append(composite_line)
                composite_line.bbox = bbox.copy()
                composite_line.text_spans.append(text_span)
                # print(f" new box {composite_line.bbox}")

        return self.composite_lines

    def find_bbox_overlaps_old(self):
        """overlaps textspans such as subscripts
        uses the bboxes
        will later creates larger spans as union of any intersecting boxes
        not rigorous"""
        self.get_bounding_boxes()
        if not self.bboxes or len(self.bboxes) == 0:
            return
        self.composite_lines = []
        current_composite_line = CompositeLine()
        current_composite_line.bbox = BBox(self.bboxes[0].xy_ranges)

        for i in range(1, len(self.bboxes)):
            bbox = self.bboxes[i]
            bbox.expand_by_margin([X_MARGIN,0])
            # print(f" current {current_composite_line.bbox} box {bbox}")
            intersect_box = current_composite_line.bbox.intersect(bbox)
            if intersect_box:
                # print(f"intersect")
                if current_composite_line.bbox.xy_ranges[1] == bbox.xy_ranges[1]:
                    # print(f"X-intersect {current_composite_line.bbox} + {bbox}")
                    pass
                else:
                    print(f"Y-intersect {current_composite_line.bbox} + {bbox}")
                    pass

                current_composite_line.box = current_composite_line.bbox.union(bbox)
            else:
                self.composite_lines.append(current_composite_line.bbox)
                current_composite_line.bbox = BBox(bbox.xy_ranges)
                # print(f" new box {current_line_box}")

        for composite_line in self.composite_lines:
            print(f"cc {self.composite_line}")



    # AmiPage

    # needs integrating
    def find_text_breaks_in_pagex(self, sortedq=None):
        """create text spans, including

        """
        print(f"======== {self.page_path} =========")
        page_element = lxml.etree.parse(str(self.page_path))
        text_elements = page_element.findall(f"//{{{SVG_NS}}}text")
        print(f"no. texts {len(text_elements)}")
        text_breaks_by_line_dict = dict()
        for text_index, text_element in enumerate(text_elements):
            ami_text = AmiText(text_element)
            style_dict, text_break_list = ami_text.find_breaks_in_text()

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
        ami_text = AmiText(text_element)
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


class AmiText:
    """wrapper for svg_text elemeent
    """

    def __init__(self, svg_text_elem):
        """create from svg_text"""
        self.svg_text_elem = svg_text_elem
        self.text_span = None
        self.create_text_span()

    def create_text_span(self):
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

    def create_text_style(self):
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

    def get_fill(self):
        return self.get_(FILL)

    def get_x_coords(self):
        return self.get_float_vals(X)

    def get_x_coord(self):
        """get first X-coord
        :return: first x_coord in list or None"""
        x_coords = self.get_x_coords()
        return x_coords[0] if x_coords else None

    def get_y_coord(self):
        return self.get_float_val(Y)

    # AmiText

    def get_widths(self):
        vals = self.get_float_vals(f"{{{SVGX_NS}}}{WIDTH}")
        return vals

    def get_last_width(self):
        """width of last character
        needed for bbox calculation
        :return: last width or 0.0 if none
        """
        widths = self.get_widths()
        return 0.0 if widths is None or len(widths) == 0 else widths[-1]

    def extract_style_dict_from_svg(self):
        style_dict = dict()
        style = self.svg_text_elem.attrib.get(STYLE)
        styles = style.split(';')
        for s in styles:
            if len(s) > 0:
                ss = s.split(":")
                style_dict[ss[0]] = ss[1]
        # y = self.get_y_coord()
        # if y:
        #     style_dict[Y] = y
        return style_dict

    # AmiText

    def get_font_family(self):
        sd = self.extract_style_dict_from_svg()
        fs = sd.get(FONT_FAMILY)
        return fs

    def get_font_size(self):
        sd = self.extract_style_dict_from_svg()
        fs = sd.get(FONT_SIZE)
        fs = fs[:-2]
        return float(fs)

    def get_font_weight(self):
        sd = self.extract_style_dict_from_svg()
        return sd.get(FONT_WEIGHT)

    def get_font_style(self):
        sd = self.extract_style_dict_from_svg()
        return sd.get(FONT_STYLE)

    def get_fill(self):
        sd = self.extract_style_dict_from_svg()
        return sd.get(FILL)

    def get_stroke(self):
        sd = self.extract_style_dict_from_svg()
        return sd.get(STROKE)

    def get_text_content(self):
        return ''.join(self.svg_text_elem.itertext())

    # AmiText

    def get_float_vals(self, attname):
        """gets list of floats if possible, else Exception
        :param attname:
        :return: list of floats
        :except: VakueError if any conversion fails"""
        attval = self.svg_text_elem.attrib.get(attname)
        if attval:
            ss = attval.split(',')
            try:
                vals = [float(s) for s in ss]
            except Exception as e:
                raise ValueError("cannot convert to floats", e)
            return vals
        return []

    def get_float_val(self, attname):
        """gets float value of attribute
        :param attname: attribute name
        :return: f;oat value or None if not possible"""
        attval = self.svg_text_elem.attrib.get(attname)
        try:
            return float(attval)
        except Exception as e:
            return None

class CompositeLine:
    """holds text spans which touch or intersect"""

    def __init__(self, bbox=None):
        self.bbox = None if bbox is None else bbox.copy()
        self.text_spans = []

    def __str__(self):
        s = f" spans: {len(self.text_spans)}:"
        for span in self.text_spans:
            s += f"__{span}"
        return s

