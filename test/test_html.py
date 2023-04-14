"""Create, transform, markup up HTML, etc."""
import logging
import os
import pprint
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd

import lxml.etree

# local
from py4ami.ami_bib import Reference, Biblioref
from py4ami.ami_dict import AmiDictionary
from py4ami.ami_html import HTMLSearcher, HtmlTree, TargetExtractor, Target

from py4ami.ami_html import HtmlUtil, H_SPAN, CSSStyle, HtmlTidy, HtmlStyle, HtmlClass, SectionHierarchy, AmiFont
from py4ami.ami_pdf import PDFArgs
from py4ami.pyamix import PyAMI
from py4ami.util import Util
from py4ami.xml_lib import HtmlLib, XmlLib

from test.resources import Resources
from test.test_all import AmiAnyTest

PARA1 = """
<span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id2507">First, the studies are relevant to different spatial levels, ranging from macro-scale regions with globally
comprehensive coverage to national level (4.2.2.3) and subnational and company level in a few cases
(4.2.3).  It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah (Deep  Decarbonization  Pathways  Project  2015;
Roelfsema et al. 2020) and even more blah.
</span>
"""

HTML_SINGLE_REF = """<span>It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah </span>"""
HTML_COMPOUND_REF = """<span>and more blah (Deep  Decarbonization  Pathways  Project  2015; Roelfsema et al. 2020)  and even more blah</span>"""
HTML_SUBSECTION_REF = """<span>to national level (4.2.2.3) and subnational</span>"""

# chunk of HTML from pdf2html on IPCC chapter
MINI_IPCC_PATH = Path(Resources.TEST_IPCC_CHAP06, "mini.html")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)
logger.warning("*****Test logger {logger}****")

"""
see ami_html

NOTE. the use of classname, classref and similar is inconsistent. We want to have:
s1  to mean class name (classname)
.s1 to mean a reference to a classname (only used in <style> elements but involved in conversions
"""



class TestHtml(AmiAnyTest):
    """
    parsing , structuring linking in/to.form HTML
    This will evolve into an ami_html.py module
    """
    # all are skipUnless

    ADMIN = True and AmiAnyTest.ADMIN
    BUG = True and AmiAnyTest.BUG
    CMD = True and AmiAnyTest.CMD
    DEBUG = True and AmiAnyTest.DEBUG
    LONG = True and AmiAnyTest.LONG
    NET = True and AmiAnyTest.NET
    OLD = True and AmiAnyTest.OLD
    NYI = True and AmiAnyTest.NYI
    USER = True and AmiAnyTest.USER

    def setUp(self) -> None:
        self.html = """<span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id2507">First, the studies are relevant to different spatial levels, ranging from macro-scale regions with globally 
        comprehensive coverage to national level (4.2.2.3) and subnational and company level in a few cases 
        (4.2.3).  It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah (Deep  Decarbonization  Pathways  Project  2015; 
        Roelfsema et al. 2020) and even more blah. 
        </span>"""
        self.html_single_ref = """<span>It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah </span>"""
        self.html_compound_ref = """<span>and more blah (Deep  Decarbonization  Pathways  Project  2015; Roelfsema et al. 2020)  and even more blah</span>"""
        self.html_subsection_ref = """<span>to national level (4.2.2.3) and subnational</span>"""

    def test_parse(self):
        """
        tests that test reference compiles
        """
        html_span = lxml.etree.fromstring(HTML_SINGLE_REF)
        assert type(html_span) is lxml.etree._Element
        assert html_span.text == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "

        html_span = lxml.etree.fromstring(HTML_COMPOUND_REF)
        assert type(html_span) is lxml.etree._Element
        assert html_span.text == "and more blah (Deep  Decarbonization  Pathways  Project  2015; Roelfsema et al. 2020)  and even more blah"

        html_span = lxml.etree.fromstring(HTML_SUBSECTION_REF)
        assert type(html_span) is lxml.etree._Element
        assert html_span.text == "to national level (4.2.2.3) and subnational"

    def test_parse_commandline(self):
        """
        Simulate running from commandline
        """
        infile = Path(Resources.TEST_IPCC_CHAP06, "fulltext.html")
        assert infile.exists()
        outpath = Path(AmiAnyTest.TEMP_DIR, "html", 'fulltext.annot.html')
        if outpath.exists():
            os.remove(outpath)
        dictfile = Path(Resources.TEST_IPCC_CHAP06, 'abbrev_as.xml')
        assert dictfile.exists()
        args = f"HTML --inpath {infile} --outpath {outpath} --annotate --dict {dictfile} --color YELLOW"
        PyAMI().run_command(args)
        assert outpath.exists(), f"outpath {outpath} should exist"
        element = lxml.etree.parse(str(outpath))
        # crude count of success
        xpath = "//*[@href]"
        href_elems = element.xpath(xpath)
        assert len(href_elems) == 3, f"expected 3 hrefs, found {len(href_elems)}"

    @unittest.skipIf(OLD, "use TextChunker")
    def test_find_single_brackets_in_span(self):
        """
        add docs here
        """
        html_span = lxml.etree.fromstring(HTML_SINGLE_REF)
        text = html_span.text
        rec = re.compile(Util.SINGLE_BRACKET_RE)
        match = rec.match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(
            0) == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "
        assert match.group(1) == "It  is  important  blah blah detailed  national  studies  "
        assert match.group(2) == "Bataille  et  al.  2016a"
        assert match.group(3) == "  and more blah "

    def test_find_single_biblio_ref_in_span(self):
        """
        need docs
        """
        html_span = lxml.etree.fromstring(HTML_SINGLE_REF)
        text = html_span.text
        match = Reference.SINGLE_REF_REC.match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(
            0) == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "
        assert match.group('pre') == "It  is  important  blah blah detailed  national  studies  "
        assert match.group('body') == "Bataille  et  al.  2016a"
        assert match.group('post') == "  and more blah "
        assert match.groupdict() == {
            'body': 'Bataille  et  al.  2016a',
            'post': '  and more blah ',
            'pre': 'It  is  important  blah blah detailed  national  studies  '
        }

    def test_find_single_biblio_ref_in_span_add_links(self):
        """
        need docs
        """
        html_span = lxml.etree.fromstring(HTML_SINGLE_REF)
        text = html_span.text
        match = Reference.SINGLE_REF_REC.match(text)
        assert match
        assert len(match.groups()) == 3

    def test_find_brackets_in_text(self):
        """
        read chunks of text and find brackets
        """
        chap444 = Path(Resources.TEST_IPCC_CHAP04, "4.4.html")
        chap444_elem = lxml.etree.parse(str(chap444))
        div_spans = chap444_elem.xpath(".//div[span]")
        bodylist = []
        rec = re.compile(Util.SINGLE_BRACKET_RE)
        for div in div_spans:
            for span in div.xpath("./span"):
                match = rec.match(span.text)
                if match:
                    body = match.group('body')
                    bodylist.append(body)
        assert len(bodylist) == 114

    def test_find_bracketed_multiple_bibliorefs_in_text(self):
        """
        read chunks of text and find biblioref brackets
        """
        chap444 = Path(Resources.TEST_IPCC_CHAP04, "4.4.html")
        chap444_elem = lxml.etree.parse(str(chap444))
        div_spans = chap444_elem.xpath(".//div[span]")
        total_bibliorefs = []
        rec = re.compile(Util.SINGLE_BRACKET_RE)
        for div in div_spans:
            for span in div.xpath("./span"):
                match = rec.match(span.text)
                if match:
                    body = match.group('body')
                    bibliorefs = Biblioref.create_refs_from_biblioref_string(body)
                    for biblioref in bibliorefs:
                        total_bibliorefs.append(biblioref)
        assert len(total_bibliorefs) == 103
        assert str(total_bibliorefs[0]) == 'de Coninck et al. 2018 => de Coninck| et al. |2018'
        assert str(total_bibliorefs[1]) == 'Grubb et al.  2021 => Grubb| et al.  |2021'

    def test_make_biblioref_manager(self):
        """
        read chunks of text and find biblioref brackets
        """
        chap444 = Path(Resources.TEST_IPCC_CHAP04, "4.4.html")
        bibliorefs = Biblioref.make_bibliorefs(chap444)
        counter = Counter()
        for biblioref in bibliorefs:
            ref = biblioref.first
            if ref not in counter:
                counter[ref] = 0
            counter[ref] += 1
        assert len(counter) == 86
        assert counter["IPCC"] == 6
        assert counter['Bindoff'] == 5
        assert counter['de Coninck'] == 2

    def test_exceptions_biblio_ref_in_span(self):
        """
        Need docs
        """
        assert Reference.SINGLE_REF_REC.match("Foo bar (d'Arcy & other stuff in 2008) not a ref")
        assert Reference.SINGLE_REF_REC.match("Foo bar (de Sitter and other stuff in 2008) not a ref")

    def test_not_ref_fail(self):
        assert not Reference.SINGLE_REF_REC.match("Foo bar (and other stuff in 2008) not a ref")

    def test_markup_dois_in_references_(self):
        """reads a references file and creates active hyperlinks to referenced articles"""

        ref_path = Path(Resources.TEST_IPCC_CHAP04, "references.html")
        assert ref_path.exists()
        ref_elem = lxml.etree.parse(str(ref_path))
        ref_divs = ref_elem.xpath("body/div")
        assert len(ref_divs) == 1316

        for div in ref_divs:
            ref = Reference.create_ref_from_div(div)
            ref.markup_dois_in_spans()
        path = Path(AmiAnyTest.TEMP_DIR, "ipcc_html")
        path.mkdir(exist_ok=True)
        chap4_dir = Path(path, "chapter04")
        chap4_dir.mkdir(exist_ok=True)
        outpath = Path(chap4_dir, "ref_doi.html")
        ref_elem.write(str(outpath))

    def test_make_reference_class(self):
        """reads a references file and creates class"""

        # ami_html = AmiHtml()
        ref_path = Path(Resources.TEST_IPCC_CHAP04, "references.html")
        assert ref_path.exists()
        ref_elem = lxml.etree.parse(str(ref_path))
        ref_divs = ref_elem.xpath("body/div")
        assert len(ref_divs) == 1316

        Reference.markup_dois_in_div_spans(ref_divs)

        # path = Path(AmiAnyTest.TEMP_DIR)
        # path.mkdir(exist_ok=True)
        chap4_dir = Path(AmiAnyTest.TEMP_HTML_DIR, "ipcc", "chapter04")
        chap4_dir.mkdir(exist_ok=True, parents=True)
        outpath = Path(chap4_dir, "ref_doi.html")
        ref_elem.write(str(outpath))

    def test_split_matched_string_in_span0(self):
        """split string in span into 3 using regex"""
        s = "prefix the (bracketed) string postfix"
        div_elem = lxml.etree.Element("div")
        span_elem = lxml.etree.SubElement(div_elem, "span")
        span_elem.attrib["class"] = "foo"
        span_elem.text = s
        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               "<div><span class=\"foo\">prefix the (bracketed) string postfix</span></div>"
        span = div_elem.xpath("./span")[0]
        text = span.text
        match = re.compile(Util.SINGLE_BRACKET_RE).match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(0) == "prefix the (bracketed) string postfix"
        assert match.group(1) == "prefix the "
        assert match.group(2) == "bracketed"
        assert match.group(3) == " string postfix"

        pref_span = HtmlUtil.add_sibling_after(span, H_SPAN, replace=True, copy_atts=True, text=match.group(1))
        target_span = HtmlUtil.add_sibling_after(pref_span, H_SPAN, copy_atts=True, text=match.group(2))
        post_span = HtmlUtil.add_sibling_after(target_span, H_SPAN, text=match.group(3))

        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               "<div><span class=\"foo\">prefix the </span><span class=\"foo\">bracketed</span><span> string postfix</span></div>"

    def test_split_matched_string_in_span(self):
        """split string in span into 3 using regex
        Tests: HtmlUtil.split_span_at_match"""
        div_elem = lxml.etree.fromstring("<div><span class='foo'>prefix the (bracketed) string postfix</span></div>")
        span = div_elem.xpath("./span")[0]

        regex = Util.SINGLE_BRACKET_RE
        spans, _ = HtmlUtil.split_span_at_match(span, regex)
        assert spans[0] is not None
        assert spans[1] is not None
        assert spans[2] is not None

        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               """<div><span class="re_pref">prefix the </span><span class="re_match">bracketed</span><span class="re_post"> string postfix</span></div>"""

        # no leading string
        div_elem = lxml.etree.fromstring("<div><span class='foo'>(bracketed) string postfix</span></div>")
        span = div_elem.xpath("./span")[0]
        spans, _ = HtmlUtil.split_span_at_match(span, regex)
        assert spans[0] is None
        assert spans[1] is not None
        assert spans[2] is not None

        # no trailing string
        div_elem = lxml.etree.fromstring("<div><span class='foo'>prefix the (bracketed)</span></div>")
        span = div_elem.xpath("./span")[0]
        spans, _ = HtmlUtil.split_span_at_match(span, regex)
        assert spans[0] is not None
        assert spans[1] is not None
        assert spans[2] is None

        # no leading or trailing string
        div_elem = lxml.etree.fromstring("<div><span class='foo'>(bracketed)</span></div>")
        span = div_elem.xpath("./span")[0]
        spans, _ = HtmlUtil.split_span_at_match(span, regex)
        assert spans[0] is None
        assert spans[1] is not None
        assert spans[2] is None

    def test_split_matched_string_in_span_recursively(self):
        """split string in span into 2n+1 using regex
        Tests: HtmlUtil.split_span_at_match"""
        div_elem = lxml.etree.fromstring(
            "<div><span class='foo'>prefix the (bracketed) and more (brackets) string postfix </span></div>")
        span = div_elem.xpath("./span")[0]

        regex = Util.SINGLE_BRACKET_RE
        HtmlUtil.split_span_at_match(span, regex, recurse=True)

        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               """<div><span class="re_pref">prefix the </span><span class="re_match">bracketed</span><span class="re_pref"> and more </span><span class="re_match">brackets</span><span class="re_post"> string postfix </span></div>"""

    def test_split_caption_at_bracketed_panel_refs(self):
        """split at text (a) more (b) etc
        Test recursive splitting through HtmlUtil.split_span_at_match"""
        s = f"Box 6.2 Figure 1 Retirement of coal-fired power plants to limit warming to 1.5°C and" \
            f" likely 2°C. (a) Historical facility age at retirement (b) the vintage year of existing" \
            f" units, (c) global coal capacity under different plant lifetimes, compared to capacity" \
            f" levels consistent with a well-below 2°C (green) and 1.5°C(blue) pathway assuming no new" \
            f" coal plants, and (d) and assuming plants currently under construction come online as scheduled," \
            f" but those in planning or permitting stages are not built. (Cui et al. 2019)"

        div, span = HtmlUtil.create_div_span(s, style={"font-size: 12pt; font-weight: bold"})
        assert len(div.getchildren()) == 1
        regex = Util.SINGLE_BRACKET_RE
        HtmlUtil.split_span_at_match(span, regex, recurse=True, id_root="ss", id_counter=0)
        assert len(div.getchildren()) == 14
        phrases = []

        for span in div.getchildren():
            phrases.append(span.text)
        assert phrases == ['Box 6.2 Figure 1 Retirement of coal-fired power plants to limit warming to '
                           '1.5°C and likely 2°C. ', 'a', ' Historical facility age at retirement ', 'b',
                           ' the vintage year of existing units, ', 'c',
                           ' global coal capacity under different plant lifetimes, compared to capacity '
                           'levels consistent with a well-below 2°C ', 'green', ' and 1.5°C', 'blue',
                           ' pathway assuming no new coal plants, and ', 'd',
                           ' and assuming plants currently under construction come online as scheduled, '
                           'but those in planning or permitting stages are not built. ', 'Cui et al. 2019']

    def test_add_href_annotation(self):
        """
        Add Href for annotated word
        """
        s = f"We believe the GHG emissions are huge"
        rec = re.compile(r"(.*?)(\bGHG\b)(.*)")
        match = rec.search(s)
        assert match and len(match.groups()) == 3
        assert match.group(1) == "We believe the "
        assert match.group(2) == "GHG"
        assert match.group(3) == " emissions are huge"

    def test_add_href_annotation_in_span(self):
        """Add Href for annotated word
        Tests HtmlUtil.split_span_at_match"""
        s = f"We believe the GHG emissions are huge"
        div, span = HtmlUtil.create_div_span(s, style={"font-size: 12pt; font-weight: bold"})
        regex = r"(.*?)(\bGHG\b)(.*)"
        HtmlUtil.split_span_at_match(span, regex, new_tags=["b", "a", "i"],
                                     recurse=False, id_root="ss", id_counter=0)
        assert len(div.getchildren()) == 3
        print(f"{lxml.etree.tostring(div)}")
        bb = b'<div><b style="font-size: 12; font-weight: bold;" class="re_pref"' \
             b' id="ss0">We believe the </b><a style="font-size: 12; font-weight: bold;"' \
             b' class="re_match" id="ss1">GHG</a><i style="font-size: 12; font-weight: bold;"' \
             b' class="re_post" id="ss2"> emissions are huge</i></div>'
        assert lxml.etree.tostring(div) == bb
        a_elem = div.xpath("./a")[0]
        a_elem.attrib["href"] = "https://wikidata.org/wiki/Q167336"
        test_dir = Path(AmiAnyTest.TEMP_DIR, "html")
        test_dir.mkdir(exist_ok=True)
        with open(str(Path(test_dir, "add_href.html")), "wb") as f:
            f.write(lxml.etree.tostring(div))

    def test_markup_chapter_with_dictionary_no_css(self):
        """read dictionary file and index a set of spans
        Test: ami_dict.markup_html_from_dictionary
        and add style
        and write result
        """
        dictionary_file = Path(Resources.TEST_IPCC_CHAP06, "abbrev_as.xml")
        assert dictionary_file.exists(), f"file should exist {dictionary_file}"
        ami_dict = AmiDictionary.create_from_xml_file(dictionary_file)
        ami_dict.ignorecase = False
        inpath = Path(Resources.TEST_IPCC_CHAP06, "fulltext.flow20.html")
        output_dir = Path(AmiAnyTest.TEMP_HTML_IPCC_CHAP06)
        output_dir.mkdir(exist_ok=True)
        output_path = Path(output_dir, "index.html")
        ami_dict.markup_html_from_dictionary(inpath, output_path, "pink")

    def test_markup_chapter_with_dictionary(self):
        """read dictionary file and index a set of spans
        Test: ami_dict.markup_html_from_dictionary
        and add style
        and write result]
        TODO USE THIS!
        """

        dict_path = Path(Resources.TEST_IPCC_CHAP06, "abbrev_as.xml")
        dict_path = Path(Resources.TEST_IPCC_CHAP06, "ipcc_ch6_rake.xml")
        ami_dict = AmiDictionary.create_from_xml_file(dict_path, ignorecase=False)
        input_path = Path(Resources.TEST_IPCC_CHAP06, "fulltext.flow.html")
        print(f"reading pdf_html {input_path}")
        html_output_dir = Path(AmiAnyTest.TEMP_HTML_IPCC_CHAP06)
        print(f"output html {html_output_dir}")
        chap6_marked_path = Path(html_output_dir, "raked.html")

        ami_dict.markup_html_from_dictionary(input_path, chap6_marked_path, "pink")
        assert chap6_marked_path.exists(), f"marked-up html in {chap6_marked_path}"
        with open(chap6_marked_path, "rb") as f:
            marked_elem = lxml.etree.parse(f)

    def test_extract_styles_as_css(self):
        """read dictionary file and index a set of spans
        Test: ami_dict.markup_html_from_dictionary
        and add style
        and write result
        USEFUL
        """
        target_path = Path(Resources.TEST_IPCC_CHAP06, "fulltext.flow20.html")
        output_dir = Path(AmiAnyTest.TEMP_HTML_IPCC_CHAP06)
        output_dir.mkdir(exist_ok=True)
        output_path = Path(output_dir, "styled.html")

        with open(target_path, "rb") as f:
            elem = lxml.etree.parse(f)
        styles = elem.xpath(".//@style")
        assert 200 >= len(styles) >= 100
        style_set = set()
        for style in styles:
            style_set.add(style)

        assert 10 >= len(style_set) >= 8

        sorted_styles = sorted(style_set)
        # assert sorted_styles == ['',
        #                          'font-family: ArialMT; font-size: 10px;',
        #                          'font-family: Calibri-Bold; font-size: 10px;',
        #                          'font-family: Calibri-Bold; font-size: 12px;',
        #                          'font-family: Calibri-Bold; font-size: 13px;',
        #                          'font-family: Calibri; font-size: 10px;',
        #                          'font-family: TimesNewRomanPS-BoldMT; font-size: 11px;',
        #                          'font-family: TimesNewRomanPS-BoldMT; font-size: 14px;',
        #                          'font-family: TimesNewRomanPS-BoldMT; font-size: 15px;',
        #                          'font-family: TimesNewRomanPS-BoldMT; font-size: 6px;',
        #                          'font-family: TimesNewRomanPS-BoldMT; font-size: 9px;',
        #                          'font-family: TimesNewRomanPS-ItalicMT; font-size: 11px;',
        #                          'font-family: TimesNewRomanPSMT; font-size: 11px;',
        #                          'font-family: TimesNewRomanPSMT; font-size: 6px;',
        #                          'font-family: TimesNewRomanPSMT; font-size: 9px;'
        #                          ]
        css_classes = dict()
        for style in sorted_styles:

            style_s = str(style)
            css_style = CSSStyle.create_css_style_from_css_string(style_s)
            if css_style:
                css_style.extract_bold_italic_from_font_family()

    def test_join_spans(self):
        """join sibling spans with the same styles
        IMPORTANT
        """
        html_path = Path(Resources.TEST_IPCC_CHAP04, "fulltext.flow20.html")
        html_element = lxml.etree.parse(str(html_path))
        divs = html_element.xpath(".//div")
        assert 400 <= len(divs)
        last_div = None
        last_style = None
        for div in divs:
            spans = div.xpath("./span")
            print(f"spans {len(spans)}")
            for span in spans:
                style = CSSStyle.create_css_style_from_attribute_of_body_element(span)
                print(f"{style}")
                if style == last_style:
                    print(f"styles match")
                last_span = span
                last_style = style

    @unittest.skipUnless(USER, "claim paras")
    @unittest.skipIf(BUG and False, "bad input file")
    def test_make_ipcc_obsidian_md_CURRENT(self):
        """
        Read IPCC exec_summary Chapter and make obsidian MD.
        Reads an executive.summary consisting of about 20 paras, each of which
        has a bold first sentence (main claim).
        Tries to split this into the main claim and subclaims.

        writes 1 file per paragraph into B_1.md, B_2.md, etc.

<body>
<p class="p1"><span class="s1"><b>Executive Summary</b></span></p>
<p class="p2"><span class="s1"><b>Global net anthropogenic Greenhouse Gas (GHG) emissions during the last decade (2010-2019) were higher than at any previous time in human history </b><i>(high confidence)</i>. Since 2010, GHG emissions have continued to grow reaching 59±6.6 GtCO<sub>2</sub>eq in 2019<sup>1</sup>, but the average annual growth in the last decade (1.3%, 2010-2019) was lower than in the previous decade (2.1%, 2000-2009) (<i>high confidence</i>). Average annual GHG emissions were 56 GtCO<sub>2</sub>eqyr<sup>-1</sup> for the decade 2010-2019 growing by about 9.1 GtCO<sub>2</sub>eqyr<sup>-1</sup> from the previous decade (2000-2009) – the highest decadal average on record (<i>high confidence</i>). {2.2.2, Table 2.1, Figure 2.5}</span></p>
<p class="p2"><span class="s1"><b>Emissions growth has varied, but persisted across all groups of greenhouse gases </b><i>(high confidence)</i>. The average annual emission levels of the last decade (2010-2019) were higher than in any previous decade for each group of greenhouse gases (<i>high confidence</i>). In 2019, CO<sub>2</sub> emissions were 45±5.5 GtCO<sub>2</sub>,<sub>2</sub> CH<sub>4</sub> 11±3.2 GtCO<sub>2</sub>eq, N<sub>2</sub>O 2.7±1.6 GtCO<sub>2</sub>eq and fluorinated gases (F-gases: HFCs, PFCs, SF<sub>6</sub>, NF<sub>3</sub>) 1.4±0.41 GtCO<sub>2</sub>eq. Compared to 1990, the magnitude and speed of these increases differed across gases: CO<sub>2</sub> from fossil fuel and industry (FFI) grew by 15 GtCO<sub>2</sub>eqyr<sup>-1</sup> (67%), CH<sub>4</sub> by 2.4 GtCO<sub>2</sub>eqyr<sup>-1</sup>(29%), F-gases by 0.97 GtCO<sub>2</sub>eqyr<sup>-1</sup> (250%), N<sub>2</sub>O by 0.65 GtCO<sub>2</sub>eqyr<sup>-1</sup> (33%). CO<sub>2</sub> emissions from net land use, land-use change and forestry (LULUCF) have shown little long-term change, with large uncertainties preventing the detection of statistically significant trends. F-gases excluded from GHG emissions inventories such as <i>chlorofluorocarbons</i> and <i>hydrochlorofluorocarbons</i> are about the same size as those included (<i>high confidence</i>). {2.2.1, 2.2.2, Table 2.1, Figure 2.2, Figure 2.3, Figure 2.5}</span></p>

        BUGS: furst bold sentence missed out in B_10.md and B_20.md
        Maybe full-stop after italics is bold?

        THIS USED A STYLE-NORMALISED FILE WHICH I THINK WAS CREARTED  BY ATOM.
        THE FILE MAY BE LOST
        BUG

        https://stackoverflow.com/questions/62472162/lxml-xpath-expression-for-selecting-all-text-under-a-given-child-node-including
        """
        in_file = Path(Resources.TEST_IPCC_CHAP02, "exec_summary.html")
        outdir = Path(AmiAnyTest.TEMP_DIR, "obsidian")
        os.makedirs(outdir, exist_ok=True)
        path = Path(in_file)
        assert path.exists(), f"{path} should exist"
        tree = lxml.etree.parse(str(path))
        ps = tree.findall(".//p")
        assert 23 <= len(ps) <= 50
        i = 0
        for p in ps:
            bs = p.xpath(".//b")
            if len(bs) > 0:
                i += 1
                for b in bs:
                    t = b.xpath('.//text()')
                    bstr = "__".join(t)
                    nonb = p.xpath(".//text()[not(ancestor::b)]")
                    tstr = "".join(nonb)
                file = Path(outdir, f"B_{i}.md")
                print(f"writing {file}")
                with open(file, "w") as f:
                    f.write(bstr)
                    f.write(tstr)

    def test_extract_ipcc_nodes_and_pointers_raw_format_NODES_CURRENT(self):
        """
        read (old style) raw html with IPCC nodes and node_pointers and convert to HTML@a elements
        example
        '(high confidence). {2.2.2, Table 2.1, Figure 2.5}' contains 3 node pointers
        """
        # html = "executive_summary_css.html"
        # html = "executive_summary1.html"
        # file = Path(Resources.TEST_IPCC_CHAP02, "maintext_old.html")
        file = Path(Resources.TEST_IPCC_DIR, "LongerReport", "fulltext.html")
        # make dictionary of regex extractor/splitters
        target_dict_from_ipcc_para_text = {
            TargetExtractor.TARGET_LIST_RE: "{([^}]+)}", # curly {...}
            TargetExtractor.TARGET_RE: "\\s*[,;]\\s*",   # semicolon/comma list ...; ...;
            TargetExtractor.TARGET_VALUE_RE: "(Table|Figure)\\s+(.*)", # (table, figure) value
        }
        print(f"text_dict {target_dict_from_ipcc_para_text}")

        node_extractor = TargetExtractor()
        HAS_CURLY = "//div[//text()[contains(., '{')]]"
        div_xp = HAS_CURLY
        paragraph_dict = node_extractor.extract_anchor_paragraphs(div_xp, file, target_dict_from_ipcc_para_text)
        print(f"paragraph_dict {paragraph_dict.keys()}")
        PACKAGE = 'package'
        SECTION = 'section'
        SUBPACKAGE = 'subpackage'

        node_re = re.compile(
            f"(?P<{PACKAGE}>"
              "(?:"
                "(?:WG\s*(?:1|2|3|I|II|III)|SROCC|SRCCL|SR1\.5"
                ")?"
              ")"
            ")"
            "\s*"
                             
             f"(?P<{SUBPACKAGE}>"
             "(?:(?:Table|Figure|Box|SPM|TS|Chapter|Sections?|CCB|"
             "Cross-Chapter\s+Box"
             "(?:\s*[A-Z]+\s*in\s+Chapter\s+[0-9]+)?"
             ")?)"
             ")"
            "\s*"
             
             f"(?P<{SECTION}>"
             "(?:(?:(?:TS\.)?[A-Z]|SPM|TS|[Ff]ootnote )\.?)?"
             "\d+(?:\.\d+)*"
             ")"
        )
        matched_dict = self.create_matched_dict_and_unmatched_keys(paragraph_dict, node_re)

        return self.create_counters(PACKAGE, SECTION, SUBPACKAGE, matched_dict, debug=True)
        # print(f"unmatched {len(unmatched_keys)} {unmatched_keys}")

        (matched_dict.keys(), Counter(pck_counter), Counter(subp_counter), Counter(sect_counter))

        # print(f"counter {counter.most_common_values()}")

    def create_counters(self, PACKAGE, SECTION, SUBPACKAGE, matched_dict, debug=False):
        pck_counter = defaultdict(int)
        subp_counter = defaultdict(int)
        sect_counter = defaultdict(int)
        for key in matched_dict:
            value = matched_dict.get(key)
            pck_counter[value[PACKAGE]] += 1
            subp_counter[value[SUBPACKAGE]] += 1
            sect_counter[value[SECTION]] += 1
        if debug:
            print(f"package: {Counter(pck_counter)}")
            print(f"subpack: {Counter(subp_counter)}")
            print(f"section: {Counter(sect_counter)}")

        return (matched_dict.keys(), Counter(pck_counter), Counter(subp_counter), Counter(sect_counter))

    def create_matched_dict_and_unmatched_keys(self, def_dict, node_re):
        print(f"def_dict {def_dict}")
        counter = Counter(def_dict)
        print(f"counter {len(counter)}: {counter.most_common()}")

        matched_dict = dict()
        unmatched_keys = set()
        for key in counter:
            match = re.match(node_re, key)
            if match is None:
                unmatched_keys.add(key)
            else:
                matched_dict[key] = match.groupdict()
        return matched_dict

    def test_create_target_node_dir_tree_from_ipcc_chapter_DEVELOP(self):
        """reads a chapter in HTML, finds targets in {...'...} , uses div id as anchor
        and builds directory tree of targets
        """
        file = Path(Resources.TEST_IPCC_DIR, "LongerReport", "fulltext.html")
        assert file.exists(), f"{file} should exist"
        table = TargetExtractor.extract_ipcc_fulltext_into_source_target_table(file)
        # TODO make pandas object to manage columns
        target_extractor = TargetExtractor.create_target_extractor(
            ['id', 'source', 'target', 'package', 'section', 'object', 'subsection', 'source_text'])
        df = pd.DataFrame(table, columns=target_extractor.column_dict.keys())
        print(f"df {df}")
        lr_path = Path(AmiAnyTest.TEMP_HTML_DIR, "ipcc", "kg", "LongReport")
        lr_path.mkdir(exist_ok=True, parents=True)
        print(f"writing CSV to {lr_path}")
        df.to_csv(path_or_buf=Path(lr_path, "edges.csv"))
        # print(f"data frame {df}")
        common_source_tuples = target_extractor.find_commonest_in_node_lists (table, node_name="source")
        common_target_tuples = target_extractor.find_commonest_in_node_lists (table, node_name="target")
        print(f"target {common_target_tuples}\nsource {common_source_tuples}")
        temp_dir = Path(AmiAnyTest.TEMP_HTML_DIR, "ipcc", "LR_network")
        temp_dir.mkdir(exist_ok=True)

        Target.make_dirs_from_targets(common_target_tuples, temp_dir)

    def test_create_target_node_dir_trees_from_ipcc_chapters_DEVELOP(self):
        """reads a chapter in HTML, finds targets in {...'...} , uses div id as anchor
        and builds directory tree of targets
        """
        packages = [
            "LongerReport",
            "wg2_spm",
            "wg3_spm",
        ]
        for package in packages:
            file = Path(Resources.TEST_IPCC_DIR, package, "fulltext.html")
            table = TargetExtractor.extract_ipcc_fulltext_into_source_target_table(file)
            common_source_tuples, common_target_tuples = self.find_commonest_in_source_target_lists(table)
            ipcc_dir = Path(AmiAnyTest.TEMP_HTML_DIR, "ipcc")
            temp_dir = Path(ipcc_dir, f"{package}_network")
            print(f"writing to {temp_dir}")
            temp_dir.mkdir(exist_ok=True)

            Target.make_dirs_from_targets(common_target_tuples, temp_dir)

    def test_unescape_xml_character_entity_to_unicode(self):
        """
        reads HTML with embedded character entities (e.g. "&#176;")
        uses html.unescape() to convert to Unicode

         """
        # import HTMLParser
        # h = HTMLParser.HTMLParser()
        # h.unescape('&copy; 2010')  # u'\xa9 2010'
        # h.unescape('&#169; 2010')  # u'\xa9 2010'
        import html
        copy = html.unescape('&copy; 2010')
        degrees = html.unescape('&#176; 2010')
        two = 2
        print(f"\ncopy is {copy} on {two} December 18{degrees}")
        degrees = html.unescape('document &#169; PMR 2022 18&#176;')
        assert degrees == 'document © PMR 2022 18°'

    def test_unescape_xml_entities_old(self):
        """
        """
        # import HTMLParser
        # h = HTMLParser.HTMLParser()
        # h.unescape('&copy; 2010')  # u'\xa9 2010'
        # h.unescape('&#169; 2010')  # u'\xa9 2010'
        import html
        copy = html.unescape('&copy; 2010')
        degrees = html.unescape('&#176; 2010')
        two = 2
        print(f"\ncopy is {copy} on {two} December 18{degrees}")
        degrees = html.unescape('document &#169; PMR 2022 18&#176;')
        assert degrees == 'document © PMR 2022 18°'

    def test_extract_ipcc_bib_pointers(self):
        """
        BEING DEVELOPED
        find biblio refs in HTML
    (Peters et al., 2020; Jackson et al., 2019; Friedlingstein et al., 2020).
    Refactor and generalise to python dict
        """
        # text_has_bracket_xpath = "//div//text()[contains(., '(')]"
        D = "\\d"
        S = "\\s"
        LB = "\\("
        RB = "\\)"
        dictx = {
            "xpath": "foo",
        }
        html_searcher = HTMLSearcher(xpath_dict=dictx)
        descend_with_paren_in_text = "//*[contains(text(), '(')]"
        balanced_brackets = f"{LB}([^{RB}]*){RB}"
        comma_semicolon_chunks = f"{S}*[,;]{S}*"
        dates1920 = f"([A-Z].*{S}+(20|19){D}{D}[a-z]?)"

        in_file = str(Path(Resources.TEST_IPCC_CHAP06, "fulltext.html"))
        html_entity = lxml.etree.parse(in_file)
        html_searcher.add_xpath("text_with_paren", descend_with_paren_in_text)
        print(f"XPATH... {html_searcher.xpath_dict.keys()}")
        html_searcher.add_chunk_re(balanced_brackets)
        html_searcher.add_splitter_re(comma_semicolon_chunks)
        html_searcher.add_subnode_key_re("ref", dates1920)
        html_searcher.set_unmatched_flag(False)

        # use first div paragraph chunk
        div712 = html_entity.xpath("//div[@id='id712']")[0]
        str_un = HtmlLib.convert_character_entities_in_lxml_element_to_unicode_string(div712)

        assert str_un == '<div style="" id="id712"><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 11px;" id="id713">Warming cannot be limited to well below 2°C without rapid and deep reductions in energy system CO</span><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 6px;" id="id715">2</span><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 11px;" id="id716"> and GHG emissions. </span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id717">In scenarios limiting likely warming to 1.5°C with limited overshoot (likely below 2°C), net energy system CO</span><span style="font-family: TimesNewRomanPSMT; font-size: 6px;" id="id719">2</span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id720"> emissions (interquartile range) fall by 87% to 97%% (60% to 79%) in 2050. In 2030, in scenarios limiting warming to 1.5°C with no or limited overshoot, net CO2 and GHG emissions fall by 35-51% and 38-52% respectively. In scenarios limiting warming to 1.5°C with no or limited overshoot (likely below 2°C), net electricity sector CO</span><span style="font-family: TimesNewRomanPSMT; font-size: 6px;" id="id724">2</span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id725"> emissions reach zero globally between 2045 and 2055 (2050 and 2080) </span><span style="font-family: TimesNewRomanPS-ItalicMT; font-size: 11px;" id="id727">(high confidence)</span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id728"> {6.7}  </span></div>'
        html_path = Path(Resources.TEST_IPCC_CHAP02, "maintext_old.html")
        html_searcher.search_path_chunk_node(html_path)



class Test_PDFHTML(AmiAnyTest):
    """
    Combine PDF2HTML with styles and other tidy
    """

    def test_pdf_to_styled_chapter_15_EXAMPLE(self):
        pdf_args = PDFArgs()
        outdir = Path(AmiAnyTest.TEMP_HTML_IPCC, "Chapter15")
        outpath1 = Path(AmiAnyTest.TEMP_HTML_IPCC, "Chapter15", "fulltext.html")
        maxpage = 30
        style_count = 17
        print_styles = True
        inpath = Path(Resources.TEST_IPCC_CHAP15, "fulltext.pdf")
        style_dict = pdf_args.pdf_to_styled_html_CORE(inpath, maxpage, outdir, outpath1)
        pprint.pprint(f"STYLE {style_dict}")

    @unittest.skipUnless(True, "multiple chapter and documents")
    def test_pdf_to_styled_multiple_EXAMPLE(self):
        pdf_args = PDFArgs()
        for chapter in [
            # "Chapter03",
            # "Chapter15",
            "LongerReport",
            # # "wg2_03", # this has performance problems due to vector graphics/boxes
            # "wg2_06",
            # "wg2_spm",
            # "wg3_spm",
        ]:
            outdir = Path(AmiAnyTest.TEMP_HTML_IPCC, chapter)
            outpath1 = Path(AmiAnyTest.TEMP_HTML_IPCC, chapter, "fulltext.html")
            maxpage = 230
            inpath = Path(Resources.TEST_IPCC_DIR, chapter, "fulltext.pdf")
            style_dict = pdf_args.pdf_to_styled_html_CORE(inpath, maxpage, outdir, outpath1)
            pprint.pprint(f"STYLE\n{style_dict}")


class TestHtmlTidy(AmiAnyTest):

    def test_html_good(self):
        """
        ensures valid html passes
        """
        # ideal file html-head-body
        html_ideal = """
        <html>
          <!-- ideal file -->
          <head>
          </head>
          <body>
            <ul>
              <li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li>
              <li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li>
            </ul>
          </body>
        </html>
            """
        html_raw = lxml.etree.fromstring(html_ideal)
        html_new = HtmlTidy._ensure_html_root(html_raw)
        assert len(html_new.xpath("/html")) == 1
        assert len(html_new.xpath("/*/html")) == 0

    def test_html_ok(self):
        """
        various allowable but non-ideal html
        """
        # ok file html-body
        html_body_only = """
        <html>
          <!-- no head -->
          <body>
            <ul>
              <li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li>
              <li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li>
            </ul>
          </body>
        </html>
            """
        html_raw = lxml.etree.fromstring(html_body_only)
        html_new = HtmlTidy._ensure_html_root(html_raw)
        assert len(html_new.xpath("/html")) == 1
        assert len(html_new.xpath("/*/html")) == 0

        # ok file html-no-body
        html_body_only = """
        <html>
          <!-- no head -->
          <ul>
            <li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li>
            <li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li>
          </ul>
        </html>
            """
        html_raw = lxml.etree.fromstring(html_body_only)
        html_new = HtmlTidy._ensure_html_root(html_raw)
        assert len(html_new.xpath("/html")) == 1
        assert len(html_new.xpath("/*/html")) == 0

    def test_wrap_element_html(self):
        """
        wraps element in <html>. Adds <head> and <body>
        """
        # no html head and implied body
        html_body_only = """<ul><li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li><li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li></ul>
            """
        html_raw = lxml.etree.fromstring(html_body_only)
        html_new = HtmlTidy.ensure_html_head_body(html_raw)
        assert len(html_new.xpath("/html")) == 1
        assert len(html_new.xpath("/html/head")) == 1
        assert len(html_new.xpath("/html/body")) == 1
        html_s = lxml.etree.tostring(html_new).decode('UTF-8')
        assert """<html><head/><body><ul><li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li><li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li></ul></body></html>""" == html_s, f"found {html_s}"

        # html but no explicit head and or body; wraps p, ul in body and wraps style in head
        html_only = """<html><style>p {color: green}</style><p>should be green</p><ul><li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li><li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li></ul></html>"""
        html_raw = lxml.etree.fromstring(html_only)
        html_new = HtmlTidy.ensure_html_head_body(html_raw)
        assert len(html_new.xpath("/html")) == 1
        assert len(html_new.xpath("/html/head")) == 1
        assert len(html_new.xpath("/html/body")) == 1
        html_s = lxml.etree.tostring(html_new).decode('UTF-8')
        assert """<html><head><style>p {color: green}</style></head><body><p>should be green</p><ul><li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li><li style="font-family: monospace; font-size: 13px; color: blue; left: 10px;">foo</li></ul></body></html>""" == html_s, f"found {html_s}"
        # for display
        html_dir = Path(AmiAnyTest.TEMP_DIR, "html")
        html_dir.mkdir(exist_ok=True)
        assert html_dir.exists(), f"{html_dir} must exist"
        with open(Path(html_dir, "html_only.html"), "w") as f:
            f.write(html_only)
        with open(Path(html_dir, "html_tidied.html"), "w") as f:
            f.write(html_s)

    def test_normalize_pdf2html_ipcc(self):
        """
        output of pdf2html normalized to have head and body
        """
        html_elem = lxml.etree.parse(str(MINI_IPCC_PATH))
        html_tidy_elem = HtmlTidy.ensure_html_head_body(html_elem)
        path = Path(AmiAnyTest.TEMP_DIR, "html", "tidy_mini.html")
        XmlLib.write_xml(html_tidy_elem, path)


class TestCSSStyle(AmiAnyTest):

    def test_extract_character_style(self):
        """
        Test extract character info and separate the rest
        creates 2 substyles
        """
        css = CSSStyle.create_css_style_from_css_string(
            "font-weight: bold; font-family: monospace; font-size: 13px; color: blue; bottom: 10px;")
        (extracted, retained) = font_style, rest_style = css.extract_substyles(
            [CSSStyle.FONT_STYLE, CSSStyle.FONT_WEIGHT, CSSStyle.FONT_FAMILY, CSSStyle.FONT_SIZE, CSSStyle.COLOR])
        assert type(extracted) is CSSStyle
        assert type(retained) is CSSStyle
        assert extracted == CSSStyle.create_css_style_from_css_string(
            "font-weight: bold; font-family: monospace; font-size: 13px; color: blue;")
        assert retained == CSSStyle.create_css_style_from_css_string("bottom: 10px")

    def test_extract_text_styles(self):
        """
        Extracts named styled components into new styles and creates HtmlStyle
        """
        css = CSSStyle.create_css_style_from_css_string(
            "font-weight: bold; font-family: monospace; font-size: 13px; color: blue; bottom: 10px;")
        extracted_style, retained_style = css.extract_text_styles()
        assert extracted_style == CSSStyle.create_css_style_from_css_string(
            "font-weight: bold; font-family: monospace; font-size: 13px; color: blue;")
        assert retained_style == CSSStyle.create_css_style_from_css_string("bottom: 10px")

    def test_extract_text_styles_into_html_style(self):
        """
        Extracts text style components into new <style>, updated class, remaining style value
        """
        css = CSSStyle.create_css_style_from_css_string(
            "font-weight: bold; font-family: monospace; font-size: 13px; color: blue; bottom: 10px;")
        class_name = "s1"
        old_class_name = "foo bar"
        new_html_style_element, retained_style_string, html_class_val = \
            css.extract_text_styles_into_class(class_name, old_classstr=old_class_name)
        assert new_html_style_element.text == ".s1 {font-weight: bold; font-family: monospace; font-size: 13px; color: blue;}"
        assert retained_style_string == "bottom: 10px;"
        assert html_class_val == "foo bar s1"

        #
        # assert ext_s == "<style>l1 {font-weight: bold; font-family: monospace; font-size: 13px; color: blue;}</style>", f"found {ext_s}"
        # ret_s = lxml.etree.tostring(retained_style_element).decode("UTF-8")
        # assert ret_s == "bottom: 10px;", f"found {ret_s}"

    def test_extract_many_text_styles_into_html_style(self):
        """
        Extracts named styled components into new styles with classrefs and creates HtmlStyle
        """
        html_s = """
        <html>
          <head>
            <style>.pink {background-color: pink;}</style>
          </head>
          <body>
            <ul>
              <li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">13px bold</li>
              <li class="pink" style="font-family: monospace; font-size: 30px; color: purple; left: 10px;">purple on pink background</li>
              <li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">bold blue</li>
              <li style="font-style: italic; font-family: monospace; font-size: 20px; color: red; left: 10px;">italic red</li>
              <li style="font-weight: bold; font-family: monospace; font-size: 13px; color: blue; left: 10px;">same as 3</li>
            </ul>
          </body>
        </html>
            """
        html_elem = lxml.etree.fromstring(html_s)
        html_elem = HtmlTidy.ensure_html_head_body(html_elem)  # redundant as tidy already
        HtmlStyle.extract_all_text_styles_to_head(html_elem)
        print(f"ss {lxml.etree.tostring(html_elem.xpath('/html/head')[0])} \n ... {lxml.etree.tostring(html_elem)}")
        html_dir = Path(AmiAnyTest.TEMP_DIR, "html")
        html_dir.mkdir(exist_ok=True)
        outpath = Path(html_dir, "styles.html")
        with open(str(outpath), "w") as f:
            f.write(lxml.etree.tostring(html_elem).decode('UTF-8'))
            logger.info(f"wrote style file to {outpath}")
            print(f"(logger) wrote style file to {outpath}")

    def test_extract_styles_from_mini_document_example(self):
        """
        starts with tidied html
        start of IPCC WG3 Chapter06
        identifies all styles and extacts into <head><style>s and replaces @style with @class
        """
        html_dir = Path(AmiAnyTest.TEMP_DIR, "html")
        html_dir.mkdir(exist_ok=True)
        html_elem = lxml.etree.parse(str(MINI_IPCC_PATH))
        html_elem = HtmlTidy.ensure_html_head_body(html_elem)
        assert len(html_elem.xpath("/html/head/style")) == 0, f"no head styles in original"
        assert len(html_elem.xpath("/html/body//*[not(normalize-space(@style))='']")) == 50, \
            f"raw document should have 50 elements with non-empty @style attributes"
        # this is so HTML browsers can see the initial file
        with open(str(Path(html_dir, "ipcc_styles0.html")), "wb") as f:
            f.write(lxml.etree.tostring(html_elem))

        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem)

        outpath = str(Path(html_dir, "ipcc_styles_voloured.html"))
        with open(outpath, "wb") as f:
            f.write(lxml.etree.tostring(html_elem))
            print(f"(logger) output to {outpath}")

        assert len(html_elem.xpath("/html/head/style")) == 7, f"7 head styles"
        assert len(html_elem.xpath("/html/body//*[@class]")) == 51, \
            f"new document should have 51 elements with @class attributes"

    def test_extract_normalize_styles_old_chapter_4_EXAMPLE(self):
        """
        Old chapter still with header/footer.
        example mainly to find styles
        """
        output_html_dir = Path(AmiAnyTest.TEMP_DIR, "html")
        output_html_dir.mkdir(exist_ok=True)
        html_elem = lxml.etree.parse(str(Path(Resources.TEST_IPCC_CHAP04, "fulltext_old.html")))
        html_elem = HtmlTidy.ensure_html_head_body(html_elem)
        assert len(html_elem.xpath("/html/head/style")) == 0, f"no head styles in original"
        assert len(html_elem.xpath("/html/body//*[not(normalize-space(@style))='']")) == 2302, \
            f"raw document should have 50 elements with non-empty @style attributes"
        # this is so HTML browsers can see the initial file
        with open(str(Path(output_html_dir, "ipcc_fulltext_styles0.html")), "wb") as f:
            f.write(lxml.etree.tostring(html_elem))

        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem)

        with open(str(Path(output_html_dir, "ipcc_chap4_fulltext_styles2.html")), "wb") as f:
            f.write(lxml.etree.tostring(html_elem))

        assert len(html_elem.xpath("/html/head/style")) == 23, f"23 head styles"
        assert len(html_elem.xpath("/html/body//*[@class]")) == 2304, \
            f"new document should have 2304 elements with @class attributes"
        assert len(html_elem.xpath("/html/body//*[contains(@class,'dec')]")) == 0, \
            f"new document should have 0 elements with @class attributes containing 'dec1', 'dec2' etc."

    def test_extract_normalize_styles_old_chapter_17_example(self):
        """
        starts with "fulltext.html" and converts to "fulltext_styles.html"
        Old chapter still with header/footer.
        example mainly to find styles
        """
        input_path = Path(Resources.TEST_IPCC_CHAP17, "fulltext.html")
        html_elem = lxml.etree.parse(str(input_path))
        html_elem = HtmlTidy.ensure_html_head_body(html_elem)
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem)

        temp_dir = Path(AmiAnyTest.TEMP_HTML_DIR, "ipcc", "chapter17")
        temp_dir.mkdir(exist_ok=True, parents=True)
        with open(str(Path(temp_dir, "fulltext_styles.html")), "wb") as f:
            f.write(lxml.etree.tostring(html_elem))

        assert len(html_elem.xpath("/html/head/style")) == 13, f"13 head styles"
        assert len(html_elem.xpath("/html/body//*[@class]")) == 1330, \
            f"new document should have 2304 elements with @class attributes"
        assert len(html_elem.xpath("/html/body//*[contains(@class,'dec')]")) == 0, \
            f"new document should have 0 elements with @class attributes containing 'dec1', 'dec2' etc."

    def test_css_parse(self):
        css_str = "height: 22; width: 34;"
        css_style = CSSStyle.create_dict_from_name_value_array_string(css_str)
        assert css_style
        assert "height" in css_style
        assert css_style.get("height") == "22"
        assert "width" in css_style
        assert css_style.get("width") == "34"

    def test_make_style_dict_from_html(self):
        """
        extracts <style> elements into a Python dic
        """
        html_str = """
        <html>
          <head>
            <style>.s0 {font-size:14 px; stroke: blue;}</style>
            <style>.s1 {font-size:10 px; fill: red;}</style>
            <style>.s2 {font-size:8 px; border: solid 1 px;}</style>
          </head>
          <body/>
        </html>
          """
        styles = CSSStyle.extract_styles_from_html_string(html_str)
        style_dict = CSSStyle.create_style_dict_from_styles(style_elems=styles)
        assert ".s1" in style_dict.keys()
        assert 'font-size:10 px; fill: red;' == style_dict[".s1"]

    def test_validate_html_styles_ERRORS(self):
        """
        try to create style_dict from invalid content. Should raise errors
        """
        duplicate_css_ref = """ 
        <html>
          <head>
            <style>.s0 {font-size:14 px; stroke: blue;}</style>
            <style>.s1 {font-size:10 px; fill: red;}</style>
            <style>.s0 {font-size:8 px; border: solid 1 px;}</style>
          </head>
          <body/>
        </html>
"""
        styles = CSSStyle.extract_styles_from_html_string(duplicate_css_ref)
        try:
            style_dict = CSSStyle.create_style_dict_from_styles(style_elems=styles)
        except ValueError as e:
            assert str(e) == "duplicate style ref .s0 {font-size:8 px; border: solid 1 px;}"

        missing_dot = """ 
        <html>
          <head>
            <style>.s0 {font-size:14 px; stroke: blue;}</style>
            <style>.s1 {font-size:10 px; fill: red;}</style>
            <style>s2 {font-size:8 px; border: solid 1 px;}</style>
          </head>
          <body/>
        </html>
"""
        styles = CSSStyle.extract_styles_from_html_string(missing_dot)
        try:
            style_dict = CSSStyle.create_style_dict_from_styles(style_elems=styles)
        except ValueError as e:
            assert str(e) == "BAD head_style s2 {font-size:8 px; border: solid 1 px;}"

        bad_css = """ 
        <html>
          <head>
            <style>.s0 {font-size:14 px; stroke: blue;}</style>
            <style>.s1 {font-size:10 px; fill: red;}</style>
            <style>.s2 {font-size:8 px border: solid 1 px;}</style>
          </head>
          <body/>
        </html>
"""
        styles = CSSStyle.extract_styles_from_html_string(bad_css)
        try:
            style_dict = CSSStyle.create_style_dict_from_styles(style_elems=styles)
        except KeyError as e:
            assert str(e) == "'bad style font-size:8 px border: solid 1 px in CSS: font-size:8 px border: solid 1 px;'"


class TestHtmlClass(AmiAnyTest):
    """

    """

    def test_minimal(self):
        """
        empty HtmlClass object
        """
        html_class = HtmlClass()
        assert html_class.classes == set()
        assert html_class.class_string == ""
        assert not html_class.has_class("foo")

    def test_single_class(self):
        """
        HtmlClass object with single class
        """
        html_class = HtmlClass("foo")
        assert html_class.classes == {"foo"}
        assert html_class.class_string == "foo"
        assert html_class.has_class("foo")

    def test_multiple_class(self):
        """
        HtmlClass object with multiple classes
        """
        html_class = HtmlClass("foo bar")
        assert html_class.classes == {"foo", "bar"}
        assert html_class.class_string == "bar foo"
        assert html_class.has_class("foo")
        assert html_class.has_class("bar")

    def test_add_class(self):
        """
        add classes to HtmlClass object
        """
        html_class = HtmlClass("")
        html_class.add_class("foo")
        assert html_class.classes == {"foo"}
        html_class.add_class("bar")
        assert html_class.classes == {"foo", "bar"}
        assert html_class.class_string == "bar foo"
        assert html_class.has_class("foo")
        assert html_class.has_class("bar")

    def test_remove_class(self):
        """
        remove classes from HtmlClass object
        """
        html_class = HtmlClass("foo bar")
        assert html_class.has_class("foo")
        assert html_class.has_class("bar")

        html_class.remove("foo")
        assert html_class.classes == {"bar"}
        assert not html_class.has_class("foo")
        assert html_class.has_class("bar")

        html_class.add_class("foo")
        assert html_class.classes == {"foo", "bar"}
        assert html_class.class_string == "bar foo"
        assert html_class.has_class("foo")
        assert html_class.has_class("bar")

        html_class.remove("baz")  # should be no effect
        assert html_class.classes == {"foo", "bar"}
        assert html_class.class_string == "bar foo"
        assert html_class.has_class("foo")
        assert html_class.has_class("bar")

    def test_replace(self):
        """
        replace existing class
        """
        html_class = HtmlClass("foo bar")

        html_class.replace_class("foo", "plugh")
        assert html_class.classes == {"bar", "plugh"}
        assert not html_class.has_class("foo")
        assert html_class.has_class("bar")
        assert html_class.has_class("plugh")
        assert html_class.class_string == "bar plugh"

        html_class.add_class("foo")
        assert html_class.classes == {"foo", "bar", "plugh"}
        assert html_class.class_string == "bar foo plugh"
        html_class.replace_class("foo", "plugh")  # contains existing class, so should equal remove
        assert html_class.class_string == "bar plugh"


class TestHtmlTree(AmiAnyTest):
    """
    makes sections from unstructured text
    """

    def test_nest_decimal_sections(self):
        """
        nests decimal sections (1.2.3, 3.4, etc.) into a tree
        """
        html_elem = lxml.etree.parse(str(Path(Resources.TEST_IPCC_CHAP04, "ipcc_fulltext_styles.html")))
        #  "<span id="id1521" class="s0 dec2">4.1</span>")
        xpath = (".//div/span["
                 "contains(@class, 'dec1') "
                 "or contains(@class, 'dec2') "
                 "or contains(@class, 'dec3') "
                 "or contains(@class, 'dec4')]")
        decimal_sections = HtmlTree.get_decimal_sections(html_elem, xpath=xpath)

        hierarchy = SectionHierarchy()
        hierarchy.add_sections(decimal_sections, poplist=["Chapter 4:"])
        hierarchy.sort_sections()

    @unittest.skip
    def test_decimal_chapters_production(self):
        # """NOT WORKING FULLY"""
        # TEST_IPCC_WG3 = Path(Resources.TEST_IPCC_DIR)
        # if not TEST_IPCC_WG3.exists():
        #     print(f"semanticClimate files not available locally")
        #     return
        html_elem = lxml.etree.parse(str(Path(Resources.TEST_IPCC_DIR, "wg2_03", "fulltext.html")))
        xpath = (".//div/span["
                 "contains(@class, 'dec1') "
                 "or contains(@class, 'dec2') "
                 "or contains(@class, 'dec3') "
                 "or contains(@class, 'dec4')]")
        decimal_sections = HtmlTree.get_decimal_sections(html_elem, xpath=xpath)

        hierarchy = SectionHierarchy()
        hierarchy.add_sections(decimal_sections, poplist=["Chapter 3:"])
        hierarchy.sort_sections()

class TestFont(AmiAnyTest):

    def _assert_new_css_style(self, style, new_value):
        css_style = CSSStyle.create_css_style_from_css_string(style)
        symbol_ref, new_css_style = AmiFont.create_font_edited_style_from_css_style_object(css_style)
        assert str(new_css_style) == new_value

    def _run_tests_0(self, tests):
        for test in tests:
            ami_font = AmiFont.extract_name_weight_style_stretched(test[0])
            assert str(ami_font) == test[0] + "/" + test[1]

    # -------------------------------


    def test_create_from_names(self):
        tests = [
            ("ArialNarrow", "Arial///Narrow"),
            ("ArialBoldItalic", "Arial/Bold/Italic/"),
            ("ArialItalic", "Arial//Italic/"),
            ("ArialBold", "Arial/Bold//"),
            ("Arial", "Arial///"),
        ]
        self._run_tests_0(tests)

        test2s = [
            ("ArialNarrow", "Arial///Narrow"),
            ("ArialNarrow-Bold", "Arial/Bold//Narrow"),
            ("Calibri", "Calibri///"),
            ("FrutigerLTPro-BlackCn", "FrutigerLTPro/Bold//Narrow"),
            ("FrutigerLTPro-BoldCn", "FrutigerLTPro/Bold//Narrow"),
            ("FrutigerLTPro-BoldCnIta", "FrutigerLTPro/Bold/Italic/Narrow"),
            ("FrutigerLTPro-Condensed", "FrutigerLTPro///Narrow"),
            ("FrutigerLTPro-CondensedIta", "FrutigerLTPro//Italic/Narrow"),
            ("FrutigerLTPro-Light", "FrutigerLTPro/Light//"),
            ("FrutigerLTPro-LightCn", "FrutigerLTPro/Light//Narrow"),
            ("FrutigerLTPro-LightCnIta", "FrutigerLTPro/Light/Italic/Narrow"),
            ("FrutigerLTPro-Roman", "FrutigerLTProRoman///"),

        ]
        self._run_tests_0(test2s)

    def test_edit_fonts_in_styles(self):
        """
        edits the style attributes to extract weights and styles
        tests: CSSStyle.create_css_style_from_css_string(style)
        """
        self._assert_new_css_style("font-family: ArialNarrowBold; fill: red",
                                  'font-family:Arial; fill:red; font-weight:Bold; font-stretched:Narrow;')
        self._assert_new_css_style("font-family: ArialBold; fill: red",
                                  'font-family:Arial; fill:red; font-weight:Bold;')
        self._assert_new_css_style("font-family: FooBarBold; fill: red",
                                  'font-family:FooBar; fill:red; font-weight:Bold;')


    def test_normalize_fonts_in_head_style_elements_CURRENT(self):
        """
        extract font properties from styles and write back into html header
        e.g.
        <html>
          <head>
            <style>.s1 {font-family:ArialNarrowBold; fill:red}</style>
            <style>.s2 {font-family:FooBar-Ita; fill:blue}</style>
          </head>
        </html>

        goes to
        <html>
          <head>
            <style>.s1 {font-family:Arial; font-weight: bold; font-stretched: Narrow; fill:red}</style>
            <style>.s2 {font-family:FooBar; font-style: italic; fill:red}</style>
          </head>
        </html>
        """
        html_str = """
        <html>
          <head>
            <style>.s1 {font-family:ArialNarrowBold; fill:red}</style>
            <style>.s2 {font-family:FooBar-Ita; fill:blue}</style>
          </head>
        </html>
"""
        html_elem = lxml.etree.fromstring(html_str)
        CSSStyle.normalize_styles_in_fonts_in_html_head(html_elem)



