# https://stackoverflow.com/questions/19917492/how-can-i-use-a-python-script-in-the-command-line-without-cd-ing-to-its-director
import logging

from collections import Counter
import re
import json
import glob
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from nltk.tokenize import sent_tokenize
from lxml import etree as LXET
import sys
# import RAKE  # python RAKE
import tkinter as tk
# from rake_nltk import Rake
import cProfile
import argparse
from pathlib import Path

# from py4ami.ami_demos import AmiDemos
from py4ami.gutil import Gutil, ScrollingCheckboxList

from py4ami.ami_dict import AmiDictionaries
from py4ami.ami_project import AmiProjects
from py4ami.file_lib import AmiPath, PROJ, FileLib
from py4ami.text_lib import AmiSection
from py4ami.xml_lib import XmlLib, H_TD, RESULTS, DataTable

# logging.warning("loading search_lib.py")

# entry

WIKIDATA_ID = "wikidataID"
# add more as needed
NS_MAP = {'SPQ': 'http://www.w3.org/2005/sparql-results#'}
NS_URI = "SPQ:uri"
NS_LITERAL = "SPQ:literal"

SMART_STOP_LIST = "SmartStoplist.txt"


class AmiSearch:

    def __init__(self):
        # these are the main facets
        self.dictionaries = []
        self.patterns = []
        self.projects = []
        self.section_types = []
        self.matches_by_amidict = {}
        self.rake = None
        self.checked_values = []
        self.data_table = None


# working global variables
        self.cur_section_type = None
        self.cur_proj = None

#        self.word_counter = None
        self.debug = False
        self.do_search = True
        self.do_plot = True
        self.ami_projects = AmiProjects()
        self.use_rake = True  # change later

        self.param_dict = {
            "max_bars": 10,
            "wikidata_label_lang": "en",
            "debug_cnt": 10000,
            "max_files": 10000,
            "min_hits": 2,
            "require_wikidata": False,
            "ami_gui": None,
        }
#        self.max_bars = 10
        self.wikidata_label_lang = "en"

        # print every debug_cnt filenamwe
        self.debug_cnt = 10000
        # maximum files to search
        self.max_files = 10000
        self.min_hits = 2
        self.require_wikidata = False

        # look up how sections work
        self.ami_dictionaries = AmiDictionaries()
        self.ami_gui = None
        self.filter = True
        self.results_by_section = {}

    def make_plot(self, counter, dict_name):
        mpl.rcParams['font.family'] = 'Helvetica'
        commonest = counter.most_common()
        keys = [c[0] for c in commonest]
        values = [c[1] for c in commonest]
        plt.bar(keys[:self.max_bars], values[:self.max_bars], color='blue')
        plt.xticks(rotation=45, ha='right')  # this seems to work
        plt.title(self.make_title(dict_name))
        plt.show()

    def make_title(self, dict_name):
        ptit = self.cur_proj.dirx.split("/")[-1:][0]
        return ptit + ":   " + self.cur_section_type + ":   " + dict_name

    def use_dictionaries(self, args):
        if args is not None and len(args) > 0:
            for arg in args:
                self.add_dictionary(arg)
        else:
            # print dictionaries
            print("\n==========AMI DICTIONARIES========")
#            print("amidict keys: ", self.dict_)
            print("==================================\n")

    def add_dictionary(self, name):
        print("dict_name:", name)
        AmiSearch._append_facet(
            "dictionary", name, self.ami_dictionaries.dictionary_dict, self.dictionaries)

    # crude till we work this out
    def use_patterns(self, args):
        if args is not None:
            for arg in args:
                self.use_pattern(arg)

    def use_pattern(self, pattern, name=None):
        """ use either name and pattern or name='pattern' """
        regex = pattern
        if name is None and "=" in pattern:
            name = pattern.split("=", 0)
            regex = pattern.split("=", 2)
        print(name, "=", regex)
        self.patterns.append(SearchPattern(regex, name))

    def use_projects(self, args):
        print("projects", args)
        if args is None or len(args) == 0:
            print("=================", "\n",
                  "must give projects; here are some to test with, but they may need checking out")
            for key in AmiProjects().project_dict.keys():
                proj = AmiProjects().project_dict[key]
                print(key, "=>", proj.description)
            print("=================")
        else:
            for arg in args:
                self.add_project(arg)

    def add_project(self, name):
        AmiSearch._append_facet(
            "project", name, self.ami_projects.project_dict, self.projects)

    def use_filters(self, name):
        print("filters NYI")

    @staticmethod
    def _append_facet(label, name, dikt, dict_list):
        if name not in dikt:
            raise Exception("unknown name: " + name +
                            " in " + str(dikt.keys()))
        dict_list.append(dikt[name])

    def search_and_generate_section(self, file, filter=filter):
        section = AmiSection.get_section_with_words(file, filter=filter)
        total_hits_by_dict = {}
        self.matches_by_amidict, hits_by_dict = self.match_single_words_against_dictionaries(
            section.words)
        total_hits = 0
        self.list_hits(hits_by_dict, section)
        self.results_by_section[section.name] = hits_by_dict
        matches_by_amidict_multiple, hits_by_mwdict = self.match_multiple_words_against_dictionaries(
            section.text)
        self.list_hits(hits_by_mwdict, section)

        for key, value in matches_by_amidict_multiple.items():
            self.matches_by_amidict.setdefault(key, []).extend(value)
        matches_by_pattern = self.match_words_against_pattern(section.words)

        return self.matches_by_amidict, matches_by_pattern, section

    def list_hits(self, hits_by_dict, section):
        for dict_name in hits_by_dict.keys():
            hits = hits_by_dict[dict_name]
            if len(hits) > 0:
                # print("matches in section", section, "are: ", self.matches_by_amidict.keys(), hits_by_dict)
                self.add_hits_to_section_index(section.name, dict_name, hits)

            # total_hits += hits

    def add_hits_to_section_index(self, section_name, dict_name, hits):
        if len(hits) > 0:
            if section_name not in self.results_by_section:
                self.results_by_section[section_name] = {}
            if dict_name not in self.results_by_section[section_name]:
                self.results_by_section[section_name][dict_name] = []
            self.results_by_section[section_name][dict_name] += hits

    def match_single_words_against_dictionaries(self, words):
        """matches the set of words in a section against set of terms in a dictionary"""
        found = False
        matches_by_amidict = {}
        hits_by_dict = {}
        for dictionary in self.dictionaries:
            hits = dictionary.match(words)
            #            print("hits", len(hits))
            wid_hits = None
            if dictionary.entry_by_term is not None:
                wid_hits = self.annotate_hits_with_wikidata(dictionary, hits)
            matches_by_amidict[dictionary.name] = wid_hits
            hits_by_dict[dictionary.name] = hits
        return matches_by_amidict, hits_by_dict

    def match_multiple_words_against_dictionaries(self, text):
        # really crude - we concatenate words into a giant string with
        matches_by_multiple = {}
        found = False
        tokenized_sents = sent_tokenize(text)
#        print("token sents", tokenized_sents)
        hits_by_dict = {}
        for dictionary in self.dictionaries:
            hits = dictionary.match_multiple_word_terms_against_sentences(
                tokenized_sents)
#            wid_hits = self.annotate_hits_with_wikidata(dictionary, hits)
            matches_by_multiple[dictionary.name] = hits
            hits_by_dict[dictionary.name] = hits
        return matches_by_multiple, hits_by_dict

    def annotate_hits_with_wikidata(self, dictionary, hits):
        wid_hits = []
        for hit in hits:
            if hit in dictionary.entry_by_term:
                entry = dictionary.entry_by_term[hit]
                if self.require_wikidata and WIKIDATA_ID not in entry.attrib:
                    print("no wikidataID for ", hit, "in", dictionary.name)
                    continue
#                wikidata_id = entry.attrib[WIKIDATA_ID]
                label = hit
                if self.wikidata_label_lang in ['hi', 'ta', 'ur', 'fr', 'de']:
                    #                            self.xpath_search(entry)  # doesn't work
                    lang_label = self.search_by_xml_lang(entry)
                    if lang_label is not None:
                        label = lang_label
                wid_hits.append(label)
        return wid_hits

    def search_by_xml_lang(self, entry):
        label = None
        synonyms = entry.findall("synonym")
        for synonym in synonyms:
            if len(synonym.attrib) > 0:
                #                print("attribs", synonym.attrib)
                pass
            if XmlLib.XML_LANG in synonym.attrib:
                lang = synonym.attrib[XmlLib.XML_LANG]
#                print("lang", lang)
                if lang == self.wikidata_label_lang:
                    label = synonym.text
#                    print("FOUND", label_xml)
                    break
        return label

    def xpath_search(self, entry):
        """doesn't yet work"""
        lang_path = "synonym[" + XmlLib.XML_LANG + \
            "='" + self.wikidata_label_lang + "']"
        #                            print("LP", lang_path)
        lang_equivs = entry.xpath(
            'synonym[@xml:lang]', namespaces={'xml': XmlLib.XML_NS})
        lang_equivs = entry.findall(lang_path)
        if len(lang_equivs) > 0:
            lang_equiv = lang_equivs[0]

    def match_words_against_pattern(self, words):
        matches_by_pattern = {}
        found = False
        for pattern in self.patterns:
            hits = pattern.match(words)
            matches_by_pattern[pattern.name] = hits
        return matches_by_pattern

    def search_and_count(self, section_files):
        """searches sections with dictionaries and also makes word counts"""
        print("search and count", section_files)
        for dictionary in self.dictionaries:
            print("dictionary for search", dictionary.name)
        dictionary_counter_dict = self.create_counter_dict(self.dictionaries)
        pattern_counter_dict = self.create_counter_dict(self.patterns)

        all_lower_words = []
        sections = []
        for index, target_file in enumerate(section_files[:self.max_files]):
            if index % self.debug_cnt == 0:
                # eg <project_dir> /oil26/PMC5203915/sections/0_front/1_article-meta/19_abstract.xml
                print("collect words in path", target_file)
            matches_by_amidict, matches_by_pattern, section = self.search_and_generate_section(
                target_file)
            sections.append(section)
            all_lower_words += [w.lower() for w in section.words]
            self.add_matches_to_counter_dict(
                dictionary_counter_dict, matches_by_amidict)
            self.add_matches_to_counter_dict(
                pattern_counter_dict, matches_by_pattern)

        self.print_results_by_section()

        return dictionary_counter_dict, pattern_counter_dict, all_lower_words, sections

    def print_results_by_section(self):
        # ic("results by section", self.results_by_section)
        print("ROWS", len(self.results_by_section))
        for section in sorted(self.results_by_section.keys()):
            print("SECTION", section)
            hits_by_dictionary = self.results_by_section[section]
            count = 0
            for dictionary in hits_by_dictionary:
                hit_list = hits_by_dictionary[dictionary]
                count += len(hit_list)
            if count == 0:
                print("skipped empty row")
                continue
            row = self.data_table.make_row()
            self.data_table.append_contained_text(row, H_TD, section)

            for dictionary in hits_by_dictionary:
                self.add_hits_for_dictionary(
                    dictionary, hits_by_dictionary, row)

    def add_hits_for_dictionary(self, dictionary, hits_by_dictionary, row):
        hit_list = hits_by_dictionary[dictionary]
        print(hit_list)
        hits = set(hit_list)
        text = ""
        for h in hits:
            text += h + " | "
        self.data_table.append_contained_text(row, H_TD, text)

    def create_counter_dict(self, search_tools):
        counter_dict = {}
        for tool in search_tools:
            counter_dict[tool.name] = Counter()
        return counter_dict

    def add_matches_to_counter_dict(self, counter_dict, matches_by_amidict):
        for amidict in matches_by_amidict:
            matches = matches_by_amidict[amidict]
            if len(matches) > 0:
                for match in matches:
                    counter_dict[amidict][match] += 1

    def use_sections(self, sections):
        if sections is None or len(sections) == 0:
            self.section_help()
        else:

            try:
                AmiSection.check_sections(sections)
                self.section_types = sections
            except Exception as ex:
                print("\n=============cannot find section============\n", ex)
                self.section_help()
                print("\n===========================")
        return

    def section_help(self):
        print("sections to be used; ALL uses whole document (Not yet tested)")
        print("\n========SECTIONS===========")
        print(AmiSection.SECTION_LIST)
        print("===========================\n")

    def run_search(self):
        for proj in self.projects:
            print("***** project", proj.dirx)
            self.cur_proj = proj
            if len(self.section_types) > 0:
                for section_type in self.section_types:
                    self.glob_for_section_files(proj, section_type)
                    sections = self.section_make_data_table_counter_and_plot(
                        section_type)
                    self.write_data_table(proj.dirx, section_type)
                    # if self.use_rake:
                    #     self.analyze_all_words_with_Rake(sections)

            # if self.use_rake:   # uses fulltext.txt
            #     files = self.glob_fulltext(proj)
            #     print("fulltext.txt", files)
            #     text = ""
            #     for file in files:
            #         with open(file, "r") as f:
            #             text += f.read()
            #     self.analyze_text_with_Rake(text)
            continue

    def write_data_table(self, project_dir, section_type):

        # lower case section name
        result_section_dir = os.path.join(
            project_dir, RESULTS, section_type.lower())
        # write_full_data_tables(self.data_table, result_section_dir)
        print("ERROR", "full_data_tables not linked in")

    def glob_fulltext(self, proj):
        globstr = os.path.join(proj.dirx, "*/fulltext*.txt")
        files = glob.glob(globstr, recursive=False)
        return files

    def glob_for_section_files(self, proj, section_type):
        self.cur_section_type = section_type
        templates = AmiPath.create_ami_path_from_templates(
            section_type, {PROJ: proj.dirx})
        self.section_files = templates.get_globbed_files()
        print("***** section_files", section_type, len(self.section_files))

    def section_make_data_table_counter_and_plot(self, section_type):
        self.create_data_table(section_type)
        counter_by_tool, pattern_dict, all_words, sections = self.search_and_count(
            self.section_files)
        self.plot_tool_hits(counter_by_tool)
        self.plot_tool_hits(pattern_dict)
        # _, _, all_words, sections = self.search_and_count(self.section_files)
#        print(all_words)
        counter = Counter(all_words)
        self.plot_and_make_dictionary(counter, "word count")

        return sections,

    def create_data_table(self, section_type):
        self.data_table = DataTable(section_type)
        column_heads = ["sections"]
        for dictionary in self.dictionaries:
            column_heads.append(dictionary.name)
        self.data_table.add_column_heads(column_heads)
        print("TAB", LXET.tostring(self.data_table.html))

    def analyze_all_words_with_Rake(self, sections):
        text = ""
        print("sections", len(sections))
        if len(sections) == 1:
            if type(sections[0]) == list:
                for sect in sections[0]:
                    text += sect.text
            else:
                print("BUG BUG ")
        else:
            for section in sections:
                if type(section) == list:
                    print("len sect", len(section))
                    print("BUG", "section should not be List")
                else:
                    text += section.text
            text = self.remove_line_ends(text)

        self.analyze_text_with_Rake(text)

    def remove_line_ends(self, text):
        # join hyphenated words at end of line
        text = text.replace("-\n", "")
        # change line ends to " " ; will break up formatting
        text = text.replace("\n", " ")
        return text

    # def analyze_text_with_Rake(self, text):
    #     text = self.remove_line_ends(text)
    #     self.rake = AmiRake(self)
    #     phrases = self.rake.analyze_text_with_RAKE(text)

    def plot_tool_hits(self, counter_by_tool):
        for tool in counter_by_tool:
            counter = counter_by_tool[tool]
            self.plot_and_make_dictionary(counter, tool)

    def plot_and_make_dictionary(self, counter, tool):
        min_counter = Counter(
            {k: c for k, c in counter.items() if c >= self.min_hits})
        if self.do_plot:
            self.make_plot(min_counter, tool)
        print("tool:", tool, "\n", min_counter.most_common())
        self.make_dictionary(tool, min_counter)

    def make_dictionary(self, tool, counter):
        print("MOVE make_dictionary")
        make_dictionary = False
        if make_dictionary:
            print("<dictionary title='"+tool+"'>")
            for k, v in counter.items():
                if v > self.min_hits:
                    print("  <entry term=`"+k.lower()+"'/>")
            print("</dictionary>")

        outfile = self.create_word_count_file(tool)
        """ TODO
        with open(outfile, "w") as f:
            print("<dictionary title='" + tool + "'>")
            for k, v in hit_counter.items():
                if v > self.min_hits:
                    print("  <entry term=`" + k.lower() + "'/>")
            print("</dictionary>")
        """

    def create_word_count_file(self, tool):
        pass

    def run_args(self):
        local_test = False  # interactive debug
        parser = create_arg_parser()
        args = parser.parse_args()
        print("args", args)
        print("cmd", "sys.argv", sys.argv)
        print("interpreted from cmd", "arg.demo", args.demo)
        #    local_test = True
        if args.debug == "config":
            ami_runs = AmiRunner()
            ami_runs.read_config(AmiSearch.DEMOS_JSON)
        elif len(sys.argv) == 1:
            print(parser.print_help(sys.stderr))
        elif args.demo is not None:
            print("DEMOS SKIPPED")
#            AmiDemos.run_demos(args.demo)
        else:
            #            ami_search = AmiSearch()
            #            copy_args_to_ami_search(args, ami_search)
            #            if ami_search.do_search:
            #                ami_search.run_search()
            copy_args_to_ami_search(args, self)
            if self.do_search:
                self.run_search()

        # this profiles it
        #    test_profile1()
        print("finished search")

    def run_search_from_gui(self, ami_gui):
        self.min_hits = 1
        self.max_bars = 25
        self.ami_gui = ami_gui

        sections = Gutil.get_selections_from_listbox(ami_gui.sections_listbox)
        print("sections", sections)
        self.use_sections(sections)

        dictionaries = Gutil.get_selections_from_listbox(
            ami_gui.dictionary_names_listbox)
        print("dictionaries", dictionaries)
        self.use_dictionaries(dictionaries)

        projects = Gutil.get_selections_from_listbox(
            ami_gui.project_names_listbox)
        print("projects", projects)
        self.use_projects(projects)

        self.run_search()

        if self.rake is not None:
            phrases = self.rake.phrases
            ami_gui.main_text_display.delete("1.0", tk.END)
            for phrase in phrases:
                print(">>", phrase)
                ami_gui.main_text_display.insert(tk.END, phrase+"\n")

    def save_rake_keywords(self, keywords):

        text = ""
        for line in keywords:
            text += line+"\n"
        dir = os.path.join(self.cur_proj.dirx, "results", "rake")
        if not os.path.exists(dir):
            os.makedirs(dir)
        file = os.path.join(dir, "keywords.txt")
        with open(file, "w", encoding="utf-8") as f:
            f.write(text)
            print(f"wrote {file}")


class AmiRun:

    SECTIONS = "sections"
    DICTIONARIES = "dictionaries"
    PROJECTS = "projects"
    PATTERNS = "patterns"
    DEFAULTS = "defaults"

    def __init__(self, params, ami_runner):
        print("AMIRUNNER", dir(ami_runner))

        self.params = params
        self.sections = self._copy_params(__class__.SECTIONS)
        self.ami_sections = AmiSection()
        self.dictionaries = self._copy_params(__class__.DICTIONARIES)
        self.ami_dictionaries = AmiDictionaries()
        self.projects = self._copy_params(__class__.PROJECTS)
        self.ami_projects = AmiProjects()
        self.patterns = self._copy_params(__class__.PATTERNS)
# copying defaults to be partially overridden
        self.defalts = ami_runner.resources[__class__.DEFAULTS]
        self.ami_runner = ami_runner

        print("defaults", self.defalts)
        print("sections", self.sections)
        print("dictionaries", self.dictionaries)
        print("projects", self.projects)
        print("patterns", self.patterns)

        return

    def _copy_params(self, type):
        return self.params[type] if type in self.params else []

    def resolve_refs(self):

        for section in self.sections:
            if section not in self.ami_sections.SECTION_LIST:
                print("sectionsx ", section, "not in",
                      self.ami_sections.SECTION_LIST)

        for dictionary in self.dictionaries:
            if dictionary not in self.ami_dictionaries.dictionary_dict:
                print("Cannot find dictionary:", dictionary,
                      "\n", self.ami_dictionaries.dictionary_dict)

        for defalt in self.defalts.items():
            print("def", defalt)
            self.__setattr__(defalt[0], defalt[1])
        print("attrs", dir(self))

        # check section_names


class AmiRunner:

    RESOURCES = "resources"
    PROJECTS = "projects"
    CLASSES = "classes"
    PATTERNS = "patterns"
    DEFAULTS = "defaults"
    DEMOS = "demos"

    def __init__(self):
        self.runs = {}
        self.ami_dicts = AmiDictionaries()

    def read_config(self, file):
        print("reading JSON", file)
        with open(file, "r") as json_file:
            data = json.load(json_file)

        self.resources = data[__class__.RESOURCES]
        print("RES keys", self.resources.keys())
        self.classes = self.resources[__class__.CLASSES]
        self.projects = self.resources[__class__.PROJECTS]
        self.patterns = self.resources[__class__.PATTERNS]
        self.defalts = self.resources[__class__.DEFAULTS]
        self.demos = data[__class__.DEMOS]

        print("resources", self.resources)
        print("classes", self.classes)
        print("projects", self.projects)
        print("patterns", self.patterns)
        print("defaults", self.defalts)
        print("demos", self.demos)

        for key, val in self.demos.items():
            print("======"+key+"======")
            ami_run = AmiRun(val, self)
            self.runs[key] = ami_run
            ami_run.resolve_refs()
            print("===================")

        print("json", data)


class SearchPattern:

    """ holds a regex or other pattern constraint (e.g. isnumeric) """
    REGEX = "_REGEX"

    _ALL = "_ALL"
    ALL_CAPS = "_ALLCAPS"
    NUMBER = "_NUMBER"
    SPECIES = "_SPECIES"
    GENE = "_GENE"
    PATTERNS = [
        _ALL,
        ALL_CAPS,
        #        GENE,
        NUMBER,
        #        SPECIES,
    ]

    def __init__(self, value, name=None):
        if value in SearchPattern.PATTERNS:
            self.type = value
            self.regex = None
            self.name = value if name is None else value
        else:
            self.type = SearchPattern.REGEX
            self.regex = re.compile(value)
            self.name = name if name is not None else "regex:"+value
            print("PATT: ", name, value)

    def match(self, words):
        matched_words = []
        for word in words:
            matched = False
            if self.regex:
                matched = self.regex.match(word)
            elif SearchPattern._ALL == self.type:
                matched = True      # pass everything
            elif SearchPattern.ALL_CAPS == self.type:
                matched = str.isupper(word)
            elif SearchPattern.NUMBER == self.type:
                matched = str.isnumeric(word)
            else:
                pass
            if matched:
                matched_words.append(word)

        return matched_words


# class AmiRake:
#     def __init__(self, ami_search=None):
#         self.min_len = 2
#         self.max_len = 6
#         self.phrases = []
#         self.phrases_with_scores = []
#         self.ami_search = ami_search
#         self.counter = None
#         # method 1 is slow but gives useful phrases
#         self.method = 1
#         # method 2 favours equation components but is a lot faster
# #        self.method = 2
#         self.checkbox_results = []
#
#     def analyze_text_with_RAKE(self, text):
#
#         self.counter = Counter()
#         keywords = self.use_rake1(
#             text) if self.method == 1 else self.use_rake2(text)
#
# #        self.make_toplevel_phraselist(self.ami_search.ami_gui, keywords)
#         text = text.lower()
#         text_counter = Counter()
#         for keyword in keywords:
#             matches_in_text = len(text.split(keyword)) - 1
#             if matches_in_text > 1:
#                 if all(x.isalpha() or x.isspace() or x == '-' for x in keyword):
#                     text_counter[keyword] = matches_in_text
#         phrases = [item[0] for item in text_counter.most_common()]
#         self.make_toplevel_phraselist(self.ami_search.ami_gui, phrases)
#
#     def make_toplevel_phraselist(self, master, phrases):
#
#         toplevel = tk.Toplevel(master)
#         toplevel.title("RAKE phraselist")
#         if phrases is None or len(phrases) == 0:
#             print("No phrases")
#         else:
#             results = []
#             scl = ScrollingCheckboxList(toplevel, receiver=self)
#             scl.pack(side="top", fill="both", expand=True)
#             scl.add_string_values(phrases)
#
#     def use_rake1(self, text):
#         stop_dir = Path(FileLib.get_pyami_resources(), SMART_STOP_LIST)
#         rake_object = RAKE.Rake(stop_dir)
#         weighted_keywords = self.sort_tuple(rake_object.run(text))  # [-10:]
#         weighted_keywords.reverse()
# #        print("keywords1", weighted_keywords)
#         keywords = self.create_keywords1(weighted_keywords)
#         return keywords
#
#     def use_rake2(self, text):
#         rake = Rake(min_length=self.min_len, max_length=self.max_len)
#         weighted_keywords = rake.extract_keywords_from_text(text)
#         print("weighted_keywords", weighted_keywords)
#         self.phrases = rake.get_ranked_phrases()  # [0:100]
#         # [0:100]
#         self.phrases_with_scores = rake.get_ranked_phrases_with_scores()
#         return self.phrases  # , self.phrases_with_scores
#
#     def create_keywords1(self, weighted_keywords):
#         keywords = []
#         for weighted_keyword in weighted_keywords:
#             keyword = weighted_keyword[0]
#             ll = len(keyword.split(" "))
#             if self.min_len <= ll <= self.max_len:
#                 self.counter[keyword] = int(weighted_keyword[1])
#                 keywords.append(keyword)
#         return keywords
#
#     def sort_tuple(self, tup):
#         """ sort
#         :reverse: None sort in ascending order
#         uses second elements of sublist as sort key
#         """
#         tup.sort(key=lambda x: x[1])
#         return tup
#
#     def receive_checked_values(self, values):
#         self.checked_values = values
#         print("V", len(values), values)
#         self.ami_search.save_rake_keywords(values)
#

def test_profile():
    """Python profiler"""
    print("profile")
    cProfile.run("[x for x in range(1500)]")


def test_profile1():
    """Python profiler"""
    print("profile1")
    cProfile.run("AmiSearch.test_sect_dicts()")


def main():
    """ debugging """
    pass
    # test_search()


def create_arg_parser():
    parser = argparse.ArgumentParser(
        description='Search sections with dictionaries and patterns')
    """
    """
    parser.add_argument('-d', '--dict', nargs="*",  # default=[AmiDictionaries.COUNTRY],
                        help='dictionaries to search with, empty gives list')
    parser.add_argument('-s', '--sect', nargs="*",  # default=[AmiSection.INTRO, AmiSection.RESULTS],
                        help='sections to search; empty gives all')
    parser.add_argument('-p', '--proj', nargs="*",
                        help='projects to search; empty will give list')
    parser.add_argument('--patt', nargs="+",
                        help='patterns to search with; regex may need quoting')
    parser.add_argument('--demo', nargs="*",
                        help='simple demos (NYI). empty gives list. May need downloading corpora')
    parser.add_argument('-l', '--loglevel', default="foo",
                        help='debug level (NYI)')
    parser.add_argument('--plot', action="store_false",
                        help='plot params (NYI)')
    parser.add_argument('--nosearch', action="store_true",
                        help='search (NYI)')
    parser.add_argument('--maxbars', nargs="?", type=int, default=25,
                        help='max bars on plot (NYI)')
    parser.add_argument('--languages', nargs="+", default=["en"],
                        help='languages (NYI)')
    parser.add_argument('--debug', nargs="+",
                        help='debugging commands , numbers, (not formalised)')
    return parser


def copy_args_to_ami_search(args, ami_search):#
    # print_args(args)
    # TODO dict on keywords
    ami_search.use_sections(args.sect)
    ami_search.use_dictionaries(args.dict)
    ami_search.use_projects(args.proj)
    ami_search.use_patterns(args.patt)
    if args.maxbars:
        ami_search.max_bars = args.maxbars
    if args.languages:
        ami_search.languages = args.languages
    for k, v in vars(args).items():
        #        print("k, v", k, "=", v)
        pass
    return ami_search


def print_args(args):
    print("commandline args")
    print("dicts", args.dict, type(args.dict))
    print("sects", args.sect, type(args.sect))
    print("projs", args.proj, type(args.proj))
    print("patterns", args.patt, type(args.patt))
    print("args>", args)


if __name__ == "__main__":
    print("running search main")
    main()
else:

    #    print("running search main anyway")
    #    main()
    pass

"""
https://gist.github.com/benhoyt/dfafeab26d7c02a52ed17b6229f0cb52
"""
"""https://stackoverflow.com/questions/22052532/matplotlib-python-clickable-points"""
