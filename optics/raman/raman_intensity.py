from optics.raman.single_spectrum import BaseRamanMeasurement
import csv
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import tkinter as tk
import matplotlib.pyplot as plt
from optics.misc_utility.tkinter_utilities import tk_sleep


class RamanIntensity(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, maxtime, start, stop,
                 steps, powermeter, attenuatorwheel, waveplate=None):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter)
        self._sleep_time = sleep_time
        self._maxtime = maxtime
        self._start = start
        self._stop = stop
        self._new_start = tk.StringVar()
        self._new_stop = tk.StringVar()
        self._new_start.set(self._start)
        self._new_stop.set(self._stop)
        self._steps = steps
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel

    def write_header(self):
        with open(self._filename, 'w', newline='') as inputfile:
            writer = csv.writer(inputfile)
            writer.writerow(['laser wavelength:', laser_wavelength])
            writer.writerow(['polarization:', self._polarization])
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
        start_time = time.time()
        with open(self._filename, 'a', newline='') as inputfile:
            writer = csv.writer(inputfile)
            while time.time() - start_time < self._maxtime:
                now = time.time() - start_time
                self._attenuatorwheel.step(self._steps, 0.005)
                tk_sleep(self._master, 300)
                power = self._powermeter.read_power()
                self.take_spectrum()
                writer.writerow(['power {}'.format(power), *[i for i in self._data]])
                self.plot_point(now, self.integrate_spectrum(self._data, self._start, self._stop))
                tk_sleep(self._master, self._sleep_time * 1000)
                self._master.update()
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
                if 'power {}'.format(point) in row:
                    title = row[0]
                    data = [float(i) for i in row[1::]]
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    ax.set_title('{}, {} polarization, {} mW'.format(self._device, self._polarization, title))
                    ax.set_xlabel(self._units)
                    ax.set_ylabel('counts')
                    ax.plot(self._xvalues, data)
                    fig.show()

    def replot(self):
        start = float(self._new_start.get())
        stop = float(self._new_stop.get())
        power = []
        data = []
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'power' in row[0]:
                    power.append(float(row[0].split('scan ')[1]))
                    data.append(self.integrate_spectrum([float(i) for i in row[1::]], start, stop))
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title('{} time scan, {} polarization, {} - {} {}'.format(self._device, self._polarization, start, stop,
                                                                        self._units))
        ax.scatter(power, data)
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
        self._single_ax1.set_title('{} intensity scan, {} polarization, {} - {} {}'.format(self._device, self._polarization,
                                                                                      self._start, self._stop,
                                                                                      self._units))
        self._single_fig.tight_layout()
        self.make_file(measurement_title='intensity measurement')
        self.write_header()
        self.measure()
        self._single_fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        self._single_fig.canvas.mpl_connect('pick_event', self.onpick)
