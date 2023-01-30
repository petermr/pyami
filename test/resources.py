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
    * TEMP - per-test output (not in repo)
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

    # temporary data (can be deleted after tests)
    TEMP_DIR = Path(TEST_RESOURCES_DIR.parent.parent, "temp")
    TEMP_DIR.mkdir(exist_ok=True)
    assert TEMP_DIR.is_dir(), f"file exists {TEMP_DIR}"

    # svg test data
    CLIMATE_10_PROJ = "climate10_proj"
    TEST_CLIMATE_10_PROJ_DIR = Path(TEST_RESOURCES_DIR, CLIMATE_10_PROJ)
    assert TEST_CLIMATE_10_PROJ_DIR.exists()
    TEST_CLIMATE_10_SVG_DIR = Path(TEST_CLIMATE_10_PROJ_DIR, "climate10", "svg")
    TEST_CLIMATE_10_HTML_TEMP_DIR = Path(TEST_CLIMATE_10_PROJ_DIR, "climate10", "html")

    TEMP_CLIMATE_10_PROJ_DIR = Path(TEMP_DIR, CLIMATE_10_PROJ)

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
    TEMP_IPCC_CHAP06 = Path(TEMP_DIR, "ipcc_chap6")

    TEST_IPCC_CHAP08 = Path(TEST_IPCC_DIR, "Chapter08")
    assert TEST_IPCC_CHAP08.exists()
    TEST_IPCC_CHAP08_DICT = Path(TEST_IPCC_CHAP08, "dict")
    assert TEST_IPCC_CHAP08_DICT.exists()
    TEST_IPCC_CHAP08_ABB_DICT = Path(TEST_IPCC_CHAP08_DICT, "ip_3_8_urban_abb.xml")
    assert TEST_IPCC_CHAP08_ABB_DICT.exists()
    TEST_IPCC_CHAP08_MAN_DICT = Path(TEST_IPCC_CHAP08_DICT, "ip_3_8_urban_man.xml")
    assert TEST_IPCC_CHAP08_MAN_DICT.exists()

    # pdfs
    TEST_PDFS_DIR = Path(TEST_RESOURCES_DIR, "pdfs")
    assert TEST_PDFS_DIR.exists()

    TEMP_PDFS_DIR = Path(TEMP_DIR, "pdfs")
    TEMP_PDFS_DIR.mkdir(exist_ok=True)

    TEST_IPCC_WG2 = Path(TEST_IPCC_DIR, "wg2")
    TEST_IPCC_WG2_CHAP03 = Path(TEST_IPCC_WG2, "Chapter03")
    TEST_IPCC_WG2_CHAP03_PDF = Path(TEST_IPCC_WG2_CHAP03, "fulltext.pdf")
    assert TEST_IPCC_WG2_CHAP03_PDF.exists(), f"{TEST_IPCC_WG2_CHAP03_PDF} should exist"

    def __init__(self):
        pass
