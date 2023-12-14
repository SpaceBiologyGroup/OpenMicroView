# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import datetime
import logging
import os
import threading
import time
from functools import partial
from queue import Queue
from statistics import mean
from time import sleep
from tkinter import FLAT, Button, Frame, IntVar, Label, PhotoImage, ttk

from picamera import PiCamera
from picamera.array import PiRGBArray
from PIL import Image, ImageTk

from .assets.icons import TRASH_ICON
from .utils import create_popup

DEFAULT_IMAGES_STORAGE = '/opt'
PICTURE_FOLDER_NAME = 'OpenMicroView_Media'
PREVIEW_MAX_H = 400
PREVIEW_MAX_W = 510


class Camera:
    """ OpenMicroView Microscope Camera """
    def __init__(self, root, tab):
        self.vs = None
        self.camera = PiCamera()
        self.outputPath = DEFAULT_IMAGES_STORAGE
        self.snapshotFrame = None
        self.frame = None
        self.tab = tab
        self.thread = None
        self.stopEvent = threading.Event()
        self.restartEvent = threading.Event()
        self.root = root
        self.panel = None
        self.i_fps = IntVar()
        self.i_brightness = IntVar()
        self.i_contrast = IntVar()
        self.i_sharpness = IntVar()
        self.i_saturation = IntVar()
        self.new_resolution = None
        self.videoQueue = Queue()
        self.camera.vflip = True
        if (not os.path.isdir(self.getImagePath())):
            os.mkdir(self.getImagePath())

        # Start The Stream
        self.startVideo()

    def close(self):
        self.stopEvent.set()
        self.restartEvent.set()
        if self.thread:
            self.thread.join(timeout=1.0)

    def fps(self, n=None):
        if (n is not None):
            self.camera.framerate = n
        return self.camera.framerate

    def brightness(self, n=None):
        if (n is None):
            self.i_brightness = self.camera.brightness
        else:
            n = round(float(n))
            self.camera.brightness = n
            self.i_brightness = self.camera.brightness
        return self.camera.brightness

    def contrast(self, n=None):
        if (n is None):
            self.i_contrast = self.camera.contrast
        else:
            n = round(float(n))
            self.camera.contrast = n
            self.i_contrast = self.camera.contrast
        return self.camera.contrast

    def sharpness(self, n=None):
        if (n is None):
            self.i_sharpness = self.camera.sharpness
        else:
            n = round(float(n))
            self.camera.sharpness = n
            self.i_sharpness = self.camera.sharpness
        return self.camera.sharpness

    def saturation(self, n=None):
        if (n is None):
            self.i_saturation = self.camera.saturation
        else:
            n = round(float(n))
            self.camera.saturation = n
            self.i_saturation = self.camera.saturation
        return self.camera.saturation

    def videoLoop(self, n, q):
        preset_ratio = self.camera.resolution[1] / self.camera.resolution[0]
        time_frame = None
        time_previous = None
        # We calculate FPS on the last 10
        fps_list = [0] * 10
        index = 0
        # If StopEvent is Set => Quit the loop
        while not self.stopEvent.isSet():
            self.restartEvent.clear()
            logging.debug("Start video loop.")
            try:
                while (not q.empty()):
                    res = q.get()
                    self.camera.resolution = res
                    preset_ratio = self.camera.resolution[1] / self.camera.resolution[0]
                    logging.debug(f'Camera Resolution changed to {res}')
                    sleep(0.3)
                # Set the preview resolution
                img_w = 240
                img_h = round(img_w * preset_ratio)
                stream = PiRGBArray(self.camera, size=(img_w, img_h))
                if self.panel:
                    self.panel.destroy()
                self.panel = None
                logging.info('Start Capture...')
                for frame in self.camera.capture_continuous(stream,
                                                            format='rgb',
                                                            use_video_port=True,
                                                            resize=(img_w, img_h)):
                    stream.truncate()
                    stream.seek(0)
                    self.image = frame.array
                    image = Image.fromarray(self.image)
                    max_h = PREVIEW_MAX_H
                    max_w = PREVIEW_MAX_W
                    ratio = min(max_w / image.width, max_h / image.height)
                    width = round(image.width * ratio)
                    height = round(image.height * ratio)
                    image = ImageTk.PhotoImage(image.resize((width, height), Image.ANTIALIAS))

                    if self.panel is None:
                        self.panel = Label(self.tab, image=image)
                        self.panel.image = image
                        self.panel.pack(padx=5, pady=10, fill='none')
                    else:
                        self.panel.configure(image=image)
                        self.panel.image = image
                    # Calculate Live Framerate (mean of last 10)
                    time_previous = time_frame
                    time_frame = time.monotonic()
                    if (time_previous is not None):
                        curr_fps = round(1 / (time_frame - time_previous))
                        fps_list[index] = curr_fps
                        self.i_fps.set(round(mean(tuple(fps_list))))
                        index = (index + 1) % 10
                    # If StopEvent is Set => Quit the loop
                    # if RestartEvent is Set => Reload the stream
                    if self.stopEvent.isSet() or self.restartEvent.isSet() or not q.empty():
                        break
            except RuntimeError:
                logging.error('RuntimeError: Exiting Camera thread...', exc_info=True)
                exit()
        logging.warning('End of VideoLoop Thread')
        return True

    def stopVideo(self):
        logging.info('Stopping Video...')
        self.stopEvent.set()

    def restartVideo(self):
        logging.info('Restarting Video...')
        self.restartEvent.set()

    def startVideo(self):
        sleep(0.2)
        logging.debug(f'Threads : {threading.active_count()}')
        self.restartEvent.clear()
        if self.thread is not None:
            self.stopEvent.set()
            self.thread.join()
        logging.info('Ready - Starting new video hread')
        self.thread = threading.Thread(name='videoLoop',
                                       target=self.videoLoop,
                                       args=("video-thread", self.videoQueue))
        self.restartEvent.clear()
        self.stopEvent.clear()
        self.thread.start()
        logging.debug('Thread Started')

    def getImagePath(self):
        return os.path.join(self.outputPath, PICTURE_FOLDER_NAME)

    def takeSnapshot(self):
        ts = datetime.datetime.now()
        filename = f"{ts.strftime(r'%Y-%m-%d_%H-%M-%S')}.jpg"
        p = os.path.join(self.getImagePath(), filename)
        self.camera.capture(p, 'jpeg')
        logging.info(f"Picture '{filename}' saved.")
        # Display the saved picture instead of Live video.
        sleep(0.2)
        photo = Image.open(p)
        max_w, max_h = 515, 330
        ratio = min(max_w / photo.width, max_h / photo.height)
        height = int(photo.height * ratio)
        width = int(photo.width * ratio)
        logging.debug(f"Resized snapshot: {width}x{height}")
        photo = photo.resize((width, height), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(photo)
        if (self.snapshotFrame is not None):
            self.snapshotFrame.destroy()
            self.snapshotFrame = None

        self.snapshotFrame = Frame(self.tab, bg='white')
        self.snapshotFrame.grid_columnconfigure(0, weight=1)
        label = Label(self.snapshotFrame, image=photo, bg='white')
        label.image = photo
        label.grid(row=0, column=0, columnspan=2, pady=10, padx=5, sticky='n')
        close = ttk.Button(self.snapshotFrame, text="Close Preview",
                           style='close.TButton',
                           command=self.closeSnapshotPreview)
        close.grid(row=1, column=0, sticky='nsew', padx=5)
        trash = PhotoImage(data=TRASH_ICON)
        del_btn = Button(self.snapshotFrame, relief=FLAT, image=trash, text="",
                         bg='#FFDDDD', highlightcolor='#FFAAAA', width=40,
                         command=partial(self.deleteSnapshot, p))
        del_btn.image = trash
        del_btn.grid(row=1, column=1, padx=5, sticky='news')
        # Remove live stream
        self.panel.pack_forget()
        # Display Snapshot frame
        self.snapshotFrame.pack(padx=(int(max_w - width) / 2), pady=0, fill='both')

    def deleteSnapshot(self, filename):
        self.closeSnapshotPreview()
        try:
            os.remove(filename)
            create_popup(text='The picture has been deleted.', close_btn='Ok')
            return True
        except OSError as e:
            create_popup(text=f'Error {e.errno}: Impossible to delete the file.', close_btn='Cancel')
            logging.error(f'Unable to remove file {filename}', exc_info=True)
            pass
        return False

    def closeSnapshotPreview(self):
        self.snapshotFrame.destroy()
        self.snapshotFrame = None
        self.panel.pack(padx=10, pady=10)
        return 0
