import glob
import re
from pathlib import Path
from urllib import request

import lxml
import requests

from py4ami.ami_integrate import HtmlGenerator
from py4ami.ipcc import IPCCSections

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
    Path(AR6_DIR, "wg1", "annexes", "glossary.pdf")

    # Path(AR6_DIR, "wg2", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg2", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg2", "chapters/*.pdf"),
    # Path(AR6_DIR, "wg2", "faqs/*.pdf"),

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
    # Path(AR6_DIR, "srccl", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "srccl", "ts", "fulltext.pdf"),
]


class AmiIntegrateTest(AmiAnyTest):

    def test_chapter_toolchain_chapters_HACKATHON(self):
        total_pages = "total_pages"
        stem = total_pages
        group_stem = "groups"
        use_svg = True  # output surves as svg?
        pages = "pages/"  # maybe "" in some dirs
        front_back = "Table of Contents|Frequently Asked Questions|Executive Summary|References"
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)
        old_style = False or True

        input_pdfs = []
        for input_pdf in INPUT_PDFS:
            input_pdfs.extend(glob.glob(str(input_pdf)))
        print(f"globbed pdfs {input_pdfs}")

        if old_style:
            for input_pdf in input_pdfs:
                HtmlGenerator.run_section_regexes(input_pdf, section_regexes)
        else:
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
                        HtmlGenerator.run_section_regexes(input_pdf, section_regexes_new)
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
