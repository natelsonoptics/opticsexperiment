import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.misc_utility import scanner, conversions
import csv
import numpy as np
from tkinter import *
import warnings
import os
from os import path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
from optics.raman.unit_conversions import convert_pixels_to_unit
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import matplotlib.pyplot as plt


class BaseRamanMeasurement:
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, polarizer=None, powermeter=None):
        self._master = master
        self._ccd = ccd
        self._grating = grating
        self._raman_gain = raman_gain
        self._center_wavelength = center_wavelength
        self._units = units
        self._integration_time = integration_time
        self._acquisitions = acquisitions
        self._shutter = shutter
        self._dark_current = darkcurrent
        self._dark_corrected = darkcorrected
        self._device = device
        self._filepath = filepath
        self._notes = notes
        self._index = index
        self._data = []
        if polarizer:
            self._polarization = int(round((np.round(polarizer.read_polarization(), 0) % 180) / 10) * 10)
        else:
            self._polarization = 'x'
        if powermeter:
            self._power = powermeter.read_power()
        else:
            self._power = 'not measured'
        self._xvalues = convert_pixels_to_unit(self._units, self._grating, self._center_wavelength, laser_wavelength)
        ## single plot
        self._single_fig = Figure()
        self._single_ax1 = self._single_fig.add_subplot(111)
        self._single_fig.tight_layout()
        self._single_canvas = FigureCanvasTkAgg(self._single_fig, master=self._master)  # A tk.DrawingArea.
        self._filename = None
        self._imagefile = None
        self._abort = False

    def make_file(self, measurement_title='single spectrum'):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._index
        self._filename = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, measurement_title, self._polarization, index, '.csv'))
        self._imagefile = path.join(self._filepath,
                                    '{}_{}_{}_{}{}'.format(self._device, measurement_title, self._polarization, index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath,
                                       '{}_{}_{}_{}{}'.format(self._device, measurement_title, self._polarization, index, '.csv'))
            self._imagefile = path.join(self._filepath,
                                        '{}_{}_{}_{}{}'.format(self._device, measurement_title, self._polarization, index, '.png'))

    def abort(self):
        self._abort = True

    def take_spectrum(self):
        raw, data = self._ccd.take_spectrum(self._integration_time, self._raman_gain, self._acquisitions,
                                            self._shutter, self._dark_current)
        if self._dark_corrected:
            dark_raw, dark_data = self._ccd.take_spectrum(self._integration_time, self._raman_gain, self._acquisitions,
                                                          False, self._dark_corrected)
            raw = raw - dark_raw
            data = data - dark_data
        self._data = data
        return raw, self._data

    def plot_single_spectrum(self):
        self._single_ax1.plot(self._xvalues, self._data)
        self._single_ax1.set_xlabel(self._units)
        self._single_ax1.set_ylabel('counts')
        self._single_fig.tight_layout()
        self._single_canvas.draw()
        self._single_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._single_fig.savefig(self._imagefile, format='png', bbox_inches='tight')

    def integrate_spectrum(self, data, start, stop):
        return np.trapz([data[i] for i in range(len(self._xvalues)) if start <= self._xvalues[i] <= stop],
                        [i for i in self._xvalues if start <= i <= stop])

    def save_single_spectrum(self):
        with open(self._filename, 'w', newline='') as inputfile:
            writer = csv.writer(inputfile)
            writer.writerow(['laser wavelength:', laser_wavelength])
            writer.writerow(['polarization:', self._polarization])
            writer.writerow(['power (W):', self._power])
            gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
            writer.writerow(['raman gain:', gain_options[self._raman_gain]])
            writer.writerow(['center wavelength:', self._center_wavelength])
            writer.writerow(['acquisitions:', self._acquisitions])
            writer.writerow(['integration time:', self._integration_time])
            writer.writerow(['shutter open:', self._shutter])
            writer.writerow(['dark current corrected:', self._dark_current])
            writer.writerow(['dark corrected:', self._dark_corrected])
            writer.writerow(['grating:', self._grating])
            writer.writerow(['notes:', self._notes])
            writer.writerow(['x value units:', self._units])
            writer.writerow(['end:', 'end of header'])
            writer.writerow(['x values', *self._xvalues])
            writer.writerow(['counts', *[i for i in self._data]])

    def main(self):
        self.make_file()
        self._single_ax1.set_title('{} single spectrum, {} polarization'.format(self._device, self._polarization))
        self._single_fig.tight_layout()
        self.take_spectrum()
        self.plot_single_spectrum()
        self.save_single_spectrum()


class RamanTime(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, maxtime, start, stop,
                 polarizer=None, powermeter=None):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, polarizer, powermeter)
        self._sleep_time = sleep_time
        self._maxtime = maxtime
        self._start = start
        self._stop = stop
        self._new_start = tk.StringVar()
        self._new_stop = tk.StringVar()
        self._new_start.set(self._start)
        self._new_stop.set(self._stop)

    def write_header(self):
        with open(self._filename, 'w', newline='') as inputfile:
            writer = csv.writer(inputfile)
            writer.writerow(['laser wavelength:', laser_wavelength])
            writer.writerow(['polarization:', self._polarization])
            writer.writerow(['power (W):', self._power])
            gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
            writer.writerow(['raman gain:', gain_options[self._raman_gain]])
            writer.writerow(['center wavelength:', self._center_wavelength])
            writer.writerow(['acquisitions:', self._acquisitions])
            writer.writerow(['integration time:', self._integration_time])
            writer.writerow(['shutter open:', self._shutter])
            writer.writerow(['dark current corrected:', self._dark_current])
            writer.writerow(['dark corrected:', self._dark_corrected])
            writer.writerow(['grating:', self._grating])
            writer.writerow(['notes:', self._notes])
            writer.writerow(['x value units:', self._units])
            writer.writerow(['end:', 'end of header'])
            writer.writerow(['x values', *self._xvalues])

    def plot_point(self, x, y):
        self._single_ax1.plot(x, y, linestyle='', color='blue', marker='o', markersize=5, picker=5)
        self._single_ax1.set_xlabel('time (s)')
        self._single_ax1.set_ylabel('counts')
        self._single_fig.tight_layout()
        self._single_canvas.draw()
        self._single_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def measure(self):
        start_time = time.time()
        with open(self._filename, 'a', newline='') as inputfile:
            writer = csv.writer(inputfile)
            while time.time() - start_time < self._maxtime:
                now = time.time() - start_time
                self.take_spectrum()
                writer.writerow(['time scan {}'.format(now), *[i for i in self._data]])
                self.plot_point(now, self.integrate_spectrum(self._data, self._start, self._stop))
                self._master.update()
                tk_sleep(self._master, self._sleep_time * 1000)
                if self._abort:
                    break

    def onpick(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ind = event.ind[0]
        point = xdata[ind]
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'time scan {}'.format(point) in row:
                    title = row[0]
                    data = [float(i) for i in row[1::]]
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    ax.set_title('{} seconds'.format(title))
                    ax.set_xlabel(self._units)
                    ax.set_ylabel('counts')
                    ax.plot(self._xvalues, data)
                    fig.show()

    def replot(self):
        start = float(self._new_start.get())
        stop = float(self._new_stop.get())
        time = []
        data = []
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'time scan' in row[0]:
                    time.append(float(row[0].split('scan ')[1]))
                    data.append(self.integrate_spectrum([float(i) for i in row[1::]], start, stop))
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('{} time scan, {} polarization, {} - {} {}'.format(self._device, self._polarization, start, stop,
                                                                        self._units))
        ax.scatter(time, data)
        ax.set_xlabel('time (seconds)')
        ax.set_ylabel('counts')
        fig.show()

    def main(self):
        row = tk.Frame(self._master)
        lab = tk.Label(row, text='start {}'.format(self._units), anchor='w')
        ent = tk.Entry(row, textvariable=self._new_start)
        row.pack(side=tk.TOP)
        lab.pack()
        ent.pack()
        row = tk.Frame(self._master)
        lab = tk.Label(row, text='stop {}'.format(self._units), anchor='w')
        ent = tk.Entry(row, textvariable=self._new_stop)
        row.pack(side=tk.TOP)
        lab.pack()
        ent.pack()
        button = tk.Button(master=row, text="Replot", command=self.replot)
        button.pack()
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        self._single_ax1.set_title('{} time scan, {} polarization, {} - {} {}'.format(self._device, self._polarization,
                                                                                      self._start, self._stop,
                                                                                      self._units))
        self._single_fig.tight_layout()
        self.make_file(measurement_title='time measurement')
        self.write_header()
        self.measure()
        self._single_fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        self._single_fig.canvas.mpl_connect('pick_event', self.onpick)








