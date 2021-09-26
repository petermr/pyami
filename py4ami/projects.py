from pathlib import Path
import os
import logging
from abc import ABC, abstractmethod

from py4ami.util import Util
from py4ami.pyamix import PyAMI
from py4ami.ami_sections import AMIFigure, AMIAbsSection


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
        self.project_dict = {}
        self.create_project_dict()

    def create_project_dict(self):
        pass
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
        return file is not None and (file in self.get_reserved_child_files()
                                     or file in self.get_reserved_child_dirs()
                                     or self.has_reserved_syntax(file))

    @classmethod
    def has_reserved_syntax(cls, path):
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
    logger = logging.getLogger("proj")

    def __init__(self, dirx, desc=None):
        self.logger.debug("CProject ctr")
        super().__init__(dirx)
        self.description = desc
        self.ctrees = None
        self.ctree_dict = None
        self.name = None

    def __repr__(self):
        r = super().__repr__()
        r += f"desc: {self.description}"
        return r

    def __str__(self):
        return self.__repr__()

    def get_ctrees(self):
        """get of create list of CTrees"""
        if not self.ctrees:
            self.ctrees = [CTree(f) for f in self.get_child_dirs() if self.has_ctree_child_markers(f)]
        return self.ctrees

    def get_ctree_dict(self):
        if not self.ctree_dict:
            self.ctree_dict = {t.get_name(): t for t in self.get_ctrees()}
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
        'files',  # rename to _files
        'target',  # delete
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

    def make_jats_sections(self, force=False):
        """recursively creates and writes sections"""
        for ctree in self.get_ctrees():
            print(f"------------{ctree.dirx.name}--------------")
            ctree.make_sections(force)

    @classmethod
    def tests(cls):

        CProject(AmiProjects.C_OIL4).get_ctrees()[0].print_tree()
        CProject(AmiProjects.C_LIION4).get_ctrees()[0].print_tree()

    def print_project(self):
        print(f"\nproj {self.dirx}")
        print(f"dirs {self.get_child_dirs()}")
        print(f"files {self.get_child_files()}")
        print(f"ctrees {self.get_ctrees()}")

    @classmethod
    def has_ctree_child_markers(cls, f):
        """checks whether is existing directory and contains reserved files
        
        e.g. 
        fulltext.xml
        fulltext.pdf
        eupmc_result.json

        :f: file to check
        """
        if f is None:
            return False
        fpath = Path(f)
        if not fpath.is_dir():
            return False
        for c in [CTree.FULLTEXT_PDF, CTree.FULLTEXT_XML, CTree.EUPMC_RESULT_JSON]:
            if Path(fpath, c).exists():
                return True
        cls.logger.warning(f"failed CTree {f}")
        return False


class CTree(CContainer):
    logger = logging.getLogger("ctree")

    FULLTEXT_PDF = "fulltext.pdf"
    FULLTEXT_XML = "fulltext.xml"
    EUPMC_RESULT_JSON = 'eupmc_result.json'

    def __init__(self, dirx):
        self.logger.debug("CTree ctr")
        super().__init__(dirx)

    RESERVED_FILES = [
        EUPMC_RESULT_JSON,
        FULLTEXT_PDF,
        FULLTEXT_XML,
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
                ll = len(str(self.pathx)+'/')
                self.logger.debug(ff, ll)
                p.write(f"{str(ff)[ll:]},\n")

    def get_sections(self, section_glob: str):
        """retrieves descendant sections by indexed globs

        :section_glob: a SectionGlob by name
        :returns: a list of section filenames relative to this CTree
        """
        sections = []
        if section_glob not in CTree.CProjectTests.glob_dict:
            self.logger.warning(f"no section_glob: {section_glob} in {CTree.CProjectTests.glob_dict.keys()}")
        else:
            glob_ = CTree.CProjectTests.glob_dict[section_glob]
            print(f"glob_ {glob_}")
            self.logger.debug(f"glob {glob_}")
            sections = self.get_descendants(glob_)
        return sections

    def create_and_write_figure_xml_sections(self, fig_type):
        fig_xml_paths = self.get_sections(fig_type)
        for fig_xml_path in fig_xml_paths:
            self.print_captions_in_ctree(fig_xml_path)

    @classmethod
    def print_captions_in_ctree(cls, fig_xml_path):
        """extracts figure info based on JATS"""
        fig = AMIFigure.create_from_jats(fig_xml_path)
        print(f"{fig} \n\n")
        print(f"XML {fig.get_xml_str()}")

    def make_sections(self, force=False):
        """creates sections based on JATS"""
        self.fulltext_xml = Path(self.dirx, self.FULLTEXT_XML)
        if self.fulltext_xml.exists():
            AMIAbsSection.make_xml_sections(self.fulltext_xml, self.dirx, force)

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
        print(proj_sections)

    @classmethod
    def make_assert(cls, ctree, title, glob, ll):
        ps = ctree.get_descendants(glob)
        assert len(ps) == ll, f"{title} ({len(ps)}) != {ll}"
        return ps

    def get_fulltext_xml(self):
        self.fulltext_xml = Path(self.dirx, self.FULLTEXT_XML)
        return self.fulltext_xml

class CProjectTests:
    logger = logging.getLogger("section_glob")
    logger.setLevel(logging.INFO)
    SECTIONS = f"sections"
    FRONT = f"{SECTIONS}/*_front"
    BODY = f"{SECTIONS}/*_body"
    BACK = f"{SECTIONS}/*_back"
    FLOATS_GROUP = f"{SECTIONS}/*_floats-group"
    FIGURES_D = f"{SECTIONS}/figures"

    ARTICLE_META = f"{FRONT}/*_article-meta"
    JOURNAL_META = f"{FRONT}/*_journal-meta"

    ABSTRACT = "abstract"
    BACK_XML = "back_xml"
    BODY_XML = "body_xml"
    FIG = "figure"
    FIGURE_OLD = "figure_old"  # old-style extraction from floats
    INTRO = "intro"
    INTRO_D = f"{BODY}/*_introduction"
    JOURNAL = "journal"
    NOTE = "note"
    PARA = "para"
    PUBLISHER = "publisher"
    REF = "ref"
    REF_LIST = "ref-list"
    REF_LIST_D = f"{BACK}/*_{REF_LIST}"
    TABLE = "table"
    TABLE_D = f"{SECTIONS}/**/*_table-wrap"
    TAB_LABEL = "table_label"
    TAB_CAPTION = "table_caption"
    TAB_BODY = "table_body"
    TITLE = "title"
    XML = "xml"

    glob_dict = {
        XML: f"{SECTIONS}/**/*.xml",

        JOURNAL: f"{JOURNAL_META}/*_journal-id.xml",
        PUBLISHER: f"{JOURNAL_META}/*_publisher.xml",
        ABSTRACT: f"{ARTICLE_META}/*_abstract.xml",

        BODY_XML: f"{BODY}/**/*.xml",
        INTRO: f"{INTRO_D}/*_p.xml",
        FIG: f"{BODY}/**/*_fig.xml",
        FIGURE_OLD: f"{FIGURES_D}/figure_*.xml",
        NOTE: f"{BACK}/**/*_notes.xml",
        PARA: f"{BODY}/**/*_p.xml",
        TABLE: f"{TABLE_D}",
        TAB_LABEL: f"{TABLE_D}/*_label.xml",
        TAB_CAPTION: f"{TABLE_D}/*_caption.xml",
        TAB_BODY: f"{TABLE_D}/*_table.xml",
        TITLE: f"{BODY}/**/*_title.xml",

        BACK_XML: f"{BACK}/**/*.xml",
        REF_LIST: f"{REF_LIST_D}",
        REF: f"{REF_LIST_D}/*_ref.xml",

    }
    print("INTRO_D", INTRO_D)
    for k in glob_dict:
        print(k, "=>", glob_dict[k])

    def __init__(self, name: str, glob_str: str) -> None:
        self.name = name
        self.glob_str = glob_str

    # @classmethod
    # def get_glob_dict(cls):
    #     return cls.glob_dict

    @classmethod
    def tests(cls):
        project = CProject(AmiProjects.C_OIL4)
        ctree = project.get_ctree('PMC4391421')
        abstracts = ctree.get_sections(CTree.CProjectTests.ABSTRACT)
        cls.logger.debug(f"abstracts {abstracts}")

    @classmethod
    def test_section_count(cls):
        project = CProject(AmiProjects.C_OIL4)
        ctree = project.get_ctree('PMC4391421')
        cls.logger.debug(f"BACK *.xml {len(ctree.get_sections(CTree.CProjectTests.BACK_XML))}")
        cls.print_section_count(ctree)

    @classmethod
    def tests_proj(cls):
        project = CProject(AmiProjects.C_LIION4)
        for ctree in project.get_ctrees():
            print(f"------------{ctree.dirx.name}--------------")
            cls.print_section_count(ctree)

    @classmethod
    def print_section_count(cls, ctree):
        for key in CTree.CProjectTests.glob_dict:
            print(f"{key} => {len(ctree.get_sections(key))}")

    @classmethod
    def tests_captions_liion4(cls):
        cls.print_fig_caption(CProject(AmiProjects.C_LIION4), cls.FIG)

    @classmethod
    def tests_sections_liion4(cls):
        project = CProject(AmiProjects.C_LIION4)
        project.make_jats_sections(force=True)

    @classmethod
    def test_captions_oil186(cls):
        c_project = CProject(Path("/Users/pm286/projects/CEVOpen/searches/oil186"))
        dirx = c_project.dirx
        print(f"dirx {dirx}")
        PyAMI().run_command(f"--proj {dirx} --split xml2sect")
        cls.print_fig_caption(c_project, cls.FIGURE_OLD)

    def print_fig_caption(cls, project, fig_type):
        for ctree in project.get_ctrees():
            print(f"------------{ctree.dirx.name}--------------")
            ctree.create_and_write_figure_xml_sections(fig_type)



def main():
    # CProject.tests()
    # CTree.tests()
    # print(f"====section_glob====")
    # CTree.SectionGlob.tests()
    # print(f"====section_count====")
    # CTree.SectionGlob.test_section_count()
    # print(f"====project====")
    # CTree.SectionGlob.tests_proj()
    # print(f"====captions====")
    # CTree.CProjectTests.tests_captions_liion4()
    print(f"====sections====")
    CProjectTests.tests_sections_liion4()


if __name__ == "__main__":
    main()
