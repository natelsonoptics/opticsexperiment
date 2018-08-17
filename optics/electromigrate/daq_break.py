import time
import numpy as np
from optics.misc_utility.curve_fit_equations import linear_fit, linear
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import os
from itertools import count
import csv
from optics.misc_utility.conversions import convert_x_to_iphoto


class DAQBreak:
    def __init__(self, ao, ai, filepath, device, steps=11, stop_voltage=0.05, desired_resistance=80,
                 break_voltage=1.5, passes=1, increase_break_voltage=True, delta_break_voltage=0.005, start_voltage=.1,
                 delta_voltage=0.002, current_drop=50e-6, abort=False, gain=1000):
        # ready the device
        self._ao = ao
        self._ai = ai
        self._ao.source_voltage(0)
        # set up the plots
        self._fig, (self._ax1, self._ax2, self._ax3) = plt.subplots(3)
        self._ax3.barh(1, 1, 0.35, color='w')
        self._ax1.title.set_text('Measured resistance: \nCurrent resistance: ')
        self._ax2.title.set_text('Breaking resistance: \nCurrent resistance: ')
        self._ax3.title.set_text('Percent of maximum current: ')
        self._ax3.set_xlim(0, 1)
        plt.tight_layout()
        self._fig.show()
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
        self._wait_time = 0.1
        self._writer = None
        self._break_voltage = break_voltage
        self._passes = passes
        self._increase_break_voltage = increase_break_voltage
        self._delta_break_voltage = delta_break_voltage
        self._start_voltage = start_voltage
        self._delta_voltage = delta_voltage
        self._current_drop = current_drop
        self._c = count(0)
        self._stop_voltage = stop_voltage
        self._steps = steps
        self._gain = gain

    def read_current(self):
        return convert_x_to_iphoto(self._ai.read()[0], self._gain, square_wave=False)

    def measure_resistance(self):
        values = np.zeros((self._steps+1, 2))
        for n, v in enumerate(np.linspace(0, self._stop_voltage, self._steps+1)):
            self._ao.source_voltage(v)
            j = self.read_current()
            values[n] = v, j
            time.sleep(self._wait_time)
            self._ax1.scatter(v, j)
            self._ax1.set_ylim(np.amin(values[:, 1]) * 0.9, np.amax(values[:, 1]) * 1.1)
            self._ax1.title.set_text('Measuring resistance\nCurrent resistance: %s ohms' % np.ceil(v / j))
            self._fig.canvas.draw()
        self._ao.source_voltage(0)
        m, b, _, _ = linear_fit(values[:, 0], values[:, 1])
        self._sweep_resistance = 1/m
        self._writer.writerow([self._sweep_resistance])
        linspace = np.linspace(np.amin(values[:, 0]), np.amax(values[:, 0]), 100)
        self._ln, = self._ax1.plot(linspace, linear(linspace, m, b))
        self._ax1.title.set_text('Measured resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
        self._fig.canvas.draw()
        self.check_status()

    def check_status(self):
        if self._sweep_resistance >= self._desired_resistance:
            self._message = 'resistance reached desired resistance'
            self._writer.writerow([self._sweep_resistance])
            self._abort = True
            self._ao.source_voltage(0)
            raise NameError
        if self._sweep_resistance < 0:
            self._message = 'slope was negative'
            self._writer.writerow([self._sweep_resistance])
            self._abort = True
            self._ao.source_voltage(0)
            raise NameError
        if self._current_dropped:
            self._message = 'current dropped'
            self._writer.writerow([self._sweep_resistance])
            self._abort = True
            self._ao.source_voltage(0)
            raise NameError
        if self._abort:
            self._message = 'Aborted'
            self._ao.source_voltage(0)
            raise NameError

    def break_junction(self):
        self._current_dropped = False
        m = 1
        while not self._abort and not self._current_dropped:
            current_break_voltage = self._break_voltage
            passes = count(0)
            while not self._current_dropped:
                currents = []
                voltages = []
                points = []
                i = self._start_voltage / self._sweep_resistance
                for n, v in enumerate(np.arange(self._start_voltage, current_break_voltage, self._delta_voltage)):
                    self._ax3.barh(1, 1, 0.35, color='white')
                    self._ao.source_voltage(v)
                    i = self.read_current()
                    voltages.append(v)
                    currents.append(i)
                    percent_max = i / np.amax(currents)
                    points.append(self._ax2.scatter(v, i))
                    self._ax2.title.set_text('Breaking junction\nCurrent resistance: %s ohms' % np.ceil(v / i))
                    self._ax3.barh(1, percent_max, 0.35)
                    self._ax3.title.set_text('Percent of maximum current: %s %%' % np.ceil(percent_max * 100))
                    self._ax3.set_xlim(0, 1)
                    self._fig.canvas.draw()
                    if v / i > self._desired_resistance:
                        break
                    if n > 1:
                        if i < currents[n-1] - self._current_drop:
                            self._current_dropped = True
                            print('current dropped')
                            break
                if len(currents) > 3:
                    linspace = np.linspace(self._start_voltage, current_break_voltage, 100)
                    m, b, _, _ = linear_fit(voltages, currents)
                    self._sweep_resistance = 1/m
                    ln, = self._ax2.plot(linspace, linear(linspace, m, b))
                    self._ax2.title.set_text('Breaking resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
                    self._fig.canvas.draw()
                self._ao.source_voltage(0)
                time.sleep(0.25)
                ln.remove()
                for x in points:
                    x.remove()
                if next(passes) >= self._passes and self._increase_break_voltage:
                    current_break_voltage += self._delta_break_voltage
            if self._sweep_resistance >= self._desired_resistance:
                plt.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
                self._ln.remove()
                break
            if self._sweep_resistance < 0:
                plt.savefig(self._filename + '%s.png' % next(self._c), format='png', bbox_inches='tight')
                self._ln.remove()
                break
            if self._current_dropped:
                self._ln.remove()
                break

    def main(self):
        try:
            while True:
                with open(self._filename + '%s.csv' % next(self._j), 'w', newline='') as inputfile:
                    self._writer = csv.writer(inputfile)
                    self._writer.writerow(['resistance'])
                    self.measure_resistance()
                    self.break_junction()
        except NameError:
            print(self._message)
            print('Final resistance: %s ohms' % np.ceil(self._sweep_resistance))
            self._ao.source_voltage(0)
