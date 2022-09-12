"""manages bibligraphy and related stuff"""

import lxml
import lxml.etree
import re
# local
# from py4ami.ami_html import H_A
from py4ami.util import Util


class Reference:
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
    DOI_REC = re.compile(r".*\s(doi:[^\s]*)\.")  # finds DOI string in running text

    AUTHORS_DATE_REC = re.compile(r"""
    (?P<first>((de )|(d')|(el ))?\s*[A-Z][^\s]+) # doesn't seem to do the prefixes yet
    (?P<others>.+)
    (?P<date>20\d\d[a-z]*)
    """, re.VERBOSE)

    DOI_PROTOCOL = "doi:"
    HTTPS_DOI_ORG = "https://doi.org/"

    def __init__(self):
        self.spans = []

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

    def markup_dois_in_spans(self):
        """iterates over contained spans until the doi-containing one is found
        """
        for span in self.spans:
            text = span.text
            doi_match = self.DOI_REC.match(text)
            if doi_match:
                doi_txt = doi_match.group(1)
                if self.DOI_PROTOCOL in doi_txt:
                    doi_txt = doi_txt.replace("doi:https", "https")
                    doi_txt = doi_txt.replace(self.DOI_PROTOCOL, self.HTTPS_DOI_ORG)
                    if doi_txt.startswith(self.DOI_PROTOCOL):
                        doi_txt = "https://" + doi_txt
                    print(f"doi: {doi_txt}")
                    a = lxml.etree.SubElement(span.getparent(), "a")  # to avoid circulkar import of H_A TODO

                    a.attrib["href"] = doi_txt
                    a.text = doi_txt
                    break
            else:
                # print(f"no doi: {text}")
                pass

    @classmethod
    def markup_dois_in_div_spans(cls, ref_divs):
        """creates refs and then marks up the spans
        May be rather specific to IPCC"""
        for div in ref_divs:
            ref = Reference.create_ref_from_div(div)
            spans = div.xpath("./span")
            ref.markup_dois_in_spans()



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
            bref = " ".join(brefstr.splitlines()).replace(r"\s+", " ")
            chunks = bref.split(";")
            for chunk in chunks:
                # print(f" chunk {chunk}")
                brefx = Biblioref.create_bref(chunk.strip())
                if brefx:
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

    @classmethod
    def make_bibliorefs(cls, file):
        chap444_elem = lxml.etree.parse(str(file))
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
        return total_bibliorefs

class Publication:
    CHAPTER = "Chapter"
    TECHNICAL_SUMMARY = "Technical Summary"

    @classmethod
    def is_chapter_or_tech_summary(cls, span_text):
        return span_text.startswith(Publication.CHAPTER) or span_text.startswith(Publication.TECHNICAL_SUMMARY)
