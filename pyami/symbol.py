import logging
# from logging import Level
import os
import configparser
import urllib.request
import re
from file_lib import FileLib
from util import Util


class SymbolIni:

    """processes config/ini files and stores symbols created"""
    NS = "${ns}"
    PARENT = "__parent__"  # indicates parent directory of an INI or similar file
    CONFIG = "config"
    PYAMI = "PYAMI"
    PRIMITIVES = ["<class 'int'>", "<class 'bool'>", "<class 'float'>"]
    LOGDIR = "logs"  # maybe need to change this

    # logger = Util.set_logger("symbol_ini.x")
    logger = logging.getLogger("symbol.ini")

    # this creates multiple output to console, needs taming
    # if logger is None:
    #     logger = Util.set_logger(
    #         "symbol_ini.x", logger_level=logging.INFO, log_file=os.path.join(LOGDIR, "symbol_ini.log"))

    def __init__(self, pyami):
        # FileLib.force_mkdir(self.LOGDIR)
        # self.logger.setLevel(logging.INFO)
        self.symbols = None
        self.pyami = pyami
        pyami.symbol_ini = self

        self.setup_environment()
        self.process_config_files()

    def process_config_files(self):
        """ """
        # remove later
        # config file is linked as PYAMI
        self.pyami.args[self.CONFIG] = os.getenv(self.PYAMI)  # "/Users/pm286/pyami/config.ini"
        config_files_str = self.pyami.args.get(self.CONFIG)
        config_files = [] if config_files_str is None else config_files_str.split(",")
        self.symbols = {}
        self.fileset = set()
        for config_file in config_files:
            self.logger.info(f"****processing config: {config_file}")
            self.process_config_file(config_file)
        self.logger.debug(f"symbols after config {self.symbols}")

    def process_config_file(self, config_file):
        """

        :param config_file:

        """
        if config_file.startswith("${") and config_file.endswith("}"):  # python config file
            file = os.environ[config_file[2:-1]]
        elif "/" not in config_file:
            file = os.path.join(FileLib.get_parent_dir(__file__), config_file)
        elif config_file.startswith("~"):  # relative to home
            home = os.path.expanduser("~")
            file = home + config_file[len("~"):]
        elif config_file.startswith("/"):  # absolute
            file = config_file
        else:
            file = None

        if file is not None:
            if os.path.exists(file):
                self.logger.debug("reading " + file)
                self.apply_config_file(file)
            else:
                self.logger.warning(f"*** cannot find config file {file} ***")

    def apply_config_file(self, file):
        """reads config file, recursively replaces {} symbols and '~'
        :file: python config file

        :param file:

        """

        if file in self.fileset:  # avoid cycles
            self.logger.debug(f"{file} already in {self.fileset}")
            return;
        else:
            self.fileset.add(file)

        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.logger.info(f"reading config file {file}")
        files_read = self.config.read(file)
        sections = self.config.sections()
        for section in sections:
            self.logger.warning(f"SECTiON in config file: {section}")
            self.convert_section_into_symbols_dict(file, section)

        self.check_targets_exist(file)
        self.recurse_ini_files()

    def check_targets_exist(self, file):
        """
assumes value
        :param file:

        """
        for item in self.symbols.items():
            val = item[1];
            if val.startswith("http"):
                if self.pyami.flagged(self.pyami.CHECK_URLS):
                    try:
                        with urllib.request.urlopen(val) as response:
                            html = response.read()
                    except urllib.error.HTTPError as ex:
                        print(f"Cannot read {val} as url {ex}")
            elif "/" in val:  # assume slash means file or url
                if not os.path.exists(val):  # all files
                    self.logger.error(f"{val} in {file} does not exist as file")
            else:
                print("non-existent target: " + val + " in " + file)

    def setup_environment(self):
        """ """
        for key in os.environ.keys():
            self.logger.info(f"{key}: {os.environ[key]}")

    def convert_section_into_symbols_dict(self, file, section):
        """

        :param file:
        :param section:

        """
        self.logger.warning("============" + section + "============" + file)
        for name in self.config[section].keys():
            if name in self.symbols:
                self.logger.debug(f"{name} already defined, skipped")
            else:
                raw_value = self.config[section][name]
                # make substitutions
                # we replace __file__ with parent dir of dictionary
                parent_dir = str(FileLib.get_parent_dir(file))
                if raw_value.startswith("~"):
                    # home directory on all OS (?)
                    new_value = os.path.expanduser("~") + raw_value[len("~"):]
                elif raw_value.startswith(self.PARENT):
                    #  the prefix __file__ may have been expanded by the parser
                    new_value = parent_dir + raw_value[len(self.PARENT):]
                elif raw_value.startswith("__file__"):
                    print("__file__ is obsolete ", file)
                else:
                    new_value = raw_value

                if name.startswith(self.NS):
                    name = os.environ["LOGNAME"] + name[len(self.NS):]
                    print("NAME", name)

                self.symbols[name] = new_value
                self.logger.warning(f"added symbol: {name} => {new_value}")

        self.logger.warning(f"symbols for {file} {section}\n {self.symbols}")

    def recurse_ini_files(self):
        """follows links to all *_ini files and runs them recursively

        does not check for cycles (yet)


        """
        keys = list(self.symbols.keys())
        # print("KEYS", keys)
        for name in keys:
            if name.endswith("_ini"):
                if name not in self.symbols:
                    self.logger.error(f"PROCESSING {self.current_file} ; cannot find symbol: {name} in {self.symbols}")
                else:
                    file = self.symbols[name]
                    self.apply_config_file(file)

    def replace_symbols(self, arg):
        """

        :param arg:

        """
        # print(f"ARGLIST {type(arglist)} {arglist}")
        self.logger.warning(f"SYMBOLS: {self.symbols}")

        if arg is None:
            return None
        elif isinstance(arg, str):
            new_arg = self.replace_symbols_in_arg(arg)
            print(f"{arg} => {new_arg}")
            return new_arg
        elif isinstance(arg, list):
            new_arg = []
            for item in arg:
                print(f"SUBLIST_ITEM {item}")
                new_item = self.replace_symbols_in_arg(item)
                new_arg.append(new_item)
            return new_arg
        elif self.is_primitive(arg):
            return arg
        else:
            print(f"Cannot process arg {arg}")
            return arg

    def is_primitive(self, arg):
        """returns true if string of classtype is maps to int, bool, etc. Horrible

        :param arg:

        """
        return str(type(arg)) in self.PRIMITIVES

    def replace_symbols_in_arg(self, arg):
        """replaces ${foo} with value of foo if in symbols

        treats any included "${" as literals (this is probably a user error)

        :param arg:

        """

        result = ""
        start = 0
        SYM_START = "${"
        SYM_END = "}"
        self.logger.info(f"expanding symbols in {arg}")
        while SYM_START in arg[start:]:
            idx0 = arg.index(SYM_START, start)
            result += arg[start:idx0]
            idx1 = arg.index(SYM_END, start)
            symbol = arg[idx0 + len(SYM_START):idx1]
            replace = self.symbols.get(symbol)
            if replace != symbol:
                self.logger.debug(symbol, " REPLACE", replace)
            end = idx1 + 1
            result += replace if replace is not None else arg[idx0: idx1 + len(SYM_END)]
            start = end
        result += arg[start:]
        if arg != result:
            self.logger.info(f"expanded {arg} to {result}")
        return result

        # return arg[2:-1] if arg.startswith(SYM_START) and arg.endswith(SYM_END) else arg

    def print_symbols(self):
        """ """
        print("symbols>>")
        for name in self.symbols:
            print(f"{name}:{self.symbols[name]}")
