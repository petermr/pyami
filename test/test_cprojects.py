import unittest
import logging
from pathlib import Path
# local
from py4ami.projects import CProject, CTree, AmiProjects, CProjectTests, CSubDir
from py4ami.pyamix import PyAMI
from test.resources import Resources


class TestCProjTree(unittest.TestCase):

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

    # def __init__(self, name: str, glob_str: str) -> None:
    #     super().__init__()
    #     self.name = name
    #     self.glob_str = glob_str

    # @classmethod
    # def get_glob_dict(cls):
    #     return cls.glob_dict

    @classmethod
    def tests(cls):
        project = CProject(AmiProjects.C_OIL4)
        ctree = project.get_ctree('PMC4391421')
        abstracts = ctree.get_sections(CProjectTests.ABSTRACT)
        cls.logger.debug(f"abstracts {abstracts}")

    @classmethod
    def test_section_count(cls):
        project = CProject(AmiProjects.C_OIL4)
        ctree = project.get_ctree('PMC4391421')
        cls.logger.debug(f"BACK *.xml {len(ctree.get_sections(CProjectTests.BACK_XML))}")
        cls.print_section_count(ctree)

    @classmethod
    def tests_proj(cls):
        project = CProject(AmiProjects.C_LIION4)
        for ctree in project.get_ctrees():
            print(f"------------{ctree.dirx.name}--------------")
            cls.print_section_count(ctree)

    @classmethod
    def print_section_count(cls, ctree):
        for key in CProjectTests.glob_dict:
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

    @classmethod
    def print_fig_caption(cls, project, fig_type):
        for ctree in project.get_ctrees():
            print(f"------------{ctree.dirx.name}--------------")
            ctree.create_and_write_figure_xml_sections(fig_type)

    def test_find_ctrees_climate10(self):
        """find main directories and files in climate10
        this has only one CTree
        exercises simple CProject/CTree navigation"""
        cproj = CProject(Resources.CLIMATE_10_PROJ_DIR)
        ctree_list = cproj.get_ctrees()
        assert len(ctree_list) == 1
        ctree = cproj.get_ctree("climate10")
        assert ctree is not None
        html_dir = ctree.get_existing_reserved_directory(CTree.HTML_DIR)
        assert html_dir.exists(), f"{html_dir} should exist"
        svg_dir = ctree.get_existing_reserved_directory(CTree.SVG_DIR)
        assert svg_dir.exists(), f"{svg_dir} should exist"
        pdfimages_dir = ctree.get_existing_reserved_directory(CTree.PDFIMAGES_DIR)
        assert not pdfimages_dir, f"{pdfimages_dir} shoukd not exist"

    def test_find_sub_trees(self):
        """find files in parts of CTree
        """
        cproj = CProject(Resources.CLIMATE_10_PROJ_DIR)
        svg_dir = cproj.get_ctree("climate10").get_existing_reserved_directory(CTree.SVG_DIR)
        svg_subtree = CSubDir(svg_dir)
        svg_child_files = svg_subtree.get_child_files()
        assert len(svg_child_files) == 10
        svg_child_dir = svg_subtree.get_child_dirs()
        assert len(svg_child_dir) == 0

    def test_find_sub_files_by_name(self):
        """find files in parts of CTree

        Note the escaping in the basename. This gets all files
        """
        cproj = CProject(Resources.CLIMATE_10_PROJ_DIR)
        svg_dir = cproj.get_ctree("climate10").get_existing_reserved_directory(CTree.SVG_DIR)

        svg_child_files = CSubDir(svg_dir).get_child_files_by_name("fulltext-page\.[2-5]\.svg")
        assert len(svg_child_files) == 4
