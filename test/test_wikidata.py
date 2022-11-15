# Tests wikipedia and wikidata methods under pytest
import ast
import lxml
import os
import pprint
import unittest
from pathlib import Path
import logging
from lxml import etree, html
import requests
# local
from py4ami.wikimedia import WikidataPage, ParserWrapper, WikidataExtractor, WikidataProperty, WikidataFilter
from py4ami.ami_dict import WIKIDATA_ID, AmiEntry
from test.resources import Resources

"""This runs under Pycharm and also
cd pyami # toplevel checkout
python3 -m test.test_wikidata
"""

try:
    from py4ami.wikimedia import WikidataLookup
    from py4ami.ami_dict import AMIDictError, AmiDictionary

    logging.info(f"loaded py4ami.ami_dict")
except Exception:
    try:
        from py4ami.wikimedia import WikidataLookup
        from py4ami.ami_dict import AMIDictError
    except Exception as e:
        logging.error(f"Cannot import from py4ami.ami_dict")

RESOURCES_DIR = Path(Path(__file__).parent.parent, "test", "resources")
TEMP_DIR = Path(Path(__file__).parent.parent, "temp_oldx")
DICTIONARY_DIR = Path(os.path.expanduser("~"), "projects", "CEVOpen", "dictionary")
EO_COMPOUND = "eoCompound"
EO_COMPOUND_DIR = Path(RESOURCES_DIR, EO_COMPOUND)


# NOTE some of these are lengthy (seconds) as they lookup on the Ne

class TestWikidataLookup(unittest.TestCase):

    def test_lookup_wikidata_acetone(self):
        term = "acetone"
        wikidata_lookup = WikidataLookup()
        qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
        assert qitem0 == "Q49546"
        assert desc == "chemical compound"
        # assert wikidata_hits == ['Q49546', 'Q24634417', 'Q329022', 'Q63986955', 'Q4673277']
        assert 'Q49546' in wikidata_hits and len(wikidata_hits) >= 3

    def test_lookup_chemical_compound(self):
        wiki_page = WikidataPage("Q49546")
        # assert is chemical compound
        qval = wiki_page.get_predicate_object("P31", "Q11173")
        assert len(qval) == 1
        wiki_page = WikidataPage("Q24634417")
        qval = wiki_page.get_predicate_object("P31", "Q11173")
        assert len(qval) == 0
        # actually a scholarly article
        qval = wiki_page.get_predicate_object("P31", "Q13442814")
        assert len(qval) == 1

    def test_lookup_wikidata_bad(self):
        """This fails"""
        term = "benzene"
        wikidata_lookup = WikidataLookup()
        qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
        # assert qitem0 == "Q170304"  # dopamine???
        # assert desc == "hormone and neurotransmitter"
        # this needs mending as it found dopmamine (4-(2-azanylethyl)benzene-1,2-diol)
        assert len(wikidata_hits) > 0
        # assert wikidata_hits == ['Q170304', 'Q2270', 'Q15779', 'Q186242', 'Q28917']

    @unittest.skip(reason="NET, long")
    def test_lookup_solvents(self):
        terms = ["acetone", "chloroform", "ethanol"]
        wikidata_lookup = WikidataLookup()
        qitems, descs = wikidata_lookup.lookup_items(terms)
        assert qitems == ['Q49546', 'Q172275', 'Q153']
        assert descs == ['chemical compound', 'chemical compound', 'chemical compound']

    @unittest.skip(reason="Net, Long")
    def test_lookup_parkinsons(self):
        terms = [
            "SCRNASeq",
            "SNPS",
            "A53T",
            "linkage disequilibrium",
            "Parkinsons",
            "transcriptomics"
        ]
        wikidata_lookup = WikidataLookup()
        # qitems, descs = wikidata_lookup.lookup_items(terms)
        temp_dir = Path(Resources.TEMP_DIR, "temp_oldx")
        # dictfile, amidict = AMIDict.create_from_list_of_strings_and_write_to_file(terms, title="parkinsons",
        #                                                                           wikidata=True, directory=temp_dir)
        # assert os.path.exists(dictfile)

    def test_parse_wikidata_html(self):
        """find Wikidata items with given property
        uses the HTML, tacky but works

        in this case the property is P31 (instance-of) and the value is one of
        three
        <div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak">
                                            <a title="Q11173" href="/wiki/Q11173">chemical compound</a>
                                        </div>

        """
        """
    <div class="wikibase-statementgroupview listview-item" id="P31" data-property-id="P31">
        <div class="wikibase-statementgroupview-property">
            <div class="wikibase-statementgroupview-property-label" dir="auto">
                <a title="Property:P31" href="/wiki/Property:P31">instance of</a>
            </div>
        </div>
        <div class="wikibase-statementlistview">
            <div class="wikibase-statementlistview-listview">
                <div id="Q407418$8A24EA26-7C5E-4494-B40C-65356BBB3AA4" class="wikibase-statementview wikibase-statement-Q407418$8A24EA26-7C5E-4494-B40C-65356BBB3AA4 wb-normal listview-item wikibase-toolbar-item">
                    <div class="wikibase-statementview-rankselector">
                        <div class="wikibase-rankselector ui-state-disabled">
                            <span class="ui-icon ui-icon-rankselector wikibase-rankselector-normal" title="Normal rank"/>
                        </div>
                    </div>
                    <div class="wikibase-statementview-mainsnak-container">
                        <div class="wikibase-statementview-mainsnak" dir="auto">
                            <div class="wikibase-snakview wikibase-snakview-e823b98d1498aa78e139709b1b02f5decd75c887">
                                <div class="wikibase-snakview-property-container">
                                    <div class="wikibase-snakview-property" dir="auto"/>
                                </div>
                                <div class="wikibase-snakview-value-container" dir="auto">
                                    <div class="wikibase-snakview-typeselector"/>
                                    <div class="wikibase-snakview-body">
                                        <div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak">
                                            <a title="Q11173" href="/wiki/Q11173">chemical compound</a>
                                        </div>
                                        ...
    """
        p31 = Path(EO_COMPOUND_DIR, "p31.html")
        tree = etree.parse(str(p31))
        root = tree.getroot()
        child_divs = root.findall("div")
        assert len(child_divs) == 2  # direct children
        child_divs = root.findall(".//div")
        assert len(child_divs) == 109  # all descendants
        snak_views = root.findall(".//div[@class='wikibase-snakview-body']")
        assert len(snak_views) == 6  # snkaviwes (boxes on right)
        # snak_a_views = root.findall(".//div[@class='wikibase-snakview-body']//a[starts-with(@title,'Q')]")
        snak_a_views = root.xpath(".//div[@class='wikibase-snakview-body']//a[starts-with(@title,'Q')]")
        assert len(snak_a_views) == 5  #
        texts = []
        titles = []
        for a in snak_a_views:
            texts.append(a.text)
            titles.append(a.get('title'))
        # assert texts == ['chemical compound',\n 'medication',\n 'p-menthan-3-ol',\n 'menthane monoterpenoids',\n 'LIPID MAPS']
        assert texts == ['chemical compound', 'medication', 'p-menthan-3-ol', 'menthane monoterpenoids', 'LIPID MAPS']
        assert titles == ['Q11173', 'Q12140', 'Q27109870', 'Q66124573', 'Q20968889']

    def test_get_predicate_value(self):
        """tests xpath working of predicate_subject test"""
        tree = html.parse(str(Path(EO_COMPOUND_DIR, "q407418.html")))
        root = tree.getroot()
        hdiv_p31 = root.xpath(".//div[@id='P31']")
        assert len(hdiv_p31) == 1
        qvals = hdiv_p31[0].xpath(".//div[@class='wikibase-snakview-body']//a[starts-with(@title,'Q')]")
        assert len(qvals) == 5

    def test_page_get_values_for_property_id(self):
        """test get all values in triples with given property
        e.g. ?page wdt:P31 ?p31_value
        USEFUL

        """
        page = WikidataPage.create_wikidata_ppage_from_file(Path(EO_COMPOUND_DIR, "q407418.html"))
        qvals = page.get_qitems_for_property_id("P31")
        assert len(qvals) == 5
        assert qvals[0].text == "chemical compound"

    def test_get_property_list(self):
        """gets property list for a page
        """
        page = WikidataPage.create_wikidata_ppage_from_file(Path(EO_COMPOUND_DIR, "q407418.html"))
        property_list = page.get_data_property_list()
        assert len(property_list) == 72
        assert property_list[0].property_name == "instance of"
        assert property_list[0].id == "P31"

    def test_get_predicate_value_1(self):
        tree = html.parse(str(Path(EO_COMPOUND_DIR, "q407418.html")))
        root = tree.getroot()
        qvals = root.xpath(".//div[@id='P31']")[0].xpath(".//div[@class='wikibase-snakview-body']//a[@title='Q11173']")
        assert len(qvals) == 1
        assert qvals[0].text == 'chemical compound'
        qvals = root.xpath(".//div[@id='P31']//div[@class='wikibase-snakview-body']//a[@title='Q11173']")
        assert len(qvals) == 1
        assert qvals[0].text == 'chemical compound'

    @unittest.skip(f"constructor for WikidataPage needs adjusting")
    def test_get_wikidata_predicate_value(self):
        """searches for instance-of (P31) chemical_compound (Q11173) in a wikidata page"""
        pred_id = "P31"
        obj_id = "Q11173"
        file = str(Path(EO_COMPOUND_DIR, "q407418.html"))
        qval = WikidataPage(file).get_predicate_object(pred_id, obj_id)
        assert qval[0].text == 'chemical compound'

    def test_get_title_of_page(self):
        title = WikidataPage("q407418").get_title()
        assert title == "L-menthol"

    def test_get_alias_list(self):
        aliases = WikidataPage("q407418").get_aliases()
        assert len(aliases) >= 30 and aliases[0:2] == ["l-menthol", "levomenthol"]

    def test_get_description(self):
        desc = WikidataPage("q407418").get_description()
        # assert desc == "chemical compound"
        assert "compound" in desc  # wikidata changed this!! 'organic compound used as flavouring and for analgesic properties'

    def test_attval_contains(self):
        """does a concatenated attavle contain a word
        <th scope="col" class="wikibase-entitytermsforlanguagelistview-cell wikibase-entitytermsforlanguagelistview-language">Language</th>

        """
        language_elems = WikidataPage("q407418").get_elements_for_attval_containing_word("class",
                                                                                         "wikibase-entitytermsforlanguagelistview-language")
        assert len(language_elems) == 1
        assert language_elems[0].text == 'Language'

    def test_find_left_properties_and_statements(self):
        """
            <div class="wikibase-snaklistview">
                <div class="wikibase-snaklistview-listview">
                    <div class="wikibase-snakview wikibase-snakview-755d14b02a41025911e80439cb6ed31dcc966768">
                        <div class="wikibase-snakview-property-container">
                            <div class="wikibase-snakview-property" dir="auto">
                               <a title="Property:P662" href="/wiki/Property:P662">PubChem CID</a>
                           </div>
                           ...
        """
        # property_list = WikidataPage("q407418").root.xpath(".//"
        #                                                    "div[@class='wikibase-snaklistview']/"
        #                                                    "div[@class='wikibase-snaklistview-listview']/"
        #                                                    "div/"
        #                                                    "div[@class='wikibase-snakview-property-container']/"
        #                                                    "div[@class='wikibase-snakview-property']/"
        #                                                    "a[starts-with(@title,'Property:')]")

        """<div class="wikibase-statementgroupview-property-label" dir="auto">
              <a title="Property:P274" href="/wiki/Property:P274">chemical formula</a></div>
        """
        lookup = "sroperty"
        lookup = "statement"
        property_list = []
        if lookup == "property":
            classx = "wikibase-statementgroupview-property-label"
            selector = f"@class='{classx}'"
            property_selector = f".//div[@class='{classx}']//a[starts-with(@title,'Property:')]"
            property_list = WikidataPage("q407418").root.xpath(property_selector)
        if lookup == "statement":
            """wikibase-statementgroupview listview-item"""
            # selector = f".//div[@class='wikibase-statementgroupview listview-item']"
            selector = f".//div[starts-with(@class,'wikibase-statementgroupview')]"
            selector = f".//div[@data-property-id]"
            selector = f".//div[@data-property-id]/div[@class='wikibase-statementlistview']//a"
            selector = f".//div[@data-property-id]"
            # selector = f".//div[contains(@class,'wikibase-statementgroupview') and contains(@class,'listview-item')]"
            # selector = f".//div[contains(@class,'listview-item')]"
        print(f" selector {selector} ")

        property_list = WikidataPage("q407418").root.xpath(selector)

        # <!-- property-[statement-list] container TOP LEVEL -->
        # <div class="wikibase-statementgroupview listview-item" id="P31" data-property-id="P31">
        # <!-- property-subject container -->
        # <div class="wikibase-statementgroupview-property">
        #   <div class="wikibase-statementgroupview-property-label" dir="auto"><a title="Property:P31" href="/wiki/Property:P31">instance of</a></div>
        # </div>
        # <!-- statementlist container -->
        # <div class="wikibase-statementlistview">
        # <div class="wikibase-statementlistview-listview">
        # <div id="Q407418$8A24EA26-7C5E-4494-B40C-65356BBB3AA4" class="wikibase-statementview wikibase-statement-Q407418$8A24EA26-7C5E-4494-B40C-65356BBB3AA4 wb-normal listview-item wikibase-toolbar-item">
        # <div class="wikibase-statementview-rankselector"><div class="wikibase-rankselector ui-state-disabled">
        # <!-- "button?" -->
        # <span class="ui-icon ui-icon-rankselector wikibase-rankselector-normal" title="Normal rank"></span>
        # </div></div>
        # <div class="wikibase-statementview-mainsnak-container">
        # <div class="wikibase-statementview-mainsnak" dir="auto"><div class="wikibase-snakview wikibase-snakview-e823b98d1498aa78e139709b1b02f5decd75c887">
        # <div class="wikibase-snakview-property-container">
        # <div class="wikibase-snakview-property" dir="auto"></div>
        # </div>
        # <!-- object-value-container -->
        # <div class="wikibase-snakview-value-container" dir="auto">
        # <div class="wikibase-snakview-typeselector"></div>
        # <div class="wikibase-snakview-body">
        # <div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak"><a title="Q11173" href="/wiki/Q11173">chemical compound</a></div>
        # <div class="wikibase-snakview-indicators"></div>
        # </div>
        # </div>
        # </div></div>
        # <div class="wikibase-statementview-qualifiers"></div>
        # </div>
        # <span class="wikibase-toolbar-container wikibase-edittoolbar-container"><span class="wikibase-toolbar wikibase-toolbar-item wikibase-toolbar-container"><span class="wikibase-toolbarbutton wikibase-toolbar-item wikibase-toolbar-button wikibase-toolbar-button-edit"><a href="#" title=""><span class="wb-icon"></span>edit</a></span></span></span>
        # <div class="wikibase-statementview-references-container">
        # <div class="wikibase-statementview-references-heading"><a class="ui-toggler ui-toggler-toggle ui-state-default"><span class="ui-toggler-icon ui-icon ui-icon-triangle-1-s"></span><span class="ui-toggler-label">0 references</span></a><div class="wikibase-tainted-references-container" data-v-app=""><div class="wb-tr-app"><!----></div></div></div>
        # <div class="wikibase-statementview-references "><div class="wikibase-addtoolbar wikibase-toolbar-item wikibase-toolbar wikibase-addtoolbar-container wikibase-toolbar-container"><span class="wikibase-toolbarbutton wikibase-toolbar-item wikibase-toolbar-button wikibase-toolbar-button-add"><a href="#" title=""><span class="wb-icon"></span>add reference</a></span></div></div>
        # </div>
        # </div><div id="Q407418$A25EE807-DBE3-47CA-9272-00BF975DAEA8" class="wikibase-statementview wikibase-statement-Q407418$A25EE807-DBE3-47CA-9272-00BF975DAEA8 wb-normal listview-item wikibase-toolbar-item">
        # <div class="wikibase-statementview-rankselector"><div class="wikibase-rankselector ui-state-disabled">
        # <span class="ui-icon ui-icon-rankselector wikibase-rankselector-normal" title="Normal rank"></span>
        # </div></div>
        # <div class="wikibase-statementview-mainsnak-container">
        # <div class="wikibase-statementview-mainsnak" dir="auto"><div class="wikibase-snakview wikibase-snakview-87cdd435c7bb91eadb3355615e99ee224aa44984">
        # <div class="wikibase-snakview-property-container">
        # <div class="wikibase-snakview-property" dir="auto"></div>
        # </div>
        # <!-- object-value-container -->
        # <div class="wikibase-snakview-value-container" dir="auto">
        # <div class="wikibase-snakview-typeselector"></div>
        # <div class="wikibase-snakview-body">
        # <div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak"><a title="Q12140" href="/wiki/Q12140">medication</a></div>
        # <div class="wikibase-snakview-indicators"></div>
        # <!-- ..... -->
        # </div>
        # </div></div>
        # </div></div>
        # </div></div><div class="wikibase-addtoolbar wikibase-toolbar-item wikibase-toolbar wikibase-addtoolbar-container wikibase-toolbar-container"><span class="wikibase-toolbarbutton wikibase-toolbar-item wikibase-toolbar-button wikibase-toolbar-button-add"><a href="#" title=""><span class="wb-icon"></span>add reference</a></span></div></div>
        # </div>
        # </div>
        # </div>
        # <span class="wikibase-toolbar-container"></span>
        # <span class="wikibase-toolbar-wrapper"><div class="wikibase-addtoolbar wikibase-toolbar-item wikibase-toolbar wikibase-addtoolbar-container wikibase-toolbar-container"><span class="wikibase-toolbarbutton wikibase-toolbar-item wikibase-toolbar-button wikibase-toolbar-button-add"><a href="#" title="Add a new value"><span class="wb-icon"></span>add value</a></span></div></span></div>
        # </div>"""
        # """wikibase-statementgroupview listview-item"""

        wikidata_page = WikidataPage("q407418")
        property_list = wikidata_page.get_data_property_list()
        assert 78 >= len(property_list) >= 70
        assert wikidata_page.get_property_id_list()[:10] == [
            'P31', 'P279', 'P361', 'P117', 'P8224', 'P2067', 'P274', 'P233', 'P2017', 'P2054']
        assert wikidata_page.get_property_name_list()[:10] == [
            'instance of', 'subclass of', 'part of', 'chemical structure', 'molecular model or crystal lattice model',
            'mass', 'chemical formula', 'canonical SMILES', 'isomeric SMILES', 'density']

        properties_dict = WikidataProperty.get_properties_dict(property_list)
        dict_str = pprint.pformat(properties_dict)
        print(f"\ndict: \n"
              f"{dict_str}")
        assert properties_dict['P662'] == {'name': 'PubChem CID', 'value': '16666'}

# all wikidata asserts are fragile
        # assert properties_dict['P31'] == {'name': 'instance of',
        #                                   'statements': {
        #                                       'Q11173': 'chemical compound',
        #                                       'Q12140': 'medication',
        #                                       'Q27109870': 'p-menthan-3-ol',
        #                                       'Q66124573': 'menthane monoterpenoids'}}

        # retains the order of addition
        # skip, fragile
        # assert sorted(list(properties_dict.keys())) == sorted([
        #     'P31', 'P279', 'P361', 'P117', 'P8224', 'P2067', 'P274', 'P233', 'P2017', 'P2054', 'P2101', 'P2102',
        #     'P2128', 'P2275', 'P703', 'P2175', 'P129', 'P366', 'P2789', 'P2868', 'P1343', 'P1987', 'P1748', 'P527',
        #     'P1889', 'P935', 'P373', 'P910', 'P268', 'P227', 'P8189', 'P244', 'P234', 'P235', 'P231', 'P661',
        #     'P662', 'P1579', 'P683', 'P592', 'P6689', 'P4964', 'P679', 'P2062', 'P3117', 'P8494', 'P2840', 'P232',
        #     'P2566', 'P5930', 'P8121', 'P7049', 'P595', 'P3345', 'P715', 'P2057', 'P2064', 'P652', 'P2115', 'P665',
        #     'P2063', 'P8313', 'P1417', 'P646', 'P1296', 'P8408', 'P6366', 'P2004', 'P10283', 'P3417', 'P5076', 'P5082'
        # ])

    def test_update_dictionary_with_wikidata_ids(self):
        """Update dictionary by adding Wikidata IDs where missing"""
        """
<dictionary title="dict_5">
    <entry name="allyl isovalerate" term="allyl isovalerate"></entry>
    <entry name="allyl octanoate" term="allyl octanoate" wikidataID="Q27251951"></entry>
    <entry name="allylhexanoate" term="allylhexanoate" wikidataID="Q3270746"></entry>
    <entry name="alpha-alaskene" term="alpha-alaskene"></entry>  <!-- not in Wikidata -->
    <entry name="alpha-amyrenone" term="alpha-amyrenone"></entry> <!-- not in Wikidata -->
</dictionary>        """
        path = Path(EO_COMPOUND_DIR, "dict_5.xml")
        dictionary = AmiDictionary.create_from_xml_file(str(path))
        assert len(dictionary.entries) == 5
        entry = dictionary.get_lxml_entry("allylhexanoate")
        assert entry.get(WIKIDATA_ID) == "Q3270746"

        entry = dictionary.get_lxml_entry("allyl isovalerate")
        assert entry.get(WIKIDATA_ID) is None
        dictionary.lookup_and_add_wikidata_to_entry(entry)
        assert entry.get(WIKIDATA_ID) == "Q27155908"

        dictionary.write_to_file(Path(Resources.TEMP_DIR, EO_COMPOUND, "dict_5.xml"))

    @unittest.skip("LONG DOWNLOAD")
    def test_add_wikidata_to_complete_dictionary_with_filter(self):
        """Takes existing dictionary and looks up Wikidata stuff for entries w/o WikidataID
        Need dictionary in AmiDictionary format"""
        input_dir = EO_COMPOUND_DIR
        output_dir = Path(Resources.TEMP_DIR, EO_COMPOUND)
        start_entry = 0
        end_entry = 10
        input_path = Path(input_dir, "eoCompound1.xml")
        assert input_path.exists(), f"{input_path} should exist"
        dictionary = AmiDictionary.create_from_xml_file(str(input_path))
        assert len(dictionary.entries) == 2114
        description = "chemical compound"

        for entry in dictionary.entries[start_entry: end_entry]:
            wikidata_id = AmiDictionary.get_wikidata_id(entry)
            if not AmiDictionary.is_valid_wikidata_id(wikidata_id):
                term = AmiDictionary.get_term(entry)
                # print(f"no wikidataID in entry: {term}")
                dictionary.lookup_and_add_wikidata_to_entry(entry, allowed_descriptions=description)
                wikidata_id = AmiDictionary.get_wikidata_id(entry)
                if wikidata_id is None:
                    print(f"no wikidata entry for {term}")
                    entry.attrib[WIKIDATA_ID] = AmiDictionary.NOT_FOUND
                else:
                    print(f"found {wikidata_id} for {term} desc = {entry.get('desc')}")
        dictionary.write_to_file(Path(output_dir, "eoCompound1.xml"))

    def test_disambiguation(self):
        """attempts to disambiguate the result of PMR-wikidata lookup
        """
        input_dir = EO_COMPOUND_DIR
        output_dir = Path(Resources.TEMP_DIR, EO_COMPOUND)
        output_dir.mkdir(exist_ok=True)
        input_path = Path(input_dir, "disambig.xml")
        assert input_path.exists(), f"{input_path} should exist"
        dictionary = AmiDictionary.create_from_xml_file(str(input_path))
        assert len(dictionary.entries) == 9
        allowed_descriptions = {
            "chemical compound": "0.9",
            "group of isomers": "0.7",
        }
        dictionary = AmiDictionary.create_from_xml_file(str(input_path))
        for entry in dictionary.entries:
            dictionary.disambiguate_wikidata_by_desc(entry)
        dictionary.write_to_file(Path(output_dir, "disambig.xml"))

    def test_extract_multiple_wikidata_hits_ghg(self):
        """
        test multiple hits for 'GHG' and use heuristics to find the most likely
        uses dictionary created from abbreviations via docanalysis
        requires WIKIDATA LOOKUP on Internet

        ghg entry is:
  <entry term="GHG" name="Greenhouse Gas" >
    <raw wikidataID="['Q167336', 'Q3588927', 'Q925312', 'Q57584895', 'Q110612403', 'Q112192791', 'Q140182']"/>
  </entry>

        """

        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        assert ami_dict is not None
        ghg = "GHG"
        ghg_element = ami_dict.get_lxml_entry(ghg)
        assert ghg_element, f"entry for {ghg} is None, probably not found"
        assert type(ghg_element) is lxml.etree._Element, f"entry has type {type(ghg_element)}"
        ghg_entry = AmiEntry.create_from_element(ghg_element)
        assert type(ghg_entry) is AmiEntry, f"ami_entry is type {type(ghg_entry)}"
        assert ghg_entry is not None
        wikidata_id = ghg_entry.wikidata_id
        assert not wikidata_id
        raw_wikidata_ids = ghg_entry.get_raw_child_wikidata_ids()
        assert len(raw_wikidata_ids) == 7
        assert raw_wikidata_ids == [
            'Q167336',
            'Q3588927',
            'Q925312',
            'Q57584895',
            'Q110612403',
            'Q112192791',
            'Q140182'
        ]

    def test_get_best_match_for_ghg(self):
        """
        gets best wikidata match for term
        WORKING
entry like:
  <entry term="GHG" name="Greenhouse Gas" >
    <raw wikidataID="['Q167336', 'Q3588927', 'Q925312', 'Q57584895', 'Q110612403', 'Q112192791', 'Q140182']"/>
  </entry>

        """
        ami_dict = AmiDictionary.create_from_xml_file(Resources.IPCC_CHAP02_ABB_DICT)
        term = "GHG"
        ami_entry = ami_dict.get_ami_entry(term)
        matched_pages = ami_entry.get_wikidata_pages_from_raw_wikidata_ids_matching_wikidata_page_title()
        assert len(matched_pages) == 1 and matched_pages[0].get_id() == "Q167336"

    def test_get_instances(self):
        """<div class="wikibase-statementview-mainsnak-container">
<div class="wikibase-statementview-mainsnak" dir="auto"><div class="wikibase-snakview wikibase-snakview-e823b98d1498aa78e139709b1b02f5decd75c887">
<div class="wikibase-snakview-property-container">
<div class="wikibase-snakview-property" dir="auto"></div>
</div>
<div class="wikibase-snakview-value-container" dir="auto">
<div class="wikibase-snakview-typeselector"></div>
<div class="wikibase-snakview-body">
<div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak"><a title="Q11173" href="/wiki/Q11173">chemical compound</a></div>
<div class="wikibase-snakview-indicators"></div>
</div>
</div>
</div></div>
<div class="wikibase-statementview-qualifiers"></div>
</div>"""
        pass

    @unittest.skip("LONG DOWNLOAD")
    def test_add_wikidata_to_imageanalysis_output(self):
        """creates dictionary from list of terms and looks up Wikidata"""
        terms = [
            "isopentyl-diphosphate delta-isomerase"
            "squalene synthase",
            "squalene monoxygenase",
            "phytoene synthase",
            "EC 2.5.1.6",
            "EC 4.4.1.14",
            "EC 1.14.17.4",
            "ETRL",
            "ETR2",
            "ERS1",
            "EIN4",
        ]
        with open(Path(RESOURCES_DIR, EO_COMPOUND, "compounds.txt"), "r") as f:
            terms = f.readlines()
            assert 100 > len(terms) > 87
        wikidata_lookup = WikidataLookup()
        # qitems, descs = wikidata_lookup.lookup_items(terms)
        temp_dir = Path(TEMP_DIR, "wikidata")
        if not temp_dir.exists():
            temp_dir.mkdir()
        # limit = 10000
        limit = 5
        amidict, dictfile = AmiDictionary.create_dictionary_from_words(terms[:limit], title="compounds",
                                                                                  wikidata=True, outdir=temp_dir)
        print(f"wrote to {dictfile}")
        assert os.path.exists(dictfile)



    def test_wikidata_extractor(self):
        query = '2-fluorobenzoic acid'
        extractor = WikidataExtractor('en')
        id = extractor.search(query)
        id_dict = extractor.load(id)
        print(id_dict)

    def test_simple_wikidata_query(self):
        """get ID list for query results
        see https://www.wikidata.org/w/api.php for options
        each entry has a small number of attributes (e.g. description, URL, )"""
        query = "isomerase"
        url_str = f"https://www.wikidata.org/w/api.php?" \
                  f"action=wbsearchentities" \
                  f"&search={query}" \
                  f"&language=en" \
                  f"&format=json"
        response = requests.get(url_str)
        js = response.json()
        print(pprint.pformat(js))

    def test_wikidata_id_lookup(self):
        """test query wikidata by ID
        """
        ids = "Q11966262"  # "Dyschirius politus" a species of insect
        url_str = f"https://www.wikidata.org/w/api.php?" \
                  f"action=wbgetentities" \
                  f"&ids={ids}" \
                  f"&language=en" \
                  f"&format=json"
        response = requests.get(url_str)
        response_js = response.json()["entities"][ids]
        # print(f"pages for {ids}\n", pprint.pformat(response_js))
        assert list(response_js.keys()) == ['pageid', 'ns', 'title', 'lastrevid', 'modified', 'type', 'id', 'labels',
                                            'descriptions', 'aliases', 'claims', 'sitelinks']
        assert response_js["id"] == ids
        assert response_js["title"] == "Q11966262"
        assert response_js["labels"]["en"]["value"] == "Dyschirius politus"
        assert response_js["descriptions"]["en"]["value"] == "species of insect"
        assert list(response_js["claims"].keys()) == [
            'P225', 'P105', 'P171', 'P31', 'P685', 'P846', 'P1939', 'P373', 'P815', 'P3151', 'P3186',
            'P3405', 'P2464', 'P1843', 'P7202', 'P7552', 'P6105', 'P6864', 'P8915', 'P3240', 'P2671',
            'P3606', 'P8707', 'P10243'
        ]
        ids = "P117"  # chemical compound
        url_str = f"https://www.wikidata.org/w/api.php?" \
                  f"action=wbgetentities" \
                  f"&ids={ids}" \
                  f"&language=en" \
                  f"&format=json"
        response = requests.get(url_str)
        response_js = response.json()["entities"][ids]
        # print(f"pages for {ids}\n", pprint.pformat(response_js))
        assert list(response_js.keys()) == ['pageid', 'ns', 'title', 'lastrevid', 'modified', 'type', 'datatype', 'id',
                                            'labels', 'descriptions', 'aliases', 'claims']
        assert response_js["id"] == "P117"
        assert response_js["title"] == "Property:P117"
        assert response_js["labels"]["en"]["value"] == "chemical structure"
        assert response_js["descriptions"]["en"][
                   "value"] == "image of a representation of the structure for a chemical compound"
        assert list(response_js["claims"].keys()) == ['P31', 'P1855', 'P3254', 'P2302', 'P1629', 'P1647', 'P2875',
                                                      'P1659']

    #        wikidata_page = WikidataPage.create_from_response(response)

    def test_multiple_ids(self):
        ids = "P31|P117"
        url_str = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={ids}&language=en&format=json"
        response = requests.get(url_str)
        json_dict = response.json()
        assert list(json_dict['entities'].keys()) == ['P31', 'P117']
        assert list(json_dict['entities']['P117'].keys()) == [
            'pageid', 'ns', 'title', 'lastrevid', 'modified', 'type', 'datatype', 'id', 'labels',
            'descriptions', 'aliases', 'claims']
        assert json_dict['entities']['P117']['labels']['en']['value'] == 'chemical structure'
        assert json_dict['entities']['P31']['labels']['en']['value'] == 'instance of'

    def test_read_wikidata_filter(self):
        path = Path(RESOURCES_DIR, "filter00.json")
        filter = WikidataFilter.create_filter(path)
        assert filter.json['plugh'] == "xyzzy"
        assert filter.json['filter']['description'] == "chemical"
        assert filter.json['filter'][
                   'regex'] == "(chemical compound|chemical element)", f"found {filter.json['filter']['regex']}"


if __name__ == '__main__':
    unittest.main()
