from lxml import etree as ET
import os
import pprint

# local

from py4ami.wikimedia import WikidataSparql
from py4ami.dict_lib import AmiDictionary


class SearchDictionaryTest:
    @classmethod
    def test_parse_wikidata_page(cls):
        qitem = "Q144362"  # azulene
        ahref_dict = cls.get_wikipedia_page_links(qitem, ["en", "de", "zz"])
        print(ahref_dict)

    @classmethod
    def test_create_from_words(cls):

        words = ["limonene", "alpha-pinene", "lantana camara"]
        dictionary = AmiDictionary.create_from_words(words, "test", "created from words", wikilangs=["en", "de"])
        dictionary.add_wikidata_from_terms()
        pprint.pprint(ET.tostring(dictionary.root))
        for entry in dictionary.entries:
            wikidata_page = dictionary.create_wikidata_page(entry)
            ids = wikidata_page.get_properties()
            print(ids)

    @classmethod
    def test(cls):
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
        dictionary = WikidataSparql(dictionary_file)
        dictionary.update_from_sparqlx(sparql_file, sparql_to_dictionary)
        ff = dictionary_file[:-(len(".xml"))] + "_update" + ".xml"
        print("saving to", ff)
        dictionary.write(ff)

    @classmethod
    def test_invasive(cls):
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

        WikidataSparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    @classmethod
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

        WikidataSparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    @classmethod
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

        WikidataSparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    @classmethod
    def test_plant_part(cls):
        """
        """
        # current dictionary does not need updating

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob

        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoPlantPart")
        assert (os.path.exists(DICT_DIR))
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

        WikidataSparql.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    @classmethod
    def test_plant(cls):
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

        option = "sparql"
        option = "plant"
        option = "invasive"
        option = "genus"
        option = "compound"
        option = "plant_part"
        option = "test_dict"
        # option = "wikipedia"
        if option == "sparql":
            SearchDictionaryTest.test()
        elif option == "plant":
            SearchDictionaryTest.test_plant()
        elif option == "invasive":
            SearchDictionaryTest.test_invasive()
        elif option == "genus":
            SearchDictionaryTest.test_plant_genus()
        elif option == "compound":
            SearchDictionaryTest.test_compound()
        elif option == "plant_part":
            SearchDictionaryTest.test_plant_part()
        elif option == "test_dict":
            SearchDictionaryTest.test_create_from_words()
        elif option == "wikipedia":
            SearchDictionaryTest.test_parse_wikidata_page()
        else:
            print("no option given")

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        import os
        # from shutil import copyfile

        PLANT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoPlant")
        assert (os.path.exists(PLANT_DIR))
        dictionary_file = os.path.join(PLANT_DIR, "eo_plant.xml")
        assert (os.path.exists(dictionary_file))
        PLANT_SPARQL_DIR = os.path.join(PLANT_DIR, "sparql_output")
        assert (os.path.exists(PLANT_SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(PLANT_SPARQL_DIR, "sparql_*.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "image_link",
                "dict_name": "image",
            },
            "taxon": {
                "id_name": "item",
                "sparql_name": "taxon",
                "dict_name": "synonym",
            }
        }


if __name__ == '__main__':
    SearchDictionaryTest.test_plant()
