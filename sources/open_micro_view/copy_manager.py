# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

import logging
import os
from subprocess import PIPE, STDOUT, Popen
from time import sleep
from tkinter import IntVar, StringVar

from .utils import B_to_readable, dir_size_bytes


class CopyManager():
    def __init__(self):
        self.source:str = None
        self.dest:str = None
        self.percent = IntVar()
        self.progress_value = IntVar()
        self.transfered_size_str = StringVar()

        self.process:Popen = None
        self.pid:int = None
        self.size_before_copy:int = 0
        self.source_size:int = 0
        self.transfered_size:int = 0
        self.transfered_files:list = []

    def isrunning(self) -> bool:
        if self.process:
            return self.process.poll() == None
        return False

    def execute(self) -> bool:
        if self.isrunning():
            logging.warning("The copy is already on going.")
            return False
        self.transfered_files = []
        self.transfered_size = 0
        self.source_size = dir_size_bytes(self.source)
        self.percent.set(int(0))
        self.transfered_size_str.set(B_to_readable(0))
        self.progress_value.set(0)
        logging.info('Starting copy...')
        if self.dest[-1] != os.path.sep:
            self.dest = self.dest + os.path.sep
        if self.source[-1] != os.path.sep:
            self.source = self.source + os.path.sep
        if not os.path.isdir(self.dest):
            os.mkdir(self.dest)
        self.size_before_copy = dir_size_bytes(self.dest)
        logging.info(f'   | size before copy: {self.size_before_copy/1024:.2f} MB')
        cmd = ['/usr/bin/rsync', '-a',r"--out-format=%l$%f$", '--no-o', '--no-g', '--no-p', self.source, self.dest]
        with Popen(cmd, stdin=None, stdout=PIPE, stderr=STDOUT) as ps:
            logging.info('   | processing...')
            self.process = ps
            sleep(0.5)
            for line in ps.stdout:
                line = line.decode('utf8')
                self.update_status(line)
            logging.warning('! nothing to read')
        logging.warning("\nProcess ended")
        return True

    def update_status(self, line):
        size = filename = None
        try:
            size, filename, _  = line.split('$')
        except ValueError:
            logging.error(line, exc_info = True)
            return None
        if filename in self.transfered_files:
            logging.warning(' + duplicate file')
            return None
        self.transfered_size += int(size)
        self.transfered_files.append(filename)
        prct = 100 * (self.transfered_size / self.source_size)
        data = B_to_readable(self.transfered_size)
        self.percent.set(int(prct))
        self.transfered_size_str.set(B_to_readable(self.transfered_size))
        self.progress_value.set(self.transfered_size)   

    def status(self) -> float:
        ''' return None if not running, or percentage executed'''
        if not self.isrunning():
            return None
        return round(self.transfered_size / self.source_size, 4)
