from pathlib import Path

import lxml.etree

from py4ami.ami_svg import AmiSVG
from py4ami.xml_lib import XmlLib

from test.resources import Resources
from test.test_all import AmiAnyTest


class TestSvg(AmiAnyTest):

    def test_create_namespaced_element(self):
        svg_elem = AmiSVG.create_SVGElement("circle")
        print(f"circle {lxml.etree.tostring(svg_elem).decode('UTF-8')}")

    def test_create_circle(self):
        svg_elem = AmiSVG.create_svg()
        circle_elem = AmiSVG.create_circle(xy=(100, 100), r=50, parent=svg_elem)
        print(f"circle {lxml.etree.tostring(svg_elem).decode('UTF-8')}")
        XmlLib.write_xml(svg_elem, Path(Resources.TEMP_DIR, "svg_test", "circle.svg"))

    def test_create_polyline(self):
        svg_elem = AmiSVG.create_svg()
        polyline_elem = AmiSVG.create_polyline(xy_array=[[100,100], [200, 200], [300,100], [200, 0]], parent=svg_elem)
        print(f"polyline {lxml.etree.tostring(svg_elem).decode('UTF-8')}")
        XmlLib.write_xml(svg_elem, Path(Resources.TEMP_DIR, "svg_test", "polyline.svg"))
