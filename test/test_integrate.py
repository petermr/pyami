import glob
import logging
import re
import time
from pathlib import Path
from urllib import request

import lxml
import pdfplumber
import requests

# from py4ami.ami_pdf import AmiPDFPlumber, AmiPlumberJson, PDFDebug, TextStyle, AmiPage
# from py4ami.ami_pdf import AmiPage
from py4ami.xml_lib import XmlLib, HtmlLib
from py4ami.ami_html import HtmlUtil
from py4ami.ami_html import AmiSpan
from py4ami.ami_html import HtmlStyle
from py4ami.ami_html import HtmlGroup
from py4ami.ami_html import P_FONTNAME, P_HEIGHT, P_STROKING_COLOR, P_NON_STROKING_COLOR, P_TEXT

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


def get_ipcc_regexes(front_back):
    section_regexes = [
        # C: Adaptation...
        ("section",
         #                f"\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References|(?:(?:[A-G]|\d+)[\.:]\d+\s+[A-Z]).*"),
         fr"\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References"
         fr"|(?:[A-Z]|\d+)[.:]\d*)\s+[A-Z].*"),
        # 7.1 Introduction
        ("sub_section",
         fr"(?P<id>FAQ \d+\.\d+"
         fr"|(?:\d+\.\d+"
         fr"|[A-Z]\.\d+)"
         fr"\.\d+)"
         fr"\s+[A-Z]*"),  # 7.1.2 subtitle or FAQ 7.1 subtitle D.1.2 Subtitle
        ("sub_sub_section",
         fr"(?P<id>"
         fr"(?:\d+\.\d+\.\d+\.\d+"  # 7.1.2.3 subsubtitle
         fr"|[A-Z]\.\d+\.\d+)"
         fr")\s+[A-Z].*")  # D.1.3
    ]
    section_regex_dict = {
        "num_faq": {
            "file_regex": "NEVER.*/spm/.*",  # check this
            "sub_section": fr"(?P<id>FAQ \d+\.\d+)"
        },
        "alpha_sect": {
            "file_regex": ".*(srocc).*/spm/.*",  # check this
            "desc": "sections of form 'A: Foo', 'A.1 Bar', 'A.1.2 'Baz'",
            "section": fr"\s*(?P<id>[A-Z][.:]\s+[A-Z].*)",  # A: Foo
            "sub_section": fr"\s(?P<id>[A-Z]\.\d+\.\d+)\s+[A-Z]*",  # A.1 Bar
            "sub_sub_section": fr"\s(?P<id>[A-Z]\.\d+\.\d+)\s+[A-Z]*"  # A.1.2 Plugh
        },
        "num_sect_old": {
            "file_regex": ".*NEVER.*",
            "desc": "sections of form '1. Introduction', "
                    "subsections '1.2 Bar' "
                    "subsubsections '1.2.3 Plugh'"
                    "subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
            "section": fr"\s*(?P<id>(?:{front_back}|\s*\d+[.:]?)\s+[A-Z].*",  # A: Foo
            "sub_section": fr"\s(?P<id>\d+\.\d+)\s+[A-Z].*",  # A.1 Bar
            "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*"  # A.1.2 Plugh

        },
        "num_sect": {
            "file_regex": ".*/syr/lr.*",
            "desc": "sections of form '1. Introduction', "
                    "subsections '1.2 Bar' "
                    "subsubsections '1.2.3 Plugh'"
                    "subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
            "section": fr"\s*(?P<id>{front_back})"
                       fr"|Section\s*(?P<id1>\d+):\s*[A-Z].*"
                       fr"|\s*(?P<id2>\d+)\.\s+[A-Z].*",  # A: Foo
            "sub_section": fr"\s*(?P<id>\d+\.\d+)\s+[A-Z].*",  # 1.1 Bar
            "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*"  # A.1.2 Plugh

        },
        "num_sect_new": {
            "file_regex": fr"NEW.*/syr/lr.*",
            "sections": {
                "desc": f"sections of form '1. Introduction', "
                        f"subsections '1.2 Bar' "
                        f"subsubsections '1.2.3 Plugh'"
                        f"subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                "section": {
                    "desc": "sections of form '1. Introduction' ",
                    "regex": fr"\s*(?P<id>{front_back}|\s*\d+[.:]?)\s+[A-Z].*",  # A: Foo
                },
                "sub_section": {
                    "desc": "sections of form ''1.2 Bar' ",
                    "regex": fr"\s(?P<id>\d+\.\d+)\s+[A-Z].*",  # A.1 Bar
                },
                "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*",  # A.1.2 Plugh
            },
            "references": "dummy"

        },
    }
    return section_regex_dict, section_regexes


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
    Path(AR6_DIR, "syr", "lr", "fulltext.pdf"),
    # Path(AR6_DIR, "syr", "spm", "fulltext.pdf"),
    #
    # Path(AR6_DIR, "wg1", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg1", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg1", "faqs", "faqs.pdf"),
    # Path(AR6_DIR, "wg1", "chapters/*.pdf" ),
    # Path(AR6_DIR, "wg1", "annexes/*.pdf"),
    #
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


class HtmlGenerator:

    # class HtmlGenerator

    @classmethod
    def run_section_regexes(cls, group_stem, input_pdf, section_regexes, total_pages, use_svg):
        path = Path(input_pdf)
        if not path.exists():
            print(f"path does not exist {path}")
            return
        print(f"section_regexes ========== {section_regexes}")

        try:
            svg_dir = Path(Path(input_pdf).parent, "svg") if use_svg else None
            cls.convert_to_html(group_stem, input_pdf, section_regexes, total_pages, debug=True, svg_dir=svg_dir,
                                max_edges=5000)
        except Exception as e:
            raise e
            # traceback.print_exc()
            # # traceback.print_exception(e)
            # print(f"*********************\nCannot read/parse {input_pdf} because {e}\n*******************")

    # class HtmlGenerator

    @classmethod
    def convert_to_html(cls, group_stem, input_pdf, section_regexes, total_pages, write=True, debug=False,
                        svg_dir=None,
                        max_edges=10000, max_lines=100):
        from py4ami.ami_pdf import AmiPDFPlumber # HORRIBLE
        input_pdf = Path(input_pdf)
        print(f"\n==================== {input_pdf} ==================")
        if not input_pdf.exists():
            raise FileExistsError(f"cannot find {input_pdf}")
        stem = input_pdf.stem
        outdir = Path(input_pdf.parent, "html", stem)
        ami_pdfplumber = AmiPDFPlumber()
        cls.create_html_pages(ami_pdfplumber, input_pdf, outdir, debug=debug, outstem=total_pages, svg_dir=svg_dir,
                              max_edges=max_edges, max_lines=max_lines)

        outfile = Path(outdir, "fulltext_final.html")
        input_html_path = Path(outdir, f"{total_pages}.html")
        # self.annotate_div_spans_write_final_html(input_html_path, outfile)
        html_elem = lxml.etree.parse(input_html_path)

        HtmlGroup.make_hierarchical_sections_KEY(
            html_elem, group_stem, section_regexes=section_regexes, outdir=outdir)
        HtmlStyle.extract_all_style_attributes_to_head(html_elem)

    # class HtmlGenerator

    @classmethod
    def create_html_pages(cls, ami_pdfplumber, input_pdf, output_page_dir, pages=None, debug=False,
                          outstem="total_pages", svg_dir=None, max_edges=10000, max_lines=100):
        from py4ami.ami_pdf import AmiPlumberJson

        pre_plumber = round(time.time(), 2)
        ami_plumber_json = ami_pdfplumber.create_ami_plumber_json(input_pdf, pages=pages)
        assert (t := type(ami_plumber_json)) is AmiPlumberJson, f"expected {t}"
        total_html = HtmlLib.create_html_with_empty_head_body()
        output_page_dir.mkdir(exist_ok=True, parents=True)
        total_html_page_body = HtmlLib.get_body(total_html)

        pre_parse = round(time.time(), 2)
        print(f"PRE {round(pre_parse - pre_plumber)}")
        ami_json_pages = list(ami_plumber_json.get_ami_json_pages())
        post_parse = round(time.time(), 2)
        print(f"PARSE {post_parse - pre_parse}")

        for i, ami_json_page in enumerate(ami_json_pages):
            page_start_time = time.time()
            print(f"==============PAGE {i + 1}================")
            html_page = cls.create_html_page(ami_pdfplumber, ami_json_page, output_page_dir, debug=debug, page_no=(i + 1),
                                             svg_dir=svg_dir,
                                             max_edges=max_edges, max_lines=max_lines)
            page_end_time = time.time()
            if html_page is not None:
                body_elems = HtmlLib.get_body(html_page).xpath("*")
                for body_elem in body_elems:
                    total_html_page_body.append(body_elem)
            total_page_time = round(time.time(), 2)
            page_time = round(page_end_time - page_start_time, 2)
            html_time = round(total_page_time - page_end_time, 2)
            if page_time > 1 or html_time > 1:
                print(f"=====================\nLONG PARSE  create_page {page_time} {html_time}\n====================")

        if debug:
            cls._check_html_pages(ami_json_pages, output_page_dir)

        path = Path(output_page_dir, f"{outstem}.html")
        HtmlStyle.add_head_styles(
            total_html,
            [
                ("div", [("border", "red solid 0.5px")]),
                ("span", [("border", "blue dotted 0.5px")]),
            ]
        )
        XmlLib.write_xml(total_html, path, debug=debug)

    # class HtmlGenerator

    @classmethod
    def _check_html_pages(cls, ami_json_pages, output_page_dir):
        """checks that HTML can be parsed (not normally necessary)"""
        for i, _ in enumerate(ami_json_pages):
            page_file = Path(output_page_dir, f"page_{i + 1}.html")
            try:
                html_elem = lxml.etree.parse(str(page_file))
            except Exception as e:
                print(f"could not read XML {page_file} because {e}")

    @classmethod
    def create_html_page(cls, ami_plumber, ami_json_page, output_page_dir, debug=False, page_no=None, svg_dir=None, max_edges=10000,
                         max_lines=100):
        from py4ami.ami_pdf import PDFDebug

        if debug:
            t1 = time.time()
            line_div, curve_div, table_div, svg = ami_json_page.create_non_text_html(svg_dir=svg_dir,
                                                                                     max_edges=max_edges,
                                                                                     max_lines=max_lines)
            t2 = time.time()
            print(f"NON TEXT {round(t2 - t1, 2)}")
            if len(tables := table_div.xpath("*")):
                table_html = HtmlLib.create_html_with_empty_head_body()
                HtmlLib.get_body(table_html).append(table_div)
                HtmlLib.write_html_file(table_div, Path(output_page_dir, f"tables_{page_no}.html"), debug=True)

            if svg_dir:
                PDFDebug().print_curves(ami_json_page.plumber_page_dict, svg_dir=svg_dir, page_no=page_no)
                if len(svg.xpath("*")) > 1:  # skip if only a box
                    XmlLib.write_xml(svg, Path(svg_dir, f"table_box_{page_no}.svg"), debug=debug)

        html_page, footer_span_list, header_span_list = ami_json_page.create_html_page_and_header_footer(ami_plumber)
        if debug:
            ami_json_page.print_header_footer_lists(footer_span_list, header_span_list)
        try:
            path = Path(output_page_dir, f"page_{page_no}.html")
            XmlLib.write_xml(html_page, path, debug=debug)
        except Exception as e:
            print(f"*******Cannot serialize page (probably strange fonts)******page{page_no} {e}")
            html_page = None
        return html_page

    @classmethod
    # TODO should be new class
    def chars_to_spans_using_pdfplumber(cls, bbox, input_pdf, page_no):
        from py4ami.ami_pdf import AmiPage
        from py4ami.ami_html import H_BODY, H_DIV
        from py4ami.ami_pdf import TextStyle

        with pdfplumber.open(input_pdf) as pdf:
            pdf_page = pdf.pages[page_no]
            ami_page = AmiPage()
            # print(f"crop: {page0.cropbox} media {page0.mediabox}, bbox {page0.bbox}")
            # print(f"rotation: {page0.rotation} doctop {page0.initial_doctop}")
            # print(f"width {page0.width} height {page0.height}")
            # print(f"text {page0.extract_text()[:2]}")
            # print(f"words {page0.extract_words()[:3]}")
            #
            # print(f"char {page0.chars[:1]}")
            span = None
            span_list = []
            maxchars = 999999
            ndec_coord = 3  # decimals for coords
            ndec_fontsize = 2
            html = HtmlUtil.create_skeleton_html()
            top_div = lxml.etree.SubElement(html.xpath(H_BODY)[0], H_DIV)
            top_div.attrib["class"] = "top"
            for ch in pdf_page.chars[:maxchars]:
                if AmiPage.skip_rotated_text(ch):
                    continue
                x0, x1, y0, y1 = AmiPage.get_xy_tuple(ch, ndec_coord)
                if bbox and not bbox.contains_point((x0, y0)):
                    # print(f" outside box: {x0, y0}")
                    continue

                text_style = TextStyle()
                text_style.set_font_family(ch.get(P_FONTNAME))
                text_style.set_font_size(ch.get(P_HEIGHT), ndec=ndec_fontsize)
                text_style.stroke = ch.get(P_STROKING_COLOR)
                text_style.fill = ch.get(P_NON_STROKING_COLOR)

                # style or y0 changes
                if not span or not span.text_style or span.text_style != text_style or span.y0 != y0:
                    # cls.debug_span_changed(span, text_style, y0)
                    span = AmiSpan()
                    span_list.append(span)
                    span.text_style = text_style
                    span.y0 = y0
                    span.x0 = x0  # set left x
                span.x1 = x1  # update right x, including width
                span.string += ch.get(P_TEXT)

            # top_div = lxml.etree.Element(H_DIV)
            div = lxml.etree.SubElement(top_div, H_DIV)
            last_span = None
            for span in span_list:
                if last_span is None or last_span.y0 != span.y0:
                    div = lxml.etree.SubElement(top_div, H_DIV)
                last_span = span
                span.create_and_add_to(div)
        for ch in pdf_page.chars[:maxchars]:
            col = ch.get('non_stroking_color')
            if col:
                logging.debug(f"txt {ch.get('text')} : col {col}")
        # print(f"HTML {html}")
        return html


class AmiIntegrateTest(AmiAnyTest):

    def test_chapter_toolchain_chapters_HACKATHON(self):
        total_pages = "total_pages"
        stem = total_pages
        group_stem = "groups"
        use_svg = True  # output surves as svg?
        pages = "pages/"  # maybe "" in some dirs
        front_back = "Table of Contents|Frequently Asked Questions|Executive Summary|References"
        section_regex_dict, section_regexes = get_ipcc_regexes(front_back)
        old_style = False or True

        input_pdfs = []
        for input_pdf in INPUT_PDFS:
            input_pdfs.extend(glob.glob(str(input_pdf)))
        print(f"globbed pdfs {input_pdfs}")

        if old_style:
            for input_pdf in input_pdfs:
                HtmlGenerator.run_section_regexes(group_stem, input_pdf, section_regexes, total_pages, use_svg)
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
                        HtmlGenerator.run_section_regexes(group_stem, input_pdf, section_regexes_new, total_pages,
                                                          use_svg)
                    # raise e

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
