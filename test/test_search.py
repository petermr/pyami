"""tests AmiSearch
"""

import logging
# local
from py4ami.search_lib import AmiSearch
from py4ami.ami_dict import AmiDictionary

def test_search():

    option = "search"  # edit this
    #    option = "sparql"
    if option == "search":
        ami_search = AmiSearch()
        ami_search.run_args()
    # elif option == "test":
    #     AmiRake().test()
    elif option == "sparql":
        AmiDictionary.test_dict_read()
    else:
        print("no option given")

