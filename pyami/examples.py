import logging
import os
from pyami import PyAMI

class Examples():
    """runs pyami with various examples of commands

    experimental
    """
    def __init__(self, pyamix=None):
        self.logger = logging.getLogger("examples")
        self.pyamix = pyamix if pyamix is not None else PyAMI()

    def example_glob(self):
        """ """
        import os
        """
        /Users/pm286/projects/openDiagram/physchem/resources/oil26/PMC4391421/sections/0_front/1_article-meta/17_abstract.xml
        """
        """
        python pyami.py\
            --glob /Users/pm286/projects/openDiagram/physchem/resources/oil26/PMC4391421/sections/0_front/1_article-meta/17_abstract.xml\
            --proj /Users/pm286/projects/openDiagram/physchem/resources/oil26\
            --apply xml2txt\
            --combine concat_str\
            --outfile /Users/pm286/projects/openDiagram/physchem/resources/oil26/files/xml_files.txt\
    OR
     python physchem/python/pyami.py --glob '/Users/pm286/projects/openDiagram/physchem/resources/oil26/**/*abstract.xml' --proj /Users/pm286/projects/openDiagram/physchem/resources/oil26 --apply xml2txt --combine concat_str --outfile /Users/pm286/projects/openDiagram/physchem/resources/oil26/files/xml_files.txt
    MOVING TO
     python pyami.py --proj ${oil26} --glob '**/*abstract.xml' --apply xml2txt --combine to_csv --outfile ${oil26}/files/abstracts.csv
    
        """
        self.pyamix.run_commands([
            "--proj", "${oil26.p}",
            "--glob", "${proj}/**/sections/**/*abstract.xml",
            "--dict", "${eo_plant.d}", "${ov_country.d}",
            "--apply", "xml2txt",
            "--combine", "concat_str",
            "--outfile", "${proj}/files/shweata_10.txt",
            "--assert", "file_exists(${proj}/files/xml_files.txt)",
        ])


    # "--config", # defaults to config.ini,~/pyami/config.ini if omitted

    # on the commandline:
    # python physchem/python/pyami.py --proj '${oil26.p}' --glob '${proj}/**/sections/**/*abstract.xml' --dict '${eo_plant.d}' '${ov_country.d}' --apply xml2txt --combine concat_str --outfile '${proj}/files/shweata_1.txt'
    # whihc expands to
    # python physchem/python/pyami.py --apply xml2txt --combine concat_str --dict '/Users/pm286/projects/CEVOpen/dictionary/eoPlant/eo_plant.xml' '/Users/pm286/dictionary/openvirus20210120/country/country.xml' --glob '/Users/pm286/projects/openDiagram/physchem/resources/oil26/**/sections/**/*abstract.xml' --outfile '/Users/pm286/projects/openDiagram/physchem/resources/oil26/files/shweata_1.txt' --proj '/Users/pm286/projects/openDiagram/physchem/resources/oil26'

    def example_xml2sect(self):

        from shutil import copyfile
        self.banner(self.example_xml2sect.__name__)

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "tst", "proj"))
        assert (os.path.exists(proj_dir), "DIR DOES NOT EXIST")
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

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "tst", "proj"))
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.pd.txt",
            "--split", "txt2para",
            "--outfile", "fulltext.pd.sc.txt",
            "--assert", "file_glob_count(${proj}/*/fulltext.pd.sc.txt,291)"
        ])


    def example_split_sentences(self):
        from shutil import copyfile
        self.banner(self.example_split_sentences.__name__)
        self.logger.loglevel = logging.DEBUG

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "tst", "proj"))
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
        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "..", "resources", "oil26"))
        self.banner(self.example_split_oil26.__name__)
        print("file", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.xml",
            "--split", "xml2sect",
        ])


    def example_filter(self):
        self.banner(self.example_filter.__name__)

        proj_dir = self.pyamix.get_symbol("oil26.p")
        print(f"proj_dir {proj_dir}")
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
        proj_dir = self.pyamix.get_symbol("oil26.p")
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

        from shutil import copyfile

        proj_dir = os.path.abspath(os.path.join(__file__, "..", "tst", "proj"))
        assert os.path.exists(proj_dir), f"proj_dir {proj_dir} exists"
        self.pyamix.run_commands([
            "--proj", proj_dir,
            "--glob", "${proj}/*/fulltext.pdf",
            "--apply", "pdf2txt",
            "--outfile", "fulltext.pd.txt",
            # "--assert",
            #     "file_glob_count(${proj}/*/fulltext.pd.txt,3)",
        ])

    def banner(self, msg):
        print(f"===================={msg}==================")
        print(f"====================       ==================")

    def run_examples(self):
        self.example_glob() # also does sectioning?

        # self.example_pdf2txt()
        # self.example_split_pdf_txt_paras()

        print(f"========================example_xml2sect======================")
        self.example_xml2sect()
        self.example_split_oil26()

        self.example_split_sentences()
        self.example_xml2sect()
        self.example_filter()
        # self.example_filter_species()

def main():
    examples = Examples()
    # test_me = PyAMITest()
    # test_me.run_tests()
    examples.run_examples()

if __name__ == "__main__":
    main()

else:

    print("running search main anyway")
    main()

