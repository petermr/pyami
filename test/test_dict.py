import logging
import os
import pprint
import re
from pathlib import Path

from lxml.etree import XMLSyntaxError, _Element
import lxml
from lxml import etree
import glob
import unittest

# local
from py4ami.ami_dict import AmiDictionary, AmiEntry, AmiDictArgs, AMIDictError, \
    AmiDictValidator, NAME, TITLE, TERM, LANG_UR, VERSION, WIKIDATA, WIKIDATA_ID
from py4ami.wikimedia import WikidataSparql, WikidataPage
from py4ami.xml_lib import XmlLib
from py4ami.constants import PHYSCHEM_RESOURCES, CEV_OPEN_DICT_DIR
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

    def test_dictionary_file1_exists(self):
        """Test that a simple dictionary "dictfile1" file exists"""
        setup_dict = self.setup()
        assert setup_dict[DICTFILE1].exists(), f"file should exist {setup_dict['dict1']}"
        self.teardown()

    def test_read_wellformed_dictionary(self):
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
        mentha_url = "https://raw.githubusercontent.com/petermr/pyami/main/py4ami/resources/amidicts/mentha_tps.xml"
        mentha_dict = AmiDictionary.create_dictionary_from_url(mentha_url)
        assert len(mentha_dict.get_entries()) == 1
        assert mentha_dict.get_first_ami_entry().get_term() == "1,8-cineole synthase"
        assert mentha_dict.get_version() == "0.0.3"

    def test_dict_has_xml_title(self):
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
        assert amidict.root.attrib[TITLE] == "minimal" # needs fixing

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
        assert 730 >= len(descendants)  >= 720

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
        entries = amidict.get_entries()
        assert entries is not None

    def test_dictionary_contains_at_least_one_entry(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_entry_count() > 0

    def test_get_first_entry(self):
        amidict = self.setup()[ONE_ENTRY_DICT]
        assert amidict.get_first_ami_entry() is not None

    def test_get_attribute_names(self):
        first_entry = self.setup()[ONE_ENTRY_DICT].get_first_ami_entry()
        assert type(first_entry) is AmiEntry
        attrib_names = {name for name in first_entry.element.attrib}
        assert attrib_names is not None

    def test_get_term_of_first_entry(self):
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

    # # add entry to existing dict
    # def test_add_entry_to_zero_entry_dict(self):
    #     amidict = AmiDictionary.create_minimal_dictionary()
    #     entry = amidict.create_and_add_entry()
    #     assert b'<entry/>' == etree.tostring(entry.element)
    #     assert b'<dictionary version="0.0.1" title="minimal" encoding="UTF-8"><entry/></dictionary>' \
    #            == etree.tostring(amidict.element)
    #     assert amidict.get_entry_count() == 1

    def test_add_entry_with_term_to_zero_entry_dict(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        entry = amidict.create_and_add_entry_with_term("foo")
        assert etree.tostring(entry) == b'<entry term="foo"/>'
        assert etree.tostring(amidict.root) == b'<dictionary title="minimal" version="0.0.1"><entry term="foo"/></dictionary>'
        assert amidict.get_entry_count() == 1

    def test_add_two_entry_with_term_to_zero_entry_dict(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        entry_foo = amidict.add_entry_element("foo")
        entry_bar = amidict.add_entry_element("bar")
        assert etree.tostring(entry_bar) == b'<entry name="bar" term="bar"/>'
        assert etree.tostring(amidict.root) == b'<dictionary title="minimal" version="0.0.1"><entry name="foo" term="foo"/><entry name="bar" term="bar"/></dictionary>'
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
        entry_bar = amidict.get_entry("bar")
        assert entry_bar is not None

    def test_fail_on_missing_entry_after_add_list_of_entries_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        amidict = AmiDictionary.create_minimal_dictionary()
        amidict.add_entries_from_words(terms)
        entry_zilch = amidict.get_entry("zilch")
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
        amidict,_ = AmiDictionary.create_dictionary_from_words(["foo", "bar", "plugh", "xyzzy"])
        assert amidict.get_entry_count() == 4
        amidict.delete_entry_by_term("bar")
        assert amidict.get_entry_count() == 3, f"entry 'bar' should have been removed"
        amidict.create_and_add_entry_with_term("bar")
        assert amidict.get_entry_count() == 4, f"entry 'bar' should have been re-added"

    # find entries
    def test_find_entry_by_term(self):
        """searches for entry by value of term"""
        amidict = self._create_amidict_with_foo_bar_entries()
        entry = amidict.get_entry("foo")
        assert entry is not None
        assert entry.attrib[TERM] == "foo", f"should retrieve entry with term 'foo'"

    def test_find_entry_by_term_bar(self):
        amidict = self._create_amidict_with_foo_bar_entries()
        entry = amidict.get_entry("bar")
        assert entry is not None

    def test_find_entry_by_term_zilch(self):
        amidict = self._create_amidict_with_foo_bar_entries()
        entry = amidict.get_entry("zilch")
        assert entry is None

    def test_delete_entry_by_term_foo(self):
        amidict = self._create_amidict_with_foo_bar_entries()
        print(f"amidict0 {lxml.etree.tostring(amidict.root)}")
        amidict.delete_entry_by_term("foo")
        print(f"amidict1 {lxml.etree.tostring(amidict.root)}")
        assert amidict.get_entry_count() == 1

    def test_delete_entry_by_term_foo_and_re_add(self):
        amidict = self._create_amidict_with_foo_bar_entries()
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
        # assert entry.get_name() is "foofoo"
        amidict.create_and_add_entry_with_term(term, replace=True)
        assert amidict.get_entry_count() == 1
        # entry = amidict.find_entry_with_term(term)
        entry = amidict.get_entry(term)
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
        entry = amidict.create_and_add_entry_with_term(term)
        assert AmiEntry.get_name(entry) is None
        AmiEntry.add_name(entry, "bar")
        assert AmiEntry.get_name(entry) == "bar"
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

    def test_dictionary_forbidden_attributes(self):
        pass

    def test_get_duplicate_entries(self):
        """Dictionary has two entries for 'apical' but only one for 'cone'"""
        dup_dict = AmiDictionary.create_from_xml_file(self.setup()[DUPLICATE_ENTRIES])
        entries = dup_dict.get_entries()
        assert len(entries) == 4, "one duplicate term omitted"
        # entry = dup_dict.get_entry("cone")
        # assert entry is not None
        # entries = dup_dict.find_entries_with_term("cone")
        # assert entries is not None and len(entries) == 1
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
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        ethnobot_dict.check_validity()
        # assert ethnobot_dict.get_version() == "0.0.1"

    def test_ethnobot_dict_has_8_entries(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        entries = ethnobot_dict.get_entries()
        assert len(entries) == 8

    def test_ethnobot_dict_entry_0_is_valid(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        entry0 = ethnobot_dict.get_entries()[0]
        AmiEntry.create_from_element(entry0).check_validity()

    def test_all_ethnobot_dict_entries_are_valid(self):
        ethnobot_dict = AmiDictionary.create_from_xml_file(self.setup()[ETHNOBOT_DICT])
        for entry in ethnobot_dict.get_entries():
            AmiEntry.create_from_element(entry).check_validity()

    # integrations
    def test_create_dictionary_from_list_of_string(self):
        terms = ["foo", "bar", "plugh", "xyzzy", "baz"]
        title = "foobar"
        directory = None
        amidict,_ = AmiDictionary.create_dictionary_from_words(terms, title)
        assert amidict is not None
        title = amidict.root.attrib[TITLE]
        assert title == "foobar"

    def test_create_dictionary_from_list_of_string_and_save(self):
        terms = ["acetone", "benzene", "chloroform", "DMSO", "ethanol"]
        temp_dir = Path(Path(__file__).parent.parent, "temp")
        assert os.path.exists(temp_dir), f"{temp_dir} exists"
        title = "solvents"
        tempfile = Path(temp_dir, title + ".xml")
        amidict, dictfile = AmiDictionary.create_dictionary_from_words(terms, title=title, outdir=temp_dir)
        assert dictfile is not None and os.path.exists(dictfile)

    def test_create_dictionary_from_list_of_string_save_and_compare(self):
        terms = ["acetone", "benzene", "chloroform", "DMSO", "ethanol"]
        temp_dir = Path(Path(__file__).parent.parent, "temp")
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

    def test_create_dictionary_from_list_of_string_and_add_wikidata(self):
        terms = ["acetone", "chloroform", "DMSO", "ethanol"]
        amidict,_ = AmiDictionary.create_dictionary_from_words(terms, title="solvents", wikidata=True)
        temp_dir = Path(Path(__file__).parent.parent, "temp")
        dictfile = amidict.write_to_dir(temp_dir)

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
        # assert text1 == dict_text, f"{text1} != {dict_text}"
        # TODO remove user from metadata

    # helpers
    def _create_amidict_with_foo_bar_entries(self):
        amidict = AmiDictionary.create_minimal_dictionary()
        entry_foo = amidict.create_and_add_entry_with_term("foo")
        entry_bar = amidict.create_and_add_entry_with_term("bar")
        return amidict

    # test helpers

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

    def test_create_dictionary_terpenes(self):
        words = ["limonene", "alpha-pinene", "Lantana camara"]
        description = "created from words"
        title = "test"
        dictionary,_ = AmiDictionary.create_dictionary_from_words(words, title=title, desc=description, wikidata=True)
        assert len(dictionary.entries) == 3

    def test_get_property_ids(self):
        """gets properties af a dictionary entry"""
        words = ["limonene"]
        dictionary,_ = AmiDictionary.create_dictionary_from_words(words, "test", "created from words",
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
        outdir = Path(Resources.TEMP_DIR,"sparql")
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


# class PDFArgs(AbstractArgs):
#     def __init__(self):
#         """arg_dict is set to default"""
#         super().__init__()
#
#
#
#     def create_arg_parser(self):
#         """creates adds the arguments for pyami commandline
#
#         """
#         self.parser = argparse.ArgumentParser(description='PDF parsing')
#         self.parser.add_argument("--maxpage", type=int, nargs=1, help="maximum number of pages", default=10)
#         self.parser.add_argument("--indir", type=str, nargs=1, help="input directory")
#         self.parser.add_argument("--inpath", type=str, nargs=1, help="input file")
#         self.parser.add_argument("--outdir", type=str, nargs=1, help="output directory")
#         self.parser.add_argument("--outform", type=str, nargs=1, help="output format ", default="html")
#         self.parser.add_argument("--flow", type=bool, nargs=1, help="create flowing HTML (heuristics)", default=True)
#         self.parser.add_argument("--imagedir", type=str, nargs=1, help="output images to imagedir")
#         self.parser.add_argument("--resolution", type=int, nargs=1, help="resolution of output images (if imagedir)",
#                                  default=400)
#         self.parser.add_argument("--template", type=str, nargs=1, help="file to parse specific type of document (NYI)")
#         self.parser.add_argument("--debug", type=str, choices=DEBUG_OPTIONS, help="debug these during parsing (NYI)")
#         return self.parser
#
#     # class PDFArgs:
#     def process_args(self):
#         """runs parsed args
#         :return:
#   --maxpage MAXPAGE     maximum number of pages
#   --indir INDIR         input directory
#   --infile INFILE [INFILE ...]
#                         input file
#   --outdir OUTDIR       output directory
#   --outform OUTFORM     output format
#   --flow FLOW           create flowing HTML (heuristics)
#   --images IMAGES       output images
#   --resolution RESOLUTION
#                         resolution of output images
#   --template TEMPLATE   file to parse specific type of document"""
#
#         if self.arg_dict:
#             fmt = self.arg_dict.get(OUTFORM)
#             print(f"fmt: {fmt}")
#             maxpage = self.arg_dict.get(MAXPAGE)
#             indir = self.arg_dict.get(INDIR)
#             inpath = self.arg_dict.get(INPATH)
#             outdir = self.arg_dict.get(OUTDIR)
#             outstem = self.arg_dict.get(OUTSTEM)
#             flow = self.arg_dict.get(FLOW) is not None
#             if not inpath:
#                 print(f"input file not given")
#             else:
#                 inpath = Path(inpath)
#                 if not inpath.exists():
#                     raise FileNotFoundError(f"input file does not exist: ({inpath}")
#                 self.convert_write(maxpage=maxpage, outdir=outdir, outstem=outstem, fmt=fmt, inpath=inpath, flow=True)
#
#     # class PDFArgs:
#     @classmethod
#     def convert_pdf(cls,
#                     path: str,
#                     fmt: str = "text",
#                     codec: str = "utf-8",
#                     password: str = "",
#                     maxpages: int = 0,
#                     caching: bool = True,
#                     pagenos: Container = set(),
#                     ) -> str:
#         """Summary
#         Parameters
#         ----------
#         path : str
#             Path to the pdf file
#         fmt : str, optional
#             Format of output, must be one of: "text", "html", "xml".
#             By default, "text" format is used
#         codec : str, optional
#             Encoding. By default "utf-8" is used
#         password : str, optional
#             Password
#         maxpages : int, optional
#             Max number of pages to convert. By default is 0, i.e. reads all pages.
#         caching : bool, optional
#             Caching. By default is True
#         pagenos : Container[int], optional
#             Provide a list with numbers of pages to convert
#         Returns
#         -------
#         str
#             Converted pdf file
#         """
#         """from pdfminer/pdfplumber"""
#         device, interpreter, retstr = PDFArgs.create_interpreter(fmt)
#         if not path:
#             raise FileNotFoundError("no input file given)")
#         try:
#             fp = open(path, "rb")
#         except FileNotFoundError as fnfe:
#             raise Exception(f"No input file given {fnfe}")
#
#         print(f"maxpages: {maxpages}")
#         for page in PDFPage.get_pages(
#                 fp,
#                 pagenos,
#                 maxpages=maxpages,
#                 password=password,
#                 caching=caching,
#                 check_extractable=True,
#         ):
#             interpreter.process_page(page)
#
#         text = retstr.getvalue().decode()
#         fp.close()
#         device.close()
#         retstr.close()
#         return text
#
#     # class PDFArgs:
#
#     @classmethod
#     def create_default_arg_dict(cls):
#         """returns a new COPY of the default dictionary"""
#         arg_dict = dict()
#         arg_dict[OUTFORM] = "html.flow"
#         arg_dict[MAXPAGE] = 5
#         arg_dict[INDIR] = None
#         arg_dict[INPATH] = None
#         arg_dict[OUTDIR] = None
#         arg_dict[OUTSTEM] = None
#         arg_dict[FLOW] = True
#         return arg_dict
#
#     @classmethod
#     def create_interpreter(cls, fmt, codec: str = "UTF-8"):
#         """creates a PDFPageInterpreter
#         :format: "text, "xml", "html"
#         :codec: default UTF-8
#         :return: (device, interpreter, retstr) device must be closed after reading, retstr
#         contains resultant str
#
#         Typical use:
#         device, interpreter, retstr = create_interpreter(format)
#
#         fp = open(path, "rb")
#         for page in PDFPage.get_pages(fp):
#             interpreter.process_page(page)
#
#         text = retstr.getvalue().decode()
#         fp.close()
#         device.close()
#         retstr.close()
#         return text
#
#         TODO convert to context manager?
#         """
#         rsrcmgr = PDFResourceManager()
#         retstr = BytesIO()
#         laparams = LAParams()
#         converters = {"text": TextConverter, "html": HTMLConverter, "flow.html": HTMLConverter, "xml": XMLConverter}
#         converter = converters.get(fmt)
#         if not converter:
#             raise ValueError(f"provide format, {converters.keys()}")
#         device = converter(rsrcmgr, retstr, codec=codec, laparams=laparams)
#         interpreter = PDFPageInterpreter(rsrcmgr, device)
#         return device, interpreter, retstr
#
#     # class PDFArgs:
#
#     def convert_write(self, fmt=None, maxpage=999999, outdir=None, outstem=None, inpath=None, flow=False,
#                       unwanteds=None):
#         """
#         create HTML (absolute or flowing) or XML
#         The preferred method is to use arg_dict
#         :param fmt: format html/xml/text
#         :param maxpage: if 0, writes all else staops at maxpages
#         :param outdir: output dir
#         :param outstem: stem of output file
#         :param inpath: input file
#         :param flow: remove absolute position so text can flow
#         """
#         if self.arg_dict:
#             maxp = self.arg_dict.get(MAXPAGE)
#             maxpage = int(maxp) if maxp else maxpage
#             outd = self.arg_dict.get(OUTDIR)
#             outdir = outd if outd else outdir
#             if not outdir:
#                 outs = self.arg_dict.get(OUTSTEM)
#                 outdir = outs if outs else outstem
#             inp = self.arg_dict.get(INPATH)
#             inpath = inp if inp else inpath
#             if fm := self.arg_dict.get(OUTFORM):
#                 fmt = fm
#             if fl := self.arg_dict.get(FLOW):
#                 flow = fl
#
#             # header_offset = -50
#             header_height = 90
#             # page_height = 892
#             # page_height_cm = 29.7
#             footer_height = 90
#
#         print(f"==============CONVERT================")
#         if fmt == "html.flow":
#             fmt = "html"
#             flow = True
#         if not inpath:
#             raise ValueError(f"no input file given")
#         inpath = Path(inpath)
#         if not inpath.exists():
#             raise FileNotFoundError(f"input file does not exist: ({inpath})")
#         result = PDFArgs.convert_pdf(path=inpath, fmt=fmt, maxpages=maxpage)
#
#         if flow:
#             tree = lxml.etree.parse(StringIO(result), lxml.etree.HTMLParser())
#             result_elem = tree.getroot()
#             HtmlUtil.add_ids(result_elem)
#             # this is slightly tacky
#             PDFUtil.remove_descendant_elements_by_tag("br", result_elem)
#             PDFUtil.remove_style(result_elem, [
#                 "position",
#                 # "left",
#                 "border",
#                 "writing-mode",
#                 "width",  # this disables flowing text
#             ])
#             PDFUtil.remove_empty_elements(result_elem, ["span"])
#             PDFUtil.remove_empty_elements(result_elem, ["div"])
#             PDFUtil.remove_lh_line_numbers(result_elem)
#             PDFUtil.remove_large_fonted_elements(result_elem)
#             marker_xpath = ".//div[a[@name]]"
#             offset, pagesize, page_coords = PDFUtil.find_constant_coordinate_markers(result_elem, marker_xpath)
#             PDFUtil.remove_headers_and_footers(result_elem, pagesize, header_height, footer_height, marker_xpath)
#             PDFUtil.remove_style_attribute(result_elem, "top")
#             PDFUtil.remove_style(result_elem, ["left", "height"])
#             PDFUtil.remove_unwanteds(result_elem, unwanteds)
#             PDFUtil.remove_newlines(result_elem)
#             self.markup_parentheses(result_elem)
#             print(f"ref_counter {self.ref_counter}")
#
#             HtmlTree.make_tree(result_elem, output_dir=outd, recs_by_section=RECS_BY_SECTION)
#
#             result = lxml.etree.tostring(result_elem).decode("UTF-8")
#             fmt = "flow.html"
#         if not outdir:
#             indir = Path(inpath).parent
#             outdir = indir
#             print(f"no outdir given, taking input {indir}")
#         if not outstem:
#             outstem = Path(inpath).stem
#         outfile = Path(outdir, f"{outstem}.{fmt}")
#         print(f"outfile {outfile}")
#         with open(str(outfile), "w") as f:
#             f.write(result)
#             print(f"wrote {f.name}")
#
#     # class PDFArgs:
#     def parse_and_process(self):
#         self.create_arg_parser()
#         if len(sys.argv) == 1:  # no args, print help
#             self.parser.print_help()
#         else:
#             self.parsed_args = self.parser.parse_args(sys.argv[1:])
#             self.arg_dict = self.create_arg_dict()
#             self.process_args()
#
#     def markup_parentheses(self, result_elem):
#         """iterate over parenthesised fields
#
#         """
#         xpath = ".//span"
#         spans = result_elem.xpath(xpath)
#         for span in spans:
#             # self.extract_brackets(span)
#             pass
#
#     def extract_brackets(self, span):
#         """extract (...) from text, and add hyperlinks for refs, NYI
#         (IPCC 2018a)
#         (Roy et al. 2018)
#         (UNFCCC 2016a, 2021)
#         (Bertram et al. 2015; Riahi et al. 2015)
#         """
#         text = ''.join(span.itertext())
#         par = span.getparent()
#         # (FooBar& Biff 2012a)
#         refregex = r"(" \
#                    r"[^\(]*" \
#                    r"\(" \
#                    r"(" \
#                    r"[A-Z][^\)]{1,50}(20\d\d|19\d\d)" \
#                    r")" \
#                    r"\s*" \
#                    r"\)" \
#                    r"(.*)" \
#                    r")"
#
#         if result := re.compile(refregex).search(text):
#             # print(f"matched: {result.group(1)} {result.group(2)}, {result.group(3)} {result.groups()}")
#             elem0 = lxml.etree.SubElement(par, H_SPAN)
#             elem0.text = result.group(1)
#             for k, v in elem0.attrib.items():
#                 elem0.attrib[k] = v
#             idx = par.index(span)
#             span.addnext(elem0)
#             current = elem0
#             for ref in result.group(2).split(";"):  # e.g. in (Foo and Bar, 2018; Plugh 2020)
#                 ref = ref.strip()
#                 if not self.ref_counter[ref]:
#                     self.ref_counter[ref] == 0
#                 self.ref_counter[ref] += 1
#                 a = lxml.etree.SubElement(par, H_A)
#                 for k, v in elem0.attrib.items():
#                     a.attrib[k] = v
#                 a.attrib[H_HREF] = "https://github.com/petermr/discussions"
#                 a.text = "([" + ref + "])"
#                 current.addnext(a)
#                 current = a
#             elem2 = lxml.etree.SubElement(par, H_SPAN)
#             for k, v in elem0.attrib.items():
#                 elem2.attrib[k] = v
#             elem2.text = result.group(3)
#
#             par.remove(span)
#
#             # print(f"par {lxml.etree.tostring(par)}")


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
