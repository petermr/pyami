import logging
import os
from shutil import copyfile
from lxml import etree as ET

# local

#from py4ami.dict_lib import AmiDictionary

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

        import pprint
        from urllib.request import urlopen
        from urllib.request import quote  # is this right??

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

    from tkinter import scrolledtext
    import tkinter as tk

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

    def __init__(self, pqitem):
        self.root = None
        self.pqitem = pqitem
        self.root = self.get_root_for_item(self.pqitem)

    # <li class="mw-search-result">
    # <div class="mw-search-result-heading">
    # <a href="/wiki/Q50887234" title="&#8206;Lantana camara var. nivea&#8206; | &#8206;variety of
    # plant&#8206;" data-serp-pos="13">
    #  <span class="wb-itemlink">
    #   <span class="wb-itemlink-label_xml" lang="en" dirx="ltr">
    #    <span class="searchmatch">Lantana</span>
    #    <span class="searchmatch">camara</span>
    #     var. nivea
    #   </span>
    #   <span class="wb-itemlink-id">(Q50887234)</span>
    # </span>
    # </a>
    # </div>
    #     <div class="searchresult">
    #     <span class="wb-itemlink-description">variety of plant</span>
    #     </div>
    #     <div class="mw-search-result-data">12 statements, 0 sitelinks - 17:16, 16 April 2021</div>
    #        </li>'
#         <li>
#         <div class="mw-search-result-heading">
#              <a href="/wiki/Q278809" title="(&#177;)-limonene | chemical compound" data-serp-pos="0">
#                <span class="wb-itemlink">
#                  <span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(&#177;)-
#                    <span class="searchmatch">limonene</span>
#                  </span>
#                  <span class="wb-itemlink-id">(Q278809)</span>
#                </span>
#              </a>
#           </div>'
# ..        <div class="searchresult">
#             <span class="wb-itemlink-description">chemical compound</span>
#           </div> '
#         """
        #   < li class ="mw-search-result" >
        #     < div class ="mw-search-result-heading" > < a href="/wiki/Q278809" title="(&#177;)-limonene |
    #     chemical compound" data-serp-pos="0" > < span class ="wb-itemlink" > < span class ="wb-itemlink-label_xml"
    #     lang="en" dirx="ltr" > ( &  # 177;)-<span class="searchmatch">limonene</span></span> <span class="wb-itemlink-id">(Q278809)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">chemical compound</span></div> <div class="mw-search-result-data">1021 statements, 32 sitelinks - 10:51, 24 May 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22282878" title="limonene biosynthetic process | The chemical reactions and pathways resulting in the formation of limonene (4-isopropenyl-1-methyl-cyclohexene), a monocyclic monoterpene." data-serp-pos="1"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr"><span class="searchmatch">limonene</span> biosynthetic process</span> <span class="wb-itemlink-id">(Q22282878)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">The chemical reactions and pathways resulting in the formation of limonene (4-isopropenyl-1-methyl-cyclohexene), a monocyclic monoterpene.</span></div> <div class="mw-search-result-data">8 statements, 0 sitelinks - 08:29, 17 May 2020</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22282225" title="limonene catabolic process | The chemical reactions and pathways resulting in the breakdown of limonene (4-isopropenyl-1-methyl-cyclohexene), a monocyclic monoterpene." data-serp-pos="2"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr"><span class="searchmatch">limonene</span> catabolic process</span> <span class="wb-itemlink-id">(Q22282225)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">The chemical reactions and pathways resulting in the breakdown of limonene (4-isopropenyl-1-methyl-cyclohexene), a monocyclic monoterpene.</span></div> <div class="mw-search-result-data">7 statements, 0 sitelinks - 13:16, 17 May 2020</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22324407" title="(4S)-limonene synthase activity | Catalysis of the reaction: geranyl diphosphate = (4S)-limonene + diphosphate." data-serp-pos="3"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(4S)-<span class="searchmatch">limonene</span> synthase activity</span> <span class="wb-itemlink-id">(Q22324407)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: geranyl diphosphate = (4S)-limonene + diphosphate.</span></div> <div class="mw-search-result-data">9 statements, 0 sitelinks - 17:28, 7 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q14916176" title="(S)-limonene 7-monooxygenase activity | Catalysis of the reaction: (4S)-limonene + H(+) + NADPH + O(2) = (4S)-perillyl alcohol + H(2)O + NADP(+)." data-serp-pos="4"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 7-monooxygenase activity</span> <span class="wb-itemlink-id">(Q14916176)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: (4S)-limonene + H(+) + NADPH + O(2) = (4S)-perillyl alcohol + H(2)O + NADP(+).</span></div> <div class="mw-search-result-data">12 statements, 0 sitelinks - 07:50, 8 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22282223" title="limonene metabolic process | The chemical reactions and pathways involving limonene (4-isopropenyl-1-methyl-cyclohexene), a monocyclic monoterpene." data-serp-pos="5"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr"><span class="searchmatch">limonene</span> metabolic process</span> <span class="wb-itemlink-id">(Q22282223)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">The chemical reactions and pathways involving limonene (4-isopropenyl-1-methyl-cyclohexene), a monocyclic monoterpene.</span></div> <div class="mw-search-result-data">7 statements, 0 sitelinks - 07:32, 17 May 2020</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q14916175" title="(S)-limonene 6-monooxygenase activity | Catalysis of the reaction: (-)-limonene + NADPH + H+ + O2 = (-)-trans-carveol + NADP+ + H2O." data-serp-pos="6"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 6-monooxygenase activity</span> <span class="wb-itemlink-id">(Q14916175)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: (-)-limonene + NADPH + H+ + O2 = (-)-trans-carveol + NADP+ + H2O.</span></div> <div class="mw-search-result-data">11 statements, 0 sitelinks - 17:43, 7 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q3596292" title="(S)-limonene 3-monooxygenase | class of enzymes" data-serp-pos="7"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 3-monooxygenase</span> <span class="wb-itemlink-id">(Q3596292)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">class of enzymes</span></div> <div class="mw-search-result-data">6 statements, 5 sitelinks - 06:33, 24 May 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22317639" title="(S)-limonene 3-monooxygenase activity | Catalysis of the reaction: (4S)-limonene + H(+) + NADPH + O(2) = (1S,6R)-isopiperitenol + H(2)O + NADP(+)." data-serp-pos="8"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 3-monooxygenase activity</span> <span class="wb-itemlink-id">(Q22317639)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: (4S)-limonene + H(+) + NADPH + O(2) = (1S,6R)-isopiperitenol + H(2)O + NADP(+).</span></div> <div class="mw-search-result-data">12 statements, 0 sitelinks - 17:35, 7 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q27089405" title="(-)-limonene | chemical compound" data-serp-pos="9"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(-)-<span class="searchmatch">limonene</span></span> <span class="wb-itemlink-id">(Q27089405)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">chemical compound</span></div> <div class="mw-search-result-data">73 statements, 0 sitelinks - 15:03, 18 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22317631" title="(R)-limonene 1,2-monooxygenase activity | Catalysis of the reaction: (4R)-limonene + NAD(P)H + H+ + O2 = NAD(P)+ + H2O + (4R)-limonene-1,2-epoxide." data-serp-pos="10"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(R)-<span class="searchmatch">limonene</span> 1,2-monooxygenase activity</span> <span class="wb-itemlink-id">(Q22317631)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: (4R)-limonene + NAD(P)H + H+ + O2 = NAD(P)+ + H2O + (4R)-limonene-1,2-epoxide.</span></div> <div class="mw-search-result-data">6 statements, 0 sitelinks - 15:06, 18 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22317627" title="(S)-limonene 1,2-monooxygenase activity | Catalysis of the reaction: (4S)-limonene + NAD(P)H + H+ + O2 = NAD(P)+ + H2O + (4S)-limonene-1,2-epoxide." data-serp-pos="11"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 1,2-monooxygenase activity</span> <span class="wb-itemlink-id">(Q22317627)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: (4S)-limonene + NAD(P)H + H+ + O2 = NAD(P)+ + H2O + (4S)-limonene-1,2-epoxide.</span></div> <div class="mw-search-result-data">6 statements, 0 sitelinks - 15:06, 18 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q16872168" title="Limonene synthase | Wikimedia disambiguation page" data-serp-pos="12"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr"><span class="searchmatch">Limonene</span> synthase</span> <span class="wb-itemlink-id">(Q16872168)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Wikimedia disambiguation page</span></div> <div class="mw-search-result-data">1 statement, 1 sitelink - 02:59, 4 May 2019</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q3596284" title="(R)-limonene 6-monooxygenase | class of enzymes" data-serp-pos="13"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(R)-<span class="searchmatch">limonene</span> 6-monooxygenase</span> <span class="wb-itemlink-id">(Q3596284)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">class of enzymes</span></div> <div class="mw-search-result-data">6 statements, 5 sitelinks - 17:17, 23 May 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q76625426" title="Limonene Hydroxylases | Members of the P-450 enzyme family that take part in the hydroxylation of limonene." data-serp-pos="14"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr"><span class="searchmatch">Limonene</span> Hydroxylases</span> <span class="wb-itemlink-id">(Q76625426)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Members of the P-450 enzyme family that take part in the hydroxylation of limonene.</span></div> <div class="mw-search-result-data">1 statement, 0 sitelinks - 13:57, 27 November 2019</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q14916177" title="(R)-limonene 6-monooxygenase activity | Catalysis of the reaction: (4R)-limonene + H+ + NADPH + O2 = (1R,5S)-carveol + H2O + NADP+." data-serp-pos="15"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(R)-<span class="searchmatch">limonene</span> 6-monooxygenase activity</span> <span class="wb-itemlink-id">(Q14916177)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: (4R)-limonene + H+ + NADPH + O2 = (1R,5S)-carveol + H2O + NADP+.</span></div> <div class="mw-search-result-data">12 statements, 0 sitelinks - 17:45, 7 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q22324412" title="(R)-limonene synthase activity | Catalysis of the reaction: geranyl diphosphate = (4R)-limonene + diphosphate." data-serp-pos="16"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(R)-<span class="searchmatch">limonene</span> synthase activity</span> <span class="wb-itemlink-id">(Q22324412)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">Catalysis of the reaction: geranyl diphosphate = (4R)-limonene + diphosphate.</span></div> <div class="mw-search-result-data">10 statements, 0 sitelinks - 17:22, 7 April 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q3596293" title="(S)-limonene 6-monooxygenase | class of enzymes" data-serp-pos="17"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 6-monooxygenase</span> <span class="wb-itemlink-id">(Q3596293)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">class of enzymes</span></div> <div class="mw-search-result-data">6 statements, 5 sitelinks - 06:41, 24 May 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q3596295" title="(S)-limonene 7-monooxygenase | class of enzymes" data-serp-pos="18"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(S)-<span class="searchmatch">limonene</span> 7-monooxygenase</span> <span class="wb-itemlink-id">(Q3596295)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">class of enzymes</span></div> <div class="mw-search-result-data">6 statements, 5 sitelinks - 06:43, 24 May 2021</div></li><li class="mw-search-result"><div class="mw-search-result-heading"><a href="/wiki/Q4543797" title="(4S)-limonene synthase | class of enzymes" data-serp-pos="19"><span class="wb-itemlink"><span class="wb-itemlink-label_xml" lang="en" dirx="ltr">(4S)-<span class="searchmatch">limonene</span> synthase</span> <span class="wb-itemlink-id">(Q4543797)</span></span></a>    </div><div class="searchresult"><span class="wb-itemlink-description">class of enzymes</span></div> <div class="mw-search-result-data">7 statements, 4 sitelinks - 09:04, 15 March 2021</div></li></ul><div class="mw-search-visualclear"/><p class="mw-search-pager-bottom">View (previous 20  |  <a href="/w/index.php?title=Special:Search&amp;limit=20&amp;offset=20&amp;profile=default&amp;search=limonene" title="Next 20 results" class="mw-nextlink">next 20</a>) (<a href="/w/index.php?title=Special:Search&amp;limit=20&amp;offset=0&amp;profile=default&amp;search=limonene" title="Show 20 results per page" class="mw-numlink">20</a> | <a href="/w/index.php?title=Special:Search&amp;limit=50&amp;offset=0&amp;profile=default&amp;search=limonene" title="Show 50 results per page" class="mw-numlink">50</a> | <a href="/w/index.php?title=Special:Search&amp;limit=100&amp;offset=0&amp;profile=default&amp;search=limonene" title="Show 100 results per page" class="mw-numlink">100</a> | <a href="/w/index.php?title=Special:Search&amp;limit=250&amp;offset=0&amp;profile=default&amp;search=limonene" title="Show 250 results per page" class="mw-numlink">250</a> | <a href="/w/index.php?title=Special:Search&amp;limit=500&amp;offset=0&amp;profile=default&amp;search=limonene" title="Show 500 results per page" class="mw-numlink">500</a>)</p>

        # lines = content.split("\\n")
        # for line in lines:
        #     print(">>", line)

    def get_root_for_item(self, qitem):
        if self.root is None:
            self.root = ParserWrapper.parse_utf8_html_to_root(WIKIDATA_SITE + qitem)
        return self.root

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
    def get_properties(self):
        pdivs = self.root.findall(".//div[@class='wikibase-statementgroupview']")
        ids = [pdiv.attrib[ID] for pdiv in pdivs]
        return ids


class WikidataSparql:

    def __init__(self):
        pass

    def update_from_sparqlx(self, sparql_file, sparql_to_dictionary):
        self.sparql_to_dictionary = sparql_to_dictionary
        self.check_unique_wikidata_ids()
        self.create_sparql_result_list(sparql_file)
        self.create_sparql_result_by_wikidata_id()
        self.update_dictionary_from_sparql()

    def create_sparql_result_list(self, sparql_file):
        assert(os.path.exists(sparql_file))
        print("sparql path", sparql_file)
        self.current_sparql = ET.parse(sparql_file, parser=ET.XMLParser(encoding="utf-8"))
        self.sparql_result_list = list(self.current_sparql.findall(SPQ_RESULTS + "/" + SPQ_RESULT, NS_MAP))
        assert(len(self.sparql_result_list) > 0)
        print("results", len(self.sparql_result_list))

    def create_sparql_result_by_wikidata_id(self):
        self.sparql_result_by_wikidata_id = {}
        id_element = self.sparql_to_dictionary[ID_NAME]
        for result in self.sparql_result_list:
            bindings = result.findall(SPQ_BINDING + "[@name='%s']/" + SPQ_URI % id_element, NS_MAP)
            if len(bindings) == 0:
                print("no bindings for {id_element}")
            else:
                uri = list(bindings)[0]
                wikidata_id = uri.text.split("/")[-1]
                if wikidata_id not in self.sparql_result_by_wikidata_id:
                    self.sparql_result_by_wikidata_id[wikidata_id] = []
                self.sparql_result_by_wikidata_id[wikidata_id].append(result)

    def apply_dicts_and_sparql(self, dictionary_file, rename_file, sparql2amidict_dict, sparql_files):

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
                assert (os.path.exists(sparql_file))
                dictionary = SearchDictionary(dictionary_file)
                dictionary.update_from_sparqlx(sparql_file, sparq2dict)
                dictionary_file = f"{dictionary_root}{keystring}_{i + 1}.xml"
                dictionary.write(dictionary_file)
        if rename_file:
            copyfile(dictionary_file, original_name)

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

        with urlopen(url) as u:
            content = u.read().decode("utf-8")
        tree = etree.parse(StringIO(content), etree.HTMLParser())
        root = tree.getroot()
        return root
