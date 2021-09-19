from py4ami.constants import PHYSCHEM_RESOURCES, DIAGRAMS_DIR, MINIPROJ, PROJECTS, MINICORPORA
from py4ami.util import Util
from pathlib import Path
import os
import logging
from abc import ABC, abstractmethod

class AmiProjects:
    """project files"""
    CCT = "cct"
    DIFFPROT = "diffprot"
    DISEASE = "disease"
    FFML = "ffml"
    FFML20 = "ffml20"
    LIION10 = "liion10"
    LIION4 = "liion4"
    OIL186 = "oil186"
    OIL26 = "oil26"
    OIL4 = "oil4"
    WORC_EXPLOSION = "worc_explosion"
    WORC_SYNTH = "worc_synth"

    PY4AMI = Path(__file__).parent
    RESOURCES = Path(PY4AMI, "resources")
    PROJECTS = Path(RESOURCES, "projects")
    C_LIION4 = Path(PROJECTS, "liion4")
    C_OIL4 = Path(PROJECTS, "oil4")

    # minicorpora
    C_ACTIVITY = "activity"
    C_INVASIVE = "invasive"
    C_PLANT_PART = "plantpart"
    C_HYDRODISTIL = "hydrodistil"

    logger = logging.getLogger("projects")

    def __init__(self):
        self.create_project_dict()

    def create_project_dict(self):
        self.project_dict = {}
        # in this repo
        # self.add_with_check(AmiProjects.LIION4, os.path.join(
        #     RESOURCES, "liion10"), "Li-ion batteries")
        # self.add_with_check(AmiProjects.CCT, os.path.join(
        #     DIAGRAMS_DIR, "satish", "cct"), "steel cooling curves"),
        # self.add_with_check(AmiProjects.DIFFPROT, os.path.join(DIAGRAMS_DIR, "rahul", "diffprotexp"),
        #                     "differential protein expr")

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
        self.project_dict[key] = CProject(file, desc)

class CContainer(ABC):
    logger = logging.getLogger("ccontainer")
    def __init__(self, dirx):
        self.dirx = dirx
        self.child_dirs = None
        self.child_files = None

    def is_not_reserved_child(self, file):
        """
        These are old files that should normally be removed.
        They are not the inverse of is_reserved_child (i.e. there may be be files
        which are not decided

        """
        pass

    def is_reserved_child(self, file):
        """ definitely reserved files

        file in given list OR file is dirx and starts with underscore
        """
        return file is not None and (file in self.get_reserved_child_files() \
                                     or file in self.get_reserved_child_dirs() \
                                     or self.has_reserved_syntax(file))

    def has_reserved_syntax(self, file):
        """syntax marking a reserved file

        Currently must start with "_" and be directory
        """
        return file.startswith("_") and os.path.isdir(file) or\
                file.endswith(".count.xml") or\
                file.endswith(".snippets.xml") or\
                file.endswith(".document.xml")

    @abstractmethod
    def get_reserved_child_files(self):
        pass

    @abstractmethod
    def get_reserved_child_dirs(self):
        pass

    def get_child_dirs(self):
        self.child_dirs = []
        if self.dirx is not None and os.path.exists(self.dirx):
            self.child_dirs = [str(Path(self.dirx, f)) for f in os.listdir(self.dirx) \
                               if os.path.isdir(Path(self.dirx, f))]
        return self.child_dirs

    def get_child_files(self):
        self.child_files = []
        if self.dirx is not None and os.path.exists(self.dirx):
            self.child_files = [str(Path(self.dirx, f)) for f in os.listdir(self.dirx) \
                                if not os.path.isdir(Path(self.dirx, f))]
        return self.child_files

    def __repr__(self):
        r = self.dirx
        r += f"\ndirs: {len(self.child_dirs) if self.child_dir is not None else ''}"
        r += f"\nfiles: {self.child_files}"
        return r

    def __str__(self):
        return self.__repr__()

class CProject(CContainer):
    logger = logging.getLogger("cproject")
    def __init__(self, dirx, desc=None):
        self.logger.debug("CProject ctr")
        super().__init__(dirx)
        self.description = desc
        self.ctrees = None

    def __repr__(self):
        r = super.__repr__()
        r += f"desc: {self.description}"
        return r

    def __str__(self):
        return self.__str__()

    def get_ctrees(self):
        self.get_child_dirs()
        self.ctrees = [CTree(f) for f in self.child_dirs if not self.is_reserved_child(f)]
        return self.ctrees

    RESERVED_FILES = [
        'hypertree.xml',
        'full.dataTables.html',
        'eupmc_results.json',
        'eupmc_fulltext_html_urls.txt',
        'entries.dataTables.html',
        'count.dataTables.html',
        'commonest.dataTables.html',

        #  should'nt be here
        'search.foo.count.xml',
        'search.foo.documents.xml',
        'search.foo.snippets.xml',
        'species.binomial.count.xml',
        'species.binomial.documents.xml',
        'species.binomial.snippets.xml',
        'summary.html',
        'summary.txt',
        'word.frequencies.count.xml',
        'word.frequencies.documents.xml',
        'word.frequencies.snippets.xml',
    ]

    RESERVED_DIRS = [
        'files', #rename to _files
        'target', #delete
    ]

    def get_reserved_child_files(self):
        return self.RESERVED_FILES

    def get_reserved_child_dirs(self):
        return self.RESERVED_DIRS

    @classmethod
    def tests(cls):

        CProject(AmiProjects.C_OIL4).get_ctrees()[0].print_tree()
        CProject(AmiProjects.C_LIION4).get_ctrees()[0].print_tree()

    def print_project(self):
        print(f"\ncproject {self.dirx}")
        print(f"dirs {self.get_child_dirs()}")
        print(f"files {self.get_child_files()}")
        print(f"ctrees {self.get_ctrees()}")

class CTree(CContainer):
    logger = logging.getLogger("ctree")
    def __init__(self, dirx):
        self.logger.debug("CTree ctr")
        super().__init__(dirx)

    RESERVED_FILES = [
        'eupmc_result.json',
        'fulltext.pdf',
        'fulltext.xml',
        'scholarly.html',

        # probably in wrong place
        'search.foo.count.xml',
        'search.foo.snippets.xml',
        'species.binomial.count.xml',
        'species.binomial.snippets.xml',
        'word.frequencies.count.xml',
        'word.frequencies.snippets.xml',
    ]

    RESERVED_DIRS = [
        'pdfimages',
        'results',
        'sections',
        'svg',

    ]
    def get_reserved_child_files(self):
        return self.RESERVED_FILES

    def get_reserved_child_dirs(self):
        return self.RESERVED_DIRS

    @classmethod
    def tests(cls):

        CProject(AmiProjects.C_OIL4).print_project()
        CProject(AmiProjects.C_LIION4).print_project()

    def print_tree(self):
        print(f"\ntree {self.dirx}")
        print(f"dirs {self.get_child_dirs()}")
        print(f"files {self.get_child_files()}")

def main():
    CProject.tests()

if __name__ == "__main__":
    main()