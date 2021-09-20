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
    def __init__(self, dirx: Path) -> None:
        self.dirx = dirx
        self.pathx = Path(dirx)
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

        path in given list OR path is dirx and starts with underscore
        """
        return file is not None and (file in self.get_reserved_child_files() \
                                     or file in self.get_reserved_child_dirs() \
                                     or self.has_reserved_syntax(file))

    def has_reserved_syntax(self, path):
        """syntax marking a reserved path

        Currently must start with "_" and be directory
        """
        return path.name.startswith("_") and os.path.isdir(path) or \
               path.name.endswith(".count.xml") or \
               path.name.endswith(".snippets.xml") or \
               path.name.endswith(".document.xml")

    @abstractmethod
    def get_reserved_child_files(self):
        pass

    @abstractmethod
    def get_reserved_child_dirs(self):
        pass

    @abstractmethod
    def get_name(self):
        return None if not self.dirx else self.dirx.name

    def get_descendants(self, glob_str: str) -> list:
        """get all descendants files (files and dirs) satisfying glob_str

        :glob_str: glob relative to CContainer
        """
        files = []
        if self.dirx:
            files = Path(self.dirx).glob(glob_str)
        return list(files)

    def get_children(self) -> list:
        """lust children as Paths"""
        child_paths = [] if self.dirx is None else list(Path(self.dirx).iterdir())
        self.logger.debug(f"child[0] {child_paths[0]}")
        return child_paths

    def get_child_dirs(self) -> list:
        self.child_dirs = [p for p in self.get_children() if p.is_dir()]
        self.logger.debug(f"child[0] {self.child_dirs[0]}")
        return self.child_dirs

    def get_child_files(self) -> list:
        self.child_files = [p for p in self.get_children() if p.is_file()]
        return self.child_files

    def __repr__(self):
        r = self.dirx.name
        r += f"\ndirs: {len(self.get_child_dirs()) if self.get_child_dirs() is not None else ''}"
        r += f"\nfiles: {self.get_child_files()}"
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
        self.ctree_dict = None

    def __repr__(self):
        r = super.__repr__()
        r += f"desc: {self.description}"
        return r

    def __str__(self):
        return self.__repr__()

    def get_ctrees(self):
        """get of create list of CTrees"""
        if not self.ctrees:
            self.ctrees = [CTree(f) for f in self.get_child_dirs() if not self.is_reserved_child(f)]
        return self.ctrees

    def get_ctree_dict(self):
        if not self.ctree_dict:
            self.ctree_dict = {t.get_name():t for t in self.get_ctrees()}
        return self.ctree_dict


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

    def get_name(self):
        self.name = None if not self.dirx else self.dirx.name
        return self.name

    def get_ctree(self, name: str):
        self.get_ctree_dict()
        return self.get_ctree_dict()[name]

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

    def get_name(self):
        return None if not self.dirx else self.dirx.name

    def print_tree(self):
        print(f"\ntree {self.dirx}")
        print(f"dirs {self.get_child_dirs()}")
        print(f"files {self.get_child_files()}")

    def write_filenames(self, files, filename):
        path_root = Path(self.pathx, "_files")
        path_root.mkdir(exist_ok=True)
        pp = Path(path_root, filename)
        print(f"wrote csv {pp}")
        with open(pp, "w") as p:
            for ff in files:
                #  filename relative to CTree
                l = len(str(self.pathx)+'/')
                self.logger.debug(ff, l)
                p.write(f"{str(ff)[l:]},\n")

    @classmethod
    def tests(cls):

        project = CProject(AmiProjects.C_OIL4)
        ctree = project.get_ctree('PMC4391421')
        print(f"ctree {ctree.__str__()}")
        sections = ctree.get_descendants("sections")
        print(f"sections {len(sections)}")
        cls.make_assert(ctree, "sections", "**/*.xml", 79)
        cls.make_assert(ctree, "figs", "**/*_fig.xml", 1)
        cls.make_assert(ctree, "images", "pdfimages/**/.png", 0)

        cls.make_assert(ctree, "paras", "**/*_p.xml", 15)
        ps = ctree.get_descendants("**/*_p.xml")
        ctree.write_filenames(ps, "paras.csv")
        proj_sections = project.get_descendants("sections")

        print(f"val test {CTree.Section.SECTION.value}")
        ctree.get_descendants(CTree.Section.SECTION.value)

    @classmethod
    def make_assert(cls, ctree, title, glob, l):
        ps = ctree.get_descendants(glob)
        assert len(ps) == l, f"{title} ({len(ps)}) != {l}"
        return ps


    from enum import Enum
    class Section(Enum):
        FIGURE = ("**/*_fig.xml")
        SECTION = ("**/sections/p_*.xml")
        BODY_TITLE = ("**/sections/*body/**/*_title.xml")

        def __init__(self, glob):
            self.globx = glob

        @ property
        def glob(self):
            return self.globx


def main():
    CProject.tests()
    CTree.tests()

if __name__ == "__main__":
    main()