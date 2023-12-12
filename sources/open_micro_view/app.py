#!/usr/bin/python3
# coding: utf-8
# ####################
#
# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from functools import partial
from tkinter import FLAT, HORIZONTAL, VERTICAL, Frame, StringVar, Tk, ttk
import logging

from .assets.icons import (BLUE_DOT, BRIGHTNESS_ICON, COLOR_ICON,
                           CONTRAST_ICON, GREEN_DOT, INFO_FPS, INFO_RES,
                           INFO_TEMP, LIGHT_ICON, RED_DOT, WHITE_DOT, icon)
from .assets.theme import configure_style
from .image_browser import ImageBrowser
from .microscope import Microscope
from .settings import Settings
from .timelapse import Timelapse

WIN_X = 800
WIN_Y = 480


class App(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg='white')
        self.show_fullframe(self)
        self.master.title("OpenMicroView")
        self.master.minsize(WIN_X, WIN_Y)
        self._geom = '200x200+0+0'
        master.geometry(f"{WIN_X}x{WIN_Y}+0+0")
        ## INIT STYLES
        configure_style(master)
         
        self.initialize_tab_list()
        

        ## Setup Camera Frame
        self.cameraFrame = Frame(self.mainFrame, borderwidth=2, relief=FLAT, bg='white', padx=1,
                                 pady=1, width=510, highlightcolor='red')
        # self.cameraFrame.place(anchor='c', )
        self.cameraFrame.grid_propagate(True)
        self.cameraFrame.grid(column=0, row=0, sticky="nswe")

        ## Create Microscope Object
        self.microscope = Microscope(master, self.cameraFrame)
        
        # Setup Settings Frame and Init Settings Panel
        self.settings =  Settings(self.microscope, self)
        self.settingsFrame = Frame(self, bg='white', padx=10, pady=10, relief=FLAT)
        self.settings.initPanel(self.settingsFrame)
        
        # Setup Timelapse Tab
        self.timelapse = Timelapse(self.microscope, self)
        self.timelapse.initTimelapseTab(self.tab3)
        
        ## Display Informations
        infoFrame = Frame(self.mainFrame, bg='white', padx=10, pady=10)
        infoFrame.grid(row=1, columnspan=2, sticky='news')
        # - Temperature
        icon(INFO_TEMP, infoFrame).grid(row=1, column=0, sticky='e')
        ttk.Label(infoFrame, textvar=self.microscope.temperature, width=4, anchor='e').grid(row=1,
                                                                                        column=1,
                                                                                        sticky='w')
        ttk.Separator(infoFrame, orient=VERTICAL).grid(row=1, column=2, sticky="ns", padx=15, pady=5)
        # - FPS
        icon(INFO_FPS, infoFrame).grid(row=1, column=3, sticky='e')
        ttk.Label(infoFrame, textvar=self.microscope.camera.i_fps, width=2, anchor='e').grid(row=1,
                                                                                         column=4,
                                                                                         sticky='e')
        ttk.Label(infoFrame, text="fps").grid(row=1, column=5, sticky='w')
        # - Screen Size
        ttk.Separator(infoFrame, orient=VERTICAL).grid(row=1, column=6, sticky="ns", padx=15, pady=5)
        icon(INFO_RES, infoFrame).grid(row=1, column=7, sticky='e')
        ttk.Label(infoFrame, textvar=self.settings.cam_res).grid(row=1, column=8)
        infoFrame.grid_columnconfigure(20, weight=1)

        # Browse Pictures Button
        start_img_browser = ImageBrowser(path=self.microscope.camera.getImagePath()).start
        browse_btn = ttk.Button(infoFrame,
                                text="Browse Pictures",
                                style='config.TButton',
                                command= start_img_browser)
        browse_btn.grid(row=1, column=20, sticky='nse', padx=15)

        # Settings Button
        self.buttonSettings = ttk.Button(infoFrame, text="Settings", style='config.TButton',
                                         command=self.showSettings)
        self.buttonSettings.grid(row=1, column=21, sticky='nsew', padx=15)
        
        # Setup Light Settings Tab
        light_setup = Frame(self.tab1, relief=FLAT, bg='white')
        light_setup.pack(fill='both')
        self.init_light_settings(light_setup)
        # Setup Camera Settings Tab
        camera_setup = Frame(self.tab2, relief=FLAT, bg='white')
        camera_setup.pack(fill='both')
        self.init_camera_settings(camera_setup)
        
        self.master.wm_title("Mini-Microscope by IMT")
        self.master.wm_protocol("WM_DELETE_WINDOW", self.close)

    def initialize_tab_list(self):
        ## Setup Different Tabs
        self.mainFrame = Frame(self)
        self.mainFrame.grid_columnconfigure(1, weight=1)
        self.mainFrame.grid_rowconfigure(0, weight=10)
        self.mainFrame.grid_rowconfigure(1, weight=1)
        self.show_fullframe(self.mainFrame)
        self.tabs = ttk.Notebook(self.mainFrame)
        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)
        self.tab3 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab1, text="Light")
        self.tabs.add(self.tab2, text="Camera")
        self.tabs.add(self.tab3, text="Timelapse")
        self.tabs.grid(column=1, row=0, sticky="news") # outside margin
        self.tab1.grid_columnconfigure(1, weight=80)
        self.tab1.grid_columnconfigure(2, weight=80)
        self.tab1.grid_rowconfigure(1, weight=1)

    # LIGHT TAB
    def init_light_settings(self, tab):
        tab.grid_columnconfigure(1, weight=3)
        self.toggler = StringVar()
        self.update_text_brightness()
        ttk.Button(tab, textvar=self.toggler,
                   command=self.light_toggle).grid(row=1, columnspan=2, 
                                                   pady=10, padx=10, sticky='news')
        
        icon(LIGHT_ICON, tab).grid(row=2, column=0, sticky='e')
        self.br = ttk.Scale(tab, from_=0, to=100, 
                            variable=self.microscope.light.brightness, 
                            orient=HORIZONTAL, 
                            command=self.setBrightness)
        self.br.set(self.microscope.light.getBrightness())
        self.br.grid(row=2, column=1, sticky='we', padx=10, pady=10)
        
        ttk.Separator(tab, orient=HORIZONTAL).grid(row=3, columnspan=2, sticky="ew", padx=15, pady=2)
        
        icons = [RED_DOT, GREEN_DOT, BLUE_DOT, WHITE_DOT]
        for i, c in enumerate("rgbw"):
            sc = ttk.Scale(tab, from_=0, to=255, 
                           variable=self.microscope.light.color[c],
                           orient=HORIZONTAL,
                           command=partial(self.microscope.light.setColor, c))
            sc.set(self.microscope.light.getColor(c))
            sc.grid(row=4+i, column=1, sticky='we', padx=10, pady=10)
            icon(icons[i], tab).grid(row=i+4, column=0, sticky='e')
        
    # CAMERA TAB
    def init_camera_settings(self, tab):
        tab.grid_columnconfigure(1, weight=3)
        ttk.Button(tab, text="Capture Image",
                   command= self.microscope.camera.takeSnapshot).grid(row=0, columnspan=2, pady=10,
                                                                      padx=10, sticky='news')
        icon(COLOR_ICON, tab).grid(row=7, column=0, sticky='e')
        icon(CONTRAST_ICON, tab).grid(row=5, column=0, sticky='e')
        icon(BRIGHTNESS_ICON, tab).grid(row=4, column=0, sticky='e')
        
        br = ttk.Scale(tab, from_=10,  to=90,  orient=HORIZONTAL,
                       command=self.microscope.camera.brightness)
        co = ttk.Scale(tab, from_=-50, to=100, orient=HORIZONTAL,
                       command=self.microscope.camera.contrast)
        sa = ttk.Scale(tab, from_=-100, to=100, orient=HORIZONTAL,
                       command=self.microscope.camera.saturation)


        br.set(self.microscope.camera.brightness())
        co.set(self.microscope.camera.contrast())
        sa.set(self.microscope.camera.saturation())
        
        br.grid(row=4, column=1, sticky='we', padx=10, pady=10)
        co.grid(row=5, column=1, sticky='we', padx=10, pady=10)
        sa.grid(row=7, column=1, sticky='we', padx=10, pady=10)

    def show_fullframe(self, pack:Frame, unpack:Frame=None):
        if unpack:
            unpack.pack_forget()
        pack.pack(fill='both', expand=True,ipadx=WIN_X/2, ipady=WIN_Y/2)


    def showSettings(self):
        self.show_fullframe(pack=self.settingsFrame, unpack=self.mainFrame)
        self.microscope.camera.stopVideo()
        self.settings.update_stats()
        
    def hideSettings(self):
        self.show_fullframe(pack=self.mainFrame , unpack=self.settingsFrame)
        self.microscope.camera.startVideo()
        
    # Needed by subclass Timelapse
    def timelapseStarted(self):
        self.tabs.state(['disabled'])
        self.buttonSettings.state(['disabled'])
        
    def timelapseStopped(self):
        self.tabs.state(['!disabled'])
        self.buttonSettings.state(['!disabled'])
    
    # Update Button Light
    def update_text_brightness(self):
        br = self.microscope.light.getBrightness()
        self.toggler.set(f"Switch {'OFF' if br > 0 else 'ON'}")

    # Toggle Light ON/OFF
    def light_toggle(self):
        self.microscope.light.toggle()
        self.update_text_brightness()
        self.br.set(int(self.microscope.light.getBrightness()*100))

    def setBrightness(self, n):
        self.microscope.light.setBrightness(n)
        self.update_text_brightness()
    
    def close(self):
        self.microscope.close()
        self.master.quit()

def start():
    root = Tk()
    root.attributes("-fullscreen", True)
    root.config(cursor="circle")
    try:
        app = App(root)
        app.mainloop()
    except KeyboardInterrupt:
        logging.error(' << Received Keyboard Interrupt')
        logging.error('    Shutting down...')
        if app: app.close()

if __name__ == '__main__':
    start()