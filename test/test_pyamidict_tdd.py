import pytest

from pathlib import Path
from lxml import etree
from lxml.etree import Element
from os.path import basename, normpath
# from py4ami.dict_lib import TDDDict
# I can't get this imported
# from test.classes import TDDDict

from py4ami.xml_lib import XmlLib

# dict1 = None
# root = None

DICTFILE1 = "dictfile1"
ROOT = "root"
ONE_ENTRY_PATH = "one_entry_file"
ONE_ENTRY_DICT = "one_entry_dict"
TDDDICT = "tttdict"


def setup():
    """Variables created afresh for every test"""
    setup_dict = {}
    dictfile1 = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
    one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    root = etree.parse(str(dictfile1)).getroot()
    assert dictfile1.exists(), "{dictfile1} exists"
    one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    one_entry_dict = TDDDict.create_dict_from_path(one_entry_path)
    assert one_entry_dict is not None
    amidict = TDDDict()

    # BUG: this should be available through pytest
    setup_dict = {
        DICTFILE1: dictfile1, # type path
        ROOT: root,
        ONE_ENTRY_PATH: one_entry_path,
        ONE_ENTRY_DICT: one_entry_dict,
        TDDDICT: amidict,
    }
    return setup_dict

def test_dictionary_file1_exists():
    """Test that a simple dictionary "dictfile1" file exists"""
    setup_dict = setup()
    assert setup_dict[DICTFILE1].exists(), f"file should exist {setup_dict['dict1']}"
    teardown()

def test_dictionary_is_TDDDict():
    """require the attribiute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    assert type(one_dict) is TDDDict, f"fila is not TDDDict {one_dict}"

def test_dictionary_has_version_attribute():
    """require the attribiute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    assert one_dict.get_version() == "1.2.3"

def test_dictionary_has_valid_version():
    """require the attribute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    assert TDDDict.is_valid_version(one_dict.get_version()), "version is not valid {one_dict.get_version()}"

def test_dict_has_XML_title():
    setup_dict = setup()
    root = setup_dict[ROOT]
    assert root.attrib[TDDDict.TITLE_A] == "dict1"

def test_dict_title_matches_filename():
    setup_dict = setup()
    root = setup_dict[ROOT]
    last_path = setup_dict[DICTFILE1].stem
    print(last_path)
    assert root.attrib["title"] == last_path

def test_dict_has_root_dictionary():
    setup_dict = setup()
    root = setup_dict[ROOT]
    assert root.tag == TDDDict.DICTIONARY_E

def test_dict_contains_xml_element():
    setup_dict = setup()
    root = etree.parse(str(setup_dict[DICTFILE1]))
    assert root is not None

# TDDDict

def test_can_create_empty_TDDDict():
    tdddict = TDDDict()

def test_can_create_TDDDict_from_file():
    setup_dict = setup()
    one_entry_path = setup_dict[ONE_ENTRY_PATH]
    tdddict = TDDDict.create_dict_from_path(one_entry_path)
    assert tdddict is not None

def test_dictionary_is_a_TDDDict():
    setup_dict = setup()
    tdddict = setup_dict[ONE_ENTRY_DICT]
    assert type(tdddict) is TDDDict

def test_dictionary_get_entries():
    setup_dict = setup()
    tdddict = setup_dict[ONE_ENTRY_DICT]
    entries = tdddict.get_entries()
    assert entries is not None

def test_dictionary_contains_at_least_one_entry():
    tdddict = setup()[ONE_ENTRY_DICT]
    assert tdddict.get_entry_count() > 0

def test_get_first_entry():
    tdddict = setup()[ONE_ENTRY_DICT]
    assert tdddict.get_first_entry() is not None

def test_get_attribute_names():
    first_entry = setup()[ONE_ENTRY_DICT].get_first_entry()
    attrib_names = {name for name in first_entry.element.attrib}
    assert attrib_names is not None

def test_get_term_of_first_entry():
    tdddict = setup()[ONE_ENTRY_DICT]
    assert tdddict.get_first_entry().element.attrib[TDDDict.TERM_A] == "Douglas Adams"

def test_get_name_of_first_entry():
    tdddict = setup()[ONE_ENTRY_DICT]
    assert tdddict.get_first_entry().element.attrib[TDDDict.NAME_A] == "Douglas Adams"

def test_get_wikidata_of_first_entry():
    tdddict = setup()[ONE_ENTRY_DICT]
    assert tdddict.get_first_entry().element.attrib[TDDDict.WIKIDATA_A] == "Q42"

def test_get_synonym_count():
    tdddict = setup()[ONE_ENTRY_DICT]
    assert len(tdddict.get_first_entry().get_synonyms()) == 2

def test_get_synonym_by_language():
    tdddict = setup()[ONE_ENTRY_DICT]
    elem = tdddict.get_first_entry().get_synonym_by_language(TDDDict.LANG_UR).element
    assert "ڈگلس ایڈمس" == ''.join(elem.itertext())

def test_dictionary_creation():
    newdict = TDDDict.create_new_dictionary()
    assert newdict is not None
    assert newdict.get_version() == "0.0.1"


def test_add_entry():
    setup_dict = setup()

    # assert amidict
    teardown()



# test helpers


def teardown():
    dict1_root = None

# ==========please split into TDDDict==============
# this should not be here but I can't load it from an outside file

XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
class TDDDict:
    pass

# elements
    DICTIONARY_E = "dictionary"
    ENTRY_E = "entry"
    SYNONYM_E = "synonym"
# attributes
    NAME_A = "name"
    TERM_A = "term"
    TITLE_A = "title"
    VERSION_A = "version"
    WIKIDATA_A = "wikidata"
    WIKIPEDIA_A = "wikipedia"
# lang
    LANG_EN = "en"
    LANG_HI = "hi"
    LANG_UR = "ur"


    def __init__(self):
        self.root = None # the XML tree for the dictionary
        self.entries = [] # child entries

    @classmethod
    def create_dict_from_path(cls, xml_file):
        assert xml_file is not None
        xml_path = Path(xml_file)
        assert xml_path.exists()
        tdddict = TDDDict()
        tdddict.root = etree.parse(str(xml_path)).getroot()
        return tdddict

    def get_entries(self):
        print (self.root)
        entry_elements = self.root.xpath(self.ENTRY_E)
        assert entry_elements is not None
        self.entries = [Entry(element) for element in entry_elements]
        return self.entries

    def get_entry_count(self):
        return len(self.get_entries())

    def get_first_entry(self):
        self.get_entries()
        # what have I done wrong?
        # first_entry = self.entries[0] if len(self.entries) > 0 else None
        first_entry = None
        if len(self.entries) > 0:
            first_entry = self.entries[0]
        return first_entry

    def get_version(self):
        """get the version attribute"""
        return None if self.root is None else Dictionary(self.root).get_version()

    @classmethod
    def is_valid_version(self, version):
        """tests validity of version string major.minor.patch

        e.g. version = "1.2.3"
        """
        parts = version.split(".")
        assert len(parts) == 3
        for part in parts:
            i = int(part)
        return True

    @classmethod
    def create_new_dictionary(cls):
        tddict = TDDDict()
        tddict.add_new_root()
        return tddict

    def add_new_root(self):
        self.root = Dictionary().element

    @classmethod
    def debug_tdd(cls):
        """This is just for debugging"""
        file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
        one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
        root = etree.parse(str(one_entry_file)).getroot()
        tddd = TDDDict.create_dict_from_path(one_entry_file)
        entries = tddd.get_entries()
        print(f"len {len(entries)} {type(entries)} entr {entries[0]} ")


class DictElement():
    def __init__(self, element=None):
        self.element = element

class Dictionary(DictElement):
    def __init__(self, element=None):
        super().__init__(element)
        if element is None:
            self.create_root_element()

    def create_root_element(self):
        self.element = etree.Element("dictionary")
        self.add_base_version()

    def add_base_version(self):
        self.element.attrib["version"] = "0.0.1"

    def get_version(self):
        if self.element is None:
            return None
        assert type(self.element) is etree._Element
        return self.element.attrib["version"]

class Entry(DictElement):
    def __init__(self, element=None):
        super().__init__(element)

    def get_synonyms(self):
        synonyms = [] if self.element is None else self.element.xpath("./"+TDDDict.SYNONYM_E)
        return [Synonym(s) for s in synonyms]

    def get_synonym_by_language(self, lang):
        synonyms = self.get_synonyms()
        for synonym in synonyms:
            if lang == synonym.element.attrib[XML_LANG]:
                return synonym
        return None


class Synonym(DictElement):

    def __init__(self, element=None):
        super().__init__(element)


def main():
    TDDDict.debug_tdd()
#     tdd = Pyamidict_TDD()
#     tdd.test_dictionary_exists()
#     tdd.test_dict_contains_xml_element()
#     tdd.test_dict_has_root_dictionary()
#     tdd.test_dict_has_XML_title()
#     tdd.test_dict_title_matches_filename()

if __name__ == "__main__":
     main()

