from lxml import etree as ET
from lxml import etree
import urllib.request
import datetime
import psutil

import logging
import os
import re
from abc import ABC
from pathlib import Path

"""AMI dictionary classes"""
"""this may have circular import of AmiDictionary"""
from py4ami.wikimedia import WikidataLookup, WikidataPage
from py4ami.util import Util
from py4ami.constants import CEV_OPEN_DICT_DIR, OV21_DIR, DICT_AMI3

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
        self.wikidata_lookup = WikidataLookup()

        if xml_file is not None:
            if not os.path.exists(xml_file):
                raise IOError("cannot find path " + str(xml_file))
            self.read_dictionary_from_xml_file(xml_file)
            self.name = xml_file.split("/")[-1:][0].split(".")[0]
        elif name is None:
            print("must have name for new dictionary")
        else:
            self.name = name

        self.options = {} if "options" not in kwargs else kwargs["options"]
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
    def read_dictionary(cls, file):
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
                    if " " not in term:
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
                    if " " not in term:
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

        entries = self.root.findall(ENTRY)
        for entry in entries:
            self.add_wikidata_to_entry(entry)

    def add_wikidata_to_entry(self, entry):
        term = entry.attrib[TERM]
        if entry.get(WIKIDATA_ID) is None:
            qitem, desc, qitems = self.wikidata_lookup.lookup_wikidata(term)
            if qitem is not None:
                entry.attrib[WIKIDATA_ID] = qitem
                entry.attrib[WIKIDATA_URL] = WIKIDATA_SITE + qitem
                entry.attrib[DESC] = desc
                synonym = ET.SubElement(entry, "synonym")
                synonym.attrib["type"] = "wikidata_hits"
                synonym.text = str(qitems)
                wikidata_page = WikidataPage(qitem)
                assert wikidata_page is not None
                wikipedia_dict = wikidata_page.get_wikipedia_page_links(
                    self.wikilangs)
                self.add_wikipedia_page_links(entry, wikipedia_dict)

    @classmethod
    def add_wikipedia_page_links(cls, entry, wikipedia_dict):
        for wp in wikipedia_dict.items():
            if wp[0] == "en":
                entry.attrib[WIKIPEDIA_PAGE] = wp[1]
            else:
                wikipedia = ET.SubElement(entry, WIKIPEDIA)
                wikipedia.attrib["lang"] = wp[0]
                wikipedia.text = wp[1]

    def create_wikidata_page(self, entry_element):
        from py4ami.wikimedia import WikidataPage

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
    STATISTICS = "statistics"
    TROPICAL_VIRUS = "tropicalVirus"
    WETLANDS = "wetlands"
    WILDLIFE = "wildlife"

    def __init__(self):
        self.dictionary_dict = {}
        self.create_search_dictionary_dict()
        self.ami3_dict_index = None

    def create_search_dictionary_dict(self):

        # / Users / pm286 / projects / CEVOpen / dictionary / eoActivity / eo_activity / Activity.xml
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
    UNKNOWN = "UNKNOWN"

    def __init__(self, element, xml_tree=None):
        self.element = element
        self.xml_tree = xml_tree
        assert element is not None, "AbsDictElem constructor should not receive None "

    def set_attribute(self, attname, attval):
        """set XML attribute
        raises error if attname or attval are missing
        will not set empty attribute value
        :attname:
        :attval: must not be empty
        :except: AMIDictError

        """
        if self.element is None:
            raise AMIDictError("AbsDictElem element is None")
        if attname is None or len(attname.strip()) == 0:
            raise AMIDictError("missing/empty attname")
        if attval is None or len(str(attval).strip()) == 0:
            raise AMIDictError(f"missing/empty attval for {attname}")
        attval = str(attval)
        self.element.attrib[attname] = attval

    def get_username(self):
        """This is NOT robust - see
        https://stackoverflow.com/questions/842059/is-there-a-portable-way-to-get-the-current-username-in-python
        """
        return psutil.Process().username()

    def get_attribute_value(self, attname):
        """get XML attribute value

        if attname is not present returns none
        :attname: attribute name
        :returns: attribute value or None if not found
        :except: raises AMIDictError for bad attname
        """
        if self.element is None:
            raise AMIDictError("AbsDictElem element is None")
        if attname is None or len(attname.strip()) == 0:
            raise AMIDictError("missing/empty attname")
        if attname not in self.element.attrib:
            return None
        return self.element.attrib[attname]


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

    def __init__(self, element, tree=None):
        """AMIDict always has an XML root element"""
        super().__init__(element, tree)
        self.file = None
        self.url = None
        assert element is not None
        assert self.element is not None
        self.entries = []  # child entries
        self.logger = logging.getLogger("amidict")
        self.wikidata_lookup = WikidataLookup()

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
        xml_tree = etree.parse(str(xml_path))
        element = xml_tree.getroot()
        assert element.tag == AMIDict.TAG
        amidict = AMIDict(element, xml_tree)
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
            raise AMIDictError(f"Failed to read URL: {xml_url}; reason = {e.reason}")
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

    def get_file(self):
        return self.file

    def set_url(self, url):
        """file may be required to validate against title"""
        self.url = url

    def get_file_or_url(self):
        return self.file if self.file is not None else self.url

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
        version = self.get_attribute_value(self.VERSION_A)
        # assert version == "XXX"
        return version

    def set_version(self, version):
        assert AMIDict.is_valid_version_string(version)
        self.set_attribute(self.VERSION_A, version)

    def get_title(self):
        return self.get_attribute_value(self.TITLE_A)

    def set_title(self, title):
        """Sets title of dictionary

        does not validate title
        :title: title of dictionary, should match stem of filename
        """
        self.set_attribute(self.TITLE_A, title)
        if self.get_stem() is None:
            self.set_file(self.UNKNOWN)

    @classmethod
    def debug_tdd(cls):
        """This is just for debugging"""
        # file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict1.xml")
        one_entry_file = Path(Path(__file__).parent.parent, "py4ami/resources/amidicts/dict_one_entry.xml")
        # root = etree.parse(str(one_entry_file)).getroot()
        tddd = AMIDict.create_dict_from_path(one_entry_file)
        entries = tddd.get_entries()
        print(f"len {len(entries)} {type(entries)} entr {entries[0]} ")

    def add_base_version(self):
        assert self.element is not None
        self.set_version("0.0.1")

    def set_encoding(self, encoding):
        self.set_attribute(AMIDict.ENCODING_A, encoding)

    def create_and_add_entry(self):
        entry_elem = Entry.create_and_add_to(self.element)
        return Entry(entry_elem)

    def create_and_add_entry_with_term(self, term, replace=False):
        """adds an Entry with term set to term

        if an entry is already present with term() = term:
        a) if replace = False, raises exceptiom
        b) else overwrites it

        Note that other attributes and children must be added later
        We may create convenience methods to do that

        All addition of terms should go through this method

        :term: term to add after stripping whitespace
        :return: new entry
        """
        term = term.strip()
        if term is None or term.strip() == "":
            raise AMIDictError(f"cannot add entry with term = None or ''")
        old_entry = self.find_entry_with_term(term)
        if old_entry is not None:
            if replace is False:
                raise AMIDictError(f"cannot replace old entry with term {term}")
            self.delete_entry(old_entry)
        entry = self.create_and_add_entry()
        assert entry.get_term() is None
        entry.add_term(term)
        assert entry.get_term() == term
        return entry

    def create_and_add_entries_from_str_list(self, strings, replace=False):
        """creates minimal entries from list of strings and adds to dictionary

        :strings: list of terms
        :replace: if True will replace entry, if False will raise error if entry exists
        """
        for term in strings:
            self.create_and_add_entry_with_term(term, replace)

    @classmethod
    def create_from_list_of_strings(cls, terms, title, metadata=None):
        """create a minimal dictionary from list of strings

        :terms: to add
        :title: mandatory title, will also form stem of filename
        :metadata: Free from text of origin if terms
        :return: dictionary
        """
        if title is None or title.strip() == "":
            raise AMIDictError(f"must give non-empty title {title}")
        amidict = AMIDict.create_minimal_dictionary()
        amidict.create_and_add_entries_from_str_list(terms)
        amidict.set_title(title)
        amidict.create_and_add_base_metadata()
        return amidict

    @classmethod
    def create_from_list_of_strings_and_write_to_file(cls, terms, title, directory, wikidata=False, metadata=None):
        """create a minimal dictionary from list of strings

        :terms: to add
        :title: mandatory title, will also form stem of filename
        :directory: to write to
        :metadata: Free from text of origin if terms
        :return: output file and amidict
        """
        if directory is None:
            raise AMIDictError("no output directory for amidict")
        amidict = cls.create_from_list_of_strings(terms, title, metadata)
        if wikidata:
            amidict.lookup_terms_in_wikidata(terms)
        file = amidict.write_to_file(directory)
        return file, amidict

    def write_to_file(self, directory):
        """writes to <title>.xml in given directory
        includes pretty-print

        :directory: If None, no action
        """
        if directory is None:
            self.logger.warning(f"no directory given for writing xml dictionary")
        title = self.get_title()
        file = Path(directory, title + ".xml")
        with open(file, "w", encoding="UTF-8") as f:
            f.write(etree.tostring(self.element, pretty_print=True).decode("UTF-8"))
        return file

    def create_base_metadata(self):
        """create Metadata object with user and date"""
        metadata = Metadata(etree.Element(Metadata.TAG))
        metadata.set_user(self.get_username())
        metadata.set_date(datetime.datetime.now())
        return metadata

    def add_metadata(self, metadata):
        self.element.insert(0, metadata.element)

    def create_and_add_base_metadata(self):
        self.add_metadata(self.create_base_metadata())

# find entries
    def find_entry_with_term(self, term, abort_multiple=True):
        """iterate through entries and return entry with term

        if more than one entry is found, raise exception

        :term: to find
        :raise: AMDictError for multiple entries with same term
        :return: None, or single Entry or list of Entry's
        """
        entries = self.find_entries_with_term(term, abort_multiple)
        if len(entries) == 0:
            return None
        elif len(entries) == 1:
            return entries[0]
        else:
            return entries

    def find_entries_with_term(self, term, abort_multiple=False):
        entries = []
        for entry in self.get_entries():
            if entry.get_term() == term:
                if abort_multiple and len(entries) > 0:
                    raise AMIDictError(f"multiple entries with term = {term}")
                entries.append(entry)
        return entries

    def delete_entries_with_term(self, term):
        """Deletes ALL entries with term

        There is no way of distinguishing between multiple entries so all are to be deleted

        :term: entries with term=<term> will be deleted
         """
        entries = self.find_entries_with_term(term, abort_multiple=False)
        for entry in entries:
            self.delete_entry(entry)

    def delete_entry(self, entry):
        """delete entry from XML tree"""
        self.element.remove(entry.element)

    def get_terms(self):
        """Get an ordered list of terms in dictionary

        :return: tuple of list of terms, list of entries without terms, list of duplicates
        """
        terms = []
        entries_without_terms = []
        duplicate_entries = []
        entries = self.get_entries()
        term_set = set()
        for i, entry in enumerate(entries):
            term = entry.get_term()
            if term is None:
                entries_without_terms.append(f"entry {i}:\n{etree.tostring(entry.element)}")
            else:
                if term in term_set:
                    self.logger.warning(f"Duplicate term ({term}) in entry {i}")
                    duplicate_entries.append(f"({term}) in entry {i}")
                else:
                    term_set.add(term)
                    terms.append(term)
        return terms, entries_without_terms, duplicate_entries

# data validity

    def check_validity(self):
        """checks dictionary has  valid <dictionary> child, valid attributes and valid child elements (NYI)"""
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
        self.check_version()

        if not self.has_valid_title():
            raise AMIDictError(f"{self.TAG} does not have valid title (must match filename)")

        if self.get_attribute_value(self.ENCODING_A) is not None:
            self.logger.warning("encoding attribute on <dictionary> element is obsolete; remove it")

        return True

    def check_version(self):
        version = self.get_version()
        try:
            AMIDict.is_valid_version_string(version)
        except AMIDictError as e:
            raise AMIDictError(f"{self.get_file_or_url()} <dictionary> has invalid version: {e.__cause__}")

    def remove_attribute(self, attname):
        if self.get_attribute_value(attname) is not None:
            self.element.attrib.pop(attname)

    def has_file(self):
        if self.file is None:
            raise AMIDictError(f"no file name stored")

    def has_valid_title(self):
        """AMIDict must have title attribute with value == stem of dict file"""
        title = self.get_title()
        if title is None:
            raise AMIDictError(f"dictionary {self.file} has no title")
        stem = self.get_stem()
        if stem != self.UNKNOWN and stem != title:
            raise AMIDictError(f"dictionary {self.file} does not match title {title}")
        return True

    def get_stem(self):
        """Get stem of input (file or URL)
        File might be baz/foo/bar.xml   # stem is bar
        URL might be https://some.where/foo/bar.xml # stem is bar
        """
        # TODO TEST and check if better function
        stem = None
        if self.file is not None:
            stem = Path(self.file).stem
        elif self.url is not None:
            # assume ends in .../foo.xml where foo is stem
            parts = self.url.split("/")
            try:
                stem_xml = parts[-1]
                stem = stem_xml.split(".")[0]
            except Exception as e:
                raise AMIDictError(f"cannot parse url {self.url} {e}")
        if stem is None:
            stem = self.UNKNOWN
        return stem

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
                _ = int(part)
        except Exception:
            raise AMIDictError(f"{cls} version attribute {versionx} parts must be integers")
        return True

    def has_xml_declaration_with_utf8(self):
        """requires XML declaration with encoding = 'UTF-8'

        :except: If absent or not UTF-8, raises AMIDict err
        """
        if self.xml_tree is not None:  # need tree for declaration
            if self.xml_tree.docinfo is None:
                raise AMIDictError("dictionary has no docinfo/XML declaratiom")
            # assert tree.docinfo.xml_version == "1.0" # XML version is ignored
            if self.xml_tree.docinfo.encoding is None or self.xml_tree.docinfo.encoding.upper() != AMIDict.UTF_8:
                raise AMIDictError("dictionary must have encoding='UTF-8' in XML declaratiom")

    def has_valid_encoding(self):
        encoding = self.get_attribute_value(AMIDict.ENCODING_A)
        return encoding is not None and encoding.upper() == AMIDict.UTF_8

    def has_valid_optional_attributes(self):
        return True

    def has_forbidden_attributes(self):
        return False

    def has_valid_children(self):
        assert False, "not yet written"

    @classmethod
    def create_amidict_and_lookup_wikidata(cls, terms, title, directory=None):
        """creates amidict from list of terms and mandatory title

        :terms: list of strings
        :title: of dictionary and stem of filename
        :directpry: if not none writes title.xml to directory
        """
        amidict = AMIDict.create_from_list_of_strings(terms, title)
        amidict.lookup_terms_in_wikidata(terms)
        if directory is not None:
            amidict.write_to_file(directory)
        return amidict

    def lookup_terms_in_wikidata(self, terms):
        """looks up terms in Wikidata
        uses self.lookup_wikidata"""
        # wikidata_lookup = WikidataLookup()
        for term in terms:
            qitem, desc, _ = self.wikidata_lookup.lookup_wikidata(term)
            if qitem is None:
                print(f"could not lookup Wikidata: {term}")
            else:
                entry = self.find_entry_with_term(term)
                entry.set_wikidata_id(qitem)
                entry.set_description(desc)


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


class Metadata(AbsDictElem):
    TAG = "metadata"
    USER_A = "user"
    DATE_A = "date"

    def __init__(self, element=None):
        super().__init__(element)

    def set_user(self, user):
        self.set_attribute(Metadata.USER_A, user)

    def get_user(self):
        return self.get_attribute_value(Metadata.USER_A)

    def set_date(self, date):
        self.set_attribute(Metadata.DATE_A, date)

    def get_date(self):
        return self.get_attribute_value(Metadata.DATE_A)


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
    ELEMENT_PARENT_TAGS = {AMIDict.TAG}

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

        term = self.get_attribute_value(self.TERM_A)
        return term

    def add_name(self, name):
        self.element.attrib[self.NAME_A] = name

    def get_name(self):
        return self.get_attribute_value(self.NAME_A)

    def get_attribute_value(self, attname):
        if attname not in self.element.attrib:
            return None
        else:
            return self.element.attrib[attname]

    def set_wikidata_id(self, idx):
        """set wikidataID, id must be Pddd... or Q... """
        if idx is None or not re.match("[PQ]\\d+", idx):
            raise AMIDictError(f"wikidata id {idx} must be Qddd... or Pddd...")
        self.set_attribute(Entry.WIKIDATA_A, idx)

    def get_wikidata_id(self):
        return self.get_attribute_value(Entry.WIKIDATA_A)

    def set_description(self, desc):
        """set description attribute, can be anything"""
        self.set_attribute(Entry.DESCRIPTION_A, desc)

    def get_description(self):
        return self.get_attribute_value(Entry.DESCRIPTION_A)

    def check_validity(self):
        self.check_valid_attributes()
        self.check_valid_children()

    def check_valid_attributes(self):
        attributes = list(self.element.attrib)
        assert attributes is not None
        # assert str(attributes) == "['name']", f"attributes {attributes}"
        # assert len(attributes) == 2, f" ATTS {attributes}"
        for attribut in attributes:
            # msg = f"ATT {attribut}"
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
