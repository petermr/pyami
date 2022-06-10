
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

    def __init__(self):
        pass

