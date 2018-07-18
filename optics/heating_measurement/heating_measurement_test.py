import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.misc_utility import scanner, conversions
import csv
import time
import matplotlib.pyplot as plt
from tkinter import *
import warnings
import os
from os import path
from optics.heating_plot import heating_plot
import numpy as np


def read_if_exists(field, function, *args):
    if field:
        return getattr(field, function)(*args)


class Measurements:
    def __init__(self):
        pass

    def make_filepaths(self, filepath, device, scan, descriptor, format_list):
        os.makedirs(filepath, exist_ok=True)
        index = scan
        filename = path.join(filepath, '{}_{}_{}'.format(device, descriptor, index))
        while path.exists(filename):
            index += 1
            filename = path.join(filepath, '{}_{}_{}'.format(device, descriptor, index))
        return ['{}.{}'.format(filename, f) for f in format_list]


class Maps(Measurements):
    def __init__(self):
        super().__init__()

    def write_header(self, writer, gain, xd, yd, xr, yr, xc, yc, polarizer, powermeter):
        writer.writerow(['gain', gain])
        writer.writerow(['x scan density', xd])
        writer.writerow(['y scan density', yd])
        writer.writerow(['x range', xr])
        writer.writerow(['y range', yr])
        writer.writerow(['x center', xc])
        writer.writerow(['y center', yc])
        writer.writerow(['polarization', read_if_exists(polarizer, 'read_polarization') if
                         read_if_exists(polarizer, 'read_polarization') else 'not measured'])
        writer.writerow(['power (W)', read_if_exists(powermeter, 'read_power') if
                         read_if_exists(powermeter, 'read_power') else 'not measured'])



class HeatingMaps(Maps):
    def __init__(self, filepath, device, scan, polarizer):
        super().__init__()
        self._polarizer = polarizer
        if self._polarizer:
            descriptor = int(round((np.round(self._polarizer.read_polarization(), 0) % 180) / 10) * 10)
        else:
            descriptor = 'heating map'
        self._filepath, self._figurepath = self.make_filepaths(filepath, device, scan, descriptor, ['csv', 'png'])




















