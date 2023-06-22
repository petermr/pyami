import lxml.etree

from py4ami.util import AmiLogger
from py4ami.xml_lib import NS_MAP, XML_NS, SVG_NS

SVG_SVG = "svg"
SVG_CIRCLE = "circle"
SVG_POLYLINE = "polyline"

POINTS = "points"
FILL = "fill"
STROKE = "stroke"
STROKE_WIDTH = "stroke-width"

logger = AmiLogger.create_named_logger(__file__)

class AmiSVG:
    """for actually rendering SVG?"""

    def __init__(self):
        pass

    @classmethod
    def create_SVGElement(cls, tag):
        svg_ns = NS_MAP[SVG_NS]
        return lxml.etree.Element(f"{{{svg_ns}}}{tag}")

    @classmethod
    def create_svg(cls):
        svg_elem = cls.create_SVGElement(SVG_SVG)
        return svg_elem

    @classmethod
    def create_circle(cls, xy, r, parent=None,  fill="yellow", stroke="red", stroke_width=1):
        circle_elem = None
        if xy and r:
            circle_elem = cls.create_SVGElement(SVG_CIRCLE)
            circle_elem.attrib["cx"] = str(xy[0])
            circle_elem.attrib["cy"] = str(xy[1])
            circle_elem.attrib["r"] = str(r)
            circle_elem.attrib["fill"] = fill
            circle_elem.attrib["stroke"] = stroke
            circle_elem.attrib["stroke-width"] = str(stroke_width)
        if parent is not None:
            parent.append(circle_elem)
        return circle_elem

    @classmethod
    def create_polyline(cls, xy_array, parent=None, fill="yellow", stroke="red", stroke_width=1, ndec=2):
        """
        creates svg:polyline
        :param xy_array: N*2 array of row-wies x,y coords
        :param parent: if not none, use ase parent element
        :param fill: default 'yellow'
        :param stroke: default red
        :param stroke_width: default 1
        :return: lxml namespaced svg:polyline
        """
        polyline_elem = None
        if xy_array:
            polyline_elem = cls.create_SVGElement(SVG_POLYLINE)
            points = ""
            for i, xy in enumerate(xy_array):
                if i > 0:
                    points += " "
                points += str(round(xy[0], ndec))+","+str(round(xy[1], ndec))
            polyline_elem.attrib[POINTS] = points
            polyline_elem.attrib[FILL] = fill
            polyline_elem.attrib[STROKE] = stroke
            polyline_elem.attrib[STROKE_WIDTH] = str(stroke_width)

        if parent is not None:
            parent.append(polyline_elem)
        return polyline_elem

    @classmethod
    def create_rect(cls, bbox, parent=None, fill="gray", stroke="blue", stroke_width=0.3):
        logger.debug(f"box {bbox}")
        svg_rect = AmiSVG.create_SVGElement("rect")
        svg_rect.attrib["fill"] = fill
        svg_rect.attrib["stroke"] = stroke
        svg_rect.attrib["stroke-width"] = str(stroke_width)
        try:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except Exception as e:
            raise ValueError(f"bbox must be four floats [x0, y0, x1, y1], got {bbox}")
        svg_rect.attrib["x"] = str(bbox[0])
        svg_rect.attrib["y"] = str(bbox[1])
        svg_rect.attrib["width"] = str(width)
        svg_rect.attrib["height"] = str(height)
        if parent is not None:
            parent.append(svg_rect)
        return svg_rect


