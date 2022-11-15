import glob
import logging
import os
import pprint
import re
import unittest
from pathlib import Path

import lxml
from lxml import etree
from lxml.etree import XMLSyntaxError, _Element

# local
from py4ami.ami_dict import AmiDictionary, AmiEntry, AmiDictArgs, AMIDictError, \
    AmiDictValidator, NAME, TITLE, TERM, LANG_UR, VERSION, WIKIDATA_ID
from py4ami.constants import PHYSCHEM_RESOURCES, CEV_OPEN_DICT_DIR
from py4ami.wikimedia import WikidataSparql, WikidataPage
from py4ami.xml_lib import XmlLib
from test.resources import Resources
from test.test_all import AmiAnyTest

# MUST use RAW content , not HTML
CEV_OPEN_RAW_DICT_URL = "https://raw.githubusercontent.com/petermr/CEVOpen/master/dictionary/"
PLANT_PART_RAW_DICT_URL = CEV_OPEN_RAW_DICT_URL + "eoPlantPart/eoplant_part.xml"
COMPOUND_RAW_DICT_URL = CEV_OPEN_RAW_DICT_URL + "eoCompound/plant_compound.xml"
ANALYSIS_METHOD_RAW_DICT_URL = CEV_OPEN_RAW_DICT_URL + "eoAnalysisMethod/eoAnalysisMethod.xml"
TEST_DIR = Path(Path(__file__).parent.parent, "test")
TEST_RESOURCE_DIR = Path(TEST_DIR, "resources")
DICTFILE1 = "dictfile1"
ROOT = "root"
ONE_ENTRY_PATH = "one_entry_file"
ONE_ENTRY_DICT = "one_entry_dict"
MINI_PLANT_PART = "mini_plant_part"
MINI_MENTHA = "mini_mentha"
ETHNOBOT_DICT = "VC_EthnobotanicalUse"
DUPLICATE_ENTRIES = "test_duplicate_entries"

AMIDICTS = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts")  # relative to dictribution base

STARTING_VERSION = "0.0.1"


# ===== helpers =====
def _create_amidict_with_foo_bar_entries():
    amidict = AmiDictionary.create_minimal_dictionary()
    entry_foo = amidict.create_and_add_entry_with_term("foo")
    entry_bar = amidict.create_and_add_entry_with_term("bar")
    return amidict


class TestAmiDictionary(AmiAnyTest):
    """These are tests for developing CODE for dictionary creation and validation

    Code for VALIDATION of dictionaries should probably be bundled with the dictionaries themselves

    """

    logging.info(f"loading {__file__}")

    DICTFILE1 = "dictfile1"
    ROOT = "root"
    ONE_ENTRY_PATH = "one_entry_file"
    ONE_ENTRY_DICT = "one_entry_dict"
    MINI_PLANT_PART = "mini_plant_part"
    MINI_MENTHA = "mini_mentha"
    ETHNOBOT_DICT = "VC_EthnobotanicalUse"
    DUPLICATE_ENTRIES = "test_duplicate_entries"

    AMIDICTS = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts")  # relative to dictribution base

    STARTING_VERSION = "0.0.1"

    ADMIN = True and AmiAnyTest.ADMIN
    CMD = True and AmiAnyTest.CMD
    LONG = True and AmiAnyTest.LONG
    NET = True and AmiAnyTest.NET
    NYI = True and AmiAnyTest.NYI
    USER = True and AmiAnyTest.USER
    VERYLONG = True and AmiAnyTest.VERYLONG

    def setup(self):
        """Variables created afresh for every test"""
        dictfile1 = Path(AMIDICTS, "dict1.xml")
        # dictfile1 = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
        one_entry_path = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
        root = etree.parse(str(dictfile1)).getroot()
        assert dictfile1.exists(), "{dictfile1} exists"
        one_entry_path = Path(AMIDICTS, "dict_one_entry.xml")
        one_entry_dict_new = AmiDictionary.create_from_xml_file(one_entry_path)
        assert one_entry_dict_new is not None
        mini_plant_part_path = Path(AMIDICTS, "mini_plant_part.xml")

        # BUG: this should be available through pytest
        setup_dict = {
            DICTFILE1: dictfile1,  # type path
            ROOT: root,
            ONE_ENTRY_PATH: one_entry_path,
            ONE_ENTRY_DICT: one_entry_dict_new,
            MINI_PLANT_PART: mini_plant_part_path,
            MINI_MENTHA: Path(AMIDICTS, "mentha_tps.xml"),
            ETHNOBOT_DICT: Path(AMIDICTS, ETHNOBOT_DICT + ".xml"),
            DUPLICATE_ENTRIES: Path(AMIDICTS, DUPLICATE_ENTRIES + ".xml"),
        }
        print(f"setup_dict {setup_dict}")
        return setup_dict

    @unittest.skipUnless("environment", ADMIN)
    def test_dictionary_file1_exists(self):
        """Test that a simple dictionary "dictfile1" file exists"""
        setup_dict = self.setup()
        assert setup_dict[DICTFILE1].exists(), f"file should exist {setup_dict['dict1']}"
        self.teardown()

    def test_read_wellformed_dictionary(self):
        """test can create from XML string
        includes well-formed and non-well-formed XML
        """
        dict_str = """
        <dictionary title='foo'>
        </dictionary>
        """
        ami_dict = AmiDictionary.create_dictionary_from_xml_string(dict_str)
        assert ami_dict is not None

        assert ami_dict.root.tag == "dictionary"

        dict_str = """
        <diktionary title='foo'>
        </dictionary>
        """
        try:
            ami_dict = AmiDictionary.create_dictionary_from_xml_string(dict_str)
        except XMLSyntaxError as e:
            print(f"xml error {e}")

    def test_dictionary_element(self):
        dict_str = """
        <dictionary title='foo'>
        </dictionary>
        """
        ami_dict = AmiDictionary.create_dictionary_from_xml_string(dict_str)
        assert ami_dict is not None
        assert ami_dict.root.tag == "dictionary"
        assert ami_dict.has_valid_root_tag()

    def test_one_entry_dict_is_ami_dictionary(self):
        """require the attribute to be present but does not check value"""
        setup_dict = self.setup()
        one_dict = setup_dict[ONE_ENTRY_DICT]
        assert type(one_dict) is AmiDictionary, f"fila is not AmiDictionary {one_dict}"

    def test_dict1_has_version_attribute(self):
        """require the version attribute to be present but does not check value"""
        setup_dict = self.setup()
        one_dict = setup_dict[DICTFILE1]
        amidict = AmiDictionary.create_from_xml_file(Path(one_dict))
        version = amidict.get_version()
        assert version == STARTING_VERSION

    def test_dict1_with_missing_version_attribute_is_not_valid(self):
        """require the version attribute to have starting value"""
        setup_dict = self.setup()
        amidict = AmiDictionary.create_from_xml_file(Path(setup_dict[DICTFILE1]))
        version = amidict.get_version()
        assert version == STARTING_VERSION

    def test_one_entry_dict_has_version_attribute(self):
        """require the attribiute to be present but does not check value"""
        setup_dict = self.setup()
        one_dict = setup_dict[ONE_ENTRY_DICT]
        assert one_dict is not None
        version = one_dict.get_version()
        assert version == "1.2.3"

    def test_dictionary_has_version(self):
        """require the attribute to be present but does not check value"""
        setup_dict = self.setup()
        one_dict = setup_dict[ONE_ENTRY_DICT]
        version = one_dict.get_version()
        assert version is not None, "missing version"

    @unittest.skip("superseded by Validator")
    def test_dictionary_has_valid_version(self):
        """require the attribute to be present but does not check value"""
        setup_dict = self.setup()
        one_dict = setup_dict[ONE_ENTRY_DICT]
        validator = AmiDictValidator(one_dict)
        version = one_dict.get_version()
        # assert validator. f"invalid version {version}"

    def test_catch_invalid_version(self):
        minimal_dict = AmiDictionary.create_minimal_dictionary()
        try:
            minimal_dict.set_version("1.2.a")
            raise AMIDictError("should catch bad version error")
        except AMIDictError as e:
            """should catch bad version"""
            # print(f"caught expected error")

    def test_create_dictionary_from_url(self):
        """lookup entry in Github repository
        note: depends on INTERNET"""
        mentha_url = "https://raw.githubusercontent.com/petermr/pyami/main/py4ami/resources/amidicts/mentha_tps.xml"
        mentha_dict = AmiDictionary.create_dictionary_from_url(mentha_url)
        assert len(mentha_dict.get_lxml_entries()) == 1
        assert mentha_dict.get_first_ami_entry().get_term() == "1,8-cineole synthase"
        assert mentha_dict.get_version() == "0.0.3"

    def test_dict_has_xml_title(self):
        """has root dictionary element got title attribute?
        e.g. <dictionary title='dict1'> ..."""
        setup_dict = self.setup()
        root = setup_dict[ROOT]
        assert root.attrib[TITLE] == "dict1"

    def test_dict_title_matches_filename(self):
        setup_dict = self.setup()
        root = setup_dict[ROOT]
        last_path = setup_dict[DICTFILE1].stem
        print(last_path)
        assert root.attrib["title"] == last_path

    def test_title_from_url_stem(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.url = "https://some.where/foo/bar.xml"
        assert amidict.root.attrib[TITLE] == "minimal"  # needs fixing

    def test_title_from_file_stem(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.file = "/user/me/foo.xml"
        assert amidict.root.attrib[TITLE] == "minimal"

    def test_dict_has_root_dictionary(self):
        setup_dict = self.setup()
        root = setup_dict[ROOT]
        assert root.tag == AmiDictionary.TAG

    def test_dict_contains_xml_element(self):
        root = etree.parse(str(self.setup()[DICTFILE1]))
        assert root is not None

    def test_can_read_url(self):

        url = PLANT_PART_RAW_DICT_URL
        tree = XmlLib.parse_url_to_tree(url)
        descendants = tree.getroot().xpath('.//*')
        assert 730 >= len(descendants) >= 720

    def test_dictionary_has_xml_declaration_with_encoding(self):
        """Checks dictionary has encoding of 'UTF-8' and XML Version 1.0
        USEFUL 2022-07"""
        dicts = [ETHNOBOT_DICT, DICTFILE1, ]
        print()
        for dikt in dicts:
            print(f"...{dikt}")
            root = etree.parse(str(self.setup()[dikt]))
            dictionary = AmiDictionary.create_from_xml_object(root)
            validator = AmiDictValidator(dictionary)
            error_list = validator.get_xml_declaration_error_list()
            assert not error_list

    def test_validate_url_dict(self):
        """tests that historic dictionaries read into validator"""
        urllist = [
            PLANT_PART_RAW_DICT_URL,
            ANALYSIS_METHOD_RAW_DICT_URL,
            COMPOUND_RAW_DICT_URL
        ]
        for url in urllist:
            print(f"url: {url}")
            tree = XmlLib.parse_url_to_tree(url)
            dictionary = AmiDictionary.create_from_xml_object(tree)
            validator = AmiDictValidator(dictionary)
            error_list = validator.get_error_list()
            assert not error_list

    # def test_dictionary_has_xml_declaration_with_encoding_method(self):
    #     amidict = AmiDictionary.create_from_xml_file(self.setup()[DICTFILE1])
    #     amidict.has_xml_declaration_with_utf8()

    # AmiDictionary

    def test_can_create_ami_dict_from_file(self):
        """read an existing XML AmiDictionary"""
        setup_dict = self.setup()
        one_entry_path = setup_dict[ONE_ENTRY_PATH]
        amidict = AmiDictionary.create_from_xml_file(one_entry_path)
        assert amidict is not None

    def test_dictionary_is_an_ami_dictionary(self):
        setup_dict = self.setup()
        amidict = setup_dict[ONE_ENTRY_DICT]
        assert type(amidict) is AmiDictionary

    def test_dictionary_get_entries(self):
        setup_dict = self.setup()
        amidict = setup_dict[ONE_ENTRY_DICT]
        entries = amidict.get_lxml_entries()
        assert entries is not None

    def test_dictionary_contains_one_entry(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_entry_count() == 1, f"dict should have 1 entry, found  {amidict.get_entry_count()}"

    def test_get_first_entry(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_first_ami_entry() is not None

    def test_get_attribute_names(self):
        first_entry = self.setup()[ONE_ENTRY_DICT].get_first_ami_entry()
        assert type(first_entry) is AmiEntry
        attrib_names = {name for name in first_entry.element.attrib}
        assert attrib_names is not None

    def test_get_term_of_first_entry(self):
        """
        tests that we can retrieve the `name` value from an element
        Also
        """
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_first_entry().attrib[TERM] == "Douglas Adams"

    def test_get_name_of_first_entry(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_first_entry().attrib[NAME] == "Douglas Adams"

    def test_get_wikidata_of_first_entry(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_first_entry().attrib[WIKIDATA_ID] == "Q42"

    def test_get_synonym_count(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert type(amidict) is AmiDictionary
        assert len(amidict.get_first_ami_entry().get_synonyms()) == 2

    def test_get_synonym_by_language(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert type(amidict) is AmiDictionary
        elem = amidict.get_first_ami_entry().get_synonym_by_language(LANG_UR).element
        assert "ڈگلس ایڈمس" == ''.join(elem.itertext())

    def test_dictionary_creation(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        assert amidict is not None
        assert amidict.get_version() == STARTING_VERSION

    def test_add_entry_with_term_to_zero_entry_dict(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        entry = amidict.create_and_add_entry_with_term("foo")
        assert etree.tostring(entry) == b'<entry term="foo"/>'
        assert etree.tostring(
            amidict.root) == b'<dictionary title="minimal" version="0.0.1"><entry term="foo"/></dictionary>'
        assert amidict.get_entry_count() == 1

    def test_add_two_entry_with_term_to_zero_entry_dict(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        entry_foo = amidict.add_entry_element("foo")
        entry_bar = amidict.add_entry_element("bar")
        assert etree.tostring(entry_bar) == b'<entry name="bar" term="bar"/>'
        assert etree.tostring(
            amidict.root) == b'<dictionary title="minimal" version="0.0.1"><entry name="foo" term="foo"/><entry name="bar" term="bar"/></dictionary>'
        assert amidict.get_entry_count() == 2

    def test_add_list_of_entries_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        term_count = len(terms)
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.add_entries_from_words(terms)
        assert amidict.get_entry_count() == term_count

    def test_find_entry_after_add_list_of_entries_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.add_entries_from_words(terms)
        entry_bar = amidict.get_lxml_entry("bar")
        assert entry_bar is not None

    def test_fail_on_missing_entry_after_add_list_of_entries_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.add_entries_from_words(terms)
        entry_zilch = amidict.get_lxml_entry("zilch")
        assert entry_zilch is None, f"missing entry returns None"

    def test_add_second_list_of_entries_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.add_entries_from_words(terms)
        terms1 = ["wibble", "wobble"]
        amidict.add_entries_from_words(terms1)
        assert amidict.get_entry_count() == len(terms) + len(terms1)

    def test_add_list_of_entries_from_list_of_string_with_duplicates_and_replace(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "bar"]
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.add_entries_from_words(terms, duplicates="replace")
        assert amidict.get_entry_count() == 4, f"'bar' should be present"

    def test_add_list_of_entries_from_list_of_string_with_duplicates_and_no_replace(self):
        """add list of terms which contains duplicate and raise error"""
        terms = ["foo", "bar", "plugh", "xyzzy", "bar"]
        amidict = AmiDictionary.create_minimal_dictionary()
        try:
            amidict.add_entries_from_words(terms, duplicates="error")
            assert False, f"AMIDict duplicate error (bar) should have been thrown"
        except AMIDictError:
            assert True, "error should have been throwm"
        assert amidict.get_entry_count() == 4, f"'bar' should be present"

    def test_add_then_remove_entry_and_replace(self):
        """create new entry , then delete, then re-add"""
        amidict, _ = AmiDictionary.create_dictionary_from_words(["foo", "bar", "plugh", "xyzzy"])
        assert amidict.get_entry_count() == 4
        amidict.delete_entry_by_term("bar")
        assert amidict.get_entry_count() == 3, f"entry 'bar' should have been removed"
        amidict.create_and_add_entry_with_term("bar")
        assert amidict.get_entry_count() == 4, f"entry 'bar' should have been re-added"

    # find entries
    def test_find_entry_by_term(self):
        """searches for entry by value of term"""
        amidict = _create_amidict_with_foo_bar_entries()
        entry = amidict.get_lxml_entry("foo")
        assert entry is not None
        assert entry.attrib[TERM] == "foo", f"should retrieve entry with term 'foo'"

    def test_find_entry_by_term_bar(self):
        amidict = _create_amidict_with_foo_bar_entries()
        entry = amidict.get_lxml_entry("bar")
        assert entry is not None

    def test_find_entry_by_term_zilch(self):
        amidict = _create_amidict_with_foo_bar_entries()
        entry = amidict.get_lxml_entry("zilch")
        assert entry is None

    def test_delete_entry_by_term_foo(self):
        amidict = _create_amidict_with_foo_bar_entries()
        print(f"amidict0 {lxml.etree.tostring(amidict.root)}")
        amidict.delete_entry_by_term("foo")
        print(f"amidict1 {lxml.etree.tostring(amidict.root)}")
        assert amidict.get_entry_count() == 1

    def test_delete_entry_by_term_foo_and_re_add(self):
        amidict = _create_amidict_with_foo_bar_entries()
        amidict.delete_entry_by_term("foo")
        amidict.create_and_add_entry_with_term("foo")
        assert amidict.get_entry_count() == 2

    def test_create_and_add_entry_with_term(self):
        term = "foo"
        amidict = AmiDictionary.create_minimal_dictionary()
        assert amidict.get_entry_count() == 0
        amidict.create_and_add_entry_with_term(term)
        assert amidict.get_entry_count() == 1
        entry = amidict.get_ami_entry(term)
        assert type(entry) is AmiEntry
        assert term == entry.get_term()

    def test_create_and_overwrite_entry_with_duplicate_term(self):
        term = "foo"
        amidict = AmiDictionary.create_minimal_dictionary()
        assert amidict.get_entry_count() == 0
        entry = amidict.create_and_add_entry_with_term(term)
        print(f"entry: {type(entry)}")
        assert isinstance(entry, _Element)
        AmiEntry.add_name(entry, "foofoo")
        amidict.create_and_add_entry_with_term(term, replace=True)
        assert amidict.get_entry_count() == 1
        entry = amidict.get_lxml_entry(term)
        assert type(entry) is _Element

        assert term == entry.attrib[TERM]
        assert NAME not in entry.attrib

    def test_create_and_fail_on_add_entry_with_duplicate_term(self):
        term = "foo"
        amidict = AmiDictionary.create_minimal_dictionary()
        entry = amidict.create_and_add_entry_with_term(term)
        try:
            amidict.create_and_add_entry_with_term(term, replace=False)
            assert False, f"should fail with duplicate entry"
        except AMIDictError as e:
            assert True, "should raise duplicate error"

    def test_create_and_overwrite_duplicate_term(self):
        term = "foo"
        amidict = AmiDictionary.create_minimal_dictionary()
        ami_entry = AmiEntry.create_from_element(amidict.create_and_add_entry_with_term(term))
        assert ami_entry.get_name() is None
        ami_entry.set_name("bar")
        assert ami_entry.get_name() == "bar"
        try:
            amidict.create_and_add_entry_with_term(term, replace=True)
            assert True, f"should overwrite duplicate entry"
        except AMIDictError as e:
            assert True, "should not raise duplicate error"

    # dictionary tests
    def test_minimal_dictionary(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        assert amidict.get_version() is not None
        # amidict.check_validity()
        amidict.remove_attribute(VERSION)
        if amidict.get_version() is not None:
            raise AMIDictError("should have removed version")

        try:
            amidict.check_validity()
            raise AMIDictError("should fail is_valid()")
        except Exception as e:
            logging.info(f"failed test {e}")

    def test_get_duplicate_entries(self):
        """Dictionary has two entries for 'apical' but only one for 'cone'"""
        dup_dict = AmiDictionary.create_from_xml_file(self.setup()[DUPLICATE_ENTRIES])
        entries = dup_dict.get_lxml_entries()
        assert len(entries) == 4, "one duplicate term omitted"
        entries = dup_dict.find_entries_with_term("apical")
        assert entries is not None and len(entries) == 1
        entries = dup_dict.find_entries_with_term("zilch")
        assert entries is not None and len(entries) == 0

    def test_get_terms_from_valid_dictionary(self):
        """ETHNOBOT has no multiple entries'"""
        ethno_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        terms = ethno_dict.get_terms()
        assert terms is not None
        assert len(terms) == 8
        assert terms == ['anti-fumitory', 'adaptogen', 'homeopathy variable agent', 'ethnomedicinal agent',
                         'phytochemical agent', 'phytomedical agent', 'plant-extracted agent', 'lung-tonifying agent']

    def test_get_terms_from_invalid_dictionary(self):
        """DUPLICATE_ENTRIES has two entries for 'apical' and some missing terms"""
        dup_dict = AmiDictionary.create_from_xml_file(self.setup()[DUPLICATE_ENTRIES])
        terms = dup_dict.get_terms()
        assert terms == ['apical', 'flowering top', 'cone', 'pistil']

    # review dictionaries
    def test_mini_plant_part_is_valid(self):
        # pp_dict = AmiDictionary(setup_amidict[MINI_PLANT_PART])
        pp_dict = AmiDictionary.create_from_xml_file(self.setup()[MINI_PLANT_PART])
        if pp_dict is None:
            raise AMIDictError(f"test_dictionary_should_have_desc cannot read dictionary {pp_dict}")
        pp_dict.check_validity()

    def test_mini_mentha_tps_dict_is_valid(self):
        mentha_dict = AmiDictionary.create_from_xml_file(self.setup()[MINI_MENTHA])
        if mentha_dict is None:
            raise AMIDictError("cannot find/read mentha_dict")
        mentha_dict.check_validity()

    def test_ethnobot_dict_has_version(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        version = ethnobot_dict.get_version()
        assert version is not None
        assert AmiDictionary.is_valid_version_string(version)
        # assert ethnobot_dict.get_version() == "0.0.1"

    def test_ethnobot_dict_is_valid(self):
        print(f" validating {ETHNOBOT_DICT}")
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        ethnobot_dict.check_validity()
        # assert ethnobot_dict.get_version() == "0.0.1"

    def test_ethnobot_dict_has_8_entries(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        entries = ethnobot_dict.get_lxml_entries()
        assert len(entries) == 8

    def test_ethnobot_dict_entry_0_is_valid(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        entry0 = ethnobot_dict.get_lxml_entries()[0]
        AmiEntry.create_from_element(entry0).check_validity()

    def test_all_ethnobot_dict_entries_are_valid(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        for entry in ethnobot_dict.get_lxml_entries():
            AmiEntry.create_from_element(entry).check_validity()

    # integrations
    def test_create_dictionary_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        title = "foobar"
        directory = None
        amidict, _ = AmiDictionary.create_dictionary_from_words(terms, title)
        assert amidict is not None
        title = amidict.root.attrib[TITLE]
        assert title == "foobar"

    def test_create_dictionary_from_list_of_string_and_save(self):
        terms = ["acetone", "benzene", "chloroform", "DMSO", "ethanol"]
        temp_dir = Path(Resources.TEMP_DIR, "dictx")
        temp_dir.mkdir(exist_ok=True)
        assert os.path.exists(temp_dir), f"{temp_dir} exists"
        title = "solvents"
        tempfile = Path(temp_dir, title + ".xml")
        amidict, dictfile = AmiDictionary.create_dictionary_from_words(terms, title=title, outdir=temp_dir)
        assert dictfile is not None and os.path.exists(dictfile)

    def test_create_dictionary_from_list_of_string_save_and_compare(self):
        terms = ["acetone", "benzene", "chloroform", "DMSO", "ethanol"]
        temp_dir = Path(Resources.TEMP_DIR, "dictxx")
        amidict, dictfile = AmiDictionary.create_dictionary_from_words(terms, title="solvents", outdir=temp_dir)
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
        # assert text1 == dict_text, f"{text1} != {dict_text}"
        # TODO remove user from metadata

    # @unittest.skip("LONG")
    def test_create_dictionary_from_list_of_string_and_add_wikidata(self):
        terms = ["acetone",
                 "chloroform",
                 # "DMSO",
                 # "ethanol"
                 ]
        amidict, _ = AmiDictionary.create_dictionary_from_words(terms, title="solvents", wikidata=True)
        temp_dir = Path(Resources.TEMP_DIR, "dict_xxx")
        dictfile = amidict.write_to_dir(temp_dir)

        with open(dictfile, "r") as f:
            dict_text = f.read()
        dict_text = re.sub("date=\"[^\"]*\"", "date=\"TODAY\"", dict_text)

        # note, the date is stripped as it changes with each run
        text1 = """<dictionary version="0.0.1" title="solvents" encoding="UTF-8">
      <metadata user="pm286" date="TODAY"/>
      <entry term="acetone" wikidataID="Q49546" description="chemical compound"/>
      <entry term="chloroform" wikidataID="Q172275" description="chemical compound"/>
    </dictionary>
    """
        # assert text1 == dict_text, f"{text1} != {dict_text}"
        # TODO remove user from metadata

    def test_find_missing_wikidata_ids(self):
        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        lxml_entries = ami_dict.get_lxml_entries_with_missing_wikidata_ids()
        # missing_wikidata_ids = AmiEntry.get_wikidata_ids_for_entries(_entries)
        missing_wikidata_terms = AmiEntry.get_terms_for_lxml_entries(lxml_entries)
        assert missing_wikidata_terms == [
            'FAQs',
            'CBEs',
            'EET',
            'GHG',
            'GWP100',
            'UNFCCC',
            'GDP',
            'HFCs',
            'HCFCs',
            'CRF',
            'WMO',
            'NGHGI',
            'GWP',
            'FFI',
            'PBEs',
            'TCBA',
            'HCEs',
            'EBEs',
            'IBE',
            'RSD',
            'HDI',
            'CSP',
            'BECCS',
            'IAMs',
            'CDR',
            'ECR',
            'ETSs',
            'EVs',
            'ODSs',
            'HCS'
        ]

    def test_disambiguate_raw_wikidata_ids_in_dictionary(self):
        """
        find
        USABLE
        """
        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        _term_id_list = ami_dict.get_disambiguated_raw_wikidata_ids()
        assert len(_term_id_list) == 3
        assert _term_id_list[0] == ('GHG', ['Q167336'])

    @unittest.skipUnless(VERYLONG, "lookup whole dictionaries")
    def test_lookup_missing_abbreviation_wikidata_ids_by_name(self):
        """
        scans dictionary for missing @wikidataID and searches wikidata by name/term
        USEFUL
        """
        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        lookup = ami_dict.lookup_missing_wikidata_ids()
        pprint.PrettyPrinter(indent=4).pprint(lookup.hits_dict)
        assert len(lookup.hits_dict) == 17
        """{   'Electric vehicles': {   'Q13629441': 'electric vehicle',
                             'Q17107666': 'Miles Electric Vehicles',
                             'Q1720353': 'Smith Electric Vehicles',
                             'Q5029961': 'Canadian Electric Vehicles',
                             'Q67371583': 'John Bradshaw Ltd.'},
    'Frequently Asked Questions': {   'Property:P9214': 'FAQ URL',
                                      'Q189293': 'FAQ',
                                      'Q76407407': 'Ffatrïoedd a busnesau a '
                                                   'gynorthwyir : cwestiynau '
                                                   'cyffredin = Supported '
                                                   'factories and businesses : '
                                                   'frequently asked '
                                                   'questions'},
    'Global Warming Potential': {'Property:P2565': 'global warming potential'},
    'Greenhouse Gas': {   'Q107315539': 'Greenhouse Gas Mitigation Workshop '
                                        '(2016)',
                          'Q167336': 'greenhouse gas',
                          'Q5604172': 'greenhouse gas emissions by the United '
                                      'Kingdom'},
"""

    @unittest.skipUnless(VERYLONG, "runs several chapters")
    def test_debug_chapter_dictionaries(self):
        self.debug_dict(dict_path=Resources.IPCC_CHAP07_ABB_DICT)
        self.debug_dict(dict_path=Resources.IPCC_CHAP07_MAN_DICT)
        self.debug_dict(dict_path=Resources.IPCC_CHAP08_ABB_DICT)
        self.debug_dict(dict_path=Resources.IPCC_CHAP08_MAN_DICT)

    @classmethod
    def debug_dict(cls, dict_path):
        print(f"======={dict_path}=======")
        ami_dict = AmiDictionary.create_from_xml_file(dict_path)
        if ami_dict:
            lookup = ami_dict.lookup_missing_wikidata_ids()
            pprint.PrettyPrinter(indent=4).pprint(lookup.hits_dict)
        else:
            print(f"****Cannot find valid dict {dict_path}****")
            logging.error(f"Cannot find valid dict {dict_path}")

    @unittest.skipUnless(VERYLONG, "lookup whole dictionaries")
    def test_lookup_missing_manual_wikidata_ids_by_name(self):
        """
        scans dictionary for missing @wikidataID and searches wikidata by name/term
        USEFUL
        """
        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP07_MAN_DICT)
        lookup = ami_dict.lookup_missing_wikidata_ids()
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(lookup.hits_dict)
        assert 8 >= len(lookup.hits_dict) >= 6

    @unittest.skipUnless(VERYLONG, "lookup whole dictionaries")
    def test_lookup_missing_wikidata_ids_by_term(self):
        """
        scans dictionary for missing @wikidataID and searches wikidata by term
        USEFUL
        """
        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        lookup = ami_dict.lookup_missing_wikidata_ids(lookup_string=TERM)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(lookup.hits_dict)
        assert 28 >= len(lookup.hits_dict) >= 22

    # {
    #     {'BECCS': {'Q146790': 'Aomori',
    #                'Q209727': 'palmitic acid',
    #                'Q455712': 'Domenico di Pace Beccafumi',
    #                'Q472237': 'Nikolaos Gyzis',
    #                'Q507854': 'Karlstadt am Main'},
    #      'CBEs': {'Q1391': 'Maryland',
    #               'Q227': 'Azerbaijan',
    #               'Q7024': 'Lugano',
    #               'Q8093': 'Nintendo',
    #               'Q884': 'South Korea'},
    #      'WMO': {'Property:P4136': 'WIGOS station ID',
    #              'Property:P5956': 'War Memorials Online ID',
    #              'Property:P9737': 'WMO code',
    #              'Q170424': 'World Meteorological Organization',
    #              'Q4468436': 'White Mountain Airport'}}
    #     }

    # =====helpers======

    def teardown(self):
        dict1_root = None


class TestSearchDictionary:

    def test_parse_wikidata_page(self):
        qitem = "Q144362"  # azulene
        wpage = WikidataPage(qitem)
        # note "zz" has no entries
        ahref_dict = wpage.get_wikipedia_page_links(["en", "de", "zz"])
        assert ahref_dict == {'en': 'https://en.wikipedia.org/wiki/Azulene',
                              'de': 'https://de.wikipedia.org/wiki/Azulen'}

    @unittest.skip("LONG DOWNLOAD")
    def test_create_dictionary_terpenes(self):
        words = ["limonene", "alpha-pinene", "Lantana camara"]
        description = "created from words"
        title = "test"
        dictionary, _ = AmiDictionary.create_dictionary_from_words(words, title=title, desc=description, wikidata=True)
        assert len(dictionary.entries) == 3

    def test_get_property_ids(self):
        """gets properties af a dictionary entry"""
        words = ["limonene"]
        dictionary, _ = AmiDictionary.create_dictionary_from_words(words, "test", "created from words",
                                                                   wikilangs=["en", "de"])
        dictionary.add_wikidata_from_terms()
        pprint.pprint(lxml.etree.tostring(dictionary.root).decode("UTF-8"))
        assert len(dictionary.entries) == 1
        wikidata_page = dictionary.create_wikidata_page(dictionary.entries[0])
        property_ids = wikidata_page.get_property_ids()
        assert len(property_ids) >= 60
        assert property_ids[:10] == ['P31', 'P279', 'P361', 'P2067', 'P274', 'P233',
                                     'P2054', 'P2101', 'P2128', 'P2199']

    def test_create_dictionary_from_sparql(self):
        PLANT = os.path.join(PHYSCHEM_RESOURCES, "plant")
        sparql_file = os.path.join(PLANT, "plant_part_sparql.xml")
        dictionary_file = os.path.join(PLANT, "eoplant_part.xml")
        """
        <result>
            <binding name='item'>
                <uri>http://www.wikidata.org/entity/Q2923673</uri>
            </binding>
            <binding name='image'>
                <uri>http://commons.wikimedia.org/wiki/Special:FilePath/White%20Branches.jpg</uri>
            </binding>
        </result>
"""
        sparql_to_dictionary = {
            "id_name": "item",
            "sparql_name": "image",
            "dict_name": "image",
        }
        dictionary = AmiDictionary.create_from_xml_file(dictionary_file)
        wikidata_sparql = WikidataSparql(dictionary)
        wikidata_sparql.update_from_sparql(sparql_file, sparql_to_dictionary)
        outdir = Path(Resources.TEMP_DIR, "sparql")
        if not outdir.exists():
            outdir.mkdir()
        # ff = dictionary_file[:-(len(".xml"))] + "_update" + ".xml"
        # print("saving to", ff)
        dictionary.write_to_dir(outdir)

    def test_invasive(self):
        """
        """

        INVASIVE_DIR = os.path.join(CEV_OPEN_DICT_DIR, "invasive_species")
        assert (os.path.exists(INVASIVE_DIR))
        dictionary_file = os.path.join(INVASIVE_DIR, "invasive_plant.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(INVASIVE_DIR, "sparql_output")
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql_*.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "image_link",
                "dict_name": "image",
            },
            "map": {
                "id_name": "item",
                "sparql_name": "taxon_range_map_image",
                "dict_name": "image",
            },
            # "taxon": {
            #     "id_name": "item",
            #     "sparql_name": "taxon",
            #     "dict_name": "synonym",
            # }
        }
        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)
        # TODO needs assert

    # LONG
    @unittest.skip("VERY LONG, SPARQL")
    def test_plant_genus(cls):
        """
        """

        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "plant_genus")
        assert (os.path.exists(DICT_DIR))
        dictionary_file = os.path.join(DICT_DIR, "plant_genus.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(DICT_DIR, "raw")
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql_test_concatenation.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "plant_genus",
                "sparql_name": "images",
                "dict_name": "image",
            },
            "map": {
                "id_name": "plant_genus",
                "sparql_name": "taxon_range_map_image",
                "dict_name": "map",
            },
            "wikipedia": {
                "id_name": "plant_genus",
                "sparql_name": "wikipedia",
                "dict_name": "wikipedia",
            },
        }
        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    def test_compound(cls):
        """
        """

        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoCompound")
        assert (os.path.exists(DICT_DIR))
        dictionary_file = os.path.join(DICT_DIR, "plant_compound.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(DICT_DIR, "raw")
        SPARQL_DIR = DICT_DIR
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql_6.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "t",
                "dict_name": "image",
            },
            "chemform": {
                "id_name": "item",
                "sparql_name": "chemical_formula",
                "dict_name": "chemical_formula",
            },
            "wikipedia": {
                "id_name": "plant_genus",
                "sparql_name": "wikipedia",
                "dict_name": "wikipedia",
            },
            # "taxon": {
            #     "id_name": "item",
            #     "sparql_name": "taxon",
            #     "dict_name": "taxon",
            # }
        }

        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    def test_plant_part(cls):
        """
        Takes WD-SPARQL-XML output (sparql.xml) and maps to AMIDictionary (eo_plant_part.xml)

        """
        # current dictionary does not need updating

        print(f"***test_plant_part")
        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoPlantPart")
        DICT_DIR = Path(TEST_RESOURCE_DIR, "eoPlantPart")
        assert os.path.exists(DICT_DIR), f"{DICT_DIR} should exist"
        dictionary_file = os.path.join(DICT_DIR, "eoplant_part.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(DICT_DIR, "raw")
        SPARQL_DIR = DICT_DIR
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "image",
                "dict_name": "image",
            },
        }

        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    def test_merge_dicts_ipcc_same_chap(self):
        """test merge dictionaries from IPCC (heavy commonality)"""

        abb2_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        abb2_set = abb2_dict.get_or_create_term_set()
        assert abb2_set == {
            'BECCS', 'CBEs', 'CDR', 'CRF', 'CSP',
            'EBEs', 'ECR', 'EET', 'ETSs',
            'EU ETS', 'EVs', 'F-gases', 'FAQs',
            'FFI', 'GDP', 'GHG', 'GTP',
            'GWP', 'GWP100', 'HCEs', 'HCFCs',
            'HCS', 'HDI', 'HFCs', 'IAMs',
            'IBE', 'LULUCF', 'NGHGI', 'ODSs',
            'PBEs', 'PFCs', 'RGGI', 'RSD',
            'TCBA', 'UNFCCC', 'WMO'
        }, f"abb2 set {abb2_set}"

        man2_dict = AmiDictionary.create_from_xml_file(Path(Resources.IPCC_CHAP02_DICT, "ip_3_2_emissions_man.xml"))
        man2_set = man2_dict.get_or_create_term_set()
        assert man2_set == {
            'CAIT', 'CEDS', 'CGTP', 'CO2-equivalent emission',
            'CRF', 'EDGAR', 'FAOSTAT', 'FFI', 'FOLU', 'Final Energy Demand', 'GTP', 'GWP',
            'GWP100', 'GtCO2eq', 'LULUCF', 'NMVOC',
            'PRIMAP', 'Paris Agreement', 'Primary Energy', 'Primary Energy Conversion',
            'SLCF', 'SRES', 'SSP', 'UNFCCC', 'WMO',
            'atmospheric lifetime', 'baseline scenario',
            'carbon budget', 'carbon pricing',
            'cumulative CO2 emissions', 'demand side solutions',
            'emission inventory', 'emission sectors',
            'emissions factor', 'emissions trajectory',
            'fluorinated gas', 'social discount rate',
            'top down atmospheric measurement'
        }, f"man2 set {man2_set}"

        # phrases
        phr2_dict = AmiDictionary.create_from_xml_file(Path(Resources.IPCC_CHAP02_DICT, "ip_3_2_emissions_phr.xml"))
        phr2_set = phr2_dict.get_or_create_term_set()
        assert phr2_set == {
            'BECCS', 'CBEs', 'CDR', 'CRF', 'CSP', 'EBEs', 'ECR', 'EET',
            'ETSs', 'EU ETS', 'EVs', 'F-gases',
            'FAQs', 'FFI', 'GDP', 'GHG', 'GTP', 'GWP', 'GWP-100', 'GWP100',
            'HCEs', 'HCFCs', 'HCS', 'HDI', 'HFCs', 'IAMs', 'IBE', 'LULUCF',
            'NGHGI', 'ODSs', 'PBEs', 'PFCs', 'RGGI', 'RSD', 'TCBA', 'UNFCCC', 'WMO'
        }

        # terms common to abbrev and manual
        abb_man_set = abb2_set.intersection(man2_set)
        assert len(abb_man_set) == 8, f"man2 set {len(abb_man_set)}"
        assert abb_man_set == {
            'GTP', 'FFI', 'GWP', 'UNFCCC', 'WMO', 'GWP100', 'CRF', 'LULUCF'}


def main(argv=None):
    print(f"running PDFArgs main")
    pdf_args = AmiDictArgs()
    try:
        pdf_args.parse_and_process()
    except Exception as e:
        print(f"***Cannot run pyami***; see output for errors: {e}")


if __name__ == "__main__":
    main()
else:
    pass


def main():
    pass
