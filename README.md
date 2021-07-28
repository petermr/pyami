# pyami
Semantic Reader of the Scientific Literature

## status
This is in very active alpha development and early documentatioon will appear on the Wiki.

# overview
* `pyami` is a personal tool that users can customise for their own needs and visions. It does not reply on remote service providers, though it can make its own use of Open sites. 

# scope
* `pyami` can collect documents (of any sort) into a corpus or `CProject`. 
* `pyami` has tools for filtering, cleaning, normalizing a corpus
* `pyami` can search this corpus by filenames, filetypes, document structure and content 
* content can include metadata, text, tables, diagrams, math, chemistry, references and (in some cases) citations
* searching uses words, phrases, dictionaries, and image content (vectors and pixels)
* search results can be transformed, filtered, aggregated, and used for iterative enhancement ("snowballing")

# architecture
* each document (`CTree`) in a CProject is split into a tree of many labelled text subsections (text, paragraphs, sentences, phrases, words). This is flexible (new types can be added bu users.
* the CTree is held on disk and can be further processed by other programs (e.g. pandas, tesseract (image2text), matplotlib
* a commandline supports many operations for searching, and transforming.
* a GUI (`ami-gui`) is layered on the commandline to help navigation, query building and visualisation.
* the commandline can be used by workflow tools such as Jupyter Notebooks
* The `pyami` code is packaged as a Python library for use by other tools

# components
There are several independent components. Many of these are customised for beginners. They can be referenced by symbols to avoid having to remember filenames. Users customise this with environment variables (often preset).
* project. The CProject holding the corpus. Users can have as many projects as they like.
* dictionary. Many searches use dictionaries and often several are used at once. There are currently over 50 dictionaries in a network but it's easy to create your own.
* code. (in Python3)
 
# commands
This is a subset of current commands:
````
optional arguments:
  -h, --help            show this help message and exit
  --apply {pdf2txt,txt2sent,xml2txt} [{pdf2txt,txt2sent,xml2txt} ...]
                        list of sequential transformations (1:1 map) to apply to pipeline ({self.TXT2SENT} NYI)
  --assert ASSERT [ASSERT ...]
                        assertions; failure gives error message (prototype)
  --combine COMBINE     operation to combine files into final object (e.g. concat text or CSV file
  --config [CONFIG [CONFIG ...]], -c [CONFIG [CONFIG ...]]
                        file (e.g. ~/pyami/config.ini) with list of config file(s) or config vars
  --debug DEBUG [DEBUG ...]
                        debugging commands , numbers, (not formalised)
  --demo [DEMO [DEMO ...]]
                        simple demos (NYI). empty gives list. May need downloading corpora
  --dict DICT [DICT ...], -d DICT [DICT ...]
                        dictionaries to ami-search with, _help gives list
  --filter FILTER [FILTER ...]
                        expr to filter with
  --glob GLOB [GLOB ...], -g GLOB [GLOB ...]
                        glob files; python syntax (* and ** wildcards supported); include alternatives in {...,...}.
  --languages LANGUAGES [LANGUAGES ...]
                        languages (NYI)
  --loglevel LOGLEVEL, -l LOGLEVEL
                        log level (NYI)
  --maxbars [MAXBARS]   max bars on plot (NYI)
  --nosearch            search (NYI)
  --outfile OUTFILE     output file, normally 1. but (NYI) may track multiple input dirs (NYI)
  --patt PATT [PATT ...]
                        patterns to search with (NYI); regex may need quoting
  --plot                plot params (NYI)
  --proj PROJ [PROJ ...], -p PROJ [PROJ ...]
                        projects to search; _help will give list
  --sect SECT [SECT ...], -s SECT [SECT ...]
                        sections to search; _help gives all(?)
  --split {txt2para,xml2sect} [{txt2para,xml2sect} ...]
                        split fulltext.* into paras, sections
  --test [{file_lib,pdf_lib,text_lib} [{file_lib,pdf_lib,text_lib} ...]]
                        run tests for modules; no selection runs all
````


## Notes for PMR?
project organization: https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
use: pkg_resources
