# Tests wikipedia and wikidata methods under pytest
import os
import unittest
from pathlib import Path
import logging

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

# NOTE some of these are lengthy (seconds) as they lookup on the Net


def test_lookup_wikidata_acetone():
    term = "acetone"
    wikidata_lookup = WikidataLookup()
    qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
    assert qitem0 == "Q49546"
    assert desc == "chemical compound"
    assert wikidata_hits == ['Q49546', 'Q24634417', 'Q329022', 'Q63986955', 'Q4673277']


def test_lookup_wikidata_bad():
    """This fails"""
    term = "benzene"
    wikidata_lookup = WikidataLookup()
    qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
    assert qitem0 == "Q170304"  # dopamine???
    assert desc == "hormone and neurotransmitter"
    # this needs mending as it found dopmamine (4-(2-azanylethyl)benzene-1,2-diol)
    assert wikidata_hits == ['Q170304', 'Q2270', 'Q15779', 'Q186242', 'Q28917']

@unittest.skip(reason="NET, long")
def test_lookup_solvents():
    terms = ["acetone", "chloroform", "ethanol"]
    wikidata_lookup = WikidataLookup()
    qitems, descs = wikidata_lookup.lookup_items(terms)
    assert qitems == ['Q49546', 'Q172275', 'Q153']
    assert descs == ['chemical compound', 'chemical compound', 'chemical compound']


@unittest.skip(reason="Net, Long")
def test_lookup_parkinsons():
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

@unittest.skip(reason="NYI")
def test_screen_qnumber_compounds():
    """find Wikidata items with given property
    uses the HTML, tacky but works

    does entry contain a property/Qnumber?
    <div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak"><a title="Q11173" href="/wiki/Q11173">chemical compound</a></div>
    """
    """Statements/instance_of/tomli wiki/Q11173">chemical compound<"""

    """</div><div id="toc"></div><h2  class="wb-section-heading section-heading wikibase-statements" dir="auto"><span class="mw-headline" id="claims">Statements</span></h2><div class="wikibase-statementgrouplistview"><div class="wikibase-listview"><div class="wikibase-statementgroupview" id="P31" data-property-id="P31">
    <div class="wikibase-statementgroupview-property">
    <div class="wikibase-statementgroupview-property-label" dir="auto"><a title="Property:P31" href="/wiki/Property:P31">instance of</a></div>
    </div>
    <div class="wikibase-statementlistview">
    <div class="wikibase-statementlistview-listview">
    <div id="Q207688$D736BECB-6723-417B-92E0-1E28B3207B25" class="wikibase-statementview wikibase-statement-Q207688$D736BECB-6723-417B-92E0-1E28B3207B25 wb-normal">
    <div class="wikibase-statementview-rankselector"><div class="wikibase-rankselector ui-state-disabled">
    <span class="ui-icon ui-icon-rankselector wikibase-rankselector-normal" title="Normal rank"></span>
    </div></div>
    <div class="wikibase-statementview-mainsnak-container">
    <div class="wikibase-statementview-mainsnak" dir="auto"><div class="wikibase-snakview wikibase-snakview-ced1023cd4dc541d794333178a2c290e308f870c">
    <div class="wikibase-snakview-property-container">
    <div class="wikibase-snakview-property" dir="auto"></div>
    </div>
    <div class="wikibase-snakview-value-container" dir="auto">
    <div class="wikibase-snakview-typeselector"></div>
    <div class="wikibase-snakview-body">
    <div class="wikibase-snakview-value wikibase-snakview-variation-valuesnak"><a title="Q902638" href="/wiki/Q902638">excipient</a></div>
    <div class="wikibase-snakview-indicators"></div>
    </div>
    </div>
    </div></div>
    <div class="wikibase-statementview-qualifiers"></div>
    </div>
    <span class="wikibase-toolbar-container"></span>
    <div class="wikibase-statementview-references-container">
    <div class="wikibase-statementview-references-heading">0 references</div>
    <div class="wikibase-statementview-references "></div>
    </div>
    </div><div id="Q207688$600787db-478a-de9f-762b-c79d7e5b0fb1" class="wikibase-statementview wikibase-statement-Q207688$600787db-478a-de9f-762b-c79d7e5b0fb1 wb-normal">
    <div class="wikibase-statementview-rankselector"><div class="wikibase-rankselector ui-state-disabled">
    <span class="ui-icon ui-icon-rankselector wikibase-rankselector-normal" title="Normal rank"></span>
    </div></div>
    <div class="wikibase-statementview-mainsnak-container">
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
    </div>"""
    pass