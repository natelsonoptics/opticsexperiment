from optics.raman.single_spectrum import BaseRamanMeasurement
import csv
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
import numpy as np
import matplotlib.pyplot as plt
from optics.misc_utility import conversions
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class RamanPolarization(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, steps, start, stop,
                  waveplate, powermeter, npc3sg_input):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter,
                         single_plot=False)
        self._sleep_time = sleep_time
        self._waveplate = waveplate
        waveplate_angle = int(round(float(str(self._waveplate.read_position())))) % 360
        self._powermeter = powermeter
        self._waveplate_positions = np.arange(waveplate_angle, waveplate_angle + 180, steps / 2)
        self._fig = Figure()
        self._fig.set_size_inches(7, 7)
        self._ax1 = self._fig.add_subplot(211)
        self._ax2 = self._fig.add_subplot(212, polar=True)
        self._wf = np.zeros((len(self._waveplate_positions), len(self._xvalues)))
        self._im = self._ax1.imshow(self._wf, interpolation='nearest', origin='lower', aspect='auto',
                                    extent=[self._xvalues[0], self._xvalues[-1], self._waveplate_positions[0] * 2,
                                            self._waveplate_positions[-1] * 2])
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._ax1.set_xlabel(self._units)
        self._ax1.set_ylabel('polarizaiton (degrees)')
        self._clb1 = self._fig.colorbar(self._im, ax=self._ax1)
        self._fig.tight_layout()
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._start = start
        self._stop = stop
        self._npc3sg_input = npc3sg_input
        self._new_start.set(self._start)
        self._new_stop.set(self._stop)

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

    def update_plot(self, im, data):
        im.set_data(data)
        values = np.unique(data)
        im.set_clim(vmin=sorted(values)[1])
        im.set_clim(vmax=np.amax(data))
        self._canvas.draw()

    def measure(self):
        with open(self._filename, 'a', newline='') as inputfile:
            writer = csv.writer(inputfile)
            for i, waveplate_position in enumerate(self._waveplate_positions):
                self._master.update()
                self._waveplate.move(waveplate_position)
                tk_sleep(self._master, 1500)
                _, data = self.take_spectrum()
                writer.writerow(['polarization {}'.format(waveplate_position * 2), *data])
                self._wf[i] = data
                self.update_plot(self._im, self._wf)
                integrated = self.integrate_spectrum(data, self._start, self._stop)
                self._ax2.plot(conversions.degrees_to_radians(waveplate_position * 2), integrated, linestyle='',
                                      color='blue', marker='o', markersize=2)
                self._canvas.draw()
                self._master.update()
                tk_sleep(self._master, self._sleep_time * 1000)
                if self._abort:
                    break

    def onpick(self, event):
        ax = event.inaxes
        if ax == self._ax1:
            ydata = event.ydata
            idx = (np.abs(np.asarray([i * 2 for i in self._waveplate_positions]) - ydata)).argmin()
            point = self._waveplate_positions[idx] * 2
            if point > ydata:
                point = self._waveplate_positions[idx - 1] * 2
        else:
            xdata = event.xdata * 180 / np.pi
            idx = (np.abs(np.asarray([(i * 2) % 360 for i in self._waveplate_positions]) - xdata % 360)).argmin()
            point = self._waveplate_positions[idx] * 2
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'end:' in row:
                    break
            for row in reader:
                if 'polarization {}'.format(point) in row:
                    title = row[0]
                    data = [float(i) for i in row[1::]]
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    ax.set_title('{}, {}'.format(self._device, title))
                    ax.set_xlabel(self._units)
                    ax.set_ylabel('counts')
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

    def rescale(self):
        vmax = float(self._new_max.get())
        vmin = float(self._new_min.get())
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('{} polarization scan'.format(self._device, self._polarization))
        im = ax.imshow(self._wf, interpolation='nearest', origin='lower', aspect='auto', vmax=vmax, vmin=vmin,
                       extent=[self._xvalues[0], self._xvalues[-1], self._waveplate_positions[0] * 2, self._waveplate_positions[-1] * 2])
        clb = fig.colorbar(im, ax=ax)
        im.set_clim(vmin, vmax)
        ax.set_xlabel('{}'.format(self._units))
        ax.set_ylabel('scan')
        fig.tight_layout()
        fig.show()

    def main(self):
        self.pack_buttons()
        self._ax1.set_title('{} polarization waterfall'.format(self._device))
        self._ax2.set_title('{} polarization spectrum, {} - {} {}'.format(self._device, self._start, self._stop, self._units))
        self._fig.tight_layout()
        self.make_file(measurement_title='polarization measurement')
        self.write_header()
        self.measure()
        self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        cid = self._fig.canvas.mpl_connect('button_press_event', self.onpick)  # click on pixel to move laser position there