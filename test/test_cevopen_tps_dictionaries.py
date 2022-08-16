import sys
import unittest
# local
from py4ami.ami_dict import AmiDictionary

"""Code for VALIDATING specific DICTIONARIES , not the code

 These are effectively tests for the dictionaries
 """


CEVOPEN_ROOT = "https://raw.githubusercontent.com/petermr/CEVOpen/master"

CEVOPEN_DICT_ROOT = f"{CEVOPEN_ROOT}/dictionary"
# this will use the config.ini system later

EO_ACTIVITY = "eoActivity"
EO_ACTIVITY_ROOT = f"{CEVOPEN_DICT_ROOT}/{EO_ACTIVITY}/eo_activity"
EO_ACTIVITY_DICT = f"{EO_ACTIVITY_ROOT}/activity.xml"

EO_COMPOUND = "eoCompound"
EO_COMPOUND_ROOT = f"{CEVOPEN_DICT_ROOT}/{EO_COMPOUND}"
EO_COMPOUND_DICT = f"{EO_COMPOUND_ROOT}/plant_compound.xml"

EO_PLANT = "eoPlant"
EO_PLANT_ROOT = f"{CEVOPEN_DICT_ROOT}/{EO_PLANT}"
EO_PLANT_DICT = f"{EO_PLANT_ROOT}/eo_plant.xml"

EO_PLANT_PART = "eoPlantPart"
EO_PLANT_PART_ROOT = f"{CEVOPEN_DICT_ROOT}/{EO_PLANT_PART}"
EO_PLANT_PART_DICT = f"{EO_PLANT_PART_ROOT}/eoplant_part.xml"

EO_PLANT_GENUS = "plant_genus"
EO_PLANT_GENUS_ROOT = f"{CEVOPEN_DICT_ROOT}/{EO_PLANT_GENUS}"
EO_PLANT_GENUS_DICT = f"{EO_PLANT_GENUS_ROOT}/plant_genus.xml"

"""verificationTest/MicrobeMod_FungalPro.xml"""
VERIFICATION_TEST = "verificationTest"
VERIFICATION_ROOT = f"{CEVOPEN_DICT_ROOT}/{VERIFICATION_TEST}"
MICRO_FUNGAL_PRO_DICT = f"{VERIFICATION_ROOT}/MicrobeMod_FungalPro.xml"
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
    EO_ACTIVITY:  EO_ACTIVITY_DICT,
    EO_COMPOUND:  EO_COMPOUND_DICT,
    EO_PLANT: EO_PLANT_DICT,
    EO_PLANT_GENUS: EO_PLANT_GENUS_DICT,
    EO_PLANT_PART: EO_PLANT_PART_DICT,

    # suffix, species
    ENZYMES: ENZYMES_XML,
    BIONAB: BIONAB_XML,

    # 2021 interns
    MENTHA: MENTHA_DICT,
    SOLANUM: SOLANUM_DICT,
    VITIS: VITIS_DICT,
    ZEA: ZEA_DICT,

    # Manny dictionaries
    MICRO_FUNGAL_PRO: MICRO_FUNGAL_PRO_DICT,
}

# core plant dictionaries


def test_check_eo_activity():
    # print(f"sys.argv {sys.argv}")
    _validate_dict(CEVOPEN_DICTS[EO_ACTIVITY])


@unittest.skip("testing multiple dictiomaries")
def test_check_eo_compound():
    _validate_dict(CEVOPEN_DICTS[EO_COMPOUND])


def test_check_eo_plant():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT])


def test_check_eo_plant_genus():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT_GENUS])


def test_check_eo_plant_part():
    _validate_dict(CEVOPEN_DICTS[EO_PLANT_PART])


# CEVOpen 2021

def test_check_mentha():
    _validate_dict(CEVOPEN_DICTS[MENTHA])


def test_check_solanum():
    _validate_dict(CEVOPEN_DICTS[SOLANUM])


def test_check_vitis():
    vitis_ = CEVOPEN_DICTS[VITIS]
    assert vitis_ == "https://raw.githubusercontent.com/petermr/crops/main/Vitis/eo_VVinifera.xml"
    _validate_dict(vitis_)


def test_check_zea():
    zea_ = CEVOPEN_DICTS[ZEA]
    assert zea_ == "https://raw.githubusercontent.com/petermr/crops/main/Zea%20mays/eo_ZeaTPS.xml"
    _validate_dict(zea_)


# enzymes
def test_check_enzymes():
    enzymes = CEVOPEN_DICTS[ENZYMES]
    _validate_dict(enzymes)


# bionomial abbreviations
def test_check_binomial_abbreviations():
    bionab = CEVOPEN_DICTS[BIONAB]
    _validate_dict(bionab)


# Manny dictionaries# @unittest.skip("URL not valid")
# # def test_check_micro_fungal():
# #     micro_fungal = CEVOPEN_DICTS[MICRO_FUNGAL_PRO]
# #     _validate_dict(micro_fungal)


# helper ----------------
def _validate_dict(dict_url):
    amidict = AmiDictionary.create_dictionary_from_url(dict_url)
    amidict.check_validity()
