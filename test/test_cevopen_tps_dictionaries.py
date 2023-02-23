import sys
import unittest
# local
import requests

from py4ami.ami_dict import AmiDictionary
# from test.test_pdf import PDFTest/

"""
Code for VALIDATING specific DICTIONARIES , not the code

These are effectively tests for the dictionaries
Requires connection to the Web
 """

VERY_LONG = True
TEST_DICT_CONTENT = False
# TEST_DICT_CONTENT = True

CEVOPEN_WEB_ROOT = "https://raw.githubusercontent.com/petermr/CEVOpen/master"

CEVOPEN_WEB_DICT_ROOT = f"{CEVOPEN_WEB_ROOT}/dictionary"
# this will use the config.ini system later

EO_ACTIVITY = "eoActivity"
EO_ACTIVITY_WEB_ROOT = f"{CEVOPEN_WEB_DICT_ROOT}/{EO_ACTIVITY}/eo_activity"
EO_ACTIVITY_WEB_DICT = f"{EO_ACTIVITY_WEB_ROOT}/activity.xml"
WEB_DICT_URL = "https://raw.githubusercontent.com/petermr/CEVOpen/master/dictionary/eoActivity/eo_activity/activity.xml"
assert EO_ACTIVITY_WEB_DICT == WEB_DICT_URL

EO_COMPOUND = "eoCompound"
EO_COMPOUND_WEB_ROOT = f"{CEVOPEN_WEB_DICT_ROOT}/{EO_COMPOUND}"
EO_COMPOUND_WEB_DICT = f"{EO_COMPOUND_WEB_ROOT}/plant_compound.xml"

EO_PLANT = "eoPlant"
EO_PLANT_WEB_ROOT = f"{CEVOPEN_WEB_DICT_ROOT}/{EO_PLANT}"
EO_PLANT_WEB_DICT = f"{EO_PLANT_WEB_ROOT}/eo_plant.xml"

EO_PLANT_PART = "eoPlantPart"
EO_PLANT_PART_WEB_ROOT = f"{CEVOPEN_WEB_DICT_ROOT}/{EO_PLANT_PART}"
EO_PLANT_PART_WEB_DICT = f"{EO_PLANT_PART_WEB_ROOT}/eoplant_part.xml"

EO_PLANT_GENUS = "plant_genus"
EO_PLANT_GENUS_WEB_ROOT = f"{CEVOPEN_WEB_DICT_ROOT}/{EO_PLANT_GENUS}"
EO_PLANT_GENUS_WEB_DICT = f"{EO_PLANT_GENUS_WEB_ROOT}/plant_genus.xml"

"""verificationTest/MicrobeMod_FungalPro.xml"""
VERIFICATION_TEST = "verificationTest"
WEB_VERIFICATION_ROOT = f"{CEVOPEN_WEB_DICT_ROOT}/{VERIFICATION_TEST}"
MICRO_FUNGAL_PRO_WEB_DICT = f"{WEB_VERIFICATION_ROOT}/MicrobeMod_FungalPro.xml"
MICRO_FUNGAL_PRO = "MicroFungal_Pro"


SAGAR_REPO = "https://raw.githubusercontent.com/sasujadhav1/Files/main/"

# species
BIONAB = "bionomial_abbreviation",
BIONAB_XML = f"{SAGAR_REPO}/bionomial_abbreviation.xml"


# enzymes
ENZYMES = "enzymes",
ENZYMES_XML = f"{SAGAR_REPO}/enzyme_names.xml"


# 2021-09 interns
CROPS = "https://raw.githubusercontent.com/petermr/crops/main"

# https://github.com/sasujadhav1/Files/blob/main/bionab.xml
# https://github.com/sasujadhav1/Files/blob/main/enzyme_names.xml

MENTHA = "Mentha",
MENTHA_DICT = f"{CROPS}/Mentha/eo_menthaTPS.xml"
SOLANUM = "Solanum",
SOLANUM_DICT = f"{CROPS}/Solanum%20lycopersicum/eo_tomato.xml"
VITIS = "Vitis vinifera"
VITIS_DICT = f"{CROPS}/Vitis/eo_VVinifera.xml"
ZEA = "Zea mays"
ZEA_DICT = f"{CROPS}/Zea%20mays/eo_ZeaTPS.xml"

CEVOPEN_DICTS = {
    EO_ACTIVITY:  EO_ACTIVITY_WEB_DICT,
    EO_COMPOUND:  EO_COMPOUND_WEB_DICT,
    EO_PLANT: EO_PLANT_WEB_DICT,
    EO_PLANT_GENUS: EO_PLANT_GENUS_WEB_DICT,
    EO_PLANT_PART: EO_PLANT_PART_WEB_DICT,

    # suffix, species
    ENZYMES: ENZYMES_XML,
    BIONAB: BIONAB_XML,

    # 2021 interns
    MENTHA: MENTHA_DICT,
    SOLANUM: SOLANUM_DICT,
    VITIS: VITIS_DICT,
    ZEA: ZEA_DICT,

    # Manny dictionaries
    MICRO_FUNGAL_PRO: MICRO_FUNGAL_PRO_WEB_DICT,
}

def test_can_read_dictionaries_from_web():
    assert can_run_dictionaries(), f"cannot read from web"


def can_run_dictionaries():
    try:
        request = requests.get(WEB_DICT_URL)
    except Exception as e:
        print (f"Cannot access WEB_DICT_URL; most tests will fail;{e}")
        return False
    return True


# core plant dictionaries


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_eo_activity():
    if not can_run_dictionaries():
        raise Exception("Cannot access web")
    # print(f"sys.argv {sys.argv}")
    _validate_dict(CEVOPEN_DICTS[EO_ACTIVITY])


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_eo_compound():
    _validate_dict(CEVOPEN_DICTS[EO_COMPOUND])


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_eo_plant():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT])


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_eo_plant_genus():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT_GENUS])


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_eo_plant_part():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT_PART])


# CEVOpen 2021

@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_mentha():
    _validate_dict(CEVOPEN_DICTS[MENTHA])


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_solanum():
    _validate_dict(CEVOPEN_DICTS[SOLANUM])


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_vitis():
    vitis_ = CEVOPEN_DICTS[VITIS]
    assert vitis_ == "https://raw.githubusercontent.com/petermr/crops/main/Vitis/eo_VVinifera.xml"
    _validate_dict(vitis_)


@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_zea():
    zea_ = CEVOPEN_DICTS[ZEA]
    assert zea_ == "https://raw.githubusercontent.com/petermr/crops/main/Zea%20mays/eo_ZeaTPS.xml"
    _validate_dict(zea_)


# enzymes
@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_enzymes():
    enzymes = CEVOPEN_DICTS[ENZYMES]
    _validate_dict(enzymes)


# bionomial abbreviations
@unittest.skipUnless(TEST_DICT_CONTENT, "skipped testing dictionaries")
@unittest.skipUnless(can_run_dictionaries(), "cannot run dictionaries from web")
def test_check_binomial_abbreviations():
    bionab = CEVOPEN_DICTS[BIONAB]
    _validate_dict(bionab)




# helper ----------------
def _validate_dict(dict_url):
    amidict = AmiDictionary.create_dictionary_from_url(dict_url)
    amidict.check_validity()
