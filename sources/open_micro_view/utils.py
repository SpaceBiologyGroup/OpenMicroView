# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import ctypes
import ctypes.util
import logging
import os
from subprocess import PIPE, Popen
from tkinter import FLAT, Frame, IntVar, StringVar, ttk
from typing import Callable

KB = 1024
MB = KB * 1024
GB = MB * 1024

B_to_KB:Callable[[int], float] = lambda x: x / 1024
B_to_MB:Callable[[int], float] = lambda x: B_to_KB(x) / 1024
B_to_GB:Callable[[int], float] = lambda x: B_to_MB(x) / 1024
B_to_readable:Callable[[int], str] = lambda x: (f"{B_to_KB(x):.2f} kB" if x < MB else (f"{B_to_MB(x):.2f} MB" if x < GB else f"{B_to_GB(x):.2f} GB"))


def seconds_to_readable(sec:int):
    r = []
    for unit in ('s', 'm', 'h'):
        r.insert(0, f"{(sec % 60):.0f} {unit}")
        sec //= 60
        if not sec:
            break
    return ' '.join(r)

def create_popup(close_btn:str=None, text:str=None, raise_over:Frame=None, cols:int=1,
                 accept_btn:str='Yes', accept_callback:Callable=None) -> Frame:
    ''' Create a popup in the middle of the scrren. '''
    frame = Frame(relief=FLAT, bg='white', highlightbackground="grey", highlightthickness=2)
    frame.place(anchor='c', relx=0.5, rely=0.5)
    if accept_callback is not None and close_btn is not None and cols == 1:
        cols = 2
    if raise_over:
        frame.tkraise(aboveThis=raise_over)
    if isinstance(text, str) and len(text):
        label = ttk.Label(frame, text=text, style='TLabel')
        label.grid(row=0, ipadx=20, padx=30, pady=20, sticky='NEWS', columnspan=cols)
    if isinstance(close_btn, str) and len(close_btn):
        ok_btn = ttk.Button(frame, text=close_btn, style='config.TButton', command=frame.destroy)
        ok_btn.grid(row=1, sticky='NS', ipadx=50, pady=10)
    if isinstance(accept_callback, Callable) and isinstance(accept_btn, str):
        callback = lambda: (frame.destroy(), accept_callback())
        acc_btn = ttk.Button(frame, text=accept_btn, style='config.TButton', command=callback)
        acc_btn.grid(row=1, column=cols - 1, sticky='NS', ipadx=50, pady=10)
    return frame


def create_progress_popup(text:str=None, raise_over:Frame=None, variable:IntVar=None,
                          maximum:int=100, status_var:StringVar=None) -> Frame:
    frame = create_popup(text=text, raise_over=raise_over)
    progressbar = None
    if isinstance(variable, IntVar):
        progressbar = ttk.Progressbar(frame, maximum=maximum, value=0, variable=variable)
    else:
        progressbar = ttk.Progressbar(frame, mode='indeterminate')

    if isinstance(status_var, StringVar):
        status = ttk.Label(progressbar, style='TLabel',
                           background='white', textvariable=status_var)
        status.place(anchor='c', relx=0.5, rely=0.5)
    progressbar.grid(row=1, ipadx=100, ipady=10, padx=10, pady=10, sticky='NEWS')
    return frame



libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
libc.umount2.argtypes = (ctypes.c_char_p, ctypes.c_int)


def umount2(target:str, options:int=0):
  if libc:
    ret = libc.umount2(target.encode(), options)
    if ret < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, f"Error unmounting {target}: {os.strerror(errno)}")


def dir_size_bytes(dir:str) -> int:
    cmd=['du', '-sb', dir]
    with Popen(cmd, stdout=PIPE, stderr=PIPE) as process:
        stdout, stderr = process.communicate()
    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")
    size = stdout.split('\t')[0]
    if size == '':
        logging.error(f"\nAn Error occured calculating dirsize:")
        logging.error(f"{cmd}.stdout: {stdout}")
        logging.error(f"{cmd}.stderr: {stderr}")
        return 0
    return int(size)