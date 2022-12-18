"""Create, transform, markup up HTML, etc."""
import lxml.etree
from pathlib import Path
import os
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path

import lxml.etree

from py4ami.ami_bib import Reference, Biblioref
from py4ami.ami_dict import AmiDictionary
# local
from py4ami.ami_html import HtmlUtil, H_SPAN, CSSStyle, HTMLSearcher
import lxml.etree

import test
from py4ami.ami_bib import Reference, Biblioref
from py4ami.ami_dict import AmiDictionary
# local
from py4ami.ami_html import HtmlUtil, H_SPAN, CSSStyle
from py4ami.util import Util
from py4ami.xml_lib import HtmlLib
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


class HtmlTest(AmiAnyTest):
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
        chap444 = Path(Resources.IPCC_CHAP04, "4.4.html")
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
        chap444 = Path(Resources.IPCC_CHAP04, "4.4.html")
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
        chap444 = Path(Resources.IPCC_CHAP04, "4.4.html")
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

        ref_path = Path(Resources.IPCC_CHAP04, "references.html")
        assert ref_path.exists()
        ref_elem = lxml.etree.parse(str(ref_path))
        ref_divs = ref_elem.xpath("body/div")
        assert len(ref_divs) == 1316

        for div in ref_divs:
            ref = Reference.create_ref_from_div(div)
            ref.markup_dois_in_spans()
        path = Path(Resources.TEMP_DIR, "ipcc_html")
        path.mkdir(exist_ok=True)
        chap4_dir = Path(path, "chapter04")
        if not chap4_dir.exists():
            chap4_dir.mkdir()
        outpath = Path(chap4_dir, "ref_doi.html")
        ref_elem.write(str(outpath))

    def test_make_reference_class(self):
        """reads a references file and creates class"""

        # ami_html = AmiHtml()
        ref_path = Path(Resources.IPCC_CHAP04, "references.html")
        assert ref_path.exists()
        ref_elem = lxml.etree.parse(str(ref_path))
        ref_divs = ref_elem.xpath("body/div")
        assert len(ref_divs) == 1316

        Reference.markup_dois_in_div_spans(ref_divs)

        path = Path(Resources.TEMP_DIR)
        path.mkdir(exist_ok=True)
        chap4_dir = Path(path, "ipcc_html", "chapter04")
        if not chap4_dir.exists():
            chap4_dir.mkdir()
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
        test_dir = Path(Resources.TEMP_DIR, "html")
        if not test_dir.exists():
            test_dir.mkdir()
        with open(str(Path(test_dir, "add_href.html")), "wb") as f:
            f.write(lxml.etree.tostring(div))

    def test_markup_chapter_with_dictionary_no_css(self):
        """read dictionary file and index a set of spans
        Test: ami_dict.markup_html_from_dictionary
        and add style
        and write result
        """
        dictionary_file = Path(Resources.IPCC_CHAP06, "abbrev_as.xml")
        assert dictionary_file.exists(), f"file should exist {dictionary_file}"
        ami_dict = AmiDictionary.create_from_xml_file(dictionary_file)
        ami_dict.ignorecase = False
        inpath = Path(Resources.IPCC_CHAP06, "fulltext.flow20.html")
        output_dir = Path(Resources.TEMP_DIR, "html")
        if not output_dir.exists():
            output_dir.mkdir()
        output_path = Path(output_dir, "chap6_index.html")
        ami_dict.markup_html_from_dictionary(inpath, output_path, "pink")

    def test_markup_chapter_with_dictionary(self):
        """read dictionary file and index a set of spans
        Test: ami_dict.markup_html_from_dictionary
        and add style
        and write result]
        TODO USE THIS!
        """

        dict_path = Path(Resources.IPCC_CHAP06, "abbrev_as.xml")
        dict_path = Path(Resources.IPCC_CHAP06, "ipcc_ch6_rake.xml")
        # output_file = "chap6_marked.html"
        output_file = "chap6_raked.html"
        ami_dict = AmiDictionary.create_from_xml_file(dict_path, ignorecase=False)
        input_path = Path(Resources.IPCC_CHAP06, "fulltext.flow.html")
        # input_path = Path(Resources.IPCC_CHAP06, "chap6.flow.html")
        print(f"reading pdf_html {input_path}")
        html_output_dir = Path(Resources.TEMP_DIR, "html")
        if not html_output_dir.exists():
            html_output_dir.mkdir()
        print(f"output html {html_output_dir}")
        chap6_marked_path = Path(html_output_dir, output_file)

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
        target_path = Path(Resources.IPCC_CHAP06, "fulltext.flow20.html")
        output_dir = Path(Resources.TEMP_DIR, "html")
        if not output_dir.exists():
            output_dir.mkdir()
        output_path = Path(output_dir, "chap6_styled.html")

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
        html_path = Path(Resources.IPCC_CHAP04, "fulltext.flow20.html")
        html_element = lxml.etree.parse(str(html_path))
        divs = html_element.xpath(".//div")
        assert 400 <= len(divs)
        last_div = None
        last_style = None
        for div in divs:
            spans = div.xpath("./span")
            print(f"spans {len(spans)}")
            for span in spans:
                style = CSSStyle.create_css_style(span)
                print(f"{style}")
                if style == last_style:
                    print(f"styles match")
                last_span = span
                last_style = style

    @unittest.skipUnless(USER, "claim paras")
    @unittest.skipIf(BUG and False, "bad input file")
    def test_make_ipcc_obsidian_md(self):
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
        in_file = Path(Resources.IPCC_CHAP02, "exec_summary.html")
        outdir = Path(Resources.TEMP_DIR, "obsidian")
        os.makedirs(outdir, exist_ok=True)
        path = Path(in_file)
        assert path.exists(), f"{path} should exist"
        tree = lxml.etree.parse(str(path))
        ps = tree.findall(".//p")
        assert 23 <=len(ps) <= 50
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

    def test_extract_ipcc_nodes_and_pointers_raw_format(self):
        """
        read (old style) raw html with IPCC nodes and node_pointers and convert to HTML@a elements
        example
        '(high confidence). {2.2.2, Table 2.1, Figure 2.5}' contains 3 node pointers
        """
        # html = "executive_summary_css.html"
        # html = "executive_summary1.html"
        exec_summ1 = Path(Resources.IPCC_CHAP02, "maintext_old.html")
        assert exec_summ1.exists(), f"{exec_summ1} should exist"
        tree = lxml.etree.parse(str(exec_summ1))
        xpath = "//div//text()[contains(., '{')]"
        texts = tree.xpath(xpath)
        print(f"texts {len(texts)}")
        node_dict_list_list = list()
        for text in texts:
            print(f"text: {text}")
            node_dict_list = self.extract_ipcc_nodes(text)
            print(f"node_dict_list {node_dict_list}")
            node_dict_list_list.append(node_dict_list)
        assert len(node_dict_list_list) == 21
        # assert str(node_dict_list_list[0]) == "[defaultdict(<class 'list'>, {'Figure': ['2.5'],'Table': ['2.1'],\n 'unmatched': ['2.2.2']})]", f"found {node_dict_list_list[0]}"
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

        in_file = str(Path(Resources.IPCC_CHAP06, "fulltext.html"))
        html_entity = lxml.etree.parse(in_file)
        html_searcher.add_xpath("text_with_paren", descend_with_paren_in_text)
        print(f"XPATH... {html_searcher.xpath_dict.keys()}")
        html_searcher.add_chunk_re(balanced_brackets)
        html_searcher.add_splitter_re(comma_semicolon_chunks)
        html_searcher.add_subnode_key_re("ref", dates1920)
        html_searcher.set_unmatched(False)

        # use first div paragraph chunk
        div712 = html_entity.xpath("//div[@id='id712']")[0]
        str_un = HtmlLib.convert_character_entities_in_lxml_element_to_unicode_string(div712)

        assert str_un == '<div style="" id="id712"><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 11px;" id="id713">Warming cannot be limited to well below 2°C without rapid and deep reductions in energy system CO</span><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 6px;" id="id715">2</span><span style="font-family: TimesNewRomanPS-BoldMT; font-size: 11px;" id="id716"> and GHG emissions. </span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id717">In scenarios limiting likely warming to 1.5°C with limited overshoot (likely below 2°C), net energy system CO</span><span style="font-family: TimesNewRomanPSMT; font-size: 6px;" id="id719">2</span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id720"> emissions (interquartile range) fall by 87% to 97%% (60% to 79%) in 2050. In 2030, in scenarios limiting warming to 1.5°C with no or limited overshoot, net CO2 and GHG emissions fall by 35-51% and 38-52% respectively. In scenarios limiting warming to 1.5°C with no or limited overshoot (likely below 2°C), net electricity sector CO</span><span style="font-family: TimesNewRomanPSMT; font-size: 6px;" id="id724">2</span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id725"> emissions reach zero globally between 2045 and 2055 (2050 and 2080) </span><span style="font-family: TimesNewRomanPS-ItalicMT; font-size: 11px;" id="id727">(high confidence)</span><span style="font-family: TimesNewRomanPSMT; font-size: 11px;" id="id728"> {6.7}  </span></div>'
        html_path = Path(Resources.IPCC_CHAP02, "maintext_old.html")
        html_searcher.search_path_chunk_node(html_path)

    # ========================================
    def extract_ipcc_nodes(self, text) -> list:
        """
        Move to a class and refactor to use dictionary
        """
        regex1 = "{([^}]*)}"
        regex2 = "\\s*[,;]\\s*"
        regex3 = "(Table|Figure)\\s+(.*)"
        ptr = 0
        node_dict_list = list()
        while True:
            match = re.search(regex1, text[ptr:])
            if not match:
                break
            ptr = match.span()[1]
            nodestr = match.group(1)
            nodes = re.split(regex2, nodestr)
            node_dict = defaultdict(list)
            node_dict_list.append(node_dict)
            for node in nodes:
                print(f"node: {node}")
                m = re.match(regex3, node)
                if m:
                    node_dict[m.group(1)].append(m.group(2))
                    continue
                unmatched = "unmatched"
                node_dict[unmatched].append(node)
            print(f"node_dict: {node_dict.items()}")
        return node_dict_list