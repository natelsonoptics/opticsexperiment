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
import matplotlib.pyplot as plt
from optics import heating_plot


class BaseRamanMeasurement:
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate=None, powermeter=None):
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
        if waveplate:
            self._polarization = int(round((np.round(waveplate.read_polarization(), 0) % 180) / 10) * 10)
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


class RamanMapScan(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, filepath, notes, device, index, xd, yd, xr, yr, xc, yc,
                 npc3sg_x, npc3sg_y, npc3sg_input, start, stop, sleep_time, powermeter, waveplate, direction=True):
        self._master = master
        self._notes = notes
        self._device = device
        super().__init__(self._master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter)
        self._xd = xd  # x pixel density
        self._yd = yd  # y pixel density
        self._yr = yr  # y range
        self._xr = xr  # x range
        self._xc = xc  # x center position
        self._yc = yc  # y center position
        self._start = start
        self._stop = stop
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._powermeter = powermeter
        self._z1 = np.zeros((self._xd, self._yd))
        self._z2 = np.zeros((self._xd, self._yd))
        self._im1 = self._single_ax1.imshow(self._z1.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self._clb1 = self._single_fig.colorbar(self._im1, ax=self._single_ax1)
        self._writer = None
        self._x_val, self._y_val = scanner.find_scan_values(self._xc, self._yc, self._xr, self._yr, self._xd, self._yd)
        self._direction = direction
        if not self._direction:
            self._y_val = self._y_val[::-1]
        self._sleep_time = sleep_time

    def abort(self):
        self._abort = True

    def write_header(self):
        self._writer.writerow(['x scan density:', self._xd])
        self._writer.writerow(['y scan density:', self._yd])
        self._writer.writerow(['x range:', self._xr])
        self._writer.writerow(['y range:', self._yr])
        self._writer.writerow(['x center:', self._xc])
        self._writer.writerow(['y center:', self._yc])
        self._writer.writerow(['polarization:', self._polarization])
        if self._powermeter:
            self._writer.writerow(['power (W):', self._powermeter.read_power()])
        else:
            self._writer.writerow(['power (W):', 'not measured'])
        self._writer.writerow(['laser wavelength:', laser_wavelength])
        gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
        self._writer.writerow(['raman gain:', gain_options[self._raman_gain]])
        self._writer.writerow(['center wavelength:', self._center_wavelength])
        self._writer.writerow(['acquisitions:', self._acquisitions])
        self._writer.writerow(['integration time:', self._integration_time])
        self._writer.writerow(['shutter open:', self._shutter])
        self._writer.writerow(['dark current corrected:', self._dark_current])
        self._writer.writerow(['dark corrected:', self._dark_corrected])
        self._writer.writerow(['grating:', self._grating])
        self._writer.writerow(['time between scans:', self._sleep_time])
        self._writer.writerow(['x value units:', self._units])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['x values', *self._xvalues])


    def setup_plots(self):
        self._clb1.set_label('counts', rotation=270, labelpad=20)
        self._single_ax1.title.set_text('Raman signal {} - {} {}'.format(self._start, self._stop, self._units))

    def update_plot(self, im, data, min_val, max_val):
        im.set_data(data.T)
        im.set_clim(vmin=min_val)
        im.set_clim(vmax=max_val)

    def onclick(self, event):
        try:
            points = [int(np.ceil(event.xdata - 0.5)), int(np.ceil(event.ydata - 0.5))]
            if not self._direction:
                points = [int(np.ceil(event.xdata - 0.5)), int(np.ceil(self._yd - event.ydata - 0.5 - 1))]
            self._npc3sg_x.move(self._x_val[points[0]])
            self._npc3sg_y.move(self._y_val[points[1]])
            print('pixel: ' + str(points))
            print('position: ' + str(self._x_val[points[0]]) + ', ' + str(self._y_val[points[1]]))
        except:
            print('invalid position')

    def run_scan(self):
        for y_ind, i in enumerate(self._y_val):
            self._master.update()
            if self._abort:
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
                break
            if not self._direction:
                y_ind = len(self._y_val) - y_ind - 1
            self._npc3sg_y.move(i)
            for x_ind, j in enumerate(self._x_val):
                self._npc3sg_x.move(j)
                tk_sleep(self._master, 1000 * self._sleep_time)  # DO NOT USE TIME.SLEEP IN TKINTER LOOP
                _, data = self.take_spectrum()
                integrated = self.integrate_spectrum(data, self._start, self._stop)
                self._writer.writerow([(x_ind, y_ind), *integrated])
                self._z1[x_ind][y_ind] = integrated
                self.update_plot(self._im1, self._z1, np.amin(self._z1), np.amax(self._z1))
                self._single_fig.tight_layout()
                self._single_canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
                self._master.update()
                if self._abort:
                    self._npc3sg_x.move(0)
                    self._npc3sg_y.move(0)
                    break
        self._npc3sg_x.move(0)
        self._npc3sg_y.move(0)  # returns piezo controller position to 0,0

    def main(self):
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        self.make_file('Raman map')
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._writer = csv.writer(inputfile)
                self.setup_plots()
                self._single_canvas.draw()
                self.write_header()
                self.run_scan()
                heating_plot.plot(self._single_ax1, self._im1, self._z1, np.amax(self._z1), np.amin(self._z1))
                self._single_canvas.draw()
                self._single_fig.savefig(self._imagefile, format='png',
                                  bbox_inches='tight')  # saves an image of the completed data
                heating_plot.plot(self._single_ax1, self._im1, self._z1, np.amax(self._z1), np.amin(self._z1))
                self._single_canvas.draw()  # shows the completed scan
                warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
                # that was never written
                cid = self._single_fig.canvas.mpl_connect('button_press_event',
                                                   self.onclick)  # click on pixel to move laser position there
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
            except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
                pass










