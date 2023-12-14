# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import sys
import threading
from time import sleep
from tkinter import Frame, StringVar, Tk

from .microscope_camera import Camera
from .microscope_light import Light


class Microscope():
    """ Microscope object including camera and light"""
    def __init__(self, root:Tk, camera_frame:Frame):
        self.light  = Light()
        self.master = root
        self.camera = Camera(self.master, camera_frame)
        self.temperature = StringVar()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(name='temperatureThread', target=self.temperature_watchdog, args=())
        self.thread.start()

    def close(self):
        self.stop_event.set()
        self.light.off()
        self.camera.close()
        self.thread.join(timeout=1.0)

    def temperature_watchdog(self):
        logging.info("Starting Temperature watchdog...")
        while not self.stop_event.is_set():
            self.refresh_temp()
            sleep(1)

    def refresh_temp(self):
        try:
            t = 0
            with open(r"/sys/class/thermal/thermal_zone0/temp", "r") as f:
                t = f.readline()
            t = round(float(t) / 1000)
            if not self.stop_event.is_set():
                self.temperature.set(f"{t} °C")
        except OSError:
            logging.error('Impossible to read temperature', exc_info=True)
            self.temperature.set('? ?')
        except RuntimeError:
            logging.error('RuntimeError: Exiting Temperature thread...', exc_info=True)
            sys.exit()
