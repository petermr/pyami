"""classes and methods to support file operations

"""
import logging
logging.debug("loading file_lib")
import os, glob, copy, json
import pathlib

# from text_lib import TextUtil



class Globber:
    """ustilities for globbing - may be obsolete"""

    def __init__(self, ami_path, recurse=True, cwd=None):
        self.ami_path = ami_path
        self.recurse = recurse
        self.cwd = os.getcwd() if cwd is None else cwd

    def get_globbed_files(self):
        """uses the glob_string_list in ami_path to create a file list"""
        files = []
        if self.ami_path:
            glob_list = self.ami_path.get_glob_string_list()
            for globb in glob_list:
                files += glob.glob(globb, recursive=self.recurse)
        return files


# section keys
_DESC = "_DESC"
PROJ =    "PROJ"
TREE =    "TREE"
SECTS =   "SECTS"
SUBSECT = "SUBSECT"
SUBSUB =  "SUBSUB"
FILE =    "FILE"
SUFFIX =  "SUFFIX"

ALLOWED_SECTS = {_DESC, PROJ, TREE, SECTS, SUBSECT, SUBSUB, FILE, SUFFIX}

# wildcards
STARS    = "**"
STAR     = "*"

# suffixes
S_PDF = "pdf"
S_PNG = "png"
S_SVG = "svg"
S_TXT = "txt"
S_XML = "xml"

# markers for processing
_NULL = "_NULL"
_REQD = "_REQD"

# known section names
SVG        = "svg"
PDFIMAGES  = "pdfimages"
RESULTS    = "results"
SECTIONS   = "sections"

# subsects
IMAGE_STAR  = "image*"

# subsects
OCTREE  = "*octree"

# results
SEARCH   = "search"
WORD     = "word"
EMPTY    = "empty"

# files
FULLTEXT_PAGE = "fulltext-page*"
CHANNEL_STAR = "channel*"
RAW = "raw"

class AmiPath:
    """holds a (keyed) scheme for generating lists of file globs
    The scheme has several segments which can be set to create a glob expr.
    """
    # keys for file scheme templates
    T_FIGURES = "fig_captions"
    T_OCTREE = "octree"
    T_PDFIMAGES = "pdfimages"
    T_RESULTS = "results"
    T_SECTIONS = "sections"
    T_SVG = "svg"

    logger = logging.getLogger("ami_path")
    # dict
    def __init__(self, scheme=None):
        self.scheme = scheme

    def print_scheme(self):
        """for debugging and enlightenment"""
        if self.scheme is not None:
            for key in self.scheme:
                print("key ",key, "=", self.scheme[key])
            print("")


    @classmethod
    def create_ami_path_from_templates(cls, key, edit_dict=None):
        """creates a new AmiPath object from selected template
        key: to template
        edit_dict: dictionary with values to edit in
        """
        key = key.lower()
        if key is None or key not in TEMPLATES:
            cls.logger.error(f"cannot find key {key}")
            cls.logger.error("no scheme for: ", key, "expected", TEMPLATES.keys())
        ami_path = AmiPath()
        # start with default template values
        ami_path.scheme = copy.deepcopy(TEMPLATES[key])
        if edit_dict:
            ami_path.edit_scheme(edit_dict)
        return ami_path

    def edit_scheme(self, edit_dict):
        """edits values in self.scheme using edit_dict"""
        for k, v in edit_dict.items():
            self.scheme[k] = v

    def permute_sets(self):
        self.scheme_list = []
        self.scheme_list.append(self.scheme)
        # if scheme has sets, expand them
        change = True
        while change:
            change = self.expand_set_lists()

    def expand_set_lists(self):
        """expands the sets in a scheme
        note: sets are held as lists in JSON

        a scheme with 2 sets of size n and m is
        expanded to n*m schemes covering all permutations
        of the set values

        self.scheme_list contains all the schemes

        returns True if any sets are expanded

        """
        change = False
        for scheme in self.scheme_list:
            for sect, value in scheme.items():
                if type(value) == list:
                    change = True
                    self.scheme_list.remove(scheme) # delete scheme with set, replace by copies
                    for set_value in value:
                        scheme_copy = copy.deepcopy(scheme)
                        self.scheme_list.append(scheme_copy)
                        scheme_copy[sect] = set_value # poke in set value
                    break # after each set processed

        return change

    def get_glob_string_list(self):
        """expand sets in AmiPath
        creates m*n... glob strings for sets with len n and m
        """
        self.permute_sets()
        self.glob_string_list = []
        for scheme in self.scheme_list:
            glob_string = AmiPath.create_glob_string(scheme)
            self.glob_string_list.append(glob_string)
        return self.glob_string_list

    @classmethod
    def create_glob_string(cls, scheme):
        glob = ""
        for sect, value in scheme.items():
            cls.logger.debug(sect, type(value), value)
            if sect not in ALLOWED_SECTS:
                cls.logger.error(f"unknown sect: {sect}")
            elif _DESC == sect:
                pass
            elif _REQD == value:
                cls.logger.error("must set ", sect)
                glob += _REQD + "/"
            elif _NULL == value:
                pass
            elif FILE == sect:
                glob += AmiPath.convert_to_glob(value)
            elif STAR in value:
                glob += AmiPath.convert_to_glob(value) + "/"
            elif SUFFIX == sect:
                glob += "." + AmiPath.convert_to_glob(value)
            else:
                glob += AmiPath.convert_to_glob(value) + "/"
        cls.logger.debug("glob", scheme, "=>", glob)
        return glob

    @classmethod
    def convert_to_glob(cls, value):
        valuex = value
        if type(value) == list:
            # tacky. string quotes and add commas and parens
            valuex = "("
            for v in value:
                valuex += v + ","
            valuex = valuex[:-1] + ")"
        return valuex

    def get_globbed_files(self):
        files = Globber(self).get_globbed_files()
        self.logger.debug("files", len(files))
        return files

class BraceGlobber:

    def braced_glob(path, recursive=False):
        from glob import glob
        from braceexpand import braceexpand
        l = [glob(x, recursive=recursive) for x in braceexpand(path)]
        return l



class FileLib:

    logger = logging.getLogger("pyami")
    @classmethod
    def force_mkdir(cls, dirx):
        """ensure dirx exists

        :dirx: directory
        """
        if not os.path.exists(dirx):
            try:
                os.mkdir(dirx)
            except Exception as e:
                cls.logger.error(f"cannot make dir {dirx} , {e}")

    @classmethod
    def force_mkparent(cls, file):
        """ensure parent directory exists

        :file: whose parent directory is to be created if absent
        """
        if file is not None:
            cls.force_mkdir(cls.get_parent_dir(file))

    @classmethod
    def force_write(cls, file, data, overwrite=True):
        """:write file, creating dirtectory if necessary
        :file: file to write to
        :data: str data to write
        :overwrite: force write iuf file exists

        may throw exception from write
        """
        import file_lib
        if file is not None:
            if os.path.exists(file) and not overwrite:
                logging.warning(f"not overwriting existsnt file {file}")
            else:
                file_lib.FileLib.force_mkparent(file)
                with open(file, "w", encoding="utf-8") as f:
                    f.write(data)

    @staticmethod
    def create_absolute_name(file):
        """create absolute name for a file"""
        absolute_file = None
        if file is not None:
            file_dir = FileLib.get_parent_dir(__file__)
            absolute_file = os.path.join(os.path.join(file_dir, file))
        return absolute_file

    @classmethod
    def get_parent_dir(cls, file):
        return None if file is None else pathlib.PurePath(file).parent

    @classmethod
    def read_pydictionary(cls, file):
        """read a json file into a python dictiomary"""
        import ast
        with open(file, "r") as f:
            pydict = ast.literal_eval(f.read())
        return pydict

    @classmethod
    def punct2underscore(cls, text):

        """ replace all ASCII punctuation except '.' , '-', '_' by '_'

        for filenames

        """
        from text_lib import TextUtil
        # this is non-trivial https://stackoverflow.com/questions/10017147/removing-a-list-of-characters-in-string

        non_file_punct = '\t \n{}!@#$%^&*()[]:;\'",|\\~+=/`'
        # [unicode(x.strip()) if x is not None else '' for x in row]

        text0 = TextUtil.replace_chars(text, non_file_punct, "_")
        return text0


    @classmethod
    def get_suffix(cls, file):
        """get suffix
        INCLUDES the "."

        """
        _suffix = None if file is None else pathlib.Path(file).suffix
        return _suffix


SECTION_TEMPLATES_JSON = 'section_templates.json'
templates_json = FileLib.create_absolute_name(SECTION_TEMPLATES_JSON)
with open(templates_json, 'r') as json_file:
    TEMPLATES = json.load(json_file)


# see https://realpython.com/python-pathlib/

def main():
    print("started file_lib")
    # test_templates()

    print("finished file_lib")


if __name__ == "__main__":
    print("running file_lib main")
    main()
else:
#    print("running file_lib main anyway")
#    main()
    pass

## examples of regex for filenames
import os
import re

def glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)

filenames = glob_re(r'.*(abc|123|a1b).*\.txt', os.listdir())

