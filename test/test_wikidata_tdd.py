# Tests wikipedia and wikidata methods under pytest

from py4ami.wikimedia import WikidataLookup

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
    assert qitem0 == "Q170304" # dopamine???
    assert desc == "hormone and neurotransmitter"
    # this needs mending as it found dopmamine (4-(2-azanylethyl)benzene-1,2-diol)
    assert wikidata_hits == ['Q170304', 'Q2270', 'Q15779', 'Q186242', 'Q28917']

def test_lookup_solvents():
    terms = ["acetone", "chloroform", "ethanol"]
    wikidata_lookup = WikidataLookup()
    qitems, descs = wikidata_lookup.lookup_items(terms)
    assert qitems == ['Q49546', 'Q172275', 'Q153']
    assert descs == ['chemical compound', 'chemical compound', 'chemical compound']

