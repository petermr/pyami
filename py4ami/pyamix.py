import ast
import logging
import sys
import os
import re
import glob
import lxml.etree as etree
import pprint
from collections import Counter
import textwrap
import traceback
from pathlib import Path
import argparse
from enum import Enum
from abc import ABC, abstractmethod
# local
from py4ami.ami_dict import AmiDictionary, AmiDictArgs
from py4ami.ami_convert import ConvType, Converters
from py4ami.ami_sections import AMIAbsSection
from py4ami.ami_gui import GUIArgs
from py4ami.ami_html import HTMLArgs
from py4ami.examples import Examples
from py4ami.file_lib import FileLib
from py4ami.pdfreader import Svg2PageConverter, Page2SectConverter, Xml2HtmlConverter, Xml2TxtConverter, Pdf2SvgConverter
from py4ami.ami_pdf import PDFArgs
from py4ami.ami_project import CProject, CTree, CSubDir, ProjectArgs
from py4ami.symbol import SymbolIni
from py4ami.text_lib import TextUtil, DSLParser
from py4ami.util import AmiLogger, Util
from py4ami.wikimedia import WikidataLookup
from py4ami.xml_lib import XmlLib

class SubParser(Enum):
    DICT = "DICT"

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
    FLAGS = "flags"
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
    SYSTEM_EXIT_OK = "SystemExitOK"
    SYSTEM_EXIT_FAIL = "SystemExitFail_"
    TEST = "test"
    WIKIDATA_SPARQL = "wikidata_sparql"
    XPATH = "xpath"
    # apply methods 1:1 input-output
    # obsolete (use Converters)
    PDF2TXT = "pdf2svg"
    PDF2SVG = "pdf2svg"
    SVG2PAGE = "svg2page"
    XML2HTML = "xml2html"
    TXT2SENT = "txt2sent"
    XML2TXT = "xml2txt"
    TXT2PARA = "txt2para"
    XML2SECT = "xml2sect"
    # combine methods n:1 input-output
    CONCAT_STR = "concat_str"
    # split methods 1:n input-output
    # symbols to update table
    SPECIAL_SYMBOLS = ["_proj"]
    LOGLEVEL = "loglevel"
    PY4AMI = "py4ami"

# parsers
    DICT_PARSER = "DICT"
    HTML_PARSER = "HTML"
    PDF_PARSER = "PDF"
    PROJECT_PARSER = "PROJECT"

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
        self.flag_dict = {}
        self.initialize_flags()
        self.wikidata_lookup = None
        self.wikipedia_lookup = None
        self.hit_counter = None
        self.symbol_ini = SymbolIni(self)
        self.set_funcs()
        self.show_symbols = False
        self.ami_dictionary = None
        self.proj = None  # current project in searches
        self.current_ctree = None  # current ctree (may change during iteration
        self.cproject = None
        self.ami_logger = None
        self.outfile = None
        if self.show_symbols:
            pprint.pp(f"SYMBOLS\n {self.symbol_ini.symbols}")

    def initialize_flags(self):
        """initialises flag_dict
        """

        self.flag_dict = {

            self.APPLY: None,
            self.CHECK_URLS: None,
            self.COMBINE: None,
            self.PRINT_SYMBOLS: False,
            self.RECURSE: True,
        }

    def set_funcs(self):
        """initializes func_dict
        """
        # 1:1 methods
        # tuple of func+file_extnsion
        self.func_dict[self.XML2TXT] = (XmlLib.remove_all_tags, ".xml.txt")
        # self.func_dict[self.PDF2TXT] = (PdfReader.read_and_convert, ".pdf.txt")
        self.func_dict[self.PDF2SVG] = (Pdf2SvgConverter.read_and_convert, ".pdf.svg")
        self.func_dict[self.SVG2PAGE] = (Svg2PageConverter.read_and_convert, ".svg.xml")
        self.func_dict[self.XML2HTML] = (Xml2HtmlConverter.read_and_convert, ".svg.html")
        # self.func_dict[self.TXT2SENT] = (TextUtil.split_into_sentences, ".sen.txt")
        # 1:n methods

    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline
        """

        def run_dict(self):
            print(f"run dict pyamix")

        def run_pdf(args):
            print(f"run pdf")

        def run_project():
            print(f"run project {self.args}")

        version = self.version()
        if not sys.argv or len(sys.argv) == 0:
            sys.argv = [PyAMI.PY4AMI]
        parser = argparse.ArgumentParser(
            description=f'py4ami: V{version} call with ONE of subcommands (DICT,GUI,HTML,PDF,PROJECT), e.g. py4ami PDF --help'
        )

        # apply_choices = [self.PDF2TXT, self.PDF2SVG, self.SVG2XML, self.TXT2SENT, self.XML2HTML, self.XML2TXT]
        apply_choices = ConvType.list_values()
        self.logger.debug(f"ch {apply_choices}")
        parser.add_argument('--version', action="store_true",
                            help=f"show version {version}")
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = textwrap.dedent(
            'Py4AMI: create, manipulate, use CProject \n'
            '----------------------------------------\n\n'
            'Py4AMI is the largest collection of functionality in the AMI system.'
            'It contains executable code and libraries to manage complex documents.\n'
            'A key structure is the corpus (CProject directory) which contains a list of subdirectories '
            '(CTrees) which themselves contain many different document features (text, tables, images, graphics.\n'
            'Py4AMI can create, fill, manipulate, transform many of the components including PDF, HTML, TXT, images, CSV.\n'
            '\n'
            'The subcommands:\n\n'
            '  DICT <options>      # create/edit/search dictionaries\n' 
            '  GUI <options>       # run tkinter GUI (prototype)\n' 
            '  HTML <options>      # create/edit HTML\n' 
            '  PDF <options>       # convert PDF into HTML and images\n' 
            '  PROJECT <options>   # create and transform a corpus of documents\n' 
            '\n'
            'After installation, run \n' 
            '  py4ami <subcommand> <options>\n'
            '\n'
            '\nExamples (# foo is a comment):\n' 
            '  py4ami        # runs help\n'
            '  py4ami -h     # runs help\n'
            '  py4ami PDF -h # runs PDF help\n'
            '  py4ami PDF --makehtml --infile foo.pdf --outdir bar/ # converts PDF to HTML\n'
            '  py4ami PROJECT --project foodir/ # converts all PDF in foodir to CTrees\n'
            '\n'
            '----------------------------------------\n\n'
        )

# obsolete commands
#         parser.add_argument('--apply', nargs="+",
#                             #                            choices=['pdf2txt', 'txt2sent', 'xml2txt'],
#                             choices=apply_choices,
#                             help='list of sequential transformations (1:1 map) to apply to pipeline '
#                                  '({self.TXT2SENT} NYI)')
#
#         parser.add_argument('--assert', nargs="+",
#                             help='assertions; failure gives error message (prototype)')
#         parser.add_argument('--combine', nargs=1,
#                             help='operation to combine files into final object (e.g. concat text or CSV path')

        # parser.add_argument('--config', '-c', nargs="+",
        #                     help='path (e.g. ~/pyami/config.ini.master) with list of config path(s) or config vars;'
        #                          ' "symbols": gives symbols')
        # parser.add_argument('--copy', nargs="+",
        #                     help='copy path or directory from=<from> to=<to> overwrite=<yes/no default=no>')
        # parser.add_argument('--debug', nargs="+", type=str,
        #                     help='debugging commands , symbols, numbers, (not formalised)')
        # parser.add_argument('--delete', nargs="+",
        #                     help='delete globbed files. Argument/s <glob> are relative to `proj`')
        # parser.add_argument('--dict', '-d', nargs="+",
        #                     help='dictionaries to ami-search with, _help gives list')
        # parser.add_argument('--examples', nargs="*", type=str,
        #                     help='simple demos, empty gives list, "all" runs all. May need downloading corpora')
        # parser.add_argument('--filter', nargs="+",
        #                     help='expr to filter with')
        # parser.add_argument('--flags', nargs="+",
        #                     help='name-value pairs collected into self.flag_dict, "help" gives list')
        # parser.add_argument('--glob', '-g', nargs="+",
        #                     help='glob files; python syntax (* and ** wildcards supported); '
        #                          'include alternatives in {...,...}. ')
        # # parser.add_argument('--help', '-h', nargs="?",
        # #                     help='output help; (NYI) an optional arg gives level')
        # parser.add_argument('--languages', nargs="+", default=["en"],
        #                     help='languages (NYI)')
        # parser.add_argument('--loglevel', '-l', default="info",
        #                     help='log level (NYI)')
        # parser.add_argument('--maxbars', nargs="?", type=int, default=25,
        #                     help='max bars on plot (NYI)')
        # parser.add_argument('--nosearch', action="store_true",
        #                     help='search (NYI)')
        # parser.add_argument('--outfile', type=str,
        #                     help='output path. default is single path (default is overwrite). '
        #                          'expands special variables _CPROJ, _CTREE, _PARENT to create iterators NYI')
        # parser.add_argument('--patt', nargs="+",
        #                     help='patterns to search with (NYI); regex may need quoting')
        # parser.add_argument('--plot', action="store_false",
        #                     help='plot params (NYI)')
        # parser.add_argument('--proj', '-p', nargs="+",
        #                     help='projects to search; _help will give list')
        # parser.add_argument('--sect', '-s', nargs="+",  # default=[AmiSection.INTRO, AmiSection.RESULTS],
        #                     help='sections to search; _help gives all(?)')
        # parser.add_argument('--split', nargs="+", choices=['txt2para', 'xml2sect'],  # split fulltext.xml,
        #                     help='split fulltext.* into paras, sections')
        # parser.add_argument('--test', nargs="*",
        #                     choices=TestFile.OPTIONS,  # tests and/or setup/teardown
        #                     help='run tests for modules; no selection runs all')
        # TODO should tests be run from this menu

        subparsers = parser.add_subparsers(help='subcommands', dest="command")

        dict_parser = AmiDictArgs().make_sub_parser(subparsers)
        gui_parser = GUIArgs().make_sub_parser(subparsers)
        html_parser = HTMLArgs().make_sub_parser(subparsers)
        pdf_parser = PDFArgs().make_sub_parser(subparsers)
        project_parser = ProjectArgs().make_sub_parser(subparsers)

        parser.epilog = "other entry points run as 'python -m py4ami.ami_dict args' also ami_pdf, ami_project"
        parser.epilog = """run:
        py4ami <subcommand> <args>
          where subcommand is in   {DICT,GUI,HTML,PDF,PROJECT} and args depend on subcommand
        """


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

    def run_command(self, args):
        """parses cmdline, runs command and outputs symbols

        :param args: either a string or a list of strings

        if args is a string we split it at spaces into a list of strings

        """
        if isinstance(args, str):
            args =  args.strip()
            args = args.split(" ")

        self.logger.debug(f"********** raw arglist {args}")
        test_catch = False
        if test_catch: # try to trap exception
            try:
                self.parse_and_run_args(args)
            except Exception as e:
                print(f"ERROR {e.args} from {args}")
                logging.error(f"\n============PARSE ERROR==({e.__cause__})======\n")
                return
            if self.is_flag_true(self.PRINT_SYMBOLS):
                self.symbol_ini.print_symbols()
        else:
            self.parse_and_run_args(args)

        return

    def parse_and_run_args(self, arglist):
        """runs cmds and makes substitutions (${...} then runs workflow

        :param arglist: 

        """
        # no args, create help
        if not arglist:
            self.logger.warning("No args, running --help")
            arglist = ["--help"]
        parser = self.create_arg_parser()
        self.args = self.make_substitutions_create_arg_tuples(arglist, parser)
        self.logger.debug("ARGS before substitution: " + str(self.args))
        # this may be redundant
        self.substitute_args()
        self.logger.debug(f"self.args {self.args}")
        self.add_single_str_to_list()
        self.logger.debug("ARGS after substitution: " + str(self.args))
        self.set_loglevel_from_args()
        self.run_arguments()

    def substitute_args(self):
        """ iterates through self.args and makes subsitutions
        May duplicates
        """
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
        # print(f"RUN ARGUMENTS on {self} {self.args}")
        # path workflow
        self.wikipedia_lookup = WikidataLookup()
        self.logger.debug(f"commandline args {self.args}")
        subparser_type = self.args.get("command")
        logging.debug(f" COMMAND: {subparser_type} {self.args}")

        # if "func" in self.args:
        #     f_func = self.args["func"]
        #     print(f"FUNC {f_func}")
        #     aa = f_func()
        #     print(f"aa {aa}")
        # messy - we need to use polymorphism
        if not subparser_type:
            abstract_args = None
        elif subparser_type == "DICT":
            abstract_args = AmiDictArgs()
        elif subparser_type == "GUI":
            abstract_args = GUIArgs()
        elif subparser_type == "HTML":
            abstract_args = HTMLArgs()
        elif subparser_type == "PDF":
            abstract_args = PDFArgs()
        elif subparser_type == "PROJECT":
            abstract_args = ProjectArgs()

        if abstract_args:
            abstract_args.parse_and_process1(self.args)
        else:
            self.run_core_mathods()

    def run_core_mathods(self):
        logging.debug(f"run_core")
        if self.FLAGS in self.args and self.args[self.FLAGS] is not None:
            self.add_flags()
        if self.CONFIG in self.args and self.args[self.CONFIG] is not None:
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
        # argsx = None
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
        # new_val = None
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
            if type(old_val) is str:
                self.logger.error(f"substitution: {old_val} unknown arg type {type(old_val)}")
            new_val = old_val

        # special symbols such as "_proj"
        self.add_special_keys_to_symbols_ini(key, new_val)
        return key, new_val

    def get_symbol(self, symb):
        """gets symbol from pyami symbol table

        """
        return self.symbol_ini.symbols.get(symb)

    def make_substitutions_create_arg_tuples(self, arglist, parser):
        """
        processes raw args to expand substitutions

        :param arglist: 
        :param parser: 
        :return: list of transformed arguments as 2-tuples
        """
        new_items = {}
        if arglist and len(arglist) > 0:
            parsed_args = self.parse_args_and_trap_errors(arglist, parser)
            if parsed_args == self.SYSTEM_EXIT_OK:  # return code 0
                return new_items
            if str(parsed_args).startswith(self.SYSTEM_EXIT_FAIL):
                raise ValueError(f"bad command arguments {parsed_args} (see log output)")

            self.logger.debug(f"PARSED_ARGS {parsed_args}")
            arg_vars = vars(parsed_args)
            for item in arg_vars.items():
                new_item = self.make_substitutions(item)
                new_items[new_item[0]] = new_item[1]
        return new_items

    def parse_args_and_trap_errors(self, arglist, parser):
        """run argparse parser.parse_args and try to trap serious errors
        --help calls SystemExit (we trap and return None)"""
        try:
            parsed_args = parser.parse_args(arglist)
        except SystemExit as se:  # exit codes
            if str(se) == '0':
                parsed_args = self.SYSTEM_EXIT_OK
            else:
                parsed_args = self.SYSTEM_EXIT_FAIL + str(se)
        except Exception as e:
            parsed_args = None
            self.logger.error(f"Cannot parse {arglist} , {e}")
        return parsed_args

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
                if self.is_flag_true(self.PRINT_SYMBOLS):
                    self.symbol_ini.print_symbols()
            else:
                self.logger.warning(f"unknown arg {arg} in  debug: ")

    def run_proj(self):
        """ project-related commands"""
        self.proj = self.args[self.PROJ]
        if not self.proj:
            self.logger.error(f"--proj must be given")
            return
        self.cproject = CProject(self.proj)

        self.logger.debug(f"{Util.basename(__file__)} proj: {self.proj}")
        # if self.args[self.CONFIG]:
        #     self.apply_config()
        if self.args[self.DELETE]:
            self.delete_files()
        if self.args[self.GLOB]:
            self.glob_files()
        if self.args[self.SPLIT]:
            self.split(self.args.get(self.SPLIT))
        if self.args[self.APPLY]:
            apply_type = self.args.get(self.APPLY)
            converter = Converters.get_converter(apply_type)
            if not converter:
                raise ValueError(f"cannot find converter for {apply_type}")
            previous = False
            if previous:
                self.add_ctree_filenames_to_content_store(apply_type)
                # print(f"content_store {self.content_store.file_dict}")
                self.apply_func(apply_type)
            else:
                converter = Converters.get_converter(apply_type)()
                print(f"{type(converter)}")
                converter.iterate_cproject(cproject=self.proj)

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
        Exceptions:

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

    def add_flags(self):
        """uses values from '--flag [value]' arguments """
        flags = self.args[self.FLAGS]
        if type(flags) is str:
            flags = [flags]
        for flag in flags:
            nv = Util.create_name_value(flag)
            if nv is None or len(nv) != 2:
                raise ValueError(f"bad value {flag}")
            if self.flag_dict.get(nv[0]) is None:
                self.logger.warning(f"adding new flag {nv}")
            self.flag_dict[nv[0]] = nv[1]

    def apply_config(self):
        config_args = self.args[self.CONFIG]
        if type(config_args) == str:
            config_args = [config_args]
        self.logger.debug(f" type {type(config_args)}")
        for config_arg in config_args:
            if config_arg == self.SYMBOLS:
                if self.is_flag_true(self.PRINT_SYMBOLS):
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
        for globx in globs:
            self.delete_glob(globx)

    def delete_glob(self, glob_exp):
        """deletes globbed files
        requires self.proj as root of globbing

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
        glob_recurse = self.is_flag_true(self.RECURSE)
        glob_ = self.args[self.GLOB]
        self.logger.info(f"glob: {glob_}")
        # create dictionary wiuth empty values?
        files = [file for file in glob.glob(glob_, recursive=glob_recurse)]
        self.content_store.add_files(files)

        self.logger.info(f"glob path count {len(self.content_store.keys())}")

    def split(self, typex):
        """ split fulltext.xml into sections"""

        # file_keys = self.content_store.get_file_keys()
        file_keys = self.content_store.keys()
        for file in file_keys:
            suffix = FileLib.get_suffix(file)
            if ".xml" == suffix and typex == self.XML2SECT:
                # self.make_xml_sections(file)
                # force = False
                force = True
                outdir = Path(Path(file).parent, "sections")
                AMIAbsSection.make_xml_sections(file, str(outdir), force)
            elif ".txt" == suffix or typex == self.TXT2PARA:
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
        #
        self.read_file_content()
        if apply_type:
            self.logger.info(f"apply {apply_type}")
            func_tuple = self.func_dict[apply_type]
            if func_tuple is None:
                self.logger.error(f"Cannot find func for {apply_type}")
            else:
                # apply data is stored in self.file_dict
                self.logger.debug(f"running {func_tuple} {apply_type}")
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
        filterx = filter_value[0]
        value = filter_value[1]
        value = self.symbol_ini.replace_symbols_in_arg(value)
        if value is None:
            self.logger.warning(f"null value in filter {filterx}")
            return None
        if filterx == self.CONTAINS and file.endswith(".txt"):
            if value in content:
                hit_list.append(value)

        elif filterx == self.DICTIONARY and file.endswith(".xml"):
            hits = self.apply_dictionary(hit_list, value)
            if len(hits) > 0:
                self.logger.debug(f"xpath {type(hits)} {hits}")
                hit_list.extend(hits)

        elif filterx == self.LOOKUP:
            self.logger.debug(f"LOOKUP VALUE {value}")
            hits = self.apply_lookup(hit_list, value)
            if hits:
                hit_list = hits
        elif filterx == self.REGEX:
            hits = self.apply_regex(hit_list, value)
            if hits:
                self.logger.debug(f"regex hits {hits}")
                hit_list = hits
        elif filterx == self.WIKIDATA_SPARQL:
            hits = self.apply_wikidata_sparql(hit_list, value)
            if hits:
                self.logger.debug(f"wikidata_sparql hits {hits}")
                hit_list = hits

        elif filterx == self.XPATH and file.endswith(".xml"):
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
                entry = self.ami_dictionary.get_lxml_entry(hit.lower())
                if entry is not None:
                    new_hits.append(hit)
                    self.hit_counter[hit] += 1

        # return [hit for hit in hits if re.match(regex, hit)]
        return new_hits

    @classmethod
    def apply_regex(cls, hits, regex):
        return [hit for hit in hits if re.match(regex, hit)]

    def add_ctree_filenames_to_content_store(self, apply_type):
        # files = []
        ctree_list = self.cproject.get_ctrees()
        # TODO add this functionality to enums
        subdir_name = None
        if apply_type == self.SVG2PAGE:
            subdir_name = CTree.SVG_DIR
            subdir_ext = "svg"

        subdirs = []
        subfiles = []
        for ctree in ctree_list:
            sd = ctree.get_existing_reserved_directory(subdir_name)
            subdir = CSubDir(sd)
            subdirs.append(subdir)
            globx = "*.svg"
            sf = subdir.get_descendants(globx)
            subfiles.extend(sf)

        print(f"subdirs {len(subdirs)} subfiles {len(subfiles)}")
        self.content_store.add_files(subfiles)

    # def get_search_string(self, filter_expr, search_method):
    #     return filter_expr[len(search_method) + 1:-1]
    #
    def read_file_content(self, to_str=True):
        """read path content as bytes into file_dict

        :to_str: if true convert content to strings

        :param to_str:  (Default value = True)

        """
        self.ami_logger = AmiLogger(self.logger, initial=10, routine=100)
        keys = self.content_store.keys()
        print(f"keys {len(keys)}")
        for file in keys:
            filestr = str(file)
            self.logger.info(f"reading... {file}")
            if filestr.endswith(".xml"):
                self.read_string_content_to_dict(file, to_str)
            elif filestr.endswith(".svg"):
                # self.save_file_name_to_dict(file)
                self.read_string_content_to_dict(file, to_str)
            elif filestr.endswith(".pdf"):
                self.save_file_name_to_dict(file)
            elif filestr.endswith(".png"):
                self.read_binary_content_to_dict(file)
            elif filestr.endswith(".txt"):
                self.read_string_content_to_dict(file, to_str=False)
            else:
                self.logger.warning(f"cannot read path into string {file}")

    def apply_lookup(self, hits, value):
        self.logger.debug(f"LOOKUP: {hits} {value}")
        for hit in hits:
            if self.get_dictionary(value) is not None:
                dictionary = self.get_dictionary(value)
                self.logger.warning("USE DICTIONARY: NYI" + str(value) + str(dictionary))
            elif value == 'wikidata':
                qnumber = self.wikipedia_lookup.lookup_wikidata(hit)
                self.ami_logger.info(f"qnumber {qnumber}")
            else:
                self.logger.error(f"cannot parse lookup: {value}")

    def apply_wikidata_sparql(self, hit_list):
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

        :param func_tuple:
        :param apply_type:

        """
        self.logger.warning(f"func_tuple {len(func_tuple)}: {func_tuple[0]} => {func_tuple[1]}")

        open_flag = self.get_open_type(apply_type)
        for file in self.content_store.keys():
            self.logger.warning(f"converting {file}")
            data = self.content_store.get_file_contents(file)
            if not data:
                encoding = "utf-8" if open_flag == "r" else None
                with open(file, open_flag, encoding=encoding) as f:
                    data = f.read()
            print(f"file {file} data {len(data)}")
            self.logger.debug(f"path: {file} => {func_tuple[0]}")
            new_file = self.create_file_name(file, func_tuple[1])
            print(f"new file: {new_file}")

            try:
                new_data = func_tuple[0](data)
                print(f"new {len(new_data)}")
            except Exception as err:
                print(f"cannot convert {file} because {err} skipped")
                return

            try:
                self.store_or_write_data(file, new_data, new_file)
            except Exception as err:
                print(f"cannot save {new_file} because {err} skipped")
                return
        return

    def get_open_type(self, apply_type):
        """ gets 'rb' for binary files or 'r' for text"""
        open_type = "rb"
        if str(apply_type) in [self.SVG2PAGE, self.XML2TXT, self.XML2HTML, self.TXT2SENT]:
            open_type = "r"
        return open_type

    # needs fixing
    @classmethod
    def create_file_name(cls, file, extension):
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

    def is_flag_true(self, flag):
        """is flag set in flag_dict
        values can be None, "None", "True", True, "False", False or strings
        Messay
        :param flag: 

        """
        val = self.flag_dict.get(flag)
        if not val or val == "None" or val == "False":
            return False
        if val:
            return True
        try:
            return ast.literal_eval(val)
        except Exception:
            return False

    def version(self):
        """reads setup.py and extracts line of form version='0.0.29'"""
        import pkg_resources  # part of setuptools
        version = pkg_resources.require("py4ami")[0].version
        return version

        # version = None
        # with open(Path(Path(__file__).parent.parent, "setup.py"), "r") as f:
        #     setup_lines = f.readlines()
        #     for line in setup_lines:
        #         match = re.match("\s*version\s*=\s*\'\s*(\d+\.\d+\.\d+)\s*\'\s*,", line)
        #         if match:
        #             version = match.group(1)
        #             break
        # print(f"VERSION {version}")
        # return version


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

    def get_file_contents(self, file):
        """return dictionary or None"""
        return self.file_dict.get(file)


class Converter(Enum):

    def __init__(self, converter_class, intype, outtype, indir=".", outdir="."):
        self.intype = intype
        self.indir = indir
        self.outtype = outtype
        self.outdir = outdir

    PDF2SVG = (Pdf2SvgConverter, "pdf", "svg", ".", "svg")
    # PDF2TXT = (PdfReader, Filetype.F_PDF, Filetype.F_TXT, ".", ".")
    XML2HTML = (Xml2HtmlConverter, "pdf", "html", ".", ".")
    XML2TXT = (Xml2TxtConverter, "xml", "txt", ".", ".")
    SVG2PAGE = (Svg2PageConverter, "svg", "html", "svg", "page")
    PAGE2SECT = (Page2SectConverter, "html", "html", "page", "sect")
    # TXT2SENT = (Txt2SentSplitter, Filetype.F_TXT, Filetype.F_TXT, ".", "sent")


def main():
    # make_cmd()
    """ main entry point for cmdline

    """
    # print(f"PYAMI")
    run_dsl = False
    run_tests = False  # needs re-implementing
    run_commands = True
    #    run_commands = False
    #    run_tests = True

    PyAMI.logger.debug(
        f"\n============== running pyami main ===============\n{sys.argv[1:]}")
    pyamix = PyAMI()
    # this needs commandline
    if run_commands:
#        logging.warning(f"main(): {sys.argv}")
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
