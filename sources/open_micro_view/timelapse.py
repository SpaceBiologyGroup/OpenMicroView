# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import os
import threading
from datetime import datetime, timedelta
from functools import partial
from queue import Queue
from time import sleep
from tkinter import IntVar, StringVar, ttk, HORIZONTAL

from picamera.exc import PiCameraRuntimeError
from PIL import Image, ImageTk

# Switch Light on before x sec at each Timelapse picture
AUTOLIGHT_INTERVAL = 3

# Minimum interval to automatically switch off the light
MIN_INTERVAL_AUTOLIGHT = 15


class Timelapse:
    def __init__(self, microscope, root_app):
        self.light = microscope.light
        self.camera = microscope.camera
        self.root_app = root_app
        self.time = {'s': 0, 'm': 0, 'h': 0}
        self.value = IntVar()
        self.s_autoStop = StringVar()
        self.t_autoStop = StringVar()
        self.autoStop = 0
        self.mode = None
        self.interval = StringVar()
        self.max = {'s': 59, 'm': 59, 'h': 24}
        self.btn = {'s': None, 'm': None, 'h': None}
        self.timelapseFrame = None
        self.nextFrame = StringVar()
        self.lastFrame = StringVar()
        self.remaining = StringVar()
        self.total_seconds = 0
        self.stopEvent = threading.Event()
        self.timelapseQueue = Queue()
        self.light_brightness = 0
        self.light_status = 0

    def initTimelapseTab(self, container):
        self.container = container
        self.tab = tab = ttk.Frame(container)
        self.timelapseFrame = ttk.Frame(container)
        self.initTimelapseFrame()
        tab.pack(fill='both')
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_columnconfigure(2, weight=1)
        # LINE 0
        self.btn['s'] = ttk.Button(tab, text='Sec.', style='time.TButton',
                                   command=partial(self.changeMode, 's'))
        self.btn['s'].grid(column=0, row=0, sticky='news', padx=5, pady=5)
        self.btn['m'] = ttk.Button(tab, text='Min.', style='time.TButton',
                                   command=partial(self.changeMode, 'm'))
        self.btn['m'].grid(column=1, row=0, sticky='news', padx=5, pady=5)
        self.btn['h'] = ttk.Button(tab, text='Hou.', style='time.TButton',
                                   command=partial(self.changeMode, 'h'))
        self.btn['h'].grid(column=2, row=0, sticky='news', padx=5, pady=5)

        # LINE 1
        ttk.Label(tab, textvar=self.value,
                  style='tlvalue.TLabel').grid(column=0, row=1, sticky='nes',
                                               padx=5, pady=5)
        self.value.set(0)
        ttk.Button(tab, text='-',
                   style='control.TButton',
                   command=self.valueMinus).grid(column=1, row=1, sticky='news',
                                                 padx=5, pady=5)
        self.plus = ttk.Button(tab, text='+',
                               style='control.TButton',
                               command=self.valuePlus).grid(column=2, row=1, sticky='news',
                                                            padx=5, pady=5)
        # LINE 3
        ttk.Label(tab, text='Interval:').grid(column=0, row=3, sticky='news')
        ttk.Label(tab, textvar=self.interval).grid(column=1, row=3, columnspan=2, sticky='news')
        self.interval.set('00:00:00')
        # LINE 4
        ttk.Separator(tab, orient=HORIZONTAL).grid(column=0, row=4, columnspan=3, padx=10, pady=2)
        # LINE 5
        ttk.Label(tab, textvar=self.t_autoStop).grid(column=0, row=5, columnspan=3, sticky='news', pady=5)

        # LINE 6
        # Automatically stop after x photos (∞)
        ttk.Label(tab, textvar=self.s_autoStop,
                  style='tlvalue.TLabel').grid(column=0, row=6, sticky='nes', padx=5, pady=5)
        self.refreshAutoStop()
        ttk.Button(tab, text='-',
                   style='control.TButton',
                   command=self.stopMinus).grid(column=1, row=6, sticky='news', padx=5, pady=5)
        self.plus = ttk.Button(tab, text='+',
                               style='control.TButton',
                               command=self.stopPlus).grid(column=2, row=6, sticky='news', padx=5, pady=5)
        # LINE 7 - nothing

        # LINE 8
        self.btn['start'] = ttk.Button(tab, text="Start Timelapse",
                                       command=self.startTimelapse)
        self.btn['start'].grid(column=0, row=8, columnspan=3, padx=5, pady=5)

        # END
        self.changeMode('s')
        self.changeValue(0)
        return

    def initTimelapseFrame(self):
        tab = self.timelapseFrame
        tab.grid_columnconfigure(1, weight=1)
        ttk.Label(tab, text='Last:').grid(row=0, column=0, sticky='news')
        ttk.Label(tab, textvar=self.lastFrame).grid(row=0, column=1, sticky='news')
        ttk.Label(tab, text='Next:').grid(row=1, column=0, sticky='news')
        ttk.Label(tab, textvar=self.nextFrame).grid(row=1, column=1, sticky='news')
        ttk.Label(tab, text='Remains:').grid(row=2, column=0, sticky='news')
        ttk.Label(tab, textvar=self.remaining).grid(row=2, column=1, sticky='news')
        ttk.Separator(tab, orient=HORIZONTAL).grid(row=3, column=0, columnspan=3, padx=30, pady=20)
        self.btn['stop'] = ttk.Button(tab, text="Stop Now",
                                      style='del.TButton',
                                      command=self.stopTimelapse)
        self.btn['stop'].grid(column=0, row=8, columnspan=2, padx=10, pady=10, sticky='news')
        return

    def changeMode(self, mode):
        if self.mode == mode:
            return
        if self.mode is not None:
            self.btn[self.mode].state(["!disabled"])
        self.btn[mode].state(["disabled"])
        self.mode = mode
        self.value.set(self.time[mode])

    def stopPlus(self):
        if self.autoStop < 100:
            self.autoStop += 5
        elif self.autoStop < 500:
            self.autoStop += 10
        else:
            self.autoStop += 20
        self.s_autoStop.set(self.autoStop)
        self.refreshAutoStop()

    def stopMinus(self):
        if self.autoStop <= 5:
            self.autoStop = 0
        elif self.autoStop <= 100:
            self.autoStop -= 5
        elif self.autoStop <= 500:
            self.autoStop -= 10
        else:
            self.autoStop -= 20
        self.refreshAutoStop()

    def refreshAutoStop(self):
        if self.autoStop:
            n = self.total_seconds * (self.autoStop - 1)
            if (n // 3600 < 24):
                duration = '{} h {} m {} s'.format(n // 3600,
                                                   n % 3600 // 60,
                                                   n % 60)
            else:
                duration = '{} d {} h {} m'.format(n // 86_400,
                                                   n % 86_400 // 3600,
                                                   n % 3600 // 60)
            self.s_autoStop.set(self.autoStop)
            self.t_autoStop.set('Autostop after {}'.format(duration))
        else:
            self.t_autoStop.set('Stop timelapse manually')
            self.s_autoStop.set('∞')

    def valuePlus(self):
        val = self.value.get() + 1
        if (val > self.max[self.mode]):
            val = 0
        self.changeValue(val)

    def valueMinus(self):
        val = self.value.get() - 1
        if (val < 0):
            val = self.max[self.mode]
        self.changeValue(val)

    def changeValue(self, value):
        self.value.set(value)
        self.time[self.mode] = value
        t = self.time
        self.total_seconds = t['s'] + (t['m'] * 60) + (t['h'] * 3600)
        self.interval.set("{} h {} min {} sec".format(t['h'], t['m'], t['s']))
        self.refreshAutoStop()
        if (self.total_seconds < 5):
            self.btn['start'].state(['disabled'])
        else:
            self.btn['start'].state(['!disabled'])

    def toggleLight(self):
        if self.light_status:
            self.light.set_brightness(0)
            self.light_status = 0
        else:
            self.light.set_brightness(self.light_brightness)
            self.light_status = 1

    def startTimelapse(self):
        self.btn['start'].state(['disabled'])
        self.camera.stopVideo()
        self.tab.pack_forget()
        self.timelapseFrame.pack(fill='both')
        self.thread = threading.Thread(target=self.timelapseLoop,
                                       args=("timelapse-thread", self.timelapseQueue))
        self.stopEvent.clear()
        self.thread.start()
        self.root_app.timelapse_started()

    def stopTimelapse(self):
        self.timelapseQueue.put('stop')
        self.camera.startVideo()
        self.tab.pack(fill='both')
        self.timelapseFrame.pack_forget()
        self.root_app.timelapse_stopped()
        if self.light_status == 0:
            self.toggleLight()

    def timelapseLoop(self, name, q):
        begin = datetime.now()
        now = begin
        path = self.camera.getImagePath()
        path = os.path.join(path, f"TL_{begin.strftime(r'%Y-%m-%d_%H-%M-%S')}")
        os.mkdir(path)
        remains = self.autoStop
        last = None
        interval = self.total_seconds
        height = 284
        width = round(height / self.camera.camera.resolution[1] * self.camera.camera.resolution[0])
        self.light_brightness = round(self.light.getBrightness() * 100)
        self.light_status = 1
        qt_photos = 0
        while (True):
            if qt_photos >= self.autoStop > 0:
                self.stopTimelapse()
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
                    self.lastFrame.set(str(datetime.strftime(last, r'%Y-%m-%d %H:%M:%S ')))
                    # Photo Counter
                    qt_photos += 1
                except PiCameraRuntimeError:
                    logging.error("Impossible to capture picture %s", filename, exc_info=True)
            # Refresh time before Next Frame
            n = int((timedelta(0, interval) - (now - last)).total_seconds())
            if interval < 3600:
                self.nextFrame.set('{} min {} sec'.format(n // 60,
                                                          n % 60))
            else:
                self.nextFrame.set('{} h {} m {} s'.format(n // 3600,
                                                           n % 3600 // 60,
                                                           n % 60))

            # AUTOLIGHT : Switch light on/off automatically before/after pictures
            if interval > MIN_INTERVAL_AUTOLIGHT:
                if ((n <= AUTOLIGHT_INTERVAL
                     and self.light_status == 0)
                    or (n > interval - 5
                        and self.light_status == 1)):
                    self.toggleLight()

            # Refresh time before End
            if remains == 0:
                self.remaining.set('∞')
            else:
                n = max(0, int(interval * (remains - qt_photos) - (interval - n)))
                if (n // 3600 < 24):  # if less than 1 day
                    r = '{} h {} m {} s'.format(n // 3600,
                                                n % 3600 // 60,
                                                n % 60)
                else:
                    r = '{} d {} h {} m'.format(n // 86_400,
                                                n % 86_400 // 3600,
                                                n % 3600 // 60)
                self.remaining.set(r)
            sleep(0.200)  # Wait 200 ms
