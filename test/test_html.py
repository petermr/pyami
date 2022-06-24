"""Create, transform, markup up HTML, etc."""
import lxml.etree
from pathlib import Path
import re
import unittest
from collections import Counter

# local
from test.resources import Resources
from py4ami.ami_pdf import H_A, H_BODY, H_SPAN
from py4ami.ami_html import AmiHtml


class Reference:
    SINGLE_BRACKET_REC = re.compile(r"""
                    (?P<pre>[^(]*)
                    [(]
                    (?P<body>
                    [^)]*
                    )
                    [)]
                    (?P<post>.*)
                    """, re.VERBOSE)  # finds a bracket pair in running text, crude
    SINGLE_REF_REC = re.compile(r"""
                    (?P<pre>.*)   # leading string without bracket
                    \(            # bracket
                    (?P<body>
                    (?:[A-Z]|de|d')
                    .*(?:20|19)\d\d[a-z,]*  # body starts uppcase and ends with date (without brackets)
                    )
                    \)            # trailing bracket
                    (?P<post>.*)  # trailing string without bracket
                    """, re.VERBOSE)
    DOI_REC = re.compile(".*\s(doi:[^\s]*)\.")  # finds DOI string in running text

    AUTHORS_DATE_REC = re.compile("""
    (?P<first>((de )|(d')|(el ))?\s*[A-Z][^\s]+) # doesn't seem to do the prefixes yet
    (?P<others>.+)
    (?P<date>20\d\d[a-z]*)
    """, re.VERBOSE)

    def __init__(self):
        pass

    @classmethod
    def create_ref_from_div(cls, div):
        """create from div which contains one or more spans
        """
        if not div:
            return None
        ref = Reference()
        ref.div = div
        ref.spans = div.xpath("./span")
        return ref

    def iterate_spans_until_doi_found(self):
        """iterates over contained spans until the doi-containing one is found
        """
        self.markup_dois_in_spans()

    def markup_dois_in_spans(self):
        for span in self.spans:
            text = span.text
            doi_match = self.DOI_REC.match(text)
            if doi_match:
                doi_txt = doi_match.group(1)
                if "doi:" in doi_txt:
                    doi_txt = doi_txt.replace("doi:https", "https")
                    doi_txt = doi_txt.replace("doi:", "https://doi.org/")
                    if doi_txt.startswith("doi:"):
                        doi_txt = "https://" + doi_txt
                    print(f"doi: {doi_txt}")
                    a = lxml.etree.SubElement(self.div, H_A)
                    a.attrib["href"] = doi_txt
                    a.text = doi_txt
                    break
            else:
                # print(f"no doi: {text}")
                pass


class Biblioref:
    """in-text pointer to References
    of form:
    Lave 1991
    Lecocq and Shalizi 2014
    Gattuso  et  al.  2018;  Bindoff  et  al.  2019
    IPBES 2019b

    IPCC  2018b:  5.3.1    # fist part only
    """

    def __init__(self):
        self.str = None
        self.first = None
        self.others = None
        self.date = None

    def __str__(self):
        s = f"{self.str} => {self.first}|{self.others}|{self.date}"
        return s

    @classmethod
    def create_refs_from_biblioref_string(cls, brefstr):
        """create from in-text string without the brackets
        :param brefstr: string may contain repeated values
        :return: list of Bibliorefs (may be empty or have one member

        """
        bibliorefs = []
        if brefstr:
            bref = " ".join(brefstr.splitlines()).replace("\s+", " ")
            chunks = bref.split(";")
            for chunk in chunks:
                # print(f" chunk {chunk}")
                if brefx := Biblioref.create_bref(chunk.strip()):
                    bibliorefs.append(brefx)
        return bibliorefs

    @classmethod
    def create_bref(cls, brefstr):
        """create Biblioref from single string
        :param brefstr: of form 'Author/s date' """

        bref = None
        match = Reference.AUTHORS_DATE_REC.match(brefstr)
        if match:
            bref = Biblioref()
            bref.str = brefstr
            bref.first = match.group("first")
            bref.others = match.group("others")
            bref.date = match.group("date")
        return bref


class TestHtml(unittest.TestCase):
    """ parsing , structuring linking in/to.form HTML
    This will evolve into an ami_html.py module
    """

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
        match = Reference.SINGLE_BRACKET_REC.match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(
            0) == "It  is  important  blah blah detailed  national  studies  (Bataille  et  al.  2016a)  and more blah "
        assert match.group(1) == "It  is  important  blah blah detailed  national  studies  "
        assert match.group(2) == "Bataille  et  al.  2016a"
        assert match.group(3) == "  and more blah "

    def test_find_single_biblio_ref_in_span(self):

        html_span = lxml.etree.fromstring(self.html_single_ref)
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

        html_span = lxml.etree.fromstring(self.html_single_ref)
        text = html_span.text
        match = Reference.SINGLE_REF_REC.match(text)
        assert match
        assert len(match.groups()) == 3

    def test_find_brackets_in_text(self):
        """read chunks of text and find brackets
        """
        chap444 = Path(Resources.IPCC_CHAP04, "4.4.html")
        chap444_elem = lxml.etree.parse(str(chap444))
        div_spans = chap444_elem.xpath(".//div[span]")
        bodylist = []
        for div in div_spans:
            for span in div.xpath("./span"):
                match = Reference.SINGLE_BRACKET_REC.match(span.text)
                if match:
                    body = match.group('body')
                    bodylist.append(body)
        assert len(bodylist) == 114

    def test_find_bracketed_multiple_bibliorefs_in_text(self):
        """read chunks of text and find biblioref brackets
        """
        chap444 = Path(Resources.IPCC_CHAP04, "4.4.html")
        chap444_elem = lxml.etree.parse(str(chap444))
        div_spans = chap444_elem.xpath(".//div[span]")
        total_bibliorefs = []
        for div in div_spans:
            for span in div.xpath("./span"):
                match = Reference.SINGLE_BRACKET_REC.match(span.text)
                if match:
                    body = match.group('body')
                    bibliorefs = Biblioref.create_refs_from_biblioref_string(body)
                    for biblioref in bibliorefs:
                        total_bibliorefs.append(biblioref)
        assert len(total_bibliorefs) == 103
        assert str(bibliorefs[0]) == 'Newell and  Mulvaney 2013 => Newell| and  Mulvaney |2013'
        assert str(bibliorefs[1]) == 'Miller and Richter 2014 => Miller| and Richter |2014'

    def test_make_biblioref_manager(self):
        """read chunks of text and find biblioref brackets
        """
        chap444 = Path(Resources.IPCC_CHAP04, "4.4.html")
        bibliorefs = self.make_bibliorefs(chap444)
        counter = Counter()
        for biblioref in bibliorefs:
            ref = biblioref.first
            if not ref in counter:
                counter[ref] = 0
            counter[ref] += 1
        assert len(counter) == 86
        assert counter["IPCC"] == 6
        assert counter['Bindoff'] == 5
        assert counter['de Coninck'] == 2

    def test_exceptions_biblio_ref_in_span(self):
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
            ref.iterate_spans_until_doi_found()
        chap4_dir = Path(Resources.TEMP_DIR, "ipcc_html", "chapter04")
        if not chap4_dir.exists():
            chap4_dir.mkdir()
        outpath = Path(chap4_dir, "ref_doi.html")
        ref_elem.write(str(outpath))

    def test_make_reference_class(self):
        """reads a references file and creates class"""

        ami_html = AmiHtml()
        ref_path = Path(Resources.IPCC_CHAP04, "references.html")
        assert ref_path.exists()
        ref_elem = lxml.etree.parse(str(ref_path))
        ref_divs = ref_elem.xpath("body/div")
        assert len(ref_divs) == 1316

        for div in ref_divs:
            ref = Reference.create_ref_from_div(div)
            spans = div.xpath("./span")
            ref.iterate_spans_until_doi_found()
        chap4_dir = Path(Resources.TEMP_DIR, "ipcc_html", "chapter04")
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
        match = Reference.SINGLE_BRACKET_REC.match(text)
        assert match
        assert len(match.groups()) == 3
        assert match.group(0) == "prefix the (bracketed) string postfix"
        assert match.group(1) == "prefix the "
        assert match.group(2) == "bracketed"
        assert match.group(3) == " string postfix"

        pref_span = self.add_sibling_after(H_SPAN, span, replace=True, copy_atts=True, text=match.group(1))
        target_span = self.add_sibling_after(H_SPAN, pref_span, copy_atts=True, text=match.group(2))
        post_span = self.add_sibling_after(H_SPAN, target_span, text=match.group(3))

        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               "<div><span class=\"foo\">prefix the </span><span class=\"foo\">bracketed</span><span> string postfix</span></div>"

    def test_split_matched_string_in_span(self):
        """split string in span into 3 using regex"""
        div_elem = lxml.etree.fromstring("<div><span class='foo'>prefix the (bracketed) string postfix</span></div>")
        span = div_elem.xpath("./span")[0]

        re_compile = Reference.SINGLE_BRACKET_REC
        spans = self.split_span_at_match(span, re_compile)
        assert spans[0] is not None
        assert spans[1] is not None
        assert spans[2] is not None

        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               "<div><span class=\"foo\">prefix the </span><span class=\"foo\">bracketed</span><span class=\"foo\"> string postfix</span></div>"

        # no leading string
        div_elem = lxml.etree.fromstring("<div><span class='foo'>(bracketed) string postfix</span></div>")
        span = div_elem.xpath("./span")[0]
        spans = self.split_span_at_match(span, re_compile)
        assert spans[0] is None
        assert spans[1] is not None
        assert spans[2] is not None

        # no trailing string
        div_elem = lxml.etree.fromstring("<div><span class='foo'>prefix the (bracketed)</span></div>")
        span = div_elem.xpath("./span")[0]
        spans = self.split_span_at_match(span, re_compile)
        assert spans[0] is not None
        assert spans[1] is not None
        assert spans[2] is None

        # no leading or trailing string
        div_elem = lxml.etree.fromstring("<div><span class='foo'>(bracketed)</span></div>")
        span = div_elem.xpath("./span")[0]
        spans = self.split_span_at_match(span, re_compile)
        assert spans[0] is None
        assert spans[1] is not None
        assert spans[2] is None


    def test_split_matched_string_in_span_recursively(self):
        """split string in span into 2n+1 using regex"""
        div_elem = lxml.etree.fromstring("<div><span class='foo'>prefix the (bracketed) and more (brackets) string postfix </span></div>")
        span = div_elem.xpath("./span")[0]

        re_compile = Reference.SINGLE_BRACKET_REC
        self.split_span_at_match(span, re_compile, recurse=True)

        assert lxml.etree.tostring(div_elem).decode("UTF-8") == \
               "<div><span class=\"foo\">prefix the </span><span class=\"foo\">bracketed</span>" \
               "<span class=\"foo\"> and more </span><span class=\"foo\">brackets</span>" \
               "<span class=\"foo\"> string postfix </span></div>"


    # ========================================

    def split_span_at_match(self, span, re_compile, copy_atts=True, recurse=True):
        """splits a span into 3 components by regex match
        :param span: span to split
        :param re_compile: compiled regex to split span
        :param copy_atts: if True copy atts from span
        :param recurse: if True rests span to trailing span and reanlyses until no more match
        :return: list of 3 spans; if spans[2] is not None it's available for recursion)
        """
        assert span is not None and span.text
        match = re_compile.match(span.text)
        spans = [None, None, None]
        if match:
            assert len(match.groups()) == 3  # some may be empty strings
            if match.group(1) != "":         # don't add empty string
                span = self.add_sibling_after(H_SPAN, span, replace=True, copy_atts=copy_atts, text=match.group(1))
                spans[0] = span
            spans[1] = self.add_sibling_after(H_SPAN, span, copy_atts=copy_atts, text=match.group(2))
            if match.group(3) != "":         # don't add empty string
                spans[2] = self.add_sibling_after(H_SPAN, spans[1], copy_atts=copy_atts, text=match.group(3))
                if recurse:
                    self.split_span_at_match(spans[2], re_compile, copy_atts=copy_atts, recurse=recurse)
        return spans

    def make_bibliorefs(self, file):
        chap444_elem = lxml.etree.parse(str(file))
        div_spans = chap444_elem.xpath(".//div[span]")
        total_bibliorefs = []
        for div in div_spans:
            for span in div.xpath("./span"):
                match = Reference.SINGLE_BRACKET_REC.match(span.text)
                if match:
                    body = match.group('body')
                    bibliorefs = Biblioref.create_refs_from_biblioref_string(body)
                    for biblioref in bibliorefs:
                        total_bibliorefs.append(biblioref)
        return total_bibliorefs

    def add_sibling_after(self, tag, anchor_elem, replace=False, copy_atts=False, text=None):
        """adds new trailing sibling of anchor_elem with tag
        :param tag: tag for new elements
        :param anchor_elem: reference element, must have a parent
        :param replace: if True, remove anchor element
        :param copy_atts: copy attributes from anchor
        :param text: if not None add text to new element
        :return: new sibling with optional ayytributes and text



        """

        assert anchor_elem is not None
        assert tag
        parent = anchor_elem.getparent()
        assert parent, f"No parent for anchor_elem"
        sibling = lxml.etree.SubElement(parent, tag)
        if copy_atts:
            for k,v in anchor_elem.attrib.items():
                sibling.attrib[k] = v
        anchor_elem.addnext(sibling)
        if text:
            sibling.text = text
        if replace:
            parent.remove(anchor_elem)
        return sibling

