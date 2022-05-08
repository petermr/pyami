# test pyami
import sys
import unittest
# local
from py4ami.pyamix import PyAMI
from py4ami.pyamix import main

class TestPyami(unittest.TestCase):

    """ tests commandline parsing, etc but not detailed methods
    """

    @classmethod
    def test_no_args(cls):
        """empty command
        outputs help (see log) and exits """
        pyamix = PyAMI()
        args = []
        pyamix.run_command(args)

    @classmethod
    def test_help(cls):
        """outputs help and exits"""
        pyamix = PyAMI()
        args = ["-h"]
        try:
            pyamix.run_command(args)
        except SystemExit as e:
            print("SystemExit {e}")

# test APPLY

    @classmethod
    def test_apply_missing_value(cls):
        """Missing parameter value
        outputs brief help and error message (see log)
        """
        pyamix = PyAMI()
        args = ["--apply"] # should have value
        try:
            pyamix.run_command(args)
            assert False, "should throw exception before this"
        except ValueError as e:
            assert True, "should fail in parser {e"

    @classmethod
    def test_apply_pdf2svg(cls):
        """Valid arguments (but no action)"""
        pyamix = PyAMI()
        args = "--apply pdf2svg"
        try:
            pyamix.run_command(args)
            assert True, "OK"
        except SystemExit:
            assert False, "should not throw SystemExit for {args}"

    @classmethod
    def test_apply_bad_param_value(cls):
        """bad argument value
        args = '--apply nonexistent'
        Fails with ValueError
        Outputs reason on log
        """

        pyamix = PyAMI()
        args = "--apply nonexistent"
        try:
            pyamix.run_command(args)
            assert False, "should fail before this with 'invalid choice'"
        except ValueError as e:
            assert True


