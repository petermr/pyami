import logging
import tkinter as tk
import tkinter.ttk as ttk

import subprocess
import os
import time

# logging.warning("load gutil.py")

HLBG = "highlightbackground"
HLTHICK = "highlightthickness"
SIDE = "side"
TITLE = "title"
TOOLTIP = "tooltip"


class ToolTip(object):

    # https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.text = None

    def showtip(self, text):
        OFFSET_X = 57
        OFFSET_Y = 27

        from tkinter import Toplevel, SOLID
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + OFFSET_X
        y = y + cy + self.widget.winfo_rooty() + OFFSET_Y
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=SOLID, borderwidth=1,
                         font=("tahoma", "15", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)

    def enter(event):
        toolTip.showtip(text)

    def leave(event):
        toolTip.hidetip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


class Gutil:
    CBOX_BOX = "box"
    CBOX_VAR = "var"
    CBOX_TEXT = "text"
    CBOX_ON = "on"
    CBOX_OFF = "off"
    CBOX_BRIEF = "brief"
    CBOX_FULL = "full"
    CBOX_DEFAULT = "default"
    CBOX_COMMAND = "command"
    CBOX_TOOLTIP = "tooltip"
    TEXT_DEFAULT = "default"

    ONVAL = 1
    OFFVAL = 0

    SUBPROC_LINE_END = "\\n"

    @staticmethod
    def create_listbox_from_list(frame, items):
        lb = tk.Listbox(master=frame, height=5,
                        selectmode=tk.MULTIPLE,
                        exportselection=False,
                        highlightcolor="green",
                        selectbackground="pink",
                        highlightthickness=1,
                        bg="#ffffdd",
                        bd=1,  # listbox border
                        fg="blue")
        for i, item in enumerate(items):
            lb.insert(i + 1, item)
        return lb

    @staticmethod
    def quoteme(ss):
        return '"' + ss + '"'

    @staticmethod
    def test_prog_bar():
        """unused demo"""

        # Create the master object
        master = tk.Tk()

        # Create a progressbar widget
        progress_bar = ttk.Progressbar(master, orient="horizontal",
                                       mode="determinate", maximum=100, value=0)

        # And a label_xml for it
        label_1 = tk.Label(master, text="Progress Bar")

        # Use the grid manager
        label_1.grid(row=0, column=0)
        progress_bar.grid(row=0, column=1)

        # Necessary, as the master object needs to draw the progressbar widget
        # Otherwise, it will not be visible on the screen
        master.update()

        progress_bar['value'] = 0
        master.update()

        while progress_bar['value'] < 100:
            progress_bar['value'] += 10
            # Keep updating the master object to redraw the progress bar
            master.update()
            time.sleep(0.5)

        # The application mainloop
        tk.mainloop()

    @staticmethod
    def make_checkbox_from_dict(master, dikt, **kwargs):
        onval = dikt[Gutil.CBOX_ON]
        side = kwargs["side"] if "side" in kwargs else None
        dikt[Gutil.CBOX_BOX], dikt[Gutil.CBOX_VAR] = \
            cbox, cvar = Gutil.create_check_box(master, text=dikt[Gutil.CBOX_TEXT], side=side,
                                                default=dikt[Gutil.TEXT_DEFAULT])
        tooltip = dikt[Gutil.CBOX_TOOLTIP] if Gutil.CBOX_BOX in dikt.keys() else None
        if tooltip is not None:
            CreateToolTip(cbox, text=tooltip)

    @staticmethod
    def create_check_box(master, text, **kwargs):
        from tkinter import ttk
        checkVar = tk.IntVar()
        defval = kwargs[Gutil.TEXT_DEFAULT] if Gutil.TEXT_DEFAULT in kwargs else None
        if defval is not None and defval == Gutil.ONVAL:
            checkVar.get()
        checkbutton = ttk.Checkbutton(master, text=text, variable=checkVar,
                                      onvalue=Gutil.ONVAL, offvalue=Gutil.OFFVAL)
        if defval is not None and defval == Gutil.ONVAL:
            checkVar.set(Gutil.ONVAL)
        side = kwargs[SIDE] if SIDE in kwargs else tk.BOTTOM
        checkbutton.pack(side=side)

        return checkbutton, checkVar

    @staticmethod
    def create_hide_frame(master, title=None):
        hide_frame = tk.Frame(master,
                              highlightbackground="green",
                              highlightthickness=1,
                              )
        return hide_frame

    @staticmethod
    def labelactive(widget, show_button, hide_button):
        widget.pack(expand=True)
        show_button.pack_forget()
        hide_button.pack()

    @staticmethod
    def labeldeactive(widget, show_button, hide_button):
        widget.pack_forget()
        show_button.pack()
        hide_button.pack_forget()

    @staticmethod
    def make_frame_with_hide(master, title=None, tooltip=None, **kwargs):
        hide_frame = Gutil.create_hide_frame(master)
        hide_frame.pack(side=tk.TOP)
        frame, title_var = Gutil.make_frame(hide_frame, **kwargs)
        if tooltip is not None:
            CreateToolTip(frame, text=tooltip)
        hide_button = None
        show_button = tk.Button(hide_frame, text="show " + title, command=lambda: Gutil.labelactive(
            frame, show_button, hide_button))
        show_button.pack_forget()
        hide_button = tk.Button(hide_frame, text="hide " + title, command=lambda: Gutil.labeldeactive(
            frame, show_button, hide_button))
        hide_button.pack()
        # leave in the hidden state. this should contract all frames within the master
        # to a single "show" button
        Gutil.labeldeactive(frame, show_button, hide_button)

        return frame, title_var

    @staticmethod
    def make_frame(master, **kwargs):
        """ makes a frame with a rim and help tooltip
        (tk uses "highlight" for the rim which other systems call "border";
         there is a separate border outside the rim. So highlightbackground is "border" colour)
        :master: the parent frame
        :kwargs:
               highlightbackground=color,
               highlightthickness=width,
               side=side,
               title=title,
               tooltip=tooltip,

        """
        defaults = {
            HLBG: "brown",
            HLTHICK: 2,
            SIDE: tk.TOP,
            TITLE: "?",
            TOOLTIP: None,
        }
        bg_col = kwargs[HLBG] if HLBG in kwargs else defaults[HLBG]
        bg_thick = kwargs[HLTHICK] if HLTHICK in kwargs else defaults[HLTHICK]
        side = kwargs[SIDE] if SIDE in kwargs else defaults[SIDE]
        title = kwargs[TITLE] if TITLE in kwargs else None
        tooltip = kwargs[TOOLTIP] if TOOLTIP in kwargs else defaults[TOOLTIP]

        frame = tk.Frame(master, highlightbackground=bg_col, highlightthickness=bg_thick)
        title_var = None
        if title is not None and title != "":
            title_var = tk.StringVar(value=title)
            label = tk.Label(frame, textvariable=title_var)
            label.pack(side=side)
            if tooltip is not None:
                CreateToolTip(label, text=tooltip)
        frame.pack(side=side, expand=True, fill=tk.X)
        return frame, title_var

    @staticmethod
    def make_help_label(master, side, text):
        label = tk.Label(master, text="?", background="white")
        CreateToolTip(label, text=text)
        label.pack(side=side)

    @staticmethod
    def refresh_entry(entry, new_text):
        entry.delete(0, tk.END)
        entry.insert(0, new_text)

    @staticmethod
    def make_entry_box(master, **kwargs):
        entry_frame = tk.Frame(master=master,
                               highlightbackground="purple", highlightthickness=3)
        entry_frame.pack(side=tk.BOTTOM)

        labelText = tk.StringVar()
        txt = kwargs[Gutil.CBOX_TEXT] if Gutil.CBOX_TEXT in kwargs else ""
        labelText.set(txt)
        entry_label = tk.Label(entry_frame, textvariable=labelText)
        entry_label.pack(side=tk.LEFT)

        default_text = kwargs[Gutil.TEXT_DEFAULT] if Gutil.TEXT_DEFAULT in kwargs else None
        entry_text = tk.StringVar(None)
        entry = tk.Entry(entry_frame, textvariable=entry_text, width=25)
        entry.delete(0, tk.END)
        if default_text is not None:
            entry.insert(0, default_text)
        entry.pack(side=tk.LEFT)

        return entry_text

    @staticmethod
    def run_subprocess_get_lines(args):
        """runs subprocess with args
         :return: tuple (stdout as lines, stderr as lines)
         """
        completed_process = subprocess.run(args, capture_output=True)
        completed_process.check_returncode()  # may throw error which caller muct catch
        # throws error
        # completed_process.stdout returns <bytes>, convert to <str>
        stdout_str = str(completed_process.stdout)
        stderr_str = str(completed_process.stderr)
        argsx = completed_process.args
        stderr_lines = stderr_str.split(Gutil.SUBPROC_LINE_END)  # the <str> conversion adds a backslash?
        stdout_lines = stdout_str.split(Gutil.SUBPROC_LINE_END)
        return stdout_lines, stderr_lines

    @staticmethod
    def get_selections_from_listbox(box):
        return [box.get(i) for i in box.curselection()]

    @staticmethod
    def make_spinbox(master, title, minn=3, maxx=100):
        spin_frame = tk.Frame(master=master, bg="#444444", bd=1, )
        spin_frame.pack(expand=True)
        label = tk.Label(master=spin_frame, text=title)
        label.pack(side="left")
        spin = tk.Spinbox(spin_frame, from_=minn, to=maxx, state="readonly", width=3)
        spin.pack(side="right")
        return spin


class AmiTree:
    def __init__(self, ami_gui):
        self.tree = None
        self.ami_gui = ami_gui
        self.main_image_display = None

    def get_or_create_treeview(self, frame, title):
        if self.tree is not None:
            self.tree.destroy()
        self.tree = ttk.Treeview(frame)
        self.tree.bind('<<TreeviewSelect>>', self.display_items_selected)

        self.color_tags()
        self.tree.pack(expand=True, fill="x")
        return self.tree

    def color_tags(self):
        self.tree.tag_configure('xml', background='pink')
        self.tree.tag_configure('pdf', background='lightgreen')
        self.tree.tag_configure('png', background='cyan')
        self.tree.tag_configure('txt', background='bisque2')

    def display_items_selected(self, event):
        id_list = self.tree.selection()

        tags_to_display = ["png", "xml", "txt"]  # refine this
        path_list = []
        for idx in id_list:
            self.display_item_selected(idx, path_list, tags_to_display)

        return id_list, path_list

    def display_item_selected(self, idx, path_list, tags_to_display):
        item_dict = self.tree.item(idx)
        for tag in tags_to_display:
            if tag in item_dict["tags"]:
                path = self.make_file_path(idx)
                path_list.append(path)
                file = os.path.join(self.directory, path)
                if self.is_image_tag(tag):
                    self.main_image_display = self.ami_gui.create_image_label(file)
                if self.is_text_tag(tag):
                    self.ami_gui.view_main_text(file)

    @classmethod
    def is_image_tag(cls, tag):
        return tag in ["png", "jpg"]

    @classmethod
    def is_text_tag(cls, tag):
        return tag in ["txt", "xml"]

    def make_file_path(self, idx):
        path_component_list = [self.tree.item(idx)["text"] for idx in self.make_path_component_id_list(idx)]
        path = os.path.join(*path_component_list)
        return path

    def make_path_component_id_list(self, idx):
        path_list = [idx]
        parent_id = "dummy"
        while parent_id != "":
            parent_id = self.tree.parent(idx)
            if parent_id == "":
                break
            path_list.append(parent_id)
            idx = parent_id
        path_list.reverse()
        return path_list

    def recursive_display(self, dirx, parent_id, tree):
        childfiles = [f.path for f in os.scandir(dirx) if os.path.isdir(dirx) and not dirx.startswith(".") and not dirx==""]
        sorted_child_files = AmiTree.sorted_alphanumeric(childfiles)
        for f in sorted_child_files:
            filename = AmiTree.path_leaf(f)
            child_id = None
            if self.display_filename(f):
                tag = self.tag_from_file_suffix(f)
                child_id = tree.insert(parent_id, 'end', text=filename, tags=tag)
            #                tree.tag_bind(tag, '<1>', self.itemClicked)

            if os.path.isdir(f) and child_id is not None:
                self.recursive_display(f, child_id, tree)

    @classmethod
    def tag_from_file_suffix(cls, file):
        tag = ""
        for suff in ["xml", "txt", "pdf", "png", "jpg", "gif"]:
            if file.endswith("." + suff):
                tag = suff
        return tag

    @classmethod
    def sorted_alphanumeric(cls, data):
        import re
        # https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(data, key=alphanum_key)

    @classmethod
    def path_leaf(cls, path):
        import ntpath
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    @classmethod
    # FIXME
    def display_filename(cls, filename):
        isd = os.path.isdir(filename)
        # return isd or filename.endswith(".xml")
        return True


# class ScrollableFrame(tk.Frame):
#     def __init__(self, master, **kwargs):
#         tk.Frame.__init__(self, master, **kwargs)
#
#         # create a canvas object and a vertical scrollbar for scrolling it
#         self.vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
#         self.vscrollbar.pack(side='right', fill="y",  expand="false")C
#         self.canvas = tk.Canvas(self,
#                                 bg='#aaa', bd=0,
#                                 height=350,
#                                 highlightthickness=2,
#                                 yscrollcommand=self.vscrollbar.set)
#         self.canvas.pack(side="left", fill="both", expand="true")
#         self.vscrollbar.config(command=self.canvas.yview)
#
#         # reset the view
#         self.canvas.xview_moveto(0)
#         self.canvas.yview_moveto(0)
#
#         # create a frame inside the canvas which will be scrolled with it
#         self.interior = tk.Frame(self.canvas, **kwargs)
#         self.canvas.create_window(0, 0, window=self.interior, anchor="nw")
#
#         self.bind('<Configure>', self.set_scrollregion)
#
#         self.vars = []
#
#
#     def set_scrollregion(self, event=None):
#         """ Set the scroll region on the canvas"""
#         print("event", event)
#         self.canvas.configure(scrollregion=self.canvas.bbox('all'))
#
#
# def scrollable_frame_test():
#     global root, scrollable_pane
#     root = tk.Tk()
#     scrollable_pane = ScrollableFrame(root, bg='#444444')
#     scrollable_pane.pack(expand="true", fill="both")
#
#     def button_callback(button_count):
#         for x in range(1, button_count):
#             print (f"x{x}")
#             var = tk.Variable()
#             vars.append(var)
#             checkbutton = tk.Checkbutton(scrollable_pane.interior, variable=var, textheck="hello world! %s" % x)
#             checkbutton.grid(row=x, column=0)
#             checkbutton.bind("<Button 1>", button_check)
#
#     def button_check(event, serial):
#         print("event", event)
#         for var in vars:
#             print("var", var)
#
#     btn_checkbox = tk.Button(scrollable_pane.interior, text="Click Me!", command=button_callback(10))
#     btn_checkbox.grid(row=0, column=0)
#     root.mainloop()

class CheckEntryFrame(tk.Frame):

    def __init__(self, master, text=None, *args, **kwargs):
        self.master = master
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.cb = ttk.Checkbutton(self, text="?")
        self.cb.pack(side=tk.LEFT)
        self.entry = tk.Entry(self, text=text)
        self.entry.pack(side=tk.RIGHT)


class ScrollingCheckboxList(tk.Frame):

    def __init__(self, master, receiver=None, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        self.receiver = receiver

        self.vsb = tk.Scrollbar(self, orient="vertical")
        self.text = tk.Text(self, width=40, height=20,
                            yscrollcommand=self.vsb.set)
        self.vsb.config(command=self.text.yview)
        self.vsb.pack(side="right", fill="y")

        self.text.pack(side="left", fill="both", expand=True)

        button = ttk.Button(self.master, text="save", command=self.get_checked_values)
        button.pack(side=tk.TOP)

        self.cbs = []
        self.checked_values = []
        self.receiver = receiver

    def add_string_values(self, strings):
        self.cbs = []
        for i, s in enumerate(strings):
            # cef = CheckEntryFrame(self, text=s)
            # cef.cb.state(['!alternate'])
            # cef.cb.state(['!selected'])
            # self.cbs.append(cef.cb)
            # cef.cb.bind("<Button 1>", self.clicked)
            cb = ttk.Checkbutton(self, text=s)
            cb.state(['!alternate'])
            cb.state(['!selected'])
            self.cbs.append(cb)
            cb.bind("<Button 1>", self.clicked)
            self.text.window_create("end", window=cb)
            self.text.insert("end", "\n")  # to force one checkbox per line

    def clicked(self, event):
        # print("clicked", event)
        pass

    def get_checked_values(self):
        checked_values = []
        for i, cb in enumerate(self.cbs):
            if cb.instate(['selected']):
                checked_values.append(cb.cget("text"))
        self.receiver.receive_checked_values(checked_values)


def scrollable_checkbox_test():
    global root
    root = tk.Tk()
    frame = tk.Frame(root)
    frame.pack()
    scl = ScrollingCheckboxList(frame)
    scl.pack(side="top", fill="both", expand=True)
    scl.add_string_values(["a", "b", "zz", "xx", "y", "zzz", "tt", "yyy"])
    root.mainloop()


if __name__ == "__main__":
    if False:
        scrollable_checkbox_test()


# if __name__ == '__main__':
#     scrollable_frame_test()


class ExtraWidgets(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.test()

    def test(self):
        ss = ttk.Style()
        ss.configure('Yellow.TFrame', background='yellow', foreground="pink", border=10, padx=5,
                     highlightcolor="purple", highlightthickness=1)
        s1 = ttk.Style()
        s1.configure('Red.TButton', background='red', foreground="green", font=('Arial', 20, 'bold'))
        s2 = ttk.Style()
        s2.configure('Blue.TButton', background='blue', foreground="red", font=('Courier', 20, 'italic'))

        frame = ttk.Frame(self.master, style="Yellow.TFrame", padding='10 10 15 15', height=400, width=250)
        frame['borderwidth'] = 5
        frame['relief'] = 'sunken'
        frame.config()
        button1 = ttk.Button(self.master, text="Button1", style="Red.TButton")
        button1.config()
        button1.pack()
        button2 = ttk.Button(self.master, text="Button2", style="Blue.TButton")
        button2.config()
        button2.pack()
        #        self.listbox_test()

        self.label_frame_test()
        s = ttk.Separator(self.master, orient=tk.HORIZONTAL)  # doesn't work
        s.pack(fill="x")
        self.notebook_test()

    def separatorTest(self):
        s = ttk.Separator(self.master, orient=tk.HORIZONTAL)
        s.pack()

    def label_frame_test(self):
        p = ttk.Panedwindow(self.master, orient=tk.HORIZONTAL)
        # two panes, each of which would get widgets gridded into it:
        f1 = ttk.Labelframe(p, text='Pane1', width=100, height=200)
        button1 = tk.Button(f1, text="button1")
        button1.pack()
        p.add(f1)
        f2 = ttk.Labelframe(p, text='Pane2', width=100, height=200)
        button2 = tk.Button(f2, text="button2")
        button2.pack()
        p.add(f2)
        p.pack()

        lf = ttk.Labelframe(self.master, text='LabelFrame', height=100, width=10, border=15)
        buttonz1 = tk.Button(lf, text="z1")
        buttonz1.pack()
        lf.pack()

        buttonz2 = tk.Button(lf, text="z2")
        buttonz2.pack()

    def notebook_test(self):
        n = ttk.Notebook(self.master)

        f1 = ttk.Frame(n)  # first page, which would get widgets gridded into it
        button11 = tk.Button(f1, text="button11")
        button11.pack()
        n.add(f1, text='One')
        f2 = ttk.Frame(n)  # second page
        n.add(f2, text='Two')
        button22 = tk.Button(f2, text="button22")
        button22.pack()
        n.pack()


if False:
    print("***********Testing gutil")
    root = tk.Tk()
    app = ExtraWidgets(master=root)
    app.mainloop()
