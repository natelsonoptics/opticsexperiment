import matplotlib
matplotlib.use('TkAgg')
from optics.hardware_control import sr7270, npc3sg_analog, hardware_addresses_and_constants
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions
import os
from os import path

class ThermvolageTime:
    def __init__(self):
        self.writer = None


    def write_header(self):
        self.writer.writerow(['gain:', self.gain])
        self.writer.writerow(['x laser position:', self.npc3sg_input.read()[0]])
        self.writer.writerow(['y laser position:', self.npc3sg_input.read()[1]])
        self.writer.writerow(['polarization:', self.polarization])
        self.writer.writerow(['notes:', self.notes])
        self.writer.writerow(['end:', 'end of header'])
        self.writer.writerow(['time', 'x_raw', 'y_raw', 'x_v', 'y_v'])

    def makefile(self):
        os.makedirs(self.filepath, exist_ok=True)
        index = self.scan
        self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.csv'))
        self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.png'))
        while path.exists(self.file):
            index += 1
            self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.csv'))
            self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.png'))

