from optics.raman.single_spectrum import BaseRamanMeasurement
import csv
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from optics.misc_utility import conversions


class RamanTime(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, number_scans, start,
                 stop, waveplate, powermeter, npc3sg_input):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter,
                         single_plot=False)
        self._sleep_time = sleep_time
        self._start = start
        self._stop = stop
        self._number_scans = number_scans
        self._fig = Figure()
        self._fig.set_size_inches(7, 7)
        self._ax1 = self._fig.add_subplot(211)
        self._ax2 = self._fig.add_subplot(212)
        self._wf = np.zeros((self._number_scans, len(self._xvalues)))
        self._im = self._ax1.imshow(self._wf, interpolation='nearest', origin='lower', aspect='auto',
                                            extent=[self._xvalues[0], self._xvalues[-1], 0, self._number_scans])
        self._ax1.set_xlabel(self._units)
        self._ax1.set_ylabel('scan')
        self._ax2.set_xlabel('time (s)')
        self._ax2.set_ylabel('counts')
        self._ax1.set_title('{} time waterfall, {} polarization'.format(self._device, self._polarization))
        self._ax2.set_title('{} vs time, {} polarization, {} - {} {}'.format(self._device, self._polarization, self._start,
                                                                             self._stop, self._units))
        self._clb1 = self._fig.colorbar(self._im, ax=self._ax1)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._fig.tight_layout()
        self._canvas.draw()
        self._npc3sg_input = npc3sg_input
        self._powermeter = powermeter
        self._new_start.set(self._start)
        self._new_stop.set(self._stop)
        self._times = []

    def write_header(self):
        with open(self._filename, 'w', newline='') as inputfile:
            writer = csv.writer(inputfile)
            position = self._npc3sg_input.read()
            writer.writerow(['x laser position:', position[0]])
            writer.writerow(['y laser position:', position[1]])
            writer.writerow(['laser wavelength:', laser_wavelength])
            if self._powermeter:
                writer.writerow(['power (W):', self._powermeter.read_power()])
            else:
                writer.writerow(['power (W):', 'not measured'])
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
            writer.writerow(['time between scans:', self._sleep_time])
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
        start_time = time.time()
        with open(self._filename, 'a', newline='') as inputfile:
            writer = csv.writer(inputfile)
            for scan in range(self._number_scans):
                now = time.time() - start_time
                self._times.append(now)
                _, data = self.take_spectrum()
                writer.writerow(['time scan {}'.format(now), *[i for i in self._data]])
                self._wf[scan] = data
                self.update_plot(self._im, self._wf)
                integrated = self.integrate_spectrum(data, self._start, self._stop)
                self._ax2.plot(now, integrated, linestyle='', color='blue', marker='o', markersize=4)
                self._fig.tight_layout()
                self._canvas.draw()
                self._master.update()
                tk_sleep(self._master, self._sleep_time * 1000)
                if self._abort:
                    break

    def onpick(self, event):
        ax = event.inaxes
        data = None
        title = ''
        if ax == self._ax1:
            ydata = int(np.ceil(event.ydata - 1))
            with open(self._filename) as inputfile:
                reader = csv.reader(inputfile, delimiter=',')
                for row in reader:
                    if 'end:' in row:
                        break
                for i, row in enumerate(reader):
                    if i == ydata + 1:
                        title = row[0]
                        data = [float(i) for i in row[1::]]
        else:
            xdata = event.xdata
            ind = (np.abs(np.asarray(self._times) - xdata)).argmin()
            point = self._times[ind]
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

    def rescale(self):
        vmax = float(self._new_max.get())
        vmin = float(self._new_min.get())
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('{} time scan, {} polarization'.format(self._device, self._polarization))
        im = ax.imshow(self._wf, interpolation='nearest', origin='lower', aspect='auto', vmax=vmax, vmin=vmin,
                              extent=[self._xvalues[0], self._xvalues[-1], 0, self._number_scans])
        clb = fig.colorbar(im, ax=ax)
        im.set_clim(vmin, vmax)
        ax.set_xlabel('{}'.format(self._units))
        ax.set_ylabel('scan')
        fig.tight_layout()
        fig.show()

    def main(self):
        self.pack_buttons()
        self.make_file(measurement_title='time measurement')
        self.write_header()
        self.measure()
        self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        cid = self._fig.canvas.mpl_connect('button_press_event', self.onpick)  # click on pixel to move laser position there