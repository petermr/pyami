import argparse
import tkinter as tk
import tkinter.ttk as ttk
from enum import Enum
from tkinter import messagebox
from tkinter import scrolledtext
from PIL import ImageTk, Image
import logging
import os
from xml.etree import ElementTree as ET
from tkinter import TOP, BOTTOM, LEFT
from pathlib import Path
from urllib.request import urlopen
import tkinterhtml as th
from io import BytesIO
from tkinter import filedialog as fd

# local
from py4ami.gutil import AmiTree, Gutil, CreateToolTip
from py4ami.gutil import Gutil as gu
from py4ami.search_lib import AmiSearch, AmiSection, AmiDictionaries, AmiProjects
from py4ami.xml_lib import XmlLib
from py4ami.wikimedia import WikidataBrowser
from py4ami.util import AbstractArgs

PYGETPAPERS = "pygetpapers"

DICTIONARY_HOME = "/Users/pm286/dictionary"
CEV_DICTIONARY_HOME = "/Users/pm286/projects/CEVOpen/dictionary"

XML_FLAG = "xml"
NOEXEC_FLAG = "noexec"
PDF_FLAG = "pdf"
CSV_FLAG = "csv"
SUPP_FLAG = "supp"
HTML_FLAG = "html"
PDFBOX_FLAG = "pdfbox"

TOTAL_HITS_ARE = "Total Hits are"
WROTE_XML = "Wrote xml"

# args
class AmiGuiArgsEnum(Enum):
    DICT = "dict"
    RUN = "run"

    def __str__(self):
        return self.value

# select by typing
# https://stackoverflow.com/questions/47839813/python-tkinter-autocomplete-combobox-with-like-search

def button1(event):
    """
    :param event:
    """

    print("button1", event)
    print(dir(event))
    tup = event.widget.curselection
    print("tup", tup, type(tup),)
    if len(tup) > 0:
        print(tup[0], event.widget.get(tup[0]))

class GUIArgs(AbstractArgs):
    """Parse args to run GUI"""

    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()
        self.dict = None
        self.run = None
        self.arg_dict = None

    def add_arguments(self):
        if self.parser is None:
            self.parser = argparse.ArgumentParser()
        """adds arguments to a parser or subparser"""
        self.parser.description = 'HTML editing analysing annotation'
        self.parser.add_argument(f"--{AmiGuiArgsEnum.DICT}", nargs="+",
                                 help="dictionary/ies to load (NYI)")
        self.parser.add_argument(f"--{AmiGuiArgsEnum.RUN}", action="store_true",
                                 help="run ami_gui")
        self.parser.epilog = "==============="

    """python -m py4ami.pyamix GUI --foobar
     """

    def read_arg_dict(self):
        logging.debug(f"read argdict {self.arg_dict}")
        self.dict = self.arg_dict.get(AmiGuiArgsEnum.DICT)
        self.run = self.arg_dict.get(AmiGuiArgsEnum.RUN)


    # class GUIArgs:
    def process_args(self):
        """runs parsed args
        :return:
        """

        logging.debug(f"====process_args==== {self.arg_dict}")
        if self.arg_dict:
            self.read_arg_dict()
        if not self.arg_dict:
            print(f"no arg_dict given, no action")
            return

        self.run = self.arg_dict.get(AmiGuiArgsEnum.RUN)

        if self.run:
            run_gui()

    # class AmiDictArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[AmiGuiArgsEnum.DICT] = None
        arg_dict[AmiGuiArgsEnum.RUN] = False
        return arg_dict

    @property
    def module_stem(self):
        """name of module"""
        return Path(__file__).stem

    def do_foobar(self):
        """uses dictionary to annotate words and phrases in HTML file"""
        from py4ami.ami_dict import AmiDictionary  # horrible
        logging.info("dummy foobar")

class AmiGui(tk.Frame):
    """ """

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.max_max_hits = 90
        self.selected_boxes = []
        self.current_project = None
        self.ami_tree = None
        self.treeview = None
        self.main_display_frame = None
        self.dashboard = None
        self.label = None
        self.show_html_frame = False
        self.dictionary_content_notebook = None
        self.assets = Path(Path(__file__).parent.parent, "assets")
        self.main_display_frame = None
        self.main_text_display = None
        self.label_display_var = None
        self.label_display = None
        self.html_frame = None
        self.xml_box = None
        self.xml_var = None
        self.pdf_box = None
        self.pdf_var = None
        self.supp_box = None
        self.supp_var = None
        self.noexec_box = None
        self.noexec_var = None
        self.csv_box = None
        self.csv_var = None
        self.html_box = None
        self.html_var = None
        self.pdfbox_box = None
        self.pdfbox_var = None
        self.ami_section_dict = None

        self.new_project_name_var = None
        self.new_project_name_entry = None
        self.new_project_desc_var = None
        self.new_project_desc_entry = None

        self.pack()
        self.current_ami_projects = AmiProjects()
        self.create_all_widgets(root)
#        self.menu_stuff()

    def create_all_widgets(self, master):
        """ Main entry

        :param master: parent frame

        """
        self.create_display_frame(master)
        self.create_dashboard(master)

    def main_text_display_button1(self, event):
        """

        :param event:

        """
        # print("Main button 1", event)
        pass

    def main_text_display_selected(self, event):
        """

        :param event:

        """
        # print("Main selected", event, event.widget.selection_get())
        pass

    def process_selection(self, event):
        """

        :param event:

        """
        text = self.get_main_text_on_release(event)
        if text:
            self.query_wikidata(text)

    def get_main_text_on_release(self, event):
        """

        :param event:

        """
        text = event.widget.selection_get() if event.widget.tag_ranges("sel") else None
        return text

    def create_display_frame(self, master):
        """

        :param master:

        """
        from py4ami.file_lib import FileLib

        self.main_display_frame = tk.Frame(master)
        self.main_display_frame.pack(side=tk.RIGHT)

        self.main_text_display = scrolledtext.ScrolledText(
            self.main_display_frame, font="Arial, 18", width=60, height=10)
        self.main_text_display.insert(tk.END, "text_display")
        self.main_text_display.pack(side=tk.BOTTOM, expand=True)
        self.main_text_display.bind(
            "<Button-1>", self.main_text_display_button1)
        self.main_text_display.bind(
            "<<Selection>>", self.main_text_display_selected)  # dummy
        self.main_text_display.bind(
            "<ButtonRelease>", self.process_selection)  # ACTIVE -> wikidata

        self.label_display_var = tk.StringVar(value="label_xml text")
        self.label_display = tk.Label(
            self.main_display_frame, textvariable=self.label_display_var)

        image_path = FileLib.create_absolute_name(
            os.path.join(self.assets, "purple_ocimum_basilicum.png"))
        if not os.path.exists(image_path):
            print(f"Cannot find purple basil: {image_path}")
        else:
            self.main_image_display = self.create_image_label(image_path)
            self.main_image_display.pack()

        url = "path://" + \
            FileLib.create_absolute_name(os.path.join("test", "index.html"))
        if self.show_html_frame:
            self.display_in_html_frame(url)

        file = FileLib.create_absolute_name(os.path.join(
            "diagrams", "luke", "papers20210121", "physrevb.94.125203_1_", "fulltext.pdf"))
        if False:
            self.open_pdf(file, self.main_text_display, page_num=0)

    def display_in_html_frame(self, url):
        try:
            self.html_frame = self.create_html_view(
                self.main_display_frame, url)
            if self.html_frame:
                self.html_frame.pack()
        except Exception as e:
            s = f"cannot load url {url}{e}"
            raise Exception(s)

    def open_pdf(self, file, text, page_num=0):
        """

        :param file:
        :param text:
        :param page_num:  (Default value = 0)

        """
        import PyPDF2
        pdf_file = PyPDF2.PdfFileReader(file)
        page = pdf_file.getPage(page_num)
        content = page.extractText()
        text.insert(1.0, content)

    def create_html_view(self, frame, htmlfile):
        """

        :param frame:
        :param htmlfile:

        """
        a = urlopen(htmlfile)
        bytez = a.read()
        content = bytez.decode()
        html = th.HtmlFrame(frame)
        html.set_content(content)
        return html

    def view_main_text(self, file):
        """

        :param file:

        """
        if file.endswith(".xml"):
            # not yet working
            # self.view_main_xml_file(path)
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                self.view_main_text_content(content)
        else:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                self.view_main_text_content(content)

    def view_main_text_content(self, content):
        """

        :param content:

        """
        self.main_text_display.delete("1.0", tk.END)
        self.main_text_display.insert(tk.END, content)

    def view_main_xml_file(self, file):
        """

        :param file:

        """
        self.xml_root = XmlLib.parse_xml_file_to_root(file)
        for child in self.xml_root:
            pass

    def create_image_label(self, image_path):
        """

        :param image_path:

        """
        frame_height = 400
        frame_width = 800
        frame_aspect_ratio = frame_width / frame_height
        image = Image.open(image_path)
        w, h = image.size
        aspect_ratio = w / h
        width = frame_width if aspect_ratio > frame_aspect_ratio else int(
            frame_height * aspect_ratio)
        height = int(
            frame_width / aspect_ratio) if aspect_ratio > frame_aspect_ratio else frame_height
        image = image.resize((width, height), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(image)

        if self.label is None:
            self.label = ttk.Label(self.main_display_frame)
        self.set_image_and_persist(img)
        return self.label

    def set_image_and_persist(self, img):
        """

        :param img:

        """
        self.label.configure(image=img)
        self.label.image = img  # needed to avoid garbage collectiom

    def create_dashboard(self, master):
        """

        :param master:

        """
        self.dashboard = tk.Frame(master)
        self.dashboard.pack(side=tk.LEFT)
        self.make_ami_widgets(self.dashboard)

    def make_ami_widgets(self, master):
        """

        :param master:

        """
        pg_frame = tk.Frame(master,
                            highlightbackground="gray",
                            highlightthickness=1)
        pg_frame.pack(side=TOP)

        self.make_cproject_frame(pg_frame, tk.TOP)
        self.make_dictionary_names_box(pg_frame)
        self.make_pygetpapers_query_frame(pg_frame, tk.TOP)
        self.make_ami_project(pg_frame)
        self.make_section_frame(pg_frame)
        self.make_ami_search(pg_frame)
        self.make_quit(pg_frame)
        return pg_frame

    def make_section_frame(self, master):
        """

        :param master:

        """
        section_frame, title_var = Gutil.make_frame_with_hide(master,
                                                              title="Sections",
                                                              tooltip="sections to be searched",
                                                              )
        section_frame.pack()

        self.sections_listbox = self.create_generic_listbox(
            AmiSection.SECTION_LIST1,
            #            AmiSection.SECTION_LIST,
            master=section_frame,
        )
        self.sections_listbox.pack(side=BOTTOM)

    def make_dictionary_names_box(self, master):
        """dictionary_dict = {
            "country": (os.path.join(DICTIONARY_HOME, "openVirus20210120", "country", "country.xml"),
                        "ISO countries from wikidata"),
            "ethics": (os.path.join(DICTIONARY_HOME, "ami3", "ethics.xml"),
                       "Ethics section terminology"),
            "invasive": (os.path.join(CEV_DICTIONARY_HOME, "Invasive_species", "invasive_plant.xml"),
                         "Invasive plant species from GISD"),
            "plant_part": (os.path.join(CEV_DICTIONARY_HOME, "eoPlantPart", "eoplant_part.xml"),
                           "Plant parts from EO literature"),
            "parkinsons": (os.path.join(DICTIONARY_HOME, "ami3", "parkinsons.xml"),
                           "Terms related to Parkinson's disease"),
        }

        :param master:

        """
        dictionary_frame, _ = Gutil.make_frame_with_hide(master,
                                                         title="Dictionaries",
                                                         highlightthickness="10",
                                                         tooltip="contains dictionary content boxes",
                                                         )
        dictionary_frame.pack(side=LEFT)

        ami_dictionaries = AmiDictionaries()
        dictionary_dict = ami_dictionaries.dictionary_dict
        self.dcb_frame = self.make_dictionary_content_boxes_frame(
            dictionary_frame)
        self.dictionary_names_listbox = self.create_generic_listbox(
            dictionary_dict.keys(),
            master=dictionary_frame,
            button_text="display dictionary content",
            command=lambda: self.make_dictionary_content_boxes(
                self.dcb_frame,
                dictionary_dict,
                Gutil.get_selections_from_listbox(
                    self.dictionary_names_listbox)
            )
        )

        dictionary_names = dictionary_dict.keys()
        self.xml_box = None
        self.xml_var = None
        self.pdf_box = None
        self.pdf_var = None
        self.supp_box = None
        self.supp_var = None
        self.noexec_box = None
        self.noexec_var = None
        self.csv_box = None
        self.csv_var = None
        self.html_box = None
        self.html_var = None
        self.pdfbox_box = None
        self.pdfbox_var = None
        self.pygetpapers_flags = {
            XML_FLAG: {
                Gutil.CBOX_BOX: self.xml_box,
                Gutil.CBOX_VAR: self.xml_var,
                Gutil.CBOX_TEXT: "XML",
                Gutil.CBOX_ON: Gutil.ONVAL,
                Gutil.CBOX_OFF: Gutil.OFFVAL,
                Gutil.CBOX_DEFAULT: Gutil.ONVAL,
                Gutil.CBOX_BRIEF: "-x",
                Gutil.CBOX_FULL: "--xml",
                Gutil.CBOX_TOOLTIP: "output XML",
            },
            PDF_FLAG: {
                Gutil.CBOX_BOX: self.pdf_box,
                Gutil.CBOX_VAR: self.pdf_var,
                Gutil.CBOX_TEXT: "PDF",
                Gutil.CBOX_ON: Gutil.ONVAL,
                Gutil.CBOX_OFF: Gutil.OFFVAL,
                Gutil.CBOX_DEFAULT: Gutil.OFFVAL,
                Gutil.CBOX_BRIEF: "-p",
                Gutil.CBOX_FULL: "--pdf",
                Gutil.CBOX_TOOLTIP: "output PDF",
            },
            SUPP_FLAG: {
                Gutil.CBOX_BOX: self.supp_box,
                Gutil.CBOX_VAR: self.supp_var,
                Gutil.CBOX_TEXT: "SUPP",
                Gutil.CBOX_ON: Gutil.ONVAL,
                Gutil.CBOX_OFF: Gutil.OFFVAL,
                Gutil.CBOX_DEFAULT: Gutil.OFFVAL,
                Gutil.CBOX_BRIEF: "-s",
                Gutil.CBOX_FULL: "--supp",
                Gutil.CBOX_TOOLTIP: "output Supplemental data (often absent)",
            },
            NOEXEC_FLAG: {
                Gutil.CBOX_BOX: self.noexec_box,
                Gutil.CBOX_VAR: self.noexec_var,
                Gutil.CBOX_TEXT: "-n",
                Gutil.CBOX_ON: Gutil.ONVAL,
                Gutil.CBOX_OFF: Gutil.OFFVAL,
                Gutil.CBOX_DEFAULT: Gutil.OFFVAL,
                Gutil.CBOX_BRIEF: "-n",
                Gutil.CBOX_FULL: "--no download",
                Gutil.CBOX_TOOLTIP: "if checked do not download ",
            },
            CSV_FLAG: {
                Gutil.CBOX_BOX: self.csv_box,
                Gutil.CBOX_VAR: self.csv_var,
                Gutil.CBOX_TEXT: "CSV",
                Gutil.CBOX_ON: Gutil.ONVAL,
                Gutil.CBOX_OFF: Gutil.OFFVAL,
                Gutil.CBOX_DEFAULT: Gutil.OFFVAL,
                Gutil.CBOX_BRIEF: "-c",
                Gutil.CBOX_FULL: "--makecsv",
                Gutil.CBOX_TOOLTIP: "output metadata as CSV",
            },
            HTML_FLAG: {
                Gutil.CBOX_BOX: self.html_box,
                Gutil.CBOX_VAR: self.html_var,
                Gutil.CBOX_TEXT: "HTML",
                Gutil.CBOX_ON: Gutil.ONVAL,
                Gutil.CBOX_OFF: Gutil.OFFVAL,
                Gutil.CBOX_DEFAULT: Gutil.OFFVAL,
                Gutil.CBOX_FULL: "--makehtml",
                Gutil.CBOX_TOOLTIP: "output metadata/abstract as HTML",
            },
        }
        self.flags_keys = self.pygetpapers_flags.keys()

    def make_pygetpapers_query_frame(self, master, TOP):
        """

        :param master:
        :param TOP:

        """

        pygetpapers_frame, title_var = Gutil.make_frame_with_hide(master,
                                                                  title="Pygetpapers",
                                                                  tooltip="build query from dictionaries, "
                                                                          "flags and text; and RUN",
                                                                  )

        self.download_save, _ = Gutil.make_frame(pygetpapers_frame,
                                                 title="project",
                                                 #                                           tooltip="build query from dictionaries, flags and text; and RUN",
                                                 )
        self.download_save.pack()

        sub_frame = self.download_save

        self.create_run_button(sub_frame)
        button = self.create_make_project_button(sub_frame)
        self.make_getpapers_args(pygetpapers_frame)
        # TODO MOVE
        # self.dcb_frame = self.make_dictionary_content_boxes_frame(pygetpapers_frame)
        self.entry_text = Gutil.make_entry_box(pygetpapers_frame, text="query")

        return pygetpapers_frame, title_var

    def make_ami_project(self, master):
        """

        :param master:

        """
        ami_project_frame, title_var = Gutil.make_frame_with_hide(master,
                                                                  title="AMI",
                                                                  tooltip="process AMI project",
                                                                  )
        ami_project_frame.pack()

        section_box = None
        section_var = None
        self.ami_section_dict = {
            Gutil.CBOX_BOX: section_box,
            Gutil.CBOX_VAR: section_var,
            Gutil.CBOX_TEXT: "make sections",
            Gutil.CBOX_ON: Gutil.ONVAL,
            Gutil.CBOX_OFF: Gutil.OFFVAL,
            Gutil.CBOX_DEFAULT: Gutil.ONVAL,  # default is ON
            Gutil.CBOX_TOOLTIP: "run ami section to create all sections ",
        }
        # make sections

        Gutil.make_checkbox_from_dict(ami_project_frame, self.ami_section_dict)

        self.pdfbox_box = None
        self.pdfbox_var = None
        self.ami_pdfbox_dict = {
            Gutil.CBOX_BOX: self.pdfbox_box,
            Gutil.CBOX_VAR: self.pdfbox_var,
            Gutil.CBOX_TEXT: "run pdfbox",
            Gutil.CBOX_ON: Gutil.ONVAL,
            Gutil.CBOX_OFF: Gutil.OFFVAL,
            Gutil.CBOX_DEFAULT: Gutil.ONVAL,
            Gutil.CBOX_TOOLTIP: "run ami pdfbox to make SVG and images",
        }

        Gutil.make_checkbox_from_dict(ami_project_frame, self.ami_pdfbox_dict)

    def make_ami_search(self, master):
        """

        :param master:

        """

        self.run_ami_frame, title_var = Gutil.make_frame_with_hide(master,
                                                                   title="Search",
                                                                   tooltip="wordcount, or phrases or ami search using dictionaries",
                                                                   )

        run_button_var = tk.StringVar(value="SEARCH PROJECT")
        ami_button = tk.Button(
            self.run_ami_frame, textvariable=run_button_var, command=self.run_ami_search)
        ami_button.pack(side=tk.BOTTOM)

        new_project_button = ttk.Button(
            self.run_ami_frame,
            text='Add CProject',
            command=self.add_cproject
        )
        CreateToolTip(new_project_button,
                      "select project in Project Box and give mnemonic in entry")
        new_project_button.pack(side=tk.BOTTOM, expand=True)
        # project name
        self.new_project_name_var = tk.StringVar()
        self.new_project_name_entry = tk.Entry(self.run_ami_frame,
                                               textvariable=self.new_project_name_var)
        self.new_project_name_entry.pack(side=LEFT)

        # project desc
        self.new_project_desc_var = tk.StringVar()
        self.new_project_desc_entry = tk.Entry(self.run_ami_frame,
                                               textvariable=self.new_project_desc_var)
        self.new_project_name_entry.pack(side=tk.RIGHT)

        self.refresh_project_listbox(self.run_ami_frame)

        return self.run_ami_frame, title_var

    def refresh_project_listbox(self, run_ami_frame):
        """

        :param run_ami_frame:

        """
        self.project_names_listbox = self.create_generic_listbox(
            self.current_ami_projects.project_dict.keys(),
            master=run_ami_frame,
        )
        self.project_names_listbox.pack(side=BOTTOM)

    def add_cproject(self):
        """ """
        new_dir = self.outdir_var.get()
        print("add CProject ", new_dir, "to project list")
        label = self.new_project_name_var.get()
        description = self.new_project_desc_var.get()
        self.current_ami_projects.add_with_check(label, new_dir, description)
        self.project_names_listbox.destroy()
        self.refresh_project_listbox(self.run_ami_frame)

        pass

    def run_ami_search(self):
        """ """
        ami_search = AmiSearch()
        ami_search.ami_projects = self.current_ami_projects
        ami_guix = self
        ami_search.run_search_from_gui(ami_guix)

    def make_getpapers_args(self, frame):
        """

        :param frame:

        """
        getpapers_args_frame = tk.Frame(frame,
                                        highlightbackground="black",
                                        highlightthickness=1)
        getpapers_args_frame.pack(side=tk.TOP)

        checkbox_frame = tk.Frame(getpapers_args_frame,
                                  highlightbackground="black",
                                  highlightthickness=1)
        checkbox_frame.pack(side=tk.TOP)

        Gutil.make_help_label(checkbox_frame, tk.LEFT,
                              "pygetpapers checkboxes")

        for key in self.flags_keys:
            self.make_pygetpapers_check_button(checkbox_frame, key)

        self.spin = Gutil.make_spinbox(
            getpapers_args_frame, "maximum hits (-k)", minn=1, maxx=self.max_max_hits)

    def make_pygetpapers_check_button(self, master, key):
        """

        :param master:
        :param key:

        """
        cbox_dict = self.pygetpapers_flags[key]
        Gutil.make_checkbox_from_dict(master, cbox_dict, side=tk.LEFT)

    def create_run_button(self, master):
        """

        :param master:

        """
        button = tk.Button(master)
        button[Gutil.CBOX_TEXT] = "DOWNLOAD"
        button[Gutil.CBOX_COMMAND] = self.create_pygetpapers_query_and_run
        button.pack(side=LEFT)
        self.pygetpapers_command = tk.Entry(master, bg="#ffffdd")
        self.pygetpapers_command.pack(side=LEFT, expand=True)

    def create_make_project_button(self, master):
        """

        :param master:

        """
        button = tk.Button(master)
        button[Gutil.CBOX_TEXT] = "Make project"
        button[Gutil.CBOX_COMMAND] = self.save_project
        self.pygetpapers_command = tk.Entry(master, bg="#ffffdd")
        self.pygetpapers_command.pack(side=tk.RIGHT, expand=True)
        button.pack(side=tk.RIGHT)
        button["state"] = "disabled"
        return button

    def make_dictionary_content_boxes(self, master, dictionary_dict, selected_dict_names):
        """

        :param master:
        :param dictionary_dict:
        :param selected_dict_names:

        """
        frame = tk.Frame(master,
                         highlightcolor="blue",
                         highlightthickness=10)
        frame.pack()
        print(f"created dictionary_content_box master{master}")

        self.dictionary_content_notebook = ttk.Notebook(frame)
        label = tk.Label(self.dictionary_content_notebook,
                         text="Dictionary Notebook")
        CreateToolTip(label, "display of selected dictionaries")
        label.pack(side=tk.TOP)
        self.dictionary_content_notebook.pack()

        self.selected_boxes = []
        for dict_name in selected_dict_names:
            search_dictionary = dictionary_dict[dict_name]
            f1 = tk.Frame(self.dictionary_content_notebook,
                          highlightcolor="blue",
                          highlightthickness=2)
            self.dictionary_content_notebook.add(f1, text=dict_name)
            description = "description??"
            curbox = self.make_dictionary_content_box(
                self.dictionary_content_notebook, dict_name, search_dictionary.file, desc=description)
            curbox.pack()

            self.selected_boxes.append(curbox)

    def make_cproject_frame(self, master, box_side):
        """

        :param master:
        :param box_side:

        """
        from tkinter import ttk

        cproject_frame, title_var = Gutil.make_frame_with_hide(master,
                                                               title="CProject",
                                                               tooltip="Project directory",
                                                               )
        cproject_frame.pack(side=TOP)

        open_button = ttk.Button(
            cproject_frame,
            text='Dir',
            command=self.select_directory
        )
        open_button.pack(side=LEFT, expand=True)

        display_button = ttk.Button(
            cproject_frame,
            text='Display',
            command=self.display_directory
        )
        display_button.pack(side=tk.RIGHT, expand=True)

        default_dir = os.path.join(os.path.expanduser("~"), "temp_cproject")

        self.outdir_var = tk.StringVar(None)
        self.dir_entry = tk.Entry(
            cproject_frame, textvariable=self.outdir_var, width=25)
        Gutil.refresh_entry(self.dir_entry, default_dir)
        self.dir_entry.pack(side=tk.RIGHT)

        return cproject_frame

    def select_directory(self):
        """ """

        filename = fd.askdirectory(
            title='Output directory',
            initialdir=os.path.expanduser("~"),  # HOME directory
        )
        Gutil.refresh_entry(self.dir_entry, filename)

    def display_directory(self):
        """ """
        title = "dummy title"
        if self.ami_tree is None:
            self.ami_tree = AmiTree(self)
        self.treeview = self.ami_tree.get_or_create_treeview(
            self.main_display_frame, title)

        parent = ''

        outdir_val = self.outdir_var.get()
        self.ami_tree.directory = outdir_val
        try:
            self.ami_tree.recursive_display(outdir_val, parent, self.treeview)
        except Exception as e:
            logging.error(f"Cannot recursively display {outdir_val}; cause: {e}")

    def make_dictionary_content_box(self, master, dictionary_name, ami_dictionary, desc="Missing desc"):
        """

        :param master:
        :param dictionary_name:
        :param ami_dictionary:
        :param desc:  (Default value = "Missing desc")

        """
        frame, _ = Gutil.make_frame(master,
                                    title=dictionary_name,
                                    tooltip=desc,
                                    )
        frame.pack(side=LEFT)

        box = self.create_generic_listbox(self.read_entry_names(ami_dictionary),
                                          master=frame, title="select dictionary items")
        box.pack(side=BOTTOM)
        box.bind("<<ListboxSelect>>", lambda event, self=self, dictionary=dictionary_name:
                 self.show_dictionary_item(event, dictionary))
        return box

    """
    https://stackoverflow.com/questions/4299145/getting-the-widget-that-triggered-an-event
    """

    def show_dictionary_item(self, event, dictionary_name):
        """

        :param event:
        :param dictionary_name:

        """
        box = event.widget
        selections = Gutil.get_selections_from_listbox(box)
        selection = selections[0] if len(selections) > 0 else None
        if selection is not None:
            term = selection.lower()
            dictionary = AmiDictionaries().dictionary_dict[dictionary_name]
            entry_xml, image_url = dictionary.get_xml_and_image_url(term)
            self.view_main_text_content(entry_xml)
            if image_url is not None:
                with urlopen(image_url) as u:
                    raw_data = u.read()
                im = Image.open(BytesIO(raw_data))
                w, h = im.size
                if w > 600:
                    h = int(h * 600 / w)
                    w = 600
                    im = im.resize((w, h), Image.ANTIALIAS)
                photo = ImageTk.PhotoImage(im)
                self.set_image_and_persist(photo)
            box.selection_clear(0, tk.END)

    def create_generic_listbox(self, items, master=None, command=None, title=None, tooltip=None, button_text="select"):
        """

        :param items:
        :param master:  (Default value = None)
        :param command:  (Default value = None)
        :param title:  (Default value = None)
        :param tooltip:  (Default value = None)
        :param button_text:  (Default value = "select")

        """
        if tooltip is None:
            tooltip = f"generic listbox {title}"
        frame, title_var = Gutil.make_frame(master,
                                            title=title,
                                            tooltip=tooltip,
                                            # highlightbackground="green",
                                            highlightthickness=2,
                                            )

        lb = Gutil.create_listbox_from_list(frame, items)
        lb.pack(side=tk.BOTTOM)

        if command is not None:
            button = tk.Button(frame, text=button_text, command=command,)
            button.pack(side=tk.BOTTOM)

        return lb

    # frames and windows
    """
    https://stackoverflow.com/questions/24656138/python-tkinter-attach-scrollbar-to-listbox-as-opposed-to-window/24656407
    """

    def run_query_and_get_output(self, args):
        """

        :param args:

        """
        try:
            _, stderr_lines = Gutil.run_subprocess_get_lines(args)
        except Exception:
            messagebox.showinfo(title="query failed",
                                message="failed, maybe no output")
            return ["failure, probably no hits"]
        saved = 0
        hits = 0
        for line in stderr_lines:
            if TOTAL_HITS_ARE in line:
                hits = line.split(TOTAL_HITS_ARE)[-1]
            if WROTE_XML in line:
                saved += 1
        messagebox.showinfo(
            title="end search", message="finished search, hits: "+str(hits)+", saved: "+str(saved))
        return stderr_lines

    def create_pygetpapers_query_and_run(self):
        """ """

        limit = self.spin.get()
        query_string = ""
        query_string = self.add_query_entry(query_string)
        query_string = self.add_dictionary_box_terms(query_string)

        if query_string == "":
            print("No query, no submission")
            messagebox.showinfo(
                title="query_output", message="no query or dictionary boxes selected; no submission")
            return

        self.project_dir = self.outdir_var.get()
        if self.project_dir == "":
            print("must give outdir")
            messagebox.showinfo(title="outdir box", message="must give outdir")
            return

        cmd_options = [PYGETPAPERS, "-q", query_string,
                       "-o", self.project_dir, "-k", limit]

        self.add_flags_to_query_command(cmd_options)

#        print("CMD", cmd_options, "\n", str(cmd_options))
        self.pygetpapers_command.insert(0, str(cmd_options))

        lines = self.run_query_and_get_output(cmd_options)

        self.display_query_output(root, lines)

        if self.ami_section_dict[Gutil.CBOX_VAR].get() == Gutil.ONVAL:
            self.run_ami_sections()
        if self.ami_pdfbox_dict[Gutil.CBOX_VAR].get() == Gutil.ONVAL:
            self.run_ami_pdfbox()

    def save_project(self):
        """ """

        pass

    def run_ami_sections(self):
        """ """
        args = ["ami", "-p", self.project_dir, "section"]
#        print("making sections", args)
        stdout_lines, _ = Gutil.run_subprocess_get_lines(args)
        #            self.main_text_display(stdout_lines)
        print("stdout", stdout_lines)

    def run_ami_pdfbox(self):
        """ """
        args = ["ami", "-p", self.project_dir, "pdfbox"]
        stdout_lines, _ = Gutil.run_subprocess_get_lines(args)
        #            self.main_text_display(stdout_lines)
        print("stdout", stdout_lines)

    def add_flags_to_query_command(self, cmd_options):
        """

        :param cmd_options:

        """

        for k, v in self.pygetpapers_flags.items():
            if k in self.pygetpapers_flags:
                if v[Gutil.CBOX_VAR].get() == Gutil.ONVAL:
                    option = v[Gutil.CBOX_BRIEF] if Gutil.CBOX_BRIEF in v else None
                    if option is None:
                        option = v[Gutil.CBOX_FULL] if Gutil.CBOX_FULL in v else None
                    if option is None:
                        print("Cannot find keys for", k)
                    else:
                        cmd_options.append(option)

    def add_query_entry(self, query_string):
        """

        :param query_string:

        """
        query_string = self.entry_text.get()
        if query_string != "":
            query_string = '("' + query_string + '")'
        return query_string

    def add_dictionary_box_terms(self, lbstr):
        """

        :param lbstr:

        """
        for box in self.selected_boxes:
            select_str = self.make_query_string(box)
            if select_str is None or select_str == "":
                continue
            if lbstr != "":
                lbstr += " AND "
            lbstr += select_str
        return lbstr

    def add_if_checked(self, cmd_options, var, val):
        """

        :param cmd_options:
        :param var:
        :param val:

        """
        if var is not None and var.get() == gu.ONVAL:
            cmd_options.append(val)

    def print_check(self):
        """ """
        s = False
        print("check", self.check.getboolean(s))

    def make_query_string(self, listbox):
        """

        :param listbox:

        """
        selected = Gutil.get_selections_from_listbox(listbox)
        s = ""
        ll = len(selected)
        s = '('
        s += Gutil.quoteme(selected[0]) if ll > 0 else ""
        for i in range(1, ll):
            s += " OR " + Gutil.quoteme(selected[i])
        s += ')'
        return s

    def selected_text(event):
        """

        :param event:

        """
        print("SELECTED", event)

    def display_query_output(self, master, lines):
        """

        :param master:
        :param lines:

        """
        # Title Label
        frame = tk.Frame(master)
        frame.pack(side=BOTTOM)
        lab = tk.Label(frame,
                       text="output",
                       font=("Arial", 15),
                       background='white',
                       foreground="white")
        lab.pack(side="bottom")
        #            .grid(column=0, row=0)

        # Creating scrolled text area
        # widget with Read only by
        # disabling the state
        text_area = scrolledtext.ScrolledText(frame,
                                              width=30,
                                              height=8,
                                              font=("Arial", 15))
        text_area.pack(side="bottom")

        # Inserting Text which is read only
        text = "\n".join(lines)
        text_area.insert(tk.INSERT, text)
        text_area.bind("<Button-1>", button1)
        text_area.bind("<<Selected Text>>", self.selected_text)
        # Making the text read only
        #        text_area.configure(state='disabled')
        return text_area

    def read_entry_names(self, dictionary_file):
        """

        :param dictionary_file:

        """
#        print(dictionary_file)
        assert (os.path.exists(dictionary_file))
        elementTree = ET.parse(dictionary_file)
        entries = elementTree.findall("entry")
        names = [entry.attrib["name"] for entry in entries]
        # print("entries", len(names))
        names = sorted(names)
        return names

    def make_quit(self, master):
        """

        :param master:

        """

        frame, title_var = Gutil.make_frame(master,
                                            title="",
                                            tooltip="quit and destroy windoe",
                                            )

        quit = tk.Button(frame, text="QUIT", fg="red",
                         command=self.master.destroy)
        quit.pack(side=tk.BOTTOM)

        pass

    def make_dictionary_content_boxes_frame(self, master):
        """

        :param master:

        """
        self.dcb_frame, title_var = Gutil.make_frame(master,
                                                     # title="select entries in dictionaries",
                                                     tooltip="dictionary content boxes will be added here",
                                                     )
        self.dcb_frame.pack()
        return self.dcb_frame

    def query_wikidata(self, text):
        """

        :param text:

        """
        print("launch wikidata browser")
        wikidata_browser = WikidataBrowser(self, text)

    def create_wikidata_query_url(self, text):
        """

        :param text:

        """
        BASE_URL = "https://www.wikidata.org/w/index.php?search="
        text = text.strip()
        text = text.replace(" ", "+")
        query = BASE_URL + text
        return query
# https://www.wikidata.org/w/index.php?search=lantana+camara&search=lantana+camara&title=Special%3ASearch&go=Go&ns0=1&ns120=1


"""unused"""


def print_console():
    """ """
    print(console.get("1.0", "end-1c"))
    root.after(1000, print_console)


def run_gui():
    global root, console
    use_console = False  # debugging not yet finished
    root = tk.Tk()
    # screen = Frame(root)
    # screen.pack()
    app = AmiGui(master=root)
    console = tk.Text(app)
    # console.pack()
    #    print_console()
    app.mainloop()

def main():
    run_gui()

if __name__ == '__main__':
    main()