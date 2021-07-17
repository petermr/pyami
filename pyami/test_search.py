"""tests AmiSearch
"""

import logging
logging.warning("loading test_search")

from search_lib.py import AmiSearch, AmiRake, SearchDictionary

def test_search():
    option = "search"  # edit this
    #    option = "sparql"
    #    option = "rake"
    if 1 == 2:
        pass
    elif option == "rake":
        AmiRake().test()

    elif option == "search":
        ami_search = AmiSearch()
        ami_search.run_args()
    elif option == "test":
        AmiRake().test()
    elif option == "sparql":
        SearchDictionary.test_dict_read()
    else:
        print("no option given")

