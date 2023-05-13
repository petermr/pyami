import copy
from pathlib import Path
import os
from lxml import etree as LXET
import requests
from urllib.request import urlopen
import lxml, lxml.etree
import logging

from py4ami.file_lib import FileLib

logging.debug("loading xml_lib")


# make leafnodes and copy remaning content as XML
TERMINAL_COPY = {
    "abstract",
    "aff",
    "article-id",
    "article-categories",
    "author-notes",
    "caption",
    "contrib-group",
    "fig",
    "history",
    "issue",
    "journal_id",
    "journal-title-group",
    "kwd-group",
    "name",
    "notes",
    "p",
    "permissions",
    "person-group",
    "pub-date",
    "publisher",
    "ref",
    "table",
    "title",
    "title-group",
    "volume",
}


TERMINALS = [
    "inline-formula",
]

TITLE = "title"

IGNORE_CHILDREN = {
    "disp-formula",
}

HTML_TAGS = {
    "italic": "i",
    "p": "p",
    "sub": "sub",
    "sup": "sup",
    "tr": "tr",
}

H_TD = "td"
H_TR = "tr"
H_TH = "th"
LINK = "link"
UTF_8 = "UTF-8"
SCRIPT = "script"
STYLESHEET = "stylesheet"
TEXT_CSS = "text/css"
TEXT_JAVASCRIPT = "text/javascript"

H_HTML = "html"
H_BODY = "body"
H_TBODY = "tbody"
H_DIV = "div"
H_TABLE = "table"
H_THEAD = "thead"
H_HEAD = "head"
H_TITLE = "title"

RESULTS = "results"

SEC_TAGS = {
    "sec",
}

LINK_TAGS = {
    "xref",
}

SECTIONS = "sections"

HTML_NS = "HTML_NS"
MATHML_NS = "MATHML_NS"
SVG_NS = "SVG_NS"
XMLNS_NS = "XMLNS_NS"
XML_NS = "XML_NS"
XLINK_NS = "XLINK_NS"

XML_LANG = "{" + XML_NS + "}" + 'lang'

NS_MAP = {
    HTML_NS: "http://www.w3.org/1999/xhtml",
    MATHML_NS: "http://www.w3.org/1998/Math/MathML",
    SVG_NS: "http://www.w3.org/2000/svg",
    XLINK_NS: "http://www.w3.org/1999/xlink",
    XML_NS: "http://www.w3.org/XML/1998/namespace",
    XMLNS_NS: "http://www.w3.org/2000/xmlns/",
}

logger = logging.getLogger("xml_lib")
logger.setLevel(logging.WARNING)
logging.debug(f"===========LOGGING {logger.level} .. {logging.DEBUG}")


class XmlLib:

    def __init__(self, file=None, section_dir=SECTIONS):
        self.max_file_len = 30
        self.file = file
        self.parent_path = None
        self.root = None
        self.logger = logging.getLogger("xmllib")
        self.section_dir = section_dir
        self.section_path = None
#         self.logger.setLevel(logging.INFO)

    def read(self, file):
        """reads XML file , saves file, and parses to self.root"""
        if file is not None:
            self.file = file
            self.parent_path = Path(file).parent.absolute()
            self.root = XmlLib.parse_xml_file_to_root(file)

    def make_sections(self, section_dir):
        """recursively traverse XML tree and write files for each terminal element"""
        self.section_dir = self.make_sections_path(section_dir)
        # indent = 0
        # filename = "1" + "_" + self.root.tag
        # self.logger.debug(" " * indent, filename)
        # subdir = os.path.join(self.section_dir, filename)
        # FileLib.force_mkdir(subdir)

        self.make_descendant_tree(self.root, self.section_dir)
        self.logger.info(
            f"wrote XML sections for {self.file} {self.section_dir}")

    @staticmethod
    def parse_xml_file_to_root(file):
        """read xml path and create root element"""
        file = str(file)  # if file is Path
        if not os.path.exists(file):
            raise IOError("path does not exist", file)
        xmlp = LXET.XMLParser(encoding=UTF_8)
        element_tree = LXET.parse(file, xmlp)
        root = element_tree.getroot()
        return root

    @staticmethod
    def parse_xml_string_to_root(xml):
        """read xml string and parse to root element"""
        from io import StringIO
        tree = LXET.parse(StringIO(xml), LXET.XMLParser(ns_clean=True))
        return tree.getroot()

    @classmethod
    def parse_url_to_tree(cls, url):
        """parses URL to lxml tree
        :param url: to parse
        :return: lxml tree"""
        with urlopen(url) as f:
            tree = lxml.etree.parse(f)
            """
    def get_html(url, retry_count=0):
    try:
        request = Request(url)
        response = urlopen(request)
        html = response.read()
    except ConectionResetError as e:
        if retry_count == MAX_RETRIES:
            raise e
        time.sleep(for_some_time)
        get_html(url, retry_count + 1)
        """
        return tree


    def make_sections_path(self, section_dir):
        self.section_path = os.path.join(self.parent_path, section_dir)
        if not os.path.exists(self.section_path):
            FileLib.force_mkdir(self.section_path)
        return self.section_path

    def make_descendant_tree(self, elem, outdir):

        self.logger.setLevel(logging.INFO)
        if elem.tag in TERMINALS:
            self.logger.debug("skipped ", elem.tag)
            return
        TERMINAL = "T_"
        IGNORE = "I_"
        children = list(elem)
        self.logger.debug(f"children> {len(children)} .. {self.logger.level}")
        isect = 0
        for child in children:
            if "ProcessingInstruction" in str(type(child)):
                # print("PI", child)
                continue
            if "Comment" in str(type(child)):
                continue
            flag = ""
            child_child_count = len(list(child))
            if child.tag in TERMINAL_COPY or child_child_count == 0:
                flag = TERMINAL
            elif child.tag in IGNORE_CHILDREN:
                flag = IGNORE

            title = child.tag
            if child.tag in SEC_TAGS:
                title = XmlLib.get_sec_title(child)

            if flag == IGNORE:
                title = flag + title
            filename = str(
                isect) + "_" + FileLib.punct2underscore(title).lower()[:self.max_file_len]

            if flag == TERMINAL:
                xml_string = LXET.tostring(child)
                filename1 = os.path.join(outdir, filename + '.xml')
                self.logger.setLevel(logging.INFO)
                self.logger.debug(f"writing dbg {filename1}")
                try:
                    with open(filename1, "wb") as f:
                        f.write(xml_string)
                except Exception:
                    print(f"cannot write {filename1}")
            else:
                subdir = os.path.join(outdir, filename)
                # creates empty dirx, may be bad idea
                FileLib.force_mkdir(subdir)
                if flag == "":
                    self.logger.debug(f">> {title} {child}")
                    self.make_descendant_tree(child, subdir)
            isect += 1

    @staticmethod
    def get_sec_title(sec):
        """get title of JATS section

        :sec: section (normally sec element
        """
        title = None
        for elem in list(sec):
            if elem.tag == TITLE:
                title = elem.text
                break

        if title is None:
            # don't know where the 'xml_file' comes from...
            if not hasattr(sec, "xml_file"):
                title = "UNKNOWN"
            else:
                title = "?_" + str(sec["xml_file"][:20])
        title = FileLib.punct2underscore(title)
        return title

    @staticmethod
    def remove_all(elem, xpath):
        for el in elem.xpath(xpath):
            el.getparent().remove(el)

    @staticmethod
    def get_or_create_child(parent, tag):
        child = None
        if parent is not None:
            child = parent.find(tag)
            if child is None:
                child = LXET.SubElement(parent, tag)
        return child

    @classmethod
    def get_text(cls, node):
        """
        get text children as string
        """
        return ''.join(node.itertext())

    @staticmethod
    def add_UTF8(html_root):
        """adds UTF8 declaration to root

        """
        from lxml import etree as LXET
        root = html_root.get_or_create_child(html_root, "head")
        LXET.SubElement(root, "meta").attrib["charset"] = "UTF-8"

    # replace nodes with text
    @staticmethod
    def replace_nodes_with_text(data, xpath, replacement):
        """replace nodes with specific text

        """
        print(data, xpath, replacement)
        tree = LXET.fromstring(data)
        for r in tree.xpath(xpath):
            XmlLib.replace_node_with_text(r, replacement)
        return tree

    @classmethod
    def replace_node_with_text(cls, r, replacement):
        print("r", r, replacement, r.tail)
        text = replacement
        if r.tail is not None:
            text += r.tail
        parent = r.getparent()
        if parent is not None:
            previous = r.getprevious()
            if previous is not None:
                previous.tail = (previous.tail or '') + text
            else:
                parent.text = (parent.text or '') + text
            parent.remove(r)

    @classmethod
    def remove_all_tags(cls, xml_string):
        """remove all tags from text

        :xml_string: string to be flattened
        :returns: flattened string
        """
        tree = LXET.fromstring(xml_string.encode("utf-8"))
        strg = LXET.tostring(tree, encoding='utf8',
                             method='text').decode("utf-8")
        return strg

    @classmethod
    def xslt_transform(cls, data, xslt_file):
        xslt_root = LXET.parse(xslt_file)
        transform = LXET.XSLT(xslt_root)
        print("XSLT log", transform.error_log)
        result_tree = transform(LXET.fromstring(data))
        assert(result_tree is not None)
        root = result_tree.getroot()
        assert(root is not None)

        return root

    @classmethod
    def xslt_transform_tostring(cls, data, xslt_file):
        root = cls.xslt_transform(data, xslt_file)
        return LXET.tostring(root).decode("UTF-8") if root is not None else None

    @classmethod
    def validate_xpath(cls, xpath):
        """
        crude syntax validation of xpath string.
        tests xpath on a trivial element
        :param xpath:
        """
        tree = lxml.etree.fromstring("<foo/>")
        try:
            tree.xpath(xpath)
        except lxml.etree.XPathEvalError as e:
            logging.error(f"bad XPath {xpath}, {e}")
            raise e


    @classmethod
    def does_element_equal_serialized_string(cls, elem, string):
        try:
            elem1 = lxml.etree.fromstring(string)
            return cls.are_elements_equal(elem, elem1)
        except:
            return False

    @classmethod
    def are_elements_equal(cls, e1, e2):
        """compares 2 elements
        :param e1:
        :param e2:
        :return: False if not equal
        """
        if type(e1) is not lxml.etree._Element or type(e2) is not lxml.etree._Element:
            raise ValueError(f" not a pair of XML elements {e1} {e2}")
        if e1.tag != e2.tag: return False
        if e1.text != e2.text: return False
        if e1.tail != e2.tail: return False
        if e1.attrib != e2.attrib: return False
        if len(e1) != len(e2): return False
        return all(cls.are_elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    @classmethod
    def write_xml(cls, elem, path, encoding="UTF-8"):
        """
        Writes XML to file
        :param elem: xml element to write
        :param path: path to write to
        :except: bad encoding
        The use of encoding='UTF-8' is because lxml has a bug in some releases
        """
        with open(path, "w") as f:
            try:
                # this solves some problems but not unknown font encodings
                # xmlstr = lxml.etree.tostring(elem, encoding='UTF-8').decode(encoding)

                xmlstr = lxml.etree.tostring(elem).decode(encoding)
            except Exception as e:
                raise ValueError(f"****** cannot decode XML: {e} *******")
            try:
                f.write(xmlstr)
            except Exception as ee:
                raise Exception(f"cannot write XMLString {e}")


    @classmethod
    def remove_attribute(cls, elem, att):
        """
        removes at attribute (by name) if it exists
        :param elem: element with the attribute
        :param att: att_name to delete
        """
        if elem is not None and att in elem.attrib:
            del elem.attrib[att]

    @classmethod
    def set_attname_value(cls, elem, attname, value):
        """
        set attribute, if value==None remove attribute
        :param elem: element with attribute
        :param attname: attribute name
        :param value: attribute value; if "" or None remove attribute
        """
        if value is None or value == "":
            XmlLib.remove_attribute(elem, attname)
        else:
            elem.attrib[attname] = value

    @classmethod
    def remove_element(cls, elem):
        """cnvenience method to remove element from tree
        :param elem: elem to be removed
        no-op if elem or its parent is None"""
        # does not remove tail (I don't think)
        if elem is not None:
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)


    @classmethod
    def get_next_element(cls, elem):
        """
        get next element after elem
        convenience method to use following::
        :param elem: element in tree
        :return: next elemnt or None
        """
        nexts = elem.xpath("following::*")
        return None if len(nexts) == 0 else nexts[0]

    @classmethod
    def get_following_elements(cls, elem, predicate=None, count=9999):
        """
        get next elements after elem
        convenience method to use following::
        :param elem: element in tree
        :param predicate: condition (with the []), e.g "[@class='.s1010']"
        :return: next elemnts or empty list
        """
        pred_string = f"" if predicate is None else f"{predicate}"
        xp = f"following::*{pred_string}"
        xp = f"following::*"
        print(f"xp: {xp} {lxml.etree.tostring(elem)}")
        nexts = elem.xpath(xp)
        # next = None if len(nexts) == 0 else nexts[:count]
        print(f"nexts {len(nexts)}")
        return nexts

    @classmethod
    def getparent(cls, elem, debug=False):
        if elem is None:
            return None;
        parent = elem.getparent()
        if parent is None and debug:
            print(f" parent of {elem} is None")
        return parent

    @classmethod
    def read_xml_element_from_github(cls, github_url=None, url_cache=None):
        """reads raw xml and parses to elem

        ent. Errors uncaught
        """
        if not github_url:
            return None
        # print(f"url: {github_url}")
        if url_cache:
            xml_elem = url_cache.read_xml_element_from_github(github_url)
        else:
            xml_elem = lxml.etree.fromstring(requests.get(github_url).text)
        return xml_elem



class HtmlElement:
    """to provide fluent HTML builder and parser NYI"""
    pass

class HtmlLib:

    @classmethod
    def convert_character_entities_in_lxml_element_to_unicode_string(cls, element, encoding="UTF-8") -> str:
        """
        converts character entities in lxml element to Unicode
        1) extract string as bytes
        2) converts bytes to unicode with html.unescape()
        (NOTE: may be able to use tostring to do this)


        :param element: lxml element
        :return: unicode string representation of element
        """
        import html
        stringx = lxml.etree.tostring(element)
        string_unicode = html.unescape(stringx.decode(encoding))
        return string_unicode

    @classmethod
    def create_html_with_empty_head_body(cls):
        """
        creates
        <html>
          <head/>
          <body/>
        </html>
        """
        html_elem = lxml.etree.Element("html")
        html_elem.append(lxml.etree.Element("head"))
        html_elem.append(lxml.etree.Element("body"))
        return html_elem

    @classmethod
    def add_copies_to_head(cls, html_elem, elems):
        """copies elems and adds them to <head> of html_elem
        no checks made for duplicates
        :param html_elem: elemnt to copy into
        :param elems: list of elements to copy (or single elemnt
        """
        if html_elem is None or elems is None:
            raise ValueError("Null arguments in HtmlLib.add_copies_to_head")
        head = html_elem.xpath("./head")[0]
        if type(elems) is not list:
            elems = [elems]
        for elem in elems:
            head.append(copy.deepcopy(elem))

    @classmethod
    def get_body(cls, html_elem):
        bodys = html_elem.xpath("./body")
        return bodys[0] if len(bodys) == 1 else None

    @classmethod
    def get_head(cls, html_elem):
        heads = html_elem.xpath("./head")
        return heads[0] if len(heads) == 1 else None

    @classmethod
    def create_new_html_with_old_styles(cls, html_elem):
        """
        creates new HTML element with empty body and copies styles from html_elem
        """
        new_html_elem = HtmlLib.create_html_with_empty_head_body()
        HtmlLib.add_copies_to_head(new_html_elem, html_elem.xpath(".//style"))
        return new_html_elem

    @classmethod
    def add_head_style(cls, html_page, target, css_value_pairs):
        """This might duplicate things in HtmlStyle"""
        if html_page is None or not target or not css_value_pairs:
            raise ValueError(f"None params in add_head_style")
        head = HtmlLib.get_head(html_page)
        style = lxml.etree.Element("style")
        head.append(style)
        style.text = target + " {"
        for css_value_pair in css_value_pairs:
            if len(css_value_pair) != 2:
                raise ValueError(f"bad css_value_pair {css_value_pair}")
            style.text += css_value_pair[0] + " : " + css_value_pair[1]
        style.text += "}"

    @classmethod
    def write_html_file(self, html_elem, outfile, debug=False):
        """writes XML elemnts to file, making directory if needed .
        adds method=True to ensure end tags
        """
        if html_elem is None or outfile is None:
            raise ValueError("null argumners to write_html_file")
        outdir = os.path.dirname(outfile)
        Path(outdir).mkdir(exist_ok=True, parents=True)
        with open(outfile, "wb") as f:
            f.write(lxml.etree.tostring(html_elem, method="html"))
        if debug:
            print(f"wrote: {outfile}")

    @classmethod
    def create_rawgithub_url(cls, site=None, username=None, repository=None, branch=None, filepath=None,
                             rawgithubuser="https://raw.githubusercontent.com"):
        """creates rawgithub url for programmatic HTTPS access to repository"""
        site = "https://raw.githubusercontent.com"
        url = f"{site}/{username}/{repository}/{branch}/{filepath}" if site and username and repository and branch and filepath else None
        # print(f"url {url}")
        return url


class DataTable:
    """
<html xmlns="http://www.w3.org/1999/xhtml">
 <head charset="UTF-8">
  <title>ffml</title>
  <link rel="stylesheet" type="text/css" href="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css"/>
  <script src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js" charset="UTF-8" type="text/javascript"> </script>
  <script src="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js" charset="UTF-8" type="text/javascript"> </script>
  <script charset="UTF-8" type="text/javascript">$(function() { $("#results").dataTable(); }) </script>
 </head>
    """

    def __init__(self, title, colheads=None, rowdata=None):
        """create dataTables
        optionally add column headings (list) and rows (list of conformant lists)

        :param title: of data_title (required)
        :param colheads:
        :param rowdata:

        """
        self.html = LXET.Element(H_HTML)
        self.head = None
        self.body = None
        self.create_head(title)
        self.create_table_thead_tbody()
        self.add_column_heads(colheads)
        self.add_rows(rowdata)
        self.head = None
        self.title = None
        self.title.text = None


    def create_head(self, title):
        """
          <title>ffml</title>
          <link rel="stylesheet" type="text/css" href="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css"/>
          <script src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js" charset="UTF-8" type="text/javascript"> </script>
          <script src="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js" charset="UTF-8" type="text/javascript"> </script>
          <script charset="UTF-8" type="text/javascript">$(function() { $("#results").dataTable(); }) </script>
        """

        self.head = LXET.SubElement(self.html, H_HEAD)
        self.title = LXET.SubElement(self.head, H_TITLE)
        self.title.text = title

        link = LXET.SubElement(self.head, LINK)
        link.attrib["rel"] = STYLESHEET
        link.attrib["type"] = TEXT_CSS
        link.attrib["href"] = "http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css"
        link.text = '.'  # messy, to stop formatter using "/>" which dataTables doesn't like

        script = LXET.SubElement(self.head, SCRIPT)
        script.attrib["src"] = "http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js"
        script.attrib["charset"] = UTF_8
        script.attrib["type"] = TEXT_JAVASCRIPT
        script.text = '.'  # messy, to stop formatter using "/>" which dataTables doesn't like

        script = LXET.SubElement(self.head, SCRIPT)
        script.attrib["src"] = "http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js"
        script.attrib["charset"] = UTF_8
        script.attrib["type"] = TEXT_JAVASCRIPT
        script.text = "."  # messy, to stop formatter using "/>" which dataTables doesn't like

        script = LXET.SubElement(self.head, SCRIPT)
        script.attrib["charset"] = UTF_8
        script.attrib["type"] = TEXT_JAVASCRIPT
        script.text = "$(function() { $(\"#results\").dataTable(); }) "

    def create_table_thead_tbody(self):
        """
     <body>
      <div class="bs-example table-responsive">
       <table class="table table-striped table-bordered table-hover" id="results">
        <thead>
         <tr>
          <th>articles</th>
          <th>bibliography</th>
          <th>dic:country</th>
          <th>word:frequencies</th>
         </tr>
        </thead>
        """

        self.body = LXET.SubElement(self.html, H_BODY)
        self.div = LXET.SubElement(self.body, H_DIV)
        self.div.attrib["class"] = "bs-example table-responsive"
        self.table = LXET.SubElement(self.div, H_TABLE)
        self.table.attrib["class"] = "table table-striped table-bordered table-hover"
        self.table.attrib["id"] = RESULTS
        self.thead = LXET.SubElement(self.table, H_THEAD)
        self.tbody = LXET.SubElement(self.table, H_TBODY)

    def add_column_heads(self, colheads):
        if colheads is not None:
            self.thead_tr = LXET.SubElement(self.thead, H_TR)
            for colhead in colheads:
                th = LXET.SubElement(self.thead_tr, H_TH)
                th.text = str(colhead)

    def add_rows(self, rowdata):
        if rowdata is not None:
            for row in rowdata:
                self.add_row_old(row)

    def add_row_old(self, row: [str]):
        """ creates new <tr> in <tbody>
        creates <td> child elements of row containing string values

        :param row: list of str
        :rtype: object
        """
        if row is not None:
            tr = LXET.SubElement(self.tbody, H_TR)
            for val in row:
                td = LXET.SubElement(tr, H_TD)
                td.text = val
                # print("td", td.text)

    def make_row(self):
        """

        :return: row element
        """
        return LXET.SubElement(self.tbody, H_TR)

    def append_contained_text(self, parent, tag, text):
        """create element <tag> and add text child
        :rtype: element

        """
        subelem = LXET.SubElement(parent, tag)
        subelem.text = text
        return subelem

    def write_full_data_tables(self, output_dir: str) -> None:
        """

        :rtype: object
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        data_table_file = os.path.join(output_dir, "full_data_table.html")
        with open(data_table_file, "w") as f:
            text = bytes.decode(LXET.tostring(self.html))
            f.write(text)
            print("WROTE", data_table_file)

    def __str__(self):
        # s = self.html.text
        # print("s", s)
        # return s
        # ic("ichtml", self.html)
        htmltext = LXET.tostring(self.html)
        print("SELF", htmltext)
        return htmltext


class Web:
    def __init__(self):
        import tkinter as tk
        root = tk.Tk()
        site = "http://google.com"
        self.display_html(root, site)
        root.mainloop()

    @classmethod
    def display_html(cls, master, site):
        import tkinterweb
        frame = tkinterweb.HtmlFrame(master)
        frame.load_website(site)
        frame.pack(fill="both", expand=True)

    @classmethod
    def tkinterweb_demo(cls):
        from tkinterweb import Demo
        Demo()


def main():

    XmlLib().test_recurse_sections()  # recursively list sections

#    test_data_table()
#    test_xml()

#    web = Web()
#    Web.tkinterweb_demo()


def test_xml():
    xml_string = "<a>foo <b>and</b> with <d/> bar</a>"
    print(XmlLib.remove_all_tags(xml_string))


def test_data_table():
    import pprint
    data_table = DataTable("test")
    data_table.add_column_heads(["a", "b", "c"])
    data_table.add_row_old(["a1", "b1", "c1"])
    data_table.add_row_old(["a2", "b2", "c2"])
    data_table.add_row_old(["a3", "b3", "c3"])
    data_table.add_row_old(["a4", "b4", "c4"])
    html = LXET.tostring(data_table.html).decode("UTF-8")
    HOME = os.path.expanduser("~")
    with open(os.path.join(HOME, "junk_html.html"), "w") as f:
        f.write(html)
    pprint.pprint(html)


if __name__ == "__main__":
    print("running file_lib main")
    main()
else:
    #    print("running file_lib main anyway")
    #    main()
    pass
