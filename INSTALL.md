# preamble
Since there are other packages called `pyami` (nothing to do with us) the formal name in `PyPI` will be `py4ami`. Informally we may use `pyami`.

There are two sections here: for those who want to download and use `py4ami` and those who are developing and uploading.


# Installation for users (download)
`py4ami` is now a `PyPI` project and by default will be installed from there. `py4ami` is now versioned as `d.d.d` (major/minor/patch). Generally you should install the latest version unless indicated.

## location
See https://pypi.org/project/py4ami/

# ====================================
# installation for developers (upload)
# ====================================

## quick instructions for experienced users
EDIT VERSION NUMBER
```cd pyami
rm -rf dist
# edit version number in setup.py
```




## repeat instructions (ONLY if you've done this before)  ============
```
cd pyami
rm -rf dist
```
# <EDIT VERSION in setup.py>
# buildoutcfg

```
python setup.py sdist

twine upload dist/*
# <login is pypi, not github>
```

## for new developers =============

**Follow this carefully. Make sure you are uploading the latest version**

````
cd <pyami> # wherever `pyami` is located
````
This should contain files like:
````
ls -l
total 88
-rw-r--r--@  1 pm286  staff   4823  4 Sep 10:02 CONFIG.md        # docs about configuration, symbols
-rw-r--r--@  1 pm286  staff   3372  4 Sep 10:11 EXAMPLES.md      # docs about examples
-rw-r--r--   1 pm286  staff  11357 20 Aug 17:43 LICENSE          # licence
-rw-r--r--@  1 pm286  staff    186  3 Sep 21:21 MANIFEST.in      # list of files to be includes 
-rw-r--r--   1 pm286  staff   7210 20 Aug 17:43 README.md        # readme 
-rw-r--r--   1 pm286  staff      0 20 Aug 17:43 __init__.py      # defines the project
drwxr-xr-x   3 pm286  staff     96 20 Aug 17:43 assets           # images, etc.
-rw-r--r--@  1 pm286  staff   1800  4 Sep 10:10 config.ini.master.  # template for user's config.ini (not yet finished)
drwxr-xr-x  31 pm286  staff    992  4 Sep 09:57 py4ami           # source and resources
drwxr-xr-x   8 pm286  staff    256  5 Sep 09:29 py4ami.egg-info  # created by build (may be missing)
-rw-r--r--@  1 pm286  staff   1955  5 Sep 09:29 setup.py         # this file
drwxr-xr-x  10 pm286  staff    320 20 Aug 17:43 test             # tests (not finished)
````
## edit the version in `setup.py`

**Every upload should have a new increased version, even if the edits are minor.**

Find the version number in `setup.py` and increase it:
````
    name='py4ami',
    url='https://github.com/petermr/pyami',
    version='0.0.6',    # increased from `0.0.5`
    description='Semantic Reader of the Scientific Literature.',
    long_description="""Pyami converts scientific articles to structured form (discrete files for sections, subsections, etc.).

````
## remove old `dist/`
````
 rm -r dist
```` 
If you don't do this it will upload the previous dist and probably throw errors. 


## create MANIFEST.in

Check MANIFEST.in.
Note that `graft` includes the full subtree. We include the test data which makes the distrib about 20 Mb.
````
more MANIFEST.in 
include LICENSE
graft py4ami/resources
include config.ini.master
include py4ami/pyami.ini
include CONFIG.md
````

## create distribution (`dist`)
````
python setup.py sdist
````
This outputs the following 
````
running sdist
running egg_info
writing py4ami.egg-info/PKG-INFO
writing dependency_links to py4ami.egg-info/dependency_links.txt
writing entry points to py4ami.egg-info/entry_points.txt
writing top-level names to py4ami.egg-info/top_level.txt
reading manifest file 'py4ami.egg-info/SOURCES.txt'
reading manifest template 'MANIFEST.in'
adding license file 'LICENSE'
writing manifest file 'py4ami.egg-info/SOURCES.txt'
running check
creating py4ami-0.0.9
creating py4ami-0.0.9/py4ami
creating py4ami-0.0.9/py4ami.egg-info
... lots of files ...
copying py4ami/resources/projects/oil4/PMC7048421/sections/2_back/2_ref-list/9_ref.xml -> py4ami-0.0.9/py4ami/resources/projects/oil4/PMC7048421/sections/2_back/2_ref-list
copying py4ami/resources/projects/oil4/files/misc4.txt -> py4ami-0.0.9/py4ami/resources/projects/oil4/files
copying test/test_all.py -> py4ami-0.0.9/test
copying test/test_dict.py -> py4ami-0.0.9/test
copying test/test_file.py -> py4ami-0.0.9/test
copying test/test_gui.py -> py4ami-0.0.9/test
copying test/test_pdf.py -> py4ami-0.0.9/test
copying test/test_search.py -> py4ami-0.0.9/test
copying test/test_xml_lib.py -> py4ami-0.0.9/test
Writing py4ami-0.0.9/setup.cfg
creating dist
Creating tar archive
removing 'py4ami-0.0.9' (and everything under it)

````
## install `twine`
````
pip install twine
````

## upload `dist` to `PyPI`
````
twine upload dist/*
````
gives a login (your `PyPI` login, not github)
````
Uploading distributions to https://upload.pypi.org/legacy/
Enter your username: petermr
Enter your password: 
Uploading py4ami-0.0.6.tar.gz
100%|████████████████████████████████████████████████████████████████████████████████████| 93.7k/93.7k [00:01<00:00, 51.6kB/s]
NOTE: Try --verbose to see response content.

View at:
https://pypi.org/project/py4ami/0.0.6/
````


## release new version

remove old dist
```
rm -rf dist/

```
```
pip install pipreqs --force
pipreqs pyami

```
* cd pyami top directory
* edit version in setup.py
```
 python setup.py bdist_wheel
 twine upload/dist*
```

# run in virtual environment

```
python -m venv venv

source venv/bin/activate
```
we are now in the venv


```
pip install py4ami --upgrade
```
check installed with
```
pip freeze
```

To leave `venv` 
```
deactivate
```