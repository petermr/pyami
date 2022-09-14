# minimal installation

CONFIG for PY4AMI
A) everyone needs a config.ini file in their directory structure
B) everyone needs environment variable $PYAMI_HOME

* clone py4ami from github
* verify it contains config.ini.master
* make a subdirectory `pyami` under your home directory
 - cd ~ on Unix/MAC
 - mkdir pyami
* copy the master config file to this directory
 - cp pyami/config.ini.master pyami/
 - set PYAMI_HOME to this directory 
* test with echo $PYAMI_HOME
giving:
`/Users/pm286/pyami/`

The rest of this file is for users who wish to change configuration

# Config files and symbols

(** some of this may be out of date)
Although `pyami` can be used with explict names 
````
pyami -p /user/monty/python/myfiles/plants
````
it is easier and less error prone to use symbols such as 
````
plants.p = /user/monty/python/myfiles/plants
pyami -p ${plants.p}
````

These symbols are defined in config files (normally `*.ini`) which are based on Python config files (see https://docs.python.org/3/library/configparser.html ).
Python only uses a single file which defines symbols in sections and can be recursive. We extend this with multiple files to 
create a network of chained INI files, supporting projects and dictionaries. The extra rules are:
* any `*_ini` symbol points to another config file which is then interpreted , thus building up a network (cyclic links are  forbidden).
* all variables are stored in the `SymbolIni` class and can be re-used on the commandline
* `pyami` variables referenced inside config files (but not ouside) are referenced by the syntax `$${...}` 
    to avoid clashing with python variables

## predefined variables

The `pyami` system has a network of variables referencing standard dictiomaries and test/reference projects. These are rooted from:
````
pyami/pyami/config.ini
````
in the `pyami` distribution. Any user can rely on these variables. 

They point to repository trees which must be separately checked out if they are to be used.

# personal `config.ini`

The user needs a minimal config.ini file to tell the system where:
* the downloaded pyami code is
* the dictionary repositories are
* any of the standard data/text repositories are.

She also needs to set the `PYAMI_HOME` environment variable to point to the directory
containing her `config.ini` file

## typical config.ini
````
# USER configuration file
#========================

# The symbols in DIRS and CODE point to communal resources, especially dictionaries, 
#   projects and parameters

; NOTE. All files use forward slash even on Windows
; use slash (/) to separate filename components, we will convert to file-separator automatically
; variables can be substituted using {}

[DIRS]
home              = ~
# where my projects are stored but yours may be different
project_dir       = ${home}/projects 
# my CEVOpen repo but yours may be different
cev_open =          ${DIRS:project_dir}/CEVOpen
# my dictionary repo but yours may be different
dict_dir =          ${DIRS:home}/dictionary
# my code directory but your may be different
code_dir =          ${home}/workspace

# PyAMI directories which are derived so don't alter them
pyami_package_dir = ${DIRS:code_dir}/pyami
pyami_src_dir     = ${DIRS:pyami_package_dir}/pyami

[SYMBOLS]
# my personal symbols
examples.p            = ${DIRS:pyami_src_dir}/tst/proj

[CODE]
# shared config INI file used by many of the tests - do not alter
code_config_ini =   ${DIRS:pyami_src_dir}/config.ini
````

The user will normally have a mixture od checked out repositories and these should be set in this file.
(Later we will try to create a GUI to help).

## central `pyami` config file
You need to check this out, but do not need to alter it.
````
# NOTE. All files use forward slash even on Windows
# use slash (/) to separate filename components, we will convert to file-separator automatically

# NOTE: PyAMI variables also use ${...} but to avoid being wrongly processed by ConfigParser
#       they are escaped as $${...} . They are then substituted in a PyAMI parse
#.      This ONLY happens in Config files

[SYMBOLS]
# symbols of general use

; # wikidata taxon name property
taxon_name.w = P225
; # italic content
all_italics.x = //p//italic/text()
; # species, e.g. Zea mays, T. rex, An. gambiae
species.r = [A-Z][a-z]?(\.|[a-z]{2,})\s+[a-z]{3,}

[URLS]
# alternatives to local filestore
petermr_url =     https://github.com/petermr
petermr_raw_url = https://raw.githubusercontent.com/petermr
tigr2ess.u =      https://github.com/petermr/tigr2ess/tree/master
# general dictionaries
dictionary_url = https://github.com/petermr/dictionary

[AMISEARCH]
# unused at present

[DICTIONARIES]
ov_ini       = $${dict_dir}/openvirus20210120/amidict.ini
cev_ini      = $${cev_open}/dictionary/amidict.ini

#docanal_ini  = ${dict_dir}/docanal/docanal.ini # not yet added


[PROJECTS]
# these are used in examples and tests but will probably be removed from here
open_battery =      $${project_dir}/open-battery
pr_liion =          ${open_battery}/liion
tigr2ess =          $${project_dir}/tigr2ess
open_diagram =      $${project_dir}/openDiagram
open_virus =        $${project_dir}/openVirus

minicorpora_ini =   $${cev_open}/minicorpora/config.ini
cev_searches_ini =  $${cev_open}/searches/config.ini
open_diag_ini =     $${project_dir}/openDiagram/physchem/resources/config.ini

````
You can see communal projects and symbols (e.g. Wikidata properties)




