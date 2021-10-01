from abc import ABC
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


def setup():
    """Variables created afresh for every test"""
    setup_dict = {}
    dictfile1 = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
    one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    root = etree.parse(str(dictfile1)).getroot()
    assert dictfile1.exists(), "{dictfile1} exists"
    one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    one_entry_dict = AMIDict.create_dict_from_path(one_entry_path)
    assert one_entry_dict is not None

    # BUG: this should be available through pytest
    setup_dict = {
        DICTFILE1: dictfile1, # type path
        ROOT: root,
        ONE_ENTRY_PATH: one_entry_path,
        ONE_ENTRY_DICT: one_entry_dict,
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
    assert type(one_dict) is AMIDict, f"fila is not TDDDict {one_dict}"

def test_dictionary_has_version_attribute():
    """require the attribiute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    # assert "xxx" == etree.tostring(one_dict.element)
    version = one_dict.get_version()
    assert version == "1.2.3"

def test_dictionary_has_version():
    """require the attribute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    version = one_dict.get_version()
    assert version is not None, "missing version"

def test_dictionary_has_valid_version():
    """require the attribute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    version = one_dict.get_version()
    assert one_dict.is_valid_version(version), "invalid version {version}}"

def test_dict_has_XML_title():
    setup_dict = setup()
    root = setup_dict[ROOT]
    assert root.attrib[AMIDict.TITLE_A] == "dict1"

def test_dict_title_matches_filename():
    setup_dict = setup()
    root = setup_dict[ROOT]
    last_path = setup_dict[DICTFILE1].stem
    print(last_path)
    assert root.attrib["title"] == last_path

def test_dict_has_root_dictionary():
    setup_dict = setup()
    root = setup_dict[ROOT]
    assert root.tag == AMIDict.TAG

def test_dict_contains_xml_element():
    setup_dict = setup()
    root = etree.parse(str(setup_dict[DICTFILE1]))
    assert root is not None

# AMIDict

def test_can_create_minimal_dictionary():
    amidict = AMIDict.create_minimal_dictionary()

def test_can_create_AmiDict_from_file():
    setup_dict = setup()
    one_entry_path = setup_dict[ONE_ENTRY_PATH]
    amidict = AMIDict.create_dict_from_path(one_entry_path)
    assert amidict is not None

def test_dictionary_is_a_TDDDict():
    setup_dict = setup()
    amidict = setup_dict[ONE_ENTRY_DICT]
    assert type(amidict) is AMIDict

def test_dictionary_get_entries():
    setup_dict = setup()
    amidict = setup_dict[ONE_ENTRY_DICT]
    entries = amidict.get_entries()
    assert entries is not None

def test_dictionary_contains_at_least_one_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_entry_count() > 0

def test_get_first_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_first_entry() is not None

def test_get_attribute_names():
    first_entry = setup()[ONE_ENTRY_DICT].get_first_entry()
    attrib_names = {name for name in first_entry.element.attrib}
    assert attrib_names is not None

def test_get_term_of_first_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_first_entry().element.attrib[AMIDict.TERM_A] == "Douglas Adams"

def test_get_name_of_first_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_first_entry().element.attrib[AMIDict.NAME_A] == "Douglas Adams"

def test_get_wikidata_of_first_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_first_entry().element.attrib[AMIDict.WIKIDATA_A] == "Q42"

def test_get_synonym_count():
    amidict = setup()[ONE_ENTRY_DICT]
    assert len(amidict.get_first_entry().get_synonyms()) == 2

def test_get_synonym_by_language():
    amidict = setup()[ONE_ENTRY_DICT]
    elem = amidict.get_first_entry().get_synonym_by_language(AMIDict.LANG_UR).element
    assert "ڈگلس ایڈمس" == ''.join(elem.itertext())

def test_dictionary_creation():
    amidict = AMIDict.create_minimal_dictionary()
    assert amidict is not None
    assert amidict.get_version() == "0.0.1"


def test_add_entry_to_zero_entry_dict():
    amidict = AMIDict.create_minimal_dictionary()
    entry = amidict.create_and_add_entry()
    assert b'<entry/>' == etree.tostring(entry.element)
    assert b'<dictionary version="0.0.1"><entry/></dictionary>' == etree.tostring(amidict.element)
    assert amidict.get_entry_count() == 1

def test_add_entry_with_term_to_zero_entry_dict():
    amidict = AMIDict.create_minimal_dictionary()
    entry = amidict.create_and_add_entry_with_term("foo")
    assert b'<entry term="foo"/>' == etree.tostring(entry.element)
    assert b'<dictionary version="0.0.1"><entry term="foo"/></dictionary>' == etree.tostring(amidict.element)
    assert amidict.get_entry_count() == 1

def test_add_two_entry_with_term_to_zero_entry_dict():
    amidict = AMIDict.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    assert b'<entry term="bar"/>' == etree.tostring(entry_bar.element)
    assert b'<dictionary version="0.0.1"><entry term="foo"/><entry term="bar"/></dictionary>' == etree.tostring(amidict.element)
    assert amidict.get_entry_count() == 2

def test_find_entry_by_term():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.find_entry_with_term("foo")
    assert entry is not None

def test_find_entry_by_term_bar():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.find_entry_with_term("bar")
    assert entry is not None

def test_find_entry_by_term_zilch():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.find_entry_with_term("zilch")
    assert entry is None

def test_delete_entry_by_term_foo():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.delete_entry_with_term("foo")
    assert amidict.get_entry_count() == 1

def test_delete_entry_by_term_foo_and_readd():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.delete_entry_with_term("foo")
    amidict.create_and_add_entry_with_term("foo")
    assert amidict.get_entry_count() == 2

# helpers
def _create_amidict_with_foo_bar_entries():
    amidict = AMIDict.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    return amidict


# test helpers


def teardown():
    dict1_root = None

# ==========please split into TDDDict==============
# this should not be here but I can't load it from an outside file
XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'


class AbsDictElem(ABC):
    """ Superclass of all SubObjects in an AMIDict tree

    AMIDict dictionaries are composed of an XML tree with wrapper objects
    on each node that requires customisation. Each Object contains an XML element
    which should not be used directly. Adding/deleting child elements and attributes
    should be done with Object methods
    """
    def __init__(self, element):
        self.element = element
        assert element is not None, "AbsDictElem constructor should not receive None "

class AMIDict(AbsDictElem):

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
# tag
    TAG = "dictionary"

    def __init__(self, element):
        """AMIDict always has an XML root element"""
        super().__init__(element)
        assert element is not None
        assert self.element is not None
        self.entries = [] # child entries

    @classmethod
    def create_minimal_dictionary(cls):
        element = etree.Element(cls.TAG)
        amidict = AMIDict(element)
        amidict.add_base_version()
        return amidict

    @classmethod
    def create_dict_from_path(cls, xml_file):
        assert xml_file is not None
        xml_path = Path(xml_file)
        assert xml_path.exists()
        element = etree.parse(str(xml_path)).getroot()
        assert element.tag == AMIDict.TAG
        amidict = AMIDict(element)
        amidict.get_entries()
        return amidict

    def get_entries(self):
        entry_elements = self.element.xpath(Entry.TAG)
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
        return None if self.element is None else AMIDict(self.element).get_version()

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
    def debug_tdd(cls):
        """This is just for debugging"""
        file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
        one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
        root = etree.parse(str(one_entry_file)).getroot()
        tddd = AMIDict.create_dict_from_path(one_entry_file)
        entries = tddd.get_entries()
        print(f"len {len(entries)} {type(entries)} entr {entries[0]} ")

    def add_base_version(self):
        assert self.element is not None
        self.element.attrib["version"] = "0.0.1"

    def get_version(self):
        assert self.element is not None
        return self.element.attrib["version"]

    def create_and_add_entry(self):
        entry_elem = Entry.create_and_add_to(self.element)
        return Entry(entry_elem)

    def create_and_add_entry_with_term(self, term):
        entry = self.create_and_add_entry()
        entry.add_term(term)
        return entry

    def find_entry_with_term(self, term):
        for entry in self.get_entries():
            if entry.get_term() == term:
                return entry
        return None

    def delete_entry_with_term(self, term):
        entry = self.find_entry_with_term(term)
        if entry is not None:
            self.delete_entry(entry)

    def delete_entry(self, entry):
        self.element.remove(entry.element)


class Entry(AbsDictElem):
    TAG = "entry"
    A_NAME = "name"
    A_TERM = "term"

    def __init__(self, element=None):
        super().__init__(element)
        assert element is not None and self.element is not None, f"entry elem is not None"

    @classmethod
    def create_and_add_to(cls, parent_element):
        return etree.SubElement(parent_element, cls.TAG)

    def get_synonyms(self):
        """list of child synonym objects"""
        synonyms = [] if self.element is None else self.element.xpath("./" + Synonym.TAG)
        return [Synonym(s) for s in synonyms]

    def get_synonym_by_language(self, lang):
        synonyms = self.get_synonyms()
        for synonym in synonyms:
            if lang == synonym.element.attrib[XML_LANG]:
                return synonym
        return None

    def add_term(self, term):
        self.element.attrib[self.A_TERM] = term

    def get_term(self):
        return self.element.attrib[self.A_TERM]

    def add_name(self, name):
        self.element.attrib[self.A_NAME] = name

    def get_name(self):
        return self.element.attrib[self.A_NAME]


class Synonym(AbsDictElem):
    TAG = "synonym"

    def __init__(self, element=None):
        super().__init__(element)
        assert element is not None, "synonym constructor "
        self.element = element


def main():
    AMIDict.debug_tdd()
#     tdd = Pyamidict_TDD()
#     tdd.test_dictionary_exists()
#     tdd.test_dict_contains_xml_element()
#     tdd.test_dict_has_root_dictionary()
#     tdd.test_dict_has_XML_title()
#     tdd.test_dict_title_matches_filename()

if __name__ == "__main__":
     main()

