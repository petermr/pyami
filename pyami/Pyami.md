# pyami distribution

This is a prototype of how to find files anf URLs in a distributed `ami` system. It will cover:
## pyami 
This will run the `pyami` system for reading and analysing documents.
## pyamidict
This creates and manages ami-dictionaries
## amiprojects
manages subprojects created under the `ami` system

# cloning from Github
checkout/clone Github repo https://github.com/petermr/openDiagram (yes, that's where the prototype code is, we'll relocate later). The relevant Python code is in https://github.com/petermr/openDiagram/physchem/python

This should contain a number of Python library prototypes (*.py). The ones for pyami are:
## file_lib.py
File management including globbing

## image_lib.py
For processing the contents of images

## plot.py
Plotting tools

## search_lib.py
For searching text.

## text_lib.py
For Natural Language Processing

## util.py
Utilities.
Also contains `AmiConfig` which manages the configuration files. This will be moved latwer

## xml_lib.py
For processing CML

## section_templates.json
Schema describing the sections of a document

## pyami.ini 
see below

# installation
## pyami.ini
Copy this file to your HOME directory (`'~'`) and edit it to use your HOME directory.

## dictionaries
Select an appropriate place to copy the main dictionary system to. (I use $HOME/dictionary). 
````
git clone https://github.com/petermr/dictionary.git 
````
will copy it. (Sorry there is quite a lot of mess in it).
If you don't want to install it locally we are developing a URL-based approach


## running dictionary traversal
At present this is either from the commandline or from an IDE (I use Pycharm)
### commandline
To recursively list directories
````
cd /some/where/dictionary/physchem/python
python util.py 
```` 
## running ami search
(It works but is currently disabled (aka broken))
````
cd /some/where/dictionary/physchem/python
python search_lib.py 
```` 

# *.ini files
The file and URL structure is managed using Python `*.ini` files. These are similar to Windows INI files and consist of 
## [ID]
The file will have a unique ID , probably based on RDF / XML namespaces

## sections
THese are indicated by the syntax `[FOO]`. The section name indicates purpose and role and may be found in other *.ini files. Names are unique within an INI. Sections cannot be nested.

## name-values
Each section holds name-value pairs (no naked names) and names are unique within a section.

## examples
### pyami.ini
see below
### a subdirectory INI for dictionaries

````
[ID]
;still being developed
id = petermr
location = https://raw.githubusercontent.com/petermr/ami3/ 
namespace_base = https://contentmine.org/
namespace = ${namespace_base}/home
prefix = petermr


[DICTIONARIES]

animaltest = animaltest.xml
auxin = auxin.xml
cochrane = cochrane.xml
compchem = compchem.xml

````
# pyami.ini 
Each time you run `pyami` it will look for $HOME/pyami.ini . You have to work out where your HOME is on Windows and put this file there. It will be read when you launch the program; it will give a warning if it can't find it.

If you aren't allowed to create files in $HOME we'll probably create the chance to read an *.INI file on launch.

## example
=========================================================
(Comnments use ';' so as not to confuse markdown)
````
; initial configuration file
; syntax: see https://docs.python.org/3/library/configparser.html
; a set of [SECTION]s containing name-value pairs 

[ID]
; defines a global namespace
; NOT yet developed
id = pyami
location = HOME
namespace_base = https://contentmine.org/
namespace = ${namespace_base}/home
prefix = home


[DIRS]
; set up your own top directories here

; EDIT THIS to your own $HOME , resolvable by "~"
home = /Users/pm286

; the URL of AMI dictionaries on Github
dictionary_url = https://github.com/petermr/dictionary
; Directory for your projects; EDIT this if you use this approach
project_dir = ${home}/projects

[URLS]
; most initial repos are in `petermr`s repos 
petermr_url = https://github.com/petermr

; prefix to read raw data
petermr_raw_url = https://raw.githubusercontent.com/petermr

[PROJECTS]
; PMR keeps most data projects (i.e. non-code) in a separate .../projects/ suddir
; EDIT in/out those projects you are using

; current (2021) CEVOpen repo
cev_open = ${DIRS:project_dir}/CEVOpen

; current (2021) open battery
open_battery = ${DIRS:project_dir}/open-battery

; an open-battery minicorpus
pr_liion = ${open_battery}/liion

; tigr2ess (2019) project 
tigr2ess = ${DIRS:project_dir}/tigr2ess

; tigr2ess URL
tigr2ess_url = https://github.com/petermr/tigr2ess/tree/master

; open diagrams (also contains prototype code)
open_diagram = ${DIRS:project_dir}/openDiagram

; open virus (2020) still slightly active. Contains some dictionaries
open_virus = ${DIRS:project_dir}/openVirus

[PYAMIGETPAPERS]
; defaults and setting for `pygetpapers`
; not yet developed or used by the program
max = 200

[DICTIONARIES]
; top dir of local dictionaries
dict_dir = ${DIRS:home}/dictionary

; dictionaries currently have two values, their directory and *.INI file
; this may change to tuples


; openvirus (2020-) but used by others
ov_link = ${dict_dir}/openvirus20210120
ov_ini = ${ov_link}/amidict.ini

; CEVopen current (2021) essential oils project
cev_link = ${PROJECTS:cev_open}/dictionary
cev_ini = ${cev_link}/amidict.ini

; tigr2ess (Cambridge-India project) (2019) 
tigr2ess_link = ${PROJECTS:tigr2ess}/dictionaries
tigr2ess_ini = ${tigr2ess_link}/amidict.ini

; open-battery (also contains prototype code)
battery_link = ${PROJECTS:open_battery}/dictionary
battery_ini = ${battery_link}/amidict.ini

; ami3 code (contains many early dictionaries)
ami3_url = ${URLS:petermr_raw_url}/ami3/master/src/main/resources/org/contentmine/ami/plugins/dictionary
ami3_ini = ${ami3_url}/amidict.ini

[AMISEARCH]
; not yet developed
; will supprt pyami (search)
````
=================================================================

## distributed files and URLs
`pyami.ini` can contain instructions to locate other resources such as dictionaries or projects. WE hope to allow symbolic references in `ami` and related programs.

In the above example the references to the *.ini files allow them to be activated in a recursive hierarchical manner (please avoid cycles! until I add checks). 


 

