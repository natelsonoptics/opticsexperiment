import numpy as np
from optics.misc_utility.curve_fit_equations import linear_fit, linear
from optics.misc_utility.curve_fit_equations import proportional_fit, proportional
import matplotlib
matplotlib.use('TkAgg')
import os
from itertools import count
import csv
from optics.misc_utility.conversions import convert_x_to_iphoto
from optics.misc_utility.random import tk_sleep
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class DAQBreak:
    def __init__(self, master, ao, ai, filepath, device, steps=11, stop_voltage=0.05, desired_resistance=80,
                 break_voltage=1.5, passes=1, increase_break_voltage=True, delta_break_voltage=0.005, start_voltage=.1,
                 delta_voltage=0.002, current_drop=50e-6, abort=False, gain=1000):
        self._master = master
        # ready the device
        self._ao = ao
        self._ai = ai
        self._ao.source_voltage(0)
        # set up the plots
        self._fig = Figure()
        self._ax1 = self._fig.add_subplot(311)
        self._ax2 = self._fig.add_subplot(312)
        self._ax3 = self._fig.add_subplot(313)
        self._ax3.barh(1, 1, 0.35, color='w')
        self._ax1.title.set_text('Measured resistance: \nCurrent resistance: ')
        self._ax2.title.set_text('Breaking resistance: \nCurrent resistance: ')
        self._ax3.title.set_text('Percent of maximum current: ')
        self._ax3.set_xlim(0, 1)
        self._fig.tight_layout()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._ln = None
        # create the filename
        os.makedirs(filepath, exist_ok=True)
        self._c = count(0)
        self._j = count(0)
        self._k = count(0)
        self._filename = os.path.join(filepath, '{}_daq_break_'.format(device))
        while os.path.exists(self._filename + '0.csv'):
            self._filename = self._filename + '1'
        # create the status tools
        self._abort = abort
        self._current_dropped = False
        self._message = 'Unknown error'
        # set the class variables
        self._sweep_resistance = 0
        self._desired_resistance = desired_resistance
        self._wait_time = 100
        self._writer = None
        self._sweep_writer = None
        self._break_voltage = break_voltage
        self._passes = passes
        self._increase_break_voltage = increase_break_voltage
        self._delta_break_voltage = delta_break_voltage
        self._start_voltage = start_voltage
        self._delta_voltage = delta_voltage
        self._current_drop = current_drop
        self._stop_voltage = stop_voltage
        self._steps = steps
        self._gain = gain
        self._current_break_voltage = self._break_voltage
        self._points = []

    def abort(self):
        self._abort = True

    def write_header(self):
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['start voltage:', self._start_voltage])
        self._writer.writerow(['start break voltage:', self._break_voltage])
        self._writer.writerow(['desired resistance:', self._desired_resistance])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['voltage', 'current', 'v/i'])
        self._sweep_writer.writerow(['gain:', self._gain])
        self._sweep_writer.writerow(['desired resistance:', self._desired_resistance])
        self._sweep_writer.writerow(['end:', 'end of header'])
        self._sweep_writer.writerow(['voltage', 'current'])

    def read_current(self):
        return convert_x_to_iphoto(self._ai.read()[0], self._gain, square_wave=False)

    def measure_resistance(self):
        if self._ln:
            [x[0].remove() for x in self._points]
            self._ln.remove()
        self._points = []
        values = np.zeros((self._steps+1, 2))
        for n, v in enumerate(np.linspace(0, self._stop_voltage, self._steps+1)):
            self._master.update()
            self._ao.source_voltage(v)
            j = self.read_current()
            values[n] = v, j
            tk_sleep(self._master, self._wait_time)
            self._points.append(self._ax1.plot(v, j, linestyle='', color='blue', marker='o', markersize=5))
            self._ax1.set_ylim(np.amin(values[:, 1]) * 0.9, np.amax(values[:, 1]) * 1.1)
            self._ax1.title.set_text('Measuring resistance\nCurrent resistance: %s ohms' % np.ceil(v / j))
            self._fig.canvas.draw()
            self._sweep_writer.writerow([v, j])
        self._ao.source_voltage(0)
        m, b, _, _ = linear_fit(values[:, 0], values[:, 1])
        self._sweep_resistance = 1/m
        linspace = np.linspace(np.amin(values[:, 0]), np.amax(values[:, 0]), 100)
        self._ln, = self._ax1.plot(linspace, linear(linspace, m, b))
        self._ax1.title.set_text('Measured resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
        self._fig.canvas.draw()
        self._master.update()
        self.check_status()

    def check_status(self):
        if self._sweep_resistance >= self._desired_resistance:
            self._message = 'resistance reached desired resistance'
            self._abort = True
            self._ao.source_voltage(0)
            raise NameError
        if self._sweep_resistance < 0:
            self._message = 'slope was negative'
            self._abort = True
            self._ao.source_voltage(0)
            raise NameError
        if self._current_dropped:
            self._message = 'current dropped'
            self._abort = True
            self._ao.source_voltage(0)
            raise NameError
        if self._abort:
            self._message = 'Aborted'
            self._ao.source_voltage(0)
            raise NameError

    def continue_breaking(self):
        if not self._abort and not self._current_dropped and not self._sweep_resistance >= self._desired_resistance \
                and not self._sweep_resistance < 0:
            return True
        else:
            return False

    def ramp_voltage(self):
        currents = []
        voltages = []
        points = []
        for n, v in enumerate(np.arange(self._start_voltage, self._current_break_voltage, self._delta_voltage)):
            self._master.update()
            if self._abort:
                break
            self._ao.source_voltage(v)
            i = self.read_current()
            self._writer.writerow([v, i, v/i])
            voltages.append(v)
            currents.append(i)
            percent_max = i / np.amax(currents)
            points.append(self._ax2.plot(v, i, linestyle='', color='blue', marker='o', markersize=5))
            self._ax2.title.set_text('Breaking junction\nCurrent resistance: %s ohms' % np.ceil(v / i))
            bar = self._ax3.barh(1, percent_max, 0.35, color='cyan')
            self._ax3.title.set_text('Percent of maximum current: %s %%' % np.ceil(percent_max * 100))
            self._canvas.draw()
            bar.remove()
            if v / i > self._desired_resistance:
                break
            if n > 1:
                if i < currents[n - 1] - self._current_drop:
                    self._current_dropped = True
                    print('current dropped')
                    break
        if len(currents) > 3:
            linspace = np.linspace(self._start_voltage, self._current_break_voltage, 100)
            m, _ = proportional_fit(voltages, currents)
            self._sweep_resistance = 1 / m
            ln, = self._ax2.plot(linspace, proportional(linspace, m))
            self._ax2.title.set_text('Breaking resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
            self._fig.canvas.draw()
            self._ao.source_voltage(0)
            tk_sleep(self._master, 250)
            ln.remove()
        [x[0].remove() for x in points]
        if self._increase_break_voltage:
            self._current_break_voltage += self._delta_break_voltage
        self._master.update()
        if self.continue_breaking():
            self.ramp_voltage()

    def break_junction(self):
        self._current_break_voltage = self._break_voltage
        self.ramp_voltage()
        if not self.continue_breaking():
            self._fig.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
        self._master.update()
        if self.continue_breaking():
            self.break_junction()

    def measure(self):
        with open(self._filename + '%s.csv' % next(self._j), 'w', newline='') as inputfile, \
                open(self._filename + '%s sweep resistance.csv' % next(self._k), 'w', newline='') as fin:
            self._writer = csv.writer(inputfile)
            self._sweep_writer = csv.writer(fin)
            self.write_header()
            self.measure_resistance()
            self.break_junction()
        self.measure()

    def main(self):
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        try:
            self.measure()
        except NameError:
            print(self._message)
            print('Final resistance: %s ohms' % np.ceil(self._sweep_resistance))
            self._ao.source_voltage(0)
