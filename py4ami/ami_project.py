import argparse
import glob
import logging
import os
import re
import textwrap
import time
import traceback
from abc import ABC, abstractmethod
from pathlib import Path

import requests
from lxml import html

from py4ami.ami_pdf import PDFArgs
from py4ami.ami_sections import AMIFigure, AMIAbsSection
from py4ami.util import Util, AbstractArgs

# local

FULLTEXT = "fulltext"


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
        return file is not None and (file in self.get_potential_reserved_child_filenames()
                                     or file in self.get_potential_reserved_child_dirnames()
                                     or self.has_reserved_syntax(file))

    @classmethod
    def has_reserved_syntax(cls, path):
        """syntax marking a reserved path

        Currently must start with "_" and be directory
        """
        return (path.name.startswith("_") and os.path.isdir(path) or
                path.name.endswith(".count.xml") or
                path.name.endswith(".snippets.xml") or
                path.name.endswith(".document.xml"))

    @abstractmethod
    def get_potential_reserved_child_filenames(self):
        pass

    @abstractmethod
    def get_potential_reserved_child_dirnames(self):
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
        """list children as Paths"""
        child_paths = [] if self.dirx is None else list(Path(self.dirx).iterdir())
        return child_paths

    def get_child_dirs(self) -> list:
        self.child_dirs = [p for p in self.get_children() if p.is_dir()]
        return self.child_dirs

    def get_child_files(self) -> list:
        self.child_files = [p for p in self.get_children() if p.is_file()]
        return self.child_files

    def get_existing_reserved_directory(self, child_name):
        """get child directory if reserved and exists
        :param child_name: name in get_potential_reserved_child_dirnames
        :return: pathname if dir exists else None
        """
        if child_name in self.get_potential_reserved_child_dirnames():
            path = Path(self.pathx, child_name)
            if path.exists():
                return path
        return None

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
        self.max_ctree_name_len = 24
        self.add_underscore = False

    def __repr__(self):
        r = super().__repr__()
        r += f"desc: {self.description}"
        return r

    def __str__(self):
        return self.__repr__()

    def get_ctrees(self):
        """get or create list of CTrees"""
        if not self.ctrees:
            self.ctrees = [CTree(f) for f in self.get_child_dirs() if self.has_ctree_child_markers(f)]
        return self.ctrees

    def get_ctree_dict(self):
        """dict of ctrees indexed by file"""
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

    def get_potential_reserved_child_filenames(self):
        return self.RESERVED_FILES

    def get_potential_reserved_child_dirnames(self):
        return self.RESERVED_DIRS

    def get_name(self):
        self.name = None if not self.dirx else self.dirx.name
        return self.name

    @classmethod
    def make_cproject_from_hrefs_in_url(cls, weburl=None, target_dir=None, suffix="pdf", maxsave=100, sleep=5,
                                        skip_exists=True):
        """Extracts href targets from a webpage/html, downloads them to given """

        page = requests.get(weburl)
        tree = html.fromstring(page.content)
        ahrefs = tree.xpath(".//a[@href]")
        urls = [ahref.attrib["href"] for ahref in ahrefs if ahref.attrib["href"].endswith(suffix)]
        for url in urls[:maxsave]:
            stem = url.split("/")[-1]
            if not target_dir.exists():
                target_dir.mkdir()
            path = Path(target_dir, stem)
            if skip_exists and path.exists():
                print(f"file exists, skipped {path}")
            else:
                content = requests.get(url).content
                with open(path, "wb") as f:
                    print(f"wrote url: {path}")
                    f.write(content)
                time.sleep(sleep)
        project = CProject(target_dir)
        return project

    @classmethod
    def make_cproject_and_fulltexts_from_hrefs_in_url(cls, weburl=None, target_dir=None, suffix="pdf", maxsave=100,
                                                      sleep=5,
                                                      keep=True, max_ctree_len=50, max_flag=20, skip_exists=True):
        cproject = CProject.make_cproject_from_hrefs_in_url(weburl=weburl, target_dir=target_dir, suffix=suffix,
                                                            maxsave=maxsave, sleep=sleep,
                                                            skip_exists=skip_exists)
        cproject.make_cproject_from_pdfs(keep=keep, max_ctree_len=max_ctree_len, max_flag=max_flag)

        cproject.pdf2htmlx()

    def make_cproject_from_pdfs(self, keep=True, files=None, max_ctree_len=24, max_flag=50):
        """makes directory for each PDF with safe names
        was 'make_project' in ami3
        for project dir with
        a.pdf
        b.pdf
        c.pdf
        makes
        a/fulltext.pdf
        b/fulltext.pdf
        c/fulltext.pdf
        If b/ and b.pdf exist, skip
        flattens punct and spaces to _, then
        truncates filename to `max_ctree_name_len`
        lowercases all filenames
        if collisions, adds _1, _2, etc to filenames
        :param keep: keep original PDFs
        :param files: explicit list of files (default is None, iterate over all PDFs)
        :param max_ctree_len: max length of filenames
        :param max_flag:maximum number of collision flags



        """
        assert Path(self.dirx).exists(), f"CProject dir should exist {self.dirx}"
        if not files:
            files = glob.glob(f"{self.dirx}/*.pdf", recursive=False)
        for file in files:
            stem = Path(file).stem
            stem_dir = CTree.flatten_filename(stem, max_len=max_ctree_len)
            ctree_dir = Path(self.dirx, stem_dir)
            if ctree_dir.exists():
                if self.add_underscore:
                    ctree_dir = self.add_underscore_extension(ctree_dir, max_flag, stem_dir)
            if not ctree_dir.exists():
                ctree_dir.mkdir()
            src_file = Path(self.dirx, file)
#            assert src_file.exists(), f"file should exist {src_file}" # problem
            dst_file = Path(ctree_dir, FULLTEXT + ".pdf")
            Util.copyanything(src_file, dst_file)

    def add_underscore_extension(self, ctree_dir, max_flag, stem_dir):
        for flag in range(1, max_flag):
            ctree_dir1 = Path(self.dirx, f"{stem_dir}_{flag}")
            if not ctree_dir1.exists():
                ctree_dir = ctree_dir1
                break
        return ctree_dir

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
        for c in CTree.get_potential_reserved_child_filenames():
            if Path(fpath, c).exists():
                return True
        for c in CTree.get_potential_reserved_child_dirnames():
            if Path(fpath, c).is_dir():
                return True
        cls.logger.warning(f"failed CTree {f}")
        return False

    def pdf2htmlx(self, maxtree=9999, maxpage=9999):
        """converts PDF to HTML
        NOTE: based on IPCC reports. Needs generalising
        """
        """ does the same as:
        python3 -m py4ami.ami_pdf --inpath ../pt195/PMC6747965/fulltext.pdf --outdir ../pt195/PMC6747965/out/ 
        """

        for i, ctree in enumerate(self.get_ctrees()):
            if i > maxtree:
                print(f"maximum number of CTress {i}")
                break
            pdf_args = PDFArgs()
            inpath = f"{Path(ctree.dirx, 'fulltext.pdf')}"
            outdir = Path(ctree.dirx, "html")
            if not outdir.exists():
                outdir.mkdir()
            outstem = "fulltext"
            fmt = "HTML"
            pdf_args.convert_write(outdir=outdir, outstem=outstem, inpath=inpath, flow=True, maxpage=maxpage)


class CTree(CContainer):
    logger = logging.getLogger("ctree")

    # child files
    FULLTEXT_PDF = "fulltext.pdf"
    FULLTEXT_XML = "fulltext.xml"
    EUPMC_RESULT_JSON = 'eupmc_result.json'
    SCHOLARLY_HTML = 'scholarly.html'
    # child dirs
    HTML_DIR = "html"
    PDFIMAGES_DIR = 'pdfimages'
    RESULTS_DIR = "results"
    SECTIONS_DIR = "sections"
    SVG_DIR = "svg"

    NON_PUNCT = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'

    def __init__(self, dirx):
        self.logger.debug("CTree ctr")
        super().__init__(dirx)
        self.fulltext_xml = None

    RESERVED_FILES = [
        EUPMC_RESULT_JSON,
        FULLTEXT_PDF,
        FULLTEXT_XML,
        SCHOLARLY_HTML,

        # probably in wrong place
        'search.foo.count.xml',
        'search.foo.snippets.xml',
        'species.binomial.count.xml',
        'species.binomial.snippets.xml',
        'word.frequencies.count.xml',
        'word.frequencies.snippets.xml',
    ]

    RESERVED_DIRS = [
        HTML_DIR,
        PDFIMAGES_DIR,
        RESULTS_DIR,
        SECTIONS_DIR,
        SVG_DIR,
    ]

    @classmethod
    def get_potential_reserved_child_filenames(cls):
        return cls.RESERVED_FILES

    @classmethod
    def get_potential_reserved_child_dirnames(cls):
        return cls.RESERVED_DIRS

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
                ll = len(str(self.pathx) + '/')
                self.logger.debug(ff, ll)
                p.write(f"{str(ff)[ll:]},\n")

    def get_sections(self, section_glob: str):
        """retrieves descendant sections by indexed globs

        :section_glob: a SectionGlob by name
        :returns: a list of section filenames relative to this CTree
        """
        sections = []
        if section_glob not in CProjectTests.glob_dict:
            self.logger.warning(f"no section_glob: {section_glob} in {CProjectTests.glob_dict.keys()}")
        else:
            glob_ = CProjectTests.glob_dict[section_glob]
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
            AMIAbsSection.make_xml_sections(self.fulltext_xml, str(self.dirx), force)

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
        print(f"proj sections {proj_sections}")

    @classmethod
    def make_assert(cls, ctree, title, glob_str, ll):
        ps = ctree.get_descendants(glob_str)
        assert len(ps) == ll, f"{title} ({len(ps)}) != {ll}"
        return ps

    def get_fulltext_xml(self):
        self.fulltext_xml = Path(self.dirx, self.FULLTEXT_XML)
        return self.fulltext_xml

    @classmethod
    def flatten_filename(cls, filename, max_len=24):
        # needs converting to comprehension
        chars = []
        for x in filename:
            if x not in CTree.NON_PUNCT:
                x = '_'
            chars.append(x)
        text = ''.join(x for x in chars)[:max_len]
        return text


class CSubDir(CContainer):
    """manages a descendant directory/subtree of a CTree
    This is less formalized than cproject and ctree and may change
    frequently.
    At the moment (2022-05) there are now "special" subtrees so code is generic
    """
    logger = logging.getLogger("subtree")

    def __init__(self, dirx, desc=None):
        self.logger.debug("CProject ctr")
        super().__init__(dirx)
        self.description = desc
        self.files = None
        self.dirs = None

    def get_name(self):
        return None

    def get_potential_reserved_child_dirnames(self):
        return []

    def get_potential_reserved_child_filenames(self):
        return []

    def get_child_files_by_name(self, regex=None):
        """list child files and directories, optionally filter by regex
        matching is on the basename, not the complete filename
        Note that "." is a regex metacharacter and needs escaping with \
        :param regex: regex matching basename"""
        files = self.get_child_files()
        if regex:
            p = re.compile(regex)
            files = [f for f in files if p.match(os.path.basename(f))]
        return files


class ProjectArgs(AbstractArgs):
    FILE = "file"
    FORMATS = "formats"
    KEEP = "keep"
    MAKE = "make"
    MAXLEN = "max_len"
    MAXFLAG = "max_flag"
    PROJECT = "project"

    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()

    def add_arguments(self):
        """creates adds the arguments for pyami commandline

        """
        if self.parser is None:
            self.parser = argparse.ArgumentParser()
        self.parser.description = textwrap.dedent('Convert raw files into a CProject. \n'
                                                  '----------------------------------\n' 
                                                  'Typically the CProject directory contains a list of files' 
                                                  '(e.g. *.pdf) and converts them into CTrees with the filestem.\n' 
                                                  'Long filenames are truncated; punctuation and ' 
                                                  'whitespace are converted to underscores.\n' 
                                                  'Duplicates have a numbered extension (_dd)\n' 
                                                  '\nExamples:\n' 
                                                  '  * PROJECT --project foobar\n' 
                                                  '  * PROJECT --project --foobar --ctree Chapter03 Chapter09\n')
        self.parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # make_project requires --project <proj>
        self.parser.add_argument(f"--{ProjectArgs.FILE}", nargs="+",
                                 help="Use list of CTrees rather than all filestems")
        self.parser.add_argument(f"--{ProjectArgs.PROJECT}", type=str, nargs=1, help="project directory")
        self.parser.add_argument(f"--{ProjectArgs.MAKE}", action='store_true',
                                 help="make project from list of filetypes")
        self.parser.add_argument(f"--{ProjectArgs.FORMATS}", type=str, nargs='+', help="input formats", default=['PDF'])
        self.parser.add_argument(f"--{ProjectArgs.KEEP}", action='store_true', help="keep original PDFs")
        self.parser.add_argument(f"--{ProjectArgs.MAXLEN}", type=int, nargs=1, help="max length of project name",
                                 # default=self.create_arg_dict()[ProjectArgs.MAXLEN]
                                 default=80 # this includes the directory tree
                                 )

        self.parser.add_argument(f"--{ProjectArgs.MAXFLAG}", type=int, nargs=1, default=20,
                                 help="max number of disambiguation flags '_")
        return self.parser

    # class ProjectArgs:
    def process_args(self):
        """runs parsed args
        :return:

        """

        if self.arg_dict:
            formats = self.arg_dict.get(ProjectArgs.FORMATS)
            project_name = self.arg_dict.get(ProjectArgs.PROJECT)
            make_project = self.arg_dict.get(ProjectArgs.MAKE)
            maxlen = self.arg_dict.get(ProjectArgs.MAXLEN)
            maxflag = self.arg_dict.get(ProjectArgs.MAXFLAG)
            keep = self.arg_dict.get(ProjectArgs.KEEP)
            files = self.arg_dict.get(ProjectArgs.FILE)

            if not project_name:
                raise ValueError("no --project given")
            project_path = Path(project_name)
            if not project_path.exists():
                raise ValueError(f"project does not exist {project_path}")
            project = CProject(project_name)
            if make_project:
                project.make_cproject_from_pdfs(files=files, max_ctree_len=maxlen, max_flag=maxflag, keep=keep)

    # class ProjectArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[ProjectArgs.FORMATS] = ['PDF']
        arg_dict[ProjectArgs.MAXLEN] = 40
        arg_dict[ProjectArgs.MAXFLAG] = 20
        return arg_dict

    @property
    def module_stem(self):
        """name of module"""
        return Path(__file__).stem


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
    logger.debug("INTRO_D", INTRO_D)
    for k in glob_dict:
        logger.debug(k, "=>", glob_dict[k])

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
    print(f"running ProjectArgs main")
    pdf_args = ProjectArgs()
    try:
        pdf_args.parse_and_process()
    except Exception as e:
        print(traceback.format_exc())
        print(f"***Cannot run pyami***; see output for errors: {e} ")

    # print(f"====sections====")
    # CProjectTests.tests_sections_liion4()


if __name__ == "__main__":
    main()
