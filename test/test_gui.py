from tkinter.messagebox import showinfo
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror


def create_input_frame(container):

    frame = ttk.Frame(container)

    # grid layout for the input frame
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(0, weight=3)

    # Find what
    ttk.Label(frame, text='Find what:').grid(column=0, row=0, sticky=tk.W)
    keyword = ttk.Entry(frame, width=30)
    keyword.focus()
    keyword.grid(column=1, row=0, sticky=tk.W)

    # Replace with:
    ttk.Label(frame, text='Replace with:').grid(column=0, row=1, sticky=tk.W)
    replacement = ttk.Entry(frame, width=30)
    replacement.grid(column=1, row=1, sticky=tk.W)

    # Match Case checkbox
    match_case = tk.StringVar()
    match_case_check = ttk.Checkbutton(
        frame,
        text='Match case',
        variable=match_case,
        command=lambda: print(match_case.get()))
    match_case_check.grid(column=0, row=2, sticky=tk.W)

    # Wrap Around checkbox
    wrap_around = tk.StringVar()
    wrap_around_check = ttk.Checkbutton(
        frame,
        variable=wrap_around,
        text='Wrap around',
        command=lambda: print(wrap_around.get()))
    wrap_around_check.grid(column=0, row=3, sticky=tk.W)

    for widget in frame.winfo_children():
        widget.grid(padx=0, pady=5)

    return frame


def create_button_frame(container):
    frame = ttk.Frame(container)

    frame.columnconfigure(0, weight=1)

    ttk.Button(frame, text='Find Next').grid(column=0, row=0)
    ttk.Button(frame, text='Replace').grid(column=0, row=1)
    ttk.Button(frame, text='Replace All').grid(column=0, row=2)
    ttk.Button(frame, text='Cancel').grid(column=0, row=3)

    for widget in frame.winfo_children():
        widget.grid(padx=0, pady=3)

    return frame


def create_main_window():

    # root window
    root = tk.Tk()
    root.title('Replace')
    root.geometry('700x150')
    root.resizable(1, 0)
    # windows only (remove the minimize/maximize button)
    try:
        root.attributes('-toolwindow', True)
    except Exception:
        pass

    # layout on the root window
    root.columnconfigure(0, weight=4)
    root.columnconfigure(1, weight=1)

    input_frame = create_input_frame(root)
    input_frame.grid(column=0, row=0)

    button_frame = create_button_frame(root)
    button_frame.grid(column=1, row=0)

    root.mainloop()


def combo():

    root = tk.Tk()
    root.geometry('300x200')
    root.resizable(False, False)
    root.title('Combobox Widget')

    def month_changed(event):
        msg = f'You selected {month_cb.get()}!'
        showinfo(title='Result', message=msg)

    # month of year
    months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

    label = ttk.Label(text="Please select a month:")
    label.pack(fill='x', padx=5, pady=5)

    # create a combobox
    selected_month = tk.StringVar()

    month_cb = ttk.Combobox(root, textvariable=selected_month)
    month_cb['values'] = months
    month_cb['state'] = 'readonly'  # normal
    month_cb.pack(fill='x', padx=5, pady=5)

    month_cb.bind('<<ComboboxSelected>>', month_changed)

    root.mainloop()


def raise_test():

    class TemperatureConverter:
        @staticmethod
        def fahrenheit_to_celsius(f, formatx=True):
            result = (f - 32) * 5 / 9
            if formatx:
                return f'{f} Fahrenheit = {result:.2f} Celsius'
            return result

        @staticmethod
        def celsius_to_fahrenheit(c, formatx=True):
            result = c * 9 / 5 + 32
            if formatx:
                return f'{c} Celsius = {result:.2f} Fahrenheit'
            return result

    class ConverterFrame(ttk.Frame):
        def __init__(self, container, unit_from, converter):
            super().__init__(container)

            self.unit_from = unit_from
            self.converter = converter

            # field options
            options = {'padx': 5, 'pady': 0}

            # temperature label_xml
            self.temperature_label = ttk.Label(self, text=self.unit_from)
            self.temperature_label.grid(column=0, row=0, sticky='w', **options)

            # temperature entry
            self.temperature = tk.StringVar()
            self.temperature_entry = ttk.Entry(self, textvariable=self.temperature)
            self.temperature_entry.grid(column=1, row=0, sticky='w', **options)
            self.temperature_entry.focus()

            # button
            self.convert_button = ttk.Button(self, text='Convert')
            self.convert_button.grid(column=2, row=0, sticky='w', **options)
            self.convert_button.configure(command=self.convert)

            # result label_xml
            self.result_label = ttk.Label(self)
            self.result_label.grid(row=1, columnspan=3, **options)

            # add padding to the frame and show it
            self.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")

        def convert(self, event=None):
            """  Handle button click event
            """
            try:
                input_value = float(self.temperature.get())
                result = self.converter(input_value)
                self.result_label.config(text=result)
            except ValueError as error:
                showerror(title='Error', message=error)

        def reset(self):
            self.temperature_entry.delete(0, "end")
            self.result_label.text = ''

    class ControlFrame(ttk.LabelFrame):
        def __init__(self, container):
            super().__init__(container)
            self['text'] = 'Options'

            # radio buttons
            self.selected_value = tk.IntVar()

            ttk.Radiobutton(
                self,
                text='F to C',
                value=0,
                variable=self.selected_value,
                command=self.change_frame).grid(column=0, row=0, padx=5, pady=5)

            ttk.Radiobutton(
                self,
                text='C to F',
                value=1,
                variable=self.selected_value,
                command=self.change_frame).grid(column=1, row=0, padx=5, pady=5)

            self.grid(column=0, row=1, padx=5, pady=5, sticky='ew')

            # initialize frames
            self.frames = {}
            self.frames[0] = ConverterFrame(
                container,
                'Fahrenheit',
                TemperatureConverter.fahrenheit_to_celsius)
            self.frames[1] = ConverterFrame(
                container,
                'Celsius',
                TemperatureConverter.celsius_to_fahrenheit)

            self.change_frame()

        def change_frame(self):
            frame = self.frames[self.selected_value.get()]
            frame.reset()
            frame.tkraise()

    class App(tk.Tk):
        def __init__(self):
            super().__init__()

            self.title('Temperature Converter')
            self.geometry('300x120')
            self.resizable(True, False)

    if __name__ == "__main__":
        app = App()
        ControlFrame(app)
        app.mainloop()


def separator_test():

    root = tk.Tk()
    root.geometry('300x200')
    root.resizable(False, False)
    root.title('Separator Widget Demo')

    ttk.Label(root, text="First Label").pack()

    separator = ttk.Separator(root, orient='horizontal')
    separator.pack(fill='x')
    ttk.Label(root, text="Second Label").pack()

    root.mainloop()


def menu_test():  # not yet working
    # menu - not used
    def menu_stuff(self):
        from tkinter import Menu

        root = tk.Tk()
        menubar = Menu(self.master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.menu("newxx"))
        filemenu.add_command(label="Open", command=self.menu("openxx"))
        filemenu.add_command(label="Save", command=self.menu("savexx"))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help Index", command=self.menu("help indexx"))
        helpmenu.add_command(label="About...", command=self.menu("ABOUTxx"))
        menubar.add_cascade(label="Help", menu=helpmenu)

        root.config(menu=menubar)
        print("before mainloop")
        root.mainloop()

    def menu(self, text):
        print("menu", text)

    # https://stackoverflow.com/questions/30004505/how-do-you-find-a-unique-and-constant-id-of-a-widget


if __name__ == "__main__":
    opt = 99
    allx = False
    if opt == 1 or allx:
        create_main_window()
    if opt == 2 or allx:
        combo()
    if opt == 3 or allx:
        raise_test()
    if opt == 4 or allx:
        separator_test()
    if opt == 5 or allx:
        menu_test()
