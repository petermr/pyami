"""AMI dictionary classes"""
from py4ami.wikimedia import WikidataLookup, WikidataPage
from py4ami.util import Util
from py4ami.constants import CEV_OPEN_DICT_DIR, OV21_DIR, DICT_AMI3, PHYSCHEM_RESOURCES
from lxml import etree as ET
from lxml import etree
from lxml.etree import Element
# import requests
# import xmltodict
import urllib.request

import logging
import os
from abc import ABC
from pathlib import Path

logging.debug("loading dict_lib")


# elements in amidict
DICTIONARY = "dictionary"
ENTRY = "entry"
IMAGE = "image"
TITLE = "title"
WIKIPEDIA = "wikipedia"

# attributes in amidict
DESC = "desc"
NAME = "name"
TERM = "term"
WIKIDATA_ID = "wikidataID"
WIKIDATA_URL = "wikidataURL"
WIKIDATA_SITE = "https://www.wikidata.org/wiki/"
WIKIPEDIA_PAGE = "wikipediaPage"
# elements

logger = logging.getLogger("dict_lib")


class AmiDictionary:
    """wrapper for an ami dictionary including search flags

    """
    TERM = "term"

    def __init__(self, xml_file=None, name=None, wikilangs=None, **kwargs):
        self.logger = logger
        self.amidict = None
        self.entries = []
        self.entry_by_term = {}
        self.entry_by_wikidata_id = {}
        self.file = xml_file
        self.ignorecase = None
        self.name = None
        self.root = None
        self.sparql_result_list = None
        self.sparql_result_by_wikidata_id = None
        self.sparql_to_dictionary = None
        self.split_terms = False
        self.term_set = set()
        self.wikilangs = wikilangs

        if xml_file is not None:
            if not os.path.exists(xml_file):
                raise IOError("cannot find path " + str(xml_file))
            self.read_dictionary_from_xml_file(xml_file)
            self.name = xml_file.split("/")[-1:][0].split(".")[0]
        elif name is None:
            print("must have name for new dictionary")
        else:
            self.name = name

        self.options = {} if not "options" in kwargs else kwargs["options"]
        if "synonyms" in self.options:
            print("use synonyms")
        if "noignorecase" in self.options:
            print("use case")
        self.split_terms = True
        self.split_terms = False

    @classmethod
    def create_from_words(cls, terms, name=None, desc=None, wikilangs=None):
        """use raw list of words and lookup each. choosing WD page and using languages """
        if name is None:
            name = "no_name"
        dictionary = AmiDictionary(name=name, wikilangs=wikilangs)
        dictionary.root = ET.Element(DICTIONARY)
        dictionary.root.attrib[TITLE] = name
        if desc:
            desc_elem = ET.SubElement(dictionary.root, DESC)
            desc_elem.text = desc
        for term in terms:
            entry = ET.SubElement(dictionary.root, ENTRY)
            entry.attrib[NAME] = term
            entry.attrib[TERM] = term
            dictionary.entries.append(entry)
        return dictionary

    @classmethod
    def read_dictionary(cls, file, ignorecase=True):
        return AmiDictionary(xml_file=file) if file is not None else None

    def read_dictionary_from_xml_file(self, file, ignorecase=True):
        self.file = file
        self.amidict = ET.parse(file, parser=ET.XMLParser(encoding="utf-8"))
        self.root = self.amidict.getroot()
        # print("ROOT", ET.tostring(self.root)[:50])
        self.name = self.root.attrib["title"]
        self.ignorecase = ignorecase

        self.entries = list(self.root.findall(ENTRY))
        self.create_entry_by_term()
        self.term_set = set()
#        print("read dictionary", self.name, "with", len(self.entries), "entries")

    def get_or_create_term_set(self):
        if len(self.term_set) == 0:
            for entry in self.entries:
                if AmiDictionary.TERM in entry.attrib:
                    term = self.term_from_entry(entry)
#                    print("tterm", term)
                    # single word terms
                    if not " " in term:
                        self.add_processed_term(term)
                    elif self.split_terms:
                        # multiword terms
                        for termx in term.split(" "):
                            #                            print("term", termx)
                            self.add_processed_term(termx)
                    else:
                        # add multiword term
                        self.add_processed_term(term)

        #            print(len(self.term_set), list(sorted(self.term_set)))
        #        print ("terms", len(self.term_set))
        return self.term_set

    def get_or_create_multiword_terms(self):
        return
        """NYI"""
        if len(self.multiwords) == 0:
            for entry in self.entries:
                if AmiDictionary.TERM in entry.attrib:
                    term = self.term_from_entry(entry)
                    # single word terms
                    if not " " in term:
                        self.add_processed_term(term)
                    elif self.split_terms:
                        # multiword terms
                        for term in " ".split(term):
                            self.add_processed_term(term)

        #            print(len(self.term_set), list(sorted(self.term_set)))
        #        print ("terms", len(self.term_set))
        return self.term_set

    def term_from_entry(self, entry):
        if AmiDictionary.TERM not in entry.attrib:
            print("missing term", ET.tostring(entry))
            term = None
        else:
            term = entry.attrib[AmiDictionary.TERM].strip()
        return term.lower() if term is not None and self.ignorecase else term

    def get_xml_and_image_url(self, term):
        entry = self.get_entry(term)
        entry_xml = ET.tostring(entry)
        image_url = entry.find(".//" + IMAGE)
        return entry_xml, image_url.text if image_url is not None else None

    def add_processed_term(self, term):
        if self.ignorecase:
            term = term.lower()
        self.term_set.add(term)  # single word countries

    def match(self, target_words):
        matched = []
        self.term_set = self.get_or_create_term_set()
        for target_word in target_words:
            target_word = target_word.lower()
            if target_word in self.term_set:
                matched.append(target_word)
        return matched

    def match_multiple_word_terms_against_sentences(self, sentence_list):
        """this will be slow with large dictionaries until we optimise the algorithm """
        matched = []

        for term in self.term_set:
            term = term.lower()
            term_words = term.split(" ")
            if len(term_words) > 1:
                for sentence in sentence_list:
                    if term in sentence.lower():
                        matched.append(term)
        return matched

    def get_entry(self, term):
        if self.entry_by_term is None:
            self.create_entry_by_term()
        entry = self.entry_by_term[term] if term in self.entry_by_term else None
        if entry is None:
            self.logger.debug(
                "entry by term", self.entry_by_term)  # very large
            pass
        return entry

    def create_entry_by_term(self):
        self.entry_by_term = {self.term_from_entry(
            entry): entry for entry in self.entries}

    def check_unique_wikidata_ids(self):
        # print("entries", len(self.entries))
        self.entry_by_wikidata_id = {}
        for entry in self.entries:
            if WIKIDATA_ID not in entry.attrib:
                print("No wikidata ID for", entry)
            else:
                wikidata_id = entry.attrib[WIKIDATA_ID]
                if wikidata_id in self.entry_by_wikidata_id.keys():
                    print("duplicate Wikidata ID:", wikidata_id, entry)
                else:
                    self.entry_by_wikidata_id[wikidata_id] = entry

    #        print("entry by id", self.entry_by_wikidata_id)

    def write(self, file):
        from lxml import etree
        et = etree.ElementTree(self.root)
        with open(file, 'wb') as f:
            et.write(f, encoding="utf-8",
                     xml_declaration=True, pretty_print=True)

    def add_wikidata_from_terms(self):

        wikidata_lookup = WikidataLookup()
        entries = self.root.findall(ENTRY)
        for entry in entries:
            term = entry.attrib[TERM]
            qitem, desc, qitems = wikidata_lookup.lookup_wikidata(term)
            entry.attrib[WIKIDATA_ID] = qitem
            entry.attrib[WIKIDATA_URL] = WIKIDATA_SITE + qitem
            entry.attrib[DESC] = desc
            synonym = ET.SubElement(entry, "synonym")
            synonym.attrib["type"] = "wikidata_hits"
            synonym.text = str(qitems)
            wikidata_page = WikidataPage(qitem)
            wikipedia_dict = wikidata_page.get_wikipedia_page_links(
                self.wikilangs)
            self.add_wikipedia_page_links(entry, wikipedia_dict)

    def add_wikipedia_page_links(self, entry, wikipedia_dict):
        for wp in wikipedia_dict.items():
            if wp[0] == "en":
                entry.attrib[WIKIPEDIA_PAGE] = wp[1]
            else:
                wikipedia = ET.SubElement(entry, WIKIPEDIA)
                wikipedia.attrib["lang"] = wp[0]
                wikipedia.text = wp[1]

    def create_wikidata_page(self, entry_element):
        from pyami.wikimedia import WikidataPage

        # refactor this - make entry a class
        wikidata_page = None
        qitem = entry_element.attrib[WIKIDATA_ID]
        if qitem is not None:
            wikidata_page = WikidataPage(qitem)

        return wikidata_page


class AmiDictionaries:
    """collection of current and some historic dictionaries"""

    ACTIVITY = "activity"
    COMPOUND = "compound"
    COUNTRY = "country"
    DISEASE = "disease"
    ELEMENT = "elements"
    INVASIVE_PLANT = "invasive_plant"
    PLANT_GENUS = "plant_genus"
    ORGANIZATION = "organization"
    PLANT_COMPOUND = "plant_compound"
    PLANT = "plant"
    PLANT_PART = "plant_part"
    SOLVENT = "solvents"

    ANIMAL_TEST = "animaltest"
    COCHRANE = "cochrane"
    COMP_CHEM = "compchem"
    CRISPR = "crispr"
    CRYSTAL = "crystal"
    DISTRIBUTION = "distributions"
    DITERPENE = "diterpene"
    DRUG = "drugs"
    EDGE_MAMMAL = "edgemammals"
    CHEM_ELEMENT = "elements"
    EPIDEMIC = "epidemic"
    ETHICS = "ethics"
    EUROFUNDER = "eurofunders"
    ILLEGAL_DRUG = "illegaldrugs"
    INN = "inn"
    INSECTICIDE = "insecticide"
    MAGNETISM = "magnetism"
    MONOTERPENE = "monoterpene"
    NAL = "nal"
    NMR = "nmrspectroscopy"
    OBESITY = "obesity"
    OPTOGENETICS = "optogenetics"
    PECTIN = "pectin"
    PHOTOSYNTH = "photosynth"
    PLANT_DEV = "plantDevelopment"
    POVERTY = "poverty"
    PROT_STRUCT = "proteinstruct"
    PROT_PRED = "protpredict"
    REFUGEE = "refugeeUNHCR"
    SESQUITERPENE = "sesquiterpene"
    SOLVENT = "solvents"
    STATISTICS = "statistics"
    TROPICAL_VIRUS = "tropicalVirus"
    WETLANDS = "wetlands"
    WILDLIFE = "wildlife"

    def __init__(self):
        self.create_search_dictionary_dict()

    def create_search_dictionary_dict(self):
        self.dictionary_dict = {}

#        / Users / pm286 / projects / CEVOpen / dictionary / eoActivity / eo_activity / Activity.xml
        self.add_with_check(AmiDictionaries.ACTIVITY,
                            os.path.join(CEV_OPEN_DICT_DIR, "eoActivity", "eo_activity", "activity.xml"))
        self.add_with_check(AmiDictionaries.COUNTRY,
                            os.path.join(OV21_DIR, "country", "country.xml"))
        self.add_with_check(AmiDictionaries.DISEASE,
                            os.path.join(OV21_DIR, "disease", "disease.xml"))
        self.add_with_check(AmiDictionaries.COMPOUND,
                            os.path.join(CEV_OPEN_DICT_DIR, "eoCompound", "plant_compound.xml"))
        self.add_with_check(AmiDictionaries.PLANT,
                            os.path.join(CEV_OPEN_DICT_DIR, "eoPlant", "plant.xml"))
        self.add_with_check(AmiDictionaries.PLANT_GENUS,
                            os.path.join(CEV_OPEN_DICT_DIR, "plant_genus", "plant_genus.xml"))
        self.add_with_check(AmiDictionaries.ORGANIZATION,
                            os.path.join(OV21_DIR, "organization", "organization.xml"))
        self.add_with_check(AmiDictionaries.PLANT_COMPOUND,
                            os.path.join(CEV_OPEN_DICT_DIR, "eoCompound", "plant_compound.xml"))
        self.add_with_check(AmiDictionaries.PLANT_PART,
                            os.path.join(CEV_OPEN_DICT_DIR, "eoPlantPart", "eoplant_part.xml"))
        self.add_with_check(AmiDictionaries.INVASIVE_PLANT,
                            os.path.join(CEV_OPEN_DICT_DIR, "Invasive_species", "invasive_plant.xml"))

        self.make_ami3_dictionaries()

#        self.print_dicts()
        return self.dictionary_dict

    def print_dicts(self):
        print("DICTIONARIES LOADED")
        dd = dir(self)
        for d in dd:
            if d[0].isupper():
                print(">>", d)

    def make_ami3_dictionaries(self):

        self.ami3_dict_index = {
            AmiDictionaries.ANIMAL_TEST: os.path.join(DICT_AMI3, "animaltest.xml"),
            AmiDictionaries.COCHRANE: os.path.join(DICT_AMI3, "cochrane.xml"),
            AmiDictionaries.COMP_CHEM: os.path.join(DICT_AMI3, "compchem.xml"),
            AmiDictionaries.CRISPR: os.path.join(DICT_AMI3, "crispr.xml"),
            AmiDictionaries.CRYSTAL: os.path.join(DICT_AMI3, "crystal.xml"),
            AmiDictionaries.DISTRIBUTION: os.path.join(DICT_AMI3, "distributions.xml"),
            AmiDictionaries.DITERPENE: os.path.join(DICT_AMI3, "diterpene.xml"),
            AmiDictionaries.DRUG: os.path.join(DICT_AMI3, "drugs.xml"),
            AmiDictionaries.EDGE_MAMMAL: os.path.join(DICT_AMI3, "edgemammals.xml"),
            AmiDictionaries.ETHICS: os.path.join(DICT_AMI3, "ethics.xml"),
            AmiDictionaries.CHEM_ELEMENT: os.path.join(DICT_AMI3, "elements.xml"),
            AmiDictionaries.EPIDEMIC: os.path.join(DICT_AMI3, "epidemic.xml"),
            AmiDictionaries.EUROFUNDER: os.path.join(DICT_AMI3, "eurofunders.xml"),
            AmiDictionaries.ILLEGAL_DRUG: os.path.join(DICT_AMI3, "illegaldrugs.xml"),
            AmiDictionaries.INN: os.path.join(DICT_AMI3, "inn.xml"),
            AmiDictionaries.INSECTICIDE: os.path.join(DICT_AMI3, "insecticide.xml"),
            AmiDictionaries.MAGNETISM: os.path.join(DICT_AMI3, "magnetism.xml"),
            AmiDictionaries.MONOTERPENE: os.path.join(DICT_AMI3, "monoterpene.xml"),
            AmiDictionaries.NAL: os.path.join(DICT_AMI3, "nal.xml"),
            AmiDictionaries.NMR: os.path.join(DICT_AMI3, "nmrspectroscopy.xml"),
            AmiDictionaries.OBESITY: os.path.join(DICT_AMI3, "obesity.xml"),
            AmiDictionaries.OPTOGENETICS: os.path.join(DICT_AMI3, "optogenetics.xml"),
            AmiDictionaries.PECTIN: os.path.join(DICT_AMI3, "pectin.xml"),
            AmiDictionaries.PHOTOSYNTH: os.path.join(DICT_AMI3, "photosynth.xml"),
            AmiDictionaries.PLANT_DEV: os.path.join(DICT_AMI3, "plantDevelopment.xml"),
            AmiDictionaries.POVERTY: os.path.join(DICT_AMI3, "poverty.xml"),
            AmiDictionaries.PROT_STRUCT: os.path.join(DICT_AMI3, "proteinstruct.xml"),
            AmiDictionaries.PROT_PRED: os.path.join(DICT_AMI3, "protpredict.xml"),
            AmiDictionaries.REFUGEE: os.path.join(DICT_AMI3, "refugeeUNHCR.xml"),
            AmiDictionaries.SESQUITERPENE: os.path.join(DICT_AMI3, "sesquiterpene.xml"),
            AmiDictionaries.SOLVENT: os.path.join(DICT_AMI3, "solvents.xml"),
            AmiDictionaries.STATISTICS: os.path.join(DICT_AMI3, "statistics.xml"),
            AmiDictionaries.TROPICAL_VIRUS: os.path.join(DICT_AMI3, "tropicalVirus.xml"),
            AmiDictionaries.WETLANDS: os.path.join(DICT_AMI3, "wetlands.xml"),
            AmiDictionaries.WILDLIFE: os.path.join(DICT_AMI3, "wildlife.xml"),
        }

        for item in self.ami3_dict_index.items():
            self.add_with_check(item[0], item[1])

    def add_with_check(self, key, file):
        #        print("adding dictionary", path)
        if key in self.dictionary_dict:
            raise Exception("duplicate dictionary key " +
                            key + " in " + str(self.dictionary_dict))
        Util.check_exists(file)
        try:
            dictionary = AmiDictionary(file)
            self.dictionary_dict[key] = dictionary
        except Exception as ex:
            print("Failed to read dictionary", file, ex)
#        print(dictionary.get_or_create_term_set())
        return

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
    ENCODING_A = "encoding"
    TITLE_A = "title"
    VERSION_A = "version"


# lang
    LANG_EN = "en"
    LANG_HI = "hi"
    LANG_UR = "ur"
# encoding
    UTF_8 = "UTF-8"
# tag
    TAG = "dictionary"

    def __init__(self, element):
        """AMIDict always has an XML root element"""
        super().__init__(element)
        self.file = None
        self.url = None
        assert element is not None
        assert self.element is not None
        self.entries = [] # child entries

    @classmethod
    def create_minimal_dictionary(cls):
        element = etree.Element(AMIDict.TAG)
        amidict = AMIDict(element)
        amidict.add_base_version()
        amidict.set_title("minimal")
        amidict.set_encoding(AMIDict.UTF_8)
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
        amidict.set_file(xml_file)
        return amidict

    @classmethod
    def create_dict_from_url(cls, xml_url):
        assert xml_url is not None
        try:
            with urllib.request.urlopen(xml_url) as f:
                # content = f.read().decode('utf-8')
                content = f.read()
        except urllib.error.URLError as e:
            raise AMIDictError(f"Failed to read URL {e.reason}")
        assert content is not None

        assert type(content) is bytes
        # msg = f"content {content}"
        # assert content == "foo", msg
        element = etree.fromstring(content)

        assert element.tag == AMIDict.TAG
        amidict = AMIDict(element)
        amidict.set_url(xml_url)
        return amidict

    def set_file(self, file):
        """file may be required to validate against title"""
        self.file = file

    def set_url(self, url):
        """file may be required to validate against title"""
        self.url = url

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
        if self.element is None:
            raise AMIDictError(f"{self.TAG} must have element")
        version = self.element.attrib["version"]
        assert version == "XXX"
        return version

    def set_version(self, version):
        assert AMIDict.is_valid_version_string(version)
        self.element.attrib[self.VERSION_A] = version

    def get_title(self):
        assert self.TITLE_A in self.element.attrib
        return self.element.attrib[self.TITLE_A]

    def set_title(self, title):
        self.element.attrib[self.TITLE_A] = title

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
        return None if not AMIDict.VERSION_A in self.element.attrib else self.element.attrib[AMIDict.VERSION_A]

    def set_encoding(self, encoding):
        self.element.attrib[AMIDict.ENCODING_A] = encoding

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

# data validity
    def check_validity(self):
        # assert f"{etree.tostring(self.element)}" == "xxx"
        if not self.has_valid_element():
            raise AMIDictError(msg="must contain valid element (NYI)")
        if not self.has_valid_tag():
            raise AMIDictError(msg="must have valid tag")
        if not self.has_valid_attributes():
            raise AMIDictError(msg="must have valid attributes")
        # assert self.has_valid_children()

    def has_valid_element(self):
        if self.element is None:
            raise AMIDictError(msg="No element in AMIDict wrapper")
        return True

    def has_valid_tag(self) -> bool:
        assert self.has_valid_element()
        return self.element.tag == AMIDict.TAG

    def has_valid_attributes(self):
        if not self.has_valid_required_attributes():
            raise AMIDictError(msg="element does not have valid required attributes")
        if not self.has_valid_optional_attributes():
            raise AMIDictError(msg="element does not have valid optional attributes")
        if self.has_forbidden_attributes():
            raise AMIDictError(msg="element has_forbidden_attributes")
        return True

    def has_valid_required_attributes(self):
        version = self.get_version()
        version_ok = AMIDict.is_valid_version_string(version)
        if not version_ok:
            raise AMIDictError(f"{self.TAG} does not have valid version")
        title_ok = self.has_valid_title()
        if not title_ok:
            raise AMIDictError(f"{self.TAG} does not have valid title")
        encoding_ok = self.has_valid_encoding()
        if not encoding_ok:
            raise AMIDictError(f"{self.TAG} does not have valid encoding")
        return True

    def remove_attribute(self, attname):
        if attname is not None and attname in self.element.attrib:
            self.element.attrib.pop(attname)

    def has_valid_title(self):
        """AMIDict must have title attribute with value == stem of dict file"""
        title = self.get_title()
        assert title is not None
        return title is not None and \
               (self.file is None or Path(self.file).stem == title)

    @classmethod
    def is_valid_version_string(cls, versionx):
        """tests validity of version string major.minor.patch

        e.g. version = "1.2.3"
        """
        if versionx is None:
            raise AMIDictError(f"{cls} does not have version attribute ")
        parts = versionx.split(".")
        if len(parts) != 3:
            raise AMIDictError(f"{cls} version attribute {versionx} does not have 3 parts")
        try:
            for part in parts:
                i = int(part)
        except:
            raise AMIDictError(f"{cls} version attribute {versionx} parts must be integers")
        return True

    def has_valid_encoding(self):
        encoding = None if not AMIDict.ENCODING_A in self.element.attrib \
            else self.element.attrib[AMIDict.ENCODING_A]
        return encoding is not None and encoding.upper() == AMIDict.UTF_8

    def has_valid_optional_attributes(self):
        return True

    def has_forbidden_attributes(self):
        return False

    def has_valid_children(self):
        assert False , "not yet written"
        return True

class AMIDictError(Exception):
    """Basic exception for errors raised in AMIDict"""
    def __init__(self, msg=None):
        if msg is None:
            msg = "An unspecifed error occured"
        super(AMIDictError, self).__init__(msg)

class Synonym(AbsDictElem):
    TAG = "synonym"

    def __init__(self, element=None):
        super().__init__(element)
        assert element is not None, "synonym constructor "
        self.element = element

class Entry(AbsDictElem):
    TAG = "entry"

    DESCRIPTION_A = "description"
    NAME_A = "name"
    TERM_A = "term"
    WIKIDATA_A = "wikidataID"
    WIKIPEDIA_A = "wikipediaPage"

    REQUIRED_ATTS = {TERM_A}
    OPTIONAL_ATTS = {DESCRIPTION_A, NAME_A, WIKIDATA_A, WIKIPEDIA_A}
    ALLOWED_ATTS = REQUIRED_ATTS.union(OPTIONAL_ATTS)
    assert len(ALLOWED_ATTS) == 5

    ELEMENT_CHILD_TAGS = {Synonym.TAG}

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
        self.element.attrib[self.TERM_A] = term

    def get_term(self):
        return self.element.attrib[self.TERM_A]

    def add_name(self, name):
        self.element.attrib[self.NAME_A] = name

    def get_name(self):
        return self.element.attrib[self.NAME_A]

    def check_validity(self):
        self.check_valid_attributes()
        self.check_valid_children()

    def check_valid_attributes(self):
        attributes = list(self.element.attrib)
        assert attributes is not None
        # assert str(attributes) == "['name']", f"attributes {attributes}"
        # assert len(attributes) == 2, f" ATTS {attributes}"
        for attribut in attributes:
            msg = f"ATT {attribut}"
            assert type(attribut) is str
            assert attribut in self.ALLOWED_ATTS, f"attribute {attribut} is not allowed in <entry>"

    def check_valid_children(self):
        for child in self.element:
            assert child.tag in self.ELEMENT_CHILD_TAGS

def main():
    AMIDict.debug_tdd()
#     tdd = Pyamidict_TDD()
#     tdd.test_dictionary_exists()
#     tdd.test_dict_contains_xml_element()
#     tdd.test_dict_has_root_dictionary()
#     tdd.test_dict_has_XML_title()
#     tdd.test_dict_title_matches_filename()


if __name__ == "__main__":
    print("running search main")
    main()
else:

    #    print("running search main anyway")
    #    main()
    pass
