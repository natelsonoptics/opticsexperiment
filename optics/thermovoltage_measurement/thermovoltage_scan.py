import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.misc_utility import scanner, conversions
import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from optics.thermovoltage_plot import thermovoltage_plot
from tkinter import *
import warnings
import os
from os import path


class ThermovoltageScan:
    def __init__(self, filepath, notes, device, scan, gain, xd, yd, xr, yr, xc, yc, polarization,
                 npc3sg_x, npc3sg_y, npc3sg_input, sr7270_top, sr7270_bottom, powermeter):
        self.filepath = filepath
        self.notes = notes
        self.device = device
        self.scan = scan
        self.gain = gain
        self.xd = xd  # x pixel density
        self.yd = yd  # y pixel density
        self.yr = yr  # y range
        self.xr = xr  # x range
        self.xc = xc  # x center position
        self.yc = yc  # y center position
        self.polarization = polarization
        self.fig, (self.ax1, self.ax2) = plt.subplots(2)
        self.npc3sg_x = npc3sg_x
        self.npc3sg_y = npc3sg_y
        self.npc3sg_input = npc3sg_input
        self.sr7270_top = sr7270_top
        self.sr7270_bottom = sr7270_bottom
        self.powermeter = powermeter
        self.norm = thermovoltage_plot.MidpointNormalize(midpoint=0)
        self.z1 = np.zeros((self.xd, self.yd))
        self.z2 = np.zeros((self.xd, self.yd))
        self.im1 = self.ax1.imshow(self.z1.T, norm=self.norm, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self.im2 = self.ax2.imshow(self.z2.T, norm=self.norm, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self.clb1 = self.fig.colorbar(self.im1, ax=self.ax1)
        self.clb2 = self.fig.colorbar(self.im2, ax=self.ax2)
        self.imagefile = None
        self.file = None
        self.writer = None
        self.x_val, self.y_val = scanner.find_scan_values(self.xc, self.yc, self.xr, self.yr, self.xd, self.yd)

    def write_header(self):
        self.writer.writerow(['gain:', self.gain])
        self.writer.writerow(['x scan density:', self.xd])
        self.writer.writerow(['y scan density:', self.yd])
        self.writer.writerow(['x range:', self.xr])
        self.writer.writerow(['y range:', self.yr])
        self.writer.writerow(['x center:', self.xc])
        self.writer.writerow(['y center:', self.yc])
        self.writer.writerow(['polarization:', self.polarization])
        self.writer.writerow(['power (W):', self.powermeter.read_power()])
        self.writer.writerow(['notes:', self.notes])
        self.writer.writerow(['end:', 'end of header'])
        self.writer.writerow(['x_raw', 'y_raw', 'x_v', 'y_v', 'x_pixel', 'y_pixel'])

    def setup_plots(self):
        self.clb1.set_label('voltage (uV)', rotation=270, labelpad=20)
        self.clb2.set_label('voltage (uV)', rotation=270, labelpad=20)
        self.ax1.title.set_text('X_1')
        self.ax2.title.set_text('Y_1')

    def update_plot(self, im, data, min_val, max_val):
        im.set_data(data.T)
        im.set_clim(vmin=min_val)
        im.set_clim(vmax=max_val)

    def onclick(self, event):
        try:
            points = [int(np.ceil(event.xdata-0.5)), int(np.ceil(event.ydata-0.5))]
            self.npc3sg_x.move(self.x_val[points[0]])
            self.npc3sg_y.move(self.y_val[points[1]])
            print('pixel: ' + str(points))
            print('position: ' + str(self.x_val[points[0]]) + ', ' + str(self.y_val[points[1]]))
        except:
            print('invalid position')

    def makefile(self):
        os.makedirs(self.filepath, exist_ok=True)
        index = self.scan
        self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.csv'))
        self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.png'))
        while path.exists(self.file):
            index += 1
            self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.csv'))
            self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.png'))

    def run_scan(self):
        for y_ind, i in enumerate(self.y_val):
            self.npc3sg_y.move(i)
            for x_ind, j in enumerate(self.x_val):
                self.npc3sg_x.move(j)
                time.sleep(0.3)
                raw = self.sr7270_bottom.read_xy()
                voltages = [conversions.convert_x_to_iphoto(x, self.gain) for x in raw]
                self.writer.writerow([raw[0], raw[1], voltages[0], voltages[1], x_ind, y_ind])
                self.z1[x_ind][y_ind] = voltages[0] * 1000000
                self.z2[x_ind][y_ind] = voltages[1] * 1000000
                self.update_plot(self.im1, self.z1, -np.amax(np.abs(self.z1)), np.amax(np.abs(self.z1)))
                self.update_plot(self.im2, self.z2, -np.amax(np.abs(self.z2)), np.amax(np.abs(self.z2)))
                plt.tight_layout()
                self.fig.canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
        self.npc3sg_x.move(0)
        self.npc3sg_y.move(0)  # returns piezo controller position to 0,0

    def main(self):
        self.makefile()
        with open(self.file, 'w', newline='') as inputfile:
            try:
                self.writer = csv.writer(inputfile)
                self.setup_plots()
                self.fig.show()
                self.write_header()
                self.run_scan()
                thermovoltage_plot.plot(self.ax1, self.im1, self.z1, np.amax(np.abs(self.z1)), -np.amax(np.abs(self.z1)))
                thermovoltage_plot.plot(self.ax2, self.im2, self.z2, np.amax(np.abs(self.z2)), -np.amax(np.abs(self.z2)))
                plt.savefig(self.imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
                thermovoltage_plot.plot(self.ax1, self.im1, self.z1, np.amax(np.abs(self.z1)), -np.amax(np.abs(self.z1)))
                thermovoltage_plot.plot(self.ax2, self.im2, self.z2, np.amax(np.abs(self.z2)), -np.amax(np.abs(self.z2)))
                self.fig.show()  # shows the completed scan
                warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
                # that was never written
                cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)  # click on pixel to move laser position there
                plt.pause(-1)  # keeps the figure open indefinitely until you close it
            except KeyboardInterrupt:
                plt.savefig(self.imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
                self.npc3sg_x.move(0)
                self.npc3sg_y.move(0)
            except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
                pass