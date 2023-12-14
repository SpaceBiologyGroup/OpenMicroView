# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import os
import threading
from datetime import datetime, timedelta
from functools import partial
from queue import Queue
from time import sleep
from tkinter import HORIZONTAL, IntVar, StringVar, ttk

from picamera.exc import PiCameraRuntimeError
from PIL import Image, ImageTk

from .utils import time_str

# Switch Light on before x sec at each Timelapse picture
AUTOLIGHT_INTERVAL = 3

# Minimum interval to automatically switch off the light
MIN_INTERVAL_AUTOLIGHT = 15


class Timelapse:
    """ Allow user to capture a timelapse"""
    def __init__(self, microscope, root_app):
        self.light = microscope.light
        self.camera = microscope.camera
        self.root_app = root_app
        self.time = {'s': 0, 'm': 0, 'h': 0}
        self.value = IntVar()
        self.s_auto_stop = StringVar()
        self.t_auto_stop = StringVar()
        self.auto_stop = 0
        self.mode = None
        self.interval = StringVar()
        self.max = {'s': 59, 'm': 59, 'h': 24}
        self.btn = {'s': None, 'm': None, 'h': None}
        self.timelapse_frame = None
        self.next_frame = StringVar()
        self.last_frame = StringVar()
        self.remaining = StringVar()
        self.total_seconds = 0
        self.stop_event = threading.Event()
        self.timelapse_queue = Queue()
        self.light_brightness = 0
        self.light_status = 0
        self.container = None
        self.tab = None
        self.thread = None

    def init_timelapse_tab(self, container):
        self.container = container
        self.tab = tab = ttk.Frame(container)
        self.timelapse_frame = ttk.Frame(container)
        self.init_timelapse_frame()
        tab.pack(fill='both')
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_columnconfigure(2, weight=1)
        # LINE 0
        self.btn['s'] = ttk.Button(tab, text='Sec.', style='time.TButton',
                                   command=partial(self.change_mode, 's'))
        self.btn['s'].grid(column=0, row=0, sticky='news', padx=5, pady=5)
        self.btn['m'] = ttk.Button(tab, text='Min.', style='time.TButton',
                                   command=partial(self.change_mode, 'm'))
        self.btn['m'].grid(column=1, row=0, sticky='news', padx=5, pady=5)
        self.btn['h'] = ttk.Button(tab, text='Hou.', style='time.TButton',
                                   command=partial(self.change_mode, 'h'))
        self.btn['h'].grid(column=2, row=0, sticky='news', padx=5, pady=5)

        # LINE 1
        ttk.Label(tab, textvar=self.value,
                  style='tlvalue.TLabel').grid(column=0, row=1, sticky='nes',
                                               padx=5, pady=5)
        self.value.set(0)
        ttk.Button(tab, text='-',
                   style='control.TButton',
                   command=self.value_minus).grid(column=1, row=1, sticky='news',
                                                 padx=5, pady=5)
        ttk.Button(tab, text='+', style='control.TButton', command=self.value_plus
                   ).grid(column=2, row=1, sticky='news', padx=5, pady=5)
        # LINE 3
        ttk.Label(tab, text='Interval:').grid(column=0, row=3, sticky='news')
        ttk.Label(tab, textvar=self.interval).grid(column=1, row=3, columnspan=2, sticky='news')
        self.interval.set('00:00:00')
        # LINE 4
        ttk.Separator(tab, orient=HORIZONTAL).grid(column=0, row=4, columnspan=3, padx=10, pady=2)
        # LINE 5
        ttk.Label(tab, textvar=self.t_auto_stop).grid(column=0, row=5, columnspan=3, sticky='news', pady=5)

        # LINE 6
        # Automatically stop after x photos (∞)
        ttk.Label(tab, textvar=self.s_auto_stop,
                  style='tlvalue.TLabel').grid(column=0, row=6, sticky='nes', padx=5, pady=5)
        self.refresh_auto_stop()
        ttk.Button(tab, text='-',
                   style='control.TButton',
                   command=self.stop_minus).grid(column=1, row=6, sticky='news', padx=5, pady=5)
        ttk.Button(tab, text='+', style='control.TButton', command=self.stop_plus
                   ).grid(column=2, row=6, sticky='news', padx=5, pady=5)
        # LINE 7 - nothing

        # LINE 8
        self.btn['start'] = ttk.Button(tab, text="Start Timelapse",
                                       command=self.start_timelapse)
        self.btn['start'].grid(column=0, row=8, columnspan=3, padx=5, pady=5)

        # END
        self.change_mode('s')
        self.change_value(0)
        return

    def init_timelapse_frame(self):
        tab = self.timelapse_frame
        tab.grid_columnconfigure(1, weight=1)
        ttk.Label(tab, text='Last:').grid(row=0, column=0, sticky='news')
        ttk.Label(tab, textvar=self.last_frame).grid(row=0, column=1, sticky='news')
        ttk.Label(tab, text='Next:').grid(row=1, column=0, sticky='news')
        ttk.Label(tab, textvar=self.next_frame).grid(row=1, column=1, sticky='news')
        ttk.Label(tab, text='Remains:').grid(row=2, column=0, sticky='news')
        ttk.Label(tab, textvar=self.remaining).grid(row=2, column=1, sticky='news')
        ttk.Separator(tab, orient=HORIZONTAL).grid(row=3, column=0, columnspan=3, padx=30, pady=20)
        self.btn['stop'] = ttk.Button(tab, text="Stop Now",
                                      style='del.TButton',
                                      command=self.stop_timelapse)
        self.btn['stop'].grid(column=0, row=8, columnspan=2, padx=10, pady=10, sticky='news')
        return

    def change_mode(self, mode):
        if self.mode == mode:
            return
        if self.mode is not None:
            self.btn[self.mode].state(["!disabled"])
        self.btn[mode].state(["disabled"])
        self.mode = mode
        self.value.set(self.time[mode])

    def stop_plus(self):
        if self.auto_stop < 100:
            self.auto_stop += 5
        elif self.auto_stop < 500:
            self.auto_stop += 10
        else:
            self.auto_stop += 20
        self.s_auto_stop.set(self.auto_stop)
        self.refresh_auto_stop()

    def stop_minus(self):
        if self.auto_stop <= 5:
            self.auto_stop = 0
        elif self.auto_stop <= 100:
            self.auto_stop -= 5
        elif self.auto_stop <= 500:
            self.auto_stop -= 10
        else:
            self.auto_stop -= 20
        self.refresh_auto_stop()

    def refresh_auto_stop(self):
        if self.auto_stop:
            n = self.total_seconds * (self.auto_stop - 1)
            duration = time_str(n)
            self.s_auto_stop.set(self.auto_stop)
            self.t_auto_stop.set(f'Autostop after {duration}')
        else:
            self.t_auto_stop.set('Stop timelapse manually')
            self.s_auto_stop.set('∞')

    def value_plus(self):
        val = self.value.get() + 1
        if (val > self.max[self.mode]):
            val = 0
        self.change_value(val)

    def value_minus(self):
        val = self.value.get() - 1
        if (val < 0):
            val = self.max[self.mode]
        self.change_value(val)

    def change_value(self, value):
        self.value.set(value)
        self.time[self.mode] = value
        t = self.time
        self.total_seconds = t['s'] + (t['m'] * 60) + (t['h'] * 3600)
        self.interval.set(f"{t['h']} h {t['m']} min {t['s']} sec")
        self.refresh_auto_stop()
        if (self.total_seconds < 5):
            self.btn['start'].state(['disabled'])
        else:
            self.btn['start'].state(['!disabled'])

    def toggle_light(self):
        if self.light_status:
            self.light.set_brightness(0)
            self.light_status = 0
        else:
            self.light.set_brightness(self.light_brightness)
            self.light_status = 1

    def start_timelapse(self):
        self.btn['start'].state(['disabled'])
        self.camera.stopVideo()
        self.tab.pack_forget()
        self.timelapse_frame.pack(fill='both')
        self.thread = threading.Thread(target=self.timelapse_loop,
                                       args=("timelapse-thread", self.timelapse_queue))
        self.stop_event.clear()
        self.thread.start()
        self.root_app.timelapse_started()

    def stop_timelapse(self):
        self.timelapse_queue.put('stop')
        self.camera.startVideo()
        self.tab.pack(fill='both')
        self.timelapse_frame.pack_forget()
        self.root_app.timelapse_stopped()
        if self.light_status == 0:
            self.toggle_light()

    def timelapse_loop(self, name, q):
        logging.debug('timelapse loop : %s', name)
        begin = datetime.now()
        now = begin
        path = self.camera.getImagePath()
        path = os.path.join(path, f"TL_{begin.strftime(r'%Y-%m-%d_%H-%M-%S')}")
        os.mkdir(path)
        remains = self.auto_stop
        last = None
        interval = self.total_seconds
        height = 284
        width = round(height / self.camera.camera.resolution[1] * self.camera.camera.resolution[0])
        self.light_brightness = round(self.light.getBrightness() * 100)
        self.light_status = 1
        qt_photos = 0
        while (True):
            if qt_photos >= self.auto_stop > 0:
                self.stop_timelapse()
            if (not q.empty()):
                msg = q.get()
                if msg == 'stop':
                    logging.info("Stopping Timelapse")
                    self.btn['start'].state(['!disabled'])
                    return
            now = datetime.now()
            if (last is None or (now - begin).total_seconds() >= interval * qt_photos):
                filename = f"{now.strftime(r'%Y-%m-%d_%H-%M-%S')}.jpg"
                p = os.path.join(path, filename)
                ###
                try:
                    self.camera.camera.capture(p, 'jpeg')
                    logging.info("Picture '%s' saved.", filename)
                    # Display the saved picture instead of Live video.
                    photo = Image.open(p)
                    photo = photo.resize((width, height), Image.ANTIALIAS)
                    photo = ImageTk.PhotoImage(photo)
                    self.camera.panel.configure(image=photo)
                    self.camera.panel.image = photo
                    last = now
                    self.last_frame.set(str(datetime.strftime(last, r'%Y-%m-%d %H:%M:%S ')))
                    # Photo Counter
                    qt_photos += 1
                except PiCameraRuntimeError:
                    logging.error("Impossible to capture picture %s", filename, exc_info=True)
            # Refresh time before Next Frame
            n = int((timedelta(0, interval) - (now - last)).total_seconds())
            if interval < 3600:
                self.next_frame.set(f'{n // 60} min {n % 60} sec')
            else:
                self.next_frame.set(f'{n // 3600} h {n % 3600 // 60} m {n % 60} s')

            # AUTOLIGHT : Switch light on/off automatically before/after pictures
            if interval > MIN_INTERVAL_AUTOLIGHT:
                if ((n <= AUTOLIGHT_INTERVAL
                     and self.light_status == 0)
                    or (n > interval - 5
                        and self.light_status == 1)):
                    self.toggle_light()

            # Refresh time before End
            if remains == 0:
                self.remaining.set('∞')
            else:
                n = max(0, int(interval * (remains - qt_photos) - (interval - n)))
                r = time_str(n)
                self.remaining.set(r)
            sleep(0.200)  # Wait 200 ms
