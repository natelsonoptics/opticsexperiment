import matplotlib
matplotlib.use('TkAgg')
import time
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
from itertools import count
import csv
import os
from os import path


class K2400Break:
    def __init__(self, filepath, device, desired_resistance, start_voltage_resistance, stop_voltage_resistance, steps,
                 start_break_voltage, break_voltage, max_break_voltage, delta_break_voltage, percent_drop, notes,
                 keithley):
        self._filepath = filepath
        self._device = device
        self._desired_resistance = desired_resistance
        self._start_voltage_resistance = start_voltage_resistance
        self._stop_voltage_resistance = stop_voltage_resistance
        self._steps = steps
        self._break_voltage = break_voltage
        self._max_break_voltage = max_break_voltage
        self._delta_break_voltage = delta_break_voltage
        self._percent_drop = percent_drop
        self._notes = notes
        self._keithley = keithley
        self._filename = None
        self._current_drop = False
        self._c = count(0)
        self._j = count(0)
        self._fig, (self._ax1, self._ax2, self._ax3) = plt.subplots(3)
        self._writer = None
        self._current_break_voltage = None
        self._start_break_voltage = start_break_voltage
        self._resistance = []
        self._voltages = []
        self._currents = []
        self._sweep_resistance = None
        self._ln2 = None
        self._message = None
        self._points = []

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        self._filename = path.join(self._filepath, '{}_'.format(self._device))
        while os.path.exists(self._filename+'0') or os.path.exists(self._filename+'0.csv'):
            self._filename = self._filename + '(1)'

    def setup_plots(self):
        self._ax3.barh(1, 1, 0.35, color='w')
        self._ax1.title.set_text('Measured resistance: \nCurrent resistance: ')
        self._ax2.title.set_text('Breaking resistance: \nCurrent resistance: ')
        self._ax3.title.set_text('Percent of maximum current: ')
        self._ax3.set_xlim(0, 1)
        plt.tight_layout()
        self._fig.show()

    def linear(self, x, M, B):
        return M * x + B

    def measure_current_resistance(self):
        self._resistance = []
        self._voltages = []
        self._currents = []
        for i in range(self._steps):
            voltage = self._stop_voltage_resistance * (i + 1) / self._steps
            self._keithley.set_voltage(voltage)
            time.sleep(0.1)
            self._currents.append(self._keithley.measure_current())
            time.sleep(0.1)
            self._voltages.append(voltage)
            self._resistance.append(self._voltages[i] / self._currents[i])
            self._ax1.scatter(self._voltages[i], self._currents[i])
            self._ax1.set_ylim(np.amin(self._currents) * 0.9, np.amax(self._currents) * 1.1)
            self._ax1.title.set_text('Measuring resistance\nCurrent resistance: %s ohms' % np.ceil(self._resistance[i]))
            self._fig.canvas.draw()

    def measure_resistance(self):
        # measure resistance
        self.measure_current_resistance()
        p, pcov = curve_fit(self.linear, self._voltages, self._currents)
        self._keithley.set_voltage(0)
        self._sweep_resistance = 1 / p[0]
        self._writer.writerow([self._sweep_resistance])
        voltage_linspace = np.linspace(np.amin(self._voltages), np.amax(self._voltages), 100)
        self._ln2, = self._ax1.plot(voltage_linspace, self.linear(voltage_linspace, p[0], p[1]))
        self._ax1.title.set_text('Measured resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
        self._fig.canvas.draw()
        if self._sweep_resistance >= self._desired_resistance:
            self._message = 'resistance reached desired resistance'
            self._writer.writerow([self._sweep_resistance])
            raise NameError
        if self._sweep_resistance < 0:
            self._message = 'slope was negative'
            self._writer.writerow([self._sweep_resistance])
            raise NameError
        if self._current_drop:
            self._message = 'current dropped'
            self._writer.writerow([self._sweep_resistance])
            raise NameError
        if self._current_break_voltage > self._max_break_voltage:
            self._message = 'break voltage exceeded maximum value'
            self._writer.writerow([self._sweep_resistance])
            raise NameError
        if np.size(np.arange(self._start_break_voltage, self._current_break_voltage, self._delta_break_voltage)) < 3:
            self._message = 'not enough points for break resistance fit. increase maximum break voltage'
            self._writer.writerow([self._sweep_resistance])
            raise NameError

    def break_junction(self):
        #  break junction
        self._currents = []
        self._voltages = []
        self._points = []
        while not self._current_drop:
            for i, v in enumerate(np.arange(self._start_break_voltage, self._current_break_voltage,
                                            self._delta_break_voltage)):
                self._keithley.set_voltage(v)
                self._ax3.barh(1, 1, 0.35, color='white')
                self._currents.append(self._keithley.measure_current())
                self._voltages.append(v)
                percent_max = self._currents[i] / np.amax(self._currents)
                self._ax2.title.set_text('Breaking junction\nCurrent resistance: %s ohms'
                                   % np.ceil(self._voltages[i] / self._currents[i]))
                self._ax3.barh(1, percent_max, 0.35)
                self._ax3.set_xlim(0, 1)
                point = self._ax2.scatter(self._voltages[i], self._currents[i])
                self._points.append(point)
                self._ax2.set_ylim(np.amin(self._currents) * 0.5, np.amax(self._currents) * 1.5)
                self._ax3.title.set_text('Percent of maximum current: %s %%' % np.ceil(percent_max * 100))
                self._fig.canvas.draw()
                if i > 0:
                    lower = (1 - self._percent_drop / 100) * self._voltages[i - 1] / self._currents[i - 1]
                    upper = (self._percent_drop / 100 + 1) * self._voltages[i - 1] / self._currents[i - 1]
                    if not lower < self._voltages[i] / self._currents[i] < upper:
                        self._current_drop = True
                        print('current dropped')
                        break
            voltage_linspace = np.linspace(np.amin(self._voltages), np.amax(self._voltages), 100)
            p, pcov = curve_fit(self.linear, self._voltages, self._currents)
            ln, = self._ax2.plot(voltage_linspace, self.linear(voltage_linspace, p[0], p[1]))
            self._fig.canvas.draw()
            time.sleep(0.5)
            self._keithley.set_voltage(0)
            resistance = 1 / p[0]
            self._ax2.title.set_text('Breaking resistance: %s ohms\n ' % np.ceil(resistance))
            self._currents = []
            self._voltages = []
            ln.remove()
            for x in self._points:
                x.remove()
            self._points = []
            if resistance >= self._desired_resistance or resistance < 0:
                plt.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
                # saves an image of the completed data
                self._ln2.remove()
                break
            self._current_break_voltage += self._delta_break_voltage
            if self._current_break_voltage > self._max_break_voltage:
                self._start_break_voltage += self._delta_break_voltage
                plt.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
                self._ln2.remove()
                break

    def main(self):
        self.makefile()
        self.setup_plots()
        self._keithley.configure()
        try:
            while True:
                with open(self._filename + '%s.csv' % next(self._j), 'w', newline='') as fn:
                    self._writer = csv.writer(fn)
                    self._writer.writerow(['resistance'])
                    self._current_break_voltage = self._break_voltage
                    self.measure_resistance()
                    self.break_junction()
        except NameError:
            print(self._message)
            print('Final resistance: %s ohms' % np.ceil(self._sweep_resistance))
            self._keithley.set_voltage(0)









