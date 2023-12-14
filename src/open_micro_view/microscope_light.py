# OpenMicroView: GUI for the open source, Raspberry Pi based namesake Microscope
# Copyright (C) 2023 V. Salvadori

from tkinter import IntVar

import board
import neopixel

# LED Strip  Configuration
LED_COUNT = 7            # Number of LEDs
LED_PIN = board.D18      # GPIO Pin
LED_ORDER = neopixel.RGBW


class Light():
    """ OpenMicroView Microscope Light """
    def __init__(self):
        # by default light is off
        self.brightness:IntVar = IntVar()
        # default color is white
        self.color:dict = {'r':IntVar(), 'g':IntVar(), 'b':IntVar(), 'w':IntVar()}
        self.pixels:neopixel.NeoPixel = neopixel.NeoPixel(LED_PIN, LED_COUNT,
                                                          pixel_order=LED_ORDER,
                                                          brightness=self.get_brightness(),
                                                          auto_write=True)
        self.set_color('w', 255)
        self.set_color('r', 0)
        self.set_color('g', 0)
        self.set_color('b', 0)
        self.reload()

    # Reload function applies the changes to the hardware.
    def reload(self):
        self.pixels.brightness = self.get_brightness()
        self.pixels.fill((self.get_color('g'),
                          self.get_color('r'),
                          self.get_color('b'),
                          self.get_color('w')))

    def on(self):
        self.brightness.set(100)
        self.reload()

    def off(self):
        self.brightness.set(0)
        self.reload()

    def set_red(self, n:int):
        self.set_color('r', n)

    def set_green(self, n:int):
        self.set_color('g', n)

    def set_blue(self, n:int):
        self.set_color('b', n)

    def set_white(self, n:int):
        self.set_color('w', n)

    def set_color(self, color:str, n:int):
        if color in ['r','g','b','w']:
            self.color[color].set(round(float(n)))
            self.reload()
        else:
            raise ValueError(f"Color '{color}' not in ['r','g','b','w']. ")

    def set_brightness(self, b:float):
        self.brightness.set(round(float(b)))
        self.reload()

    def get_brightness(self) -> float:
        return self.brightness.get() / 100

    def get_color(self, color) -> int:
        return int(self.color[color].get())

    def get_colors(self) -> int:
        return {k: v.get() for k, v in self.color.items()}

    def toggle(self) -> bool:
        # If light is on turn it off, if its off turn it on
        self.set_brightness(0 if self.brightness.get() else 100)
        self.reload()
        return self.brightness.get() > 0
