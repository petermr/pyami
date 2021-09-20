import logging
from typing import Tuple
from configparser import ConfigParser, ExtendedInterpolation
import os
import urllib.request
from xml.etree import ElementTree as ET
import ast


class Util:
    """Utilities, mainly staticmethod or classmethod and not tightly linked to AMI"""

    @classmethod
    def set_logger(cls, module,
                   ch_level=logging.INFO, fh_level=logging.DEBUG,
                   log_file=None, logger_level=logging.WARNING):
        """create console and stream loggers

        taken from https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook

        :param module: module to create logger for
        :param ch_level:
        :param fh_level:
        :param log_file:
        :param logger_level:
        :returns: singleton logger for module
        :rtype logger:

        """
        print("pyami: setting logger")
        _logger = logging.getLogger(module)
        _logger.setLevel(logger_level)
        # create path handler

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if log_file is not None:
            fh = logging.FileHandler(log_file)
            fh.setLevel(fh_level)
            fh.setFormatter(formatter)
            _logger.addHandler(fh)

        # create console handler
        ch = logging.StreamHandler()
        ch.setLevel(ch_level)
        ch.setFormatter(formatter)
        _logger.addHandler(ch)

        _logger.debug(f"PyAMI {_logger.level}{_logger.name}")
        return _logger

    @staticmethod
    def check_exists(file):
        """
        raise exception on null value or non-existent path
        """
        if file is None:
            raise Exception("null path")

        if os.path.isdir(file):
#            print(path, "is directory")
            pass
        elif os.path.isfile(file):
#            print(path, "is path")
            pass
        else:
            try:
                f = open(file, "r")
                print("tried to open", file)
                f.close()
            except:
                raise FileNotFoundError(str(file) + " should exist")

    @staticmethod
    def find_unique_keystart(keys, start):
        """finds keys that start with 'start'
        return a list, empty if none found or null args"""
        return [] if keys is None or start is None else [k for k in keys if k.startswith(start)]

    @staticmethod
    def find_unique_dict_entry(the_dict, start):
        """
        return None if 0 or >= keys found
        """
        keys = Util.find_unique_keystart(the_dict, start)
        if len(keys) == 1:
            return the_dict[keys[0]]
        print("matching keys:", keys)
        return None

    @classmethod
    def read_pydict_from_json(cls, file):
        with open(file, "r") as f:
            contents = f.read()
            dictionary = ast.literal_eval(contents)
            return dictionary

class AmiLogger():
    """wrapper for logger to limit or condense voluminous output

    adds a dictionary of counts for each log level
    """
    def __init__(self, logger, initial=10, routine=100):
        """create from an existing logger"""
        self.logger = logger
        self.func_dict = {
            "debug": self.logger.debug,
            "info": self.logger.info,
            "warning": self.logger.warning,
            "error": self.logger.error,

        }
        self.initial = initial
        self.routine = routine
        self.count = {
        }
        self.reset_counts()

    def reset_counts(self):
        for level in self.func_dict.keys():
            self.count[level] = 0

    # these will be called instead of logger
    def debug(self, msg):
        self._print_count(msg, "debug")
    def info(self, msg):
        self._print_count(msg, "info")
    def warning(self, msg):
        self._print_count(msg, "warning")
    def error(self, msg):
        self._print_count(msg, "error")
    # =======

    def _print_count(self, msg, level):
        """called by the wrapper"""
        logger_func = self.func_dict[level]
        if not level in self.count:
            self.count[level] = 0;
        if self.count[level] <= self.initial or self.count[level] % self.routine == 1:
            logger_func(f"{self.count[level]}: {msg}")
        else:
            print(".", end="")
        self.count[level] += 1

