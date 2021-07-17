# Configuration file/s and symbols for `pyami`

`pyami` has a system for users and resource providers to customise the environment.
This avoids having to use absolute filenames if possible, set run parameters for
computation and graphics. The editing should be minimal.

# why do we need this?

Every user has a differeht environment, wants to use different files, or constrain operations. 
Many of the resources (dictionaries, settings, corpora...) are provided by external sources and 
users won't wish to maintain changes. Moreover it can lead to reproducibility if everyone can share 
the same resources through common symbols.
Ideas welcome.

# how does it work?

`pyami` can be controlled by a commandline DSL (domain-specific language) (which can also be driven by the `pyami_gui). At present it knows about:

* files and directories, especailly relative to ContentMine-style CProjects (directories with conventional naming)

* a number of `pyami` commands/subcommands relevant to content-mining and often closely linked to common shell/textmining commands.
* parameters to control their operation
* dictionaries for searching text files

## config files
The basic architecture is Python and Python-like config files. These are usually conventionally called `*.ini` or `*.cfg`; we use `CONFIG.ini`. 


# Symbols

A major aspect of `pyami` is the use of symbols. These support string-value pairs and are based on Python's <a href="https://docs.python.org/3/library/configparser.html#quick-start">`configparser`</a>, both syntax and tools. This system allows:
* sections within config files.
* extended symbols (e.g. `dirs:name`) referencing other sections
* <a href="https://docs.python.org/3/library/configparser.html#interpolation-of-values">symbol substitution</a> using `${...}` as symbol references. Symbols do not have to be defined in order and can occur multiple times (`foo${bar}baz${plugh}end`), but cannot be recursive/nested (`foo${${baz}${plugh}}end`)
* `pyami` symbols. Certain strings are reserved and reserved for a second processing run. At present this is only `proj`which is then used to substyitute all `${proj}`. 

## processing

Symbols in the primary config file are 

* first processed by the Python system and create an internal symbol table (dict). 
* processed by `pyami` to create new symbols and create an extended network of config files.

# `pyami` CONFIG network

`pyami` has the following namespaces:

## local, controlled by the user

These may include local variables and parameters, local ami-dictionaries and local CProject (corpora). 

## ami-dictionaries

Most dictionaries are not created by the user, who should not be required to update their symbols. These are called "remote" even if they have been downloaded locally, normally by cloning a repository of dictionaries. "`pyami` convention is that remote dictionaries should have a `CONFIG.ini` file which defines "remote dictionaries and symbols.

Each dictionary will have its distinct symbol, and may be namespaced.

This means that dictionary owners can create their own symbols and parameters. Users will access the single `CONFIG.ini` file and automatically import all symbols and parameters. Any upgrades or changes will be seamlessly inported.

This linking can , in principle, continue further but may not be wise. `pyami` will avoid cyclic loops.

## ami-projects

Projects can use the same approach as dictionaries, and this is an easy way to manage multicorpoa work.

Because `proj` is coupled to `--proj` and is central to many uses of `pyami` its value will be stored. It can then be used in expressions such as `--glob ${proj}/*/sections/**/*abstract.xml`

# contents of user `CONFIG.ini`

Currently my config looks like:
```
; NOTE. All files use forward slash even on Windows
; use slash (/) to separate filename components, we will convert to file-separator automatically
; variables can be substituted using {}

````
Here the main directories are defined. Note:
* `~` expands to the home directory on any system
* I have my local directory containing many projects
* I shall be using the CEVOpen repository
````
[DIRS]
home = ~
project_dir = ${home}/projects
cev_open =    ${DIRS:project_dir}/CEVOpen
````
URLs can be used by some routines in the system. `dictionary_url` represents a collection on non-CEV dictionaries
````

[URLS]
dictionary_url = https://github.com/petermr/dictionary
petermr_url = https://github.com/petermr
petermr_raw_url = https://raw.githubusercontent.com/petermr
tigr2ess.u =        https://github.com/petermr/tigr2ess/tree/master
````
Three collections of dictionaries, cloned from our websites. The ini files link to the `ini` files in the collections , and these will be processed. This makes the dictionary symbols available locally.
````

[DICTIONARIES]
dict_dir = ${DIRS:home}/dictionary
ov_ini = ${dict_dir}/openvirus20210120/amidict.ini
cev_ini = ${DIRS:cev_open}/dictionary/amidict.ini

````
A variety of corpora / projects, cloned from repositories, on local storage
````

[PROJECTS]
open_battery =      ${DIRS:project_dir}/open-battery
pr_liion =          ${open_battery}/liion
tigr2ess =          ${DIRS:project_dir}/tigr2ess
open_diagram =      ${DIRS:project_dir}/openDiagram
open_virus =        ${DIRS:project_dir}/openVirus

minicorpora_ini =   ${DIRS:cev_open}/minicorpora/config.ini
cev_searches_ini =  ${DIRS:cev_open}/searches/config.ini
open_diag_ini =     ${DIRS:project_dir}/openDiagram/physchem/resources/config.ini

````


