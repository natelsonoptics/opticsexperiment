from optics.raman.single_spectrum import BaseRamanMeasurement
import csv
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import tkinter as tk
import matplotlib.pyplot as plt
from optics.misc_utility.tkinter_utilities import tk_sleep
from optics.misc_utility import conversions
import numpy as np


class RamanPolarization(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, start, stop, steps,
                  waveplate, powermeter, npc3sg_input):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter,
                         single_plot=True, polar=True)
        self._sleep_time = sleep_time
        self._start = start
        self._stop = stop
        self._new_start = tk.StringVar()
        self._new_stop = tk.StringVar()
        self._new_start.set(self._start)
        self._new_stop.set(self._stop)
        self._powermeter = powermeter
        self._waveplate = waveplate
        self._waveplate_angle = int(round(float(str(self._waveplate.read_position())))) % 360
        self._max_waveplate_angle = self._waveplate_angle + 180
        self._npc3sg_input = npc3sg_input
        self._steps = steps
        self._polarizations = []

    def write_header(self):
        with open(self._filename, 'w', newline='') as inputfile:
            writer = csv.writer(inputfile)
            position = self._npc3sg_input.read()
            writer.writerow(['x laser position:', position[0]])
            writer.writerow(['y laser position:', position[1]])
            if self._powermeter:
                writer.writerow(['power (W):', self._powermeter.read_power()])
            else:
                writer.writerow(['power (W):', 'not measured'])
            writer.writerow(['laser wavelength:', laser_wavelength])
            gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
            writer.writerow(['raman gain:', gain_options[self._raman_gain]])
            writer.writerow(['center wavelength:', self._center_wavelength])
            writer.writerow(['acquisitions:', self._acquisitions])
            writer.writerow(['integration time:', self._integration_time])
            writer.writerow(['shutter open:', self._shutter])
            writer.writerow(['dark current corrected:', self._dark_current])
            writer.writerow(['dark corrected:', self._dark_corrected])
            writer.writerow(['grating:', self._grating])
            writer.writerow(['time between scans (s):', self._sleep_time])
            writer.writerow(['notes:', self._notes])
            writer.writerow(['x value units:', self._units])
            writer.writerow(['end:', 'end of header'])
            writer.writerow(['x values', *self._xvalues])

    def plot_point(self, x, y):
        self._single_ax1.plot(x, y, linestyle='', color='blue', marker='o', markersize=5, picker=5)
        self._single_ax1.set_xlabel('power on sample (mW)')
        self._single_ax1.set_ylabel('counts')
        self._single_fig.tight_layout()
        self._single_canvas.draw()
        self._single_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def measure(self):
        with open(self._filename, 'a', newline='') as inputfile:
            writer = csv.writer(inputfile)
            for i in np.arange(self._waveplate_angle, self._max_waveplate_angle, self._steps):
                if self._abort:
                    break
                self._master.update()
                self._waveplate.move(i)
                tk_sleep(self._master, 1500)
                self._master.update()
                polarization = float(str(self._waveplate.read_polarization())) % 360
                self._polarizations.append(polarization)
                # converts waveplate angle to polarizaiton angle
                _, data = self.take_spectrum()
                writer.writerow(['polarization {}'.format(polarization), *data])
                integrated = self.integrate_spectrum(data, self._start, self._stop)
                self._single_ax1.plot(conversions.degrees_to_radians(polarization), integrated, linestyle='',
                                      color='blue', marker='o', markersize=2)
                self._single_fig.tight_layout()
                self._single_canvas.draw()
                self._single_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
                self._master.update()

    def onpick(self, event):
        xdata = event.xdata * 180 / np.pi
        idx = (np.abs(np.asarray(self._polarizations) - xdata)).argmin()
        point = self._polarizations[idx]
        print(point)
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'polarization {}'.format(point) in row:
                    title = row[0]
                    data = [float(i) for i in row[1::]]
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    ax.set_title('{}, {}'.format(self._device, title))
                    ax.set_xlabel(self._units)
                    ax.plot(self._xvalues, data)
                    fig.show()

    def replot(self):
        start = float(self._new_start.get())
        stop = float(self._new_stop.get())
        polarization = []
        data = []
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'polarization' in row[0]:
                    polarization.append(float(row[0].split(' ')[1]))
                    data.append(self.integrate_spectrum([float(i) for i in row[1::]], start, stop))
        fig = plt.figure()
        ax = fig.add_subplot(111, polar=True)
        ax.set_title('{} polarization scan, {} - {} {}'.format(self._device, start, stop, self._units))
        ax.scatter([conversions.degrees_to_radians(i) for i in polarization], data)
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
        self._single_ax1.set_title('{} polarization scan, {} - {} {}'.format(self._device, self._start, self._stop,
                                                                             self._units))
        self._single_fig.tight_layout()
        self.make_file(measurement_title='polarization measurement')
        self.write_header()
        self.measure()
        self._single_fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        self._single_fig.canvas.mpl_connect('button_press_event', self.onpick)
