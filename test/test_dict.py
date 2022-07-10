import unittest

from lxml import etree as ET
import os
import pprint
from pathlib import Path
from collections import Container

# local

from py4ami.wikimedia import WikidataSparql, WikidataPage
from py4ami.ami_dict import AmiDictionary
from py4ami.util import AbstractArgs

TEST_DIR = Path(Path(__file__).parent.parent, "test")
TEST_RESOURCE_DIR = Path(TEST_DIR, "resources")

class TestSearchDictionary:

    def test_parse_wikidata_page(self):
        qitem = "Q144362"  # azulene
        wpage = WikidataPage(qitem)
        # note "zz" has no entries
        ahref_dict = wpage.get_wikipedia_page_links(["en", "de", "zz"])
        assert ahref_dict == {'en': 'https://en.wikipedia.org/wiki/Azulene',
                              'de': 'https://de.wikipedia.org/wiki/Azulen'}

    def test_create_dictionary(self):

        words = ["limonene", "alpha-pinene", "Lantana camara"]
        description = "created from words"
        name = "test"
        dictionary = AmiDictionary.create_dictionary_from_words_and_add_wikidata(words, name, description)
        assert len(dictionary.entries) == 3

    def test_get_property_ids(self):
        """gets properties af a dictionary entry"""
        words = ["limonene"]
        dictionary = AmiDictionary.create_dictionary_from_words(words, "test", "created from words", wikilangs=["en", "de"])
        dictionary.add_wikidata_from_terms()
        pprint.pprint(ET.tostring(dictionary.root).decode("UTF-8"))
        assert len(dictionary.entries) == 1
        wikidata_page = dictionary.create_wikidata_page(dictionary.entries[0])
        property_ids = wikidata_page.get_property_ids()
        assert len(property_ids) >= 60
        assert property_ids[:10] == ['P31', 'P279', 'P361', 'P2067', 'P274', 'P233',
                                     'P2054', 'P2101', 'P2128', 'P2199']

    # @unittest.skip(reason="needs debugging")
    def test_create_dictionary_from_sparql(self):
        from py4ami.constants import PHYSCHEM_RESOURCES
        PLANT = os.path.join(PHYSCHEM_RESOURCES, "plant")
        sparql_file = os.path.join(PLANT, "plant_part_sparql.xml")
        dictionary_file = os.path.join(PLANT, "eoplant_part.xml")
        """
        <result>
            <binding name='item'>
                <uri>http://www.wikidata.org/entity/Q2923673</uri>
            </binding>
            <binding name='image'>
                <uri>http://commons.wikimedia.org/wiki/Special:FilePath/White%20Branches.jpg</uri>
            </binding>
        </result>
"""
        sparql_to_dictionary = {
            "id_name": "item",
            "sparql_name": "image",
            "dict_name": "image",
        }
        dictionary = AmiDictionary(dictionary_file)
        wikidata_sparql = WikidataSparql(dictionary)
        wikidata_sparql.update_from_sparql(sparql_file, sparql_to_dictionary)
        ff = dictionary_file[:-(len(".xml"))] + "_update" + ".xml"
        print("saving to", ff)
        dictionary.write(ff)

    def test_invasive(self):
        """
        """

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        # from shutil import copyfile

        INVASIVE_DIR = os.path.join(CEV_OPEN_DICT_DIR, "invasive_species")
        assert (os.path.exists(INVASIVE_DIR))
        dictionary_file = os.path.join(INVASIVE_DIR, "invasive_plant.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(INVASIVE_DIR, "sparql_output")
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql_*.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "image_link",
                "dict_name": "image",
            },
            "map": {
                "id_name": "item",
                "sparql_name": "taxon_range_map_image",
                "dict_name": "image",
            },
            # "taxon": {
            #     "id_name": "item",
            #     "sparql_name": "taxon",
            #     "dict_name": "synonym",
            # }
        }
        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)
        # TODO needs assert

    @unittest.skip(reason="circular import AmiDictionary")
    def test_plant_genus(cls):
        """
        """

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        # from shutil import copyfile

        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "plant_genus")
        assert (os.path.exists(DICT_DIR))
        dictionary_file = os.path.join(DICT_DIR, "plant_genus.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(DICT_DIR, "raw")
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql_test_concatenation.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "plant_genus",
                "sparql_name": "images",
                "dict_name": "image",
            },
            "map": {
                "id_name": "plant_genus",
                "sparql_name": "taxon_range_map_image",
                "dict_name": "map",
            },
            "wikipedia": {
                "id_name": "plant_genus",
                "sparql_name": "wikipedia",
                "dict_name": "wikipedia",
            },
        }
        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    @unittest.skip(reason="circular import AmiDictionary")
    def test_compound(cls):
        """
        """

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob
        # from shutil import copyfile

        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoCompound")
        assert (os.path.exists(DICT_DIR))
        dictionary_file = os.path.join(DICT_DIR, "plant_compound.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(DICT_DIR, "raw")
        SPARQL_DIR = DICT_DIR
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql_6.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "t",
                "dict_name": "image",
            },
            "chemform": {
                "id_name": "item",
                "sparql_name": "chemical_formula",
                "dict_name": "chemical_formula",
            },
            "wikipedia": {
                "id_name": "plant_genus",
                "sparql_name": "wikipedia",
                "dict_name": "wikipedia",
            },
            # "taxon": {
            #     "id_name": "item",
            #     "sparql_name": "taxon",
            #     "dict_name": "taxon",
            # }
        }

        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

    # @unittest.skip(reason="circular import AmiDictionary")
    def test_plant_part(cls):
        """
        Takes WD-SPARQL-XML output (sparql.xml) and maps to AMIDictionary (eo_plant_part.xml)

        """
        # current dictionary does not need updating

        from py4ami.constants import CEV_OPEN_DICT_DIR
        import glob

        print(f"***test_plant_part")
        DICT_DIR = os.path.join(CEV_OPEN_DICT_DIR, "eoPlantPart")
        DICT_DIR = Path(TEST_RESOURCE_DIR,  "eoPlantPart")
        assert os.path.exists(DICT_DIR), f"{DICT_DIR} should exist"
        dictionary_file = os.path.join(DICT_DIR, "eoplant_part.xml")
        assert (os.path.exists(dictionary_file))
        SPARQL_DIR = os.path.join(DICT_DIR, "raw")
        SPARQL_DIR = DICT_DIR
        assert (os.path.exists(SPARQL_DIR))
        rename_file = False

        sparql_files = glob.glob(os.path.join(SPARQL_DIR, "sparql.xml"))

        sparql_files.sort()
        sparql2amidict_dict = {
            "image": {
                "id_name": "item",
                "sparql_name": "image",
                "dict_name": "image",
            },
        }

        AmiDictionary.apply_dicts_and_sparql(dictionary_file, rename_file, sparql2amidict_dict, sparql_files)

class PDFArgs(AbstractArgs):
    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()



    def create_arg_parser(self):
        """creates adds the arguments for pyami commandline

        """
        self.parser = argparse.ArgumentParser(description='PDF parsing')
        self.parser.add_argument("--maxpage", type=int, nargs=1, help="maximum number of pages", default=10)
        self.parser.add_argument("--indir", type=str, nargs=1, help="input directory")
        self.parser.add_argument("--inpath", type=str, nargs=1, help="input file")
        self.parser.add_argument("--outdir", type=str, nargs=1, help="output directory")
        self.parser.add_argument("--outform", type=str, nargs=1, help="output format ", default="html")
        self.parser.add_argument("--flow", type=bool, nargs=1, help="create flowing HTML (heuristics)", default=True)
        self.parser.add_argument("--imagedir", type=str, nargs=1, help="output images to imagedir")
        self.parser.add_argument("--resolution", type=int, nargs=1, help="resolution of output images (if imagedir)",
                                 default=400)
        self.parser.add_argument("--template", type=str, nargs=1, help="file to parse specific type of document (NYI)")
        self.parser.add_argument("--debug", type=str, choices=DEBUG_OPTIONS, help="debug these during parsing (NYI)")
        return self.parser

    # class PDFArgs:
    def process_args(self):
        """runs parsed args
        :return:
  --maxpage MAXPAGE     maximum number of pages
  --indir INDIR         input directory
  --infile INFILE [INFILE ...]
                        input file
  --outdir OUTDIR       output directory
  --outform OUTFORM     output format
  --flow FLOW           create flowing HTML (heuristics)
  --images IMAGES       output images
  --resolution RESOLUTION
                        resolution of output images
  --template TEMPLATE   file to parse specific type of document"""

        if self.arg_dict:
            fmt = self.arg_dict.get(OUTFORM)
            print(f"fmt: {fmt}")
            maxpage = self.arg_dict.get(MAXPAGE)
            indir = self.arg_dict.get(INDIR)
            inpath = self.arg_dict.get(INPATH)
            outdir = self.arg_dict.get(OUTDIR)
            outstem = self.arg_dict.get(OUTSTEM)
            flow = self.arg_dict.get(FLOW) is not None
            if not inpath:
                print(f"input file not given")
            else:
                inpath = Path(inpath)
                if not inpath.exists():
                    raise FileNotFoundError(f"input file does not exist: ({inpath}")
                self.convert_write(maxpage=maxpage, outdir=outdir, outstem=outstem, fmt=fmt, inpath=inpath, flow=True)

    # class PDFArgs:
    @classmethod
    def convert_pdf(cls,
                    path: str,
                    fmt: str = "text",
                    codec: str = "utf-8",
                    password: str = "",
                    maxpages: int = 0,
                    caching: bool = True,
                    pagenos: Container = set(),
                    ) -> str:
        """Summary
        Parameters
        ----------
        path : str
            Path to the pdf file
        fmt : str, optional
            Format of output, must be one of: "text", "html", "xml".
            By default, "text" format is used
        codec : str, optional
            Encoding. By default "utf-8" is used
        password : str, optional
            Password
        maxpages : int, optional
            Max number of pages to convert. By default is 0, i.e. reads all pages.
        caching : bool, optional
            Caching. By default is True
        pagenos : Container[int], optional
            Provide a list with numbers of pages to convert
        Returns
        -------
        str
            Converted pdf file
        """
        """from pdfminer/pdfplumber"""
        device, interpreter, retstr = PDFArgs.create_interpreter(fmt)
        if not path:
            raise FileNotFoundError("no input file given)")
        try:
            fp = open(path, "rb")
        except FileNotFoundError as fnfe:
            raise Exception(f"No input file given {fnfe}")

        print(f"maxpages: {maxpages}")
        for page in PDFPage.get_pages(
                fp,
                pagenos,
                maxpages=maxpages,
                password=password,
                caching=caching,
                check_extractable=True,
        ):
            interpreter.process_page(page)

        text = retstr.getvalue().decode()
        fp.close()
        device.close()
        retstr.close()
        return text

    # class PDFArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[OUTFORM] = "html.flow"
        arg_dict[MAXPAGE] = 5
        arg_dict[INDIR] = None
        arg_dict[INPATH] = None
        arg_dict[OUTDIR] = None
        arg_dict[OUTSTEM] = None
        arg_dict[FLOW] = True
        return arg_dict

    @classmethod
    def create_interpreter(cls, fmt, codec: str = "UTF-8"):
        """creates a PDFPageInterpreter
        :format: "text, "xml", "html"
        :codec: default UTF-8
        :return: (device, interpreter, retstr) device must be closed after reading, retstr
        contains resultant str

        Typical use:
        device, interpreter, retstr = create_interpreter(format)

        fp = open(path, "rb")
        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)

        text = retstr.getvalue().decode()
        fp.close()
        device.close()
        retstr.close()
        return text

        TODO convert to context manager?
        """
        rsrcmgr = PDFResourceManager()
        retstr = BytesIO()
        laparams = LAParams()
        converters = {"text": TextConverter, "html": HTMLConverter, "flow.html": HTMLConverter, "xml": XMLConverter}
        converter = converters.get(fmt)
        if not converter:
            raise ValueError(f"provide format, {converters.keys()}")
        device = converter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        return device, interpreter, retstr

    # class PDFArgs:

    def convert_write(self, fmt=None, maxpage=999999, outdir=None, outstem=None, inpath=None, flow=False,
                      unwanteds=None):
        """
        create HTML (absolute or flowing) or XML
        The preferred method is to use arg_dict
        :param fmt: format html/xml/text
        :param maxpage: if 0, writes all else staops at maxpages
        :param outdir: output dir
        :param outstem: stem of output file
        :param inpath: input file
        :param flow: remove absolute position so text can flow
        """
        if self.arg_dict:
            maxp = self.arg_dict.get(MAXPAGE)
            maxpage = int(maxp) if maxp else maxpage
            outd = self.arg_dict.get(OUTDIR)
            outdir = outd if outd else outdir
            if not outdir:
                outs = self.arg_dict.get(OUTSTEM)
                outdir = outs if outs else outstem
            inp = self.arg_dict.get(INPATH)
            inpath = inp if inp else inpath
            if fm := self.arg_dict.get(OUTFORM):
                fmt = fm
            if fl := self.arg_dict.get(FLOW):
                flow = fl

            # header_offset = -50
            header_height = 90
            # page_height = 892
            # page_height_cm = 29.7
            footer_height = 90

        print(f"==============CONVERT================")
        if fmt == "html.flow":
            fmt = "html"
            flow = True
        if not inpath:
            raise ValueError(f"no input file given")
        inpath = Path(inpath)
        if not inpath.exists():
            raise FileNotFoundError(f"input file does not exist: ({inpath})")
        result = PDFArgs.convert_pdf(path=inpath, fmt=fmt, maxpages=maxpage)

        if flow:
            tree = lxml.etree.parse(StringIO(result), lxml.etree.HTMLParser())
            result_elem = tree.getroot()
            HtmlUtil.add_ids(result_elem)
            # this is slightly tacky
            PDFUtil.remove_descendant_elements_by_tag("br", result_elem)
            PDFUtil.remove_style(result_elem, [
                "position",
                # "left",
                "border",
                "writing-mode",
                "width",  # this disables flowing text
            ])
            PDFUtil.remove_empty_elements(result_elem, ["span"])
            PDFUtil.remove_empty_elements(result_elem, ["div"])
            PDFUtil.remove_lh_line_numbers(result_elem)
            PDFUtil.remove_large_fonted_elements(result_elem)
            marker_xpath = ".//div[a[@name]]"
            offset, pagesize, page_coords = PDFUtil.find_constant_coordinate_markers(result_elem, marker_xpath)
            PDFUtil.remove_headers_and_footers(result_elem, pagesize, header_height, footer_height, marker_xpath)
            PDFUtil.remove_style_attribute(result_elem, "top")
            PDFUtil.remove_style(result_elem, ["left", "height"])
            PDFUtil.remove_unwanteds(result_elem, unwanteds)
            PDFUtil.remove_newlines(result_elem)
            self.markup_parentheses(result_elem)
            print(f"ref_counter {self.ref_counter}")

            HtmlTree.make_tree(result_elem, output_dir=outd, recs_by_section=RECS_BY_SECTION)

            result = lxml.etree.tostring(result_elem).decode("UTF-8")
            fmt = "flow.html"
        if not outdir:
            indir = Path(inpath).parent
            outdir = indir
            print(f"no outdir given, taking input {indir}")
        if not outstem:
            outstem = Path(inpath).stem
        outfile = Path(outdir, f"{outstem}.{fmt}")
        print(f"outfile {outfile}")
        with open(str(outfile), "w") as f:
            f.write(result)
            print(f"wrote {f.name}")

    # class PDFArgs:
    def parse_and_process(self):
        self.create_arg_parser()
        if len(sys.argv) == 1:  # no args, print help
            self.parser.print_help()
        else:
            self.parsed_args = self.parser.parse_args(sys.argv[1:])
            self.arg_dict = self.create_arg_dict()
            self.process_args()

    def markup_parentheses(self, result_elem):
        """iterate over parenthesised fields

        """
        xpath = ".//span"
        spans = result_elem.xpath(xpath)
        for span in spans:
            # self.extract_brackets(span)
            pass

    def extract_brackets(self, span):
        """extract (...) from text, and add hyperlinks for refs, NYI
        (IPCC 2018a)
        (Roy et al. 2018)
        (UNFCCC 2016a, 2021)
        (Bertram et al. 2015; Riahi et al. 2015)
        """
        text = ''.join(span.itertext())
        par = span.getparent()
        # (FooBar& Biff 2012a)
        refregex = r"(" \
                   r"[^\(]*" \
                   r"\(" \
                   r"(" \
                   r"[A-Z][^\)]{1,50}(20\d\d|19\d\d)" \
                   r")" \
                   r"\s*" \
                   r"\)" \
                   r"(.*)" \
                   r")"

        if result := re.compile(refregex).search(text):
            # print(f"matched: {result.group(1)} {result.group(2)}, {result.group(3)} {result.groups()}")
            elem0 = lxml.etree.SubElement(par, H_SPAN)
            elem0.text = result.group(1)
            for k, v in elem0.attrib.items():
                elem0.attrib[k] = v
            idx = par.index(span)
            span.addnext(elem0)
            current = elem0
            for ref in result.group(2).split(";"):  # e.g. in (Foo and Bar, 2018; Plugh 2020)
                ref = ref.strip()
                if not self.ref_counter[ref]:
                    self.ref_counter[ref] == 0
                self.ref_counter[ref] += 1
                a = lxml.etree.SubElement(par, H_A)
                for k, v in elem0.attrib.items():
                    a.attrib[k] = v
                a.attrib[H_HREF] = "https://github.com/petermr/discussions"
                a.text = "([" + ref + "])"
                current.addnext(a)
                current = a
            elem2 = lxml.etree.SubElement(par, H_SPAN)
            for k, v in elem0.attrib.items():
                elem2.attrib[k] = v
            elem2.text = result.group(3)

            par.remove(span)

            # print(f"par {lxml.etree.tostring(par)}")


def main(argv=None):
    print(f"running PDFArgs main")
    pdf_args = AmiDictArgs()
    try:
        pdf_args.parse_and_process()
    except Exception as e:
        print(f"***Cannot run pyami***; see output for errors: {e}")


if __name__ == "__main__":
    main()
else:
    pass

def main():
    pass