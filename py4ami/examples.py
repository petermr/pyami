import logging
import os
import tempfile
import shutil
from PIL import Image
from pathlib import Path
import glob

logger = logging.getLogger("examples")


class Examples:
    """runs pyami with various examples of commands

    experimental
    """

    def __init__(self, pyamix=None):
        # self.pyamix = pyamix if pyamix is not None else PyAMI()
        self.logger = logger
        self.pyamix = pyamix
        self.test_copy_dir = None

    def example_help(self):
        """checks whether parser works"""
        print(f" symbols {self.pyamix.symbol_ini.symbols.keys()}")
        self.pyamix.commandline("--help")

    def example_symbols(self):
        """checks whether parser works
        debugs symbols"""
        self.pyamix.commandline("--debug symbols")

    def setup(self):
        proj_dir = Path(Path(__file__).parent, "resources/projects/oil4")

        assert os.path.exists(proj_dir), "path {proj_dir}"
        self.test_copy_dir = tempfile.TemporaryDirectory().name
        shutil.copytree(proj_dir, self.test_copy_dir)
        print(f"copy_dir {self.test_copy_dir}")
        return proj_dir

    def teardown(self):
        if os.path.exists(self.test_copy_dir):
            shutil.rmtree(self.test_copy_dir)

    def example_copy(self):
        self.pyamix.run_command([
            "--copy", "${examples_test.p}", "${temp_dir}/examples", "overwrite",
            "--assert", "file_exists(${temp_dir}/examples/files/xml_files.txt)",
        ])

    def example_delete(self):
        self.banner(self.example_delete.__name__)

        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--delete", "**/*_p.xml", "**/*_p.xml.txt", "*/sections/", "**/italic.xml", "**/cell.txt"
        ])

    def example_glob0(self):
        """ globs fig.xml files
        creates a globbed list of filenames
        then iterates through this and identifies and writes list of files to named path
        """
        # self.setup()
        self.pyamix.run_command(
            "--proj ${examples_test.p} --glob ${examples_test.p}/**/sections/**/*fig.xml"
            # f"--proj {self.test_copy_dir} --glob {self.test_copy_dir}/**/sections/**/*fig.xml" \
            # " --outfile _figures/fig0.txt"
        )
        # self.teardown()

    def example_glob00(self):
        """ globs abstracts
        """
        self.pyamix.run_command([
            "--proj", "${examples_test.p}",
            "--glob", "${examples_test.p}/**/sections/**/*abstract.xml",
            "--outfile", "_files/abstracts.csv",
        ])

    def example_captions(self):
        """ """
        self.pyamix.run_commands([
            # "--proj", "${examples_test.p}",
            # "--debug symbols",
            "--test _setup",
            # [
            # "--glob", "${examples_test.p}/**/sections/**/*fig.xml",
            # "--glob", "${exam_temp}/**/sections/**/*fig.xml",
            # "--outfile", "${exam_temp}/files/captions/",
            # ],
            # "--test _teardown",
        ])

    def example_glob(self):
        """ """

        self.pyamix.run_command([
            # "--proj", "${oil26.p}",
            "--debug", "symbols",
            "--proj", "${examples_test.p}",
            "--glob", "${examples_test.p}/**/sections/**/*abstract.xml",
            "--dict", "${eo_plant.d}", "${ov_country.d}",
            "--apply", "xml2txt",
            "--combine", "concat_str",
            "--outfile", "${examples_test.p}/files/examples.txt",
            "--assert", "file_exists(${examples_test.p}/files/xml_files.txt)",
        ])

    # "--config", # defaults to config.ini.master,~/pyami/config.ini.master if omitted

    # on the commandline:
    # python physchem/python/pyamix.py --proj '${oil26.p}' --glob '${proj}/**/sections/**/*abstract.xml'
    # --dict '${eo_plant.d}' '${ov_country.d}' --apply xml2txt --combine concat_str
    # --outfile '${proj}/files/shweata_1.txt'
    # whihc expands to
    # python physchem/python/pyamix.py --apply xml2txt --combine concat_str
    # --dict '/Users/pm286/projects/CEVOpen/dictionary/eoPlant/eo_plant.xml'
    # '/Users/pm286/dictionary/openvirus20210120/country/country.xml' -
    # -glob '/Users/pm286/projects/openDiagram/physchem/resources/oil26/**/sections/**/*abstract.xml'
    # --outfile '/Users/pm286/projects/openDiagram/physchem/resources/oil26/files/shweata_1.txt'
    # --proj '/Users/pm286/projects/openDiagram/physchem/resources/oil26'

    def example_xml2sect(self):

        self.banner(self.example_xml2sect.__name__)

        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, Path(proj_dir).exists())
        # split into sections
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--glob", "${examples_test.p}/*/fulltext.xml",
            "--split", "xml2sect",
            "--assert", "file_glob_count(${examples_test.p}/*/sections/**/*.xml,291)"
        ])

    def example_xml2sect_cmd(self):  # not yet running

        proj_dir = self.setup()
        print("path", proj_dir, os.path.exists(proj_dir))
        # split into sections
        cmd = f"python -m py4ami.pyami --proj {proj_dir} --split xml2sect"
        os.system(cmd)
        self.teardown()

    def example_split_pdf_txt_paras(self):
        self.setup()
#        self.logger.loglevel = logging.DEBUG
        self.banner(self.example_split_pdf_txt_paras.__name__)

        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--glob", "${examples_test.p}/*/fulltext.pdf.txt",
            "--split", "txt2para",
            "--outfile", "fulltext.pdf.sec.txt",
            "--assert", "file_glob_count(${examples_test.p}/*/fulltext.pdf.sec.txt,291)"
        ])
        self.teardown()

    def example_split_sentences(self):
        self.banner(self.example_split_sentences.__name__)
#        self.logger.loglevel = logging.DEBUG
        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--glob", "${examples_test.p}/*/fulltext.pdf.txt",
            "--apply", "txt2sent",
            "--outfile", "fulltext.pdf.sen.txt",
            "--split", "txt2para",
            "--assert",
            "glob_count(${examples_test.p}/*/fulltext.pd.sn.txt,3)",
            "len(${examples_test.p}/PMC4391421/fulltext.pd.sn.txt,181)",
            "item(${examples_test.p}/PMC4391421/fulltext.pd.sn.txt,0,)",

        ])

    def example_split_oil26(self):
        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.banner(self.example_split_oil26.__name__)
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--glob", "${examples_test.p}/*/fulltext.xml",
            "--split", "xml2sect",
        ])

    def example_filter(self):
        self.banner(self.example_filter.__name__)

        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--glob", "${examples_test.p}/**/*_p.xml",
            "--apply", "xml2txt",
            "--filter", "contains(cell)",
            "--combine", "concat_str",
            "--outfile", "${examples_test.p}/results/cell.txt"
        ])

    def example_filter_species(self):
        self.banner(self.example_filter_species.__name__)
        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,  # "/Users/pm286/projects/openDiagram/physchem/resources/oil26",
            "--glob", "${examples_test.p}/**/*_p.xml",
            "--filter",
            "xpath(${all_italics.x})",  # "xpath(//p//italic/text())",
            # "regex([A-Z][a-z]?(\.|[a-z]{2,})\s+[a-z]{3,})",
            "regex(${species.r})",
            "dictionary(${eo_plant.d})",  # local, snowballed
            # "lookup(wikidata)", # crude and obsolete
            "wikidata_sparql(${taxon_name.w})",  # "wikidata_sparql(P225)",
            # "_NOT", "dictionary(stopwrds)"
            # plants
            # SELECT ?item ?itemLabel
            # WHERE {?item wdt: P225 "Ocimum sanctum".
            # SERVICE wikibase: label_xml {bd: serviceParam wikibase: language "[AUTO_LANGUAGE],en".}
            # }
            # "wiki_sparql(read sparql_query"Qxxx for plant_species")"
            # "--update(eo_plant.d),"
            # " --dict", "${eo_plant.d}",
            "--combine", "concat_xml",
            "--outfile", "italic.xml"
        ])

    def example_pdf2txt(self):
        self.banner(self.example_pdf2txt.__name__)

        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print(f"path {proj_dir} exists= {os.path.exists(proj_dir)}")
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--glob", "${examples_test.p}/*/fulltext.pdf",
            "--apply", "pdf2txt",
            "--outfile", "fulltext.pdf.txt",
        ])

    def example_search(self):
        self.banner(self.example_search.__name__)
        print(f" search not yet working")
        return
        proj_dir = self.pyamix.get_symbol("examples_test.p")
        dict_file = self.pyamix.get_symbol("mini_plant.d")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--search", dict_file,
        ])

    def example_words(self):
        self.banner(self.example_words.__name__)
        print(f" words not yet working")
        return
        proj_dir = self.pyamix.get_symbol("examples_test.p")
        print("path", proj_dir, os.path.exists(proj_dir))
        self.pyamix.run_command([
            "--proj", proj_dir,
            "--words",
        ])

    @classmethod
    def banner(cls, msg):
        print(f"===================={msg}==================")
        ss = " "*len(msg)
        print(f"===================={ss}==================")

    def run_examples(self, example_list):
        """WARNING:symbol.ini:0 6 proj /Users/pm286/projects/openDiagram/physchem/resources/oil26
        this is being pulled from somewhere?"""
        example_dict = {
            "ca": (self.example_captions, "captions"),
            "cp": (self.example_copy, "copy files"),
            "de": (self.example_delete, "deleting files"),
            "fi": (self.example_filter, "simple filter (not complete)"),
            "g0": (self.example_glob0, "globbing files"),
            "gl": (self.example_glob, "globbing files"),
            "pd": (self.example_pdf2txt, "convert pdf to text"),
            "pa": (self.example_split_pdf_txt_paras, "split pdf text into paragraphs"),
            "sc": (self.example_xml2sect, "split xml into sections"),
            "scd": (self.example_xml2sect_cmd(), "split xml into sections using cmd"),
            #             "sl": (self.example_split_oil26, "split oil4 project into sections"),
            "se": (self.example_split_sentences, "split text to sentences"),
            "sp": (self.example_filter_species, "extract species with italics and regex (not finalised)"),
            "sr": (self.example_search, "search with dictionaries (NYI)"),
            "wd": (self.example_words, "extract words (NYI"),
        }
        if not example_list:
            print(f"choose example from:")
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
            self.logger.warning(f"EXAMPLE {example}")
            if example in example_dict:
                print(f"\n\n\n"
                      f"+++++++++++++++++++++++++++++++++++++++\n"
                      f"                    {example}\n"
                      f"+++++++++++++++++++++++++++++++++++++++\n")
                func = example_dict[example][0]
                self.logger.debug(f"EXAMPLE_FUNC .. {func}")
                try:
                    func()
                except ValueError as e:
                    self.logger.critical(f"example {example} failed {e}")

            elif example is not None:
                print(
                    f"unknown example: {example}\nchoose from: {example_dict.keys()}")

    def transform_img_to_png(self, file):

        outfile = Path(file + ".png")  # change this
        print(f"path: {outfile}")
        try:
            with Image.open(file) as im:
                print(file, im.format, f"{im.size}x{im.mode}")
        except OSError:
            print(f"cannot convert image {file}")
            if False:
                try:
                    with open(file, "rb") as buffer:
                        # buf = io.BytesIO(buffer)
                        bb = buffer.read()
                        bbx = binascii.unhexlify(bb)
                        im = Image.open(bbx)
                except OSError:
                    print(f"cannot parse {file}")
        # with Image.open(path) as image:
        #     print(f" binary {f}")
        #     image.save(outfile)

    def transform_images_to_png(self):
        """These images are from pdfminer3 - they can't be parsed"""
        globstr = "/Users/pm286/misc/images/*.img"
        files = glob.glob(globstr)
        # files = Globber(globstr).get_globbed_files()
        for ff in files:
            self.transform_img_to_png(ff)


"""
from io import BytesIO

imagefile = BytesIO()
animage.save(imagefile, format='PNG')
imagedata = imagefile.getvalue()
"""


def main():
    from py4ami.pyamix import PyAMI
    examples = Examples(PyAMI())
    # examples.example_help()
    # examples.run_examples(None)
    # examples.run_examples(["all"])
    # examples.run_examples(["g0"])
    # examples.run_examples(["gl"])
#    examples.run_examples(["sc"]) # works
    examples.run_examples(["scd"])
    # examples.example_symbols()
    # examples.example_pdf2txt()
    # examples.run_examples(["sc"])
    # examples.transform_images_to_png() # fails
    # examples.logger.warning(f"calling examples directory will be phased out")
    # print(f" examples args: {sys.argv}")
    # # test_me = PyAMITest()
    # # test_me.run_tests()
    # examples.run_examples(sys.argv[1:])


if __name__ == "__main__":
    main()

else:
    logger.debug("not running main()")
