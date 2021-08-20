"""constants shared over the AMI system
"""
import logging
import os

logging.debug("loading constants.py")

HOME = os.path.expanduser("~")
PYDIAG = "../../python/diagrams"
DICT_DIR = os.path.join(HOME, "dictionary")
PROJECTS = os.path.join(HOME, "projects")

OV21_DIR = os.path.join(DICT_DIR, "openVirus20210120")
CEV_DICT_DIR = os.path.join(DICT_DIR, "cevopen")
PMR_DIR = os.path.join(DICT_DIR, "pmr")

OPEN_DIAGRAM = os.path.join(PROJECTS, "openDiagram")
OPEN_DIAGRAM_SEARCH = os.path.join(OPEN_DIAGRAM, "searches")

PHYSCHEM = os.path.join(OPEN_DIAGRAM, "physchem")
PHYSCHEM_RESOURCES = os.path.join(PHYSCHEM, "resources")
PHYSCHEM_PYTHON = os.path.join(PHYSCHEM, "python")   # where code and config lives
DIAGRAMS_DIR = os.path.join(PROJECTS, "openDiagram", "python", "diagrams")

# require CEVOpen repo

CEV_OPEN_DIR = os.path.join(PROJECTS, "CEVOpen")
CEV_OPEN_DICT_DIR = os.path.join(CEV_OPEN_DIR, "dictionary")
MINICORPORA = os.path.join(CEV_OPEN_DIR, "minicorpora")

# require dictionary repo
DICT_CEV_OPEN = os.path.join(DICT_DIR, "cevopen")
DICT_AMI3 = os.path.join(DICT_DIR, "ami3")

# require openVirus repo
OPEN_VIRUS = os.path.join(PROJECTS, "openVirus")
MINIPROJ = os.path.join(OPEN_VIRUS, "miniproject")
FUNDER = os.path.join(MINIPROJ, "funder")

# requires Worcester repo
WORCESTER_DIR = os.path.join(PROJECTS, "worcester")
