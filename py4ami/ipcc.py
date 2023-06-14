import re
from collections import defaultdict, Counter
from pathlib import Path

import lxml
from lxml.etree import _Element
import pandas as pd

from py4ami.ami_html import URLCache, HtmlUtil
from py4ami.xml_lib import HtmlLib, XmlLib

class IPCCSections:

    @classmethod
    def get_ipcc_regexes(cls, front_back="Table of Contents|Frequently Asked Questions|Executive Summary|References"):
        """
        :param front_back: common section headings (not numbered)
        :return: (section_regex_dict, section_regexes) to manage regexes (largely for IPCC).

        The dict is more powerful but doesn't work properly yet

        """
        section_regexes = [
            # C: Adaptation...
            ("section",
             #                f"\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References|(?:(?:[A-G]|\d+)[\.:]\d+\s+[A-Z]).*"),
             fr"\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References"
             fr"|(?:[A-Z]|\d+)[.:]\d*)\s+[A-Z].*"),
            # 7.1 Introduction
            ("sub_section",
             fr"(?P<id>FAQ \d+\.\d+"
             fr"|(?:\d+\.\d+"
             fr"|[A-Z]\.\d+)"
             fr"\.\d+)"
             fr"\s+[A-Z]*"),  # 7.1.2 subtitle or FAQ 7.1 subtitle D.1.2 Subtitle
            ("sub_sub_section",
             fr"(?P<id>"
             fr"(?:\d+\.\d+\.\d+\.\d+"  # 7.1.2.3 subsubtitle
             fr"|[A-Z]\.\d+\.\d+)"
             fr")\s+[A-Z].*")  # D.1.3
        ]
        section_regex_dict = {
            "num_faq": {
                "file_regex": "NEVER.*/spm/.*",  # check this
                "sub_section": fr"(?P<id>FAQ \d+\.\d+)"
            },
            "alpha_sect": {
                "file_regex": ".*(srocc).*/spm/.*",  # check this
                "desc": "sections of form 'A: Foo', 'A.1 Bar', 'A.1.2 'Baz'",
                "section": fr"\s*(?P<id>[A-Z][.:]\s+[A-Z].*)",  # A: Foo
                "sub_section": fr"\s(?P<id>[A-Z]\.\d+\.\d+)\s+[A-Z]*",  # A.1 Bar
                "sub_sub_section": fr"\s(?P<id>[A-Z]\.\d+\.\d+)\s+[A-Z]*"  # A.1.2 Plugh
            },
            "num_sect_old": {
                "file_regex": ".*NEVER.*",
                "desc": "sections of form '1. Introduction', "
                        "subsections '1.2 Bar' "
                        "subsubsections '1.2.3 Plugh'"
                        "subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                "section": fr"\s*(?P<id>(?:{front_back}|\s*\d+[.:]?)\s+[A-Z].*",  # A: Foo
                "sub_section": fr"\s(?P<id>\d+\.\d+)\s+[A-Z].*",  # A.1 Bar
                "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*"  # A.1.2 Plugh

            },
            "num_sect": {
                "file_regex": ".*/syr/lr.*",
                "desc": "sections of form '1. Introduction', "
                        "subsections '1.2 Bar' "
                        "subsubsections '1.2.3 Plugh'"
                        "subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                "section": fr"\s*(?P<id>{front_back})"
                           fr"|Section\s*(?P<id1>\d+):\s*[A-Z].*"
                           fr"|\s*(?P<id2>\d+)\.\s+[A-Z].*",  # A: Foo
                "sub_section": fr"\s*(?P<id>\d+\.\d+)\s+[A-Z].*",  # 1.1 Bar
                "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*"  # A.1.2 Plugh

            },
            "num_sect_new": {
                "file_regex": fr"NEW.*/syr/lr.*",
                "sections": {
                    "desc": f"sections of form '1. Introduction', "
                            f"subsections '1.2 Bar' "
                            f"subsubsections '1.2.3 Plugh'"
                            f"subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                    "section": {
                        "desc": "sections of form '1. Introduction' ",
                        "regex": fr"\s*(?P<id>{front_back}|\s*\d+[.:]?)\s+[A-Z].*",  # A: Foo
                    },
                    "sub_section": {
                        "desc": "sections of form ''1.2 Bar' ",
                        "regex": fr"\s(?P<id>\d+\.\d+)\s+[A-Z].*",  # A.1 Bar
                    },
                    "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*",  # A.1.2 Plugh
                },
                "references": "dummy"

            },
        }
        return section_regex_dict, section_regexes

class IPCCAnchor:
    """holds statements from IPCC Reports and outward links"""

    @classmethod
    def create_confidences(cls, div):
        """iterates over all spans in div, terminating if "* confidence is found,
         starting new div until end. ignores {targets}
        some chunks may not make grammatical sense
        :return: divs with original span"""
        curly_re = re.compile("(?P<pre>.*)\{(?P<targets>.*)\}(?P<post>.*)")
        confidence_re = re.compile("\s*\(?(?P<level>.*)\s+confidence\s*\)?\s*(?P<post>.*)")
        parent = div.getparent()
        current_div = None
        spans = list(div.xpath("./span"))
        for span in spans:
            if not span.text:
                continue
            if current_div is None:
                current_div = lxml.etree.SubElement(parent, "div")
            if "confidence" in span.text and len(span.text) < 50:  # because confidence can occur elsewhere
                current_div.append(span)
                match = confidence_re.match(span.text)
                level = match.group("level")
                span.attrib["confidence"] = level
                print(f"confidence: {level}")
                span.attrib["class"] = "confidence"
                span.attrib["style"] = "background: #ddffff"
                # confidence ends div
                current_div = None
            else:
                match = curly_re.match(span.text)
                if match:
                    span = lxml.etree.SubElement(current_div, "span")
                    span.text = match.group("pre")
                    span = lxml.etree.SubElement(current_div, "span")
                    span.attrib["class"] = "targets"
                    span.text = match.group("targets")
                    span = lxml.etree.SubElement(current_div, "span")
                    span.text = match.group("post")
                else:
                    current_div.append(span)
        parent.remove(div)

class IPCCTargetLink:
    """link between IPCC reports"""

    def __init__(self, ipcc_id, span_link):
        self.ipcc_id = ipcc_id
        self.span_link = span_link
        self.link_factory = None
        self.bad_links = set()

    def _follow_ipcc_target_link(
            self,
            ipcc_target_link,
            anchor_link,
            wg_dict=None,
            url_cache=None,
            stem="ipcc/ar6",
            leaf_name=None):

        if not leaf_name:
            print(f"must give leaf name")
            return None, None
        if anchor_link is not None:
            anchor = lxml.etree.SubElement(anchor_link, "a")
            anchor.text = ipcc_target_link

        if not self.make_report_chapter_id(ipcc_target_link, wg_dict):
            self.bad_links.add(ipcc_target_link)
            return None, None
        (chapter, id, report) = self.make_report_chapter_id(ipcc_target_link, wg_dict)

        filepath = f"{stem}/{report}/{chapter}/{leaf_name}"
        html = None
        branch = "main"
        site = self.link_factory.target.site
        site = "https://raw.githubusercontent.com" if not site else site
        username = self.link_factory.target.username
        repository = self.link_factory.target.repository
        target_url = f"{site}/{username}/{repository}/{branch}/{filepath}"
        # print(f"target_url {target_url}")
        try:
            html = XmlLib.read_xml_element_from_github(github_url=target_url, url_cache=url_cache)
        except Exception as e:
            # print(f"failed to read HTML {e}")
            pass
        if html is None:
            # print(f"failed to read HTML")
            return None, None
        # print(f"looking for ID {id}")
        sections = html.xpath(f"//*[@id='{id}']")
        target_text = ""
        for i, section in enumerate(sections):
            target_text += ("" if i == 0 else "SEP") + ''.join(section.getparent().itertext())
        return (id, target_text) if target_text else (None, None)

    def make_report_chapter_id(self, ipcc_link, wg_dict):
        """splits REPORT CHAP ID string
        e.g. WGI SPM A.1.2.3 => wg1/spm#A.1.2.3
        :return: None if cannot parse
        """
        href = ipcc_link.strip().split()
        if len(href) != 3:
            # print(f"target must have 3 components {ipcc_link}")
            return None
        report = wg_dict.get(href[0])
        if not report:
            # print(f"cannot find report from {href[0]}")
            return None
        chapter = href[1].lower() if len(href) > 1 else None
        chapters = ["spm", "lr", "ts"]
        if chapter not in chapters:
            # print(f"only chapters : {chapters} allowed")
            return None

        id = href[2] if len(href) > 2 else None
        if not id:
            return None
        return chapter, id, report

    def follow_ipcc_target_link(self, url_cache=None, leaf_name=None):
        """
        :return: tuple (id, target text)
        """
        link_factory = self.link_factory
        ipcc_id = self.ipcc_id
        anchor_link = self.span_link

        # github_url = link_factory.create_github_url()

        target_result_tuple = self._follow_ipcc_target_link(ipcc_id, anchor_link, wg_dict=link_factory.wg_dict,
                                                            url_cache=url_cache, leaf_name=leaf_name, )
        # print(f"type {type(target_result_tuple)} len {len(target_result_tuple)}")
        (idx, target_text) = target_result_tuple
        # print(f"id {type(idx)} text {type(target_text)}")
        return (idx, target_text)

    @classmethod
    def read_links_from_span_and_follow_to_ipcc_repository_KEY(cls, anchor_div, leaf_name, link_factory,
                                                               span_with_curly_ids):
        """
        reads a span in an chor_div and extracts curly link_ids
        splits the curly content into target ids (curly_count)

        Follows these to repository
        returns a table with (<= curly_count

        :param anchor_div: if not None adds an anchor
        """
        if anchor_div is None:
            raise ValueError(f" anchor_div must not be None")

        anchor_id = anchor_div.attrib.get("id")
        if not anchor_id:
            spans = anchor_div.xpath("./span")
            if len(spans) > 0:
                anchor_id = spans[0].get("id")
        target_to_anchor_table = []
        bad_links = set()
        text = ''.join(anchor_div.itertext())
        if not anchor_id:
            print(f" anchor_id is None for {text[:50]}")
            return target_to_anchor_table, bad_links
        curly_brace_link_content_parser = re.compile(".*{(?P<links>[^}]+)}.*")
        match = curly_brace_link_content_parser.match(span_with_curly_ids.text)
        if match:
            links_text = match.group("links")
            ipcc_ids = re.split(",|;", links_text)
            anchor_span_link = lxml.etree.SubElement(anchor_div, "span")
            anchor_span_link.attrib["id"] = anchor_id
            url_cache = URLCache()
            parent_div = span_with_curly_ids.getparent()
            anchor_text = ''.join(parent_div.itertext())
            # print (f" ipcc_ids {ipcc_ids}")
            for ipcc_id in ipcc_ids:
                target_link = link_factory.create_target_link(ipcc_id, anchor_span_link)
                (target_id, target_text) = target_link.follow_ipcc_target_link(url_cache=url_cache,
                                                                               leaf_name=leaf_name)
                if (target_id, target_text):
                    anchor_to_target_row = [anchor_id, anchor_text, ipcc_id, target_id, target_text]
                    target_to_anchor_table.append(anchor_to_target_row)
                bad_links.update(target_link.bad_links)
        if target_to_anchor_table:
            # this is just debug
            # print(f"**ROWS**{len(target_to_anchor_table)}\n{target_to_anchor_table}")
            anchor_target_df = pd.DataFrame(target_to_anchor_table,
                                            columns=["a_id", "a_text", "ipcc_id", "t_id", "t_text"])
            # print(f"anchor_to_target dataframe:\n {anchor_target_df}")
        # print(f"bad links {bad_links}")
        return target_to_anchor_table, bad_links

    @classmethod
    def create_dataframe_from_IPCC_target_ids_in_curly_brackets_divs_KEY(cls, divs, leaf_name, link_factory):
        table = []
        bad_link_set = set()
        table.append(["anchor_text", "anchor_id", "target_id", "target_text"])
        curly_re = re.compile(".*\{(P<curly>[.^\}]*)\}.*")
        for div in divs:
            cls.follow_ids_in_curly_links(bad_link_set, curly_re, div, leaf_name, link_factory, table)
            IPCCAnchor.create_confidences(div)
        print(f" table {len(table)}")
        print(f"bad_link_set {bad_link_set}")
        df = pd.DataFrame(table)
        return df

    @classmethod
    def follow_ids_in_curly_links(cls, bad_link_set, curly_re, div, leaf_name, link_factory, table):
        id_spans = div.xpath("./span[@id]")
        anchor_id = None if len(id_spans) == 0 else id_spans[0].attrib.get("id")
        # print(f"anchor_id {anchor_id}")
        # print(f" targets span {span.text}")
        for span in div.xpath("./span[@class='targets']"):
            match = curly_re.match(span.text)
            if match:
                print(f"match group {match.group('curly')}")
            rows, bad_links = IPCCTargetLink.read_links_from_span_and_follow_to_ipcc_repository_KEY(div, leaf_name,
                                                                                                    link_factory,
                                                                                                    span)
            bad_link_set.update(bad_links)
            if rows:
                table.extend(rows)

class IPCCTarget:
    """
    parses target string and maybe caches some data
    """
    def __init__(self):
        self.raw = "" #raw text
        self.package = "" # WG2, SRCCL, etc.
        self.section = "" # Chapter, Annexe, etc
        self.object = "" # Figure, Table, etc
        self.subsection = "" # A, B,   A.1.2, etc
        self.unparsed_str = "" #anything else

    # class Target:

    def __str__(self):
        ss = self.__repr__()
        return ss

    def create_list(self):
        ll = [self.package, self.section, self.object, self.subsection, self.unparsed_str, self.raw]
        return ll

    def __repr__(self):
        return "|".join(self.create_list())

    # class Target:

    @classmethod
    def create_target_from_fields(cls, str):
        """
        parse __str__ string into field where possible

        package, section, object, subsection, unparsed, raw
        :param strings: the fields in the Target
        """
        target = None
        strings = str.split(',')
        if strings and len(strings) >= 5:
            target = IPCCTarget()
            target.package = strings[0]
            target.section = strings[1]
            target.object = strings[2]
            target.subsection = strings[3]
            target.unparsed_str = strings[4]
        if strings and len(strings) == 6:
            target.raw = strings[5]

        # assert target is not None, f"cannot create target from {str}"
        return target

    # class Target:

    @classmethod
    def create_target_from_str(cls, string):
        """
        parse string into hierarchy where possible
        package, section, object, subsection, section
        """
        target = IPCCTarget()
        target.raw = string
        # string = cls.add_missing_commas(string)
        strings = re.split("\s+", string)
        ptr = 0
        target.package, ptr = cls.parse_chunk(strings, ptr, package_re, "package")
        target.section, ptr = cls.parse_chunk(strings, ptr, section_re, "section")
        target.object, ptr = cls.parse_chunk(strings, ptr, object_re, "object")
        target.subsection, ptr = cls.parse_chunk(strings, ptr, subsection_re, "subsection")
        # target.subsubsection, ptr = cls.parse_chunk(strings, ptr, subsubsection_re, "subsubsection")
        if len(strings) > ptr:
            target.unparsed_str = ' '.join(strings[ptr:])
        return target

    # class Target:

    @classmethod
    def parse_chunk(cls, strings, ptr, pattern, name):
        """
        takes new chunk off the list (should be a stack) and parsers
        If successful returns the chunk and advances pointer; else returns "" and no advance
        """
        if ptr >= len(strings):
            return "", ptr
        try:
            match = re.match(pattern, strings[ptr])
        except Exception as e:
            raise ValueError(f"regex error {e} in {pattern}")
        if match:
            return strings[ptr], ptr + 1
        return "", ptr

    # class Target:

    def normalize(self):
        """removes porse errors and inconsistency of formats, etc
        """
        unparsed_words = self.unparsed_str.split()
        if len(unparsed_words) >= 1:
            # print(f">>>> norm {self}")
            first = unparsed_words[0]
            if first == 'SPM':
                pass
            # section in unparsed and missing/duplicated in self.section
            if re.match(section_re, first) and self.section == '' or self.section == first:
                self.section = first
                unparsed_words.pop(0)
            # move single unparsed to empty subsection
            if len(unparsed_words) == 1 and self.subsection == '':
                self.transfer_first_unparsed_to_subsection(unparsed_words)
            # named CCBox
            if self.object == 'CCBox':
                # print(f" self ccbox: {self}")
                if self.subsection == '':
                    if len(self.unparsed_str) == 1 or \
                        len(self.unparsed_str) >= 1 and self.unparsed_str[0].isupper():
                            self.transfer_first_unparsed_to_subsection(unparsed_words)
                            unparsed_words.pop()
            # chapter/ES ['WGII', '', '', '7', ['ES'], 'WGII 7 ES']
            if unparsed_words == ['ES']:
                print("self ES {self}")
            if len(unparsed_words) == 3 and unparsed_words[:2] == ["in", "Chapter"]:
                if self.section == '':
                    self.section = unparsed_words[1] # type
                    section_number = unparsed_words[2] # number
                    self.subsection = section_number + "." +  self.subsection
                    unparsed_words = unparsed_words[3:]
                    # print(f"in_Chapter {self}")

            if unparsed_words and self.subsection == unparsed_words[0]:
                unparsed_words = unparsed_words[1:]
            self.unparsed_str = " ".join(unparsed_words)
            if self.unparsed_str != "":
                print(f"UNPARSED {self}")

    @classmethod
    def make_dirs_from_targets(cls, common_target_tuples, temp_dir):
        assert temp_dir is not None, f"must have temp_dir"
        for target_string in common_target_tuples:
            target_strs = target_string[0]
            # TODO make parsable target string
            target = IPCCTarget.create_target_from_fields(target_strs)
            if not target:
                # print(f"bad target {target_string}")
                continue
            target.make_directories(temp_dir)

    def make_directories(self, temp_dir):
        """makes directories from sections/subsections, etc"""
        if not self.package:
            pass
        package_dir = Path(temp_dir, self.package)
        package_dir.mkdir(exist_ok=True)
        parent_dir = package_dir
        if self.section:
            section_dir = Path(parent_dir, self.section)
            section_dir.mkdir(exist_ok=True)
            parent_dir = section_dir
        if self.object:
            object_dir = Path(parent_dir, self.object)
            object_dir.mkdir(exist_ok=True)
            parent_dir = object_dir
        if self.subsection:
            subsection_file = Path(parent_dir, self.subsection)
            subsection_file.touch()


    # class Target:

    def transfer_first_unparsed_to_subsection(self, unparsed_words):
        # words = self.unparsed_str.split()
        self.subsection = unparsed_words[0]
        # words = " ".join(words[1:])
        # return words

    def type(self):
        pass


class TargetExtractor:

    """
    extracts nodes/hyperlinks in text
    """
    UNMATCHED = "unmatched"
    TARGET_LIST_RE = "node_re"
    TARGET_RE = "split_node_re"
    TARGET_VALUE_RE = "name_value_re"

    def __init__(self):
        self.column_dict = dict()

#class TargetExtractor

    def read_columns(self, names):
        assert names and type(names) is list, f"must give list of names"
        for col_no, name in enumerate(names):
            if name.strip() == "" or " " in name:
                raise ValueError(f"names must not be/have whitespace [{name}]")
            if name in self.column_dict:
                raise ValueError(f"duplicate column name {name}")
            self.column_dict[name] = col_no

    @classmethod
    def create_target_extractor(cls, column_names):
        try:
            target_extractor = TargetExtractor()
            target_extractor.read_columns(column_names)
            return target_extractor
        except ValueError as e:
            raise e

    # class TargetExtractor

    def extract_node_dict_lists_from_file(self, xml_inpath, div_xp=None, regex_dict=None):
        """
        extracts lists of nodes in text. Nodes are defined by xpath and regex
        :param xml_inpath: file with divs
        :param div_xp: Must return <div> elements at present
        :param regex_dict: dict of regexes to extract nodes
        """
        assert xml_inpath.exists(), f"{xml_inpath} should exist"
        tree = lxml.etree.parse(str(xml_inpath))
        root = tree.getroot()
        HtmlUtil.add_generated_ids(root) # adds ids to each element
        if div_xp is None or regex_dict is None:
            return None
        print(f"div_xp {div_xp}")
        divs_with_text = list(root.xpath(div_xp))
        ll = len(divs_with_text)
        print(f"xpath/tree texts {ll}")
        node_dict_list_list = list()
        for div in divs_with_text:
            if type(div) is not _Element:
                raise ValueError(f"div_xpath must return divs")
            node_dict_list = self.extract_nodes_by_regex(div, regex_dict=regex_dict)
            node_dict_list_list.append(node_dict_list)
        return node_dict_list_list

    # class TargetExtractor

    def extract_nodes_by_regex(self, div_with_text, regex_dict=None) -> list:
        """
        Searches text with hierachical regexes
        """
        div_id = div_with_text.attrib.get('id')
        text_in_div = ''.join(div_with_text.itertext())
        print(f"{div_id} {text_in_div[:100]}")

        ptr = 0
        node_dict_list = list()
        if regex_dict is None:
            return node_dict_list
        reg1 = regex_dict.get(TargetExtractor.TARGET_LIST_RE)
        reg2 = regex_dict.get(TargetExtractor.TARGET_RE)
        reg3 = regex_dict.get(TargetExtractor.TARGET_VALUE_RE)
        if reg1 is None or reg2 is None or reg3 is None:
            return node_dict_list
        while text_in_div[ptr:] is not None:
            ptr_ = text_in_div[ptr:]
            match = re.search(reg1, ptr_)
            if match is None:
                break
            ptr += match.span()[1]
            nodestr = match.group(1)
            nodes = re.split(reg2, nodestr)
            node_dict = defaultdict(list)
            node_dict_list.append(node_dict)
            for node in nodes:
                m = re.match(reg3, node)
                if m:
                    node_dict[m.group(1)].append(m.group(2))
                    node_dict["div_id"] = div_id
                    print(f"node_dict {node_dict}")
                    continue
                node_dict[TargetExtractor.UNMATCHED].append(node)
            pass
        pass
        return node_dict_list

    # class TargetExtractor

    def extract_anchor_paragraphs(self, div_xp, file, target_dict_from_text):
        """
        reads xml file , finds divs, applies regexes to find targetrefss in text
        """
        node_dict_list_list = self.extract_node_dict_lists_from_file(
            file,
            div_xp=div_xp,  # all paras wit curly {...
            regex_dict=target_dict_from_text)

        def_dict = defaultdict()

        for node_dict_list in node_dict_list_list:
            ll = len(node_dict_list)
            if ll > 1:
                print(f"*****node_dict_list {ll}")
                for node_dict in node_dict_list:
                    print(f"----{len(node_dict.keys())}----")
                    for key in node_dict.keys():
                        print(f"key {key} ") # mainly unmatched but also Table, div_id
                        value_list = node_dict[key]
                        print(f"value_list {value_list}")
                        for value in value_list:
                            if value not in def_dict:
                                def_dict[value] = 0
                            def_dict[value] += 1
                    print("")
        return def_dict

    # class TargetExtractor

    @classmethod
    def add_missing_commas(cls, string):
        """
        some targets are (wrongly) concatenated
        """
        string = string.replace(" WG", ", WG")
        string = string.replace(" SR", ", SR")
        return string

    # class TargetExtractor

    @classmethod
    def create_normalized_target(cls, target_str):

        target_str = cls.clean_target_string(target_str)
        target = IPCCTarget.create_target_from_str(target_str)
        target.normalize()
        return target

    # class TargetExtractor

    @classmethod
    def clean_target_string(cls, target_str):
        """
        cleans typos from target string
        """
        subst_list = [
            ["SR\s*1\.5", "SR1.5 ", "rejoin package name"],
            ["WG1\.", "WG1 ", "separate package from section"],
            ["TS\.", "TS ", "separate subpackage from sections"],
            ["SPM\.", "SPM ", "separate subpackage from sections"],
            ["\s+", " ", "normalise to 1 space"],
            ["WPM", "SPM", "single instance"],
            ["WG\s*I", "WGI", "remove internal sp ('WG II')"],
            ["Cross\-([Cc]hapter)\s*[Bb]ox", "CCBox", "Cross Chapter Box"],
            ["Cross\-([Ss]ection)\s*[Bb]ox", "CSBox", "Cross Section Box"],
            ["Cross\-([Ww]orking\s+[Gg]roup|WG)\s+[Bb]ox", "CWGBox", "Cross Working Group"],
        ]

        for subst in subst_list:
            target_str = re.sub(subst[0], subst[1], target_str)  # separate subpackage from sections
        return target_str

    # class TargetExtractor

    @classmethod
    def extract_ipcc_fulltext_into_source_target_table(cls, file):
        """
        partly written by ChatGPT (2023-04-06) but mainly by PMR
        """
        tree = lxml.etree.parse(file)
        root = tree.getroot()
        # Initialize the table
        table = []
        unparsed = 0
        # TODO extract source_id from IPCC paragraphs
        section_re = re.compile("^([A-Z]|\d)(\.\d+)*$")
        last_section_id = ""
        for paragraph in root.findall('.//div'):
            paragraph_id = paragraph.get('id')
            para_text = ''.join(paragraph.itertext())
            label = paragraph.findall("./span")
            strip = "no span" if not label else label[0].text.strip()
            section_match = section_re.match(strip)
            section_id = section_match.group(0) if section_match else ""
            if section_id != '':
                # print(f"section_id {section_id}")
                last_section_id = section_id
            unp, para_table = cls.match_id_and_targets_in_para(para_text, paragraph_id, last_section_id)
            unparsed += unp
            if para_table == []:
                continue
            table.extend(para_table)
        print(f"un/parsed: {unparsed}/{len(table)}")
        return table

    # class TargetExtractor

    @classmethod
    def match_id_and_targets_in_para(cls, para_text, paragraph_id, last_section_id):
        """

        """
        # print(f" IN last {last_section_id}")
        curly_re = re.compile("(.*){(.*)}(.*)")
        match_curly = curly_re.match(para_text)
        # targets = []
        subtable = []
        unparsed = 0
        max_para_text = 50
        if match_curly:
            curly_text = match_curly.group(2)
            curly_text = cls.add_missing_commas(curly_text)
            clause_parts = re.split('\s*[:;,]\s*', curly_text)
            for part in clause_parts:
                target_str = part.strip()
                if target_str == '':
                    continue
                target = cls.create_normalized_target(target_str)
                if len(target.unparsed_str) > 0:
                    unparsed += 1
                row = [paragraph_id, last_section_id,
                        target.raw, target.package, target.section, target.object, target.unparsed_str, para_text[:max_para_text]]
                subtable.append(row)
        return unparsed, subtable

    # class TargetExtractor

    def find_commonest_in_node_lists(self, table, node_name=None):

        if not node_name:
            raise ValueError(f"node names are none")
        node_col = self.column_dict.get(node_name)
        if not node_col:
            raise ValueError(f"node name '{node_name}' not in column_dict {self.column_dict.keys()}")
        node_dict = defaultdict(int)
        for row in table:
            node_dict[row[node_col]] += 1
        node_counter = Counter(node_dict)
        common_node = [n for n in node_counter.most_common() if n[1] > 1]
        return common_node


packages = ["WGI", "WG1", "WGII", "WG2", "WGIII", "WG3", "SRCCL", "SR1.5", "SR15", "SROCC"]
subpackages = ["Chapter", "SPM", "TS", "ES"]
objects = ["Table", "Figure", "CCBox"]
subsections = ["A", "B", "C", "D", "E", "F"]

package_re = "WGI+|WG[123]|SR(?:CCL|OCC|1\.?5)"
section_re = "Chapter|Anne(xe)?|SPM|SM|TS|ES|[Ss]ections?"
object_re = "[Ff]ig(ure)?|[Tt]ab(le)?|[Ff]ootnote|Box|CCBox|CSBox"
subsection_re = "^\d+$|^[A-F]$|^ES|([A-E]?\.?\d+(\.\d+)?(\.\d+)?)"
# subsubsection_re = "[1-9](?:\.[1-9]){0, 2}"


class LinkFactory:
    """"""
    class LinkNode:
        """filepath = stem/leaf_name and takes precedence over those"""
        def __init__(self, site=None, username=None, repository=None, branch=None,
                     stem=None, leaf_name=None, filepath=None):
            self.site = site
            self.username = username
            self.repository = repository
            self.branch = branch
            self.stem = stem
            self.leaf_name = leaf_name
            self.filepath = filepath

        def set_file_path(
              self,
              stem,
              leaf_name,
              filepath
        ):
            self.filepath = filepath if filepath else (stem + "/" + leaf_name) if stem and leaf_name else None

    #    class LinkFactory:

    def __init__(self):
        self.anchor = LinkFactory.LinkNode(site="https://raw.githubuser.com")
        self.target = LinkFactory.LinkNode(site="https://raw.githubuser.com")
        self.wg_dict = None

        self.link = None
        self.span_link = None

    #    class LinkFactory:

    @classmethod
    def create_factory(
        cls,
        anchor_site=None,
        anchor_username=None,
        anchor_repository=None,
        anchor_branch=None,
        anchor_stem=None,
        anchor_leaf_name=None,
        anchor_filepath=None,

        target_site=None,
        target_username=None,
        target_repository=None,
        target_branch=None,
        target_stem=None,
        target_leaf_name=None,
        target_filepath=None,

        wg_dict = None
    ):
        link_factory = LinkFactory()

        link_factory.anchor.site = anchor_site
        link_factory.anchor.username = anchor_username
        link_factory.anchor.repository = anchor_repository
        link_factory.anchor.branch = anchor_branch
        link_factory.anchor.set_file_path(anchor_stem,
                                          anchor_leaf_name,
                                          anchor_filepath)

        link_factory.target.site = target_site
        link_factory.target.username = target_username
        link_factory.target.repository = target_repository
        link_factory.target.branch = target_branch
        link_factory.target.set_file_path(target_stem,
                                          target_leaf_name,
                                          target_filepath)

        link_factory.wg_dict = wg_dict
        return link_factory

    #    class LinkFactory:

    # def create_ipcc_target_link(self, link, span_link):
    #     target_link = IPCCTargetLink(link, span_link)
    #     return target_link

    @classmethod
    def create_default_ipcc_link_factory(cls):
        anchor_username = target_username = "petermr"
        anchor_repository = target_repository = "semanticClimate"
        anchor_branch = target_branch = "main"
        anchor_stem = target_stem = "ipcc/ar6"
        target_leaf_name = "fulltext.annotations.id.html"
        wg_dict = {
            "WGI": "wg1",
            "wgi": "wg1",
            "WG2": "wg2",
            "wg2": "wg2",
            "WG3": "wg3",
            "wg3": "wg3",
        }
        link_factory = LinkFactory.create_factory(
            anchor_username=anchor_username,
            anchor_repository=anchor_repository,
            anchor_branch=anchor_branch,
            anchor_stem=anchor_stem,

            target_username=target_username,
            target_repository=target_repository,
            target_branch=target_branch,
            target_stem=target_stem,

            target_leaf_name=target_leaf_name,

            wg_dict=wg_dict
        )
        return link_factory

    #    class LinkFactory:

    def create_target_link(self, ipcc_id, anchor_span_link):
        target_link = IPCCTargetLink(ipcc_id, anchor_span_link)
        target_link.link_factory = self
        return target_link

    def create_github_url(self):
        github_url = HtmlLib.create_rawgithub_url(
            branch=self.anchor.branch,
            filepath=self.anchor.filepath,
            repository=self.anchor.repository,
            username=self.anchor.username
        )
        return github_url

