import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.misc_utility import scanner
import csv
import numpy as np
import matplotlib.pyplot as plt
from optics.thermovoltage_plot import thermovoltage_plot
from tkinter import *
import warnings
import os
from os import path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from optics.misc_utility.random import tk_sleep


class ThermovoltageScanDC:
    def __init__(self, master, filepath, notes, device, scan, gain, xd, yd, xr, yr, xc, yc, npc3sg_x, npc3sg_y, q,
                 powermeter, polarizer, direction=True):
        self._master = master
        self._filepath = filepath
        self._gain = gain
        self._notes = notes
        self._device = device
        self._q = q
        self._scan = scan
        self._xd = xd  # x pixel density
        self._yd = yd  # y pixel density
        self._yr = yr  # y range
        self._xr = xr  # x range
        self._xc = xc  # x center position
        self._yc = yc  # y center position
        self._polarizer = polarizer
        self._measuredpolarization = self._polarizer.read_polarization()
        self._polarization = int(round((np.round(self._measuredpolarization, 0) % 180)/10)*10)
        self._fig = Figure()
        self._ax1 = self._fig.add_subplot(111)
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._powermeter = powermeter
        self._norm = thermovoltage_plot.MidpointNormalize(midpoint=0)
        self._z1 = np.zeros((self._xd, self._yd))
        self._im1 = self._ax1.imshow(self._z1.T, norm=self._norm, cmap=plt.cm.coolwarm, interpolation='nearest',
                                     origin='lower')
        self._clb1 = self._fig.colorbar(self._im1, ax=self._ax1)
        self._imagefile = None
        self._filename = None
        self._writer = None
        self._x_val, self._y_val = scanner.find_scan_values(self._xc, self._yc, self._xr, self._yr, self._xd, self._yd)
        self._direction = direction
        if not self._direction:
            self._y_val = self._y_val[::-1]
        self._fig.tight_layout()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._abort = False

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
        self._writer.writerow(['actual polarization:', self._measuredpolarization])
        self._writer.writerow(['power (W):', self._powermeter.read_power()])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['v_raw', 'v_dc', 'x_pixel', 'y_pixel'])

    def setup_plots(self):
        self._clb1.set_label('voltage (uV)', rotation=270, labelpad=20)
        self._ax1.title.set_text('X_1')

    def update_plot(self, im, data, min_val, max_val):
        im.set_data(data.T)
        im.set_clim(vmin=min_val)
        im.set_clim(vmax=max_val)

    def onclick(self, event):
        try:
            points = [int(np.ceil(event.xdata-0.5)), int(np.ceil(event.ydata-0.5))]
            self._npc3sg_x.move(self._x_val[points[0]])
            self._npc3sg_y.move(self._y_val[points[1]])
            print('pixel: ' + str(points))
            print('position: ' + str(self._x_val[points[0]]) + ', ' + str(self._y_val[points[1]]))
        except:
            print('invalid position')

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._filename = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, self._polarization, 'DC', index,
                                                                          '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, self._polarization, 'DC',
                                                                           index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, self._polarization, 'DC',
                                                                              index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, self._polarization, 'DC',
                                                                               index, '.png'))

    def run_scan(self):
        for y_ind, i in enumerate(self._y_val):
            if self._abort:
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
                break
            self._master.update()
            if not self._direction:
                y_ind = len(self._y_val) - y_ind - 1
            self._npc3sg_y.move(i)
            for x_ind, j in enumerate(self._x_val):
                if self._abort:
                    self._npc3sg_x.move(0)
                    self._npc3sg_y.move(0)
                    break
                self._master.update()
                self._npc3sg_x.move(j)
                tk_sleep(self._master, 300)
                data = self._q.read()
                raw = data[0] - data[1]
                voltage = raw / self._gain
                self._writer.writerow([raw, voltage, x_ind, y_ind])
                self._z1[x_ind][y_ind] = voltage * 1000000
                self.update_plot(self._im1, self._z1, -np.amax(np.abs(self._z1)), np.amax(np.abs(self._z1)))
                self._fig.tight_layout()
                self._fig.canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
        self._npc3sg_x.move(0)
        self._npc3sg_y.move(0)  # returns piezo controller position to 0,0

    def main(self):
        self.makefile()
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._writer = csv.writer(inputfile)
                self.setup_plots()
                self.write_header()
                self.run_scan()
                thermovoltage_plot.plot(self._ax1, self._im1, self._z1, np.amax(np.abs(self._z1)), -np.amax(np.abs(self._z1)))
                self._canvas.draw()
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
                thermovoltage_plot.plot(self._ax1, self._im1, self._z1, np.amax(np.abs(self._z1)), -np.amax(np.abs(self._z1)))
                self._canvas.draw() # shows the completed scan
                warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
                # that was never written
                cid = self._fig.canvas.mpl_connect('button_press_event', self.onclick)  # click on pixel to move laser position there
            except KeyboardInterrupt:
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
            except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
                pass