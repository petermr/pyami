import os
from configparser import ConfigParser, ExtendedInterpolation
import lxml.etree as ET
import urllib


# local

class AmiConfig:
    """configuration files for the AMI system
    """
    PYAMI_INI = "pyami.ini"
    DIRS = "DIRS"
    DICTS = "DICTIONARIES"
    LINK_SUFFIX = "_link"
    INI_SUFFIX = "_ini"
    URLINI_SUFFIX = "_urlini"
    URL_SUFFIX = "_url"
    SLASH = "/"

    def __init__(self, **kwargs):
        self.inistring = kwargs.get("inistring")
        self.inifile = kwargs.get("inifile")
        self.parser = None
        self._process_init_args()
        self.dict_id_dict = {}

    def _process_init_args(self):
        if self.inistring is not None:
            pass
        elif self.inifile is None:
            self.inifile = os.path.abspath(AmiConfig.get_default_pyami_ini_file())
        if self.inifile is not None:
            if os.path.exists(self.inifile):
                self.parser, _ = AmiConfig.read_ini_get_parser(self.inifile)
        elif self.inistring is not None:
            self.parser = ConfigParser(allow_no_value=True, interpolation=ExtendedInterpolation())
            self.parser.read_string(self.inistring)
            print("read from string")
        else:
            print("arguments wrong")

    def traverse_dictionary_dirs(self):

        assert self.parser is not None
        result = "traversed"
        dict_section = self.parser[AmiConfig.DICTS]
        for dict_key in dict_section.keys():
            print("dict key", dict_key)
            if dict_key.endswith(AmiConfig.LINK_SUFFIX):
                print("skipped link: ", dict_key)
            elif dict_key.endswith(AmiConfig.URL_SUFFIX):
                self.read_url_dicts(dict_key, dict_section)
            elif dict_key.endswith(AmiConfig.INI_SUFFIX):
                self.read_file_dicts(dict_key, dict_section)
            elif dict_key.endswith(AmiConfig.URLINI_SUFFIX):
                print("*_urlini not yet implemented")
            elif dict_key == "dict_dir":
                pass
            else:
                print("skipped key:", dict_key)
        return result

    def read_file_dicts(self, dict_key, dict_section):
        ini_file = self.create_ini_filename_from_link(dict_key, dict_section)
        print("dictionary ini path", dict_key, ini_file)
        if ini_file is None:
            print(f"no ini_file path for {dict_key}, please create in {AmiConfig.PYAMI_INI}")
        if not os.path.exists(ini_file):
            print("INI path does not exist, needs creating", ini_file)
        else:
            dict_config = AmiConfig(inifile=ini_file)
            sub_section = dict_config.parser[AmiConfig.DICTS]
            self.read_amidicts_in_inifile(dict_key, dict_section, sub_section)

    def read_amidicts_in_inifile(self, dict_ref, dict_section, sub_section):
        for dict_id in sub_section.keys():
            print("dict_id", dict_id)
            if dict_id in self.dict_id_dict:
                print("duplicate dict id: ", dict_id)
            if not dict_section[dict_ref] or not sub_section[dict_id]:
                print("No subsection for ", dict_id)
            else:
                file = self.read_dict_xml(dict_ref, dict_section, dict_id, sub_section)
                # FIXME
                if file is not None and dict_id in self.dict_id_dict:
                    self.dict_id_dict[dict_id]

    @classmethod
    def create_ini_filename_from_link(cls, ini_key, dict_section):
        # ini_key = dict_ref[:-(len(AmiConfig.LINK_SUFFIX))] + AmiConfig.INI_SUFFIX
        ini_file = dict_section[ini_key] if ini_key in dict_section else None
        return ini_file

    def read_dict_xml(self, dict_ref, dict_section, dict_name, sub_section):
        ini_dir = dict_section[dict_ref].rpartition(AmiConfig.SLASH)[0]
        file = os.path.join(ini_dir, sub_section[dict_name])
        file = AmiConfig.transform_file_separator(file)
        if not os.path.exists(file):
            print("dict_ref path does not exist", file)
            file = None
        else:
            file_tree_xml = ET.parse(file)
            self._debug_desc_and_entries(dict_name, file_tree_xml)
        return file

    @staticmethod
    def transform_file_separator(file):
        file = file.replace(AmiConfig.SLASH, os.path.sep)
        return file

    @classmethod
    def _debug_desc_and_entries(cls, dict_name, file_tree_xml):
        descs = file_tree_xml.findall("desc")
        entries = file_tree_xml.findall("entry")
        wikidata = file_tree_xml.findall("entry[@wikidataID]")

        if descs:
            print(dict_name, "entries", len(entries), "wikidata", len(wikidata))
            for desc in descs:
                print("d: ", desc.text)
        else:
            print("no descs")

    def read_url_dicts(self, dict_key, dict_section):
        ini_url = self.create_ini_url_from_link(dict_key, dict_section)
        print("read url dicts", ini_url)
        txt = urllib.request.urlopen(ini_url).read().decode('utf-8')
        ami_config = AmiConfig(inistring=txt)
        parent_url = "/".join(ini_url.split("/")[:-1])
        print("section", parent_url)
        ami_config.process_dict_url(AmiConfig.DICTS, parent_url)

    def process_dict_url(self, section, parent_url):
        for dict_name in self.parser[section].keys():
            dict_terminal = self.parser[section][dict_name]
            dict_url = "/".join([parent_url, dict_terminal])
            tree_xml = self.read_xml_from_url(dict_url)
            entries = tree_xml.findall("entry")
            print(dict_terminal, "=", len(entries))

    @classmethod
    def read_xml_from_url(cls, dict_url):
        response = urllib.request.urlopen(dict_url).read()
        tree_xml = ET.fromstring(response)
        return tree_xml

    @staticmethod
    def test():
        ami_config = AmiConfig()
        print("ami", ami_config.parser.keys())
        for k in ami_config.parser.keys():
            print("k", k)
        print("cfg", type(ami_config))

    @staticmethod
    def test_dicts():
        """ finds and prints dictionaries"""
        ami_config = AmiConfig()
        dicts_dirs = ami_config.traverse_dictionary_dirs()
        print("dicts", dicts_dirs)

    @classmethod
    def test2_debug(cls):
        ami_config = AmiConfig()
        for sect_name in ami_config.parser.section_types():
            print("\n>>>>", sect_name, "\n>>>>>")
            section = ami_config.parser[sect_name]
            for k in section.keys():
                print(k)
                print(section[k])

    @staticmethod
    def read_ini_get_parser(ini_file):
        """create inifile name and read it

        return: parser, inifile
        """
        parser = ConfigParser(interpolation=ExtendedInterpolation())
        if not os.path.exists(ini_file):
            print("INI path does not exist", ini_file)
        else:
            print("read", AmiConfig.PYAMI_INI, ini_file)
            parser.read(ini_file)
        return parser, ini_file

    @staticmethod
    def get_default_pyami_ini_file():
        inifile = os.path.join(AmiConfig.get_home(), AmiConfig.PYAMI_INI)
        return inifile

    @staticmethod
    def get_home():
        home = os.path.expanduser("~")
        return home

    @staticmethod
    def create_ini_url_from_link(dict_ref, dict_section):
        ini_key = dict_ref[:-(len(AmiConfig.URL_SUFFIX))] + AmiConfig.INI_SUFFIX
        ini_file = dict_section[ini_key] if ini_key in dict_section else None
        return ini_file

    @classmethod
    def tests(cls):
        cls.test()
        cls.test_dicts()
        cls.test2_debug()
