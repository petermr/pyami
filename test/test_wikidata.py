# Tests wikipedia and wikidata methods under pytest
import os
import unittest
from pathlib import Path
import logging
from lxml import etree, html
# local
from py4ami.wikimedia import WikidataPage, ParserWrapper
from py4ami.dict_lib import AmiDictionary, WIKIDATA_ID

try:
    from py4ami.wikimedia import WikidataLookup
    from py4ami.dict_lib import AMIDict, AMIDictError, Entry

    logging.info(f"loaded py4ami.dict_lib")
except Exception:
    try:
        from py4ami.wikimedia import WikidataLookup
        from py4ami.dict_lib import AMIDict, AMIDictError, Entry
    except Exception as e:
        logging.error(f"Cannot import from py4ami.dict_lib")

RESOURCES_DIR = Path(Path(__file__).parent.parent, "test", "resources")
TEMP_DIR = Path(Path(__file__).parent.parent, "temp")


# NOTE some of these are lengthy (seconds) as they lookup on the Net

class TestWikidataLookup:

    def test_lookup_wikidata_acetone(self):
        term = "acetone"
        wikidata_lookup = WikidataLookup()
        qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
        assert qitem0 == "Q49546"
        assert desc == "chemical compound"
        assert wikidata_hits == ['Q49546', 'Q24634417', 'Q329022', 'Q63986955', 'Q4673277']

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
        assert qitem0 == "Q170304"  # dopamine???
        assert desc == "hormone and neurotransmitter"
        # this needs mending as it found dopmamine (4-(2-azanylethyl)benzene-1,2-diol)
        assert wikidata_hits == ['Q170304', 'Q2270', 'Q15779', 'Q186242', 'Q28917']

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
        temp_dir = Path(Path(__file__).parent.parent, "temp")
        dictfile, amidict = AMIDict.create_from_list_of_strings_and_write_to_file(terms, title="parkinsons",
                                                                                  wikidata=True, directory=temp_dir)
        assert os.path.exists(dictfile)

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
        p31 = Path(RESOURCES_DIR, "p31.html")
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
        tree = html.parse(str(Path(RESOURCES_DIR, "q407418.html")))
        root = tree.getroot()
        p31 = root.xpath(".//div[@id='P31']")
        assert len(p31) == 1
        qvals = p31[0].xpath(".//div[@class='wikibase-snakview-body']//a[starts-with(@title,'Q')]")
        assert len(qvals) == 5

    def test_get_predicate_value_1(self):
        tree = html.parse(str(Path(RESOURCES_DIR, "q407418.html")))
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
        pred = "P31"
        obj = "Q11173"
        file = str(Path(RESOURCES_DIR, "q407418.html"))
        qval = WikidataPage(file).get_predicate_object(pred, obj)
        assert qval[0].text == 'chemical compound'

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
        path = Path(RESOURCES_DIR, "dict_5.xml")
        dictionary = AmiDictionary(str(path))
        assert len(dictionary.entries) == 5
        entry = dictionary.get_entry("allylhexanoate")
        assert entry.get(WIKIDATA_ID) == "Q3270746"

        entry = dictionary.get_entry("allyl isovalerate")
        assert entry.get(WIKIDATA_ID) is None
        dictionary.add_wikidata_to_entry(entry)
        assert entry.get(WIKIDATA_ID) == "Q27155908"

        dictionary.write(Path(TEMP_DIR, "dict_5.xml"))




