import PySimpleGUI as sg                        # Part 1 - The import
import matplotlib
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter
from tkinter import *


def test1():
    # Define the window's contents
    layout = [  [sg.Text("What's your name?")],     # Part 2 - The Layout
                [sg.Input()],
                [sg.Button('Ok')] ]

    # Create the window
    window = sg.Window('Window Title', layout)      # Part 3 - Window Defintion

    # Display and interact with the Window
    event, values = window.read()                   # Part 4 - Event loop or Window.read call

    # Do something with the information gathered
    print('Hello', event, values, "! Thanks for trying PySimpleGUI")

    # Finish up by removing from the screen
    window.close()                                  # Part 5 - Close the Window

def test2():
    # Define the window's contents
    layout = [[sg.Text("What's your name?")],
              [sg.Input(key='-INPUT-')],
              [sg.Text(size=(40,1), key='-OUTPUT-')],
              [sg.Button('Ok'), sg.Button('Quit')]]

    # Create the window
    window = sg.Window('Window Title', layout)

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break
        # Output a message to the window
        window['-OUTPUT-'].update('Hello ' + values['-INPUT-'] + "! Thanks for trying PySimpleGUI")

    # Finish up by removing from the screen
    window.close()

def test3():
    layout = [[sg.Button(f'{row}, {col}') for col in range(4)] for row in range(4)]

    event_str, values = sg.Window('List Comprehensions', layout).read(close=True)
    print(event_str, values)

    text = "Hello" + "u\u00A9"+" "+"anticancéreux" + " 抗肿瘤药 "
    event, values = sg.Window('Window Title', [[sg.Text(text)],[sg.Input()],[sg.Button('Ok')]]).read(close=True)
    print(event, values)

    event, values = sg.Window('Window Title', [[sg.T("What's your name?")],[sg.I()],[sg.B('Ok')]]).read(close=True)
    print(event, values)

def test4():
    filename = sg.popup_get_file('Enter the file you wish to process')
    sg.popup('You entered', filename)

    n = 300
    for i in range(1, n):
        sg.one_line_progress_meter('My Meter', i + 1, n, 'key', 'Optional message')
    print = sg.Print
    for i in range(100):
        print(i)

def test5():
    sg.theme('Dark Blue 3')  # please make your windows colorful

    layout = [[sg.Text('Rename files or folders')],
              [sg.Text('Source for Folders', size=(15, 1)), sg.InputText(), sg.FolderBrowse()],
              [sg.Text('Source for Files ', size=(15, 1)), sg.InputText(), sg.FolderBrowse()],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Rename Files or Folders', layout)

    event, values = window.read()
    window.close()
    folder_path, file_path = values[0], values[1]  # get the data from the values dictionary
    sg.Print(folder_path, file_path) ## immediately self-destructs unless blocked
    n = 100
    for i in range(1, n):
        sg.one_line_progress_meter('My Meter', i + 1, n, 'key', 'Optional message')

    print(folder_path, file_path)
    print("EXIT")

def test6():
    import PySimpleGUI as sg
    import os.path

    # First the window layout in 2 columns

    file_list_column = [
        [
            sg.Text("Image Folder"),
            sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
            sg.FolderBrowse(),
        ],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
            )
        ],
    ]

    # For now will only show the name of the file that was chosen
    image_viewer_column = [
        [sg.Text("Choose an image from list on left:")],
        [sg.Text(size=(40, 1), key="-TOUT-")],
        [sg.Image(key="-IMAGE-")],
    ]

    # ----- Full layout -----
    layout = [
        [
            sg.Column(file_list_column),
            sg.VSeperator(),
            sg.Column(image_viewer_column),
        ]
    ]

    window = sg.Window("Image Viewer", layout)

    # Run the Event Loop
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        # Folder name was filled in, make a list of files in the folder
        if event == "-FOLDER-":
            folder = values["-FOLDER-"]
            try:
                # Get list of files in folder
                file_list = os.listdir(folder)
            except:
                file_list = []

            fnames = [
                f
                for f in file_list
                if os.path.isfile(os.path.join(folder, f))
                   and f.lower().endswith((".png", ".gif", ".txt"))
            ]
            window["-FILE LIST-"].update(fnames)
        elif event == "-FILE LIST-":  # A file was chosen from the listbox
            try:
                filename = os.path.join(
                    values["-FOLDER-"], values["-FILE LIST-"][0]
                )
                window["-TOUT-"].update(filename)
                window["-IMAGE-"].update(filename=filename)

            except:
                pass

    window.close()

matplotlib.use("TkAgg")

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="top", fill="both", expand=1)
    return figure_canvas_agg


def test7():

    fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
    t = np.arange(0, 3, .01)
    fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))

    # Define the window layout
    layout = [
        [sg.Text("Plot test")],
        [sg.Canvas(key="-CANVAS-")],
        [sg.Button("Ok")],
    ]

    # Create the form and show it without the plot
    window = sg.Window(
        "Matplotlib Single Graph",
        layout,
        location=(0, 0),
        finalize=True,
        element_justification="center",
        font="Helvetica 18",
    )

    # Add the plot to the window
    draw_figure(window["-CANVAS-"].TKCanvas, fig)

    event, values = window.read()

    window.close()

def test8():
    import PySimpleGUI as sg
    import cv2
    import numpy as np

    def main():
        sg.theme("LightGreen")

        # Define the window layout
        layout = [
            [sg.Text("OpenCV Demo", size=(60, 1), justification="center")],
            [sg.Image(filename="", key="-IMAGE-", size=(300,300), pad=(3,3,12,12))],
            [sg.Radio("None", "Radio", True, size=(10, 1))],
            [
                sg.Radio("threshold", "Radio", size=(10, 1), key="-THRESH-"),
                sg.Slider(
                    (0, 255),
                    128,
                    1,
                    orientation="h",
                    size=(40, 15),
                    key="-THRESH SLIDER-",
                ),
            ],
            [
                sg.Radio("canny", "Radio", size=(10, 1), key="-CANNY-"),
                sg.Slider(
                    (0, 255),
                    128,
                    1,
                    orientation="h",
                    size=(20, 15),
                    key="-CANNY SLIDER A-",
                ),
                sg.Slider(
                    (0, 255),
                    128,
                    1,
                    orientation="h",
                    size=(20, 15),
                    key="-CANNY SLIDER B-",
                ),
            ],
            [
                sg.Radio("blur", "Radio", size=(10, 1), key="-BLUR-"),
                sg.Slider(
                    (1, 11),
                    1,
                    1,
                    orientation="h",
                    size=(40, 15),
                    key="-BLUR SLIDER-",
                ),
            ],
            [
                sg.Radio("hue", "Radio", size=(10, 1), key="-HUE-"),
                sg.Slider(
                    (0, 225),
                    0,
                    1,
                    orientation="h",
                    size=(40, 15),
                    key="-HUE SLIDER-",
                ),
            ],
            [
                sg.Radio("enhance", "Radio", size=(10, 1), key="-ENHANCE-"),
                sg.Slider(
                    (1, 255),
                    128,
                    1,
                    orientation="h",
                    size=(40, 15),
                    key="-ENHANCE SLIDER-",
                ),
            ],
            [sg.Button("Exit", size=(10, 1))],
        ]

        # Create the window and show it without the plot
        window = sg.Window("OpenCV Integration", layout, size=(800,1000), location=(200, 400))

        cap = cv2.VideoCapture(0)

        while True:
            event, values = window.read(timeout=20)
            if event == "Exit" or event == sg.WIN_CLOSED:
                break

            ret, frame = cap.read()

            if values["-THRESH-"]:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)[:, :, 0]
                frame = cv2.threshold(
                    frame, values["-THRESH SLIDER-"], 255, cv2.THRESH_BINARY
                )[1]
            elif values["-CANNY-"]:
                frame = cv2.Canny(
                    frame, values["-CANNY SLIDER A-"], values["-CANNY SLIDER B-"]
                )
            elif values["-BLUR-"]:
                frame = cv2.GaussianBlur(frame, (21, 21), values["-BLUR SLIDER-"])
            elif values["-HUE-"]:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                frame[:, :, 0] += int(values["-HUE SLIDER-"])
                frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
            elif values["-ENHANCE-"]:
                enh_val = values["-ENHANCE SLIDER-"] / 40
                clahe = cv2.createCLAHE(clipLimit=enh_val, tileGridSize=(8, 8))
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            imgbytes = cv2.imencode(".png", frame)[1].tobytes()
            window["-IMAGE-"].update(data=imgbytes)

        window.close()

def test9():
    import PySimpleGUI as sg

    sg.theme('Dark Blue 3')  # Add a touch of color
    # All the stuff inside your window.
    layout = [[sg.Text('Some text on Row 1')],
              [sg.Text('Enter something on Row 2'), sg.InputText()],
              [sg.Button('Ok'), sg.Button('Cancel')]]

    # Create the Window
    window = sg.Window('Window Title', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        print('You entered ', values[0])

    window.close()

def test10():
    import PySimpleGUI as sg

    layout = []
    for i in range(1, 6):
        layout += [sg.Text(f'{i}. xxx'), sg.In(key=i)],
    layout += [[sg.Button('Save'), sg.Button('Exit')]]

    window = sg.Window('To Do List Example', layout)
    event, values = window.read()

def test11():
    # fails on first line

    import PySimpleGUI as SG
# AttributeError: __enter__
    with SG.FlexForm('Everything bagel') as form:
        layout = [
            [SG.Text('All graphic widgets in one form!', size=(30, 1), font=("Helvetica", 25), text_color='blue')],
            [SG.Text('Here is some text.... and a place to enter text')],
            [SG.InputText()],
            [SG.Checkbox('My first checkbox!'), SG.Checkbox('My second checkbox!', default=True)],
            [SG.Radio('My first Radio!     ', "RADIO1", default=True), SG.Radio('My second Radio!', "RADIO1")],
            [SG.Multiline(default_text='This is the default Text shoulsd you decide not to type anything',
                          scale=(2, 10))],
            [SG.InputCombo(['Combobox 1', 'Combobox 2'], size=(20, 3)),
             SG.Slider(range=(1, 100), orientation='h', size=(35, 20), default_value=85)],
            [SG.Listbox(values=['Listbox 1', 'Listbox 2', 'Listbox 3'], size=(30, 6)),
             SG.Slider(range=(1, 100), orientation='v', size=(10, 20), default_value=25),
             SG.Slider(range=(1, 100), orientation='v', size=(10, 20), default_value=75),
             SG.Slider(range=(1, 100), orientation='v', size=(10, 20), default_value=10)],
            [SG.Text('_' * 100, size=(70, 1))],
            [SG.Text('Choose Source and Destination Folders', size=(35, 1))],
            [SG.Text('Source Folder', size=(15, 1), auto_size_text=False, justification='right'),
             SG.InputText('Source'), SG.FolderBrowse()],
            [SG.Text('Destination Folder', size=(15, 1), auto_size_text=False, justification='right'),
             SG.InputText('Dest'),
             SG.FolderBrowse()],
            [SG.Submit(), SG.Cancel(), SG.SimpleButton('Customized', button_color=('white', 'green'))]
        ]

    button, values = form.LayoutAndRead(layout)

def test12():
    import PySimpleGUI as sg

    sg.theme('Dark Brown 1')

    headings = ['HEADER 1', 'HEADER 2', 'HEADER 3', 'HEADER 4']
    header = [[sg.Text('  ')] + [sg.Text(h, size=(14, 1)) for h in headings]]

    input_rows = [[sg.Input(size=(15, 1), pad=(0, 0)) for col in range(4)] for row in range(10)]

    layout = header + input_rows

    window = sg.Window('Table Simulation', layout, font='Courier 12')
    event, values = window.read()

def test13():
    import PySimpleGUI as sg

    def ToDoItem(num):
        return [sg.Text(f'{num}. '), sg.CBox(''), sg.In()]

    layout = [ToDoItem(x) for x in range(1, 6)] + [[sg.Button('Save'), sg.Button('Exit')]]

    window = sg.Window('To Do List Example', layout)
    event, values = window.read()

def test14():
    import PySimpleGUI as sg
    import matplotlib.pyplot as plt

    """
        Simultaneous PySimpleGUI Window AND a Matplotlib Interactive Window
        A number of people have requested the ability to run a normal PySimpleGUI window that
        launches a MatplotLib window that is interactive with the usual Matplotlib controls.
        It turns out to be a rather simple thing to do.  The secret is to add parameter block=False to plt.show()
    """

    def draw_plot():
        plt.plot([0.1, 0.2, 0.5, 0.7])
        plt.show(block=False)

    layout = [[sg.Button('Plot'), sg.Cancel(), sg.Button('Popup')]]

    window = sg.Window('Have some Matplotlib....', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        elif event == 'Plot':
            draw_plot()
        elif event == 'Popup':
            sg.popup('Yes, your application is still running')
    window.close()

def test15():
    import PySimpleGUI as sg
    """      
    Demonstrates using a "tight" layout with a Dark theme.      
    Shows how button states can be controlled by a user application.  The program manages the disabled/enabled      
    states for buttons and changes the text color to show greyed-out (disabled) buttons      
    """

    sg.ChangeLookAndFeel('Dark')
    sg.SetOptions(element_padding=(0, 0))

    layout = [[sg.T('User:', pad=((3, 0), 0)), sg.OptionMenu(values=('User 1', 'User 2'), size=(20, 1)),
               sg.T('0', size=(8, 1))],
              [sg.T('Customer:', pad=((3, 0), 0)), sg.OptionMenu(values=('Customer 1', 'Customer 2'), size=(20, 1)),
               sg.T('1', size=(8, 1))],
              [sg.T('Notes:', pad=((3, 0), 0)), sg.In(size=(44, 1), background_color='white', text_color='black')],
              [sg.Button('Start', button_color=('white', 'black'), key='Start'),
               sg.Button('Stop', button_color=('white', 'black'), key='Stop'),
               sg.Button('Reset', button_color=('white', 'firebrick3'), key='Reset'),
               sg.Button('Submit', button_color=('white', 'springgreen4'), key='Submit')]
              ]

    window = sg.Window("Time Tracker", layout, default_element_size=(12, 1), text_justification='r',
                       auto_size_text=False, auto_size_buttons=False, default_button_element_size=(12, 1),
                       finalize=True)

    window['Stop'].update(disabled=True)
    window['Reset'].update(disabled=True)
    window['Submit'].update(disabled=True)
    recording = have_data = False
    while True:
        event, values = window.read()
        print(event)
        if event == sg.WIN_CLOSED:
            exit(69)
        if event == 'Start':
            window['Start'].update(disabled=True)
            window['Stop'].update(disabled=False)
            window['Reset'].update(disabled=False)
            window['Submit'].update(disabled=True)
            recording = True
        elif event == 'Stop' and recording:
            window['Stop'].update(disabled=True)
            window['Start'].update(disabled=False)
            window['Submit'].update(disabled=False)
            recording = False
            have_data = True
        elif event == 'Reset':
            window['Stop'].update(disabled=True)
            window['Start'].update(disabled=False)
            window['Submit'].update(disabled=True)
            window['Reset'].update(disabled=False)
            recording = False
            have_data = False
        elif event == 'Submit' and have_data:
            window['Stop'].update(disabled=True)
            window['Start'].update(disabled=False)
            window['Submit'].update(disabled=True)
            window['Reset'].update(disabled=False)
            recording = False

def delib_error():
    import PySimpleGUI as sg

    def main():
        sg.set_options(suppress_raise_key_errors=False, suppress_error_popups=False, suppress_key_guessing=False)

        layout = [[sg.Text('My Window')],
                  [sg.Input(k='-IN-'), sg.Text(size=(12, 1), key='-OUT-')],
                  [sg.Button('Go'), sg.Button('Exit')]]

        window = sg.Window('Window Title', layout, finalize=True)

        while True:  # Event Loop
            event, values = window.read()
            print(event, values)
            if event == sg.WIN_CLOSED or event == 'Exit':
                break
# this is a deliberate error
            window['-O U T-'].update(values['-IN-'])
        window.close()

    def func():

        main()

    func()

def tree():
    treedata = sg.TreeData()

    treedata.Insert("", '_A_', 'A', [1, 2, 3])
    treedata.Insert("", '_B_', 'B', [4, 5, 6])
    treedata.Insert("_A_", '_A1_', 'A1', ['can', 'be', 'anything'])

    layout = [[sg.Text('My Window')],
              [treedata],
              [sg.Input(k='-IN-'), sg.Text(size=(12, 1), key='-OUT-')],
              [sg.Button('Go'), sg.Button('Exit')]]

    window = sg.Window('Window Title', layout, finalize=True)

    while True:  # Event Loop
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        # this is a deliberate error
#        window['-O U T-'].update(values['-IN-'])
    window.close()


def slider():
    # Testing async window, see if can have a slider
    # that adjusts the size of text displayed

    import PySimpleGUI as sg
    fontSize = 12
    layout = [[sg.Spin([sz for sz in range(6, 172)], font=('Helvetica 20'), initial_value=fontSize, change_submits=True,
                       key='spin'),
               sg.Slider(range=(6, 172), orientation='h', size=(10, 20),
                         change_submits=True, key='slider', font=('Helvetica 20')),
               sg.Text("Aa", size=(2, 1), font="Helvetica " + str(fontSize), key='text')]]

    sz = fontSize
    window = sg.Window("Font size selector", layout, grab_anywhere=False)
    # Event Loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        sz_spin = int(values['spin'])
        sz_slider = int(values['slider'])
        sz = sz_spin if sz_spin != fontSize else sz_slider
        if sz != fontSize:
            fontSize = sz
            font = "Helvetica " + str(fontSize)
            window['text'].update(font=font)
            window['slider'].update(sz)
            window['spin'].update(sz)

    print("Done.")

# test1()
# test2()
# test3()
# test4()
test5()
# test6()
# test7()
# test8()
# test9()
# test10()
# test11()
# test12()
# test13()
# test14()
# test15()
# delib_error()
# tree()
# slider()