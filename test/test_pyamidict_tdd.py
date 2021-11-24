"""These are tests for developing CODE for dictionary creation and validation

Code for VALIDATION of dictionaries should probably be bundled with the dictionaries themselves

"""
# from abc import ABC
# import pytest

from pathlib import Path
from lxml import etree
# from lxml.etree import Element
# from os.path import basename, normpath
# from tempfile import TemporaryDirectory
import os
import re

# from py4ami.xml_lib import XmlLib
from ..py4ami.dict_lib import AmiDictionary, AMIDict, AMIDictError, Synonym, Entry
# from py4ami.wikimedia import WikidataLooku
# dict1 = None
# root = None

DICTFILE1 = "dictfile1"
ROOT = "root"
ONE_ENTRY_PATH = "one_entry_file"
ONE_ENTRY_DICT = "one_entry_dict"
MINI_PLANT_PART = "mini_plant_part"
MINI_MENTHA = "mini_mentha"
ETHNOBOT_DICT = "VC_EthnobotanicalUse"
DUPLICATE_ENTRIES = "test_duplicate_entries"

AMIDICTS = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts") # relative to dictribution base

STARTING_VERSION = "0.0.1"

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
        DUPLICATE_ENTRIES: Path(AMIDICTS, DUPLICATE_ENTRIES + ".xml"),
    }
    return setup_dict

def test_dictionary_file1_exists():
    """Test that a simple dictionary "dictfile1" file exists"""
    setup_dict = setup()
    assert setup_dict[DICTFILE1].exists(), f"file should exist {setup_dict['dict1']}"
    teardown()

def test_one_entry_dict_is_AmiDictionary():
    """require the attribute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[ONE_ENTRY_DICT]
    assert type(one_dict) is AMIDict, f"fila is not AmiDictionary {one_dict}"

def test_dict1_has_version_attribute():
    """require the version attribute to be present but does not check value"""
    setup_dict = setup()
    one_dict = setup_dict[DICTFILE1]
    amidict = AMIDict.create_dict_from_path(Path(one_dict))
    version = amidict.get_version()
    assert version == STARTING_VERSION

def test_dict1_with_missing_version_attribute_is_not_valid():
    """require the version attribute to have starting value"""
    setup_dict = setup()
    amidict = AMIDict.create_dict_from_path(Path(setup_dict[DICTFILE1]))
    version = amidict.get_version()
    assert version == STARTING_VERSION

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

def test_title_from_url_stem():
    amidict = AMIDict.create_minimal_dictionary();
    amidict.set_url("https://some.where/foo/bar.xml")
    assert amidict.get_stem() == "bar"

def test_title_from_file_stem():
    amidict = AMIDict.create_minimal_dictionary();
    amidict.set_file("/user/me/foo.xml")
    assert amidict.get_stem() == "foo"

def test_dict_has_root_dictionary():
    setup_dict = setup()
    root = setup_dict[ROOT]
    assert root.tag == AMIDict.TAG

def test_dict_contains_xml_element():
    root = etree.parse(str(setup()[DICTFILE1]))
    assert root is not None


def test_dictionary_has_xml_declaration_with_encoding():
    tree = etree.parse(str(setup()[DICTFILE1]))
    assert tree.docinfo is not None
    assert tree.docinfo.xml_version == "1.0"
    assert tree.docinfo.encoding is not None
    assert tree.docinfo.encoding.upper() == 'UTF-8', f"dict must have encoding = 'UTF-8'"

def test_dictionary_has_xml_declaration_with_encoding_method():
    amidict = AMIDict.create_dict_from_path(setup()[DICTFILE1])
    amidict.has_xml_declaration_with_utf8()


# AmiDictionary

def test_can_create_minimal_dictionary():
    amidict = AMIDict.create_minimal_dictionary()

def test_can_create_AmiDict_from_file():
    setup_dict = setup()
    one_entry_path = setup_dict[ONE_ENTRY_PATH]
    amidict = AMIDict.create_dict_from_path(one_entry_path)
    assert amidict is not None

def test_dictionary_is_a_AmiDictionary():
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
    assert amidict.get_version() == STARTING_VERSION

# add entry to existing dict
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

def test_add_list_of_entries_from_list_of_string():
    terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
    term_count = len(terms)
    amidict = AMIDict.create_minimal_dictionary()
    amidict.create_and_add_entries_from_str_list(terms)
    assert amidict.get_entry_count() == term_count

def test_find_entry_after_add_list_of_entries_from_list_of_string():
    terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
    amidict = AMIDict.create_minimal_dictionary()
    amidict.create_and_add_entries_from_str_list(terms)
    entry_bar = amidict.find_entry_with_term("bar")
    assert entry_bar is not None

def test_fail_on_missing_entry_after_add_list_of_entries_from_list_of_string():
    terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
    amidict = AMIDict.create_minimal_dictionary()
    amidict.create_and_add_entries_from_str_list(terms)
    entry_zilch = amidict.find_entry_with_term("zilch")
    assert entry_zilch is None, f"missing entry returns None"

def test_add_second_list_of_entries_from_list_of_string():
    terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
    amidict = AMIDict.create_minimal_dictionary()
    amidict.create_and_add_entries_from_str_list(terms)
    terms1 = ["wibble", "wobble"]
    amidict.create_and_add_entries_from_str_list(terms1)
    assert amidict.get_entry_count() == len(terms) + len(terms1)

def test_add_list_of_entries_from_list_of_string_with_duplicates_and_replace():
    terms = ["foo", "bar", "plugh", "xyzzy", "bar"]
    amidict = AMIDict.create_minimal_dictionary()
    amidict.create_and_add_entries_from_str_list(terms, replace=True)
    assert amidict.get_entry_count() == 4, f"'bar' should be present"

def test_add_list_of_entries_from_list_of_string_with_duplicates_and_no_replace():
    terms = ["foo", "bar", "plugh", "xyzzy", "bar"]
    amidict = AMIDict.create_minimal_dictionary()
    try:
        amidict.create_and_add_entries_from_str_list(terms, replace=False)
        assert False, f"AMIDict duplicate error should have been thrown"
    except AMIDictError:
        assert True, "error should have been throwm"
    assert amidict.get_entry_count() == 4, f"'bar' should be present"

def test_add_then_remove_entry_and_replace():
    amidict = AMIDict.create_minimal_dictionary()
    amidict.create_and_add_entries_from_str_list(["foo", "bar", "plugh", "xyzzy"])
    assert amidict.get_entry_count() == 4
    amidict.delete_entries_with_term("bar")
    assert amidict.get_entry_count() == 3, f"entry 'bar' should have been removed"
    amidict.create_and_add_entry_with_term("bar")
    assert amidict.get_entry_count() == 4, f"entry 'bar' should have been re-added"

# find entries
def test_find_entry_by_term():
    """searches for entry by value of term"""
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.find_entry_with_term("foo")
    assert entry is not None
    assert entry.get_term() == "foo", f"should retrieve entry with term 'foo'"

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
    entry = amidict.delete_entries_with_term("foo")
    assert amidict.get_entry_count() == 1

def test_delete_entry_by_term_foo_and_re_add():
    amidict = _create_amidict_with_foo_bar_entries()
    entry = amidict.delete_entries_with_term("foo")
    amidict.create_and_add_entry_with_term("foo")
    assert amidict.get_entry_count() == 2

def test_create_and_add_entry_with_term():
    term = "foo"
    amidict = AMIDict.create_minimal_dictionary()
    assert amidict.get_entry_count() == 0
    amidict.create_and_add_entry_with_term(term)
    assert amidict.get_entry_count() == 1
    entry = amidict.find_entry_with_term(term)
    assert type(entry) is Entry
    assert term == entry.get_term()

def test_create_and_overwrite_entry_with_duplicate_term():
    term = "foo"
    amidict = AMIDict.create_minimal_dictionary()
    assert amidict.get_entry_count() == 0
    entry = amidict.create_and_add_entry_with_term(term)
    entry.add_name("foofoo")
    # assert entry.get_name() is "foofoo"
    amidict.create_and_add_entry_with_term(term, replace=True)
    assert amidict.get_entry_count() == 1
    entry = amidict.find_entry_with_term(term)
    assert type(entry) is Entry
    assert term == entry.get_term()
    assert entry.get_name() is None

def test_create_and_fail_on_add_entry_with_duplicate_term():
    term = "foo"
    amidict = AMIDict.create_minimal_dictionary()
    entry = amidict.create_and_add_entry_with_term(term)
    try:
        amidict.create_and_add_entry_with_term(term, replace=False)
        assert False, f"should fail with duplicate entry"
    except AMIDictError as e:
        assert True, "should raise duplicate error"

def test_create_and_overwrite_duplicate_term():
    term = "foo"
    amidict = AMIDict.create_minimal_dictionary()
    entry = amidict.create_and_add_entry_with_term(term)
    assert entry.get_name() is None
    entry.add_name("bar")
    assert entry.get_name() == "bar"
    try:
        amidict.create_and_add_entry_with_term(term, replace=True)
        assert True, f"should overwrit duplicate entry"
    except AMIDictError as e:
        assert True, "should not raise duplicate error"

# dictionary tests
def test_dictionary_should_have_version():
    amidict = AMIDict.create_minimal_dictionary()
    assert amidict.get_version() is not None
    # amidict.check_validity()
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

def test_get_duplicate_entries():
    """Dictionary has two entries for 'apical' but only one for 'cone'"""
    dup_dict = AMIDict.create_dict_from_path(setup()[DUPLICATE_ENTRIES])
    entries = dup_dict.find_entries_with_term("cone")
    assert entries is not None and len(entries) == 1
    entries = dup_dict.find_entries_with_term("apical")
    assert entries is not None and len(entries) == 2
    entries = dup_dict.find_entries_with_term("zilch")
    assert entries is not None and len(entries) == 0

def test_get_terms_from_valid_dictionary():
    """ETHNOBOT has no multiple entries'"""
    ethno_dict = AMIDict.create_dict_from_path(setup()[ETHNOBOT_DICT])
    terms, no_terms, mult_terms = ethno_dict.get_terms()
    assert terms is not None
    assert len(terms) == 8
    assert terms == ['anti-fumitory', 'adaptogen', 'homeopathy variable agent', 'ethnomedicinal agent',
 'phytochemical agent', 'phytomedical agent', 'plant-extracted agent', 'lung-tonifying agent']
    assert no_terms == []
    assert mult_terms == []

def test_get_terms_from_invalid_dictionary():
    """DUPLICATE_ENTRIES has two entries for 'apical' and some missing terms"""
    dup_dict = AMIDict.create_dict_from_path(setup()[DUPLICATE_ENTRIES])
    terms, no_terms, mult_terms = dup_dict.get_terms()
    assert terms == ['apical', 'flowering top', 'cone', 'pistil']
    assert no_terms == []
    assert mult_terms == ['(apical) in entry 2']


# review dictionaries
def test_mini_plant_part_is_valid():
    # pp_dict = AmiDictionary(setup_amidict[MINI_PLANT_PART])
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

# integrations
def test_create_dictionary_from_list_of_string():
    terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
    title = "foobar"
    directory = None
    amidict = AMIDict.create_from_list_of_strings(terms, title)
    assert amidict is not None
    title = amidict.get_title()
    assert title == "foobar"
    assert amidict.has_valid_title()

def test_create_dictionary_from_list_of_string_and_save():
    terms = ["acetone", "benzene", "chloroform", "DMSO", "ethanol"]
    temp_dir = Path(Path(__file__).parent.parent, "temp")
    assert os.path.exists(temp_dir), f"{temp_dir} exists"
    title = "solvents"
    tempfile = Path(temp_dir, title+".xml")
    dictfile, amidict = AMIDict.create_from_list_of_strings_and_write_to_file(terms, title=title, directory=temp_dir)
    assert dictfile is not None and os.path.exists(dictfile)

def test_create_dictionary_from_list_of_string_save_and_compare():
    terms = ["acetone", "benzene", "chloroform", "DMSO", "ethanol"]
    temp_dir = Path(Path(__file__).parent.parent, "temp")
    dictfile, amidict = AMIDict.create_from_list_of_strings_and_write_to_file(terms, title="solvents", directory=temp_dir)
    with open(dictfile, "r") as f:
        dict_text = f.read()
    dict_text = re.sub("date=\"[^\"]*\"", "date=\"TODAY\"", dict_text)
    assert len(dict_text) > 200, "lines of dict_text"
    assert type(dict_text) is str, f"{type(dict_text)}"
    # note, the date is nstripped as it changes with each run
    text1 = """<dictionary version="0.0.1" title="solvents" encoding="UTF-8">
  <metadata user="pm286" date="TODAY"/>
  <entry term="acetone"/>
  <entry term="benzene"/>
  <entry term="chloroform"/>
  <entry term="DMSO"/>
  <entry term="ethanol"/>
</dictionary>
"""
    assert text1 == dict_text, f"{text1} != {dict_text}"

def test_create_dictionary_from_list_of_string_and_add_Wikidata():
    terms = ["acetone", "chloroform", "DMSO", "ethanol"]
    amidict = AMIDict.create_amidict_and_lookup_wikidata(terms, "solvents")
    temp_dir = Path(Path(__file__).parent.parent, "temp")
    dictfile = amidict.write_to_file(temp_dir)

    with open(dictfile, "r") as f:
        dict_text = f.read()
    dict_text = re.sub("date=\"[^\"]*\"", "date=\"TODAY\"", dict_text)

    # note, the date is stripped as it changes with each run
    text1 = """<dictionary version="0.0.1" title="solvents" encoding="UTF-8">
  <metadata user="pm286" date="TODAY"/>
  <entry term="acetone" wikidataID="Q49546" description="chemical compound"/>
  <entry term="chloroform" wikidataID="Q172275" description="chemical compound"/>
  <entry term="DMSO" wikidataID="Q407927" description="organosulfur chemical compound used as a solvent"/>
  <entry term="ethanol" wikidataID="Q153" description="chemical compound"/>
</dictionary>
"""
    assert text1 == dict_text, f"{text1} != {dict_text}"


# helpers
def _create_amidict_with_foo_bar_entries():
    amidict = AMIDict.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    return amidict

# test helpers


def teardown():
    dict1_root = None

