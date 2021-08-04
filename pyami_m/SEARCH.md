# Alpha code for searching document corpus

This outdates (2021-04-08) other docs

## Overall objective is to combine `pygetpapers` and `pyami` (search_lib) into

download PAPERS into PROJECTS , find SECTIONS and index with (DICTIONARIES and/or PATTERNS) into a searchable KNOWLEDGEBASE and analyse for new INSIGHTS.


## search_lib.py
The scheme is:
````
search SECTIONS in PROJECTS with (DICTIONARIES and/or PATTERNS) with (DISPLAY and/or ANALYSIS) options
````

The command line is typically:
````
python search_lib.py --proj p1 [p2...] --dict d1 [d2...] --sect s1 [s2...] --patt p1 [p2...] [--plot pl1 [pl2...]]

````

## help
````
python search_lib 
````
gives
````
usage: search_lib.py [-h] [-d [DICT [DICT ...]]] [-s [SECT [SECT ...]]]
                     [-p [PROJ [PROJ ...]]] [--patt PATT [PATT ...]]
                     [--demo [DEMO [DEMO ...]]] [-l LOGLEVEL] [--plot]
                     [--nosearch] [--maxbars [MAXBARS]]
                     [--languages LANGUAGES [LANGUAGES ...]]

Search sections with dictionaries and patterns

optional arguments:
  -h, --help            show this help message and exit
  -d [DICT [DICT ...]], --dict [DICT [DICT ...]]
                        dictionaries to search with, empty gives list
  -s [SECT [SECT ...]], --sect [SECT [SECT ...]]
                        sections to search; empty gives all
  -p [PROJ [PROJ ...]], --proj [PROJ [PROJ ...]]
                        projects to search; empty will give list
  --patt PATT [PATT ...]
                        patterns to search with; regex may need quotingsearch SECTIONS in PROJECTS with (DICTIONARIES and/or PATTERNS) with DISPLAY options
  --demo [DEMO [DEMO ...]]
                        simple demos (NYI). empty gives list. May need
                        downloading corpora
  -l LOGLEVEL, --loglevel LOGLEVEL
                        debug level (NYI)
  --plot                plot params (NYI)
  --nosearch            search (NYI)
  --maxbars [MAXBARS]   max bars on plot (NYI)
  --languages LANGUAGES [LANGUAGES ...]
                        languages (NYI)
````   

## demos
These are a good way of getting started. 
````
python search_lib.py --demo d1 [d2...]
````

To get a list of demos:
````
python search_lib.py --demo 
````
gives:
````
no demo given, choose from 
'ethics', 'luke', 'plant_parts', 'worcester', 'word'
````
Note that some demos are in other repos and may not be loaded. We will gradually trim them down and move into this project.

## projects
There are a number of hardcoded corpora / projects. To get a list
````
python search_lib.py --proj 
````
gives:
````

================= 
 must give projects; here are some to test with, but they may need checking out
liion10 => Li-ion batteries
ffml20 => forcefields + ML
oil26 => 26 oil plant papers
oil186 => 186 oil plant papers
cct => steel cooling curves
disease => disease papers
diffprot => differential protein expression
worc_synth => chemical synthesese
worc_explosion => explosion hazards
activity => biomedical activities
hydrodistil => hydrodistillation
invasive => invasive plants
plantpart => plant parts
=================
finished search

## dictionaries
There are a number of hardcoded dictionaries. To get a list
````
python search_lib.py --dict 
````
gives:
````
running search main
core dicts ['activity', 'country', 'disease', 'compound', 'plant', 'plant_genus', 'organization', 'plant_compound', 'plant_part', 'invasive_plant']
````
(There are 50 more, but not linked into Wikidata)

## sections 
There are a number of hardcoded document sections. To get a list
````
python search_lib.py --dict 
````
gives:
````
sections to be used; ALL uses whole document (Not yet tested)

========SECTIONS===========
['abstract', 'acknowledge', 'affiliation', 'author', 'background', 'discussion', 'empty', 'ethics', 'fig_caption', 'front', 'introduction', 'jrnl_title', 'keyword', 'method', 'material', 'octree', 'pdfimage', 'pub_date', 'publisher', 'reference', 'results', 'results', 'sections', 'svg', 'table', 'title', 'word']
===========================
````

## Patterns
Documentatioo be added (they have been impemented). It includes regular expressions and capitalization (and more to come)

## Flags
These control display, output, etc. and are not fully impemented. 


## demo run ("ethics")
This runs 3 word patterns on the `ethics` sections of documents. No dictiomary is used. Matplot images will be added later.
````
(base) pm286macbook:python pm286$ python search_lib.py --demo ethics
running search main
DEMOS
RUN DEMOS: ['ethics']
core dicts dict_keys(['activity', 'country', 'disease', 'compound', 'plant', 'plant_genus', 'organization', 'plant_compound', 'plant_part', 'invasive_plant'])
name country
name disease
filters NYI
AB12 = ^[A-Z]{1,}[^\s]*\d{1,}$
PATT:  AB12 ^[A-Z]{1,}[^\s]*\d{1,}$
all_capz = _ALLCAPS
_all = _ALL
***** project /Users/pm286/projects/openVirus/miniproject/disease/1-part
_DESC <class 'str'> ethics statements; often in methods but found elsewhere
PROJ <class 'str'> /Users/pm286/projects/openVirus/miniproject/disease/1-part
TREE <class 'str'> *
SECTS <class 'str'> sections
SUBSECT <class 'str'> **
SUBSUB <class 'str'> *ethic*
FILE <class 'str'> *p*
SUFFIX <class 'str'> xml
glob /Users/pm286/projects/openVirus/miniproject/disease/1-part/*/sections/**/*ethic*/*p*.xml
files 69
***** section_files ethics 69
file /Users/pm286/projects/openVirus/miniproject/disease/1-part/PMC7343349/sections/1_body/1_methods_and_materials/1_ethics_statement/1_p.xml
lang: en 
 [('cameroon', 3), ('bangladesh', 3), ('kenya', 3), ('spain', 2)]
lang: en 
 [('measles', 2)]
lang: en 
 [('A/Leningrad/134/17/57', 2), ('A/17/duck/Potsdam/86/92', 2), ('BSL-3', 2)]
lang: en 
 [('WNV', 4), ('(IACUC)', 3), ('RSV', 3), ('(H2N2)', 2), ('HIV/AIDS', 2), ('CONEP', 2), ('SRC', 2), ('CETEA', 2), ('(DC18RESI0100).\n', 2), ('IACUC', 2), ('IRB', 2), ('(FAMERP),', 2), ('KEMRI', 2), ('2010/63/UE.\n', 2), ('BSL-3', 2), ('UTMB', 2)]
lang: en 
 [('Committee', 34), ('consent', 30), ('Health', 26), ('obtained', 26), ('informed', 26), ('Animal', 25), ('Ethics', 25), ('animal', 22), ('National', 19), ('number', 19), ('Institutional', 17), ('Care', 17), ('approval', 17), ('Use', 15), ('Review', 15), ('guidelines', 15), ('collected', 14), ('patients', 14), ('accordance', 14), ('written', 14), ('participants', 14), ('ethical', 14), ('Laboratory', 13), ('surveillance', 13), ('provided', 12), ('Institute', 11), ('use', 11), ('animals', 10), ('Ethical', 10), ('part', 10), ('protocol', 9),
 ...
 ('Command', 2), ('Donor', 2), ('code', 2), ('authorities.\n', 2), ('article', 2), ('contain', 2), ('included', 2), ('UTMB', 2), ('includes', 2), ('Personal', 2), ('Egyptian', 2), ('pathogenic', 2), ('Beijing', 2)]
END DEMO
finished search
````
## demo ("plant parts")
```
(base) pm286macbook:python pm286$ python search_lib.py --demo plant_parts
running search main
DEMOS
RUN DEMOS: ['plant_parts']
core dicts dict_keys(['activity', 'country', 'disease', 'compound', 'plant', 'plant_genus', 'organization', 'plant_compound', 'plant_part', 'invasive_plant'])
name activity
name compound
name invasive_plant
name plant
name plant_compound
name plant_part
name plant_genus
filters NYI
***** project /Users/pm286/projects/CEVOpen/searches/oil186
_DESC <class 'str'> introduction or background; looks for these words anywhere in file titles
PROJ <class 'str'> /Users/pm286/projects/CEVOpen/searches/oil186
TREE <class 'str'> *
SECTS <class 'str'> **
SUBSECT <class 'str'> *introduction*
SUBSUB <class 'str'> **
FILE <class 'str'> *
SUFFIX <class 'str'> xml
glob /Users/pm286/projects/CEVOpen/searches/oil186/*/**/*introduction*/**/*.xml
_DESC <class 'str'> introduction or background; looks for these words anywhere in file titles
PROJ <class 'str'> /Users/pm286/projects/CEVOpen/searches/oil186
TREE <class 'str'> *
SECTS <class 'str'> **
SUBSECT <class 'str'> *background*
SUBSUB <class 'str'> **
FILE <class 'str'> *
SUFFIX <class 'str'> xml
glob /Users/pm286/projects/CEVOpen/searches/oil186/*/**/*background*/**/*.xml
files 1002
***** section_files introduction 1002
file /Users/pm286/projects/CEVOpen/searches/oil186/PMC5622403/sections/1_body/0_1__introduction/0_title.xml
lang: en 
 [('antioxidant', 164), ('antifungal', 70), ('analgesic', 15), ('cosmetics', 10), ('antiparasitic', 8), ('cytotoxicity', 8), ('diuretic', 8), ('perfume', 7), ('stimulant', 7), ('antiseptic', 7), ('sedative', 5), ('carminative', 5), ('antipyretic', 5), ('anthelmintic', 5), ('anxiolytic', 4), ('antimalarial', 4), ('insecticide', 4), ('fungicide', 4), ('decongestant', 3), ('hypolipidemic', 3), ('antiprotozoal', 3), ('antispasmodic', 3), ('laxative', 3), ('astringent', 2), ('emmenagogue', 2), ('adjuvant', 2), ('acaricide', 2)]
lang: en 
 [('carvacrol', 18), ('eugenol', 14), ('thymol', 14), ('caryophyllene', 4), ('chavicol', 4), ('ethanol', 4), ('nerol', 3), ('p-cymene', 3), ('sabinene', 2), ('geraniol', 2), ('terpinolene', 2), ('cedrol', 2), ('estragole', 2), ('pulegone', 2), ('acetone', 2), ('hexane', 2), ('(e)-cinnamaldehyde', 2)]
lang: en 
 []
lang: en 
 [('basil', 32), ('cinnamon', 24), ('oregano', 12), ('marjoram', 2)]
lang: en 
 [('seed', 67), ('fruit', 41), ('leaf', 37), ('root', 31), ('herb', 31), ('resin', 20), ('bark', 17), ('flower', 14), ('flowering', 9), ('wood', 7), ('apical', 4), ('peel', 4), ('epidermis', 3), ('grass', 3), ('rhizome', 3), ('trichomes', 2), ('branch', 2)]
lang: en 
 [('rudbeckia', 23), ('mentha', 22), ('citrus', 21), ('thymus', 20), ('microbiota', 19), ('ocimum', 15), ('india', 14), ('origanum', 14), ('basilicum', 14), ('echinophora', 14), ('cymbopogon', 13), ('piper', 13), ('vitex', 13), ('ricinus', 12), ('zanthoxylum', 12), ('rosmarinus', 10), ('allium', 10), ('conradina', 10), ('cinnamomum', 9), ('salvia', 9), ('eucalyptus', 9), ('moringa', 9), ('anethum', 9), ('artemisia', 8), ('majorana', 8), ('ferula', 8), ('syzygium', 8), ('elyonurus', 8), ('satureja', 8), ('protium', 7), ('pistacia', 7), ('nigella', 7), ('tagetes', 7), ('calamus', 7), ('laser', 7), ('rhaponticum', 6), ('lavandula', 6), ('echinops', 6), ('aurantium', 6), ('aframomum', 6), ('terminalia', 6), ('plectranthus', 6), ('anisum', 5), ('dracocephalum', 5), ('ziziphora', 5), ('cleistocalyx', 5), ('cupressus', 5), ('hedyosmum', 5), ('ocotea', 5), ('capsicum', 5), ('argentina', 4), ('kundmannia', 4), ('eryngium', 4), ('phlomis', 4), ('ajuga', 4), ('lippia', 4), ('moldavica', 4), ('melissa', 4), ('psidium', 4), ('osmanthus', 4), ('annona', 4), ('tetracarpidium', 3), ('pimpinella', 3), ('coccinia', 3), ('melaleuca', 3), ('arabidopsis', 3), ('zataria', 3), ('glandora', 3), ('acorus', 3), ('marina', 3), ('achillea', 3), ('pycnocycla', 3), ('teucrium', 3), ('curcuma', 3), ('eugenia', 3), ('cuminum', 3), ('peregrina', 3), ('maple', 3), ('lannea', 3), ('listeria', 3), ('silybum', 3), ('pinus', 2), ('tanacetum', 2), ('cacao', 2), ('vetiveria', 2), ('daucus', 2), ('niphogeton', 2), ('faba', 2), ('brassica', 2), ('chenopodium', 2), ('avicennia', 2), ('cucurbita', 2), ('lindera', 2), ('zea', 2), ('foeniculum', 2), ('argania', 2), ('haematostaphis', 2), ('aloysia', 2), ('persica', 2), ('citronella', 2), ('cassia', 2), ('pimenta', 2), ('coleus', 2), ('pittosporum', 2), ('chamaemelum', 2), ('lens', 2), ('valeriana', 2), ('corymbia', 2)]
_DESC <class 'str'> methods and/or materials; looks for these words anywhere in file titles
PROJ <class 'str'> /Users/pm286/projects/CEVOpen/searches/oil186
TREE <class 'str'> *
SECTS <class 'str'> **
SUBSECT <class 'str'> *method*
SUBSUB <class 'str'> **
FILE <class 'str'> *p
SUFFIX <class 'str'> xml
glob /Users/pm286/projects/CEVOpen/searches/oil186/*/**/*method*/**/*p.xml
_DESC <class 'str'> methods and/or materials; looks for these words anywhere in file titles
PROJ <class 'str'> /Users/pm286/projects/CEVOpen/searches/oil186
TREE <class 'str'> *
SECTS <class 'str'> **
SUBSECT <class 'str'> *material*
SUBSUB <class 'str'> **
FILE <class 'str'> *p
SUFFIX <class 'str'> xml
glob /Users/pm286/projects/CEVOpen/searches/oil186/*/**/*material*/**/*p.xml
files 3390
***** section_files method 3390
file /Users/pm286/projects/CEVOpen/searches/oil186/PMC5849894/sections/1_body/1_material_and_methods/3_methods/2_sample_preparation_and_pr/3_p.xml
lang: en 
 [('antioxidant', 126), ('antifungal', 83), ('cytotoxicity', 33), ('analgesic', 12), ('acaricide', 10), ('insecticide', 6), ('anthelmintic', 5), ('antiparasitic', 4), ('phytotoxicity', 4), ('anticoagulant', 4), ('sedative', 3), ('fungicide', 3), ('derivative', 3), ('pesticide', 3), ('pro-oxidant', 2), ('adjuvant', 2)]
lang: en 
 [('ethanol', 116), ('hexane', 92), ('acetone', 32), ('carvacrol', 20), ('thymol', 10), ('toluene', 5), ('camphene', 5), ('cyclohexane', 5), ('benzene', 4), ('eugenol', 3), ('myrcene', 3), ('terpinolene', 3), ('curzerene', 2), ('nonane', 2), ('piperitenone', 2), ('humulene', 2), ('heptanal', 2), ('biphenyl', 2), ('caryophyllene', 2), ('6-methyl-5-hepten-2-one', 2), ('(e)-cinnamaldehyde', 2)]
lang: en 
 []
lang: en 
 [('cinnamon', 28), ('basil', 15), ('oregano', 9)]
lang: en 
 [('seed', 121), ('leaf', 66), ('resin', 56), ('root', 51), ('fruit', 47), ('flowering', 41), ('flower', 19), ('bark', 13), ('wood', 11), ('grass', 6), ('peel', 6), ('ovary', 4), ('petiole', 3), ('umbel', 3), ('pericarp', 3), ('rhizome', 2), ('needle', 2), ('apical', 2), ('perianth', 2), ('herb', 2)]
lang: en 
 [('eucalyptus', 21), ('listeria', 18), ('syzygium', 17), ('zea', 16), ('citrus', 15), ('microbiota', 14), ('salvia', 13), ('laser', 12), ('ocimum', 12), ('arabidopsis', 12), ('phyla', 11), ('allium', 10), ('mentha', 10), ('vitex', 10), ('cereus', 9), ('theobroma', 9), ('lavandula', 8), ('rosmarinus', 8), ('basilicum', 8), ('curcuma', 7), ('calamus', 7), ('cacao', 6), ('zataria', 6), ('capsicum', 6), ('croton', 6), ('pinus', 6), ('ricinus', 6), ('zanthoxylum', 6), ('moldavica', 6), ('niphogeton', 5), ('cinnamomum', 5), ('piper', 4), ('anisum', 4), ('pimpinella', 4), ('faba', 4), ('india', 4), ('cleistocalyx', 4), ('tribolium', 4), ('ginkgo', 4), ('wollemia', 4), ('satureja', 4), ('cassia', 4), ('tetracarpidium', 3), ('melaleuca', 3), ('dracocephalum', 3), ('tagetes', 3), ('paris', 3), ('trigonella', 3), ('cymbopogon', 3), ('pelargonium', 3), ('vetiveria', 3), ('origanum', 3), ('majorana', 3), ('avicennia', 3), ('bahia', 3), ('columbia', 3), ('hedyosmum', 3), ('siparuna', 3), ('achillea', 3), ('cuminum', 3), ('lippia', 3), ('pavia', 3), ('itatiaia', 3), ('ribes', 2), ('aria', 2), ('coccinia', 2), ('panax', 2), ('california', 2), ('mirabilis', 2), ('laguna', 2), ('andrea', 2), ('nauplius', 2), ('triticum', 2), ('raphanus', 2), ('solanum', 2), ('lens', 2), ('haematostaphis', 2), ('cotyledon', 2), ('beta', 2), ('biota', 2), ('elyonurus', 2), ('floribunda', 2), ('calycanthus', 2), ('idiospermum', 2), ('chimonanthus', 2), ('thymus', 2), ('corymbia', 2), ('cupressus', 2), ('betonica', 2), ('glechoma', 2), ('hyptis', 2), ('leonurus', 2), ('melissa', 2), ('marrubium', 2), ('stachys', 2), ('scutellaria', 2), ('ziziphora', 2)]
END DEMO
finished search
````



