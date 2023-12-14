# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import threading
from time import sleep
from tkinter import StringVar, Frame, Tk

from .microscope_camera import Camera
from .microscope_light import Light


class Microscope():
    def __init__(self, root:Tk, cameraFrame:Frame):
        self.light  = Light()
        self.master = root
        self.camera = Camera(self.master, cameraFrame)
        self.temperature = StringVar()
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(name='temperatureThread', target=self.temperature_watchdog, args=())
        self.thread.start()

    def close(self):
        self.stopEvent.set()
        self.light.off()
        self.camera.close()
        self.thread.join(timeout=1.0)

    def temperature_watchdog(self):
        logging.info("Starting Temperature watchdog...")
        while not self.stopEvent.isSet():
            self.refresh_temp()
            sleep(1)

    def refresh_temp(self):
        try:
            t = 0
            with open(r"/sys/class/thermal/thermal_zone0/temp") as f:
                t = f.readline()
            t = round(float(t) / 1000)
            if not self.stopEvent.isSet():
                self.temperature.set(f"{t} °C")
        except OSError:
            logging.error('Impossible to read temperature', exc_info=True)
            self.temperature.set('? ?')
        except RuntimeError:
            logging.error('RuntimeError: Exiting Temperature thread...', exc_info=True)
            exit()
