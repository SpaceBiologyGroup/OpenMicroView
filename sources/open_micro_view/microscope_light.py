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
                                                          brightness=self.getBrightness(),
                                                          auto_write=True)
        self.setColor('w', 255)
        self.setColor('r', 0)
        self.setColor('g', 0)
        self.setColor('b', 0)
        self.reload()

    # Reload function applies the changes to the hardware.
    def reload(self):
        self.pixels.brightness = self.getBrightness()
        self.pixels.fill((self.getColor('g'),
                          self.getColor('r'),
                          self.getColor('b'),
                          self.getColor('w')))

    def on(self):
        self.brightness.set(100)
        self.reload()

    def off(self):
        self.brightness.set(0)
        self.reload()

    def setRed(self, n:int):
        self.setColor('r', n)

    def setGreen(self, n:int):
        self.setColor('g', n)

    def setBlue(self, n:int):
        self.setColor('b', n)

    def setWhite(self, n:int):
        self.setColor('w', n)

    def setColor(self, color:str, n:int):
        if color in ['r','g','b','w']:
            self.color[color].set(round(float(n)))
            self.reload()
        else:
            raise ValueError(f"Color '{color}' not in ['r','g','b','w']. ")

    def set_brightness(self, b:float):
        self.brightness.set(round(float(b)))
        self.reload()

    def getBrightness(self) -> float:
        return self.brightness.get() / 100

    def getColor(self, color) -> int:
        return int(self.color[color].get())

    def getColors(self) -> int:
        return {k: v.get() for k, v in self.color.items()}

    def toggle(self) -> bool:
        # If light is on turn it off, if its off turn it on
        self.set_brightness(0 if self.brightness.get() else 100)
        self.reload()
        return self.brightness.get() > 0
