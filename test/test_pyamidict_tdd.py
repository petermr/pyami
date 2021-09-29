import pytest

from pathlib import Path
from lxml import etree
from os.path import basename, normpath
# from py4ami.dict_lib import TDDDict
# I can't get this imported
# from test.classes import TDDDict

from py4ami.xml_lib import XmlLib

# dict1 = None
# root = None

def setup():
    setup_dict = {}
    dictfile1 = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
    one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    root = etree.parse(str(dictfile1)).getroot()
    assert dictfile1.exists(), "{dictfile1} exists"
    one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
    one_entry_dict = TDDDict.create_dict_from_file(one_entry_file)
    assert one_entry_dict is not None
    amidict = TDDDict()
    # this is because I can't yet run tests under pytest
    setup_dict = {
        "dictfile1": dictfile1,
        "root": root,
        "one_entry_file": one_entry_file,
        "one_entry_dict" : one_entry_dict,
        "tttdict": amidict,
    }
    return setup_dict

def test_dictionary_file1_exists():
    setup_dict = setup()
    assert setup_dict["dictfile1"].exists(), f"file should exist {setup_dict['dict1']}"
    teardown()

def test_dict_has_XML_title():
    setup_dict = setup()
    root = setup_dict["root"]
    assert root.attrib["title"] == "dict1"

def test_dict_title_matches_filename():
    setup_dict = setup()
    root = setup_dict["root"]
    last_path = setup_dict["dictfile1"].stem
    print(last_path)
    assert root.attrib["title"] == last_path

def test_dict_has_root_dictionary():
    setup_dict = setup()
    root = setup_dict["root"]
    assert root.tag == "dictionary"

def test_dict_contains_xml_element():
    setup_dict = setup()
    root = etree.parse(str(setup_dict["dictfile1"]))
    assert root is not None

# entries

def test_can_create_empty_TDDDict():
    tdddict = TDDDict()

def test_can_create_TDDDict_from_file():
    setup_dict = setup()
    one_entry_file = setup_dict["one_entry_file"]
    tdddict = TDDDict.create_dict_from_file(one_entry_file)

def test_dictionary_is_a_TDDDict():
    setup_dict = setup()
    tdddict = setup_dict["one_entry_dict"]
    assert type(tdddict) is TDDDict

def test_dictionary_get_entries():
    setup_dict = setup()
    tdddict = setup_dict["one_entry_dict"]
    entries = tdddict.get_entries()
    assert entries is not None

def test_dictionary_contains_at_least_one_entry():
    tdddict = setup()["one_entry_dict"]
    assert tdddict.get_entry_count() > 0

def test_get_first_entry():
    tdddict = setup()["one_entry_dict"]
    ll = len(tdddict.get_entries())
    assert ll > 0, "len > 0"
    assert tdddict.get_first_entry() is not None

def test_get_term_of_first_entry():
    tdddict = setup()["one_entry_dict"]
    assert tdddict.get_first_entry().attrib["term"] == "Douglas Adams"

def test_get_name_of_first_entry():
    tdddict = setup()["one_entry_dict"]
    assert tdddict.get_first_entry().attrib["name"] == "Douglas Adams"

def test_get_wikidata_of_first_entry():
    tdddict = setup()["one_entry_dict"]
    assert tdddict.get_first_entry().attrib["wikipedia"] == "Q42"

def test_get_synonym_count():
    tdddict = setup()["one_entry_dict"]
    assert len(tdddict.get_synonyms()) == 2

def test_get_synonym_by_language():
    tdddict = setup()["one_entry_dict"]
    assert tdddict.get_synonym("ur") ==

def test_add_entry():
    setup_dict = setup()

    # assert amidict
    teardown()



# test helpers


def teardown():
    dict1_root = None

# this should not be here but I can't load it from an outside file
class TDDDict:
    pass

    def __init__(self):
        self.root = None # the XML tree for the dictionary
        self.entries = [] # child entries

    @classmethod
    def create_dict_from_file(cls, xml_file):
        assert xml_file is not None
        xml_path = Path(xml_file)
        assert xml_path.exists()
        tdddict = TDDDict()
        tdddict.root = etree.parse(str(xml_path)).getroot()
        return tdddict

    def get_entries(self):
        print (self.root)
        self.entries = self.root.xpath('entry')
        assert self.entries is not None
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

    @classmethod
    def debug_tdd(cls):
        """This is just for debugging"""
        file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
        one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
        root = etree.parse(str(one_entry_file)).getroot()
        tddd = TDDDict.create_dict_from_file(one_entry_file)
        entries = tddd.get_entries()
        print(f"len {len(entries)} {type(entries)} entr {entries[0]} ")

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

