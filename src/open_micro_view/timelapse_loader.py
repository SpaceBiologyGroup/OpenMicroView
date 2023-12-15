# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import os
import threading
import time
from tkinter import Frame, IntVar, Label, TclError

from PIL import Image, ImageTk

IMG_EXTENSIONS = ['jpg', 'jpeg', 'png']


class TimelapseLoader:
    """ Load and play a timelapse """
    def __init__(self, fullpath:str, callback:callable = None):
        self.max_w, self.max_h = 500, 280
        self.fullpath = fullpath
        self.stop_event = threading.Event()
        self.files = [f for f in os.listdir(self.fullpath) if f.split('.')[-1] in IMG_EXTENSIONS]
        self.files.sort()
        self.frames_loaded = 0
        self.frames = []
        self.total_frames = len(self.files)
        self.is_ready = False
        self.thread = None
        self.play_thread = None
        self.timelapse_frame = None
        self.callback = callback
        self.timelapse_fps = 4
        self.pause_event = threading.Event()
        self.timelapse_increment = 1
        self.tk_player_index = IntVar(0)
        self.tk_n_frames_loaded = IntVar(0)

    def __del__(self):
        self.quit()

    def quit(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)
        self.is_ready = False

    def update_status(self):
        self.tk_n_frames_loaded.set(self.frames_loaded)

    def check_stop_event(self):
        if self.stop_event.is_set():
            logging.info("Stopping timelapse loading...")
            self.frames = None
            raise StopAsyncIteration('Stop event received.')

    def __load(self):
        ''' @Threaded - Load the timelapse frames'''
        h = w = ratio = None
        try:
            for img in self.files:
                self.check_stop_event()
                logging.debug('[%d/%d] loading %s',
                              self.frames_loaded + 1, self.total_frames, img)
                path = os.path.join(self.fullpath, img)
                photo:Image = Image.open(path)
                if ratio is None:
                    ratio = min(self.max_w / photo.width, self.max_h / photo.height)
                    h, w = int(photo.height * ratio), int(photo.width * ratio)
                photo = ImageTk.PhotoImage(photo.resize((w, h), Image.LANCZOS))
                self.check_stop_event()  # check if stopped before adding frame to list
                self.frames.append(photo)
                self.frames_loaded += 1
                self.update_status()
            logging.info('Done')
            self.is_ready = True
            if self.callback is not None:
                self.callback()
        except StopAsyncIteration:
            logging.warning("Quitting: stop signal received")
            return None

    def __play(self):
        ''' @Threaded - Play the timelapse inside container Frame '''
        try:
            frame = self.timelapse_frame
            last_frame = time.time_ns()
            minimum_step = 1_000_000_000 / self.timelapse_fps
            sleep_step = 1 / (self.timelapse_fps * 5)
            while not self.stop_event.is_set():
                now = time.time_ns()
                if self.tk_player_index.get() >= self.total_frames - 1:
                    self.pause(False)
                elif (not self.pause_event.is_set() and now - last_frame > minimum_step):
                    img = self.get_current_frame(increment=1)
                    frame.configure(image=img)
                    # frame.image = img
                    last_frame = now
                else:
                    coef = (1, self.timelapse_fps)[self.pause_event.is_set()]
                    time.sleep(sleep_step * coef)
        except TclError:
            logging.warning('Impossible to play timelapse: Container was destroyed.',
                            exc_info=True)
        finally:
            logging.info('Exiting Thread.__play')

    def pause(self, update:bool=False):
        ''' Pause the video player'''
        self.pause_event.set()
        if update:
            img = self.get_current_frame()
            self.timelapse_frame.configure(image=img)

    def get_current_frame(self, increment:int=0):
        v = int(self.tk_player_index.get())
        v2 = v + increment
        v2 = min(max(v2, 0), len(self.frames) - 1)
        if v2 != v:
            self.tk_player_index.set(v2)
        return self.frames[v2]

    def play(self, container:Frame=None) -> bool:
        # Unpause if thread exists
        if self.play_thread is not None:
            self.pause_event.clear()
            return True
        # Create timelapse frame
        if not self.timelapse_frame:
            if not container:
                logging.error('Container cannot be none on first call')
                return False
            img = self.frames[self.tk_player_index.get()]
            self.timelapse_frame = Label(container, image=img, background='white')
            self.timelapse_frame.pack(side='top', fill='both')
        # Start to play
        self.play_thread = threading.Thread(name='TimelapsePlayer', target=self.__play, args=[])
        self.play_thread.start()
        return True

    def load(self):
        self.reset()
        self.thread = threading.Thread(name='TimelapseLoader', target=self.__load, args=[])
        self.thread.start()

    def reset(self):
        self.stop_event.clear()
        self.frames_loaded = 0
        self.frames = []
        self.total_frames = len(self.files)
        self.is_ready = False
        self.tk_player_index.set(0)
        self.tk_n_frames_loaded.set(0)
