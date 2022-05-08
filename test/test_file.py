"""tests for file_lib"""
import os
import logging
from py4ami.file_lib import AmiPath, PROJ, FILE

FILE_LIB = "file_lib"
PDF_LIB = "pdf_lib"
TEXT_LIB = "text_lib"
_SETUP = "_setup"
_TEARDOWN = "_teardown"
TEST = "test"


class TestFile:
    logger = logging.getLogger("test_file")
    TEST = "test"

    OPTIONS = [
        FILE_LIB,
        PDF_LIB,
        TEXT_LIB,
        _SETUP,
        _TEARDOWN,
    ]

    @classmethod
    def test_templates(cls):
        PYDIAG = "../../python/diagrams"
        #    simple_test()

        cls._analyze_sections(PYDIAG + "/" + "luke/papers20210121")  # Zero?
        cls._analyze_sections(PYDIAG + "/" + "../liion")
        cls._analyze_sections(PYDIAG + "/" + "satish/cct")

    @classmethod
    def test_file_simple(cls):
        PYDIAG = "../../python/diagrams"
        globbed_files = AmiPath.create_ami_path_from_templates("abstract", {PROJ: PYDIAG + "/" + "../liion"}),
        cls.logger.debug(f"globbed files {len(globbed_files)}, {globbed_files[:5]}")

    @classmethod
    def _analyze_sections(cls, proj_dir):
        cls.logger.info(f"proj dir exists  {os.path.exists(proj_dir)}")
        for ami_path in [
            AmiPath.create_ami_path_from_templates("abstract", {PROJ: proj_dir, FILE: "*background*"}),
            AmiPath.create_ami_path_from_templates("acknowledge", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("affiliation", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("author", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("fig_caption", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("introduction", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("jrnl_title", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("keyword", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("method", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("octree", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("pdfimage", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("pub_date", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("publisher", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("reference", {PROJ: proj_dir}),
            # AmiPath.create_ami_path_from_templates("results", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("results_discuss", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("climate10_", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("table", {PROJ: proj_dir}),
            AmiPath.create_ami_path_from_templates("title", {PROJ: proj_dir}),
        ]:
            globbed_files = ami_path.get_globbed_files()
            cls.logger.warning(f"globbed files: {len(globbed_files)} {globbed_files[:5]}")
            return

    @classmethod
    def example_setup(cls, pyamix):
        """ setup test or examples

        :pyamix:
        """
        pyamix.run_commands([
            "--delete ${exam_temp}",
            "--copy ${examples_test.p} ${exam_temp} overwrite",
        ])

    @classmethod
    def example_teardown(cls, pyamix):
        """ clean example files

        """
        pyamix.run_command([
            "--delete", "${exam_temp}",
        ])

    @classmethod
    def run_arg_tests(cls, args):
        """This needs revision , maybe using Examples()"""
        cls.logger.warning(f"*****running tests : {args[TEST]}")
        if not args[TEST]:
            cls.logger.warning(f"No tests given: choose some/all of {TEST}")
            return
        if FILE_LIB in args[TEST]:
            cls.logger.warning("run test_file")
            cls.test_file.main()
        if PDF_LIB in args[TEST]:
            cls.logger.warning("run test_pdf")
            cls.test_pdf.test_read_pdf()
        if TEXT_LIB in args[TEST]:
            cls.logger.warning("run test_text NYI")


def main():
    TestFile.test_file_simple()
    TestFile.test_templates()
