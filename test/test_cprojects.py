import os
import shutil
import sys
import unittest
import logging
from pathlib import Path
import traceback
# local
from py4ami.ami_project import CProject, CTree, AmiProjects, CProjectTests, CSubDir, ProjectArgs
from py4ami.pyamix import PyAMI
from py4ami.file_lib import FileLib
from py4ami.util import Util
from test.resources import Resources
from test.test_all import AmiAnyTest

SYN_URL = "https://www.ipcc.ch/syn"
SROCC_URL = "https://www.ipcc.ch/srocc"
SRCCL_URL = "https://www.ipcc.ch/srccl"
SR1_5_URL = "https://www.ipcc.ch/sr1.5"
WG3_URL = "https://www.ipcc.ch/report/ar6/wg3/"
WG2_URL = "https://www.ipcc.ch/report/ar6/wg2/"
WG1_URL = "https://www.ipcc.ch/report/ar6/wg1/"

DOWNLOAD_IPCC_SYN_DIR = Path(AmiAnyTest.TEMP_DIR, "syn") # make projects
DOWNLOAD_IPCC_SR1_5_DIR = Path(AmiAnyTest.TEMP_DIR, "sr1_5") # make projects
DOWNLOAD_IPCC_SROCC_DIR = Path(AmiAnyTest.TEMP_DIR, "srocc") # make projects
DOWNLOAD_IPCC_SRCCL_DIR = Path(AmiAnyTest.TEMP_DIR, "srccl") # make projects
DOWNLOAD_IPCC_WG3A_DIR = Path(AmiAnyTest.TEMP_DIR, "wg3a") # make projects
DOWNLOAD_IPCC_WG2A_DIR = Path(AmiAnyTest.TEMP_DIR, "wg2a") # make projects
DOWNLOAD_IPCC_WG1A_DIR = Path(AmiAnyTest.TEMP_DIR, "wg1a") # make projects


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
    @unittest.skip("obsolete, args have changed")

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
        cproj = CProject(Resources.TEST_CLIMATE_10_PROJ_DIR)
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
        cproj = CProject(Resources.TEST_CLIMATE_10_PROJ_DIR)
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
        cproj = CProject(Resources.TEST_CLIMATE_10_PROJ_DIR)
        svg_dir = cproj.get_ctree("climate10").get_existing_reserved_directory(CTree.SVG_DIR)

        svg_child_files = CSubDir(svg_dir).get_child_files_by_name(r"fulltext-page\.[2-5]\.svg")
        assert len(svg_child_files) == 4

    def test_make_cproject_from_pdfs(self):
        """makes a CProject from pdf files
        shows the adjustment of filenames to be unique"""
        assert Resources.TEST_PDFS_DIR.exists()
        dst = AmiAnyTest.TEMP_PDFS_DIR
        src = Resources.TEST_PDFS_DIR
        cproject = CProject(AmiAnyTest.TEMP_PDFS_DIR)
        # names are short enough and uniue
        self.clean_directories(src, dst)
        cproject.make_cproject_from_pdfs()
        self.assert_exists(cproject.dirx, ['1758_2946_3_38', '1758_2946_3_44', '1758_2946_4_15'])
        self.clean_directories(src, dst)
        cproject.make_cproject_from_pdfs(max_ctree_len=11)
        self.assert_exists(cproject.dirx, ['1758_2946_3', '1758_2946_4'])
        self.clean_directories(src, dst)
        cproject.make_cproject_from_pdfs(max_ctree_len=9)
        self.assert_exists(cproject.dirx, ['1758_2946', '1758_2946', '1758_2946'])

    def test_make_cproject_from_pdf_list(self):
        """makes a CProject from pdf files
        shows the adjustment of filenames to be unique"""
        assert Resources.TEST_PDFS_DIR.exists()
        dst = AmiAnyTest.TEMP_PDFS_DIR
        src = Resources.TEST_PDFS_DIR
        self.clean_directories(src, dst)
        cproject = CProject(AmiAnyTest.TEMP_PDFS_DIR)
        # names are short enough and uniue
        self.clean_directories(src, dst)
        filesx = [
            '1758-2946-3-38.pdf',
            '1758-2946-4-15.pdf'
        ]
        cproject.make_cproject_from_pdfs(files=filesx)
        self.assert_exists(cproject.dirx, ['1758_2946_3_38', '1758_2946_4_15'])
        print(f"src {src} dst {dst}")


    def test_make_cproject_from_pdf_list_cmd(self):
        """makes a CProject from pdf files commandline
        shows the adjustment of filenames to be unique"""
        assert Resources.TEST_PDFS_DIR.exists()
        dst = AmiAnyTest.TEMP_PDFS_DIR
        src = Resources.TEST_PDFS_DIR
        cproject = CProject(dirx=AmiAnyTest.TEMP_PDFS_DIR)
        self.clean_directories(None, dst)

        dirstr = str(cproject.dirx)
        print(f"dirstr: {dirstr}")
        FileLib.copy_file('1758-2946-3-38.pdf', src, dst)
        FileLib.copy_file('1758-2946-4-15.pdf', src, dst)

        PyAMI().run_command(
            ['PROJECT', '--project', dirstr, '--make', '--file', '1758-2946-3-38.pdf', '1758-2946-4-15.pdf'])
        ctree_3_38_dir = Path(AmiAnyTest.TEMP_PDFS_DIR, "1758_2946_3_38")
        assert ctree_3_38_dir.exists(), f"dir should exist {ctree_3_38_dir}"
        file_3_38 = Path(ctree_3_38_dir, 'fulltext.pdf')
        assert file_3_38.exists(), f"file should exist {file_3_38}"
        print(f"PDFS dir {AmiAnyTest.TEMP_PDFS_DIR}")

    VERY_LONG = False
    @unittest.skipUnless(DOWNLOAD_IPCC_WG3A_DIR and VERY_LONG, "VERY LONG, DOWNLOADS")
    def test_download_pdfs_from_hrefs_in_url(self):
        # Util.delete
        downloads = [
            (SR1_5_URL, DOWNLOAD_IPCC_SR1_5_DIR),
            (SRCCL_URL, DOWNLOAD_IPCC_SRCCL_DIR),
            (SROCC_URL, DOWNLOAD_IPCC_SROCC_DIR),
            (WG1_URL, DOWNLOAD_IPCC_WG1A_DIR),
            (WG2_URL, DOWNLOAD_IPCC_WG2A_DIR),
            (WG3_URL, DOWNLOAD_IPCC_WG3A_DIR),
        ]
        for web, target in downloads:
            CProject.download_hrefs_in_url(weburl=web,
                                           target_dir=target,
                                           maxsave=5,
                                           skip_exists=True)

    @unittest.skipUnless(DOWNLOAD_IPCC_WG3A_DIR, "VERY LONG, DOWNLOADS")
    def test_make_cproject_from_webpage(self):
        """
        download whole of IPCC WG3 into CProject
        I
        """
        CProject.make_cproject_and_fulltexts_from_hrefs_in_url(weburl=WG3_URL,
                                                               target_dir=DOWNLOAD_IPCC_WG3A_DIR,
                                                               skip_exists=True)



    @unittest.skip("VERY LONG")
    def test_cproject_pdf2html(self):
        sect = "wg3"
        sect = "wg2"
        wg_path = Path(AmiAnyTest.TEMP_DIR, sect)
        if not wg_path.exists():
            project = CProject.make_cproject_and_fulltexts_from_hrefs_in_url(weburl=f"https://www.ipcc.ch/report/ar6/{sect}/",
                                                 target_dir=Path(AmiAnyTest.TEMP_DIR, f"{sect}"), skip_exists=True)
        wg_project = CProject(wg_path)
        # wg3_project.pdf2htmlx(maxpage=999, maxtree=2)
        wg_project.pdf2html_in_ctrees()

    def test_main_help(self):
        sys.argv.append("--help")
        try:
            main()
        except SystemExit:
            pass


    # ================================
    @classmethod
    def clean_directories(cls, src, dst):
        """
        cleans destination directad copies new files
        if src is None, cleans dst and leaves it empty
        :param src: directory with files to copy
        :param dst: destination directory complete copy of src
        """
        if dst.exists():
            shutil.rmtree(dst)
        if src:
            FileLib.copyanything(src, dst)
        elif not dst.exists():
            os.mkdir(dst)

    @classmethod
    def assert_exists(cls, cproj_dir, file_list):
        assert cproj_dir.exists(), f"cproj {cproj_dir} should exist"
        for file in file_list:
            f = Path(cproj_dir, file)
            assert f.exists() and f.is_dir(), f"{f} should be existing dir"


def main(argv=None):
    print(f"running PDFArgs main")
    pdf_args = ProjectArgs()
    try:
        pdf_args.parse_and_process()
    except Exception as e:
        print(traceback.format_exc())
        print(f"***Cannot run pyami***; see output for errors: {e}")


if __name__ == "__main__":
    main()
else:
    pass
