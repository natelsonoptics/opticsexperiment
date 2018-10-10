import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from optics.misc_utility.tkinter_utilities import tk_sleep
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
import csv
from optics.misc_utility import conversions
import os
from os import path
import numpy as np
import tkinter as tk

class HeatingTime:
    def __init__(self, master, filepath, notes, device, scan, gain, rate, maxtime, bias, osc, npc3sg_input, sr7270_top,
                 sr7270_bottom, powermeter, polarizer):
        self._master = master
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._polarizer = polarizer
        self._measuredpolarization = self._polarizer.read_polarization()
        self._polarization = int(round((np.round(self._measuredpolarization, 0) % 180) / 10) * 10)
        self._npc3sg_input = npc3sg_input
        self._sr7270_top = sr7270_top
        self._sr7270_bottom = sr7270_bottom
        self._powermeter = powermeter
        self._rate = rate
        self._maxtime = maxtime
        self._writer = None
        self._fig = Figure()
        self._ax1 = self._fig.add_subplot(211)
        self._ax2 = self._fig.add_subplot(212)
        self._max_iphoto_x = 0
        self._min_iphoto_x = 0
        self._max_iphoto_y = 0
        self._min_iphoto_y = 0
        self._start_time = None
        self._iphoto = None
        self._sleep = 1 / self._rate * 1000
        self._bias = bias
        self._osc = osc
        self._filename = None
        self._imagefile = None
        self._fig.tight_layout()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._abort = False

    def abort(self):
        self._abort = True

    def write_header(self):
        position = self._npc3sg_input.read()
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['x laser position:', position[0]])
        self._writer.writerow(['y laser position:', position[1]])
        self._writer.writerow(['polarization:', self._polarization])
        self._writer.writerow(['actual polarization:', self._measuredpolarization])
        self._writer.writerow(['power (W):', self._powermeter.read_power()])
        self._writer.writerow(['applied voltage (V):', self._sr7270_top.read_applied_voltage()])
        self._writer.writerow(['osc amplitude (V):', self._sr7270_top.read_oscillator_amplitude()])
        self._writer.writerow(['osc frequency:', self._sr7270_top.read_oscillator_frequency()])
        self._writer.writerow(['time constant:', self._sr7270_bottom.read_tc()])
        self._writer.writerow(['top time constant:', self._sr7270_top.read_tc()])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['time', 'x_raw', 'y_raw', 'iphoto_x', 'iphoto_y'])

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, self._polarization, index, '.png'))

    def setup_plots(self):
        self._ax1.title.set_text('X_1')
        self._ax2.title.set_text('Y_1')
        self._ax1.set_ylabel('current (mA)')
        self._ax2.set_ylabel('current (mA)')
        self._ax1.set_xlabel('time (s)')
        self._ax2.set_xlabel('time (s)')
        self._canvas.draw()

    def set_limits(self):
        if self._iphoto[0] > self._max_iphoto_x:
            self._max_iphoto_x = self._iphoto[0]
        if self._iphoto[0] < self._min_iphoto_x:
            self._min_iphoto_x = self._iphoto[0]
        if 0 < self._min_iphoto_x < self._max_iphoto_x:
            self._ax1.set_ylim(self._min_iphoto_x * 1000 / 1.3, self._max_iphoto_x * 1.3 * 1000)
        if self._min_iphoto_x < 0 < self._max_iphoto_x:
            self._ax1.set_ylim(self._min_iphoto_x * 1.3 * 1000, self._max_iphoto_x * 1.3 * 1000)
        if self._min_iphoto_x < self._max_iphoto_x < 0:
            self._ax1.set_ylim(self._min_iphoto_x * 1.3 * 1000, self._max_iphoto_x * 1 / 1.3 * 1000)
        if self._iphoto[1] > self._max_iphoto_y:
            self._max_iphoto_y = self._iphoto[1]
        if self._iphoto[1] < self._min_iphoto_y:
            self._min_iphoto_y = self._iphoto[1]
        if self._min_iphoto_y > 0 < self._max_iphoto_y:
            self._ax2.set_ylim(self._min_iphoto_y * 1000 / 1.3, self._max_iphoto_y * 1.3 * 1000)
        if self._min_iphoto_y < 0 < self._max_iphoto_y:
            self._ax2.set_ylim(self._min_iphoto_y * 1.3 * 1000, self._max_iphoto_y * 1.3 * 1000)
        if self._min_iphoto_y > self._max_iphoto_y > 0:
            self._ax2.set_ylim(self._min_iphoto_y * 1.3 * 1000, self._max_iphoto_y / 1.3 * 1000)

    def measure(self):
        self._master.update()
        raw = self._sr7270_bottom.read_xy()
        self._iphoto = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        tk_sleep(self._master, self._sleep)
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, raw[0], raw[1], self._iphoto[0], self._iphoto[1]])
        self._ax1.plot(time_now, self._iphoto[0] * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self._ax2.plot(time_now, self._iphoto[1] * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self.set_limits()
        self._fig.tight_layout()
        self._fig.canvas.draw()
        self._master.update()
        if not self._abort and time.time() - self._start_time < self._maxtime:
            self.measure()

    def main(self):
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        self.makefile()
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._sr7270_top.change_applied_voltage(self._bias)
                tk_sleep(self._master, 300)
                self._sr7270_top.change_oscillator_amplitude(self._osc)
                tk_sleep(self._master, 300)
                self._start_time = time.time()
                self._writer = csv.writer(inputfile)
                self.write_header()
                self.setup_plots()
                self.measure()
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data