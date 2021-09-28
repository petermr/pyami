from pathlib import Path
from lxml import etree
from os.path import basename, normpath

from py4ami.xml_lib import XmlLib

class PyamiTDD():

    def __init__(self):
        print (f"this file {Path(__file__)}")
        self.dict1 = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")

    def test_dictionary_exists(self):
        self.setup()
        assert self.dict1.exists(), f"file should {self.dict1}"
        self.teardown()

    def test_dict_has_XML_title(self):
        root = etree.parse(str(self.dict1)).getroot()
        assert root.attrib["title"] == "dict1"

    def test_dict_title_matches_filename(self):
        root = etree.parse(str(self.dict1)).getroot()
        last_path = self.dict1.stem
        print(last_path)
        assert root.attrib["title"] == last_path

    def test_dict_has_root_dictionary(self):
        root = etree.parse(str(self.dict1)).getroot()
        assert root.tag == "dictionary"

    def test_dict_contains_xml_element(self):
        root = etree.parse(str(self.dict1))
        assert root is not None

    def setup(self):
        self.dict1_root = XmlLib.parse_xml_file_to_root(self.dict1)
        pass

    def teardown(self):
        pass

def main():
    tdd = PyamiTDD()
    tdd.test_dictionary_exists()
    tdd.test_dict_contains_xml_element()
    tdd.test_dict_has_root_dictionary()
    tdd.test_dict_has_XML_title()
    tdd.test_dict_title_matches_filename()

if __name__ == "__main__":
    main()

