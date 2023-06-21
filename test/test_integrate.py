import glob
import re
import unittest
from pathlib import Path
from urllib import request

import lxml
import pandas as pd
import requests

from py4ami.ami_html import HtmlStyle
from py4ami.ami_integrate import HtmlGenerator
from py4ami.ipcc import IPCCSections, IPCCCommand
from py4ami.wikimedia import WikidataLookup
from py4ami.xml_lib import HtmlLib

from test.resources import Resources
from test.test_all import AmiAnyTest

"""
tests 'complete processes ; also aimed at testing different document types
may cross directories
"""
SEMANTIC_CLIMATE = "https://rawgithubuser.com/petermr/semanticClimate"
IPBES = SEMANTIC_CLIMATE + "/" + "ipbes"

SEMANTIC_CLIMATE_DIR = Path(Resources.LOCAL_PROJECT_DIR, "semanticClimate")
MISC_DIR = Path(SEMANTIC_CLIMATE_DIR, "misc")
SC_OPEN_DOC_DIR = Path(SEMANTIC_CLIMATE_DIR, "openDocuments")
IPBES_DIR = Path(SEMANTIC_CLIMATE_DIR, "ipbes")
AR6_DIR = Path(SEMANTIC_CLIMATE_DIR, "ipcc", "ar6")


INPUT_PDFS = [
    # Path(SC_OPEN_DOC_DIR, "SR21914094338.pdf"),
    # Path(SC_OPEN_DOC_DIR, "Phd_thesis_granceri_pdfA.pdf"),
    # Path(SC_OPEN_DOC_DIR, "Malmo_onyok.pdf"),
    # Path(SC_OPEN_DOC_DIR, "Guo_Ying.pdf"),
    # Path(SC_OPEN_DOC_DIR, "skarin.pdf"),
    # Path(SC_OPEN_DOC_DIR, "hampton.pdf"),
    # Path(SC_OPEN_DOC_DIR, "sustainable_livelihoods.pdf"),
    # Path(IPBES_DIR, "ipbes_global_assessment_report_summary_for_policymakers.pdf"), # something wrong with IPBES
    # Path(IPBES_DIR, "2020 IPBES GLOBAL REPORT (CHAPTER 1)_V5_SINGLE.pdf"),
    # # Path(MISC_DIR, "2502872.pdf"),
    # Path(AR6_DIR, "misc", "AR6_FS_review_process.pdf"),
    # Path(AR6_DIR, "misc", "2018-03-Preface-3.pdf"),
    # Path(AR6_DIR, "syr", "lr", "fulltext.pdf"),
    # Path(AR6_DIR, "syr", "spm", "fulltext.pdf"),
    #
    # Path(AR6_DIR, "wg1", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg1", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg1", "faqs", "faqs.pdf"),
    # Path(AR6_DIR, "wg1", "chapters/*.pdf" ),
    # Path(AR6_DIR, "wg1", "annexes/*.pdf"), # repeat
    # Path(AR6_DIR, "wg1", "annexes", "glossary.pdf")

    # Path(AR6_DIR, "wg2", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg2", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg2", "chapters/*.pdf"),
    # Path(AR6_DIR, "wg2", "faqs/*.pdf"),

    # Path(AR6_DIR, "wg3", "annexes/*.pdf"),
    # Path(AR6_DIR, "wg3", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg3", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg3", "Chapter07.pdf"),

    # Path(AR6_DIR, "srocc", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "srocc", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "srocc", "chapters", "Ch02.pdf"),
    # Path(AR6_DIR, "srocc", "annexes/*.pdf"),
    #
    # Path(AR6_DIR, "sr15", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "sr15", "glossary", "fulltext.pdf"),
    #
    Path(AR6_DIR, "srccl", "chapters", "Chapter05.pdf"),
    # Path(AR6_DIR, "srccl", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "srccl", "ts", "fulltext.pdf"),
]


def annotate_glossary(glossary_html, style_class, link_class):
    if not Path(glossary_html).exists():
        print(f"Glossary does not exists {glossary_html}")
        return
    glossary_elem = lxml.etree.parse(glossary_html)
    annotate_lead_entries(glossary_elem, style_class, use_bold=True)

    add_links_to_terms(glossary_elem, link_class)

    HtmlLib.write_html_file(glossary_elem, Path(Path(glossary_html).parent, "annotated_glossary.html"))
    return glossary_elem


def add_links_to_terms(glossary_elem, link_class):
    unlinked_set = set()
    link_spans = glossary_elem.xpath(f".//div/span[@class='{link_class}']")
    link_spans = glossary_elem.xpath(f".//div/span")
    link_spans = [span for span in link_spans if HtmlStyle.is_bold(span)]
    div_bolds = [div for div in glossary_elem.xpath(".//div")]
    for div in div_bolds:
        spans = div.xpath("./span")
        if len(spans) > 0 and HtmlStyle.is_bold(spans[0]):
            for span in spans[1:]:
                if HtmlStyle.is_italic(span):
                    add_link(glossary_elem, span, unlinked_set)
            print(f"is bold {spans[0].text}")

    attnames = ["style", "x0", "x1", "y0", "y1", "width", "top", "left", "right"]
    add_inline_links(attnames, glossary_elem, link_class, link_spans, unlinked_set)

    print(f"unlinked {len(unlinked_set)} {unlinked_set}")


def add_inline_links(attnames, glossary_elem, link_class, link_spans, unlinked_set):
    for span in link_spans:
        delete_atts(attnames, span)
        if span.attrib.get("class") == link_class:
            add_link(glossary_elem, span, unlinked_set)


def add_link(glossary_elem, span, unlinked_set):
    ref = normalize_id(span.text)
    targets = glossary_elem.xpath(f".//div/a[@class='lead' and @name='{ref}']")
    if len(targets) == 1:
        a_elem = lxml.etree.SubElement(span, "a")
        a_elem.attrib["href"] = "#" + ref
        a_elem.text = span.text
        span.text = ""
        print(f"... {ref}")
    elif len(targets) > 0:
        print(f"multiple targets {ref}")
    else:
        span.attrib["style"] = "color: red"
        unlinked_set.add(ref)


def delete_atts(attnames, span):
    for att in attnames:
        attval = span.attrib.get(att)
        if attval:
            del (span.attrib[att])


def annotate_lead_entries(glossary_elem, style_class, use_bold=False):
    if use_bold:
        div_entries = [div for div in glossary_elem.xpath(f".//div[span]") if HtmlStyle.is_bold(div.xpath('./span')[0])]
    else:
        div_entries = glossary_elem.xpath(f".//div[span[@class='{style_class}']]")
    print(f"entries: {len(div_entries)}")
    for div_entry in div_entries:
        spans = div_entry.xpath('./span')
        del (spans[0].attrib["style"])
        lead_text = spans[0].text.strip()
        lead_id = normalize_id(lead_text)
        print(f"> {lead_text}")
        a_elem = lxml.etree.SubElement(div_entry, "a")
        a_elem.attrib["id"] = lead_id
        a_elem.attrib["name"] = lead_id
        a_elem.attrib["class"] = "lead"
        div_entry.insert(0, a_elem)
        a_elem.attrib["style"] = "background: #ffeeee;"
        a_elem.text = " "


def normalize_id(text):
    return None if not text else text.strip().replace(" ()@$#%^&*-+~<>,.?/:;\"'[]{}", "_").lower()

REPORTS =  [
    "wg1",
    "wg2",
    "wg3",
    "sr15",
    "srocc",
    "srccl",
]


class AmiIntegrateTest(AmiAnyTest):

    def test_chapter_toolchain_chapters_HACKATHON(self):
        front_back = "Table of Contents|Frequently Asked Questions|Executive Summary|References"
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)

        # input_pdfs = []
        # for input_pdf in INPUT_PDFS:
        #     input_pdfs.extend()

        input_pdfs = []
        for input_pdf in INPUT_PDFS:
            pdfs = glob.glob(str(input_pdf))
            input_pdfs.extend(pdfs)
        print(f"globbed pdfs {input_pdfs}")

        for input_pdf in input_pdfs:
            IPCCCommand.run_toolchain_pdf_to_structured_html(input_pdf, section_regexes)

    @unittest.skip("not yet developed nested sections")
    def test_chapter_toolchain_chapters_DEVELOP(self):
        """nested sections"""
        front_back = IPCCSections.get_major_section_names()
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)
        input_pdfs = [glob.glob(str(input_pdf)) for input_pdf in INPUT_PDFS]
        for input_pdf in input_pdfs:
            filename = str(input_pdf)
            print(f"===={filename}====")
            print(f" section_regex_dict_keys {section_regex_dict.keys()}")
            for name, rx in section_regex_dict.items():
                print(f"key {name} : {rx}")
                file_regex = rx.get('file_regex')
                if re.match(str(file_regex), filename):
                    print(f"MATCHED {name}: {file_regex}")
                    section_regexes_new = [
                        ('section', rx.get("section")),
                        ('sub_section', rx.get("sub_section")),
                        ('sub_sub_section', rx.get("sub_sub_section"))
                    ]
                    IPCCCommand.run_toolchain_pdf_to_structured_html(input_pdf, section_regexes_new)
                # raise e

    def test_small_pdf_with_styles_KEY(self):

        input_pdfs = [
            Path(AR6_DIR, "misc", "AR6_FS_review_process.pdf"),
            Path(AR6_DIR, "misc", "2018-03-Preface-3.pdf"),
        ]
        front_back = ""
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back)

        use_svg = True
        for input_pdf in input_pdfs:
            HtmlGenerator.run_section_regexes(input_pdf, section_regexes, group_stem="styles")


    def test_glossaries_KEY(self):
        """iterates over glossaries and adds internal links"""

        front_back = ""
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back)

        use_svg = True
        for report in REPORTS:
            for g_type in [
                "glossary",
                # "acronyms"
            ]:
                input_pdf = Path(AR6_DIR, report, "annexes", f"{g_type}.pdf")
                HtmlGenerator.run_section_regexes(input_pdf, section_regexes, group_stem="glossary")
                glossary_html = Path(AR6_DIR, report, "annexes", "html", "glossary", "glossary_groups.html")
                if glossary_html.exists():
                    glossary_elem = annotate_glossary(glossary_html, style_class="s1020", link_class='s100')
                    glossary_file = Path(AR6_DIR, report, "annexes", "html", "glossary", "annotated_glossary.html")
                    if glossary_file.exists():
                        annotated_glossary = lxml.etree.parse(glossary_file)

    def test_merge_glossaries_KEY(self):
        """iterates over 6 glossaries and adds internal links"""

        reports = [
            "wg1",
            "wg2",
            "wg3",
            "sr15",
            "srocc",
            "srccl",
        ]
        name_set = set()
        for report in reports:
            glossary_file = Path(AR6_DIR, report, "annexes", "html", "glossary", "annotated_glossary.html")
            if not glossary_file.exists():
                print(f"files does not exist {glossary_file}")
                continue
            glossary_elem = lxml.etree.parse(str(glossary_file))
            head_divs = glossary_elem.xpath("//div[span]")
            for head_div in head_divs:
                name = head_div.xpath("span")[0].text
                if not name:
                    continue
                name = name.strip()
                if name[:2] != "AI" and name[:2] != "AV" and name[:1] != "(" and name[:5] != "[Note":
                    name_set.add(name)
            print (f"entries {len(head_divs)}")
        print(f"names {len(name_set)}")
        sorted_names = sorted(name_set)
        for name in sorted_names:
            print(f"> {name}")


    def test_lookup_wikidata(self):
        max_entries = 50
        report = "wg1"
        annotated_glossary = lxml.etree.parse(
            Path(AR6_DIR, report, "annexes", "html", "glossary", "annotated_glossary.html"))
        lead_divs = annotated_glossary.xpath(".//div[a]")
        for div in lead_divs[:max_entries]:
            term = div.xpath("./a")[0].attrib["name"]
            term = div.xpath("span")[0].text
            qitem0, desc, wikidata_hits = WikidataLookup().lookup_wikidata(term)
            print(f"{term}: qitem {qitem0} desc {desc}")

    def test_extract_authors(self):
        """
        extract authors from chapters using regex
        """
        html_dir = Path(AR6_DIR, "srccl", "chapters", "html", "Chapter05")
        filename = "groups_groups.html"
        author_roles = IPCCCommand.get_author_roles()
        df = IPCCCommand.extract_authors_and_roles(filename, author_roles, html_dir)
        print(f"df {df}")


    def test_github_hyperlinks(self):
        """tests that Github links can retrieve and display content"""
        SC_REPO = "https://github.com/petermr/semanticClimate"
        GITHUB_DISPLAY = "https://htmlpreview.github.io/?"
        BLOB_MAIN = "blob/main"
        test_url = f"{SC_REPO}/{BLOB_MAIN}/test.html"

        print(f"test: {test_url}")

        with request.urlopen(test_url) as f:
            s = f.read().decode()  # the decode turns the bytes into a string for printing
            # this is NOT the raw content, but wrapped to display as raw htnl
        assert " <title>semanticClimate/test.html at main · petermr/semanticClimate · GitHub</title>" in s

        # this is the HTML for web display
        display_url = f"{GITHUB_DISPLAY}{SC_REPO}/{BLOB_MAIN}/test.html"
        print(f"display url: {display_url}")
        try:
            page = requests.get(display_url)
            content = page.content
            print(content)
            html = lxml.html.fromstring(content)
        except OSError as e:
            print(f"error {e}")
        body = html.xpath("/html/body")[0]
        print(f"body {lxml.etree.tostring(body)}")
        assert body is not None
