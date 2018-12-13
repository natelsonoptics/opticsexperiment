import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
import csv
from optics.misc_utility import conversions
import os
from os import path
import numpy as np
from optics.misc_utility.tkinter_utilities import tk_sleep
import tkinter as tk



class BaseMeasurement:
    def __init__(self, master, filepath, index, device, waveplate):
        self._abort = False
        self._filepath = filepath
        self._device = device
        self._waveplate = waveplate
        if self._waveplate:
            self._measuredpolarization = self._waveplate.read_polarization()
            self._polarization = int(round((np.round(self._measuredpolarization, 0) % 180) / 10) * 10)
        else:
            self._measuredpolarization = 'x'
            self._polarization = 'x'
        self._index = index
        self._filename = None
        self._imagefile = None
        self._master = master
        self._fig = Figure()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def abort(self):
        self._abort = True

    def make_file(self, measurement_type):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._index
        self._filename = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, measurement_type,
                                                                          self._polarization, index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, measurement_type,
                                                                           self._polarization, index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, measurement_type,
                                                                              self._polarization, index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}_{}{}'.format(self._device, measurement_type,
                                                                               self._polarization, index, '.png'))

    def label_plots(self, ax, title, xlabel, ylabel, tight_layout=True):
        ax.title.set_text(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        self.update_plot(tight_layout)

    def update_plot(self, tight_layout=True):
        if tight_layout:
            self._fig.tight_layout()
        self._fig.canvas.draw()
        self._master.update()

    def add_scatter_point(self, ax, y, linestyle='', color='blue', marker='o', markersize=2, tight_layout=True):
        ax.plot(y, y, linestyle=linestyle, color=color, marker=marker, markersize=markersize)
        self.update_plot(tight_layout)


class BaseLockInIntensityMeasurement(BaseMeasurement):
    def __init__(self, master, filepath, notes, device, index, gain, maxtime, steps,
                 npc3sg_input, sr7270_single_reference, powermeter, attenuatorwheel, waveplate):
        super().__init__(master, filepath, index, device, waveplate)
        self._npc3sg_input = npc3sg_input
        self._master = master
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._gain = gain
        self._steps = steps
        self._npc3sg_input = npc3sg_input
        self._sr7270_single_reference = sr7270_single_reference
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._maxtime = maxtime
        self._writer = None
        self._fig = Figure()
        self._ax1 = self._fig.add_subplot(311)
        self._ax2 = self._fig.add_subplot(312)
        self._ax3 = self._fig.add_subplot(313)
        self._max_x = 0
        self._min_x = 0
        self._max_y = 0
        self._min_y = 0
        self._max_power = 0
        self._min_power = 0
        self._start_time = None
        self._voltages = None
        self._power = None
        self._filename = None
        self._imagefile = None

    def setup_plots(self, voltage=True):
        if voltage:
            label = 'voltage (uV)'
        else:
            label = 'current (mA)'
        for i, j, k in zip((self._ax1, self._ax2, self._ax3), ('X_1', 'Y_1', 'power on sample'),
                           (label, label, 'power (mW)')):
            self.label_plots(i, j, 'time (s)', k)

    def measure(self):
        self._master.update()
        self._attenuatorwheel.step(self._steps, 0.005)
        tk_sleep(self._master, 100)
        time_now = time.time() - self._start_time
        self._power = self._powermeter.read_power()
        raw = self._sr7270_single_reference.read_xy()
        self._voltages = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        self._writer.writerow([time_now, self._power, raw[0], raw[1], self._voltages[0], self._voltages[1]])
        self._ax1.plot(time_now, self._voltages[0] * 1000000, linestyle='', color='blue', marker='o', markersize=2)
        self._ax2.plot(time_now, self._voltages[1] * 1000000, linestyle='', color='blue', marker='o', markersize=2)
        self._ax3.plot(time_now, self._power * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self.set_limits()
        self._fig.tight_layout()
        self._fig.canvas.draw()
        self._master.update()
        if time.time() - self._start_time < self._maxtime and not self._abort:
            self.measure()

    def main(self):
        self.make_file('intensity measurement')
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        with open(self._filename, 'w', newline='') as inputfile:
            self._start_time = time.time()
            self._writer = csv.writer(inputfile)
            self.write_header()
            self.setup_plots()
            self.measure()
            self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')










