import logging
logging.info("loading pyami.py")
import sys
import os
import re
import glob
import lxml.etree as etree

from file_lib import FileLib
from xml_lib import XmlLib
from text_lib import TextUtil
from text_lib import DSLParser
from pdfreader import PdfReader
from symbol import SymbolIni
import pprint
import ast


class PyAMI:
    """ """
    OUTFILE       = "outfile"

    # flags
    APPLY         = "apply"
    ASSERT        = "assert"
    CHECK_URLS    = "check_urls"
    COMBINE       = "combine"
    CONTAINS      = "contains"
    FILTER        = "filter"
    GLOB          = "glob"
    PRINT_SYMBOLS = "print_symbols"
    PROJ          = "proj"
    RECURSE       = "recurse"
    REGEX         = "regex"
    SECT          = "sect"
    SPLIT         = "split"
    TEST          = "test"
    XPATH         = "xpath"
    # apply methods 1:1 input-output
    PDF2TXT       = "pdf2txt"
    TXT2SENT      = "txt2sent"
    XML2TXT       = "xml2txt"
    # combine methods n:1 input-output
    CONCAT_STR    = "concat_str"
    # split methods 1:n input-output
    TXT2PARA      = "txt2para"
    XML2SECT      = "xml2sect"
    # symbols to update table
    NEW_SYMBOLS   = ["proj"]
    LOGLEVEL      = "loglevel"

    logger = logging.getLogger("pyami")
    symbol_ini = None

    def __init__(self):
        self.args = {} # args captured in here as name/value without "-" or "--"
        self.apply = []
        self.combine = None
        self.config = None
        self.current_file = None
        self.fileset = None
        self.file_dict = {}
        self.func_dict = {}
        self.result = None
        self.set_flags()
        self.symbol_ini = SymbolIni(self)
        self.set_funcs()
        self.show_symbols = False
        if self.show_symbols:
            pprint.pp(f"SYMBOLS\n {self.symbol_ini.symbols}")

    def set_flags(self):
        """ """
        self.flag_dict = {}
        self.flag_dict[self.APPLY] = None
        self.flag_dict[self.CHECK_URLS] = None
        self.flag_dict[self.COMBINE] = None
        self.flag_dict[self.PRINT_SYMBOLS] = None
        self.flag_dict[self.RECURSE] = True

    def set_funcs(self):
        """ """
        # 1:1 methods
        self.func_dict[self.XML2TXT] = XmlLib.remove_all_tags
        self.func_dict[self.PDF2TXT] = PdfReader.read_and_convert
        self.func_dict[self.TXT2SENT] = TextUtil.split_into_sentences
        # 1:n methods


    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline"""
        import argparse
        parser = argparse.ArgumentParser(description='Search sections with dictionaries and patterns')
        # apply_choices = [self.PDF2TXT, self.TXT2SENT, self.XML2TXT]
        # print("ch", apply_choices)
        parser.add_argument('--apply', nargs="+",
                            choices=['pdf2txt','txt2sent','xml2txt'],
                            help='list of sequential transformations (1:1 map) to apply to pipeline ({self.TXT2SENT} NYI)')
        parser.add_argument('--assert', nargs="+",
                            help='assertions; failure gives error message (prototype)')
        parser.add_argument('--combine', nargs=1,
                            help='operation to combine files into final object (e.g. concat text or CSV file')
        parser.add_argument('--config', '-c', nargs="*", default="PYAMI",
                            help='file (e.g. ~/pyami/config.ini) with list of config file(s) or config vars')
        parser.add_argument('--debug', nargs="+",
                            help='debugging commands , numbers, (not formalised)')
        parser.add_argument('--demo', nargs="*",
                            help='simple demos (NYI). empty gives list. May need downloading corpora')
        parser.add_argument('--dict', '-d', nargs="+",
                            help='dictionaries to ami-search with, _help gives list')
        parser.add_argument('--filter', nargs="+",
                            help='expr to filter with')
        parser.add_argument('--glob', '-g', nargs="+",
                            help='glob files; python syntax (* and ** wildcards supported); '
                                 'include alternatives in {...,...}. ')
        # parser.add_argument('--help', '-h', nargs="?",
        #                     help='output help; (NYI) an optional arg gives level')
        parser.add_argument('--languages', nargs="+", default=["en"],
                            help='languages (NYI)')
        parser.add_argument('--loglevel', '-l', default="info",
                            help='log level (NYI)')
        parser.add_argument('--maxbars', nargs="?", type=int, default=25,
                            help='max bars on plot (NYI)')
        parser.add_argument('--nosearch', action="store_true",
                            help='search (NYI)')
        parser.add_argument('--outfile', type=str,
                            help='output file, normally 1. but (NYI) may track multiple input dirs (NYI)')
        parser.add_argument('--patt', nargs="+",
                            help='patterns to search with (NYI); regex may need quoting')
        parser.add_argument('--plot', action="store_false",
                            help='plot params (NYI)')
        parser.add_argument('--proj', '-p', nargs="+",
                            help='projects to search; _help will give list')
        parser.add_argument('--sect', '-s', nargs="+",  # default=[AmiSection.INTRO, AmiSection.RESULTS],
                            help='sections to search; _help gives all(?)')
        parser.add_argument('--split', nargs="+", choices=['txt2para','xml2sect'], # split fulltext.xml,
                            help='split fulltext.* into paras, sections')
        parser.add_argument('--test', nargs="*",
                            choices=['file_lib', 'pdf_lib', 'text_lib'], # tests,
                            help='run tests for modules; no selection runs all')
        return parser

    def run_commands(self, arglist=None):
        """parses cmdline, runs cmds and outputs symbols

        :param arglist:  (Default value = None)

        """

        self.logger.info(f"********** raw arglist {arglist}")
        self.parse_and_run_args(arglist)
        if self.flagged(self.PRINT_SYMBOLS):
            self.symbol_ini.print_symbols()


    def parse_and_run_args(self, arglist):
        """runs cmds and makes substitutions (${...} then runs workflow

        :param arglist: 

        """
        if arglist is None:
            arglist = []
        parser = self.create_arg_parser()
        self.args = self.extract_parsed_arg_tuples(arglist, parser)
        self.logger.info("ARGS: "+str(self.args))
        self.substitute_args()
        self.set_loglevel_from_args()
        self.run_workflows()

    def substitute_args(self):
        """ """
        new_items = {}
        for item in self.args.items():
            new_item = self.make_substitutions(item)
            self.logger.debug(f"++++++++{item} ==> {new_item}")
            new_items[new_item[0]] = new_item[1]
        self.args = new_items
        self.logger.info(f"******** substituted ARGS {self.args}")

    def run_workflows(self):
        """ """
        # file workflow
        self.logger.warning(f"commandline args {self.args}")
        if self.PROJ in self.args:
            if self.SECT in self.args or self.GLOB in self.args:
                self.run_file_workflow()
        if self.TEST in self.args:
            print(f"TEST in **args {self.args}")
            self.run_arg_tests()


    def make_substitutions(self, item):
        """

        :param item: 

        """
        old_val = item[1]
        key = item[0]
        new_val = None
        if old_val is None:
            new_val = None
        elif isinstance(old_val, list) and len(old_val) ==1: # single string in list
            # not sure of list, is often used when only one value
            val_item = old_val[0]
            new_val = self.symbol_ini.replace_symbols_in_arg(val_item)
        elif isinstance(old_val, list):
            new_list = []
            for val_item in old_val:
                new_v = self.symbol_ini.replace_symbols_in_arg(val_item)
                new_list.append(new_v)
            self.logger.debug(f"UPDATED LIST ITEMS: {new_list}")
            new_val = new_list
        elif isinstance(old_val, (int, bool, float, complex)):
            new_val = old_val
        elif isinstance(old_val, str):
            if "${" in old_val:
                self.logger.debug(f"Unresolved reference : {old_val}")
                new_val = self.symbol_ini.replace_symbols_in_arg(old_val)
            else:
                new_val = old_val
                # new_items[key] = new_val
        else:
            self.logger.error(f"{old_val} unknown arg type {type(old_val)}")
            new_val = old_val
        self.add_selected_keys_to_symbols_ini(key, new_val)
        return (key, new_val)

    def get_symbol(self, symb):
        """gets symbol from pyami symbol table

        """
        return self.symbol_ini.symbols.get(symb)

    def extract_parsed_arg_tuples(self, arglist, parser):
        """

        :param arglist: 
        :param parser: 

        """
        parsed_args = parser.parse_args() if not arglist else parser.parse_args(arglist)
        self.logger.info(f"PARSED_ARGS {parsed_args}")
        args = {}
        arg_vars = vars(parsed_args)
        new_items = {}
        for item in arg_vars.items():
            new_item = self.make_substitutions(item)
            new_items[new_item[0]] = new_item[1]
        return new_items

    def add_selected_keys_to_symbols_ini(self, key, value):
        """

        :param key: 
        :param value: 

        """
        if key in self.NEW_SYMBOLS:
            self.symbol_ini.symbols[key] = value

    def set_loglevel_from_args(self):
        """ """
        levels = {
            "debug" : logging.DEBUG,
            "info" : logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }

        if self.LOGLEVEL in self.args:
            loglevel = self.args[self.LOGLEVEL]
            self.logger.info(f"loglevel {loglevel}")
            if loglevel is not None:
                loglevel = str(loglevel)
            if loglevel is not None and loglevel.lower() in levels:
                level = levels[loglevel.lower()]
                self.logger.setLevel(level)

    def run_file_workflow(self):
        """ """
        # import glob
        # import pathlib
        # import file_lib
        # self.logger.info("globbing")
        self.logger.debug(f"ARGS {self.args}")
        if not self.args:
            self.logger.error("no args given; try --proj or --test")
        elif self.args[self.PROJ]:
            self.run_proj()
        elif self.args[self.TEST]:
            self.run_arg_tests()
        else:
            self.logger.error("{self.args} requires --proj or --test")
        return

    def run_proj(self):
        self.proj = self.args[self.PROJ]
        if self.args[self.GLOB]:
            self.glob_files()
        if self.args[self.SPLIT]:
            self.split(self.args.get(self.SPLIT))
        if self.args[self.APPLY]:
            self.apply_func(self.args.get(self.APPLY))
        if self.args[self.FILTER]:
            self.filter_file()
        if self.args[self.COMBINE]:
            self.combine_files_to_object()
        if self.args[self.OUTFILE]:
            self.write_output()
        if self.args[self.ASSERT]:
            self.run_assertions()

    def run_arg_tests(self):
        self.logger.warning(f"*****running tests : {self.args[self.TEST]}")
        _TESTS = ["file_lib", "pdf_lib", "text_lib"]
        if not self.args[self.TEST]:
            print (f"No tests given: choose some/all of {_TESTS}")
            return
        if "file_lib" in self.args[self.TEST]:
            import test_file
            print("run test_file")
            test_file.main()
        if "pdf_lib" in self.args[self.TEST]:
            import test_pdf
            print("run test_pdf")
            test_pdf.test_read_pdf()
        if "text_lib" in self.args[self.TEST]:
            # import test_text
            print("run test_text NYI")
            # test_text.main()

    def glob_files(self):
        import glob
        glob_recurse = self.flagged(self.RECURSE)
        glob_ = self.args[self.GLOB]
        self.logger.info(f"glob: {glob_}")
        self.file_dict = {file: None for file in glob.glob(glob_, recursive=glob_recurse)}
        self.logger.info(f"glob file count {len(self.file_dict)}")

    def split(self, type):
        """ split fulltext.xml into sections"""

        for file in self.file_dict:
            suffix = FileLib.get_suffix(file)
            if ".xml" == suffix or type==self.XML2SECT:
                self.make_xml_sections(file)
            elif ".txt" == suffix or type == self.TXT2PARA:
                self.make_text_sections(file)
            else:
                self.logger.warning(f"no match for suffix: {suffix}")


    def make_xml_sections(self, file):
        xml_libx = XmlLib();
        xml_libx.logger.setLevel(logging.DEBUG)
        doc = xml_libx.read(file)
        xml_libx.make_sections("sections")

    def make_text_sections(self, file):
        sections = []
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            sections = TextUtil.split_at_empty_newline(text)
        self.file_dict[file] = sections
        for sect in sections:
            print(sect)


    def apply_func(self, apply_type):
        """ """
        self.read_file_content()
        if apply_type :
            self.logger.info(f"apply {apply_type}")
            func = self.func_dict[apply_type]
            if (func is None):
                self.logger.error(f"Cannot find func for {apply_type}")
            else:
                # apply data is stored in self.file_dict
                self.apply_to_file_content(func)
        return

    def normalize(self, unistr):
        import unicodedata
        print("NYI")
        unicodedata.normalize('NFKC', unistr)
        pass

    def filter_file(self):
        filter_expr = self.args[self.FILTER]
        self.logger.warning(f"filter: {filter_expr}")

        files = set()
        # record hits
        for file in self.file_dict:
            filter_true = self.apply_filter(file, filter_expr)
            if filter_true:
                files.add(file)
        # delete hits from dict
        for file in files:
            if file in self.file_dict:
                del self.file_dict[file]

    def apply_filter(self, file, filter_expr):
        found = False
        if not filter_expr:
            self.logger.error(f"No filter expression")
            return found
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        hits = []
        if isinstance(filter_expr, list):
            # and'ed at present
            for f_expr in filter_expr:
                hits = self.apply_filter_expr(content, file, f_expr, hits)
        else:
            hits = self.apply_filter_expr(content, file, filter_expr, hits)

        return hits

    def apply_filter_expr(self, content, file, filter_expr, hit_list):
        """ applies filters to hit list, usually AND"""
        if filter_expr.startswith(self.CONTAINS) and file.endswith(".txt"):
            search_str = self.get_search_string(filter_expr, self.CONTAINS)
            if search_str in content:
                hit_list.append(search_str)
        elif filter_expr.startswith(self.XPATH) and file.endswith(".xml"):
            xpath_str = self.get_search_string(filter_expr, self.XPATH)
            tree = etree.parse(file)
            # print(f"xpath: {xpath_str}")
            hits = tree.xpath(xpath_str)
            hit_list.extend(hits)
        elif filter_expr.startswith(self.REGEX):
            hits = self.apply_regex(hit_list, self.get_search_string(filter_expr, self.REGEX))
            if hits:
                print(f"hits {hits}")
                hit_list = hits
        return hit_list

    def apply_regex(self, hits, regex):
        print(f"REGEX {regex}")
        return [hit for hit in hits if re.match(regex, hit)]

    def get_search_string(self, filter_expr, search_method):
        return filter_expr[len(search_method) + 1:-1]

    def read_file_content(self, to_str=True):
        """read file content as bytes into file_dict
        
        :to_str: if true convert content to strings

        :param to_str:  (Default value = True)

        """
        for file in self.file_dict:
            self.logger.info(f"reading {file}")
            if file.endswith(".xml"):
                self.read_string_content(file, to_str)
            elif file.endswith(".pdf"):
                self.lazy_read_binary_file(file)
            elif file.endswith(".png"):
                self.read_binary_content(file)
            elif file.endswith(".txt"):
                self.read_string_content(file, to_str=False)
            else:
                self.logger.warning(f"cannot read file into string {file}")


    def read_string_content(self, file, to_str):
        """reads file into string
        Can process bytes to string

        """
        data = None
        with open(file, "r", encoding="utf-8") as f:
            try:
                data = f.read()
                if to_str and isinstance(data, bytes):
                    data = data.decode("utf-8")
                self.file_dict[file] = data
            except UnicodeDecodeError as ude:
                self.logger.error(f"skipped decoding error {ude}")
        return data

    def lazy_read_binary_file(self, file):
        self.file_dict[file] = file

    def read_binary_content(self, file):
        with open(file, "rb", ) as f:
            try:
                data = f.read()
                self.file_dict[file] = data
            except Error as e:
                self.logger.error(f"skipped reading error {e}")

    def apply_to_file_content(self, func):
        """applies func to all string content in file_dict

        :param func: 

        """
        for file in self.file_dict:
            data = self.file_dict.get(file)
            self.logger.warning(f"file: {file} => {type(data)} => {func}")
            new_data = func(data)
            self.file_dict[file] = new_data
        return

    def combine_files_to_object(self):
        """ """
        methods = self.args.get(self.COMBINE)
        if methods and methods == self.CONCAT_STR:
            self.result = "\n".join(self.file_dict.values())
            # print(self.result)

    def write_output(self):
        """ """
        self.outfile = self.args[self.OUTFILE]
        if self.result: # single output
            self.write_single_result()

        if self.file_dict:
            self.write_multiple_results()

    def write_multiple_results(self):
        for file in self.file_dict:
            data = self.file_dict[file]
            parent = FileLib.get_parent_dir(file)
            new_outfile = os.path.join(parent, self.outfile)
            # if not isinstance(data, list):
            #     # data = [data]
            #     pass # this was a  mistake
            with open(new_outfile, "w", encoding="utf-8") as f:
                self.logger.warning(f"wrote results {new_outfile}")
                # for d in data:
                f.write(f"{str(data)}")

    def write_single_result(self):
        FileLib.force_write(self.outfile, self.result, overwrite=True)
        self.logger.warning(f"wrote results {self.outfile}")

    def run_assertions(self):
        """ """
        assertions = self.args.get(self.ASSERT)
        if assertions is not None:
            self.parser = DSLParser()
            if isinstance(assertions, str):
                assertions = [assertions]
            for assertion in assertions:
                self.parser.parse_and_run(assertion)

    def flagged(self, flag):
        """is flag set in flag_dict
        
        if flag is in flag_dict and not falsy return true
        :flag:

        :param flag: 

        """
        return True if self.flag_dict.get(flag) else False

    def test_glob(self):
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
        self.run_commands([
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

    def test_xml2sect(self):
        from shutil import copyfile

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "tst", "proj"))
        assert os.path.exists(proj_dir)
        # split into sections
        self.run_commands([
                        "--proj", proj_dir,
                        "--glob", "${proj}/*/fulltext.xml",
                        "--split", "xml2sect",
                        "--assert", "file_glob_count(${proj}/*/sections/**/*.xml,291)"
                        ])

    def test_split_pdf_txt_paras(self):
        self.logger.loglevel = logging.DEBUG

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "tst", "proj"))
        print("file", proj_dir, os.path.exists(proj_dir))
        self.run_commands([
                        "--proj", proj_dir,
                        "--glob", "${proj}/*/fulltext.pd.txt",
                        "--split", "txt2para",
                        "--outfile", "fulltext.pd.sc.txt",
                        "--assert", "file_glob_count(${proj}/*/fulltext.pd.sc.txt,291)"
                        ])

    def test_split_sentences(self):
        from shutil import copyfile
        self.logger.loglevel = logging.DEBUG

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "tst", "proj"))
        print("file", proj_dir, os.path.exists(proj_dir))
        self.run_commands([
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

    def test_split_oil26(self):

        proj_dir = os.path.abspath(os.path.join(__file__, "../src", "..", "resources", "oil26"))
        print("file", proj_dir, os.path.exists(proj_dir))
        self.run_commands([
                        "--proj", proj_dir,
                        "--glob", "${proj}/*/fulltext.xml",
                        "--split", "xml2sect",
                        ])

    def test_filter(self):
        from shutil import copyfile

        # proj_dir = os.path.abspath(os.path.join(__file__, "..", "tst", "proj"))
        proj_dir = self.get_symbol("oil26.p")
        print(f"proj_dir {proj_dir}")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.run_commands([
                        "--proj", proj_dir,
                        "--glob", "${proj}/**/*_p.xml",
                        "--apply", "xml2txt",
                        "--filter", "contains(cell)",
                        "--combine", "concat_str",
                        "--outfile", "cell.txt"
                        ])

    def test_filter_italics(self):
        from shutil import copyfile

        # proj_dir = os.path.abspath(os.path.join(__file__, "..", "tst", "proj"))
        # prof_dir = ${oil26}
        proj_dir = self.get_symbol("oil26.p")
        print("file", proj_dir, os.path.exists(proj_dir))
        self.run_commands([
                        "--proj", proj_dir,
                        "--glob", "${proj}/**/*_p.xml",
                        "--filter", "xpath('//p//italic/text()')",
                        # "regex('[A-Z][a-z]+\s+[a-z]{3,}')",
                        "--combine", "concat_xml",
                        "--outfile", "italic.xml"
                        ])


    def test_pdf2txt(self):
        from shutil import copyfile

        proj_dir = os.path.abspath(os.path.join(__file__, "..", "tst", "proj"))
        assert os.path.exists(proj_dir), f"proj_dir {proj_dir} exists"
        self.run_commands([
                        "--proj", proj_dir,
                        "--glob", "${proj}/*/fulltext.pdf",
                        "--apply", "pdf2txt",
                        "--outfile", "fulltext.pd.txt",
                        # "--assert",
                        #     "file_glob_count(${proj}/*/fulltext.pd.txt,3)",
        ])

    def run_tests(self):
        # self.test_glob() # also does sectioning?

        # self.test_pdf2txt()
        # self.test_split_pdf_txt_paras()

        # self.test_xml2sect()
        # self.test_split_oil26()

        # self.test_split_sentences()
        # self.test_xml2sect()
        # self.test_filter()
        self.test_filter_italics()




def main():
    """ main entry point for cmdline

    """

    run_dsl = False
    run_tests = True
    run_commands = False

    print(f"\n============== running pyami main ===============\n{sys.argv[1:]}")
    # this needs commandline
    if run_commands:
        PyAMI().run_commands()
    # pyami.run_tests()
    if run_dsl:
        DSLParser.run_tests(sys.argv[1:])
    if run_tests:
        PyAMI().run_tests()
    # pyami.run_commands(sys.argv[1:])


if __name__ == "__main__":

    print(f"sys.argv: {sys.argv}")
    main()

else:

    print("running search main anyway")
    main()
