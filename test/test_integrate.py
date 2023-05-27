from pathlib import Path

import lxml

from py4ami.ami_html import HtmlGroup
from py4ami.ami_pdf import AmiPDFPlumber
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


class AmiIntegrateTest(AmiAnyTest):



    def test_chapter_toolchain_chapters_HACKATHON(self):
        total_pages = "total_pages"
        stem = total_pages
        group_stem = "groups"
        pages = "pages/"   # maybe "" in some dirs
        docs = [
            Path(SC_OPEN_DOC_DIR, "SR21914094338.pdf"),
            # Path(SC_OPEN_DOC_DIR, "Phd_thesis_granceri_pdfA.pdf"),
            # Path(SC_OPEN_DOC_DIR, "Malmo_onyok.pdf"),
            # Path(SC_OPEN_DOC_DIR, "Guo_Ying.pdf"),
            # Path(SC_OPEN_DOC_DIR, "skarin.pdf"),
            # Path(SC_OPEN_DOC_DIR, "hampton.pdf"),
            # Path(SC_OPEN_DOC_DIR, "sustainable_livelihoods.pdf"),
            # Path(IPBES_DIR, "ipbes_global_assessment_report_summary_for_policymakers.pdf"),
            # Path(IPBES_DIR, "2020 IPBES GLOBAL REPORT (CHAPTER 1)_V5_SINGLE.pdf"),
            # Path(MISC_DIR, "2502872.pdf"),
            # Path(AR6_DIR, "syr", "lr", "fulltext.pdf"),
        ]
        section_regexes = [
            ("section",
             "\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References|\d+\.\d+)\s*.*"),
            # 7.1 Introductiom
            ("sub_section", "(?P<id>FAQ \d+\.\d+|\d+\.\d+\.\d+)\s.*"),  # 7.1.2 subtitle or FAQ 7.1 subtitle
            ("sub_sub_section", "(?P<id>\d+\.\d+\.\d+\.\d+)\s*.*")  # 7.1.2.3 subsubtitle
        ]
        for input_pdf in docs:
            self.convert_to_html(group_stem, input_pdf, section_regexes, total_pages, debug=True, svg_dir=Path(Resources.TEMP_DIR, "svg_debug"))

    def convert_to_html(self, group_stem, input_pdf, section_regexes, total_pages, write=True, debug=False, svg_dir=None):
        print(f"\n==================== {input_pdf} ==================")
        if input_pdf.exists():
            stem = input_pdf.stem
            outdir = Path(input_pdf.parent, stem)
            ami_pdfplumber = AmiPDFPlumber()
            ami_pdfplumber.create_html_pages(input_pdf, outdir, debug=debug, outstem=total_pages, svg_dir=svg_dir)

            outfile = Path(outdir, "fulltext_final.html")
            input_html_path = Path(outdir, f"{total_pages}.html")
            # self.annotate_div_spans_write_final_html(input_html_path, outfile)
            html_elem = lxml.etree.parse(input_html_path)

            HtmlGroup.make_hierarchical_sections_KEY(
                html_elem, group_stem, section_regexes=section_regexes, outdir=outdir)

    pass