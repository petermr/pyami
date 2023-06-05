# alpha code for searching document corpus

SEE ALSO <a href="SEARCH.md">SEARCH TUTORIAL</a>

This is installed on `pypi` as `py4ami` (https://pypi.org/project/py4ami/) note the `4`
to avoid collision on `pypi`. But locally this is `pyami` (maybe we'll change this).
It should be possible to 
* `pip install py4ami`
* `from py4ami import pyami` (sic)

## prerequisites

- create getpapers output
- run `ami section` to create sections AND/OR
- run `ami pdfbox` to extract images

# strategy

The search is hierarchical, maybe with backwards loops.

## search foreign repository with `(py)getpapers`

This is well established and be a keyword search and depends on the repo's engines - very variable. It's likely to contain many false positives. The results are stored as full text , XML and PDF. The XML can be split into sections with `ami section` or `pyamisection` (being written - nearly finished.

## search for sections

Use glob-based wildcards to extract only the sections of interest (e.g. abstract, references, methods, results...). see [./file_lib.py](section search)

## search content in sections, using dictionaries

The new code [./search.py] will replaces `ami search`.

## DEMO with multiple projects , dictionaries and sections

**for Monday 2021-03-22**

**RUN**

```
python search_lib.py
```

# demo



## section search

This is set up with files from Steel articles and is hardcoded into `file_lib`.

https://github.com/petermr/openDiagram/blob/master/physchem/python/file_lib.py

This exercises about 20 globs that are useful for scientific papers.
At this stage just try to run it and report any errors. It's fairly easy to point it at your own project.

## word frequencies

An example hardcoded into:

https://github.com/petermr/openDiagram/blob/master/physchem/python/text_lib.py

This extracts the content from sections, removes stopwords , and creates a Counter (Multiset) to show the freequencies of words ("word cloud").

## dictionary search

This will apply dictionaries to sections. Not yet written.

https://github.com/petermr/openDiagram/blob/master/physchem/python/search.py

## xml and sections

Will create sections from JATS-XML (replaces `ami section`). Over 50% written.

https://github.com/petermr/openDiagram/blob/master/physchem/python/xml_lib.py

## Notes
```
long_desc = "Pyami converts scientific articles to structured form (discrete files for sections, subsections, etc.)."+
"XML or HTML files are directly split into *.xml, PDFs or TXT are heuristically split into text and images."+
"Text can be searched with (lists of) words, regexes, ami-dictionaries or through globbing filenames."+
"Images can be analysed as collections of primtives and built into"+
"semantic plots."+
"pyami uses a commandline based on argparser and a GUI based on tkinter. The input data is usually created "+
"by `pygetpapers` but can also take in directories of PDF files."+
"Pyami is extensible through command-based modules and since all output consists of standard files in "+
"nested directories it is easy to analyse it with other Python tools."
long_desc="Pyami desc"
print (f"long:desc {long_desc}")
```

# update 2022-09-29

Created subcommands (subparsers) in `py4ami`:
* `DICT`: display and edit dictionaries
* `GUI`: launches `py4ami.ami-gui` (under development)
* `HTML`: parse raw HTML to be semantic
* `PDF` convert PDF to semantic form
* `PROJECT`: make `CProject` from a list of raw files (normally PDF)

# update 2023-06-05
test_integrate.py runs prototype applications

<!-- this is HTML
<table>
  <tbody>
    <tr><td><b>Lantana</b></td><td>plant</td></tr>
    <tr><td>Kangaroo</td><td>animal</td></tr>
  </tbody>
</table>
-->