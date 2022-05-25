import logging
import os
from shutil import copyfile

from lxml import etree as ET

# local

# from py4ami.dict_lib import AmiDictionary

logging.debug("loading wikimedia.py")

WIKIDATA_QUERY_URI = "https://www.wikidata.org/w/index.php?search="
WIKIDATA_SITE = "https://www.wikidata.org/wiki/"

STATEMENTS = "statements"
# HTML classes in WD search output
SEARCH_RESULT = "searchresult"
MW_SEARCH_RESULT_DATA = "mw-search-result-data"
MW_SEARCH_RESULTS = "mw-search-results"
MW_SEARCH_RESULT_HEADING = "mw-search-result-heading"
WB_SLLV_LV = "wikibase-sitelinklistview-listview"
ID = "id"

BODY = "body"
HREF = "href"
TITLE = "title"
DESC = "desc"

# elements in SPARQL output
SPQ_RESULTS = "SPQ:results"
SPQ_RESULT = "SPQ:result"
SPQ_URI = "SPQ:uri"
SPQ_BINDING = "SPQ:binding"

# entry
NS_MAP = {'SPQ': 'http://www.w3.org/2005/sparql-results#'}  # add more as needed
NS_URI = "SPQ:uri"
NS_LITERAL = "SPQ:literal"

# names mapping SPARQL output to amidict
ID_NAME = "id_name"
SPQ_NAME = "sparql_name"
DICT_NAME = "dict_name"


# this should go in config files
class WikidataPredicate:
    chemistry = {
        "P31": {
            "Q11173": "chemical compound",
            "weight": 0.9
            },

        "P117": {"object": "chemical structure",
                 "weight": 0.9
                 },
        "P271": {"object": "chemical formula",
                 "weight": 0.9
                 },
        "P223": {"object": "canonical SMILES",
                 "weight": 0.9
                 },
        "P223": {"object": "canonical SMILES",
                 "weight": 0.9
                 },
        # "IDENTIFIER": {"InChI" : }
    }

# TODO add docstrings and check return values
class WikidataLookup:

    def __init__(self, exact_lookup=False):
        self.term = None
        self.wikidata_dict = None
        self.root = None
        self.exact_lookup = exact_lookup

    def lookup_wikidata(self, term):
        """
        Looks up term in Wikidata and gets Q number and descriptiom

        NOTE requires Internet

        :param term: word or phrase to lookup
        :return: triple (e.g. qitem[0], qitem[1]["desc"], wikidata_hits)
        """

        from urllib.parse import quote

        self.term = term
        url = WIKIDATA_QUERY_URI + quote(term.encode('utf8'))
        self.root = ParserWrapper.parse_utf8_html_to_root(url)
        body = self.root.find(BODY)
        ul = body.find(".//ul[@class='" + MW_SEARCH_RESULTS + "']")
        qitem = None  # to avoid UnboundLocalError
        if ul is not None:
            self.wikidata_dict = self.create_dict_for_all_possible_wd_matches(ul)
            sort_orders = sorted(self.wikidata_dict.items(), key=lambda item: int(item[1][STATEMENTS]), reverse=True)
            wikidata_hits = [s[0] for s in sort_orders[:5]]
            #            pprint.pprint(sort_orders[0:3])
            #  take the first
            qitem = sort_orders[0]
            # TODO fix non-tuples
        if qitem is None:
            return None, None, None
        else:
            return qitem[0], qitem[1]["desc"], wikidata_hits

    # def lookup_qitem(self, qitem):
    #     root = ParserWrapper.parse_utf8_html_to_root(WIKIDATA_SITE + qitem)
    #     return root

    def lookup_items(self, terms):
        """looks up a series of terms and returns a tuple of list(qitem), list(desc)
        NOTE requires Internet
        :terms: strings to search for"""

        qitems = []
        descs = []
        for term in terms:
            qitem0, desc, wikidata_hits = self.lookup_wikidata(term)
            qitems.append(qitem0)
            descs.append(desc)
        return qitems, descs

    def create_dict_for_all_possible_wd_matches(self, ul):
        wikidata_dict = {}
        for li in ul:
            result_heading_a = li.find("./div[@class='" + MW_SEARCH_RESULT_HEADING + "']/a")
            qitem = result_heading_a.attrib[HREF].split("/")[-1]
            if qitem in wikidata_dict:
                print(f"duplicate wikidata entry {qitem}")
            else:
                self.add_subdict_title_desc_statements(li, qitem, result_heading_a, wikidata_dict)
        return wikidata_dict

    def add_subdict_title_desc_statements(self, li, qitem, result_heading_a, wikidata_dict):
        sub_dict = {}
        wikidata_dict[qitem] = sub_dict
        # make title from text children not tooltip
        sub_dict[TITLE] = ''.join(result_heading_a.itertext()).split("(Q")[0]
        sub_dict[DESC] = li.find("./div[@class='" + SEARCH_RESULT + "']/span").text
        # just take statements at present (n statements or 1 statement)
        sub_dict[STATEMENTS] = \
            li.find("./div[@class='" + MW_SEARCH_RESULT_DATA + "']").text.split(",")[0].split(" statement")[0]


class WikidataBrowser:
    """ """

    def __init__(self, ami_gui, text):
        from py4ami.xml_lib import XmlLib
        from lxml import etree as LXET
        from tkinterhtml import HtmlFrame
        import tkinter as tk
        from tkinter import scrolledtext
        from py4ami.gutil import CreateToolTip
        from urllib.request import urlopen

        toplevel = tk.Toplevel(ami_gui.master)
        text_display = scrolledtext.ScrolledText(
            toplevel, font=("Arial, 18"), width=60, height=10)
        text_display.pack(side=tk.BOTTOM)
        label = tk.Label(toplevel, text="Wikidata search results")
        CreateToolTip(label, "Contains text representation \nof wikidata query")
        label.pack(side=tk.TOP)
        url = ami_gui.create_wikidata_query_url(text)
        with urlopen(url) as response:
            the_page = bytes.decode(response.read())
        html_root = XmlLib.parse_xml_string_to_root(the_page)
        self.remove_xpath(html_root, ".//script")
        head = html_root.xpath(".//head")[0]
        style = LXET.SubElement(head, "style")
        style.attrib["type"] = "text/css"
        style.text = "* {font-size:40pt; color:red;}"
        html_content = bytes.decode(LXET.tostring(html_root))
        # div id="content" class="mw-body"
        content_elem = html_root.xpath(".//div[@id='content']")[0]
        div_content = LXET.tostring(content_elem)
        # print(content) # doesn't display well in tkinter
        text_display.insert("1.0", div_content)
        text_display.pack_forget()

        frame = HtmlFrame(toplevel, horizontal_scrollbar="auto")
        frame.set_content(html_content)
        frame.pack()

    def remove_xpath(self, element, xpath):
        """

        :param element:
        :param xpath:

        """
        for subelem in element.xpath(xpath):
            subelem.getparent().remove(subelem)


class WikidataPage:
    PROPERTY_ID = "id"

    def __init__(self, pqitem):
        self.root = None
        self.pqitem = pqitem
        self.root = self.get_root_for_item(self.pqitem)

    @classmethod
    def create_wikidata_ppage_from_file(cls, file):
        pass

    def get_root_for_item(self, qitem):
        """search wikidata site for QItem
        :param qitem: Qitem (or P item to search
        :return: parsed lxml root"""
        if self.root is None:
            self.root = ParserWrapper.parse_utf8_html_to_root(self.get_wikidata_site() + qitem)
        return self.root

    @classmethod
    def get_wikidata_site(cls):
        return WIKIDATA_SITE

# WikidataPage

    def get_wikipedia_page_links(self, lang_list):
        """
<h2 class="wb-section-heading section-heading wikibase-sitelinks" dirx="auto">
  <span class="mw-headline" id="sitelinks">Sitelinks</span></h2>
  <div class="wikibase-sitelinkgrouplistview">
    <div class="wikibase-listview">
      <div class="wikibase-sitelinkgroupview mw-collapsible" data-wb-sitelinks-group="wikipedia">
        <div class="wikibase-sitelinkgroupview-heading-section">
          <div class="wikibase-sitelinkgroupview-heading-container">
            <h3 class="wb-sitelinks-heading" dirx="auto" id="sitelinks-wikipedia">Wikipedia<span
            class="wikibase-sitelinkgroupview-hit_counter">(27 entries)</span></h3>
            <span class="wikibase-toolbar-container">
              <span class="wikibase-toolbar-item wikibase-toolbar ">
                <span class="wikibase-toolbar-item wikibase-toolbar-button wikibase-toolbar-button-edit">
                  <a href="/wiki/Special:SetSiteLink/Q144362" title="">
                    <span class="wb-icon"></span>edit
                  </a>
                </span>
            </span>
        </span>
        </div>
        </div>
<div class="mw-collapsible-content">
<div class="wikibase-sitelinklistview">
<ul class="wikibase-sitelinklistview-listview">
  <li class="wikibase-sitelinkview wikibase-sitelinkview-arwiki" data-wb-siteid="arwiki">
    <span class="wikibase-sitelinkview-siteid-container">
      <span class="wikibase-sitelinkview-siteid wikibase-sitelinkview-siteid-arwiki" title="Arabic">arwiki</span>
    </span>
    <span class="wikibase-sitelinkview-link wikibase-sitelinkview-link-arwiki">
      <span class="wikibase-sitelinkview-page" dirx="auto" lang="ar">
        <a href="https://ar.wikipedia.org/wiki/%D8%A2%D8%B2%D9%88%D9%84%D9%8A%D9%86" hreflang="ar"
        title="آزولين">آزولين</a>
      </span>
      <span class="wikibase-badgeselector wikibase-sitelinkview-badges"></span>
    </span>
  </li>
  ...
  <li class="wikibase-sitelinkview wikibase-sitelinkview-enwiki" data-wb-siteid="enwiki">
    <span class="wikibase-sitelinkview-siteid-container">
      <span class="wikibase-sitelinkview-siteid wikibase-sitelinkview-siteid-enwiki" title="English">enwiki</span>
    </span>
    <span class="wikibase-sitelinkview-link wikibase-sitelinkview-link-enwiki">
      <span class="wikibase-sitelinkview-page" dirx="auto" lang="en">
        <a href="https://en.wikipedia.org/wiki/Azulene" hreflang="en" title="Azulene">Azulene</a>
      </span>
      <span class="wikibase-badgeselector wikibase-sitelinkview-badges"></span>
    </span>
  </li>
        """
        # ul = root.find(".//ul[@class='" + "wikibase-sitelinklistview-listview" +"']")
        #     li_lang = ul.find("./li[@data-wb-siteid='" +f"{lang}wiki" + "']")
        #     ahref = li_lang.find(".//a[@hreflang]")
        #     print(ahref.attrib["href"])

        lang_pages = {}
        if lang_list:
            for lang in lang_list:
                href_lang = ".//ul[@class='" + WB_SLLV_LV + "']" + "/li[@data-wb-siteid='" + f"{lang}wiki" + "']" + \
                            "//a[@hreflang]"
                a = self.root.find(href_lang)
                if a is not None:
                    lang_pages[lang] = a.attrib[HREF]
        return lang_pages

    def get_image(self):
        pass

    """
    <div class="wikibase-statementgroupview" id="P5037" data-property-id="P5037">
    <div class="wikibase-statementgroupview-property">
    """

    # WikidataPage

    def get_properties(self):
        pdivs = self.root.findall(".//div[@class='wikibase-statementgroupview']")
        ids = [pdiv.attrib[ID] for pdiv in pdivs]
        return ids

    def get_data_property_list(self):
        """gets data_properties (the Statements and Identifiers)
        :return: list of properties , may be empty
        """
        selector = WikidataPage.get_data_property_xpath()
        property_list = self.root.xpath(selector)
        return property_list

    @classmethod
    def get_data_property_xpath(cls):
        """selector for data_properties """
        return f".//div[@data-property-id]"

    def get_property_id_list(self):
        property_list = self.get_data_property_list()
        property_id_list = [property.get("id") for property in property_list]
        return property_id_list

    def get_property_name_list(self):
        property_list = self.get_data_property_list()
        property_name_list = [WikidataPage.get_property_name(property) for property in property_list]
        return property_name_list

    @classmethod
    def get_property_name(cls, property):
        """gets property name from property box"""
        return property.xpath('./div/div/a')[0].text

    @classmethod
    def get_id(cls, property):
        """gets property name from property box"""
        return property.get(cls.PROPERTY_ID)

    @classmethod
    def extract_statements(cls, property):
        xpath = f"./div[@class='wikibase-statementlistview']/div[@class='wikibase-statementlistview-listview']/div/div[@class='wikibase-statementview-mainsnak-container']/div[@class='wikibase-statementview-mainsnak']/div/div[@class='wikibase-snakview-value-container']/div[@class='wikibase-snakview-body']//div/a"
        statements = property.xpath(xpath)
        return statements

    @classmethod
    def get_properties_dict(cls, property_list):
        """makes python dict from list of properties"""
        properties_dict = {}
        for property in property_list:
            id = WikidataPage.get_id(property)
            property_dict = cls.create_property_dict(property)
            properties_dict[id] = property_dict
        return properties_dict

    @classmethod
    def create_property_dict(cls, property):
        """creates python dict from wikidata_page
        Not complete (doesn't do scalar values)"""
        id = WikidataPage.get_property_name(property)
        name = WikidataPage.get_property_name(property)
        property_dict = {
            "name": name,
        }
        statements = WikidataPage.extract_statements(property)
        if len(statements) > 0:
            statement_dict = {}
            for statement in statements:
                id = statement.get('title')
                value = statement.text
                if id:
                    statement_dict[id] = value
                    # print(f"statement {id} {value}")
                else:
                    # print(f"value: {value}")
                    property_dict["value"] = value
            if len(statement_dict) > 0:
                property_dict["statements"] = statement_dict
        return property_dict




    @classmethod
    def get_predicate_object_from_file(cls, wikidata_file, pred, obj):
        """finds wikidata predicate+object
        a WikidataPage contains a list of predicate+obj
        we search with their values
        :param
        """
        wikidata = WikidataPage(wikidata_file)
        # root = html.parse(wikidata_file).getroot()
        pred_obj_list = wikidata.get_predicate_object(pred, obj)
        return pred_obj_list

    def get_predicate_object(self, pred, obj):
        pred_obj_list = self.root.xpath(
            f".//div[@id='{pred}']//div[@class='wikibase-snakview-body']//a[@title='{obj}']")
        return pred_obj_list

    def get_title(self):
        """gets title (string preceeding Q/P number)
        identical to label in language of browser (or only en?)
        """
        title_elem_list = self.root.xpath(
            f"/html/body/div/h1/span/span[@class='wikibase-title-label']")
        title = title_elem_list[0].text
        return title

    def get_aliases(self):
        """gets aliases ("also known as")
        """
        """
        < ul
        class ="wikibase-entitytermsview-aliases" >
        < li class ="wikibase-entitytermsview-aliases-alias" data-aliases-separator="|" > l-menthol < / li > 
        < li class ="wikibase-entitytermsview-aliases-alias" data-aliases-separator="|" > levomenthol < / li > 
        """
        alias_elem_list = self.root.xpath(
            f"/html/body//ul[@class='wikibase-entitytermsview-aliases']/li")
        alias_list = [li.text for li in alias_elem_list]
        return alias_list

    def get_description(self):
        """gets description (maybe in English?)
        precedes the aliases

        <div class="wikibase-entitytermsview-heading-description">chemical compound</div>

        """
        # desc_list = self.root.xpath(
        #     f"/html//*[@class='wikibase-entitytermsview-heading-description']")
        desc_list = self.get_elements_for_normalized_attrib_val("class", "wikibase-entitytermsview-heading-description")
        # desc_list = self.root.xpath(
        #     f"/html//*[normalize-space(@class)='wikibase-entitytermsview-heading-description']")
        assert desc_list is not None
        assert len(desc_list) == 1
        desc = desc_list[0].text
        return desc

    def get_elements_for_normalized_attrib_val(self, attname, attval, lead="//*", trail=""):
        """some attvals contain leading/trailing space
        searches for <lead>/*[@foo=bar] where bar might be whitespaced
        :param attname: attribute name
        :param attval: normalized attribute value required
        :param lead: leading string (e.g. "/html//*")
        :param trail: trailing string (e.g. "/li"
        """
        xpath = self.create_xpath_for_equality_whitespaced_attvals(attname, attval, lead=lead, trail=trail)
        elems = self.root.xpath(xpath)
        return elems

    def create_xpath_for_equality_whitespaced_attvals(self, attname, attval, lead="", trail=""):
        """Some attribute values have extraneous whitespace
        <zz foo="bar "/>
        then [@foo='bar'] fails
        This is a hack
        :param attname: attribute name
        :param attval: normalized attribute value required
        :param lead: leading string (e.g. "/html//*")
        :param trail: trailing string (e.g. "/li"
        return xpath
        """

        xpath = f"{lead}[concat(' ',normalize-space(@{attname}),' ')=concat(' ',normalize-space('{attval}'),' ')]{trail}"
        return xpath

    def get_elements_for_attval_containing_word(self, attname, attval, lead="//*", trail=""):
        """some attvals contain leading/trailing space
        searches for <lead>/*[@foo=bar] where bar might be whitespaced
        :param attname: attribute name
        :param attval: normalized attribute value required
        :param lead: leading string (e.g. "/html//*")
        :param trail: trailing string (e.g. "/li"
        """
        xpath = self.create_xpath_for_contains_whitespaced_attvals(attname, attval, lead=lead, trail=trail)
        # print(f"{xpath}")
        elems = self.root.xpath(xpath)
        return elems

    def create_xpath_for_contains_whitespaced_attvals(self, attname, attval, lead="", trail=""):
        """searches for complete words in whitespace-concatenated attribute values
        <zz foo="bar plugh barbara plinge"/>
        searches for 'bar' but not 'barbara'
        Not tested
        :param attname: attribute name
        :param attval: normalized attribute value required
        :param lead: leading string (e.g. "/html//*")
        :param trail: trailing string (e.g. "/li"
        return xpath
        """

        xpath = f"{lead}[contains(concat(' ',normalize-space(@{attname}),' '),concat(' ',normalize-space('{attval}'),' '))]{trail}"
        return xpath

    # def _get_elements_for_normalized_attrib_val(self, attname, attval):
    #     """some attvals contain trailing space"""
    #     xpath = f"/html//*[contains(concat(' ',@{attname},' '),concat(' ','{attval}',' '))]"
    #     print(f"xpath |{xpath}|")
    #     xpath = f"/html//*[normalize-space(@{attname})='{attval}']"
    #     elems = self.root.xpath(xpath)
    #     return elems

"""<div class="wikibase-entitytermsview-heading-description">chemical compound</div>"""
class WikidataSparql:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def update_from_sparqlx(self, sparql_file, sparql_to_dictionary):
        self.sparql_to_dictionary = sparql_to_dictionary

        self.dictionary.check_unique_wikidata_ids()
        self.create_sparql_result_list(sparql_file)
        self.create_sparql_result_by_wikidata_id()
        self.update_dictionary_from_sparql()

    def create_sparql_result_list(self, sparql_file):
        assert (os.path.exists(sparql_file))
        print("sparql path", sparql_file)
        self.current_sparql = ET.parse(sparql_file, parser=ET.XMLParser(encoding="utf-8"))
        self.sparql_result_list = list(self.current_sparql.findall(SPQ_RESULTS + "/" + SPQ_RESULT, NS_MAP))
        assert (len(self.sparql_result_list) > 0)
        print("results", len(self.sparql_result_list))

    def create_sparql_result_by_wikidata_id(self):
        self.sparql_result_by_wikidata_id = {}
        id_element = self.sparql_to_dictionary[ID_NAME]
        for result in self.sparql_result_list:
            # TODO fix syntax
            bindings = result.findall(SPQ_BINDING + "[@name='%s']/" + SPQ_URI % id_element, NS_MAP)
            if len(bindings) == 0:
                print("no bindings for {id_element}")
            else:
                uri = list(bindings)[0]
                wikidata_id = uri.text.split("/")[-1]
                if wikidata_id not in self.sparql_result_by_wikidata_id:
                    self.sparql_result_by_wikidata_id[wikidata_id] = []
                self.sparql_result_by_wikidata_id[wikidata_id].append(result)

# WikidataSparql
    @classmethod
    def apply_dicts_and_sparql(cls, dictionary_file, rename_file, sparql2amidict_dict, sparql_files):
        """TODO this is a mess"""
        keystring = ""
        # svae original path
        original_name = dictionary_file
        dictionary_root = os.path.splitext(dictionary_file)[0]
        save_file = dictionary_root + ".xml.save"
        copyfile(dictionary_file, save_file)
        for key in sparql2amidict_dict.keys():
            sparq2dict = sparql2amidict_dict[key]
            keystring += f"_{key}"
            for i, sparql_file in enumerate(sparql_files):
                dictionary_file = cls.create_and_write_dictionary(dictionary_file, dictionary_root, i, keystring,
                                                                  sparq2dict, sparql_file)
        if rename_file:
            copyfile(dictionary_file, original_name)

    @classmethod
    def create_and_write_dictionary(cls, dictionary_file, dictionary_root, i, keystring, sparq2dict, sparql_file):
        from py4ami.dict_lib import AmiDictionary
        assert (os.path.exists(sparql_file))
        dictionary = AmiDictionary(dictionary_file)
        dictionary.update_from_sparqlx(sparql_file, sparq2dict)
        dictionary_file = f"{dictionary_root}{keystring}_{i + 1}.xml"
        dictionary.write(dictionary_file)
        return dictionary_file

    # WikidataSparql

    def update_dictionary_from_sparql(self):

        print("sparql result by id", len(self.sparql_result_by_wikidata_id))
        sparql_name = self.sparql_to_dictionary[SPQ_NAME]
        dict_name = self.sparql_to_dictionary[DICT_NAME]
        for wikidata_id in self.sparql_result_by_wikidata_id.keys():
            if wikidata_id in self.entry_by_wikidata_id.keys():
                entry = self.entry_by_wikidata_id[wikidata_id]
                result_list = self.sparql_result_by_wikidata_id[wikidata_id]
                for result in result_list:
                    bindings = list(result.findall(SPQ_BINDING + "/" + "[@name='" + sparql_name + "']", NS_MAP))
                    if len(bindings) > 0:
                        binding = bindings[0]
                        self.update_entry(entry, binding, dict_name)

    #                print("dict", ET.tostring(entry))

    def update_entry(self, entry, binding, dict_name):
        updates = list(binding.findall(NS_URI, NS_MAP)) + \
                  list(binding.findall(NS_LITERAL, NS_MAP))
        entry_child = ET.Element(dict_name)
        entry_child.text = updates[0].text
        if entry_child.text is not None and len(entry_child.text.strip()) > 0:
            entry.append(entry_child)

    #        print(">>", ET.tostring(entry))

    def get_results_xml(self, query):
        """query Wikidata SPARQL endpoint and return XML results
        Shweata M Hegde and Peter Murray-Rust
        :query: as SPARQL
        :return: xml <results>"""
        from SPARQLWrapper import SPARQLWrapper
        import sys
        WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

        user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
        # TODO adjust user agent; see https://w.wiki/CX6
        sparql = SPARQLWrapper(WIKIDATA_SPARQL_ENDPOINT, agent=user_agent)
        sparql.setQuery(query)
        # sparql.setReturnFormat(XML)
        return sparql.query().convert().toxml()


class ParserWrapper:
    @classmethod
    def parse_utf8_html_to_root(cla, url):
        from io import StringIO
        from urllib.request import urlopen
        from lxml import etree
        from urllib.error import HTTPError

        try:
            with urlopen(url) as u:
                content = u.read().decode("utf-8")
        except HTTPError as e:
            print(f"cannout open {url} because {e}")
        tree = etree.parse(StringIO(content), etree.HTMLParser())
        root = tree.getroot()
        return root

import pprint
import requests

class WikidataExtractor:
    """Thanks to Awena for showing the approach"""
    VERSION = "0.1"
    USER_AGENT = "Mozilla/5.0 (compatible; Pyami/" + VERSION + "; +https://github.com/petermr/pyami/)"
    WIKIDATA_API = "https://www.wikidata.org/w/api.php"

    def __init__(self, lang='en'):
        self.lang = lang.lower()
        self.cache = {}
        self.query = None
        self.number_of_requests = 0
        self.result = None

    def __str__(self):
        return self.query

    def __len__(self):
        return len(self.cache)

    def __eq__(self, other):
        if isinstance(other, bool):
            return bool(self.cache) == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def number_of_requests(self):
        return self.number_of_requests

    def search(self, query):
        return self._request(query, False)

    def load(self, id=None):
        if not id:
            return {}
        if id not in self.cache:
            data = self._request(False, id)
            self.cache[id] = self._parse(data, id)
        return self.cache[id]

    def _request(self, query=False, id=False):
        headers = {
            "User-Agent": WikidataExtractor.USER_AGENT
        }

        params, self.query = self.get_params(id, query)
        data = requests.get(self.WIKIDATA_API, headers=headers, params=params)
        result = data.json()
        self.result = result

        self.number_of_requests += 1
        CODE = "code"
        ENTITIES = "entities"
        ERR = "error"
        ID = "id"
        INFO = "info"
        LANGUAGE = "language"
        MATCH = "match"
        SEARCH = "search"
        TEXT = "text"

        if ERR in result:
            raise Exception(result[ERR][CODE], result[ERR][INFO])
        elif query and SEARCH in result and result[SEARCH]:
            guess = None
            for item in result[SEARCH]:
                if ID in item and MATCH in item and TEXT in item[MATCH] and LANGUAGE in item[MATCH]:
                    if item[MATCH][LANGUAGE] == self.lang:
                        if not guess:
                            guess = item[ID]
                        if item[MATCH][TEXT].lower().strip() == query.lower():
                            return item[ID]
                return guess
        elif id and ENTITIES in result and result[ENTITIES]:
            if id in result[ENTITIES] and result[ENTITIES][id]:
                return result[ENTITIES][id]
        if query:
            return {}
        # return None
        return result

    def get_params(self, id, query):
        params = None
        if id:
            params = {
                "action": "wbgetentities",
                "ids": id,
                "language": self.lang,
                "format": "json"
            }
        elif query:
            query = query.strip()
            params = {
                "action": "wbsearchentities",
                "search": query,
                "language": self.lang,
                "format": "json"
            }
        return params, query

    def _parse(self, data, id):
        DESCRIPTION = "description"
        DESCRIPTIONS = "descriptions"
        ID = "id"
        LABEL = "label"
        LABELS = "labels"
        VALUE = "value"

        result = {ID: id}
        if id and data:
            if LABELS in data:
                if self.lang in data[LABELS]:
                    result[LABEL] = data[LABELS][self.lang][VALUE]
            if DESCRIPTIONS in data:
                if self.lang in data[DESCRIPTIONS]:
                    result[DESCRIPTION] = data[DESCRIPTIONS][self.lang][VALUE]
        # if "claims" in data:
        # 	# results to human readable format
        # 	for key	in data["claims"]:
        # 		try:
        # 			if key=="P31":		# instance of
        # 				result["instance"]			= data["claims"][key][0]["mainsnak"]["datavalue"]["value"]["id"]
        return result

