# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import json as Json
import logging
import os
import threading
from functools import partial
from math import ceil, gcd
from time import sleep
from tkinter import HORIZONTAL, Frame, IntVar, StringVar, X, ttk

from .copy_manager import CopyManager
from .image_browser import ImageBrowser
from .utils import (B_to_readable, create_popup, create_progress_popup,
                    dir_size_bytes, umount2)

CONFIG_FILE = './config.json'
MEDIA_FOLDER = '/media/'
USB_CP_DIR = 'OpenMicroView_Pictures'
LICENSE = 'OpenMicroView - Copyright © 2023 V. Salvadori'


class Settings:
    """ Application Settings """
    def __init__(self, microscope, app):
        self.microscope = microscope
        self.camera     = microscope.camera
        self.images_path = self.camera.getImagePath()
        self.light      = microscope.light
        self.frame      = None
        self.app        = app
        self.cam_res    = StringVar()
        self.curRes     = self.camera.camera.resolution
        self.btn        = {'saveConfig':None, 'loadConfig':None}
        self.cp_dev     = StringVar()
        self.frame_cp   = None
        self.frame_mv   = None
        self.loading_frame = None
        self.copy_manager  = CopyManager()
        self.copy_thread   = None
        self.number_imgs   = StringVar()
        self.number_tls    = StringVar()
        self.size_files    = StringVar()

    def initPanel(self, frame:Frame):
        ''' Initialise setting panel.'''
        self.frame = frame
        for col in range(0, 3):
            frame.grid_columnconfigure(col, weight=1, pad=1)
        for row in range(0, 6):
            frame.grid_rowconfigure(row, weight=1, pad=2)
        frame.grid_columnconfigure(1, minsize=150)
        res = self.camera.camera.resolution
        self.cam_res.set(f"{res[0]}x{res[1]} ({self.resolutionRatio(res)})")

        # Title
        ttk.Label(frame, text='Settings', style='title.TLabel').grid(column=0,
                                                                     row=0,
                                                                     sticky='nsew')
        # Exit Button
        ttk.Button(frame, text="Back", command=self.app.hide_settings,
                   style='config.TButton').grid(column=4,
                                                row=0,
                                                columnspan=2,
                                                sticky='nse')

        # Resolution Selector
        ttk.Label(frame, text='Camera Res.:').grid(column=0, row=1, rowspan=2)
        ttk.Label(frame, textvariable=self.cam_res).grid(column=1, row=1)
        res_selector = ttk.Scale(frame, from_=0, to=4, orient=HORIZONTAL,
                                 command=self.selectResolution)
        res_selector.grid(column=1, columnspan=2, row=2, sticky='nsew')

        # Snapshot Path
        self.images_path = self.camera.getImagePath()
        ttk.Label(frame, text="Images are saved in:").grid(column=0, row=5, sticky='sw')
        ttk.Label(frame, text=self.images_path).grid(column=0, row=6, columnspan=2, sticky='nw')

        lic = ttk.Label(frame, text=LICENSE)
        lic.bind('<Button-1>', self.show_license)
        lic.grid(column=0, row=9, columnspan=2, sticky='sw')

        # Picture management
        self.mvcp_frame = None
        self.load_copy_settings_section()
        ttk.Label(self.mvcp_frame, text="Manage pictures", style='TLabel').grid(row=0,
                                                                                sticky='news')
        tabs = ttk.Notebook(self.mvcp_frame)

        ''' TAB DETAILS'''
        self.tab_details = ttk.Frame(tabs)
        self.tab_details.grid_columnconfigure(0, weight=1)
        self.tab_details.grid_rowconfigure(list(range(5)), weight=1)
        ttk.Label(self.tab_details, textvariable=self.number_imgs, justify='left').grid(row=0, sticky='news')
        ttk.Label(self.tab_details, textvariable=self.number_tls, justify='left').grid(row=1, sticky='news')
        ttk.Label(self.tab_details, textvariable=self.size_files, justify='left').grid(row=2, sticky='news')
        browse_btn = ttk.Button(self.tab_details, text="Browse Pictures",
                                style='TButton',
                                command=self.image_browser)
        browse_btn.grid(row=4, sticky='ews')
        tabs.add(self.tab_details, text="Details", sticky='news', padding=20)

        ''' TAB: COPY '''
        self.tab_cp = ttk.Frame(tabs)
        self.tab_cp.grid_columnconfigure([0, 1], weight=1)
        self.tab_cp.grid_rowconfigure([0, 2], weight=1)
        self.tab_cp.grid_rowconfigure(1, weight=2)
        ttk.Button(self.tab_cp, text='↻ Refresh list', style='config.TButton',
                   command=self.refreshDevicesList).grid(row=0, columnspan=2,
                                                         ipadx=10, pady=10, sticky="N")
        self.cp_btn = ttk.Button(self.tab_cp, text="Copy All",
                                 style='config.TButton', state=['disabled'])
        self.cp_btn.grid(row=2, column=0, padx=10, pady=15, sticky='SEW')
        self.cp_btn.bind('<Button 1>', self.trigger_copy)

        self.ejct_btn = ttk.Button(self.tab_cp, text="Eject",
                                   style='config.TButton', state=['disabled'],
                                   command=self.eject_usb)
        self.ejct_btn.grid(row=2, column=1, padx=10, pady=15, sticky='SEW')

        self.refreshDevicesList()
        tabs.add(self.tab_cp, text="Copy", sticky='WE')

        ''' TAB: DELETE'''
        self.tab_del = ttk.Frame(tabs)
        self.tab_del.grid_columnconfigure(0, weight=1)
        self.del_btn = ttk.Button(self.tab_del, text="Delete all pictures",
                                  style='del.TButton',
                                  command=self.confirm_delete_pictures)
        self.del_btn.grid(row=1, padx=10, pady=10, ipadx=10, ipady=5)
        tabs.add(self.tab_del, text="Delete", sticky='WE')

        tabs.grid(sticky='news', ipadx=25, ipady=10)

        # SAVE / RELOAD Settings
        ttk.Label(frame, text="Light/Camera configuration:").grid(column=4, columnspan=2, row=1)
        self.btn['saveConf'] = ttk.Button(frame, text='Save',
                                          style='config.TButton',
                                          command=self.btnSaveConfig)
        self.btn['saveConf'].grid(column=4, columnspan=1, row=2, padx=10, sticky='news')
        self.btn['loadConf'] = ttk.Button(frame, text='Load',
                                          style='config.TButton',
                                          command=self.btnLoadConfig)
        self.btn['loadConf'].grid(column=5, columnspan=1, row=2, padx=10, sticky='news')

    def update_stats(self):
        def _f():
            files = os.listdir(self.images_path)
            n_imgs = 0
            n_tl = 0
            for f in files:
                if f.split('.')[-1] in ['jpg', 'jpeg']:
                    n_imgs += 1
                elif f[0:3] == 'TL_':
                    n_tl += 1
            self.number_imgs.set(f'{n_imgs} single shot pictures')
            self.number_tls.set(f'{n_tl} timelapses')
            s = dir_size_bytes(self.images_path)
            self.size_files.set(f'{B_to_readable(s)} used')
        threading.Thread(name='FilesStats', target=_f, args=()).start()

    def image_browser(self):
        browser = ImageBrowser(path=self.images_path)
        browser.start()

    def load_copy_settings_section(self):
        if (self.mvcp_frame is None):
            self.mvcp_frame = ttk.Frame(self.frame, height=60)
        self.mvcp_frame.grid(column=3, row=6, columnspan=3, rowspan=4,
                             sticky='news')
        self.mvcp_frame.grid_propagate(1)

    def btnSaveConfig(self):
        ''' Called from Button Save config '''
        self.btn['saveConf'].state(['disabled'])
        self.btn['loadConf'].state(['disabled'])
        self.saveConfig()
        self.btn['saveConf'].state(['!disabled'])
        self.btn['loadConf'].state(['!disabled'])

    def btnLoadConfig(self):
        ''' Called from btn Load Config: Reset the configuration to the config file '''
        self.btn['saveConf'].state(['disabled'])
        self.btn['loadConf'].state(['disabled'])
        self.loadConfig()
        self.btn['saveConf'].state(['!disabled'])
        self.btn['loadConf'].state(['!disabled'])

    def selectResolution(self, r):
        ''' Callback by scale object to select the Resolution '''
        r = round(float(r))
        res = {0:(800, 480), 1:(1296, 730), 2:(1296, 972),
               3:(1920, 1080), 4:(2592, 1944), 5:(3280, 2464)}
        resolutions = {k: f"{x}x{y} ({int(x / gcd(x, y))}:{int(y / gcd(x, y))}) "
                       for k, (x, y) in res.items()}

        if r not in resolutions:
            logging.error('Resolution out of range')
            return False
        self.cam_res.set(resolutions[r])

        current = self.curRes
        new = res[r]
        if (current != new):
            self.camera.videoQueue.put(new)
            self.curRes = new
        return True

    def resolutionRatio(self, r:tuple) -> str:
        ''' return a string representing the resolution ratio (e.g. 16:9) '''
        x, y = int(r[0]), int(r[1])
        div = gcd(x, y)
        return f'{int(x / div)}:{int(y / div)}'

    def saveConfig(self):
        """ Get current config and save it to CONFIG_FILE """
        logging.info('Saving configuration...')
        settings = self.getConfig()
        json_config = Json.dumps(settings)
        with open(CONFIG_FILE, 'w') as f:
            f.write(json_config)

    def loadConfig(self):
        """ Load Config from CONFIG_FILE and apply it """
        logging.info('Reloading configuration...')
        try:
            with open(CONFIG_FILE, 'r') as f:
                json_config = f.read()
            settings = Json.loads(json_config)
            self.setConfig(settings)
        except OSError:
            create_popup(text="Impossible to load config.", close_btn="Ok")
            logging.error(f'Error while loading {CONFIG_FILE}.', exc_info=True)

    def getConfig(self) -> dict:
        """ Returns current config in a dictionnary """
        return ({
            'light': self.light.getColors(),
            'camera':{
                'brightness': self.camera.brightness(),
                'contrast': self.camera.contrast(),
                'sharpness': self.camera.sharpness(),
                'saturation': self.camera.saturation()
            }
        })

    def setConfig(self, config:dict):
        ''' Apply the Config passed in parameter '''
        if ('light' in config):
            for c in ['r', 'g', 'b', 'w']:
                if c in config['light'] and (0 <= int(config['light'][c]) <= 255):
                    self.light.setColor(c, int(config['light'][c]))
            self.light.reload()  # Apply changes
        if ('camera' in config):
            camConf = config['camera']
            if 'brightness' in camConf:
                self.camera.brightness(camConf['brightness'])
            if 'contrast' in camConf:
                self.camera.contrast(camConf['contrast'])
            if 'sharpness' in camConf:
                self.camera.sharpness(camConf['sharpness'])
            if 'saturation' in camConf:
                self.camera.saturation(camConf['saturation'])

    def refreshDevicesList(self):
        ''' Display the new usb devices List '''
        self.refreshStorages()
        if self.frame_cp is not None:
            self.frame_cp.destroy()
        self.cp_btn.state(['disabled'])
        self.ejct_btn.state(['disabled'])

        self.frame_cp = ttk.Frame(self.tab_cp)
        self.frame_cp.grid(row=1, columnspan=2, sticky='new', ipady=20)
        for d in self.storages:
            # Add a line with detected usb devices, on click trigger mvcp_selection
            ttk.Radiobutton(self.frame_cp, text=d,
                            command=self.mvcp_selection,
                            variable=self.cp_dev, value=d).pack(fill=X)
        if not self.storages:
            self.noUSB = ttk.Label(self.frame_cp, text="No USB device Connected.")
            self.noUSB.pack(fill='both', padx=20)
        # also refresh stats
        self.update_stats()

    def refreshStorages(self):
        ''' Add the USB Storage devices to self.storages '''
        self.storages = []
        self.cp_dev.set("")
        # Browse /media/*
        for _dir in os.listdir(MEDIA_FOLDER):
            abs_path = os.path.join(MEDIA_FOLDER, _dir)
            if os.path.isdir(abs_path):
                # Browse /media/$username/*
                for usb in os.listdir(abs_path):
                    if (os.lstat(os.path.join(abs_path, usb)).st_uid != 0):
                        self.storages.append(os.path.join(_dir, usb))

    def mvcp_selection(self):
        ''' Activate or deactivate the Copy Button after a change '''
        if self.cp_dev.get() != '' and not self.copy_manager.isrunning():
            self.cp_btn.state(['!disabled'])
            self.ejct_btn.state(['!disabled'])
        else:
            self.cp_btn.state(['disabled'])
            self.ejct_btn.state(['disabled'])

    ''' DELETE PICTURES '''
    def confirm_delete_pictures(self):
        logging.info('Triggered deletion of Pictures')
        self.del_btn.state(['disabled'])
        total = self.number_imgs.get()
        if total == 0:
            create_popup(text='There is currently no picture stored locally.',
                         close_btn='Ok', raise_over=self.frame)
            self.del_btn.state(['!disabled'])
            return None
        popup = create_popup(text=f'This will delete all {total} currently stored locally.\nAre you sure ?',
                             raise_over=self.frame, cols=2,
                             accept_btn='Delete All',
                             accept_callback=self.delete_pictures)

        ok_btn = ttk.Button(popup, text='Delete All', style='config.TButton',
                            command=partial(self.delete_pictures, popup))

        ok_btn.grid(row=1, column=1, sticky='NS', ipadx=50, pady=10)

        close_btn = ttk.Button(popup, text='Cancel', style='config.TButton',
                               command=(lambda: [self.del_btn.state(['!disabled']), popup.destroy()]))
        close_btn.grid(row=1, column=0, sticky='NS', ipadx=50, pady=10)

    def delete_pictures(self, popup):
        logging.info("Deleting Pictures..")
        popup.destroy()
        path = self.images_path
        files = [f for f in os.listdir(path) if f.split('.')[-1] in ['jpeg', 'jpg', 'png']]
        total = len(files)
        progress = IntVar(0)
        status = StringVar("")
        i = 0
        if total <= 0:
            logging.warning('No Files to delete.')
            return None
        logging.info(f'Deleting {total} files...')
        popup = create_progress_popup(text=f'Deleting {total} files...',
                                      raise_over=self.frame,
                                      variable=progress,
                                      status_var=status,
                                      maximum=total)
        self.app.master.update()
        sleep(0.5)
        refresh_rate = ceil(total / 250)
        for file in files:
            i += 1
            if i % refresh_rate == 0:
                progress.set(i)
                status.set(f"{i}/{total}")
                self.app.master.update()
            os.remove(os.path.join(path, file))
        sleep(0.5)
        popup.destroy()
        create_popup(text='All images have been deleted.',
                     close_btn='Ok', raise_over=self.frame)
        self.del_btn.state(['!disabled'])
        self.update_stats()

    ''' EJECT USB '''
    def eject_usb(self):
        if self.copy_manager.isrunning():
            logging.error("The copy manager is already happening.")
            return False
        target = os.path.join(MEDIA_FOLDER, str(self.cp_dev.get()))
        try:
            umount2(target)
        except OSError as e:
            create_popup("Cancel",
                         f"Impossible to eject device, try again later:\n Error: {os.strerror(e.errno)}")
            logging.error('Error while ejecting device.', exc_info=True)
        self.refreshDevicesList()

    def show_license(self, event=None):
        license = ("OpenMicroView - Copyright (C) 2023 V. Salvadori\n\n"
                   + "This program is distributed under GNU General Public License v3 and\n"
                   + "comes with ABSOLUTELY NO WARRANTY. This is a free software.\n"
                   + "You are welcome to redistribute it under certain conditions.\n\n"
                   + "For details read the LICENSE file included in this project.")
        create_popup(close_btn='Close', text=license)

    ''' COPY PICTURES '''
    def trigger_copy(self, event):
        self.update_stats()
        if self.copy_manager.isrunning():
            logging.error("Copy already happening.")
            return False
        target = os.path.join(MEDIA_FOLDER, str(self.cp_dev.get()), USB_CP_DIR)
        self.copy_manager.source = self.images_path
        self.copy_manager.dest = target
        self.show_popup_copying()
        logging.info(f"Starting copy to USB '{target}'...")
        self.copy_thread = threading.Thread(name='copyThread', target=self.start_copy, args=())
        self.copy_thread.start()
        return True

    def show_popup_copying(self):
        logging.info('Copying pictures to USB...')
        total = dir_size_bytes(self.images_path)
        popup = create_progress_popup(text=f'Copying {B_to_readable(total)}...',
                                      raise_over=self.frame,
                                      variable=self.copy_manager.progress_value,
                                      status_var=self.copy_manager.transfered_size_str,
                                      maximum=total)
        self.loading_frame = popup

    def show_popup_copied(self):
        self.loading_frame.destroy()
        self.loading_frame = None
        create_popup(text='All images have been copied.',
                     close_btn='Ok', raise_over=self.frame)
        self.update_stats()
        return 0

    # @THREADED
    def start_copy(self):
        self.cp_btn.state(['disabled'])
        self.ejct_btn.state(['disabled'])
        logging.info("Thread: Starting copy...")
        self.copy_manager.execute()
        self.show_popup_copied()
        logging.info("Thread: Copy done.")
        self.copy_thread = None
