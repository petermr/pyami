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
from py4ami.dict_lib import AMIDict, AMIDictError, Synonym, Entry

# dict1 = None
# root = None

DICTFILE1 = "dictfile1"
ROOT = "root"
ONE_ENTRY_PATH = "one_entry_file"
ONE_ENTRY_DICT = "one_entry_dict"
MINI_PLANT_PART = "mini_plant_part"
MINI_MENTHA = "mini_mentha"

AMIDICTS = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts") # relative to dictribution base


def setup():
    """Variables created afresh for every test"""
    setup_dict = {}
    dictfile1 = Path(AMIDICTS, "dict1.xml")
    # dictfile1 = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
    one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    root = etree.parse(str(dictfile1)).getroot()
    assert dictfile1.exists(), "{dictfile1} exists"
    one_entry_path = Path(AMIDICTS, "dict_one_entry.xml")
    one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    one_entry_dict = AMIDict.create_dict_from_path(one_entry_path)
    mini_plant_part_path = Path(AMIDICTS, "mini_plant_part.xml")
    assert one_entry_dict is not None

    # BUG: this should be available through pytest
    setup_dict = {
        DICTFILE1: dictfile1, # type path
        ROOT: root,
        ONE_ENTRY_PATH: one_entry_path,
        ONE_ENTRY_DICT: one_entry_dict,
        MINI_PLANT_PART: mini_plant_part_path,
        MINI_MENTHA: Path(AMIDICTS, "mentha_tps.xml"),
    }
    return setup_dict

def test_dictionary_file1_exists():
    """Test that a simple dictionary "dictfile1" file exists"""
    setup_dict = setup()
    assert setup_dict[DICTFILE1].exists(), f"file should exist {setup_dict['dict1']}"
    teardown()

def test_one_entry_dict_is_AMIDict():
    """require the attribute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    assert type(one_dict) is AMIDict, f"fila is not AMIDict {one_dict}"

def test_dict1_has_version_attribute():
    """require the attribiute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[DICTFILE1]
    amidict = AMIDict.create_dict_from_path(Path(one_dict))
    version = amidict.get_version()
    assert version == "0.0.1"

def test_dict1_with_missing_version_attribute_is_not_valid():
    """require the attribiute to be present but does not check value"""
    setup_dict = setup()
    amidict = AMIDict.create_dict_from_path(Path(setup_dict[DICTFILE1]))
    version = amidict.get_version()
    assert version == "0.0.1"

def test_one_entry_dict_has_version_attribute():
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
    assert one_dict.is_valid_version_string(version), "invalid version {version}}"

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

def test_dictionary_is_a_AMIDict():
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
    assert amidict.get_first_entry().element.attrib[Entry.TERM_A] == "Douglas Adams"

def test_get_name_of_first_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_first_entry().element.attrib[Entry.NAME_A] == "Douglas Adams"

def test_get_wikidata_of_first_entry():
    amidict = setup()[ONE_ENTRY_DICT]
    assert amidict.get_first_entry().element.attrib[Entry.WIKIDATA_A] == "Q42"

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
    assert b'<dictionary version="0.0.1" title="minimal" encoding="UTF-8"><entry/></dictionary>' == etree.tostring(amidict.element)
    assert amidict.get_entry_count() == 1

def test_add_entry_with_term_to_zero_entry_dict():
    amidict = AMIDict.create_minimal_dictionary()
    entry = amidict.create_and_add_entry_with_term("foo")
    assert b'<entry term="foo"/>' == etree.tostring(entry.element)
    assert b'<dictionary version="0.0.1" title="minimal" encoding="UTF-8"><entry term="foo"/></dictionary>' == etree.tostring(amidict.element)
    assert amidict.get_entry_count() == 1

def test_add_two_entry_with_term_to_zero_entry_dict():
    amidict = AMIDict.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    assert b'<entry term="bar"/>' == etree.tostring(entry_bar.element)
    assert b'<dictionary version="0.0.1" title="minimal" encoding="UTF-8"><entry term="foo"/><entry term="bar"/></dictionary>' == etree.tostring(amidict.element)
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

def test_delete_entry_by_term_foo_and_re_add():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.delete_entry_with_term("foo")
    amidict.create_and_add_entry_with_term("foo")
    assert amidict.get_entry_count() == 2

# dictionary tests
def test_dictionary_should_have_version():
    amidict = AMIDict.create_minimal_dictionary()
    assert amidict.get_version() is not None
    assert amidict.is_valid() is True
    amidict.remove_attribute(AMIDict.VERSION_A)
    if amidict.get_version() is not None:
        raise AMIDictError("should have removed version")
    try:
        amidict.is_valid()
        raise AMIDictError("should fail is_valid()")
    except:
        # expect fail
        pass

def test_dictionary_forbidden_attributes():
    pass

# review dictionaries
def test_mini_plant_part_is_valid():
    # pp_dict = AMIDict(setup_amidict[MINI_PLANT_PART])
    pp_dict = AMIDict.create_dict_from_path(setup()[MINI_PLANT_PART])
    if pp_dict is None:
        raise AMIDictError(f"test_dictionary_should_have_desc cannot read dictionary {pp_dict}")
    pp_dict.is_valid()

def test_mini_mentha_tps_dict_is_valid():
    mentha_dict = AMIDict.create_dict_from_path(setup()[MINI_MENTHA])
    if mentha_dict is None:
        raise AMIDictError("cannot find/read mentha_dict")
    mentha_dict.is_valid()


# helpers
def _create_amidict_with_foo_bar_entries():
    amidict = AMIDict.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    return amidict


# test helpers


def teardown():
    dict1_root = None

# # ==========please split into TDDDict==============
# # this should not be here but I can't load it from an outside file
# XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
#
#
# class AbsDictElem(ABC):
#     """ Superclass of all SubObjects in an AMIDict tree
#
#     AMIDict dictionaries are composed of an XML tree with wrapper objects
#     on each node that requires customisation. Each Object contains an XML element
#     which should not be used directly. Adding/deleting child elements and attributes
#     should be done with Object methods
#     """
#     def __init__(self, element):
#         self.element = element
#         assert element is not None, "AbsDictElem constructor should not receive None "
#
# class AMIDict(AbsDictElem):
#
# # attributes
#     ENCODING_A = "encoding"
#     TITLE_A = "title"
#     VERSION_A = "version"
#
#
# # lang
#     LANG_EN = "en"
#     LANG_HI = "hi"
#     LANG_UR = "ur"
# # encoding
#     UTF_8 = "UTF-8"
# # tag
#     TAG = "dictionary"
#
#     def __init__(self, element):
#         """AMIDict always has an XML root element"""
#         super().__init__(element)
#         self.file = None
#         assert element is not None
#         assert self.element is not None
#         self.entries = [] # child entries
#
#     @classmethod
#     def create_minimal_dictionary(cls):
#         element = etree.Element(AMIDict.TAG)
#         amidict = AMIDict(element)
#         amidict.add_base_version()
#         amidict.set_title("minimal")
#         amidict.set_encoding(AMIDict.UTF_8)
#         return amidict
#
#     @classmethod
#     def create_dict_from_path(cls, xml_file):
#         assert xml_file is not None
#         xml_path = Path(xml_file)
#         assert xml_path.exists()
#         element = etree.parse(str(xml_path)).getroot()
#         assert element.tag == AMIDict.TAG
#         amidict = AMIDict(element)
#         amidict.get_entries()
#         amidict.set_file(xml_file)
#         return amidict
#
#     def set_file(self, file):
#         """file may be required to validate against title"""
#         self.file = file
#
#     def get_entries(self):
#         entry_elements = self.element.xpath(Entry.TAG)
#         assert entry_elements is not None
#         self.entries = [Entry(element) for element in entry_elements]
#         return self.entries
#
#     def get_entry_count(self):
#         return len(self.get_entries())
#
#     def get_first_entry(self):
#         self.get_entries()
#         # what have I done wrong?
#         # first_entry = self.entries[0] if len(self.entries) > 0 else None
#         first_entry = None
#         if len(self.entries) > 0:
#             first_entry = self.entries[0]
#         return first_entry
#
#     def get_version(self):
#         """get the version attribute"""
#         if self.element is None:
#             raise AMIDictError(f"{self.TAG} must have element")
#         version = self.element.attrib["version"]
#         assert version == "XXX"
#         return version
#
#     def set_version(self, version):
#         assert AMIDict.is_valid_version_string(version)
#         self.element.attrib[self.VERSION_A] = version
#
#     def get_title(self):
#         assert self.TITLE_A in self.element.attrib
#         return self.element.attrib[self.TITLE_A]
#
#     def set_title(self, title):
#         self.element.attrib[self.TITLE_A] = title
#
#     @classmethod
#     def debug_tdd(cls):
#         """This is just for debugging"""
#         file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
#         one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
#         root = etree.parse(str(one_entry_file)).getroot()
#         tddd = AMIDict.create_dict_from_path(one_entry_file)
#         entries = tddd.get_entries()
#         print(f"len {len(entries)} {type(entries)} entr {entries[0]} ")
#
#     def add_base_version(self):
#         assert self.element is not None
#         self.element.attrib["version"] = "0.0.1"
#
#     def get_version(self):
#
#         assert self.element is not None
#         return None if not AMIDict.VERSION_A in self.element.attrib else self.element.attrib[AMIDict.VERSION_A]
#
#     def set_encoding(self, encoding):
#         self.element.attrib[AMIDict.ENCODING_A] = encoding
#
#     def create_and_add_entry(self):
#         entry_elem = Entry.create_and_add_to(self.element)
#         return Entry(entry_elem)
#
#     def create_and_add_entry_with_term(self, term):
#         entry = self.create_and_add_entry()
#         entry.add_term(term)
#         return entry
#
#     def find_entry_with_term(self, term):
#         for entry in self.get_entries():
#             if entry.get_term() == term:
#                 return entry
#         return None
#
#     def delete_entry_with_term(self, term):
#         entry = self.find_entry_with_term(term)
#         if entry is not None:
#             self.delete_entry(entry)
#
#     def delete_entry(self, entry):
#         self.element.remove(entry.element)
#
# # data validity
#     def is_valid(self):
#         # assert f"{etree.tostring(self.element)}" == "xxx"
#         if not self.has_valid_element():
#             raise AMIDictError(msg="must contain valid element (NYI)")
#         if not self.has_valid_tag():
#             raise AMIDictError(msg="must have valid tag")
#         if not self.has_valid_attributes():
#             raise AMIDictError(msg="must have valid attributes")
#         return True
#         # assert self.has_valid_children()
#
#     def has_valid_element(self):
#         if self.element is None:
#             raise AMIDictError(msg="No element in AMIDict wrapper")
#         return True
#
#     def has_valid_tag(self) -> bool:
#         assert self.has_valid_element()
#         return self.element.tag == AMIDict.TAG
#
#     def has_valid_attributes(self):
#         if not self.has_valid_required_attributes():
#             raise AMIDictError(msg="element does not have valid required attributes")
#         if not self.has_valid_optional_attributes():
#             raise AMIDictError(msg="element does not have valid optional attributes")
#         if self.has_forbidden_attributes():
#             raise AMIDictError(msg="element has_forbidden_attributes")
#         return True
#
#     def has_valid_required_attributes(self):
#         version = self.get_version()
#         version_ok = AMIDict.is_valid_version_string(version)
#         if not version_ok:
#             raise AMIDictError(f"{self.TAG} does not have valid version")
#         title_ok = self.has_valid_title()
#         if not title_ok:
#             raise AMIDictError(f"{self.TAG} does not have valid title")
#         encoding_ok = self.has_valid_encoding()
#         if not encoding_ok:
#             raise AMIDictError(f"{self.TAG} does not have valid encoding")
#         return True
#
#     def remove_attribute(self, attname):
#         if attname is not None and attname in self.element.attrib:
#             self.element.attrib.pop(attname)
#
#     def has_valid_title(self):
#         """AMIDict must have title attribute with value == stem of dict file"""
#         title = self.get_title()
#         assert title is not None
#         return title is not None and \
#                (self.file is None or Path(self.file).stem == title)
#
#     @classmethod
#     def is_valid_version_string(cls, versionx):
#         """tests validity of version string major.minor.patch
#
#         e.g. version = "1.2.3"
#         """
#         if versionx is None:
#             raise AMIDictError(f"{cls} does not have version attribute ")
#         parts = versionx.split(".")
#         if len(parts) != 3:
#             raise AMIDictError(f"{cls} version attribute {versionx} does not have 3 parts")
#         try:
#             for part in parts:
#                 i = int(part)
#         except:
#             raise AMIDictError(f"{cls} version attribute {versionx} parts must be integers")
#         return True
#
#     def has_valid_encoding(self):
#         encoding = None if not AMIDict.ENCODING_A in self.element.attrib \
#             else self.element.attrib[AMIDict.ENCODING_A]
#         return encoding is not None and encoding.upper() == AMIDict.UTF_8
#
#     def has_valid_optional_attributes(self):
#         return True
#
#     def has_forbidden_attributes(self):
#         return False
#
#     def has_valid_children(self):
#         assert False , "not yet written"
#         return True
#
# class AMIDictError(Exception):
#     """Basic exception for errors raised in AMIDict"""
#     def __init__(self, msg=None):
#         if msg is None:
#             msg = "An unspecifed error occured"
#         super(AMIDictError, self).__init__(msg)
#
# class Entry(AbsDictElem):
#     TAG = "entry"
#
#     DESCRIPTION_A = "description"
#     NAME_A = "name"
#     TERM_A = "term"
#     WIKIDATA_A = "wikidata"
#     WIKIPEDIA_A = "wikipedia"
#
#     REQUIRED_ATTS = {TERM_A}
#     OPTIONAL_ATTS = {DESCRIPTION_A, NAME_A, WIKIDATA_A, WIKIPEDIA_A}
#
#     def __init__(self, element=None):
#         super().__init__(element)
#         assert element is not None and self.element is not None, f"entry elem is not None"
#
#     @classmethod
#     def create_and_add_to(cls, parent_element):
#         return etree.SubElement(parent_element, cls.TAG)
#
#     def get_synonyms(self):
#         """list of child synonym objects"""
#         synonyms = [] if self.element is None else self.element.xpath("./" + Synonym.TAG)
#         return [Synonym(s) for s in synonyms]
#
#     def get_synonym_by_language(self, lang):
#         synonyms = self.get_synonyms()
#         for synonym in synonyms:
#             if lang == synonym.element.attrib[XML_LANG]:
#                 return synonym
#         return None
#
#     def add_term(self, term):
#         self.element.attrib[self.TERM_A] = term
#
#     def get_term(self):
#         return self.element.attrib[self.TERM_A]
#
#     def add_name(self, name):
#         self.element.attrib[self.NAME_A] = name
#
#     def get_name(self):
#         return self.element.attrib[self.NAME_A]
#
#
# class Synonym(AbsDictElem):
#     TAG = "synonym"
#
#     def __init__(self, element=None):
#         super().__init__(element)
#         assert element is not None, "synonym constructor "
#         self.element = element
#
#
# def main():
#     AMIDict.debug_tdd()
# #     tdd = Pyamidict_TDD()
# #     tdd.test_dictionary_exists()
# #     tdd.test_dict_contains_xml_element()
# #     tdd.test_dict_has_root_dictionary()
# #     tdd.test_dict_has_XML_title()
# #     tdd.test_dict_title_matches_filename()
#
# if __name__ == "__main__":
#      main()

