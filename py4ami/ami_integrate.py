import logging
from pathlib import Path

import lxml
import pdfplumber

from py4ami.ami_html import HtmlUtil, P_FONTNAME, P_HEIGHT, P_STROKING_COLOR, P_NON_STROKING_COLOR, AmiSpan, P_TEXT, \
    HtmlGroup, HtmlStyle
from py4ami.xml_lib import HtmlLib, XmlLib


class HtmlGenerator:

    # class HtmlGenerator

    @classmethod
    def run_section_regexes(cls, input_pdf, section_regexes, total_pages="total_pages", group_stem="groups", use_svg=True):
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
                        max_edges=10000, max_lines=10):
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

        pre_plumber = HtmlGenerator.pmr_time()
        ami_plumber_json = ami_pdfplumber.create_ami_plumber_json(input_pdf, pages=pages)
        assert (t := type(ami_plumber_json)) is AmiPlumberJson, f"expected {t}"
        total_html = HtmlLib.create_html_with_empty_head_body()
        output_page_dir.mkdir(exist_ok=True, parents=True)
        total_html_page_body = HtmlLib.get_body(total_html)

        pre_parse = HtmlGenerator.pmr_time()
        print(f"PRE {round(pre_parse - pre_plumber)}")
        ami_json_pages = list(ami_plumber_json.get_ami_json_pages())
        post_parse = HtmlGenerator.pmr_time()
        print(f"PARSE {post_parse - pre_parse}")

        for i, ami_json_page in enumerate(ami_json_pages):
            page_start_time = HtmlGenerator.pmr_time()
            print(f"==============PAGE {i + 1}================")
            html_page = cls.create_html_page(ami_pdfplumber, ami_json_page, output_page_dir, debug=debug, page_no=(i + 1),
                                             svg_dir=svg_dir,
                                             max_edges=max_edges, max_lines=max_lines)
            page_end_time = HtmlGenerator.pmr_time()
            if html_page is not None:
                body_elems = HtmlLib.get_body(html_page).xpath("*")
                for body_elem in body_elems:
                    total_html_page_body.append(body_elem)
            total_page_time = HtmlGenerator.pmr_time()
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

    @classmethod
    def pmr_time(cls, ndec=2):
        import datetime
        # return round(float(datetime.second), ndec)
        return 0

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
                         max_lines=10):
        from py4ami.ami_pdf import PDFDebug

        if debug:
            t1 = HtmlGenerator.pmr_time()
            line_div, curve_div, table_div, svg = ami_json_page.create_non_text_html(svg_dir=svg_dir,
                                                                                     max_edges=max_edges,
                                                                                     max_lines=max_lines)
            t2 = HtmlGenerator.pmr_time()
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
    # Maybe should be lower and wrapped?
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

