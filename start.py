#!/usr/bin/python3
# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

# Configure log format
fmt = "OpenMicroView.%(threadName)-14s: [%(levelname)-7s][%(module)s:%(funcName)s]  %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)

from src import open_micro_view

# Start interface
if __name__ == '__main__':
    open_micro_view.start()
