# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
from tkinter import CENTER, FLAT

from ttkthemes import ThemedStyle


def configure_style(master) -> ThemedStyle:
    FONT_NAME = 'Quicksand'
    gui_style = ThemedStyle(master=master)
    gui_style.theme_use('classic')
    logging.debug(gui_style.theme_names())
    
    gui_style.configure('.', font=(FONT_NAME, 12), foreground='black', background='white', padding=1)
    # LABELS
    gui_style.configure('TLabel', font=(FONT_NAME, 12), foreground='black', background='white')
    gui_style.configure('title.TLabel', font=(FONT_NAME, 18), foreground='black', background='white')
    gui_style.configure('tlvalue.TLabel', font=('Noto Mono', 20), foreground='black', background='white',
                        justify=CENTER, padding=5)
    gui_style.configure('H1.TLabel', font=['Lato', '-60'], background='#ffffff')
    # BUTTONS
    
    gui_style.configure('TButton', font=(FONT_NAME, 18), background="#FEFEFE", bordercolor='darkgrey',
                        borderwidth=1, relief=FLAT, padding=5) # inside padding
    gui_style.configure('close.TButton', font=(FONT_NAME, 18), background="#EFEEEE", relief=FLAT, padding=5)
    gui_style.configure('control.TButton', font=(FONT_NAME, 24), background="#FFFFFF", relief=FLAT, padding=5)
    gui_style.configure('config.TButton', font=(FONT_NAME, 12), background="#FEFEFE", relief=FLAT, padding=3)
    gui_style.configure('time.TButton', font=(FONT_NAME, 15), background="#FFFFFF", relief=FLAT, padding=5)
    gui_style.configure('del.TButton', font=(FONT_NAME, 15), background="#FFDDDD", relief=FLAT, padding=2)
    gui_style.configure('shutdown.TButton', font=(FONT_NAME, 12), background="#FFDDDD", relief=FLAT, padding=3)

    # NOTEBOOK
    # gui_style.layout("TNotebook", [])
    gui_style.configure('TNotebook.Tab', font=(FONT_NAME, 15), background="lightgray", padding=5,
                        bordercolor='#FF0000')
    gui_style.map('TNotebook.Tab', background=[('selected', 'white')] )
    gui_style.configure('TNotebook', padding=5, tabmargins=0)
    # CHECKBOXES / RADIO BUTTONS
    gui_style.configure('TCheckbutton', font=(FONT_NAME, 12), background="white", relief=FLAT, indicatorrelief=FLAT,
                        indicatormargin=3, padding=10)
    gui_style.configure('TRadiobutton', font=(FONT_NAME, 12), background="white", relief=FLAT, indicatorrelief=FLAT,
                        indicatormargin=3, padding=10)
    # TSCALE
    gui_style.configure('Horizontal.TScale', font=(FONT_NAME, 20), sliderthickness=30, relief=FLAT, padding=10)
    gui_style.configure('Horizontal.Player.TScale', font=(FONT_NAME, 12), sliderthickness=15, relief=FLAT, padding=5)
    # FRAME
    gui_style.configure('default.TFrame', background='#ffffff')
    # Progressbar
    gui_style.configure("Horizontal.TProgressbar", background="lightblue", troughcolor="white",
                        bordercolor="darkblue", lightcolor="lightblue", darkcolor="darkblue")

    return gui_style
