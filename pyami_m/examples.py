import logging
import os
import sys

logger = logging.getLogger("examples")

class Examples():
    """runs pyami with various examples of commands

    experimental
    """
    from pyami_m.pyamix import PyAMI

    pyamix = PyAMI()
    def __init__(self, pyamix=None):
        # self.pyamix = pyamix if pyamix is not None else PyAMI()
        self.logger = logger
        pass

    def example_glob(self):
        """ """

        self.pyamix.run_commands([
            # "--proj", "${oil26.p}",
            "--debug", "debug", "symbols",
            "--proj", "${misc4.p}",
            "--glob", "${proj}/**/sections/**/*abstract.xml",
            "--dict", "${eo_plant.d}", "${ov_country.d}",
            "--apply", "xml2txt",
            "--combine", "concat_str",
            "--outfile", "${proj}/files/misc4.txt",
            "--assert", "file_exists(${proj}/files/xml_files.txt)",
        ])


    # "--config", # defaults to config.ini,~/pyami/config.ini if omitted

    # on the commandline:
    # python physchem/python/pyamix.py --proj '${oil26.p}' --glob '${proj}/**/sections/**/*abstract.xml' --dict '${eo_plant.d}' '${ov_country.d}' --apply xml2txt --combine concat_str --outfile '${proj}/files/shweata_1.txt'
    # whihc expands to
    # python physchem/python/pyamix.py --apply xml2txt --combine concat_str --dict '/Users/pm286/projects/CEVOpen/dictionary/eoPlant/eo_plant.xml' '/Users/pm286/dictionary/openvirus20210120/country/country.xml' --glob '/Users/pm286/projects/openDiagram/physchem/resources/oil26/**/sections/**/*abstract.xml' --outfile '/Users/pm286/projects/openDiagram/physchem/resources/oil26/files/shweata_1.txt' --proj '/Users/pm286/projects/openDiagram/physchem/resources/oil26'

    def example_xml2sect(self):

        self.banner(self.example_xml2sect.__name__)

        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        # split into sections
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.xml",
            "--split", "xml2sect",
            "--assert", "file_glob_count(${proj}/*/sections/**/*.xml,291)"
        ])


    def example_split_pdf_txt_paras(self):
        self.logger.loglevel = logging.DEBUG
        self.banner(self.example_split_pdf_txt_paras.__name__)

        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.pd.txt",
            "--split", "txt2para",
            "--outfile", "fulltext.pd.sc.txt",
            "--assert", "file_glob_count(${proj}/*/fulltext.pd.sc.txt,291)"
        ])


    def example_split_sentences(self):
        self.banner(self.example_split_sentences.__name__)
        self.logger.loglevel = logging.DEBUG
        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.pd.txt",
            "--apply", "txt2sent",
            "--outfile", "fulltext.pd.sn.txt",
            "--split", "txt2para",
            "--assert",
            "glob_count(${proj}/*/fulltext.pd.sn.txt,3)",
            "len(${proj}/PMC4391421/fulltext.pd.sn.txt,181)",
            "item(${proj}/PMC4391421/fulltext.pd.sn.txt,0,)",

        ])


    def example_split_oil26(self):
        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.banner(self.example_split_oil26.__name__)
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.xml",
            "--split", "xml2sect",
        ])


    def example_filter(self):
        self.banner(self.example_filter.__name__)

        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/**/*_p.xml",
            "--apply", "xml2txt",
            "--filter", "contains(cell)",
            "--combine", "concat_str",
            "--outfile", "cell.txt"
        ])


    def example_filter_species(self):
        self.banner(self.example_filter_species.__name__)
        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,  # "/Users/pm286/projects/openDiagram/physchem/resources/oil26",
            "--glob", "${proj}/**/*_p.xml",
            "--filter",
            "xpath(${all_italics.x})",  # "xpath(//p//italic/text())",
            "regex(${species.r})",  # "regex([A-Z][a-z]?(\.|[a-z]{2,})\s+[a-z]{3,})",
            "dictionary(${eo_plant.d})",  # local, snowballed
            # "lookup(wikidata)", # crude and obsolete
            "wikidata_sparql(${taxon_name.w})",  # "wikidata_sparql(P225)",
            # "_NOT", "dictionary(stopwrds)"
            # plants
            # SELECT ?item ?itemLabel
            # WHERE {?item wdt: P225 "Ocimum sanctum".
            # SERVICE wikibase: label {bd: serviceParam wikibase: language "[AUTO_LANGUAGE],en".}
            # }
            # "wiki_sparql(read sparql_query"Qxxx for plant_species")"
            # "--update(eo_plant.d),"
            # " --dict", "${eo_plant.d}",
            "--combine", "concat_xml",
            "--outfile", "italic.xml"
        ])


    def example_pdf2txt(self):
        self.banner(self.example_pdf2txt.__name__)

        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.pdf",
            "--apply", "pdf2txt",
            "--outfile", "fulltext.pd.txt",
        ])

    def example_delete(self):
        self.banner(self.example_delete.__name__)

        proj_dir = self.pyamix.get_symbol("misc4.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--delete", "**/*_p.xml", "**/*_p.xml.txt", "*/sections/", "**/italic.xml", "**/cell.txt"
        ])


    def banner(self, msg):
        print(f"===================={msg}==================")
        ss = " "*len(msg)
        print(f"===================={ss}==================")

    def run_examples(self, example_list):
        """WARNING:symbol.ini:0 6 proj /Users/pm286/projects/openDiagram/physchem/resources/oil26
        this is being pulled from somewhere?"""
        example_dict = {
            "de": (self.example_delete, "deleting files"),
            "gl": (self.example_glob, "globbing files"),
            "pd": (self.example_pdf2txt, "convert pdf to text"),
            "pa": (self.example_split_pdf_txt_paras, "split pdf text into paragraphs"),
            "sc": (self.example_xml2sect, "split xml into sections"),
            "sl": (self.example_split_oil26, "split oil26 project into sections"),
            "se": (self.example_split_sentences, "split text to sentences"),
            "fi": (self.example_filter, "simple filter (not complete)"),
            "sp": (self.example_filter_species, "extract species with italics and regex (not finalised)"),
        }
        if not example_list:
            print(f"choose from:")
            for abbrev in example_dict:
                print(f"{abbrev} => {example_dict[abbrev][1]}")
            print(f"\nall => all examples")
        elif len(example_list) == 1 and example_list[0] == 'all':
            self.logger.warning(f"RUNNING ALL EXAMPLES: ")
            examples_keys = list(example_dict.keys())
            #  dont use 'delete' on examples
            examples_keys.remove("de")
            self.run_example_list(example_dict, examples_keys)
        else:
            self.run_example_list(example_dict, example_list)

    def run_example_list(self, example_dict, example_list):
        for example in example_list:
            if example in example_dict:
                print(f"\n\n\n"
                      f"+++++++++++++++++++++++++++++++++++++++\n"
                      f"                    {example}\n"
                      f"+++++++++++++++++++++++++++++++++++++++\n")
                example_dict[example][0]()
            else:
                print(f"unknown example: {example}\nchoose from: {example_dict.keys()}")


def main():
    print(f" examples args: {sys.argv}")
    examples = Examples()
    # test_me = PyAMITest()
    # test_me.run_tests()
    examples.run_examples(sys.argv[1:])

if __name__ == "__main__":
    main()

else:
    logger.debug("not running main()")

