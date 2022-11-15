# test pyami
import argparse
import ast
from pathlib import Path
import sys
import unittest
# local
from py4ami.pyamix import PyAMI
from py4ami.pyamix import main
from test.test_all import AmiAnyTest
from test.test_dict import AMIDICTS, TestAmiDictionary


class TestPyami(AmiAnyTest):

    """ tests commandline parsing, etc but not detailed methods
    some of these tests are old-style before we introduced SUBCOMMANDS
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

    @unittest.skip("obsolete")
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

    @unittest.skip("obsolete")
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
    @unittest.skip("obsolete")
    def test_no_flags(self):
        """
        """

        args = "--apply pdf2svg"
        pyami = PyAMI()
        pyami.run_command(args)
        assert not pyami.flag_dict.get(pyami.PRINT_SYMBOLS)
        print(f"flags {pyami.flag_dict}")

    @unittest.skip("obsolete")
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

    @unittest.skip("obsolete")
    def test_set_unknown_flag(self):
        """set unknown flag, with possible checking
        """
        pyami = PyAMI()
        args = "--flags foo=bar"
        pyami.run_command(args)
        assert pyami.flag_dict.get(PyAMI.RECURSE), f"RECURSE should be True by default"

    @unittest.skip("obsolete")
    def test_set_numeric_flag(self):
        """set numeric flag
        """
        pyami = PyAMI()
        args = "--flags foo=42"
        pyami.run_command(args)
        assert pyami.flag_dict.get("foo") == 42, f" foo shoule be 42"


    @unittest.skip("obsolete")
    def test_multiple_flags(self):
        """
        """
        pyami = PyAMI()

        args = "--flags print_symbols=True foo=bar"
        pyami.run_command(args)
        assert pyami.flag_dict.get(PyAMI.PRINT_SYMBOLS)
        assert pyami.flag_dict.get("foo") == "bar"

    def test_argparse_from_strings(self):
        """running commandline tests without sys.atgv"""
        parser = argparse.ArgumentParser()
        parser.add_argument('--foo')
        args = parser.parse_args(['--foo', 'BAR'])
        var_dict = vars(args)
        assert var_dict == {'foo': 'BAR'}

        parser.add_argument('--plugh')
        args = parser.parse_args('--plugh XYZZY'.split())
        var_dict = vars(args)
        assert var_dict == {'foo': None, 'plugh': 'XYZZY'}

    def test_argparse_BAD_command_args(self):

        with self.assertRaises(ValueError) as e:
            infile = TestAmiDictionary().setup()[TestAmiDictionary.ETHNOBOT_DICT]
            pyami = PyAMI()
            args = f"DICT --dict {infile} --validatex"
            pyami.run_command(args)
        assert "bad command arguments" in str(e.exception), f"exception [{str(e)}]"


    def test_argparse_DICT_validate(self):

        infile = TestAmiDictionary().setup()[TestAmiDictionary.ETHNOBOT_DICT]
        pyami = PyAMI()
        args = f"DICT --dict {infile} --validate"
        pyami.run_command(args)

    def test_argparse_PDF_pdf2html(self):

        ff = Path(__file__)
        infile = Path(ff.parent.parent, "test", "resources/ipcc/Chapter06/fulltext.pdf")
        outdir = Path(ff.parent.parent, "temp_oldx/ipcc_html/Chapter06/")
        pyami = PyAMI()
        args = f"PDF --inpath {infile} --outdir temp_oldx --pdf2html pdfminer --pages 5 8 10 13 --outstem exec"
        pyami.run_command(args)

    @unittest.skip("not yet written")
    def test_argparse_PROJECT_pdf2html(self):

        indir = "not yet written, contains PDF files"
        pyami = PyAMI()
        args = f"PROJECT --indir {indir} --outdir temp_oldx"
        pyami.run_command(args)

    def test_parent_parser(self):
        """reusable code"""
        """from https://stackoverflow.com/questions/7498595/python-argparse-add-argument-to-multiple-subparsers/7498853#7498853"""
        # Same main parser as usual
        parser = argparse.ArgumentParser()

        # Usual arguments which are applicable for the whole script / top-level args
        parser.add_argument('--verbose', help='Common top-level parameter',
                            action='store_true', required=False)

        # Same subparsers as usual
        subparsers = parser.add_subparsers(help='Desired action to perform', dest='action')

        # Usual subparsers not using common options
        parser_other = subparsers.add_parser("extra-action", help='Do something without db')

        # Create parent subparser. Note `add_help=False` and creation via `argparse.`
        parent_parser = argparse.ArgumentParser(add_help=False)
        parent_parser.add_argument('-p', help='add db parameter', required=True)

        # Subparsers based on parent

        parser_create = subparsers.add_parser("create", parents=[parent_parser],
                                              help='Create something')
        # Add some arguments exclusively for parser_create

        parser_update = subparsers.add_parser("update", parents=[parent_parser],
                                              help='Update something')
        # Add some arguments exclusively for parser_update

        parser.print_help()
        """usage: [-h] [--verbose] {extra-action,create,update} ...

positional arguments:
  {extra-action,create,update}
                        Desired action to perform
    extra-action        Do something without db
    create              Create something
    update              Update something

optional arguments:
  -h, --help            show this help message and exit
  --verbose             Common top-level parameter
And the help message for the create action:

>>> parser_create.print_help()
usage:  create [-h] -p P

optional arguments:
  -h, --help  show this help message and exit
  -p P        add db parameter
  """
