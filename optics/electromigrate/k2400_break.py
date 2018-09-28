import numpy as np
from optics.misc_utility.curve_fit_equations import linear_fit, linear
import matplotlib
matplotlib.use('TkAgg')
import os
from itertools import count
import csv
import tkinter as tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure


class KeithleyBreak:
    def __init__(self, master, sourcemeter, filepath, device, steps=11, stop_voltage=0.05, desired_resistance=80,
                 break_voltage=1.5, passes=1, increase_break_voltage=True, delta_break_voltage=0.005, start_voltage=.1,
                 delta_voltage=0.002, r_percent=.4, abort=False):
        self._master = master
        # ready the device
        self._sourcemeter = sourcemeter
        self._sourcemeter.reset()
        self._sourcemeter.set_voltage(0)
        self._sourcemeter.configure_measurement()
        self._sourcemeter.configure_measurement(measurement_mode=0)
        self._sourcemeter.display_measurement(displayed_measurement_mode=1)
        self._sourcemeter.enable_output()
        self._sourcemeter.configure_measurement(measurement_mode=1, auto_range=False, manual_range=0.1)
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
        self._j = count(0)
        self._filename = os.path.join(filepath, '{}_k2400break_'.format(device))
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
        self._break_voltage = break_voltage
        self._passes = passes
        self._increase_break_voltage = increase_break_voltage
        self._delta_break_voltage = delta_break_voltage
        self._start_voltage = start_voltage
        self._delta_voltage = delta_voltage
        self._r_percent = r_percent
        self._c = count(0)
        self._stop_voltage = stop_voltage
        self._steps = steps
        self._pass = count(0)
        self._points = []

    def abort(self):
        self._abort = True

    def do_nothing(self):
        pass

    def measure_resistance(self):
        values = np.zeros((self._steps+1, 2))
        self._points = []
        for n, i in enumerate(np.linspace(0, self._stop_voltage, self._steps+1)):
            self._master.update()
            self._sourcemeter.set_voltage(i)
            v, j, _, _, _ = self._sourcemeter.read_points()
            values[n] = v, j
            self._master.after(self._wait_time, self.do_nothing())
            self._points.append(self._ax1.scatter(i, j))
            self._ax1.set_ylim(np.amin(values[:, 1]) * 0.9, np.amax(values[:, 1]) * 1.1)
            self._ax1.title.set_text('Measuring resistance\nCurrent resistance: %s ohms' % np.ceil(i / j))
            self._fig.canvas.draw()
        self._sourcemeter.set_voltage(0)
        m, b, _, _ = linear_fit(values[:, 0], values[:, 1])
        self._sweep_resistance = 1/m
        self._writer.writerow([self._sweep_resistance])
        linspace = np.linspace(np.amin(values[:, 0]), np.amax(values[:, 0]), 100)
        self._ln, = self._ax1.plot(linspace, linear(linspace, m, b))
        self._ax1.title.set_text('Measured resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
        self._fig.canvas.draw()
        self.check_status()

    def remove_points(self):
        for x in self._points:
            x.remove()
        self._ln.remove()

    def check_status(self):
        if self._sweep_resistance >= self._desired_resistance:
            self._message = 'resistance reached desired resistance'
            self._writer.writerow([self._sweep_resistance])
            self._abort = True
            self._sourcemeter.set_voltage(0)
            raise NameError
        if self._sweep_resistance < 0:
            self._message = 'slope was negative'
            self._writer.writerow([self._sweep_resistance])
            self._abort = True
            self._sourcemeter.set_voltage(0)
            raise NameError
        if self._current_dropped:
            self._message = 'current dropped'
            self._writer.writerow([self._sweep_resistance])
            self._abort = True
            self._sourcemeter.set_voltage(0)
            raise NameError
        if self._abort:
            self._message = 'Aborted'
            self._sourcemeter.set_voltage(0)
            raise NameError

    def loop_one(self, current_break_voltage):
        if not self._abort:
            self._master.update()
            currents = []
            voltages = []
            points = []
            for n, v_applied in enumerate(np.arange(self._start_voltage, current_break_voltage, self._delta_voltage)):
                self._master.update()
                self._ax3.barh(1, 1, 0.35, color='white')
                self._sourcemeter.set_voltage(v_applied)
                v, j, _, _, _ = self._sourcemeter.read_points()
                voltages.append(v_applied)
                currents.append(j)
                percent_max = j / np.amax(currents)
                points.append(self._ax2.scatter(v, j))
                self._ax2.title.set_text('Breaking junction\nCurrent resistance: %s ohms' % np.ceil(v / j))
                self._ax3.barh(1, percent_max, 0.35)
                self._ax3.title.set_text('Percent of maximum current: %s %%' % np.ceil(percent_max * 100))
                self._ax3.set_xlim(0, 1)
                self._fig.canvas.draw()
                self._master.update()
                if n > 1:
                    upper = (1 + self._r_percent / 100) * voltages[n - 1] / currents[n - 1]
                    lower = (1 - self._r_percent / 100) * voltages[n - 1] / currents[n - 1]
                    if not lower < v / j < upper:
                        self._current_dropped = True
                        print('current dropped')
                        break
                if self._abort:
                    break
            if len(currents) > 3:
                linspace = np.linspace(self._start_voltage, current_break_voltage, 100)
                m, b, _, _ = linear_fit(voltages, currents)
                self._sweep_resistance = 1 / m
                ln, = self._ax2.plot(linspace, linear(linspace, m, b))
                self._ax2.title.set_text('Breaking resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
                self._fig.canvas.draw()
                self._master.after(250, self.do_nothing())
                ln.remove()
            self._sourcemeter.set_voltage(0)
            for x in points:
                x.remove()
            if next(self._pass) >= self._passes and self._increase_break_voltage:
                current_break_voltage += self._delta_break_voltage
            if not self._current_dropped or not self._abort: # this is pretty much a while loop, but you can't use a while loop in Tkinter
                self.loop_one(current_break_voltage)

    def loop_two(self):
        self._master.update()
        current_break_voltage = self._break_voltage
        self._pass = count(0)
        self.loop_one(current_break_voltage)
        stop = False
        if self._sweep_resistance >= self._desired_resistance:
            self._fig.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
            self._ln.remove()
            stop = True
        if self._sweep_resistance < 0:
            self._fig.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
            self._ln.remove()
            stop = True
        if self._current_dropped:
            self._ln.remove()
        if not self._abort and not self._current_dropped and not stop:
            self.loop_two()

    def break_junction(self):
        self._current_dropped = False
        self.loop_two()

    def main_loop(self):
        with open(self._filename + '%s.csv' % next(self._j), 'w', newline='') as inputfile:
            self._writer = csv.writer(inputfile)
            self._writer.writerow(['resistance'])
            self.measure_resistance()
            self.break_junction()
            self.remove_points()
        self.main_loop()

    def main(self):
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        try:
            self.main_loop()
        except NameError:
            print(self._message)
            print('Final resistance: %s ohms' % np.ceil(self._sweep_resistance))
            self._fig.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
            self._sourcemeter.set_voltage(0)