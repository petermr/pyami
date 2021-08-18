# Examples

`pyami` contains `emaples.py` with about 7 examples. Their basic operatiom is correct, but the output is messy and verbose.

The examples can be run from the `physchem/python` directory
by

Update:
````
cd <yourdir>/pyami/pyami_m
pwd
/Users/pm286/workspace/pyami/pyami_m

python -m pyamix --examples all
````
and the args are:
````

python -m pyamix --examples
WARNING:root:loading templates.json
WARNING:pyami:
============== running pyami main ===============
['--examples']
choose example from:
de => deleting files
cp => copy files
g0 => globbing files
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
so 
````
python -m examples gl
````
runs the file globbing.

The actual commands expand to the commandlines 

````
        python -m examples 
             --debug   dummy   symbols 
             --proj   ${misc4.p} 
             --glob   ${proj}/**/sections/**/*abstract.xml 
             --dict   ${eo_plant.d}   ${ov_country.d} 
             --apply   xml2txt 
             --combine   concat_str 
             --outfile   ${proj}/files/misc4.txt 
             --assert   file_exists(${proj}/files/xml_files.txt) 
        
        python -m examples 
             --proj   ${misc4.p}
             --glob   ${proj}/*/fulltext.xml 
             --split   xml2sect 
             --assert   file_glob_count(${proj}/*/sections/**/*.xml,291) 

        python -m examples 
             --proj   ${misc4.p}
             --glob   ${proj}/*/fulltext.pd.txt 
             --split   txt2para 
             --outfile   fulltext.pd.sc.txt 
             --assert   file_glob_count(${proj}/*/fulltext.pd.sc.txt,291) 
			 
        python -m examples 
             --proj   ${misc4.p}
             --glob   ${proj}/*/fulltext.pd.txt 
             --apply   txt2sent 
             --outfile   fulltext.pd.sn.txt 
             --split   txt2para 
             --assert 
             glob_count(${proj}/*/fulltext.pd.sn.txt,3) 
             len(${proj}/PMC4391421/fulltext.pd.sn.txt,181) 
             item(${proj}/PMC4391421/fulltext.pd.sn.txt,0,) 

        python -m examples 
             --proj   ${misc4.p}
             --glob   ${proj}/*/fulltext.xml 
             --split   xml2sect 
        
        python -m examples 
             --proj   ${misc4.p}
             --glob   ${proj}/**/*_p.xml 
             --apply   xml2txt 
             --filter   contains(cell) 
             --combine   concat_str 
             --outfile   cell.txt 

        python -m examples 
             --proj   ${misc4.p}  
             --glob   ${proj}/**/*_p.xml 
             --filter 
             xpath(${all_italics.x})   
             regex(${species.r})   
             dictionary(${eo_plant.d})   
             wikidata_sparql(${taxon_name.w})   
             --combine   concat_xml 
             --outfile   italic.xml 

        python -m examples 
             --proj   ${misc4.p}
             --glob   ${proj}/*/fulltext.pdf 
             --apply   pdf2txt 
             --outfile   fulltext.pd.txt 
        ````
        The output is in `pyami/usertests/petermr/example...log.txt`
        
