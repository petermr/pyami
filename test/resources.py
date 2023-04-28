"""Resources such as data used by other modules
This may develop into a dataclass"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class Resources:
    """
    Files can be:
    * TEST - input for test, distributed with package
    * TEMP - per-test output (not in repo) - can be used for further understanding
    * LOCAL* - other files in user directory - relevant tests ignored if not present
           (these are dictionaries, corpora, etc. used for development but not used for regression tests)
    """
    # small example projects in package
    RESOURCES_DIR = Path(Path(__file__).parent.parent, "py4ami", "resources")
    assert RESOURCES_DIR.name == "resources", f"{RESOURCES_DIR.name} should be 'resources'"

    # test data (often snipped form large projects
    TEST_RESOURCES_DIR = Path(Path(__file__).parent, "resources")
    assert TEST_RESOURCES_DIR.name == "resources", f"{TEST_RESOURCES_DIR.name} should be 'resources'"
    assert TEST_RESOURCES_DIR.exists(), f"dir exists {TEST_RESOURCES_DIR}"
    assert TEST_RESOURCES_DIR.is_dir(), f"file exists {TEST_RESOURCES_DIR}"

    # svg test data
    CLIMATE_10_PROJ = "climate10_proj"
    TEST_CLIMATE_10_PROJ_DIR = Path(TEST_RESOURCES_DIR, CLIMATE_10_PROJ)
    assert TEST_CLIMATE_10_PROJ_DIR.exists()
    TEST_CLIMATE_10_SVG_DIR = Path(TEST_CLIMATE_10_PROJ_DIR, "climate10", "svg")

    # ipcc and html
    TEST_IPCC_DIR = Path(TEST_RESOURCES_DIR, "ipcc")
    TEST_IPCC_DICT_DIR = Path(TEST_IPCC_DIR, "dict")

    # local files not in package; mainly for development can be skipped
    HOME = os.path.expanduser("~")
    LOCAL_PROJECT_DIR = Path(HOME, "projects")  # PMR specific - change if you are developing with your own projects
    LOCAL_PROJECT_DIR = LOCAL_PROJECT_DIR if LOCAL_PROJECT_DIR.exists() else None
    USE_LOCAL = False  # change for tests that require local files
    if USE_LOCAL and LOCAL_PROJECT_DIR:
        LOCAL_SEMANTIC_CLIMATE_REPO = None if not LOCAL_PROJECT_DIR else Path(LOCAL_PROJECT_DIR, "semanticClimate")
        LOCAL_IPCC_DIR = Path(LOCAL_SEMANTIC_CLIMATE_REPO, "ipcc/ar6/wg3")  # PMR debugging
        if Path(LOCAL_IPCC_DIR).exists():
            LOCAL_IPCC_CHAP07 = Path(LOCAL_IPCC_DIR, "Chapter07")
            assert LOCAL_IPCC_CHAP07.exists()
            LOCAL_IPCC_CHAP07_DICT = Path(LOCAL_IPCC_CHAP07, "dict")
            assert LOCAL_IPCC_CHAP07_DICT.exists()
            LOCAL_IPCC_CHAP07_ABB_DICT = Path(LOCAL_IPCC_CHAP07_DICT, "ip_3_7_agric_abb.xml")
            # assert IPCC_CHAP07_ABB_DICT.exists()
            LOCAL_IPCC_CHAP07_MAN_DICT = Path(LOCAL_IPCC_CHAP07_DICT, "ip_3_7_agric_man.xml")
            assert LOCAL_IPCC_CHAP07_MAN_DICT.exists(), f"no dict {LOCAL_IPCC_CHAP07_MAN_DICT}"

    TEST_IPCC_CHAP02 = Path(TEST_IPCC_DIR, "Chapter02")
    assert TEST_IPCC_CHAP02.exists()
    TEST_IPCC_CHAP02_DICT = Path(TEST_IPCC_CHAP02, "dict")
    assert TEST_IPCC_CHAP02_DICT.exists()
    TEST_IPCC_CHAP02_ABB_DICT = Path(TEST_IPCC_CHAP02_DICT, "ip_3_2_emissions_abb.xml")
    assert TEST_IPCC_CHAP02_ABB_DICT.exists()
    TEST_IPCC_CHAP02_MAN_DICT = Path(TEST_IPCC_CHAP02_DICT, "ip_3_2_emissions_man.xml")
    assert TEST_IPCC_CHAP02_MAN_DICT.exists()

    TEST_IPCC_CHAP04 = Path(TEST_IPCC_DIR, "Chapter04")
    assert TEST_IPCC_CHAP04.exists()
    TEST_IPCC_CHAP06 = Path(TEST_IPCC_DIR, "Chapter06")
    assert TEST_IPCC_CHAP06.exists()
    TEST_IPCC_CHAP06_PDF = Path(TEST_IPCC_CHAP06, "fulltext.pdf")
    assert TEST_IPCC_CHAP06_PDF.exists()

    TEST_IPCC_CHAP08 = Path(TEST_IPCC_DIR, "Chapter08")
    assert TEST_IPCC_CHAP08.exists()
    TEST_IPCC_CHAP08_DICT = Path(TEST_IPCC_CHAP08, "dict")
    assert TEST_IPCC_CHAP08_DICT.exists()
    TEST_IPCC_CHAP08_ABB_DICT = Path(TEST_IPCC_CHAP08_DICT, "ip_3_8_urban_abb.xml")
    assert TEST_IPCC_CHAP08_ABB_DICT.exists()
    TEST_IPCC_CHAP08_MAN_DICT = Path(TEST_IPCC_CHAP08_DICT, "ip_3_8_urban_man.xml")
    assert TEST_IPCC_CHAP08_MAN_DICT.exists()

    TEST_IPCC_CHAP15 = Path(TEST_IPCC_DIR, "Chapter15")
    assert TEST_IPCC_CHAP15.exists()
    TEST_IPCC_CHAP17 = Path(TEST_IPCC_DIR, "Chapter17")
    assert TEST_IPCC_CHAP17.exists()

    TEST_IPCC_LONGER_REPORT = Path(TEST_IPCC_DIR, "LongerReport")
    assert TEST_IPCC_LONGER_REPORT.exists(), f"{TEST_IPCC_LONGER_REPORT} should exist"

    TEST_IPCC_SROCC = Path(TEST_IPCC_DIR, "srocc")
    assert TEST_IPCC_SROCC.exists(), f"{TEST_IPCC_SROCC} should exist"

    TEST_IPCC_SR15 = Path(TEST_IPCC_DIR, "sr15")
    assert TEST_IPCC_SR15.exists(), f"{TEST_IPCC_SR15} should exist"

    TEST_IPCC_SRCCL = Path(TEST_IPCC_DIR, "srccl")
    assert TEST_IPCC_SRCCL.exists(), f"{TEST_IPCC_SRCCL} should exist"

    # pdfs
    TEST_PDFS_DIR = Path(TEST_RESOURCES_DIR, "pdfs")
    assert TEST_PDFS_DIR.exists()

    # TEST_IPCC_WG2 = Path(TEST_IPCC_DIR, "wg2")
    TEST_IPCC_WG2_CHAP03 = Path(TEST_IPCC_DIR, "wg2_03")
    TEST_IPCC_WG2_CHAP03_PDF = Path(TEST_IPCC_WG2_CHAP03, "fulltext.pdf")
    assert TEST_IPCC_WG2_CHAP03_PDF.exists(), f"{TEST_IPCC_WG2_CHAP03_PDF} should exist"

    # could be changed by user
    TEMP_DIR = Path(Path(__file__).parent.parent, "temp")

    WG_REPORTS = {
        "default": {
            "footer_height": 70,
            "header_height": 70,
        },
        "SROCC_TS": {
            "name": "SROCC_TS",
            "input_pdf": Path(TEST_IPCC_SROCC, "ts", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "srocc", "ts", "pages"),
            "footer_height": 70,
            "header_height": 70
        },
        "SROCC_SPM": {
            "name": "SROCC_SPM",
            "input_pdf": Path(TEST_IPCC_SROCC, "spm", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "srocc", "spm", "pages"),
            "footer_height": 70,
            "header_height": 70
        },

        "SRCCL_TS": {
            "name": "SRCCL_TS",
            "input_pdf": Path(TEST_IPCC_SRCCL, "ts", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "srccl", "ts", "pages"),
            "footer_height": 70,
            "header_height": 70
        },

        "SRCCL_SPM": {
            "name": "SRCCL_SPM",
            "input_pdf": Path(TEST_IPCC_SRCCL, "spm", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "srccl", "spm", "pages"),
            "footer_height": 70,
            "header_height": 70
        },

        "SR15_TS": {
            "name": "SR15_TS",
            "input_pdf": Path(TEST_IPCC_SR15, "ts", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "sr15", "ts", "pages"),
            "footer_height": 70,
            "header_height": 70
        },

        "SR15_SPM": {
            "name": "SR15_SPM",
            "input_pdf": Path(TEST_IPCC_SR15, "spm", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "sr15", "spm", "pages"),
            "footer_height": 70,
            "header_height": 70
        },

        "WG1_TS": {
            "name": "WG1_TS",
            "input_pdf": Path(TEST_IPCC_DIR, "wg1", "ts", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "wg1", "ts", "pages"),
            "footer_height": 30,
            "header_height": 50
        },

        "WG1_SPM": {
            "name": "WG1_SPM",
            "input_pdf": Path(TEST_IPCC_DIR, "wg1", "spm", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "wg1", "spm", "pages"),
            "footer_height": 30,
            "header_height": 50
        },

        "WG2_TS": {
            "name": "WG2_TS",
            "input_pdf": Path(TEST_IPCC_DIR, "wg2", "ts", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "wg2", "ts", "pages"),
            "footer_height": 30,
            "header_height": 50,
            "left_col_left": 54,
            "right_col_left": 318.2,
        },

        "WG2_SPM": {
            "name": "WG2_SPM",
            "input_pdf": Path(TEST_IPCC_DIR, "wg2", "spm", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "wg2", "spm", "pages"),
            "footer_height": 30,
            "header_height": 50
        },

        "WG3_TS": {
            "name": "WG3_TS",
            "input_pdf": Path(TEST_IPCC_DIR, "wg3", "ts", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "wg3", "ts", "pages"),
            "footer_height": 30,
            "header_height": 50
        },

        "WG3_SPM": {
            "name": "WG3_SPM",
            "input_pdf": Path(TEST_IPCC_DIR, "wg3", "spm", "fulltext.pdf"),
            "output_page_dir": Path(TEMP_DIR, "html", "ipcc", "wg3", "spm", "pages"),
            "footer_height": 30,
            "header_height": 50
        },

    }

    def __init__(self):
        pass
