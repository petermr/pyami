# pyami
Semantic Reader of the Scientific Literature.

A scientific article is not a single dumb file; it can be transformed into many semantic, useful sub-documents. `pyami` is a Python framework for doing this; it reads the scientific literature in bulk, transforms, searches and and analyses the contents.

### status
This is in very active alpha development and early documentation will appear on the Wiki.

# overview
* `pyami` is a personal (client-side) tool that users can customise for their own needs and visions. It does not reply on remote service providers, though it can make its own use of Open sites. 

# scope
* `pyami` can collect documents (of any sort) into a corpus or `CProject`. 
* `pyami` has tools for filtering, cleaning, normalizing a corpus
* `pyami` can search this corpus by filenames, filetypes, document structure and content 
* content can include metadata, text, tables, diagrams, math, chemistry, references and (in some cases) citations
* searching uses words, phrases, dictionaries, and image content (vectors and pixels)
* search results can be transformed, filtered, aggregated, and used for iterative enhancement ("snowballing")

# architecture
* downloaded documents (a corpus) are stored on your disk in a folder/directory (a CProject`)
* each document (`CTree`) in a `CProject` is a living subtree of many labelled text subsections (text, paragraphs, sentences, phrases, words) and images (`png`) . This is flexible (new types and subdirectories) can be added by users).
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
This is a subset of current commands (NYI=not yet implemented):
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

# getting started
There are an alpha series of commandline examples which show the operation of the system. Currently:
````
 examples args: ['examples.py']
choose from:
gl => globbing files
pd => convert pdf to text
pa => split pdf text into paragraphs
sc => split xml into sections
sl => split oil26 project into sections
se => split text to sentences
fi => simple filter (not complete)
sp => extract species with italics and regex (not finalised)

all => all examples
````

## config file
**everyone needs**

### a 'pyami' directory. 

This can be naywhere but normally where you put program files and their
setting. It will be easiest if it's a direct subdirectory of your HOME directory. 
It MUST include a `pyami.ini` file. By default you can use the one in the `py4ami` distribution

### an environmental variable `PYAMI_HOME` 

This will point to the `pyami.ini` file. 
See [./CONFIG.md](CONFIG.md)


`
````
(base) pm286macbook:pyami pm286$ more ~/pyami/config.ini
; NOTE. All files use forward slash even on Windows
; use slash (/) to separate filename components, we will convert to file-separator automatically
; variables can be substituted using {}

[DIRS]
home           = ~
dictionary_url = https://github.com/petermr/dictionary
project_dir =    ${home}/projects
cev_open =       ${DIRS:project_dir}/CEVOpen
code_dir =       ${DIRS:project_dir}/openDiagram/physchem/python
; # wikidata taxon name property
; taxon_name.w = P225777
; # italic content
; all_italics.x = xpath(//p//italic/text())
; # species, e.g. Zea mays, T. rex, An. gambiae
; species.r = [A-Z][a-z]?(\.|[a-z]{2,})\s+[a-z]{3,})

[URLS]
petermr_url = https://github.com/petermr
petermr_raw_url = https://raw.githubusercontent.com/petermr
tigr2ess.u =        https://github.com/petermr/tigr2ess/tree/master

[AMISEARCH]
oil3.p = ${DIRS:code_dir}/tst/proj
# wikidata taxon name property
taxon_name = P225
# italic content
all_italics.x = //p//italic/text()
# species, e.g. Zea mays, T. rex, An. gambiae
species.r = [A-Z][a-z]?(\.|[a-z]{2,})\s+[a-z]{3,}

[DICTIONARIES]
dict_dir     = ${DIRS:home}/dictionary

ov_ini       = ${dict_dir}/openvirus20210120/amidict.ini
cev_ini      = ${DIRS:cev_open}/dictionary/amidict.ini

# docanal_ini  = ${dict_dir}/docanal/docanal.ini # not yet added


[PROJECTS]
open_battery =      ${DIRS:project_dir}/open-battery
pr_liion =          ${open_battery}/liion
tigr2ess =          ${DIRS:project_dir}/tigr2ess
open_diagram =      ${DIRS:project_dir}/openDiagram
open_virus =        ${DIRS:project_dir}/openVirus

minicorpora_ini =   ${DIRS:cev_open}/minicorpora/config.ini
cev_searches_ini =  ${DIRS:cev_open}/searches/config.ini
open_diag_ini =     ${DIRS:project_dir}/openDiagram/physchem/resources/config.ini


(base) pm286macbook:pyami pm286$ 
````

##UPDATE `py4ami.ami_dict` and `py4ami.ami_pdf`

These now support `argparse` in their own right (2022-07-09)
They will each give an argparse of commands 

### `ami_pdf`

(2022-07-09)

```
python -m py4ami.ami_pdf --help
running PDFArgs main
usage: ami_pdf.py [-h] [--maxpage MAXPAGE] [--indir INDIR] [--inpath INPATH] [--outdir OUTDIR]
                  [--outform OUTFORM] [--flow FLOW] [--imagedir IMAGEDIR] [--resolution RESOLUTION]
                  [--template TEMPLATE] [--debug {words,lines,rects,curves,images,tables,hyperlinks,annots}]

PDF parsing

optional arguments:
  -h, --help            show this help message and exit
  --maxpage MAXPAGE     maximum number of pages
  --indir INDIR         input directory
  --inpath INPATH       input file
  --outdir OUTDIR       output directory
  --outform OUTFORM     output format
  --flow FLOW           create flowing HTML (heuristics)
  --imagedir IMAGEDIR   output images to imagedir
  --resolution RESOLUTION
                        resolution of output images (if imagedir)
  --template TEMPLATE   file to parse specific type of document (NYI)
  --debug {words,lines,rects,curves,images,tables,hyperlinks,annots}
                        debug these during parsing (NYI)

```


## Notes for PMR?
project organization: https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
use: pkg_resources

# WARNING
...
AmiUtil exists in both py4ami and pyamiimage. There should be a separate library
