import ast
from bs4 import BeautifulSoup
from collections import Counter
import glob
import json
import logging
import nltk
import os
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

logging.debug("loading text_lib")

from py4ami.file_lib import AmiPath, FileLib

NFKD = "NFKD"

"""tags
b i em strong 
table 
fig 

"""
TAGS = {
    "\n": "",
    "</sup>": "",
    "</sub>": "",
    "</xref>": "",
}

TAG_REGEXES = {
    " +<": "<",
    "<xref[^>]*>": "@",
    " *<sup>": "^",
    " *<sub>": "_",
}

PUNCT = "!@#$%^&*+{}[]:;'|<>,.?/~`\"\\"

LIION_PROJ = os.path.abspath(os.path.normpath(os.path.join("../liion")))
PY_DIAG = "../../python/diagrams"

CCT_PROJ = os.path.abspath(os.path.normpath(
    os.path.join(PY_DIAG, "satish/cct")))

STOPWORDS_EN = nltk.corpus.stopwords.words("english")
STOPWORDS_PUB = {
    'figure', 'permission', 'reproduced', 'copyright', 'authors', 'society', "university", 'table',
    "manuscript", "published", "declare", "conflict", "research", "diagram", "images", "version",
    "data", "Fig", "different", "time", "min", "experiments", "group", "analysis",
    "study", "activity", "treated", "Extraction", "using", "mean", "work", "path",
    "samples", "performed", "analyzed", "support", "values", "approved", "significant",
    "thank", "interest", "supported",

}
OIL186 = "/Users/pm286/projects/CEVOpen/searches/oil186"  # pmr only


class ProjectCorpus:
    """manages an AMI CProject, not yet fully incorporated"""

    logger = logging.getLogger("text_lib_corpus")

    def __init__(self, cwd, tree_glob="./*/"):
        self.cwd = cwd
        self.tree_glob = tree_glob
        self.words = []

    """NEEDS REFACTORING """

    def read_analyze_child_documents(self):
        self.logger.warning("WARNING NYI FULLY")
        #        self.files = self.glob_corpus_files()
        self.files = glob.glob(os.path.join(self.cwd, self.tree_glob))
        self.logger.warning("glob", self.cwd, self.tree_glob,
                            str(len(self.files)), self.files[:5])
        for file in self.files:
            section = AmiSection()
            section.read_file_get_text_filtered_words(file)
            c = Counter(AmiSection.get_section_with_words(file).words)
        #            self.logger.warning("most common", path.split("/")[-2:-1], c.most_common(20))
        wordz = TextUtil.get_aggregate_words_from_files(self.files)
        self.logger.warning(wordz)
        cc = Counter(wordz)
        self.words = wordz
        self.logger.warning("Common", cc.most_common(50))

    def glob_corpus_files(self, glob_path, recurse=True):
        ami_path = AmiPath()
        ami_path.recurse = recurse
        files = ami_path.get_globbed_files()
        return files

    @classmethod
    def test(cls, project):
        cls.logger.warning("start test", project)
        assert (os.path.exists(project))
        project = ProjectCorpus(project)
        project.read_analyze_child_documents()
        cls.logger.warning("end test")

    @classmethod
    def test_oil(cls):
        cls.logger.warning("start test", OIL186)
        assert (os.path.exists(OIL186))
        project = ProjectCorpus(OIL186)
        project.read_analyze_child_documents()
        cls.logger.warning("end test")

    def __str__(self):
        return " ".join(map(str, self.sentences))


class Document:
    """ a standalone hierarchical document
    level of Tree or below
    may contain a subset of the conventional document"""

    def __init__(self, file="f"):
        self.sections = None
        self.file = file
        self.words = []

    #        if path is not None and os.path.isfile(path):
    #            self.words = self.get_words_from_terminal_file(path)

    def create_analyze_sections(self):
        sections_file = os.path.abspath(os.path.join(self.file, "sections"))
        if not os.path.exists(sections_file):
            if not os.path.exists("fulltext.xml"):
                logging.error("No fulltext.xml, so no sections")
            else:
                logging.error("PLEASE CREATE sections with ami sections, will add pyami later")
                jats_parser = JatsParser()
                jats_parser.create_sections_from_xml("fulltext.xml")
            return
        files = glob.glob(os.path.join(sections_file, "**/*.xml"))
        for terminal_file in files:
            # REFACTOR
            terminal_page = TextUtil.get_words_from_terminal_file(
                terminal_file)
            self.words.extend(terminal_page.get_words_from_sentences())

    # REFACTOR
    @staticmethod
    def get_words_from_file(terminal_file):
        ami_section = AmiSection()
        ami_section.read_file_get_text_filtered_words(terminal_file)
        ami_section.sentences = [Sentence(s) for s in (
            nltk.sent_tokenize(ami_section.txt))]
        ami_section.sentences = ami_section.sentences
        if os.path.exists(ami_section.txt_file):
            logging.info("skipping existing text")
        if ami_section.xml_file is not None:
            """read a path as an ami-section of larger document """
            with open(ami_section.xml_file, "r", encoding="utf-8") as f:
                ami_section.xml = f.read()
            # assumes this has been chunked to sections
            #        logging.info("t", len(self.text), self.text[:50])
            ami_section.txt = ami_section.flatten_xml_to_text(ami_section.xml)
            #        self.sentences = Sentence.merge_false_sentence_breaks(self.sentences)

            sentence_file = AmiSection.create_txt_filename_from_xml(
                ami_section.xml_file)
            if not os.path.exists(sentence_file):
                #                logging.info("wrote sentence path", sentence_file)
                AmiSection.write_numbered_sentence_file(
                    sentence_file, ami_section.sentences)
            ami_section.get_words_from_sentences()
        return ami_section.words


class AmiSection:
    """the xml sub-document with text
    Currently either <title> or <p>

≈    Will often get annotated with sentence markers
    """
    logger = logging.getLogger("ami_section")

    SECTION_LIST = None
    XML_SUFF = ".xml"
    TXT_SUFF = ".txt"

    # sections in template path
    ABSTRACT = "ABSTRACT"
    ACKNOW = "ACKNOW"
    AFFIL = "AFFIL"
    AUTHOR = "AUTHOR"
    BACKGROUND = "BACKGROUND"
    DISCUSS = "DISCUSS"
    EMPTY = "EMPTY"
    ETHICS = "ETHICS"
    FIG_CAPTION = "FIG_CAPTION"
    FRONT = "FRONT"
    INTRO = "INTRO"
    JRNL = "JRNL"
    KWD = "KEYWORD"
    METHOD = "METHOD"
    MATERIAL = "MATERIAL"
    OCTREE = "OCTREE"
    PDFIMAGE = "PDFIMAGE"
    PUB_DATE = "PUB_DATE"
    PUBLISHER = "PUBLISHER"
    REFERENCE = "REFERENCE"
    #    RESULTS     = "results_discuss"
    RESULTS = "RESULTS"
    SECTIONS = "SECTIONS"
    SVG = "SVG"
    TABLE = "TABLE"
    TITLE = "TITLE"
    WORD = "WORD"

    SECTION_LIST0 = [
        ABSTRACT,
        ACKNOW,
        AFFIL,
        AUTHOR,
        BACKGROUND,
        DISCUSS,
        EMPTY,
        ETHICS,
        FIG_CAPTION,
        FRONT,
        INTRO,
        JRNL,
        KWD,
        METHOD,
        MATERIAL,
        OCTREE,
        PDFIMAGE,
        PUB_DATE,
        PUBLISHER,
        REFERENCE,
        RESULTS,
        RESULTS,
        SECTIONS,
        SVG,
        TABLE,
        TITLE,
        WORD,
    ]

    SECTION_TEMPLATES_JSON = "section_templates.json"
    TEMPLATES = None

    def read_section_dict(file):
        """reads the dictionary of sections"""

        dictf = os.path.join(FileLib.get_py4ami(), file)
        dikt = FileLib.read_pydictionary(dictf)
        logging.info(f"dict_keys: {dikt.keys()}")
        return dikt

    templates_json = Path(FileLib.get_pyami_resources(),
                          SECTION_TEMPLATES_JSON)
    SECTION_LIST1 = read_section_dict(templates_json)
    SECTION_LIST = SECTION_LIST1
    logging.debug("text_lib: reading section_templates")
    logging.debug("SECTION LIST", SECTION_LIST1)

    logging.debug("loading templates.json")
    with open(templates_json, 'r') as json_file:
        TEMPLATES = json.load(json_file)

    def __init__(self):
        self.words = []
        self.xml_file = None
        self.xml = None
        self.txt_file = None
        self.text = None
        self.write_text = True
        self.sentences = None
        self.name = None

    #        self.read_section()

    @classmethod
    def get_section_with_words(cls, file, filter=True):
        #        document = Document(path)  # level of tree
        #        words = document.words
        section = AmiSection()
        section.read_file_get_text_filtered_words(file)
        if filter:
            section.words = TextUtil.filter_words(section.words)

        return section

    def add_name(self, file):
        """creates name (within a sections/) dirx from path
        e.g. /Users/pm286/projects/openDiagram/physchem/resources/oil26/PMC5485486/sections/0_front/1
        _article-meta/13_abstract.xml
        yields 0_front/1_article-meta/13_abstract.xml """
        if file is None:
            self.logger.warning("null path")
            return None
        file_components = file.split("/")[::-1]
        components = []
        # include name up to CTree
        for i, c in enumerate(file_components):
            # read back to "sections" and then read the CTree name
            components.append(c)
            if c == "sections":
                components.append(file_components[i + 1])
                break
        self.name = "/".join(components[::-1])

    def read_file_get_text_filtered_words(self, file):
        """reads xml or txt path
        reads path, flattens xml to text, removes stopwords and filters texts
        creates instance vars:
        self.xml_file
        self.text_file if self_write_text
        self.sentences tokenized by nltk


        returns tuple(flattened text and filtered words)
        """
        self.text = None
        if file is None:
            raise Exception("path is None")
        if file.endswith(AmiSection.XML_SUFF):
            self.xml_file = file
            self.txt_file = AmiSection.create_txt_filename_from_xml(
                self.xml_file)
            if os.path.exists(self.txt_file):
                self.add_name(self.txt_file)
                self.sentences = AmiSection.read_numbered_sentences_file(
                    self.txt_file)
            if os.path.exists(self.xml_file):
                self.add_name(self.xml_file)
                """read a path as an ami-section of larger document """
                with open(self.xml_file, "r", encoding="utf-8") as f:
                    try:
                        self.xml = f.read()
                    except Exception as ex:
                        self.logger.error("error reading: ", file, ex)
                        raise ex
                self.text = self.flatten_xml_to_text(self.xml)
                self.sentences = [Sentence(s) for s in (
                    nltk.sent_tokenize(self.text))]
                #                        self.sentences = Sentence.merge_false_sentence_breaks(self.sentences)
                if self.write_text and not os.path.exists(self.txt_file):
                    self.logger.warning("wrote sentence path", self.txt_file)
                    AmiSection.write_numbered_sentence_file(
                        self.txt_file, self.sentences)
            self.words = self.get_words_from_sentences()

    def __str__(self):

        # self.words = []
        # self.xml_file = None
        # self.xml = None
        # self.txt_file = None
        # self.text = None
        # self.write_text = True
        # self.sentences = None
        s = f"xml: {self.xml_file}\n"
        s += f"txt: {self.txt_file}"
        return self.name

    # static utilities
    @staticmethod
    def check_sections(sections):
        for section in sections:
            if section not in AmiSection.SECTION_LIST:
                print("\n===========allowed sections=========\n",
                      AmiSection.SECTION_LIST,
                      "\n====================================")
                raise Exception("unknown section: ", section)

    @staticmethod
    def create_txt_filename_from_xml(xml_file):
        sentence_file = xml_file[:-
        len(AmiSection.XML_SUFF)] + AmiSection.TXT_SUFF
        return sentence_file

    @staticmethod
    def flatten_xml_to_text(xml):
        """removes xml tags , diacritics, """
        text = TextUtil.strip_xml_tags(xml)
        text = TextUtil.remove_para_tags(text)
        text = unicodedata.normalize(NFKD, text)
        text = TextUtil.flatten_non_ascii(text)
        return text

    @classmethod
    def write_numbered_sentence_file(cls, file, sentences):
        """writes numbered sentences"""
        with open(file, "w", encoding="utf-8") as f:
            for i, sentence in enumerate(sentences):
                f.write(str(i) + Sentence.NUMBER_SPLIT +
                        sentence.string + "\n")

    @classmethod
    def read_numbered_sentences_file(cls, file):
        """ read path with lines of form line_no<sep>text where line_no starts at 0"""
        sentences = None
        if file is not None and os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) == 0:
                cls.logger.warning("warning empty path", file)
                pass
            try:
                sentences = Sentence.read_number_sentences(lines)
            except Exception as ex:
                print(ex, file, "in read numbered sentences")

        return sentences

    def get_words_from_sentences(self) -> list:
        for sentence in self.sentences:
            words = sentence.words
            self.words.extend(words)
        return self.words


class Sentence:
    NUMBER_SPLIT = ": "

    def __init__(self, string):
        self.string = string
        #        self.words = Sentence.tokenize_to_words(string)
        self.words = string.split(" ")
        self.words = Sentence.remove_punct(self.words)

    @staticmethod
    def tokenize_to_words(string):
        """ may be quite slow compared to brute splitting at spaces

        returns: list of words"""
        return nltk.word_tokenize(string)

    @staticmethod
    def remove_punct(tokens):
        """removes tokens consisting of punctuation in present `PUNCT`

        tokens: list of words
        returns: words diminished by deleted punctuation

        """
        tokens = [token for token in tokens if token not in PUNCT]
        return tokens

    @staticmethod
    def read_numbered_line(text):
        chunks = text.split(Sentence.NUMBER_SPLIT)
        if not len(chunks) > 1 or not str.isdigit(text[0]):
            raise Exception("Not a numbered sentence", text)
        return int(chunks[0]), chunks[1]

    @staticmethod
    def read_number_sentences(lines):
        """reads lines of form line_no<sep>text where line_no starts at 0"""
        sentences = []
        lasti = -1
        for i, line in enumerate(lines):
            line_no, text = Sentence.read_numbered_line(line)
            if i != lasti + 1 or i != line_no:
                raise Exception(
                    "failed to read lines in order", i, line_no, line)
            lasti = i
            sentences.append(Sentence(text))
        return sentences

    def __str__(self):
        return " ".join(map(str, self.words))


class TextUtil:
    logger = logging.getLogger("text_util")

    @staticmethod
    def strip_xml_tags(text):
        soup = BeautifulSoup(text, "xml")
        stripped_text = soup.get_text()
        return stripped_text

    @staticmethod
    def clean_line_ends(text):
        """change line ends such as \r, \r\n to \n

        """
        return re.sub[r'[\r|\n|\r\n]+', '\n', text]

    @staticmethod
    def join_xml_texts(xml_string):
        """remove all tags in XML

        replace all tags by spaces. We may later wish to exclude some names tags (e.g. <sup>)
        :param xml_string: XML in serialized form
        :returns: flattened string with spaces replacing tags
        """
        # remove tags
        untagged_text = str.join(
            " ", list(ET.fromstring(xml_string).itertext()))
        return untagged_text

    @staticmethod
    def remove_para_tags(text):
        """remove certain tags within paras lexically.
        Works on flat text

        Messy. At present tags are in TAGS and TAG_REGEXES
        """
        for key in TAGS:
            text = text.replace(key, TAGS[key])
        for regex in TAG_REGEXES:
            text = re.sub(regex, TAG_REGEXES[regex], text)
        return text

    @staticmethod
    def flatten_non_ascii(text):
        """remove diacritics and other 'non-ascii' characters

        Messy.

        """
        text = text.encode("ascii", "ignore").decode("utf-8", "ignore")
        return text

    @staticmethod
    def remove_non_alphanumeric(text, remove_digits=False):
        """
        Remove nonalphanumeric characters

        remove_digits: remove digits 0-9
        """
        pattern = r'[^A-Za-z0-9\s]' if not remove_digits else r'[A-Za-z\s]'
        text = re.sub(pattern, '', text)
        return text

    @staticmethod
    def get_aggregate_words_from_files(files):
        all_words = []
        for file in files:
            words = TextUtil.get_section_with_words(file).words
            all_words.extend(words)
        return all_words

    @staticmethod  # OBSOLETE
    def filter_words(words) -> list:
        words = [w for w in words if len(w) > 2]
        words = [w for w in words if w.lower() not in STOPWORDS_EN]
        words = [w for w in words if w.lower() not in STOPWORDS_PUB]
        words = [w for w in words if not w.isnumeric()]
        return words

    @classmethod
    def replace_chars(cls, text, unwanted_chars, replacement) -> str:
        """replaces all chars in unwanted chars with wanted_char

        :param text: source text
        :param unwanted_chars: string or list of unwanted characters
        :param replacement: replacement character
        :returns modified string
        """
        text0 = ''.join(
            [c if c not in unwanted_chars else replacement for c in text])
        return text0

    @classmethod
    def split_into_sentences(cls, text, method="Spacy") -> list:
        """ splits a paragraph into sentences

        uses nltk sent_tokenize
        :param text: para to split
        :returns: list of sentences (empty list for null or empty input)
        """
        sentences = []
        if text:
            sentences = nltk.sent_tokenize(text)
            for sent in sentences[:10]:
                cls.logger.debug(">>", sent)
        return sentences

    @classmethod
    def split_at_empty_newline(cls, text) -> list:
        """create a new section at each empty newlines

        leading newline is ignored
        trailing whitspace is trimmed

        Example:
        foo
        bar

        baz


        boodle

        will give:
        ['foo\nbar', 'baz', '', `boodle`]
        trailing newlines are consumed.
        final newline?[EOF] is consumed

        """
        # trim leading newline
        if text[0] == "\n":
            text = text[1:]
        lines = text.split('\n')
        sects = []
        sect = []
        for line in lines:
            line = line.rstrip()
            if line == '':
                sects.append(sect)
                sect = []
            else:
                sect.append(line)
        if len(sect) > 0:
            sects.append(sect)
        return sects

    @classmethod
    def test_split_at_empty_newline(cls):
        text = """
foo
bar

baz


boodle
        """
        lines = cls.split_at_empty_newline(text)
        assert (str(lines) == "[['foo', 'bar'], ['baz'], [], ['boodle']]")


class WordFilter:
    # These should really be read from path

    # false positives in organizatiom dictionary.
    ORG_STOP = {
        "basis",
        "orange",
    }

    """ filters a list of words
    generally deletes words not satisfying a condition but this may develop
    """

    def __init__(self, stopword_sets=[STOPWORDS_EN, STOPWORDS_PUB],
                 min_length=2, delete_numeric=True, delete_non_alphanum=True):

        self.min_length = min_length
        self.use_lower_stopwords = True
        self.stop_words_set = {}
        for swset in stopword_sets:
            self.stop_words_set = self.stop_words_set.union(swset)
        #            set(STOPWORDS_EN).union(STOPWORDS_PUB)
        self.delete_numeric = delete_numeric
        self.delete_non_alphanum = True
        self.regex = None
        self.keep_regex = True
        self.split_spaces = False

    def show_params(self):
        self.logger.info("min length", self.min_length,
                         "use lower", self.use_lower_stopwords,
                         "sop wrds set", self.stop_words_set,
                         "delete numeric", self.delete_numeric,
                         "delete nonalpha", self.delete_non_alphanum,
                         "regex", self.regex,
                         "keep regex", self.keep_regex,
                         "split spaces", self.split_spaces
                         )

    def filter_words(self, words):
        words = self.delete_short_words(words, self.min_length)
        words = self.delete_stop_words(words, self.stop_words)
        if self.delete_numeric:
            words = self.delete_num(words)
        if self.delete_non_alphanumeric:
            words = self.delete_non_alphanum(words)
        if self.regex is not None:
            words = self.filter_by_regex(words, self.regex, self.keep_regex)

        return words

    def set_regex(self, regex_string, keep=True):
        """ filter words by regex

        regex_string: regex to match
        keep: if True accept matching words else reject matches
        """
        self.regex = re.compile(regex_string)
        self.keep_regex = keep

    @staticmethod
    def delete_num(self, words):
        """delete words satisfying str.isnumeric() """
        words = [w for w in words if not w.isnumeric()]
        return words

    @staticmethod
    def delete_non_alphanum(self, words):
        """delete strings satisfying str.isalnum()"""
        words = [w for w in words if w.isalnum()]
        return words

    @staticmethod
    def delete_stop_words_list(self, words, stop_words_list):
        """delete words in lists of stop words"""
        for stop_words in stop_words_list:
            words = [w for w in words if w.lower() not in stop_words]
        return words

    def filter_stop_words(self, words, stop_words, keep=False):
        if keep:
            words = [w for w in words if w.lower() in stop_words]
        else:
            words = [w for w in words if w.lower() not in stop_words]
        return words

    def delete_short_words(self, words, min_length):
        """delete words less than equal to min_length"""
        words = [w for w in words if len(w) > min_length]
        return words

    def filter_by_regex(self, words, regex_string, keep=True):
        words1 = [w for w in words if re.match(regex_string)]
        return words1


class DSLParser:
    """A DomainSpecificLangauge parser for pyami commands

    currently accepts a simple nested lambda-like language similar to xpath

    Later we'll move to something like pyparsing
    https://pyparsing-docs.readthedocs.io/
    """
    STR = "STR"
    LIST = "LIST"
    NUMB = "NUMB"
    FILE = "FILE"
    # assertions
    FILE_EXISTS = "file_exists"
    GLOB_COUNT = "glob_count"
    ITEM = "item"
    LEN = "len"

    OPERATORS = {
        "concat": [STR, STR],
        "contains": [STR, STR],
        "content": [FILE],
        "count": [LIST],
        "ends_with": [STR, STR],
        "equals": [[STR, NUMB], [STR, NUMB]],
        "exists": [FILE],
        "greater_than": [[STR, NUMB], [STR, NUMB]],
        "item": [LIST, NUMB],
        "less_than": [[STR, NUMB], [STR, NUMB]],
        "length": [STR],
        "lower": [STR],
        "normalize": [STR],
        "reg_matches": [STR, STR],
        "starts_with": [STR, STR],
        "substring": [STR, NUMB, NUMB],
        "upper": [STR],

    }

    logger = logging.getLogger("dsl_parser")

    def __init__(self):
        self.tree = {}
        self.argstr = None

    def parse_and_run(self, expr):
        """

        :param expr:

        """
        self.arg_store = []
        self.current_dict = None
        self.parse_args(expr)
        self.logger.info(f"parsed: {self.arg_store}")
        return

    def parse_args(self, argstr):
        self.logger.info(f"argstr: {argstr}")
        if not argstr:
            return None, None
        args = []
        while len(argstr) > 0:
            grabbed = self.grab_next_arg(argstr)
            if not grabbed:
                self.logger.debug(f"DSL Null args")
                break
                # continue
            arg = grabbed[0]
            rest_argstr = grabbed[1]
            self.logger.info(f"               EXTRACTED {arg} "
                             f"                         ... {rest_argstr}")
            if arg is not None:
                arg = self.dequote(arg)
                self.current_dict = {}
                self.current_dict["extracted"] = arg
                self.arg_store.append(self.current_dict)
                args.append(arg)
            if not rest_argstr or len(rest_argstr) == 0:
                break
            if rest_argstr[0] != ',':
                raise ValueError(f"expected leading comma in {rest_argstr}")
            argstr = rest_argstr[1:]
        self.logger.info(f"{len(args)} ARGS: {args}")

    @classmethod
    def dequote(cls, arg):
        """remove balanced qoutes from start and end of string

        len(arg) must be > 1
        :param arg:string to dequote
        :returns: dequoted string or original if not possible
        """
        if isinstance(arg, str):
            # start/end are same character
            if len(arg) > 1 and (arg[0] == arg[-1]):
                if arg[0] == "'" or arg[0] == '"':
                    arg = arg[1:-1]
        return arg

    def grab_next_arg(self, argstr):
        # next() can be NUMB, FILE, EXPR, STR, LIST
        ch = argstr[0]
        arg = None
        if ch == '\"' or ch == "\'":  # string or possibly list
            arg, rest_args = self.grab_string(argstr)
            self.logger.debug(len(arg))
            arg = self.dequote(arg)
            self.logger.debug(
                f"argstr [{argstr}] grabbed quoted string arg: [{arg} ({len(arg)})] + rest_args [{rest_args}]")
        elif ch in ".-+0123456789":  # number
            arg, rest_args = self.grab_number(argstr)
            self.logger.debug(f"grabbed number {type(arg)} {arg}")
        else:  # expressiom
            arg, rest_args = self.grab_expr(argstr)
            self.logger.debug(f"arg: [{arg}] === rest_args: [{rest_args}]")
            funct_arg = self.get_function_and_args(arg)
            if not funct_arg:
                return None
            funct = funct_arg[0]
            funct_args = funct_arg[1]
            self.logger.debug(f"               FUNCT: [{funct}] \n"
                              f"                    ... ARGS [{funct_args}]")
            self.parse_args(funct_args)
            arg = None
        self.logger.debug(f"grabbed ||{arg}||{rest_args}||")
        return arg, rest_args

    def get_function_and_args(self, argstr):
        if not argstr:
            return None
        idx = argstr.index("(")
        funct = argstr[:idx]
        funct_args = argstr[idx + 1:-1]
        return funct, funct_args

    def grab_number(self, argstr):  # ends with comma or EOS
        idx = argstr.find(",", 1)
        if idx == -1:
            idx = len(argstr)

        arg = self.create_int_or_float(argstr[:idx])
        argstr = argstr[idx:]
        return arg, argstr

    def create_int_or_float(self, arg):
        if isinstance(arg, int):
            arg = int(arg)
        elif isinstance(arg, float):
            arg = float(arg)
        return arg

    def grab_string(self, argstr):
        quote = argstr[0]
        idx = argstr.find(quote, 1)
        if idx == -1:
            raise Exception(f"cannot parse as quoted string: {argstr}")
        arg = argstr[:idx + 1]
        argstr = argstr[idx + 1:]
        self.logger.debug(f"str {argstr}")
        return arg, argstr,

    def grab_expr(self, argstr):
        for key in self.OPERATORS:
            if argstr.startswith(key + "("):
                # idx = len(key)+1
                idx = self.get_balanced_bracket(argstr)
                arg = argstr[:idx + 1]
                rest = argstr[idx + 1:]
                self.logger.debug(f"{arg} -- {rest}")
                return arg, rest
        return None, None

    def get_balanced_bracket(self, param):

        level = 0
        found_brackets = False
        for i, c in enumerate(param):
            if c == '(':
                level += 1
                found_brackets = True
            elif c == ')':
                level -= 1
                if level < 0:
                    raise Exception(f"unexpected ) in {param}")
                if level == 0:
                    return i
        return -1

    # ============================================

    def assert_file_exists(self, file):
        """

        :param file:

        """
        if not os.path.exists(file):
            self.assert_error(f"path {file} does not exist")
        else:
            self.logger.info(f"File exists: {file}")
            pass

    def assert_glob_count(self, glob_, count):
        count = int(count)
        files = [file for file in glob.glob(glob_, recursive=True)]
        self.assert_equals(len(files), count)

    def assert_equals(self, arg1, arg2):
        if arg1 != arg2:
            raise Exception(f"{arg1} != {arg2}")

    def assert_item_in_file(self, file, idx, val):
        listx = self.read_list_from_file(file)
        if listx is None:
            raise Exception(f"cannot read list from path {file}")
        idx = int(idx)
        itemx = listx[idx]
        print(f"item {type(itemx)}")
        listxx = self.eval_string_as_list(itemx)
        self.logger.debug("type: ", type(listxx), len(listxx))
        if itemx != val:
            raise Exception(f"{itemx} != {val}")

    def assert_len(self, obj, length):
        val = int(length)
        listx = self.read_list_from_file(obj)
        if listx is not None:
            if len(listx) != val:
                ss = f"{obj} len {len(listx)} != {val}"
                self.logger.debug("ss ", ss)
                raise Exception(ss)
        elif isinstance(obj, list):
            if len(obj) != val:
                raise Exception(f"len {obj} != {val}")
        else:
            raise Exception(f"unknown type {obj}")

    def read_list_from_file(self, file):
        content = self.read_text_content(file)
        if content is None:
            raise Exception(f"{file} does not exist")
        return self.eval_string_as_list(content)

    def eval_string_as_list(self, content):
        return [n.strip() for n in ast.literal_eval(content)]

    def read_text_content(self, file):
        content = None
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
        return content

    def assert_error(self, msg):
        """

        :param msg:

        """
        self.logger.error(msg)

    @classmethod
    def test_parser1(cls):
        DSLParser().parse_and_run("length('kasbkSAD')")
        print("=================")
        DSLParser().parse_and_run("starts_with('foo bar baz','foo')")
        print("=================")
        DSLParser().parse_and_run("substring('abcdefghijklm',5,10)")
        # DSLParser().parse_and_run("starts_with('foo'),substring('abcdef',2,4),73,ends_with('bar'),'wombats',length(content('myfile'))")
        print("=================")
        # DSLParser().parse_and_run("content('myfile')")
        print("=================")
        # DSLParser().parse_and_run("substring(content('myfile'),5,77)")
        # DSLParser().parse_and_run("starts_with(item(list(content('myfile')),2),'bar')")

    @classmethod
    def run_tests(cls, dummy):
        cls.test_parser1()


class JatsParser:
    # TODO
    def __init__(self):
        raise NotImplementedError()


def main():
    import lxml
    print("started text_lib")
    #    ProjectCorpus.test(CCT_PROJ)
    #    ProjectCorpus.test(LIION_PROJ)
    #     ProjectCorpus.test_oil()
    #     TextUtil.test_split_at_empty_newline()
    #     ProjectCorpus.test_oil()
    DSLParser.test_parser1()
    print("finished text_lib")


if __name__ == "__main__":
    main()
else:
    #    main()
    pass
