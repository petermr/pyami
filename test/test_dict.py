import unittest

from lxml import etree as ET
import os
import pprint
from pathlib import Path

# local

from py4ami.wikimedia import WikidataSparql, WikidataPage
from py4ami.dict_lib import AmiDictionary

TEST_DIR = Path(Path(__file__).parent.parent, "test")
TEST_RESOURCE_DIR = Path(TEST_DIR, "resources")

class TestSearchDictionary:

    def test_parse_wikidata_page(self):
        qitem = "Q144362"  # azulene
        wpage = WikidataPage(qitem)
        # note "zz" has no entries
        ahref_dict = wpage.get_wikipedia_page_links(["en", "de", "zz"])
        assert ahref_dict == {'en': 'https://en.wikipedia.org/wiki/Azulene',
                              'de': 'https://de.wikipedia.org/wiki/Azulen'}

    def test_create_dictionary(self):

        words = ["limonene", "alpha-pinene", "Lantana camara"]
        dictionary = AmiDictionary.create_from_words(words, "test", "created from words", wikilangs=["en", "de"])
        dictionary.add_wikidata_from_terms()
        pprint.pprint(ET.tostring(dictionary.root).decode("UTF-8"))
        assert len(dictionary.entries) == 3

    def test_get_property_ids(self):
        """gets properties af a dictionary entry"""
        words = ["limonene"]
        dictionary = AmiDictionary.create_from_words(words, "test", "created from words", wikilangs=["en", "de"])
        dictionary.add_wikidata_from_terms()
        pprint.pprint(ET.tostring(dictionary.root).decode("UTF-8"))
        assert len(dictionary.entries) == 1
        wikidata_page = dictionary.create_wikidata_page(dictionary.entries[0])
        property_ids = wikidata_page.get_properties()
        assert len(property_ids) >= 60
        assert property_ids[:10] == ['P31', 'P279', 'P361', 'P2067', 'P274', 'P233',
                                     'P2054', 'P2101', 'P2128', 'P2199']

    # @unittest.skip(reason="needs debugging")
    def test_create_dictionary_from_sparql(self):
        from py4ami.constants import PHYSCHEM_RESOURCES
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
        dictionary = AmiDictionary(dictionary_file)
        wikidata_sparql = WikidataSparql(dictionary)
        wikidata_sparql.update_from_sparql(sparql_file, sparql_to_dictionary)
        ff = dictionary_file[:-(len(".xml"))] + "_update" + ".xml"
        print("saving to", ff)
        dictionary.write(ff)

    def test_invasive(self):
        """
        """

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        # from shutil import copyfile

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
        wikidata_sparql = WikidataSparql(AmiDictionary(dictionary_file))
        wikidata_sparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)
        # TODO needs assert

    @unittest.skip(reason="circular import AmiDictionary")
    def test_plant_genus(cls):
        """
        """

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        # from shutil import copyfile

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
        wikidata_sparql = WikidataSparql(AmiDictionary(dictionary_file))
        wikidata_sparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    @unittest.skip(reason="circular import AmiDictionary")
    def test_compound(cls):
        """
        """

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        # from shutil import copyfile

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

        wikidata_sparql = WikidataSparql(AmiDictionary(dictionary_file))
        wikidata_sparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    # @unittest.skip(reason="circular import AmiDictionary")
    def test_plant_part(cls):
        """
        Takes WD-SPARQL-XML output (sparql.xml) and maps to AMIDictionary (eo_plant_part.xml)

        """
        # current dictionary does not need updating

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob

        print(f"***test_plant_part")
        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoPlantPart")
        DICT_DIR = Path(TEST_RESOURCE_DIR,  "eoPlantPart")
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

        wikidata_sparql = WikidataSparql(AmiDictionary(dictionary_file))
        wikidata_sparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

def main(argv=None):
    print(f"running PDFArgs main")
    pdf_args = PDFArgs()
    try:
        pdf_args.process1_args()
    except Exception as e:
        print(f"***Cannot run pyami***; see output for errors: {e}")


if __name__ == "__main__":
    main()
else:
    pass

def main():
    pass