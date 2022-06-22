"""Create, transform, markup up HTML, etc."""
import lxml.etree
from pathlib import Path
import re
import unittest

# local
from test.resources import Resources
from py4ami.ami_pdf import H_A


class Test_Html(unittest.TestCase):

    SINGLE_BRACKET_REC = re.compile("([^\(]*)([^\)]*\))(.*)")
    SINGLE_REF_REC = re.compile(r"""
                    (?P<pre>.*)   # leading string without bracket
                    \(            # bracket
                    (?P<body>
                    (?:[A-Z]|de|d')
                    .*(?:(?:20\d\d|19\d\d)[a-z\,]*))  # body starts uppcase and ends with date (without brackets)
                    \)            # trailing bracket
                    (?P<post>.*)  # trailing string without bracket
                    """, re.VERBOSE)

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
        """tests that test reference compiles"""
        html_span = lxml.etree.fromstring(self.html_single_ref)
        assert type(html_span) is lxml.etree._Element
        assert html_span.text == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "

        html_span = lxml.etree.fromstring(self.html_compound_ref)
        assert type(html_span) is lxml.etree._Element
        assert html_span.text == "and more blah (Deep  Decarbonization  Pathways  Project  2015; Roelfsema et al. 2020)  and even more blah"

        html_span = lxml.etree.fromstring(self.html_subsection_ref)
        assert type(html_span) is lxml.etree._Element
        assert html_span.text == "to national level (4.2.2.3) and subnational"

    def test_find_single_brackets_in_span(self):
        html_span = lxml.etree.fromstring(self.html_single_ref)
        text = html_span.text
        match = self.SINGLE_BRACKET_REC.match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(0) == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "
        assert match.group(1) == "It  is  important  blah blah detailed  national  studies  "
        assert match.group(2) == "(Bataille  et  al.  2016a)"
        assert match.group(3) == "  and more blah "

    def test_find_single_biblio_ref_in_span(self):

        html_span = lxml.etree.fromstring(self.html_single_ref)
        text = html_span.text
        match = self.SINGLE_REF_REC.match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(0) == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "
        assert match.group('pre') == "It  is  important  blah blah detailed  national  studies  "
        assert match.group('body') == "Bataille  et  al.  2016a"
        assert match.group('post') == "  and more blah "
        assert match.groupdict() == {
                                    'body': 'Bataille  et  al.  2016a',
                                    'post': '  and more blah ',
                                    'pre': 'It  is  important  blah blah detailed  national  studies  '
                                    }

    def test_exceptions_biblio_ref_in_span(self):
        assert self.SINGLE_REF_REC.match("Foo bar (d'Arcy & other stuff in 2008) not a ref")
        assert self.SINGLE_REF_REC.match("Foo bar (de Sitter and other stuff in 2008) not a ref")


    def test_not_ref_fail(self):
        assert not self.SINGLE_REF_REC.match("Foo bar (and other stuff in 2008) not a ref")

    def test_markup_references(self):

        DOI_REC = re.compile(".*\s(doi:[^\s]*)\.")

        ref_path = Path(Resources.CHAP04, "references.html" )
        assert ref_path.exists()
        ref_elem = lxml.etree.parse(str(ref_path))
        ref_divs = ref_elem.xpath("body/div")
        assert len(ref_divs) == 1316

        for div in ref_divs:
            spans = div.xpath("./span")
            self._iterate_spans_until_doi_found(DOI_REC, div, spans)
        chap4_dir = Path(Resources.TEMP_DIR, "ipcc_html", "chapter04")
        if not chap4_dir.exists():
            chap4_dir.mkdir()
        outpath = Path(chap4_dir, "ref_doi.html")
        # tree = lxml.etree.ElementTree(ref_elem)
        ref_elem.write(str(outpath))

    def _iterate_spans_until_doi_found(self, DOI_REC, div, spans):
        for span in spans:
            text = span.text
            doi_match = DOI_REC.match(text)
            if doi_match:
                doi_txt = doi_match.group(1)
                if "doi:" in doi_txt:
                    doi_txt = doi_txt.replace("doi:https", "https")
                    doi_txt = doi_txt.replace("doi:", "https://doi.org/")
                    if doi_txt.startswith("doi:"):
                        doi_txt = "https://" + doi_txt
                    print(f"doi: {doi_txt}")
                    a = lxml.etree.SubElement(div, H_A)
                    a.attrib["href"] = doi_txt
                    a.text = doi_txt
                    break
            else:
                print(f"no doi: {text}")
