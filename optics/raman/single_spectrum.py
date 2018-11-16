import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.misc_utility import scanner, conversions
import csv
import numpy as np
from optics.thermovoltage_plot import thermovoltage_plot
from tkinter import *
import warnings
import os
from os import path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
from optics.raman.unit_conversions import convert_pixels_to_unit
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength


def take_single_spectrum(ccd, grating, raman_gain, center_wavelength=785, units='nm', integration_time=1, acqusitions=1, shutter=True):
    raw, data = ccd.take_spectrum(integration_time, raman_gain, acqusitions, shutter)
    plt.plot(convert_pixels_to_unit(units, grating, center_wavelength, laser_wavelength), data)
    plt.xlabel(units)
    plt.ylabel('counts')
    plt.show()