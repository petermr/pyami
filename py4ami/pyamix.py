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
import shutil
import argparse

from py4ami.dict_lib import AmiDictionary
from py4ami.examples import Examples
from py4ami.file_lib import FileLib
from py4ami.xml_lib import XmlLib
from py4ami.text_lib import TextUtil, DSLParser
from py4ami.pdfreader import PdfReader
from py4ami.symbol import SymbolIni
from py4ami.util import AmiLogger
from py4ami.wikimedia import WikidataLookup
from py4ami.ami_sections import AMIAbsSection

logging.debug("loading pyamix.py")
logging.warning(Path(__file__))


class PyAMI:
    """ main entry point for running pyami
     """
    OUTFILE = "outfile"

    # flags
    APPLY = "apply"
    ASSERT = "assert"
    CHECK_URLS = "check_urls"
    COPY = "copy"
    COMBINE = "combine"
    CONFIG = "config"
    CONTAINS = "contains"
    DEBUG = "debug"
    DELETE = "delete"
    DEST = "dest"
    DICTIONARY = "dictionary"
    EXAMPLES = "examples"
    FILTER = "filter"
    GLOB = "glob"
    LOOKUP = "lookup"
    PRINT_SYMBOLS = "print_symbols"
    PROJ = "proj"
    RECURSE = "recurse"
    REGEX = "regex"
    SECT = "sect"
    SRC = "src"
    SPLIT = "split"
    SYMBOLS = "symbols"
    TEST = "test"
    WIKIDATA_SPARQL = "wikidata_sparql"
    XPATH = "xpath"
    # apply methods 1:1 input-output
    PDF2TXT = "pdf2txt"
    TXT2SENT = "txt2sent"
    XML2TXT = "xml2txt"
    # combine methods n:1 input-output
    CONCAT_STR = "concat_str"
    # split methods 1:n input-output
    TXT2PARA = "txt2para"
    XML2SECT = "xml2sect"
    # symbols to update table
    SPECIAL_SYMBOLS = ["_proj"]
    LOGLEVEL = "loglevel"

    logger = logging.getLogger("pyami")
    symbol_ini = None

    def __init__(self):
        """constructor 

        creates symbols
        """

        self.logger.debug(f"===============Examples=================")
        if self.logger.getEffectiveLevel() <= logging.DEBUG:
            traceback.print_stack(file=sys.stdout)

        self.args = {}  # args captured in here as name/value without "-" or "--"
        self.apply = []
        self.combine = None
        self.config = None
        self.current_file = None
        self.fileset = None
        # self.file_dict = {}  # possibly to be replaced by content_store.file_dict
        self.content_store = ContentStore(self)  # will expose content_store.file_dict
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
        self.proj = None  # current project in searches
        self.current_ctree = None  # current ctree (may change during iteration
        # self.ami_logger = None
        if self.show_symbols:
            pprint.pp(f"SYMBOLS\n {self.symbol_ini.symbols}")

    def set_flags(self):
        """initialises flag_dict
        """

        self.flag_dict = {}
        self.flag_dict[self.APPLY] = None
        self.flag_dict[self.CHECK_URLS] = None
        self.flag_dict[self.COMBINE] = None
        self.flag_dict[self.PRINT_SYMBOLS] = None
        self.flag_dict[self.RECURSE] = True

    def set_funcs(self):
        """initializes func_dict
        """
        # 1:1 methods
        # tuple of func+file_extnsion
        self.func_dict[self.XML2TXT] = (XmlLib.remove_all_tags, ".xml.txt")
        self.func_dict[self.PDF2TXT] = (PdfReader.read_and_convert, ".pdf.txt")
        self.func_dict[self.TXT2SENT] = (
            TextUtil.split_into_sentences, ".sen.txt")
        # 1:n methods

    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline
        """
        parser = argparse.ArgumentParser(
            description='Search sections with dictionaries and patterns')
        apply_choices = [self.PDF2TXT, self.TXT2SENT, self.XML2TXT]
        self.logger.debug(f"ch {apply_choices}")
        parser.add_argument('--apply', nargs="+",
                            #                            choices=['pdf2txt', 'txt2sent', 'xml2txt'],
                            choices=apply_choices,
                            help='list of sequential transformations (1:1 map) to apply to pipeline '
                                 '({self.TXT2SENT} NYI)')
        parser.add_argument('--assert', nargs="+",
                            help='assertions; failure gives error message (prototype)')
        parser.add_argument('--combine', nargs=1,
                            help='operation to combine files into final object (e.g. concat text or CSV path')
        parser.add_argument('--config', '-c', nargs="+",
                            help='path (e.g. ~/pyami/config.ini.master) with list of config path(s) or config vars;'
                                 ' "symbols": gives symbols')
        parser.add_argument('--copy', nargs="+",
                            help='copy path or directory from=<from> to=<to> overwrite=<yes/no default=no>')
        parser.add_argument('--debug', nargs="+", type=str,
                            help='debugging commands , symbols, numbers, (not formalised)')
        parser.add_argument('--delete', nargs="+",
                            help='delete globbed files. Argument/s <glob> are relative to `proj`')
        parser.add_argument('--dict', '-d', nargs="+",
                            help='dictionaries to ami-search with, _help gives list')
        parser.add_argument('--examples', nargs="*", type=str,
                            help='simple demos, empty gives list, "all" runes all. May need downloading corpora')
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
                            help='output path. default is single path (default is overwrite). '
                                 'expands special variables _CPROJ, _CTREE, _PARENT to create iterators NYI')
        parser.add_argument('--patt', nargs="+",
                            help='patterns to search with (NYI); regex may need quoting')
        parser.add_argument('--plot', action="store_false",
                            help='plot params (NYI)')
        parser.add_argument('--proj', '-p', nargs="+",
                            help='projects to search; _help will give list')
        parser.add_argument('--sect', '-s', nargs="+",  # default=[AmiSection.INTRO, AmiSection.RESULTS],
                            help='sections to search; _help gives all(?)')
        parser.add_argument('--split', nargs="+", choices=['txt2para', 'xml2sect'],  # split fulltext.xml,
                            help='split fulltext.* into paras, sections')
        # parser.add_argument('--test', nargs="*",
        #                     choices=TestFile.OPTIONS,  # tests and/or setup/teardown
        #                     help='run tests for modules; no selection runs all')
        # TODO should tests be run from this menu
        return parser

    def commandline(self, commandline: str) -> None:
        """runs a commandline as a single string
        """
        if not commandline:
            self.run_command(["--help"])
        else:
            arglist = commandline.split(" ")
            self.run_command(arglist)

    def run_commands(self, arglistlist):
        """runs a list of commands

        :param arglistlist:  A list of commands (which are usually lists)

        for each list element uses run_command
        This allows for setup, assertions, etc.

        typical example:
        self.run_commands
        """
        if arglistlist is not None and isinstance(arglistlist, list):
            for arglist in arglistlist:
                self.run_command(arglist)

    def run_command(self, arglist):
        """parses cmdline, runs command and outputs symbols

        :param arglist: either a string or a list of strings

        if arglist is a string we split it at spaces into a list of strings

        """
        if isinstance(arglist, str):
            arglist = arglist.split(" ")

        self.logger.debug(f"********** raw arglist {arglist}")
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
        self.logger.debug("ARGS before substitution: "+str(self.args))
        self.substitute_args()
        self.logger.debug(f"self.args {self.args}")
        self.add_single_str_to_list()
        self.logger.debug("ARGS after substitution: "+str(self.args))
        self.set_loglevel_from_args()
        self.run_arguments()

    def substitute_args(self):
        """ """
        new_items = {}
        self.logger.debug(f"SYMBOLS1 {self.symbol_ini.symbols}")
        for item in self.args.items():
            new_item = self.make_substitutions(item)
            self.logger.debug(f"++++++++{item} ==> {new_item}")
            new_items[new_item[0]] = new_item[1]
        self.args = new_items
        self.logger.debug(f"******** substituted ARGS {self.args}")

    def add_single_str_to_list(self):
        """convert single strings to list of one string"""
        str_args = [self.DEBUG, self.EXAMPLES]
        for str_arg in str_args:
            self.logger.debug(f"key {str_arg}")
            self.replace_single_values_in_self_args_with_list(str_arg)
            self.logger.debug(f"args => {self.args}")

    def run_arguments(self):
        """ parse and expland arguments then ru options for

        Currently:
        * examples
        * project
        * tests

        There will be more here

         """
        # path workflow
        self.wikipedia_lookup = WikidataLookup()
        self.logger.warning(f"commandline args {self.args}")
        self.logger.warning(f"args: {self.args}")

        if self.args[self.CONFIG]:
            self.apply_config()

        if self.EXAMPLES in self.args:
            example_args = self.args[self.EXAMPLES]
            if example_args is not None:
                self.logger.debug(f" examples args: {example_args}")
                Examples(self).run_examples(example_args)

        if self.COPY in self.args and not self.args[self.COPY] is None:
            self.logger.warning(f"COPY {self.args[self.COPY]}")
            self.copy_files()

        if self.PROJ in self.args:
            if self.SECT in self.args or self.GLOB in self.args or self.SPLIT in self.args:
                self.run_project_workflow()

        # elif TestFile.TEST in self.args:
        #     self.logger.warning(f"TEST in **args {self.args}")
        #     TestFile.run_arg_tests(self.args)
        # TODO linkup with test arguments

    def replace_single_values_in_self_args_with_list(self, key):
        """always returns list even for single arg
        e.g. turns "foo" into ["foo"]
        This is to avoid strings being interpreted as lists of characters
        I am sure there is a more pythonic way
        """
        argsx = None
        if self.args is None:
            self.logger.warning(f"NULL self.args")
        elif key in self.args:
            argsx = self.args[key]
            if argsx is not None:
                if type(argsx) != list:
                    self.args[key] = [argsx]

    def make_substitutions(self, item):
        """

        :param item: 

        """
        old_val = item[1]
        key = item[0]
        new_val = None
        if old_val is None:
            new_val = None
        elif isinstance(old_val, list) and len(old_val) == 1:  # single string in list
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
            new_val = self.symbol_ini.replace_symbols_in_arg(old_val)
            if "${" in new_val:
                raise ValueError(f"Unresolved reference : {new_val}")
                # print("=====================")
                # self.symbol_ini.print_symbols()
                # print("=====================")
                # new_val = self.symbol_ini.replace_symbols_in_arg(old_val)
            # else:
            #     new_val = old_val
                # new_items[key] = new_val
        else:
            self.logger.error(f"{old_val} unknown arg type {type(old_val)}")
            new_val = old_val

        # special symbols such as "_proj"
        self.add_special_keys_to_symbols_ini(key, new_val)
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
        self.logger.debug(f"PARSED_ARGS {parsed_args}")
        args = {}
        arg_vars = vars(parsed_args)
        new_items = {}
        for item in arg_vars.items():
            new_item = self.make_substitutions(item)
            new_items[new_item[0]] = new_item[1]
        return new_items

    def add_special_keys_to_symbols_ini(self, key, value):
        """

        :param key: 
        :param value: 

        """
        if key in self.SPECIAL_SYMBOLS:
            self.symbol_ini.symbols[key] = value
            self.logger.warning(f"added reserved symbol {key} => {value}")

    def set_loglevel_from_args(self):
        """ """
        levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
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
                self.logger.loglevel = level

    def run_project_workflow(self):
        """ run when PROJ is set"""
        self.logger.debug(f"ARGS {self.args}")
        if not self.args:
            self.logger.error("no args given; try --examples or --help")
            return
        if self.args[self.DEBUG]:
            self.run_debug()
        if self.args[self.PROJ]:
            self.hit_counter = Counter()
            self.run_proj()
            self.logger.debug(f"hit counter: {self.hit_counter}")
        # if self.args[self.TEST]:
        #     TestFile.run_arg_tests(self.args)
        # TODO fix tests
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
        """ project-related commands"""
        self.proj = self.args[self.PROJ]
        # if self.args[self.CONFIG]:
        #     self.apply_config()
        if self.args[self.DELETE]:
            self.delete_files()
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

    def copy_files(self):
        """copies path or directory

        copies a path or complete directory

        Args:
            src (str): path or dirx to copy, must exist
            dest (str): destination must be a directory. If path becomes a child of <to>; if a
            directory creates or replaces <to>
            overwrite (bool, optional): whether to overwrite if path exists. Defaults to False.
        Exceptions:
            FileNotFoundError: if src does not exist, or dest cannot be created

        """
        # self.logger.warning(f"NOT IMPLERMENTED")
        # return
        self.replace_single_values_in_self_args_with_list(self.COPY)
        argsx = self.args[self.COPY]
        if len(argsx) < 2:
            raise TypeError("copy needs >= 2 args")

        src = argsx[0]
        src_path = Path(src)
        if not src_path.exists():
            raise FileNotFoundError(
                str(src_path), "src must exist as path or directory")

        dest = argsx[1]
        dest_path = Path(dest)

        overwrite = len(argsx) > 2 and argsx[2] == "overwrite"
        FileLib.copy_file_or_directory(dest_path, src_path, overwrite)

    def apply_config(self):
        config_args = self.args[self.CONFIG]
        if type(config_args) == str:
            config_args = [config_args]
        self.logger.debug(f" type {type(config_args)}")
        for config_arg in config_args:
            if config_arg == self.SYMBOLS:
                self.symbol_ini.print_symbols()
            else:
                self.logger.warning(f"processing INI NYI: {config_arg}")

    def delete_files(self):
        """deletes files in glob

        requires proj to be set
        """
        if self.proj is None or self.proj == "":
            self.logger.error(f"delete requires --proj; ignored")
            return
        globs = self.args[self.DELETE]
        for glob in globs:
            self.delete_glob(glob)

    def delete_glob(self, glob_exp):
        """deletes globbed files

        Args:
            glob_exp (str): glob expression


        """
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
        glob_recurse = self.flagged(self.RECURSE)
        glob_ = self.args[self.GLOB]
        self.logger.info(f"glob: {glob_}")
        # create dictionary wiuth empty values?
        files = [file for file in glob.glob(glob_, recursive=glob_recurse)]
        self.content_store.add_files(files)

        self.logger.info(f"glob path count {len(self.content_store.keys())}")

    def split(self, type):
        """ split fulltext.xml into sections"""

        # file_keys = self.content_store.get_file_keys()
        file_keys = self.content_store.keys()
        for file in file_keys:
            suffix = FileLib.get_suffix(file)
            if ".xml" == suffix and type == self.XML2SECT:
                # self.make_xml_sections(file)
                force = False
                force = True
                outdir = Path(Path(file).parent, "sections")
                AMIAbsSection.make_xml_sections(file, outdir, force)
            elif ".txt" == suffix or type == self.TXT2PARA:
                self.make_text_sections(file)
            else:
                self.logger.warning(f"no match for suffix: {suffix}")

    @classmethod
    def make_xml_sections(cls, file):
        xml_libx = XmlLib()
        xml_libx.logger.setLevel(logging.DEBUG)
        xml_libx.read(file)
        xml_libx.make_sections("sections", )

    def make_text_sections(self, file):
        sections = []
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
            sections = TextUtil.split_at_empty_newline(text)
            self.store_or_write_data(file, sections, )

    def apply_func(self, apply_type):
        """ """
        self.read_file_content()
        if apply_type:
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
        file_keys = self.content_store.keys()
        for file in file_keys:
            filter_true = self.apply_filter(file, filter_expr)
            if filter_true:
                files.add(file)
        # delete hits from dict
        for file in files:
            if file in self.content_store.keys():
                del self.content_store.file_dict[file]

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
                self.logger.warning(f"wikidata_sparql hits {hits}")
                hit_list = hits

        elif filter == self.XPATH and file.endswith(".xml"):
            tree = etree.parse(file)
            hits = [h.strip() for h in tree.xpath(value)]
            if len(hits) > 0:
                self.logger.warning(f"xpath {type(hits)} {hits}")
                hit_list.extend(hits)

        self.logger.debug(f"hit list {hit_list}")
        if hit_list:
            self.logger.info(f"non-zero list {hit_list}")
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
        self.ami_dictionary = AmiDictionary.read_dictionary(
            file=dictionary_file)
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
        """read path content as bytes into file_dict

        :to_str: if true convert content to strings

        :param to_str:  (Default value = True)

        """
        self.logger = AmiLogger(self.logger, initial=10, routine=100)
        for file in self.content_store.keys():
            self.logger.info(f"reading... {file}")
            if file.endswith(".xml"):
                self.read_string_content_to_dict(file, to_str)
            elif file.endswith(".pdf"):
                self.save_file_name_to_dict(file)
            elif file.endswith(".png"):
                self.read_binary_content_to_dict(file)
            elif file.endswith(".txt"):
                self.read_string_content_to_dict(file, to_str=False)
            else:
                self.logger.warning(f"cannot read path into string {file}")

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
            self.logger.warning(f"wikidata input {hit_list}")
        return hit_list

    def get_dictionary(self, value):
        dictionary = None
        command_value = self.extract_command_value(value)
        if command_value is not None and command_value[0] == "dictionary":
            dictionary = command_value[1]
        return dictionary

    def read_string_content_to_dict(self, file, to_str):
        """reads path into string
        Can process bytes to string

        DO WE NEED TO STORE THIS?
        """
        data = None
        self.logger.info(f"reading string content from {file}")
        with open(file, "r", encoding="utf-8") as f:
            try:
                data = f.read()
                if to_str and isinstance(data, bytes):
                    data = data.decode("utf-8")
                self.store_or_write_data(file, data)
                # self.file_dict[path] = data
            except UnicodeDecodeError as ude:
                self.logger.error(f"skipped decoding error {ude}")
        return data

    def save_file_name_to_dict(self, file):
        self.store_or_write_data(file, file)
        # self.file_dict[path] = path

    def read_binary_content_to_dict(self, file):
        with open(file, "rb", ) as f:
            try:
                data = f.read()
                self.store_or_write_data(file, data)
                # self.file_dict[path] = data
            except Exception as e:
                self.logger.error(f"skipped reading error {e}")

    def apply_to_file_content(self, func_tuple, apply_type):
        """applies func to all string content in file_dict

        :param func: 

        """
        # for file in self.content_store.keys():
        #     data = self.content_store(file)
        #     self.logger.debug(f"path: {file} => {func_tuple[0]}")
        #     new_file = self.create_file_name(file, func_tuple[1])
        #
        #     try:
        #         new_data = func_tuple[0](data)
        #         self.store_or_write_data(file, new_data, new_file)
        #     except Exception as pdferr:
        #         self.logger.warning(
        #             f"cannot read PDF {file} because {pdferr} (probably not a PDF), skipped")
        return

    # needs fixing
    def create_file_name(self, file, extension):
        pathname = Path(file)
        return str(pathname.with_suffix(extension))

    def store_or_write_data(self, file, data, new_file=None) -> None:
        """store or write data to disk"""
        if file in self.content_store.file_dict:
            old_data = self.content_store.file_dict[file]
            if old_data is not None and old_data != data:
                self.logger.warning(
                    f"===============================\n"
                    f"=========OVERWRITING data for {file}\n"
                    f"{self.content_store.file_dict[file]} \n========WITH======\n"
                    f"{data}")
                if new_file is not None:
                    self.logger.warning(f"WROTE: {new_file}")
                    with open(new_file, "w", encoding="utf-8") as f:
                        f.write(data)
                    self.content_store.file_dict[file] = new_file

        # save data old-style
        self.content_store.file_dict[file] = data

    def combine_files_to_object(self):
        """ """
        methods = self.args.get(self.COMBINE)
        if methods and methods == self.CONCAT_STR:
            self.result = "\n".join(self.content_store.file_dict.values())
            self.logger.warning(f"combine {self.result}")

    def write_output(self):
        """ """
        self.outfile = self.args[self.OUTFILE]
        if self.result:  # single output
            self.write_single_result()

        if self.content_store.file_dict:
            self.write_multiple_results()

    def write_multiple_results(self):
        for file in self.content_store.file_dict:
            data = self.content_store.file_dict[file]
            if data is None:
                self.logger.debug(f"data is NONE")
                continue
            print(f"Valid data")
            parent = FileLib.get_parent_dir(file)
            new_outfile = os.path.join(parent, self.outfile)
            try:
                FileLib.force_mkparent(new_outfile)
                self.logger.warning(f"writing path {new_outfile}")
                with open(new_outfile, "w", encoding="utf-8") as f:
                    self.logger.warning(f"wrote results {new_outfile}")
                    f.write(f"{str(data)}")
            except Exception as e:
                self.logger.warning(f"cannot write because {e}")

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


class ContentStore:
    """holds path-related content

    replaces earlier py4ami.file_dict
    uses a dict
    at presemt the key is the path(name) and the value is either the content or None
    """

    def __init__(self, pyami):
        self.pyami = pyami
        self.file_dict = {}

    def add_files(self, files, add_contents=False):
        for file in files:
            self.add_file(file, add_contents)

    def add_file(self, file, add_contents=False):
        self.file_dict[file] = self.get_contents(file) if add_contents else None

    def keys(self):
        return self.file_dict.keys() if self.file_dict is not None else None

    def get_file_contents(self):
        """return dictionary or None"""
        return self.file_dict


def main():
    """ main entry point for cmdline

    """

    run_dsl = False
    run_tests = False  # needs re-implementing
    run_commands = True
#    run_commands = False
#    run_tests = True

    PyAMI.logger.warning(
        f"\n============== running pyami main ===============\n{sys.argv[1:]}")
    pyamix = PyAMI()
    # this needs commandline
    if run_commands:
        pyamix.run_command(sys.argv[1:])
    if run_tests:
        pyamix.run_tests()
    if run_dsl:
        DSLParser.run_tests(sys.argv[1:])


if __name__ == "__main__":

    # PyAMI.logger.warning(f"sys.argv: {sys.argv}")
    # DONT rune main
    main()

else:

    PyAMI.logger.debug(" NOT running search main anyway")
