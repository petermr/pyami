"""tests for file_lib"""
import os
import logging
from file_lib import AmiPath
from file_lib import PROJ, FILE

logger = logging.getLogger("test_file")
def test_templates():
    PYDIAG = "../../python/diagrams"
    #    simple_test()

    _analyze_sections(PYDIAG + "/" + "luke/papers20210121")  # Zero?
    _analyze_sections(PYDIAG + "/" + "../liion")
    _analyze_sections(PYDIAG + "/" + "satish/cct")


def test_file_simple():
    PYDIAG = "../../python/diagrams"
    globbed_files = AmiPath.create_ami_path_from_templates("abstract", {PROJ: PYDIAG + "/" + "../liion"}),
    logger.debug(f"globbed files {len(globbed_files)}, {globbed_files[:5]}")


def _analyze_sections(proj_dir):
    logger.info(f"proj dir exists  {os.path.exists(proj_dir)}")
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
        AmiPath.create_ami_path_from_templates("svg", {PROJ: proj_dir}),
        AmiPath.create_ami_path_from_templates("table", {PROJ: proj_dir}),
        AmiPath.create_ami_path_from_templates("title", {PROJ: proj_dir}),
    ]:
        globbed_files = ami_path.get_globbed_files()
        logger.warning(f"globbed files: {len(globbed_files)} {globbed_files[:5]}")
        return

def main():
    test_file_simple()
    test_templates()

