import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.misc_utility import scanner, conversions
import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from tkinter import *
import warnings
import os
from os import path
from optics.heating_plot import heating_plot

class HeatingScan:
    def __init__(self, filepath, notes, device, scan, gain, bias, osc, xd, yd, xr, yr, xc, yc, polarization,
                 npc3sg_x, npc3sg_y, npc3sg_input, sr7270_top, sr7270_bottom, powermeter):
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._bias = bias
        self._osc = osc
        self._xd = xd  # x pixel density
        self._yd = yd  # y pixel density
        self._yr = yr  # y range
        self._xr = xr  # x range
        self._xc = xc  # x center position
        self._yc = yc  # y center position
        self._polarization = polarization
        self._fig, (self._ax1, self._ax2) = plt.subplots(2)
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_top = sr7270_top
        self._sr7270_bottom = sr7270_bottom
        self._powermeter = powermeter
        self._z1 = np.zeros((self._xd, self._yd))
        self._z2 = np.zeros((self._xd, self._yd))
        self._im1 = self._ax1.imshow(self._z1.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self._im2 = self._ax2.imshow(self._z2.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self._clb1 = self._fig.colorbar(self._im1, ax=self._ax1)
        self._clb2 = self._fig.colorbar(self._im2, ax=self._ax2)
        self._imagefile = None
        self._filename = None
        self._writer = None
        self._x_val, self._y_val = scanner.find_scan_values(self._xc, self._yc, self._xr, self._yr, self._xd, self._yd)

    def write_header(self):
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['x scan density:', self._xd])
        self._writer.writerow(['y scan density:', self._yd])
        self._writer.writerow(['x range:', self._xr])
        self._writer.writerow(['y range:', self._yr])
        self._writer.writerow(['x center:', self._xc])
        self._writer.writerow(['y center:', self._yc])
        self._writer.writerow(['polarization:', self._polarization])
        self._writer.writerow(['power (W):', self._powermeter.read_power()])
        self._writer.writerow(['applied voltage (V):', self._sr7270_top.read_applied_voltage()[0]])
        self._writer.writerow(['osc amplitude (V):', self._sr7270_top.read_oscillator_amplitude()[0]])
        self._writer.writerow(['osc frequency:', self._sr7270_top.read_oscillator_frequency()[0]])
        self._writer.writerow(['time constant:', self._sr7270_bottom.read_tc()[0]])
        self._writer.writerow(['top time constant:', self._sr7270_top.read_tc1()[0]])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['x_raw', 'y_raw', 'x_iphoto', 'y_iphoto', 'x_pixel', 'y_pixel'])

    def setup_plots(self):
        self._clb1.set_label('current (mA)', rotation=270, labelpad=20)
        self._clb2.set_label('current (mA)', rotation=270, labelpad=20)
        self._ax1.title.set_text('iphoto X')
        self._ax2.title.set_text('iphoto Y')

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
        self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.png'))

    def run_scan(self):
        for y_ind, i in enumerate(self._y_val):
            self._npc3sg_y.move(i)
            for x_ind, j in enumerate(self._x_val):
                self._npc3sg_x.move(j)
                time.sleep(0.3)
                raw = self._sr7270_bottom.read_xy()
                currents = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
                self._writer.writerow([raw[0], raw[1], currents[0], currents[1], x_ind, y_ind])
                self._z1[x_ind][y_ind] = currents[0] * 1000
                self._z2[x_ind][y_ind] = currents[1] * 1000
                self.update_plot(self._im1, self._z1, -np.amax(np.abs(self._z1)), np.amax(np.abs(self._z1)))
                self.update_plot(self._im2, self._z2, -np.amax(np.abs(self._z2)), np.amax(np.abs(self._z2)))
                plt.tight_layout()
                self._fig.canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
        self._npc3sg_x.move(0)
        self._npc3sg_y.move(0)  # returns piezo controller position to 0,0

    def main(self):
        self.makefile()
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._writer = csv.writer(inputfile)
                self.setup_plots()
                self._fig.show()
                self._sr7270_top.change_applied_voltage(self._bias)
                time.sleep(0.3)
                self._sr7270_top.change_oscillator_amplitude(self._osc)
                self.write_header()
                self.run_scan()
                heating_plot.plot(self._ax1, self._im1, self._z1, np.amax(np.abs(self._z1)), -np.amax(np.abs(self._z1)))
                heating_plot.plot(self._ax2, self._im2, self._z2, np.amax(np.abs(self._z2)), -np.amax(np.abs(self._z2)))
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
                heating_plot.plot(self._ax1, self._im1, self._z1, np.amax(np.abs(self._z1)), -np.amax(np.abs(self._z1)))
                heating_plot.plot(self._ax2, self._im2, self._z2, np.amax(np.abs(self._z2)), -np.amax(np.abs(self._z2)))
                self._fig.show()  # shows the completed scan
                warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
                # that was never written
                cid = self._fig.canvas.mpl_connect('button_press_event', self.onclick)  # click on pixel to move laser position there
                plt.pause(-1)  # keeps the figure open indefinitely until you close it
            except KeyboardInterrupt:
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
                self._sr7270_top.change_applied_voltage(0)
            except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
                pass