from py4ami.constants import PHYSCHEM_RESOURCES, DIAGRAMS_DIR, MINIPROJ, PROJECTS, MINICORPORA
from py4ami.util import Util
import os
import logging
logging.warning("loading projects.py")


class AmiProjects:
    """project files"""
    CCT = "cct"
    DIFFPROT = "diffprot"
    DISEASE = "disease"
    FFML = "ffml"
    FFML20 = "ffml20"
    LIION10 = "liion10"
    OIL186 = "oil186"
    OIL26 = "oil26"
    WORC_EXPLOSION = "worc_explosion"
    WORC_SYNTH = "worc_synth"

    # minicorpora
    C_ACTIVITY = "activity"
    C_INVASIVE = "invasive"
    C_PLANT_PART = "plantpart"
    C_HYDRODISTIL = "hydrodistil"

    logger = logging.getLogger("ami_project")

    def __init__(self):
        self.create_project_dict()

    def create_project_dict(self):
        self.project_dict = {}
        # in this repo
        self.add_with_check(AmiProjects.LIION10, os.path.join(
            PHYSCHEM_RESOURCES, "liion10"), "Li-ion batteries")
        self.add_with_check(AmiProjects.FFML20, os.path.join(
            DIAGRAMS_DIR, "luke", "ffml20"), "forcefields + ML")
        self.add_with_check(AmiProjects.OIL26, os.path.join(
            PHYSCHEM_RESOURCES, "oil26"), "26 oil plant papers")
        # self.add_with_check(AmiProjects.CCT, os.path.join(
        #     DIAGRAMS_DIR, "satish", "cct"), "steel cooling curves"),
        # self.add_with_check(AmiProjects.DIFFPROT, os.path.join(DIAGRAMS_DIR, "rahul", "diffprotexp"),
        #                     "differential protein expr")
        # foreign resources
        self.add_with_check(AmiProjects.DISEASE, os.path.join(
            MINIPROJ, "disease", "1-part"), "disease papers")
        self.add_with_check(AmiProjects.OIL186, os.path.join(
            PROJECTS, "CEVOpen/searches/oil186"), "186 oil plant papers")
        self.add_with_check(AmiProjects.WORC_SYNTH, os.path.join(
            PROJECTS, "worcester", "synthesis"), "chemical syntheses")
        self.add_with_check(AmiProjects.WORC_EXPLOSION, os.path.join(
            PROJECTS, "worcester", "explosion"), "explosion hazards")

        # minicorpora
        self.add_with_check(AmiProjects.C_ACTIVITY, os.path.join(
            MINICORPORA, "activity"), "biomedical activities")
        self.add_with_check(AmiProjects.C_HYDRODISTIL, os.path.join(
            MINICORPORA, "hydrodistil"), "hydrodistillation")
        self.add_with_check(AmiProjects.C_INVASIVE, os.path.join(
            MINICORPORA, "invasive"), "invasive plants")
        self.add_with_check(AmiProjects.C_PLANT_PART, os.path.join(
            MINICORPORA, "plantpart"), "plant parts")

    def add_with_check(self, key, file, desc=None):
        """checks for existence and adds filename to project_dict
        key: unique name for ami_dict , default ami_dict in AmiProjects"""
        if not os.path.isdir(file):
            self.logger.error("project files not available for ", file)
            return
        Util.check_exists(file)
        if key in self.project_dict:
            raise Exception(
                str(key) + " already exists in project_dict,  must be unique")
        self.project_dict[key] = AmiProject(file, desc)


class AmiProject:
    def __init__(self, dir, desc=None):
        self.dir = dir
        self.description = desc
