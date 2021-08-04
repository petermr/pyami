import logging
import sys
import os
import re
import glob
import lxml.etree as etree
import pprint
from collections import Counter
import traceback
from pathlib import Path

from pyami_m.dict_lib import AmiDictionary
from pyami_m.file_lib import FileLib
from pyami_m.xml_lib import XmlLib
from pyami_m.text_lib import TextUtil, DSLParser
from pyami_m.pdfreader import PdfReader
from pyami_m.symbol import SymbolIni
from pyami_m.util import AmiLogger
from pyami_m.wikimedia import WikidataLookup

logging.debug("loading pyamix.py")

class PyAMI:
    """ """
    OUTFILE       = "outfile"

    # flags
    APPLY         = "apply"
    ASSERT        = "assert"
    CHECK_URLS    = "check_urls"
    DELETE        = "delete"
    COMBINE       = "combine"
    CONTAINS      = "contains"
    DEBUG         = "debug"
    DICTIONARY    = "dictionary"
    FILTER        = "filter"
    GLOB          = "glob"
    KEEP          = "keep"
    LOOKUP        = "lookup"
    PRINT_SYMBOLS = "print_symbols"
    PROJ          = "proj"
    RECURSE       = "recurse"
    REGEX         = "regex"
    SECT          = "sect"
    SPLIT         = "split"
    SYMBOLS       = "symbols"
    TEST          = "test"
    WIKIDATA_SPARQL = "wikidata_sparql"
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

        self.logger.debug(f"===============Examples=================")
        if self.logger.getEffectiveLevel() <= logging.DEBUG:
            traceback.print_stack(file=sys.stdout)

        self.args = {} # args captured in here as name/value without "-" or "--"
        self.apply = []
        self.combine = None
        self.config = None
        self.current_file = None
        self.fileset = None
        self.file_dict = {} # possibly to be replaced by content_store.file_dict
        # self.content_store =  ContentStore(self) # will expose content_store.file_dict
        self.func_dict = {}
        self.result = None
        self.set_flags()
        self.wikidata_lookup = None
        self.wikipedia_lookup = None
        self.hit_counter = None
        self.symbol_ini = SymbolIni(self)
        self.set_funcs()
        self.show_symbols = False
        self.ami_dictionary = None
        self.ami_logger = None
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
        # tuple of func+file_extnsion
        self.func_dict[self.XML2TXT] = (XmlLib.remove_all_tags, ".xml.txt")
        self.func_dict[self.PDF2TXT] = (PdfReader.read_and_convert, ".pdf.txt")
        self.func_dict[self.TXT2SENT] = (TextUtil.split_into_sentences, ".sen.txt")
        # 1:n methods


    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline"""
        import argparse
        parser = argparse.ArgumentParser(description='Search sections with dictionaries and patterns')
        apply_choices = [self.PDF2TXT, self.TXT2SENT, self.XML2TXT]
        self.logger.debug("ch", apply_choices)
        parser.add_argument('--apply', nargs="+",
                            choices=['pdf2txt', 'txt2sent', 'xml2txt'],
                            help='list of sequential transformations (1:1 map) to apply to pipeline ({self.TXT2SENT} NYI)')
        parser.add_argument('--assert', nargs="+",
                            help='assertions; failure gives error message (prototype)')
        parser.add_argument('--delete', nargs="+",
                            help='delete globbed files. Argument/s <glob> are relative to `proj`')
        parser.add_argument('--combine', nargs=1,
                            help='operation to combine files into final object (e.g. concat text or CSV file')
        parser.add_argument('--config', '-c', nargs="*", default="PYAMI",
                            help='file (e.g. ~/pyami/config.ini) with list of config file(s) or config vars')
        parser.add_argument('--debug', nargs="+",
                            help='debugging commands , symbols, numbers, (not formalised)')
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
        parser.add_argument('--keep', nargs=1,
                            help='delete all except globbed files. Single argument <glob> is relative to `proj`')
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
        parser.add_argument('--split', nargs="+", choices=['txt2para','xml2sect'],  # split fulltext.xml,
                            help='split fulltext.* into paras, sections')
        parser.add_argument('--test', nargs="*",
                            choices=['file_lib', 'pdf_lib', 'text_lib'], # tests,
                            help='run tests for modules; no selection runs all')
        return parser

    def run_commands(self, arglist=None):
        """parses cmdline, runs cmds and outputs symbols

        :param arglist:  (Default value = None)

        """
        # if len(sys.argv) == 1:
        #     parser.print_help(sys.stderr)
        #     sys.exit()

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
        self.logger.debug("ARGS: "+str(self.args))
        self.substitute_args()
        self.logger.debug("ARGS1: "+str(self.args))
        self.set_loglevel_from_args()
        self.run_workflows()

    def substitute_args(self):
        """ """
        new_items = {}
        self.logger.debug(f"SYMBOLS1 {self.symbol_ini.symbols}")
        for item in self.args.items():
            new_item = self.make_substitutions(item)
            self.logger.debug(f"++++++++{item} ==> {new_item}")
            new_items[new_item[0]] = new_item[1]
        self.args = new_items
        self.logger.info(f"******** substituted ARGS {self.args}")

    def run_workflows(self):
        """ """
        # file workflow
        self.wikipedia_lookup = WikidataLookup()
        self.logger.warning(f"commandline args {self.args}")
        if self.PROJ in self.args:
            if self.SECT in self.args or self.GLOB in self.args:
                self.run_file_workflow()
        elif self.TEST in self.args:
            self.logger.warning(f"TEST in **args {self.args}")
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
                self.logger.debug(f"OLD SYM {val_item}")
                new_v = self.symbol_ini.replace_symbols_in_arg(val_item)
                self.logger.debug(f"NEW SYM {new_v}")
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
        return key, new_val

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
            return
        if self.args[self.DEBUG]:
            self.run_debug()
        if self.args[self.PROJ]:
            self.hit_counter = Counter()
            self.run_proj()
            self.logger.debug(f"hit counter: {self.hit_counter}")
        if self.args[self.TEST]:
            self.run_arg_tests()
        # else:
        #     self.logger.error("{self.args} requires --proj or --test")
        return

    def run_debug(self):
        for arg in self.args[self.DEBUG]:
            if arg == self.SYMBOLS:
                self.symbol_ini.print_symbols()
            else:
                self.logger.warning(f"unknown arg {arg} in  debug: ")

    def run_proj(self):
        self.proj = self.args[self.PROJ]
        if self.args[self.DELETE]:
            self.delete_files()
        # if self.args[self.KEEP]: # NYI
        #     self.keep_files()
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
            self.logger.warning(f"No tests given: choose some/all of {_TESTS}")
            return
        if "file_lib" in self.args[self.TEST]:
            import test_file
            self.logger.warning("run test_file")
            test_file.main()
        if "pdf_lib" in self.args[self.TEST]:
            import test_pdf
            self.logger.warning("run test_pdf")
            test_pdf.test_read_pdf()
        if "text_lib" in self.args[self.TEST]:
            # import test_text
            self.logger.warning("run test_text NYI")
            # test_text.main()

    def delete_files(self):
        if self.proj is None or self.proj == "":
            self.ami_logger.error(f"delete requires --proj; ignored")
            return
        globs = self.args[self.DELETE]
        for glob in globs:
            self.delete_glob(glob)

    def delete_glob(self, glob_exp):
        if ".." in glob_exp or glob_exp.endswith("*"):
            self.logger.error(f"glob {glob_exp} cannot contain .. or end in *")
            return
        full_glob = self.proj + "/" + glob_exp
        self.logger.warning(f"delete: {full_glob}")
        glob_recurse = True  # change this later
        globs = glob.glob(full_glob, recursive=glob_recurse)
        if globs is not None:
            files = {file: None for file in globs}
            self.logger.warning(f"deleting {len(files)} files ")
            for f in files:
                p = Path(f)
                if p.is_dir():
                    self.logger.warning(f"Cannot yet delete directories {p}")
                else:
                    p.unlink()

    def glob_files(self):
        import glob
        glob_recurse = self.flagged(self.RECURSE)
        glob_ = self.args[self.GLOB]
        self.logger.info(f"glob: {glob_}")
        files = {file: None for file in glob.glob(glob_, recursive=glob_recurse)}
        self.file_dict = files
        # self.content_store.create_file_dict(files)

        self.logger.info(f"glob file count {len(self.file_dict)}")

    def split(self, type):
        """ split fulltext.xml into sections"""

        # file_keys = self.content_store.get_file_keys()
        file_keys = self.file_dict.keys()
        for file in file_keys:
            suffix = FileLib.get_suffix(file)
            if ".xml" == suffix or type == self.XML2SECT:
                self.make_xml_sections(file)
            elif ".txt" == suffix or type == self.TXT2PARA:
                self.make_text_sections(file)
            else:
                self.logger.warning(f"no match for suffix: {suffix}")


    def make_xml_sections(self, file):
        xml_libx = XmlLib()
        xml_libx.logger.setLevel(logging.DEBUG)
        _ = xml_libx.read(file)
        xml_libx.make_sections("sections")

    def make_text_sections(self, file):
        sections = []
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            sections = TextUtil.split_at_empty_newline(text)
            self.store_or_write_data(file, sections, )
        # self.content_store.store(file, sections)
        #     for sect in sections:
        #         self.ami_logger.warning(f"{sect})


    def apply_func(self, apply_type):
        """ """
        self.read_file_content()
        if apply_type :
            self.logger.info(f"apply {apply_type}")
            func_tuple = self.func_dict[apply_type]
            if func_tuple is None:
                self.logger.error(f"Cannot find func for {apply_type}")
            else:
                # apply data is stored in self.file_dict
                self.apply_to_file_content(func_tuple, apply_type)

        return

    def normalize(self, unistr):
        import unicodedata
        self.logger.error("NYI")
        unicodedata.normalize('NFKC', unistr)
        pass

    def filter_file(self):
        filter_expr = self.args[self.FILTER]
        self.logger.warning(f"filter: {filter_expr}")

        files = set()
        # record hits
        file_keys = self.file_dict.keys()
        for file in file_keys:
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
        self.logger.debug(f"filter_expr {filter_expr}")
        filter_expr = filter_expr.strip()
        filter_value = self.extract_command_value(filter_expr)
        if filter_value is None:
            self.logger.error(f"bad filter_expr {filter_expr}")
            return hit_list
        filter = filter_value[0]
        value = filter_value[1]
        value = self.symbol_ini.replace_symbols_in_arg(value)
        if value is None:
            self.logger.warning(f"null value in filter {filter}")
            return None
        if filter == self.CONTAINS and file.endswith(".txt"):
            if value in content:
                hit_list.append(value)

        elif filter == self.DICTIONARY and file.endswith(".xml"):
            hits = self.apply_dictionary(hit_list, value)
            if len(hits) > 0:
                self.logger.debug(f"xpath {type(hits)} {hits}")
                hit_list.extend(hits)

        elif filter == self.LOOKUP:
            self.logger.debug(f"LOOKUP VALUE {value}")
            hits = self.apply_lookup(hit_list, value)
            if hits:
                hit_list = hits
        elif filter == self.REGEX:
            hits = self.apply_regex(hit_list, value)
            if hits:
                self.logger.debug(f"regex hits {hits}")
                hit_list = hits
        elif filter == self.WIKIDATA_SPARQL:
            hits = self.apply_wikidata_sparql(hit_list, value)
            if hits:
                self.ami_logger.warning(f"wikidata_sparql hits {hits}")
                hit_list = hits

        elif filter == self.XPATH and file.endswith(".xml"):
            tree = etree.parse(file)
            hits = [h.strip() for h in tree.xpath(value)]
            if len(hits) > 0:
                self.ami_logger.warning(f"xpath {type(hits)} {hits}")
                hit_list.extend(hits)

        self.logger.debug(f"hit list {hit_list}")
        if hit_list:
            self.ami_logger.info(f"non-zero list {hit_list}")
        return hit_list

    @classmethod
    def extract_command_value(cls, command_expr):
        """split command(value) into tuple

        value may have nested commands.

        :returns: tuple of command, value
        """
        if command_expr is None:
            return None
        bits = command_expr.split("(", 1)
        cls.logger.debug(f"BITS {bits}")

        return (bits[0], bits[1][:-1]) if len(bits) > 1 and bits[1].endswith(")") else None

    def apply_dictionary(self, hits, name):

        dictionary_file = self.get_symbol(name)
        if dictionary_file is None:
            dictionary_file = name
        self.ami_dictionary = AmiDictionary.read_dictionary(file=dictionary_file)
        new_hits = []
        if self.ami_dictionary is not None:
            for hit in hits:
                entry = self.ami_dictionary.get_entry(hit.lower())
                if entry is not None:
                    new_hits.append(hit)
                    self.hit_counter[hit] += 1

        # return [hit for hit in hits if re.match(regex, hit)]
        return new_hits

    @classmethod
    def apply_regex(cls, hits, regex):
        return [hit for hit in hits if re.match(regex, hit)]

    # def get_search_string(self, filter_expr, search_method):
    #     return filter_expr[len(search_method) + 1:-1]
    #
    def read_file_content(self, to_str=True):
        """read file content as bytes into file_dict
        
        :to_str: if true convert content to strings

        :param to_str:  (Default value = True)

        """
        self.ami_logger = AmiLogger(self.logger, initial=10, routine=100)
        for file in self.file_dict:
            self.ami_logger.info(f"reading {file}")
            if file.endswith(".xml"):
                self.read_string_content_to_dict(file, to_str)
            elif file.endswith(".pdf"):
                self.save_file_name_to_dict(file)
            elif file.endswith(".png"):
                self.read_binary_content_to_dict(file)
            elif file.endswith(".txt"):
                self.read_string_content_to_dict(file, to_str=False)
            else:
                self.logger.warning(f"cannot read file into string {file}")

    def apply_lookup(self, hits, value):
        self.logger.debug(f"LOOKUP: {hits} {value}")
        for hit in hits:
            if False:
                pass
            elif self.get_dictionary(value) is not None:
                dictionary = self.get_dictionary(value)
                self.logger.warning("USE DICTIONARY: NYI", value, dictionary)
            elif value == 'wikidata':
                qnumber = self.wikipedia_lookup.lookup_wikidata(hit)
                self.ami_logger.info(f"qnumber {qnumber}")
            else:
                self.logger.error(f"cannot parse lookup: {value}")

    def apply_wikidata_sparql(self, hit_list, value):
        if hit_list:
            self.ami_logger.warning(f"wikidata input {hit_list}")
        return hit_list

    def get_dictionary(self, value):
        dictionary = None
        command_value = self.extract_command_value(value)
        if command_value is not None and command_value[0] == "dictionary":
            dictionary = command_value[1]
        return dictionary

    def read_string_content_to_dict(self, file, to_str):
        """reads file into string
        Can process bytes to string

        DO WE NEED TO STORE THIS?
        """
        data = None
        self.ami_logger.info(f"reading string content from {file}")
        with open(file, "r", encoding="utf-8") as f:
            try:
                data = f.read()
                if to_str and isinstance(data, bytes):
                    data = data.decode("utf-8")
                self.store_or_write_data(file, data)
                # self.file_dict[file] = data
            except UnicodeDecodeError as ude:
                self.logger.error(f"skipped decoding error {ude}")
        return data

    def save_file_name_to_dict(self, file):
        self.store_or_write_data(file, file)
        # self.file_dict[file] = file

    def read_binary_content_to_dict(self, file):
        with open(file, "rb", ) as f:
            try:
                data = f.read()
                self.store_or_write_data(file, data)
                # self.file_dict[file] = data
            except Exception as e:
                self.logger.error(f"skipped reading error {e}")

    def apply_to_file_content(self, func_tuple, apply_type):
        """applies func to all string content in file_dict

        :param func: 

        """
        for file in self.file_dict.keys():
            data = self.file_dict.get(file)
            self.logger.debug(f"file: {file} => {func_tuple[0]}")
            new_file = self.create_file_name(file, func_tuple[1])

            try:
                new_data = func_tuple[0](data)
                self.store_or_write_data(file, new_data, new_file)
            except Exception as pdferr:
                print(f"cannot read PDF {file} because {pdferr} (probably not a PDF), skipped")
        return

    # needs fixing
    def create_file_name(self, file, extension):
        pathname = Path(file)
        return str(pathname.with_suffix(extension))

    def store_or_write_data(self, file, data, new_file=None) -> None:
        """store or write data to disk"""
        if file in self.file_dict:
            old_data = self.file_dict[file]
            if old_data is not None and old_data != data:
                self.ami_logger.warning(f"===============================\n"
                                        f"=========OVERWRITING data for {file}\n"
                                        f"{self.file_dict[file]} \n========WITH======\n"
                                        f"{data}")
                if new_file is not None:
                    self.ami_logger.warning(f"WROTE: {new_file}")
                    with open(new_file, "w", encoding="utf-8") as f:
                        f.write(data)
                    self.file_dict[file] = new_file

        # save data old-style
        self.file_dict[file] = data

    def combine_files_to_object(self):
        """ """
        methods = self.args.get(self.COMBINE)
        if methods and methods == self.CONCAT_STR:
            self.result = "\n".join(self.file_dict.values())
            self.ami_logger.warning(f"combine {self.result}")

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
                self.ami_logger.warning(f"wrote results {new_outfile}")
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

    # def run_examples(self):
    #     # from examples import Examples
    #     examples = Examples()
    #
    #     examples.example_pdf2txt()
    #     examples.example_split_pdf_txt_paras()
    #
    #     examples.example_xml2sect()
    #     examples.example_split_oil26()
    #
    #     examples.example_split_sentences()
    #     examples.example_xml2sect()
    #     examples.example_filter()
    #     examples.example_filter_species()
    #
    #     pass

class ContentStore():
    """caches content or writes it to disk

    replaces earlier pyami_m.file_dict
    """

    def __init__(self, pyami):
        self.pyami = pyami
        self.file_dict = {}

def main():

    """ main entry point for cmdline

    """

    run_dsl = False
    examples = True
    run_commands = False

    PyAMI.logger.warning(f"\n============== running pyami main ===============\n{sys.argv[1:]}")
    pyami = PyAMI()
    # this needs commandline
    if run_commands:
        pyami.run_commands()
    # pyami_m.run_tests()
    if run_dsl:
        DSLParser.run_tests(sys.argv[1:])
    # if examples:
    #     pyami_m.run_examples()
    else:
        pyami.run_commands(sys.argv[1:])


if __name__ == "__main__":

    PyAMI.logger.warning(f"sys.argv: {sys.argv}")
    # DONT rune main
    main()

else:

    PyAMI.logger.debug(" NOT running search main anyway")
