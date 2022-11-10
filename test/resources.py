"""Resources such as data used by other modules
This may develop into a dataclass"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Resources:
    RESOURCES_DIR = Path(Path(__file__).parent.parent, "py4ami", "resources")
    TEST_RESOURCES_DIR = Path(Path(__file__).parent, "resources")
    assert TEST_RESOURCES_DIR.exists(), f"dir exists {TEST_RESOURCES_DIR}"
    assert TEST_RESOURCES_DIR.is_dir(), f"file exists {TEST_RESOURCES_DIR}"
    TEMP_DIR = Path(TEST_RESOURCES_DIR.parent.parent, "temp")
    if not TEMP_DIR.exists():
        TEMP_DIR.mkdir()
    assert TEMP_DIR.is_dir(), f"file exists {TEMP_DIR}"

    # svg
    CLIMATE_10_PROJ = "climate10_proj"
    CLIMATE_10_PROJ_DIR = Path(TEST_RESOURCES_DIR, CLIMATE_10_PROJ)
    assert CLIMATE_10_PROJ_DIR.exists()
    CLIMATE_10_SVG_DIR = Path(CLIMATE_10_PROJ_DIR, "climate10", "svg")
    CLIMATE_10_HTML_TEMP_DIR = Path(CLIMATE_10_PROJ_DIR, "climate10", "html")
    TEMP_CLIMATE_10_PROJ_DIR = Path(TEMP_DIR, CLIMATE_10_PROJ)

    # ipcc and html
    IPCC_DIR = Path(TEST_RESOURCES_DIR, "ipcc")
    LOCAL_IPCC_DIR = "/Users/pm286/projects/semanticClimate/ipcc/ar6/wg3" # PMR debugging

    IPCC_CHAP02 = Path(IPCC_DIR, "Chapter02")
    assert IPCC_CHAP02.exists()
    IPCC_CHAP02_DICT = Path(IPCC_CHAP02, "dict")
    assert IPCC_CHAP02_DICT.exists()
    IPCC_CHAP02_ABB_DICT = Path(IPCC_CHAP02_DICT, "ip_3_2_emissions_abb.xml")
    assert IPCC_CHAP02_ABB_DICT.exists()
    IPCC_CHAP02_MAN_DICT = Path(IPCC_CHAP02_DICT, "ip_3_2_emissions_man.xml")
    assert IPCC_CHAP02_MAN_DICT.exists()

    IPCC_CHAP04 = Path(IPCC_DIR, "Chapter04")
    assert IPCC_CHAP04.exists()
    IPCC_CHAP06 = Path(IPCC_DIR, "Chapter06")
    assert IPCC_CHAP06.exists()

    if Path(LOCAL_IPCC_DIR).exists():
        IPCC_CHAP07 = Path(LOCAL_IPCC_DIR, "Chapter07")
        assert IPCC_CHAP07.exists()
        IPCC_CHAP07_DICT = Path(IPCC_CHAP07, "dict")
        assert IPCC_CHAP07_DICT.exists()
        IPCC_CHAP07_ABB_DICT = Path(IPCC_CHAP07_DICT, "ip_3_7_agric_abb.xml")
        # assert IPCC_CHAP07_ABB_DICT.exists()
        IPCC_CHAP07_MAN_DICT = Path(IPCC_CHAP07_DICT, "ip_3_7_agric_man.xml")
        assert IPCC_CHAP07_MAN_DICT.exists(), f"no dict {IPCC_CHAP07_MAN_DICT}"

        IPCC_CHAP08 = Path(LOCAL_IPCC_DIR, "Chapter08")
        assert IPCC_CHAP08.exists()
        IPCC_CHAP08_DICT = Path(IPCC_CHAP08, "dict")
        assert IPCC_CHAP08_DICT.exists()
        IPCC_CHAP08_ABB_DICT = Path(IPCC_CHAP08_DICT, "ip_3_8_urban_abb.xml")
        assert IPCC_CHAP08_ABB_DICT.exists()
        IPCC_CHAP08_MAN_DICT = Path(IPCC_CHAP08_DICT, "ip_3_8_urban_man.xml")
        assert IPCC_CHAP08_MAN_DICT.exists()

    # pdfs
    PDFS_DIR = Path(TEST_RESOURCES_DIR, "pdfs")
    assert PDFS_DIR.exists()
    TEMP_PDFS_DIR = Path(TEMP_DIR, "pdfs")
    if not TEMP_PDFS_DIR.exists():
        TEMP_PDFS_DIR.mkdir()

    def __init__(self):
        pass
