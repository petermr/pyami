from py4ami.dict_lib import AMIDict
"""Code for VALIDATING specific DICTIONARIES , not the code

 These are effectively tests for the dictionaries
 """


CEVOPEN_ROOT = "https://raw.githubusercontent.com/petermr/CEVOpen/master"

CEVOPEN_DICT_ROOT = f"{CEVOPEN_ROOT}/dictionary"
# this will use the config.ini system later
EO_PLANT = "eoPlant"
EO_PLANT_ROOT = f"{CEVOPEN_DICT_ROOT}/{EO_PLANT}"
EO_PLANT_DICT = f"{EO_PLANT_ROOT}/eo_plant.xml"

# 2021-09 interns
CROPS =  "https://raw.githubusercontent.com/petermr/crops/main"
VITIS = "Vitis vinifera"
VITIS_DICT = f"{CROPS}/Vitis%20vinifera/eo_Gene.xml"
ZEA = "Zea mays"
ZEA_DICT = f"{CROPS}/Zea%20mays/eo_ZeaTPS.xml"
MENTHA = "Mentha",
MENTHA_DICT = f"{CROPS}/Mentha/eo_Gene.xml"

CEVOPEN_DICTS = {
    EO_PLANT : EO_PLANT_DICT,
    MENTHA : MENTHA_DICT,
    VITIS : VITIS_DICT,
    ZEA : ZEA_DICT,

}

def test_eoPlant_is_valid():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT])

def test_mentha_is_valid():
    _validate_dict(CEVOPEN_DICTS[MENTHA])

def test_vitis_is_valid():
    _validate_dict(CEVOPEN_DICTS[VITIS])

def test_zea_is_valid():
    _validate_dict(CEVOPEN_DICTS[ZEA])

# helper
def _validate_dict(dict_url):
    amidict = AMIDict.create_dict_from_url(dict_url)
    amidict.check_validity()


