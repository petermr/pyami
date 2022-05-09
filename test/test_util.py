# test util

import logging
import sys
import unittest
from pathlib import Path
import shutil

# local
from py4ami.util import Util
from test.resources import Resources

logger = logging.getLogger("py4ami_test_util")

class TestUtil(unittest.TestCase):

    # def __init__(self):
    sys_argv_save = None

    @classmethod
    def setUp(cls):
        """save args as they will be edited"""
        cls.sys_argv_save = sys.argv

    @classmethod
    def tearDown(cls):
        """restore args"""
        sys.argv = cls.sys_argv_save

    @classmethod
    def test_add_argstr(cls):
        # this is a hack as normally there is only one element
        sys.argv = sys.argv[1:]
        assert sys.argv[1:] == []
        cmd = "foo bar plinge"
        Util.add_sys_argv_str(cmd)
        assert sys.argv[1:] == ["foo", "bar", "plinge"]

    @classmethod
    def test_add_args(cls):
        # this is a hack as normally there is only one element
        sys.argv = sys.argv[1:]
        assert sys.argv[1:] == []
        args = ["foox", "barx", "plingex"]
        Util.add_sys_argv(args)
        assert sys.argv[1:] == ["foox", "barx", "plingex"]

    @classmethod
    def test_copy_anything(cls):
        src = Resources.CLIMATE_10_SVG_DIR
        dst = Path(Resources.TEMP_DIR, "tempzz")
        if dst.exists():
            shutil.rmtree(dst)
        Util.copyanything(src, dst)
        assert Path(dst).exists()


