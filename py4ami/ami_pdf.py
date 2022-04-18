import lxml
from lxml import etree

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

# style bundle
FONT_SIZE = "font-size"
FONT_STYLE = "font-style"
FONT_WEIGHT = "font-weight"
FONT_FAMILY = "font-family"
STYLE = "style"
FILL = "fill"
STROKE = "stroke"


class TextStyle:
    # try to map onto HTML italic/normal
    font_style = None
    # height in pixels
    font_size = None
    font_family = None
    # try to map onto HTML bold/norma
    font_weight = None
    # fill colour of text
    fill = None
    # stroke colour of text
    stroke = None


class TextSpan:
    """holds text content and attributes
    can be transformed into HTML
    """
    y = None
    start_x = None
    end_x = None
    text_style = None
    text_content = ""
    bbox = None

    def __str__(self):
        s = self.xy + ": " + (self.text_content[:10] + "... " if self.text_content is not None else "")
        return s

    def __repr__(self):
        return self.__str__()

    @property
    def xy(self):
        return "(" + str(self.start_x) + "," + str(self.y) + ")" if (self.start_x and self.y) else ""

    def __init__(self):
        pass


class AmiPage:

    def __init__(self):
        self.page_path = None
        self.page_element = None
        self.text_elements = None
        self.text_spans = []

    @classmethod
    def create_page_from_SVG(cls, svg_path):
        page = AmiPage()
        page.page_path = svg_path
        page.create_text_lines()
        return page

    def create_text_lines(self):
        self.create_raw_text_spans(sort_axes=SORT_XY)
        self.create_spans_from_long_whitespace()

    def create_raw_text_spans(self, sort_axes=None):
        """create text spans, including

        """
        if not sort_axes:
            sort_axes = []
        print(f"======== {self.page_path} =========")
        self.page_element = lxml.etree.parse(str(self.page_path))
        self.text_elements = self.page_element.findall(f"//{{{SVG_NS}}}text")
        print(f"texts {len(self.text_elements)}")
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
        print(f"text_spans {len(self.text_spans)}")
        for axis in sort_axes:
            if axis == X:
                self.text_spans = sorted(self.text_spans, key=lambda span: span.start_x)
            if axis == Y:
                self.text_spans = sorted(self.text_spans, key=lambda span: span.y)

            print(f"text_spans {axis}: {self.text_spans}")
            for text_span in self.text_spans:
                # print(f"> {text_span}")
                pass

        return self.text_spans

    def get_ami_text(self, index):
        if not self.text_elements or index < 0 or index >= len(self.text_elements):
            return None
        return AmiText(self.text_elements[index])

    def create_spans_from_long_whitespace(self):
        pass

    # needs integrating
    def find_text_breaks_in_pagex(self, sortedq=None):
        """create text spans, including

        """
        print(f"======== {self.page_path} =========")
        page_element = lxml.etree.parse(str(self.page_path))
        text_elements = page_element.findall(f"//{{{SVG_NS}}}text")
        print(f"texts {len(text_elements)}")
        text_breaks_by_line_dict = dict()
        for text_index, text_element in enumerate(text_elements):
            ami_text = AmiText(text_element)
            style_dict, text_break_list = ami_text.find_breaks_in_text()
            print(f"style {style_dict.get(Y)}")

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
                print(f"{text_content[current - offset:]}")
            else:
                # TODO
                new_text = TextSpan()
                # new_texts.append(tex)
        return text_breaks_by_line_dict

    # needs integrating
    def find_breaks_in_text(text_element):
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

    def create_text_span(self):
        text_span = TextSpan()
        text_span.text_style = self.create_text_style()
        text_span.text_content = self.get_text_content()
        text_span.start_x = self.get_x_coord()
        text_span.y = self.get_y_coord()
        return text_span

    def create_text_style(self):
        style = TextStyle()
        style.y = self.get_y_coord()
        style.x = self.get_x_coord()
        style.font_size = self.get_font_size()
        style.font_family = self.get_font_size()
        style.font_style = self.get_font_style()
        style.font_weight = self.get_font_weight()
        return style

    def get_x_coords(self):
        return self.get_float_vals(X)

    def get_x_coord(self):
        """get first X-coord
        :return: first x_coord in list or None"""
        x_coords = self.get_x_coords()
        return x_coords[0] if x_coords else None

    def get_y_coord(self):
        return self.get_float_val(Y)

    def get_widths(self):
        return self.get_float_vals(f"{{{SVGX_NS}}}width")

    def extract_style_dict_from_svg(self):
        style_dict = dict()
        style = self.svg_text_elem.attrib.get(STYLE)
        styles = style.split(';')
        for s in styles:
            if len(s) > 0:
                ss = s.split(":")
                style_dict[ss[0]] = ss[1]
        y = self.get_y_coord()
        if y:
            style_dict[Y] = y
        return style_dict

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

    def get_text_content(self):
        return ''.join(self.svg_text_elem.itertext())

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
                raise ValueError("cannot convert to floats, e")
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
