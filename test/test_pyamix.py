# test pyami
import ast
import sys
import unittest
# local
from py4ami.pyamix import PyAMI
from py4ami.pyamix import main
from test.test_all import AmiAnyTest


class TestPyami(AmiAnyTest):

    """ tests commandline parsing, etc but not detailed methods
    """

    def test_no_args(self):
        """empty command
        outputs help (see log) and exits """
        pyamix = PyAMI()
        args = []
        pyamix.run_command(args)

    def test_help(self):
        """outputs help and exits"""
        pyamix = PyAMI()
        args = ["-h"]
        try:
            pyamix.run_command(args)
        except SystemExit as e:
            print("SystemExit {e}")

# test APPLY

    def test_apply_missing_value(self):
        """Missing parameter value
        outputs brief help and error message (see log)
        """
        args = ["--apply"] # should have value
        try:
            PyAMI().run_command(args)
            assert False, "should throw exception before this"
        except ValueError as e:
            assert True, "should fail in parser {e"

    def test_apply_pdf2svg(self):
        """Valid arguments (but no action)"""
        args = "--apply pdf2svg"
        try:
            PyAMI().run_command(args)
            assert True, "OK"
        except SystemExit:
            assert False, "should not throw SystemExit for {args}"

    def test_apply_bad_param_value(self):
        """bad argument value
        args = '--apply nonexistent'
        Fails with ValueError
        Outputs reason on log
        """

        args = ["foo", "--apply nonexistent"]
        try:
            PyAMI().run_command(args)
            assert False, "should fail before this with 'invalid choice'"
        except ValueError as e:
            assert True

# flags
    def test_no_flags(self):
        """
        """

        args = "--apply pdf2svg"
        pyami = PyAMI()
        pyami.run_command(args)
        assert not pyami.flag_dict.get(pyami.PRINT_SYMBOLS)
        print(f"flags {pyami.flag_dict}")

    def test_single_flag(self):
        """Checks name is kept as a string and uses boolean as test
        """

        pyami = PyAMI()
        args = "--flags print_symbols=False"
        pyami.run_command(args)
        assert pyami.flag_dict.get(PyAMI.RECURSE), f"RECURSE should be True by default"
        assert not pyami.is_flag_true(PyAMI.PRINT_SYMBOLS)

        print("===========with symbols==========")
        args = "--flags print_symbols"
        pyami.run_command(args)
        assert pyami.is_flag_true(PyAMI.PRINT_SYMBOLS)

    def test_set_unknown_flag(self):
        """set unknown flag, with possible checking
        """
        pyami = PyAMI()
        args = "--flags foo=bar"
        pyami.run_command(args)
        assert pyami.flag_dict.get(PyAMI.RECURSE), f"RECURSE should be True by default"

    def test_set_numeric_flag(self):
        """set numeric flag
        """
        pyami = PyAMI()
        args = "--flags foo=42"
        pyami.run_command(args)
        assert pyami.flag_dict.get("foo") == 42, f" foo shoule be 42"


    def test_multiple_flags(self):
        """
        """
        pyami = PyAMI()

        args = "--flags print_symbols=True foo=bar"
        pyami.run_command(args)
        assert pyami.flag_dict.get(PyAMI.PRINT_SYMBOLS)
        assert pyami.flag_dict.get("foo") == "bar"



