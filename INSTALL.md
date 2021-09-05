# preamble
Since there are other packages called `pyami` (nothing to do with us) the formal name in `PyPI` will be `py4ami`. Informally we may use `pyami`.

There are two sections here: for those who want to download and use `py4ami` and those who are developing and uploading.


# Installation for users (download)
`py4ami` is now a `PyPI` project and by default will be installed from there. `py4ami` is now versioned as `d.d.d` (major/minor/patch). Generally you should install the latest version unless indicated.

## location
See https://pypi.org/project/py4ami/

# installation for developers (upload)

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
NOTE: If there are errors in `setup.py` and you change the version and re-upload the old version will cause the upload to fail. This cost me 
a lot of time. So make sure your setup is correct.

Find the version number in `setup.py` and increase it:
````
    name='py4ami',
    url='https://github.com/petermr/pyami',
    version='0.0.6',    # increased from `0.0.5`
    description='Semantic Reader of the Scientific Literature.',
    long_description="""Pyami converts scientific articles to structured form (discrete files for sections, subsections, etc.).

````

## create distribution
````
python setup.py sdist
````
This outputs the following (I may have got `resources/` wrong 
````
running sdist
running egg_info
writing py4ami.egg-info/PKG-INFO
writing dependency_links to py4ami.egg-info/dependency_links.txt
writing entry points to py4ami.egg-info/entry_points.txt
writing top-level names to py4ami.egg-info/top_level.txt
reading manifest file 'py4ami.egg-info/SOURCES.txt'
reading manifest template 'MANIFEST.in'
warning: no files found matching 'py4ami/resources'
warning: manifest_maker: MANIFEST.in, line 4: 'recursive-include' expects <dir> <pattern1> <pattern2> ...

warning: no files found matching 'config.ini'
adding license file 'LICENSE'
writing manifest file 'py4ami.egg-info/SOURCES.txt'
running check
creating py4ami-0.0.6
creating py4ami-0.0.6/py4ami
creating py4ami-0.0.6/py4ami.egg-info
creating py4ami-0.0.6/py4ami/resources
creating py4ami-0.0.6/test
copying files to py4ami-0.0.6...
copying CONFIG.md -> py4ami-0.0.6
copying LICENSE -> py4ami-0.0.6
copying MANIFEST.in -> py4ami-0.0.6
copying README.md -> py4ami-0.0.6
copying setup.py -> py4ami-0.0.6
copying py4ami/__init__.py -> py4ami-0.0.6/py4ami
copying py4ami/ami_config.py -> py4ami-0.0.6/py4ami
copying py4ami/ami_demos.py -> py4ami-0.0.6/py4ami
copying py4ami/ami_gui.py -> py4ami-0.0.6/py4ami
copying py4ami/constants.py -> py4ami-0.0.6/py4ami
copying py4ami/dict_lib.py -> py4ami-0.0.6/py4ami
copying py4ami/examples.py -> py4ami-0.0.6/py4ami
copying py4ami/file_lib.py -> py4ami-0.0.6/py4ami
copying py4ami/gutil.py -> py4ami-0.0.6/py4ami
copying py4ami/jats_lib.py -> py4ami-0.0.6/py4ami
copying py4ami/misc.py -> py4ami-0.0.6/py4ami
copying py4ami/pdfreader.py -> py4ami-0.0.6/py4ami
copying py4ami/projects.py -> py4ami-0.0.6/py4ami
copying py4ami/pyami.ini -> py4ami-0.0.6/py4ami
copying py4ami/pyamix.py -> py4ami-0.0.6/py4ami
copying py4ami/search_lib.py -> py4ami-0.0.6/py4ami
copying py4ami/symbol.py -> py4ami-0.0.6/py4ami
copying py4ami/text_lib.py -> py4ami-0.0.6/py4ami
copying py4ami/text_xml.py -> py4ami-0.0.6/py4ami
copying py4ami/util.py -> py4ami-0.0.6/py4ami
copying py4ami/wikimedia.py -> py4ami-0.0.6/py4ami
copying py4ami/xml_lib.py -> py4ami-0.0.6/py4ami
copying py4ami.egg-info/PKG-INFO -> py4ami-0.0.6/py4ami.egg-info
copying py4ami.egg-info/SOURCES.txt -> py4ami-0.0.6/py4ami.egg-info
copying py4ami.egg-info/dependency_links.txt -> py4ami-0.0.6/py4ami.egg-info
copying py4ami.egg-info/entry_points.txt -> py4ami-0.0.6/py4ami.egg-info
copying py4ami.egg-info/not-zip-safe -> py4ami-0.0.6/py4ami.egg-info
copying py4ami.egg-info/top_level.txt -> py4ami-0.0.6/py4ami.egg-info
copying py4ami/resources/section_templates.json -> py4ami-0.0.6/py4ami/resources
copying test/test_all.py -> py4ami-0.0.6/test
copying test/test_dict.py -> py4ami-0.0.6/test
copying test/test_file.py -> py4ami-0.0.6/test
copying test/test_gui.py -> py4ami-0.0.6/test
copying test/test_pdf.py -> py4ami-0.0.6/test
copying test/test_search.py -> py4ami-0.0.6/test
copying test/test_xml_lib.py -> py4ami-0.0.6/test
Writing py4ami-0.0.6/setup.cfg
Creating tar archive
removing 'py4ami-0.0.6' (and everything under it)

````
## install `twine`
````
pip install twine
````

## check your upload
This is very important. Trivial errors here can make uploads very difficult.

````
twine check sdist/*
````

## upload `dist` to `PyPI`
**Make sure you have the correct version in `setup.py` . **

````
twine upload sdist/*
````
gives a login (your `PyPI` login, NOT github)
````
Uploading distributions to https://upload.pypi.org/legacy/
Enter your username: petermr
Enter your password: 
Uploading py4ami-0.0.6.tar.gz
100%|████████████████████████████████████████████████████████████████████████████████████| 93.7k/93.7k [00:01<00:00, 51.6kB/s]
NOTE: Try --verbose to see response content.
HTTPError: 400 Bad Request from https://upload.pypi.org/legacy/
The description failed to render in the default format of reStructuredText. See https://pypi.org/help/#description-content-type for more information.
````
