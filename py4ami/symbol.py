import configparser
import logging
import os
import urllib.request
from pathlib import Path

# local
from py4ami.file_lib import FileLib


class SymbolIni:

    """processes config/ini files and stores symbols created"""
    NS = "${ns}"
    PARENT = "__parent__"  # indicates parent directory of an INI or similar path
    CONFIG = "config"
    CONFIG_INI = "config.ini"
    PYAMI = "PYAMI"
    PYAMI_HOME = "PYAMI_HOME"
    PYAMI_DIR = "PYAMI_DIR"
    PRIMITIVES = ["<class 'int'>", "<class 'bool'>", "<class 'float'>"]
    LOGDIR = "logs"  # maybe need to change this
    SYMBOL_INI = "symbol.ini"

    SYMBOL_NOT_FOUND = "symbol not found"
    SYM_START = "${"
    SYM_END = "}"

    logger = logging.getLogger(SYMBOL_INI)

    def __init__(self, pyami):
        # FileLib.force_mkdir(self.LOGDIR)
        self.logger.debug(f"new PyAMI Object in SymbolIni")
        self.symbols = None
        self.pyami = pyami
        pyami.symbol_ini = self
        self.config = None
        self.setup_environment()
        self.process_config_files()
        self.pyami_home = None
        self.fileset = None

    def process_config_files(self):
        """ """
        # remove later
        # config path is linked as PYAMI

        self.pyami_home = os.getenv(self.PYAMI_HOME)  # "/Users/pm286/pyami/"
        if not self.pyami_home:
            # use `py4ami` to get bundled `config.ini`
            self.pyami_home = Path(__file__).parent
            self.logger.warning(f" environment variable $PYAMI_HOME not set, defaulting to bundled config.ini in {self.pyami_home}")
        if not os.path.exists(self.pyami_home) or not os.path.isdir(self.pyami_home):
            self.logger.fatal(f" $PYAMI_HOME {self.pyami_home} must be a directory")
            self.add_default_directory()
            return
        config_ini = os.path.join(self.pyami_home, self.CONFIG_INI)
        if not os.path.exists(config_ini) or os.path.isdir(config_ini):
            self.logger.fatal(f" {self.CONFIG_INI}  or {config_ini} must be an existing file")
            self.add_default_symbols()
            return

        self.pyami.args[self.CONFIG] = config_ini  # "/Users/pm286/pyami/config.ini.master"
        self.logger.debug(f"config path in args: {config_ini}")
        config_files_str = self.pyami.args.get(self.CONFIG)
        config_files = [] if config_files_str is None else config_files_str.split(",")
        self.symbols = {}
        self.fileset = set()
        self.logger.debug(f"config files {config_files_str}")
        for config_file in config_files:
            self.logger.info(f"****processing config: {config_file}")
            self.process_config_file(config_file)
        self.logger.debug(f"symbols after config {self.symbols}")

    def process_config_file(self, config_file):
        """

        :param config_file:

        """
        # this is the config path pointed to by PYAMI
        self.logger.info(f"config path {config_file}")
        self.logger.info(f"package {__package__}, path {__file__}, parent.parent {Path(__file__).parent.parent}", )
        if config_file.startswith("${") and config_file.endswith("}"):  # python config path
            file = os.environ[config_file[2:-1]]
        elif "/" not in config_file:
            file = os.path.join(FileLib.get_parent_dir(__file__), config_file)
        elif config_file.startswith("~"):  # relative to home
            file = self.get_home_dir(config_file)
        elif config_file.startswith("__file__"):  # relative to home
            file = self.get_code_dir(config_file)
        elif config_file.startswith("/"):  # absolute
            file = config_file
        else:
            file = None

        if file is not None:
            if os.path.exists(file):
                self.logger.debug("reading. " + file)
                self.apply_config_file(file)
            else:
                self.logger.warning(f"*** cannot find config path {file} ***")

    @classmethod
    def get_home_dir(cls, config_file):
        home = os.path.expanduser("~")
        file = home + config_file[len("~"):]
        return file

    @classmethod
    def get_code_dir(cls, config_file):
        home = os.path.expanduser("~")
        file = __file__
        print("FILE ", file)
        return file

    def apply_config_file(self, file):
        """reads config path, recursively replaces {} symbols and '~'
        :path: python config path

        :param file:

        """

        if file in self.fileset:  # avoid cycles
            self.logger.debug(f"{file} already in {self.fileset}")
            return
        else:
            self.fileset.add(file)

        self.config = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation())
        self.logger.info(f"reading config path {file}")
        # we have to substitute ami values before the configParser gets there!!!!!
        files_read = self.config.read(file)
        sections = self.config.sections()
        for section in sections:
            self.logger.debug(f"SECTION [{section}] in config path: {file}")
            self.convert_section_into_symbols_dict(file, section)

        # self.print_symbols()

        self.check_targets_exist(file)
        self.recurse_ini_files()

    def check_targets_exist(self, file):
        """
assumes value
        :param file:

        """
        for item in self.symbols.items():
            # we are going through ALL the symbols? possibly needs rethinking
            val = item[1]
            if val.startswith("http"):
                if self.pyami.is_flag_true(self.pyami.CHECK_URLS):
                    try:
                        with urllib.request.urlopen(val) as response:
                            html = response.read()
                    except urllib.error.HTTPError as ex:
                        print(f"Cannot read {val} as url {ex}")
            elif "/" in val:  # assume slash means path or url
                # Logic not yet worked out
                if not os.path.exists(val):  # all files
                    self.logger.debug(
                        f"{val} called from {file} does not exist as path")
            else:
                self.logger.debug(f"not a path: {val} in {file}")

    def setup_environment(self):
        """ lists environment variables but doesn't yet do anything"""
        for key in os.environ.keys():
            self.logger.info(f"{key}: {os.environ[key]}")

    def convert_section_into_symbols_dict(self, file, section):
        """

        :param file:
        :param section:

        """
        self.logger.debug("============" + section +
                          "============ in: " + file)
        self.logger.debug(f" self.symbols {self.symbols.keys()}")
        for key in self.config[section].keys():
            self.logger.debug(
                f"key in config: {key} == {self.config[section]} == {list(self.config[section].keys())}")

            raw_value = self.config[section][key]
            self.logger.debug(f"raw_value {raw_value}")
            # make substitutions
            # we replace __file__ with parent dirx of dictionary
            parent_dir = str(FileLib.get_parent_dir(file))
            if raw_value.startswith("~"):
                # home directory on all OS (?)
                new_value = os.path.expanduser("~") + raw_value[len("~"):]
            elif raw_value.startswith(self.PARENT):
                #  the prefix __file__ may have been expanded by the parser
                new_value = parent_dir + raw_value[len(self.PARENT):]
            elif raw_value.startswith("__file__"):
                logging.debug("__file__ is obsolete ", file)
            else:
                new_value = self.replace_symbols_in_arg(raw_value)
                if new_value != raw_value:
                    self.logger.debug(
                        f"ami symbols replaced {raw_value} with {new_value}")
                new_value = raw_value

            if key.startswith(self.NS):
                key = os.environ["LOGNAME"] + key[len(self.NS):]
                print("NAME", key)
            if "${" in new_value:
                self.logger.debug(f"Replaced local symbols")
                new_value = self.replace_symbols_in_arg(new_value)

            if key not in self.symbols:
                self.symbols[key] = new_value
                self.logger.debug(f"added symbol: {key} => {new_value}")
            elif self.symbols[key] != new_value:
                self.logger.info(
                    f"changed symbol: {key} from {self.symbols[key]} => {new_value}")
                self.symbols[key] = new_value
            elif self.symbols[key] == new_value:
                self.logger.debug(
                    f"retained symbol: {key} with {self.symbols[key]}")
                self.symbols[key] = new_value

        self.logger.debug(f"symbols for {file} {section}\n {self.symbols}")

    def recurse_ini_files(self):
        """follows links to all *_ini files and runs them recursively

        does not check for cycles (yet)


        """
        keys = list(self.symbols.keys())
        # print("KEYS", keys)
        for name in keys:
            if name.endswith("_ini"):
                if name not in self.symbols:
                    self.logger.error(
                        f"PROCESSING {self.current_file} ; cannot find symbol: {name} in {self.symbols}")
                else:
                    file = self.symbols[name]
                    self.apply_config_file(file)

    def replace_symbols_in_arg(self, arg):
        """replaces ${foo} with value of foo if in symbols

        treats any included "${" as literals (this is probably a user error)

        :param arg:

        """

        result = ""
        start = 0
        self.logger.info(f"expanding symbols in {arg}")
        arg = str(arg)
        while SymbolIni.SYM_START in arg[start:]:
            idx0 = arg.index(SymbolIni.SYM_START, start)
            result += arg[start:idx0]
            idx1 = arg.index(SymbolIni.SYM_END, start)
            symbol = arg[idx0 + len(SymbolIni.SYM_START):idx1]
            replace = self.symbols.get(symbol)
            if replace is None:
                if not self.is_reserved_symbol(symbol):
                    self.print_symbols()
                    raise ValueError(f"{self.SYMBOL_NOT_FOUND}: {symbol}")
                else:
                    self.logger.warning(f"found reserved symbol {symbol}")
            elif replace != symbol:
                self.logger.debug(symbol, " REPLACE", replace)
            else:
                # symbol not found
                raise ValueError(f"symbol replaces itself {symbol}")
            self.logger.debug(f"{idx0} {idx1} {symbol} {replace}")
            orig = arg[idx0: idx1 + len(SymbolIni.SYM_END)]
            result += replace if replace is not None else orig
            start = idx1 + len(SymbolIni.SYM_END)
        result += arg[start:]
        if arg != result:
            self.logger.info(f"expanded {arg} to {result}")
        return result

        # return arg[2:-1] if arg.startswith(SYM_START) and arg.endswith(SYM_END) else arg

    @classmethod
    def is_reserved_symbol(cls, symbol):
        """reserved symbols start with underscore"""
        return symbol is not None and symbol.startswith("_")

    def print_symbols(self):
        """ """
        print("\n\nsymbols>>")
        for name in self.symbols:
            print(f"{name}:{self.symbols[name]}")
        print("<<\n\n")

    def add_default_symbols(self):
        logging.warning(f"must create default symbols")

    def add_default_directory(self):
        logging.warning(f"must create default directory")
