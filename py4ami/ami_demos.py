
import os

from py4ami.constants import PHYSCHEM_PYTHON
from py4ami.util import Util
from py4ami.text_lib import AmiSection
from py4ami.ami_dict import AmiDictionaries
from py4ami.ami_project import AmiProjects
from py4ami.text_lib import WordFilter
from py4ami.search_lib import AmiSearch


class AmiDemos:

    FIG_CAPTION_DEMO = "fig_caption"
    LUKE_DEMO = "luke"
    DIFFPROT_DEMO = "diffprot"
    DISEASE_DEMO = "disease"
    ETHICS_DEMO = "ethics"
    GENUS_DEMO = "genus"  # TODO
    INVASIVE_DEMO = "invasive"
    MATTHEW_DEMO = "matthew"
    PLANT_DEMO = "plant"
    WORCESTER_DEMO = "worcester"
    WORD_DEMO = "word"

    DEMOS_JSON = os.path.join(PHYSCHEM_PYTHON, "demos.json")

    @staticmethod
    def run_demos(demos):
        demo_dict = {
            AmiDemos.DIFFPROT_DEMO: AmiDemos.diffprot_demo,
            AmiDemos.DISEASE_DEMO: AmiDemos.disease_demo,
            AmiDemos.ETHICS_DEMO: AmiDemos.ethics_demo,
            AmiDemos.FIG_CAPTION_DEMO: AmiDemos.fig_caption_demo,
            AmiDemos.INVASIVE_DEMO: AmiDemos.invasive_demo,
            AmiDemos.LUKE_DEMO: AmiDemos.luke_demo,
            AmiDemos.MATTHEW_DEMO: AmiDemos.matthew_demo,
            AmiDemos.PLANT_DEMO: AmiDemos.plant_parts_demo,
            AmiDemos.WORCESTER_DEMO: AmiDemos.worc_demo,
            AmiDemos.WORD_DEMO: AmiDemos.word_demo,
        }
        print("RUN DEMOS:", demos)
        if demos is None or len(demos) == 0:
            print("no demo given, choose from ", demo_dict.keys())
        else:
            for demo in demos:
                AmiDemos.run_demo(demo_dict, demo)
        print("END DEMO")

    @staticmethod
    def run_demo(demo_dict, demo):
        if demo in demo_dict.keys():
            demo_dict[demo]()
        else:
            demo_funct = Util.find_unique_dict_entry(demo_dict, demo)
            if demo_funct is not None:
                print("running:", demo_funct)
                demo_funct()

    @staticmethod
    def plant_parts_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2
        ami_search.wikidata_label_lang = "en"

        ami_search.use_sections([
            #            "method",
            AmiSection.INTRO,
            AmiSection.METHOD,
            #            AmiSection.TABLE,
            #            "fig_caption"
        ])
        ami_search.use_dictionaries([
            # intern dictionaries
            AmiDictionaries.ACTIVITY,
            AmiDictionaries.COMPOUND,
            AmiDictionaries.INVASIVE_PLANT,
            AmiDictionaries.PLANT,
            AmiDictionaries.PLANT_PART,
            AmiDictionaries.PLANT_GENUS,
        ])
        ami_search.use_projects([
            AmiProjects.OIL186,
        ])
        ami_search.use_filters([
            WordFilter.ORG_STOP
        ])

#        ami_search.add_regex("abb_genus", "^[A-Z]\.$")

        if ami_search.do_search:
            ami_search.run_search()

#    def add_regex(self, name, regex):
#        self.patterns.append(SearchPattern(name, SearchPattern.REGEX, regex))

    @staticmethod
    def diffprot_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.METHOD, ])
        ami_search.use_dictionaries(
            [AmiDictionaries.PROT_STRUCT, AmiDictionaries.PROT_PRED, AmiDictionaries.CRISPR])
        ami_search.use_projects([AmiProjects.DIFFPROT, ])

        ami_search.use_pattern("^[A-Z]{1,}[^\\s]*\\d{1,}$", "AB12")
        ami_search.use_pattern("_ALLCAPS", "all_capz")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()

    @staticmethod
    def ethics_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.ETHICS, ])
        ami_search.use_dictionaries(
            [AmiDictionaries.ETHICS, AmiDictionaries.COUNTRY, AmiDictionaries.DISEASE, ])
        ami_search.use_projects([AmiProjects.DISEASE, ])
        ami_search.use_filters([WordFilter.ORG_STOP])

        ami_search.use_pattern("^[A-Z]{1,}[^\\s]*\\d{1,}$", "AB12")
        ami_search.use_pattern("_ALLCAPS", "all_capz")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()

    @staticmethod
    def fig_caption_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.FIG_CAPTION, ])
        ami_search.use_dictionaries([])
        ami_search.use_projects([AmiProjects.CCT, ])

        ami_search.use_pattern("Fig(ure)?", "FIG")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()

    @staticmethod
    def matthew_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.FIG_CAPTION, AmiSection.METHOD])
        ami_search.use_dictionaries(
            [AmiDictionaries.ELEMENT, AmiDictionaries.CRYSTAL, AmiDictionaries.MAGNETISM])
        ami_search.use_projects([AmiProjects.LIION10, ])

        ami_search.use_pattern("^[A-Z]{1,}[^\\s]*\\d{1,}$", "AB12")
        ami_search.use_pattern("_ALLCAPS", "all_capz")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()

    @staticmethod
    def species_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.INTRO, AmiSection.METHOD])
        ami_search.use_dictionaries([])
        ami_search.use_projects([AmiProjects.OIL26, ])

        ami_search.use_pattern("^[A-Z][en]?\\.", "SPECIES_ABB")
        ami_search.use_pattern("_ITALICS", "_italics")

        ami_search.run_search()

    @staticmethod
    def invasive_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.SECTIONS])
        ami_search.use_dictionaries([AmiDictionaries.INVASIVE_PLANT])
        ami_search.use_dictionaries(
            [AmiDictionaries.PLANT_GENUS])  # to check it works
        ami_search.use_projects([AmiProjects.C_INVASIVE])
        ami_search.use_projects([AmiProjects.OIL186])

        ami_search.run_search()

    @staticmethod
    def disease_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 1
        ami_search.max_bars = 200

        ami_search.use_sections(
            [AmiSection.METHOD, AmiSection.RESULTS, AmiSection.ABSTRACT])
        ami_search.use_dictionaries(
            [AmiDictionaries.DISEASE, AmiDictionaries.MONOTERPENE])
        ami_search.use_projects([AmiProjects.OIL186])

        ami_search.run_search()

    @staticmethod
    def luke_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.METHOD, ])
        ami_search.use_dictionaries([AmiDictionaries.ELEMENT])
        ami_search.use_projects([AmiProjects.FFML20, ])

        ami_search.use_pattern("^[A-Z]{1,}[^\\s]*\\d{1,}$", "AB12")
        ami_search.use_pattern("_ALLCAPS", "all_capz")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()

    @staticmethod
    def worc_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.METHOD])
        ami_search.use_dictionaries([AmiDictionaries.ELEMENT])
        ami_search.use_dictionaries([AmiDictionaries.SOLVENT])
        ami_search.use_dictionaries([AmiDictionaries.NMR])
        ami_search.use_projects(
            [AmiProjects.WORC_EXPLOSION, AmiProjects.WORC_SYNTH])

        ami_search.use_pattern("^[A-Z]{1,}[^\\s]*\\d{1,}$", "AB12")
        ami_search.use_pattern("_ALLCAPS", "all_capz")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()

    @staticmethod
    def word_demo():
        ami_search = AmiSearch()
        ami_search.min_hits = 2

        ami_search.use_sections([AmiSection.METHOD])
        ami_search.use_projects(
            [AmiProjects.WORC_EXPLOSION, AmiProjects.WORC_SYNTH])

        ami_search.use_pattern("^[A-Z]{1,}[^\\s]*\\d{1,}$", "AB12")
        ami_search.use_pattern("_ALLCAPS", "all_capz")
        ami_search.use_pattern("_ALL", "_all")

        ami_search.run_search()
