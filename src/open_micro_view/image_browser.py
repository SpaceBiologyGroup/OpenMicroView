# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import os
import shutil
from functools import cmp_to_key, partial
from tkinter import (FLAT, GROOVE, Button, Frame, Label, PhotoImage, StringVar,
                     TclError, ttk)

from PIL import Image, ImageTk

from .assets.icons import PAUSE_ICON, PLAY_ICON, TRASH_ICON, icon_button
from .timelapse_loader import IMG_EXTENSIONS, TimelapseLoader
from .utils import (B_to_MB, B_to_readable, create_popup, dir_size_bytes,
                    seconds_to_readable)


class ImageBrowser():
    '''
    Root
      |- Frame
          |- 5x Buttons
          |- 2x Label
          |- IMG-Frame
             |- Label
                |- PhotoImage
    '''

    def __init__(self, path:str):
        self.max_w, self.max_h = 700, 350
        self.path:str = path
        self.img_list:list = None
        self.frame:Frame = None
        self.root = None
        self.image_frame:Frame = None
        self.current_index:int = None
        self.current_image:Label = None
        self.current_image_path:str = None
        self.load_tl_btn:ttk.Button = None
        self.timelapse_loader:TimelapseLoader = None
        self.timelapse_fps:int = 5
        # TKinter Variales
        self.tk_file_info:StringVar = StringVar()
        self.tk_filename:StringVar = StringVar()
        self.tk_filesize:StringVar = StringVar()
        self.tk_file_index:StringVar = StringVar()

    def quit(self) -> None:
        if self.timelapse_loader:
            self.timelapse_loader.quit()
        if self.frame:
            self.frame.destroy()
            self.frame = None
        self.img_list = None
        self.image_frame = None
        self.current_index = None
        self.current_image = None
        self.current_image_path = None
        return None

    def compare_file_creation_date(self, f1:str, f2:str) -> float:
        t1 = os.path.getctime(os.path.join(self.path, f1))
        t2 = os.path.getctime(os.path.join(self.path, f2))
        return t2 - t1

    def start(self):
        logging.info('Starting picture browser')
        try:
            self.img_list = [f for f in os.listdir(self.path)
                             if f.split('.')[-1] in IMG_EXTENSIONS or f[0:3] == 'TL_']
            self.img_list = sorted(self.img_list,
                                   key=cmp_to_key(self.compare_file_creation_date))
        except OSError as e:
            create_popup(close_btn='Ok',
                         text=f'Error: impossible to read directory:\n"{self.path}",\n{str(e)}')
            return False
        if len(self.img_list) <= 0:
            create_popup(close_btn='Ok',
                         text='There is no picture to browse.')
            return False
        self.initialize_view()

    def initialize_view(self) -> Frame:
        # Main Frame
        self.frame = Frame(borderwidth=2, relief=FLAT, bg='white', padx=10, pady=10)
        self.frame.place(anchor='c', relwidth=1, relheight=1, relx=0.5, rely=0.5)
        self.root = self.frame.master
        # Image Frame
        self.image_frame = Frame(self.frame, borderwidth=2, relief=GROOVE, bg='#FFFEFD')
        self.image_frame.pack(padx=5, pady=5, side='top', expand=True)

        # Info Row
        info_row = Frame(self.frame, background='white', borderwidth=2)
        info_row.pack(fill='x', side='bottom')
        for col in range(0, 9):
            info_row.grid_columnconfigure(col, weight=1, pad=1)
        # [  |  filename - size   |  ]
        lbl = ttk.Label(info_row, textvariable=self.tk_file_info, justify='center')
        lbl.grid(row=0, column=1, columnspan=8)

        # [DEL|  |<<| <|  |##|  |> |>>|XX]
        style = 'TButton'
        # Delete Button
        trash = PhotoImage(data=TRASH_ICON)
        text = 'Are you sure you want to delete this picture'
        del_btn = Button(info_row, image=trash, text="",
                         bg='#FFDDDD', highlightcolor='#FFAAAA', width=40,
                         command=lambda:create_popup(text=text,
                                                     close_btn='Cancel',
                                                     accept_btn='Delete',
                                                     accept_callback=self.delete_picture))
        del_btn.image = trash
        del_btn.grid(row=1, column=0, padx=5, sticky='news')

        # Arrows Buttons
        btn = ttk.Button(info_row, text=' << ', style=style, command=partial(self.prev_pic, 5))
        btn.grid(row=1, column=2)
        btn = ttk.Button(info_row, text=' < ', style=style, command=self.prev_pic, padding=())
        btn.grid(row=1, column=3)

        lbl = ttk.Label(info_row, textvariable=self.tk_file_index)
        lbl.grid(row=1, column=5)

        btn = ttk.Button(info_row, text=' > ', style=style, command=self.next_pic)
        btn.grid(row=1, column=7)
        btn = ttk.Button(info_row, text=' >> ', style=style, command=partial(self.next_pic, 5))
        btn.grid(row=1, column=8)
        # Close Button
        btn = ttk.Button(info_row, text='Close', style=style, command=self.quit)
        btn.grid(row=1, column=9)

        self.update_picture(0)
        return self.frame

    def delete_picture(self):
        try:
            full_path = self.current_image_path
            if os.path.isfile(full_path):
                os.remove(full_path)
                self.img_list.pop(self.current_index)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
                self.img_list.pop(self.current_index)
        except OSError as e:
            create_popup("ok", f'An error occured :\n{str(e)}')
        finally:
            self.update_picture(self.current_index, force=True)

    def clear_picture_frame(self):
        if self.current_image is not None:
            self.current_image.destroy()
            self.current_image = None

    def load_timelapse(self, _dir:str):
        self.clear_picture_frame()
        self.current_image = frame = Frame(self.image_frame, background='white', borderwidth=2)
        frame.pack(fill='both', expand=True, ipadx=10, ipady=10)
        frame.grid_columnconfigure([0, 2], weight=2)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure([1, 2], weight=1)
        self.timelapse_loader = TimelapseLoader(_dir, self.display_timelapse)
        text = 'The timelapse is being loaded...'
        ttk.Label(frame, text=text).grid(row=1, column=1)
        progressbar = ttk.Progressbar(frame,
                                      maximum=self.timelapse_loader.total_frames,
                                      value=0,
                                      variable=self.timelapse_loader.tk_n_frames_loaded)
        progressbar.grid(row=2, column=1)

        cancel_btn = ttk.Button(frame, text="Cancel", style='del.TButton',
                                command=self.cancel_timelapse)
        cancel_btn.grid(row=3, column=1, sticky='NS', ipadx=50, pady=10)

        self.timelapse_loader.load()

    def display_timelapse(self):
        if self.timelapse_loader.is_ready:
            self.clear_picture_frame()
        self.current_image = Frame(self.image_frame, background='white')
        self.current_image.pack(side='top', ipady=5, ipadx=5, expand=True)
        timelapse_toolbar = Frame(self.current_image, background='white')
        timelapse_toolbar.pack(side='bottom', fill='x', pady=5)
        timelapse_toolbar.grid_columnconfigure(list(range(10)), weight=1)

        icon_button(timelapse_toolbar, PLAY_ICON,
                    style='config.TButton',
                    command=self.timelapse_loader.play
                    ).grid(column=0, row=0, sticky='news', padx=5)

        icon_button(timelapse_toolbar, PAUSE_ICON,
                    style='config.TButton',
                    command=self.timelapse_loader.pause
                    ).grid(column=1, row=0, sticky='news', padx=5)
        ttk.Scale(timelapse_toolbar,
                  from_=0, to=self.timelapse_loader.total_frames - 1,
                  variable=self.timelapse_loader.tk_player_index,
                  command=(lambda v: self.timelapse_loader.pause(True))
                  ).grid(column=2, row=0, columnspan=8, sticky='news', padx=5)

        self.timelapse_loader.play(self.current_image)

    def cancel_timelapse(self):
        self.timelapse_loader.quit()
        self.prompt_timelapse()

    def prompt_timelapse(self):
        dirname = self.img_list[self.current_index]
        fullpath = os.path.join(self.path, dirname)
        size = dir_size_bytes(fullpath)
        self.clear_picture_frame()
        frame = Frame(self.image_frame, background='white', borderwidth=2)
        frame.pack(fill='both', expand=True, padx=20, pady=30)
        self.current_image = frame
        # Show first frame from the timelapse
        img = Label(frame, text='Loading preview...',
                    background='white', foreground='grey', padx=2, pady=2)
        img.pack(side='top', expand=True, pady=5)

        # y = 0.3628x + 1.9867
        estimation = int(0.36 * B_to_MB(size) + 1.98)  # Seconds
        estimation = seconds_to_readable(estimation)
        text = (f'Do you want to load the timelapse {dirname} of size {B_to_readable(size)} ?\n'
                + f'This operation may take some time (ETA: ~ {estimation}).')
        ttk.Label(frame, text=text, justify='center').pack(expand=True, pady=5)
        load_tl = ttk.Button(frame, text="Load Timelapse", style='config.TButton',
                             command=partial(self.load_timelapse, fullpath))
        load_tl.pack(side='bottom', expand=True, pady=10)

        try:
            n_frames = f' - {len(os.listdir(fullpath))} frames'
            self.tk_file_info.set(self.tk_file_info.get() + n_frames)
        except OSError:
            logging.error("Impossible to list files in %s", fullpath, exc_info=True)

        frame.update()
        try:
            # Find the first image in the directory
            f = ''
            for f in os.listdir(fullpath):
                if f.split('.')[-1] in IMG_EXTENSIONS:
                    break
                f = False
            if f:
                photo:Image = Image.open(os.path.join(fullpath, f))
                ratio = min(400 / photo.width, 150 / photo.height)
                h, w = int(photo.height * ratio), int(photo.width * ratio)
                photo = ImageTk.PhotoImage(photo.resize((w, h), Image.LANCZOS))
                img.configure(image=photo, relief=GROOVE)
                img.image = photo
                img.update()
        except TclError:
            logging.error("prompt_timelapse: Frame was destroyed.")

    def update_picture(self, index:int, force:bool=False):
        if self.timelapse_loader:
            self.timelapse_loader.quit()
            self.timelapse_loader = None
        if len(self.img_list) <= 0:
            create_popup(text="There is no more picture to browse.",
                         accept_btn='Close browser', accept_callback=self.quit)
        # Ensure index is valid
        index = min(max(index, 0), len(self.img_list) - 1)
        if not force and index == self.current_index:
            return None
        self.current_index = index
        # Retrieve image from index
        filename = self.img_list[index]
        self.current_image_path = os.path.join(self.path, filename)

        # update Info
        file_size_bytes = 0
        if os.path.isfile(self.current_image_path):
            file_size_bytes = os.path.getsize(self.current_image_path)
        elif os.path.isdir(self.current_image_path):
            file_size_bytes = dir_size_bytes(self.current_image_path)
        self.tk_filename.set(filename)
        self.tk_filesize.set(B_to_readable(file_size_bytes))
        self.tk_file_info.set(filename + " - " + B_to_readable(file_size_bytes))
        self.tk_file_index.set(f"{self.current_index + 1}/{len(self.img_list)}")

        if filename[0:3] == 'TL_' and os.path.isdir(self.current_image_path):
            self.prompt_timelapse()
            return None
        # Load image
        self.clear_picture_frame()
        self.frame.update()
        try:
            photo:Image = Image.open(self.current_image_path)
            mp = f"{round((photo.width * photo.height) / 1_000_000, 1):.1f} MP"
            self.tk_file_info.set(self.tk_file_info.get() +
                                  f" - {photo.width}x{photo.height} ({mp})")
            # Set size
            ratio = min(self.max_w / photo.width, self.max_h / photo.height)
            height = int(photo.height * ratio)
            width = int(photo.width * ratio)
            # In case the button has been pushed multiple times, another picture should take over.
            if index != self.current_index:
                return False
            photo = ImageTk.PhotoImage(photo.resize((width, height), Image.LANCZOS))
            # Remove previous image
            # Create Frame
            self.clear_picture_frame()
            self.current_image = Label(self.image_frame, image=photo)
            self.current_image.image = photo
            self.current_image.pack(fill='both')
        except OSError as e:
            self.clear_picture_frame()
            self.current_image = Label(self.image_frame, background='white',
                                       text=f'Error while opening {filename}:\n{str(e)}')
            self.current_image.pack(fill='both')
        return None

    def next_pic(self, n:int=1):
        self.update_picture(self.current_index + n)

    def prev_pic(self, n:int=1):
        self.update_picture(self.current_index - n)
