"""constants shared over the AMI system
"""
import logging
import os

logging.debug("loading constants.py")

HOME = os.path.expanduser("~")
PYDIAG = "../../python/diagrams"
LOCAL_DICT_DIR = os.path.join(HOME, "dictionary")
LOCAL_PROJECTS = os.path.join(HOME, "projects")

LOCAL_OV21_DIR = os.path.join(LOCAL_DICT_DIR, "openVirus20210120")
LOCAL_CEV_DICT_DIR = os.path.join(LOCAL_DICT_DIR, "cevopen")
PMR_DIR = os.path.join(LOCAL_DICT_DIR, "pmr")

OPEN_DIAGRAM = os.path.join(LOCAL_PROJECTS, "openDiagram")
OPEN_DIAGRAM_SEARCH = os.path.join(OPEN_DIAGRAM, "searches")

PHYSCHEM = os.path.join(OPEN_DIAGRAM, "physchem")
PHYSCHEM_RESOURCES = os.path.join(PHYSCHEM, "resources")
PHYSCHEM_PYTHON = os.path.join(PHYSCHEM, "python")   # where code and config lives
DIAGRAMS_DIR = os.path.join(LOCAL_PROJECTS, "openDiagram", "python", "diagrams")

# require CEVOpen repo

LOCAL_CEV_OPEN_DIR = os.path.join(LOCAL_PROJECTS, "CEVOpen")
LOCAL_CEV_OPEN_DICT_DIR = os.path.join(LOCAL_CEV_OPEN_DIR, "dictionary")
LOCAL_MINICORPORA = os.path.join(LOCAL_CEV_OPEN_DIR, "minicorpora")

# require dictionary repo
LOCAL_DICT_CEV_OPEN = os.path.join(LOCAL_DICT_DIR, "cevopen")
LOCAL_DICT_AMI3 = os.path.join(LOCAL_DICT_DIR, "ami3")

# require openVirus repo
LOCAL_OPEN_VIRUS = os.path.join(LOCAL_PROJECTS, "openVirus")
LOCAL_MINIPROJ = os.path.join(LOCAL_OPEN_VIRUS, "miniproject")
LOCAL_FUNDER = os.path.join(LOCAL_MINIPROJ, "funder")

# requires Worcester repo
WORCESTER_DIR = os.path.join(LOCAL_PROJECTS, "worcester")
