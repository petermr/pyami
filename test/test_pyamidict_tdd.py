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
ETHNOBOT_DICT = "VC_EthnobotanicalUse"

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
        ETHNOBOT_DICT: Path(AMIDICTS, ETHNOBOT_DICT+".xml"),
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

def test_create_dictionary_from_url():
    mentha_url = "https://raw.githubusercontent.com/petermr/pyami/main/py4ami/resources/amidicts/mentha_tps.xml"
    mentha_dict = AMIDict.create_dict_from_url(mentha_url)
    assert len(mentha_dict.get_entries()) == 1
    assert mentha_dict.get_first_entry().get_term() == "1,8-cineole synthase"
    assert mentha_dict.get_version() == "0.0.3"
    mentha_dict.check_validity()

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
    amidict.check_validity()
    amidict.remove_attribute(AMIDict.VERSION_A)
    if amidict.get_version() is not None:
        raise AMIDictError("should have removed version")
    try:
        amidict.check_validity()
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
    pp_dict.check_validity()

def test_mini_mentha_tps_dict_is_valid():
    mentha_dict = AMIDict.create_dict_from_path(setup()[MINI_MENTHA])
    if mentha_dict is None:
        raise AMIDictError("cannot find/read mentha_dict")
    mentha_dict.check_validity()

def test_ethnobot_dict_has_version():
    ethnobot_dict = AMIDict.create_dict_from_path(setup()[ETHNOBOT_DICT])
    assert ethnobot_dict.get_version() is not None
    assert AMIDict.is_valid_version_string(ethnobot_dict.get_version())
    # assert ethnobot_dict.get_version() == "0.0.1"

def test_ethnobot_dict_is_valid():
    ethnobot_dict = AMIDict.create_dict_from_path(setup()[ETHNOBOT_DICT])
    ethnobot_dict.check_validity()
    # assert ethnobot_dict.get_version() == "0.0.1"

def test_ethnobot_dict_has_8_entries():
    ethnobot_dict = AMIDict.create_dict_from_path(setup()[ETHNOBOT_DICT])
    entries = ethnobot_dict.get_entries()
    assert len(entries) == 8

def test_ethnobot_dict_entry_0_is_valid():
    ethnobot_dict = AMIDict.create_dict_from_path(setup()[ETHNOBOT_DICT])
    entry0 = ethnobot_dict.get_entries()[0]
    entry0.check_validity()

def test_all_ethnobot_dict_entries_are_valid():
    ethnobot_dict = AMIDict.create_dict_from_path(setup()[ETHNOBOT_DICT])
    for entry in ethnobot_dict.get_entries():
        entry.check_validity()

# helpers
def _create_amidict_with_foo_bar_entries():
    amidict = AMIDict.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    return amidict

# test helpers


def teardown():
    dict1_root = None

