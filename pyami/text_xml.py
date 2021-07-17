
import logging
import os
from .xml_lib import XmlLib

class Text_XML:

    def test_recurse_sections(self):
#        / Users / pm286 / projects / openDiagram / physchem / resources / oil26 / PMC4391421 / fulltext.xml
        file = os.path.abspath(os.path.join(__file__, "../src", "..", "resources", "liion10", "PMC7040616", "fulltext.xml"))
        print(file)
#        doc = XmlLib("../resources/liion/PMC7077619/fulltext.xml")
#        doc = XmlLib(file)
        xml_lib = XmlLib();
        doc = xml_lib.read(file)
        xml_lib.make_sections("sections")

def main():
    Text_XML().test_recurse_sections