import contextlib
import visa
import time
import numpy as np
from optics.misc_utility.curve_fit_equations import linear_fit, linear
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import os
from itertools import count
import csv


@contextlib.contextmanager
def connect(address):
    rm = visa.ResourceManager()
    rm.list_resources()
    inst = rm.open_resource(address)
    try:
        yield SourceMeter(inst)
    finally:
        SourceMeter(inst).set_voltage(0)


class SourceMeter:
    def __init__(self, inst):
        self._inst = inst

    def reset(self):
        self._inst.write('*RST')

    def configure_source(self, source_mode=0, compliance_level=0.1, output_level=0):
        """source_mode: 0 for voltage, 1 for current"""
        self._inst.write(':SOUR:FUNC {}'.format('VOLT' if source_mode == 0 else 'CURR'))
        self._inst.write(':SOUR:{} {}'.format('VOLT' if source_mode == 0 else 'CURR', output_level))
        self._inst.write(':{}:PROT {}'.format('CURR' if source_mode == 0 else 'VOLT', compliance_level))

    def set_voltage(self, output_level, compliance_level=0.1):
        self.configure_source(source_mode=0, compliance_level=compliance_level, output_level=output_level)

    def configure_measurement(self, measurement_mode=0, auto_range=True, manual_range=0.1):
        """measurement_mode: 0 for voltage, 1 for current, 2 for resistance"""
        values = {0: 'VOLT', 1: 'CURR', 2: 'RES'}
        self._inst.write('SENS:{}:RANG:AUTO {}'.format(values[measurement_mode], 'ON' if auto_range else 'OFF'))
        if not auto_range:
            self._inst.write(':{}:RANG {}'.format(values[measurement_mode], manual_range))

    def display_measurement(self, displayed_measurement_mode=0):
        """displayed_measurement_mode: 0 for voltage, 1 for current, 2 for resistance"""
        values = {0: 15, 1: 22, 2: 29}
        self._inst.write(':SYST:KEY {}'.format(values[displayed_measurement_mode]))

    def enable_output(self, enabled=True):
        self._inst.write(':OUTP {}'.format('ON' if enabled else 'OFF'))

    def configure_multipoint(self, output_mode=0, arm_count=1, trigger_count=1):
        """output mode: 0 for fix, 1 for sweep, 2 for list"""
        values = {0: 'FIX', 1: 'SWE', 2: 'LIST'}
        self._inst.write(':ARM:COUN {}'.format(arm_count))
        self._inst.write(':TRIG:COUN {}'.format(trigger_count))
        self._inst.write(':SOUR:VOLT:MODE {}'.format(values[output_mode]))
        self._inst.write(':SOUR:CURR:MODE {}'.format(values[output_mode]))

    def configure_trigger(self, arming_source=0, timer_setting=0.01, trigger_source=0, trigger_delay=0):
        """arming_source: 0: immediate, 1: bus, 2: tim, 3: man, 4: tlin, 5: nst, 6L pst, 7:bst
        trigger_source: 0: immediate, 1 tlin"""
        arming_values = {0: 'IMM', 1: 'BUS', 2: 'TIM', 3: 'MAN', 4: 'TLIN', 5: "NST", 6: 'PST', 7: 'BST'}
        trigger_values = {0: 'IMM', 1: 'TLIN'}
        self._inst.write(':ARM:SOUR {}'.format(arming_values[arming_source]))
        self._inst.write(':ARM:TIM {}'.format(timer_setting))
        self._inst.write(':TRIG:SOUR {}'.format(trigger_values[trigger_source]))
        self._inst.write(':TRIG:DEL {}'.format(trigger_delay))

    def initiate_trigger(self):
        self._inst.write(':TRIG:CLE')  # clears trigger first
        self._inst.write(':INIT')  # initiates

    def wait_for_operation_complete(self, timeout=10):
        starttime = time.time()
        while time.time() < starttime + timeout:
            if float(self._inst.query('*OPC?')) == 1:
                break
            time.sleep(0.1)

    def fetch(self):
        return [float(i) for i in self._inst.query(':FETC?').strip().split(',')]

    def read_points(self, counts=1, timeout=10):
        self.configure_multipoint(trigger_count=counts)
        self.configure_trigger()
        self.initiate_trigger()
        self.wait_for_operation_complete(timeout=timeout)
        voltage, current, resistance, timestamp, status = self.fetch()
        return voltage, current, resistance, timestamp, status


class KeithleyBreak:
    def __init__(self, sourcemeter, filepath, device, steps=11, stop_voltage=0.05, desired_resistance=80,
                 break_voltage=1.5, passes=1, increase_break_voltage=True, delta_break_voltage=0.005, start_voltage=.1,
                 delta_voltage=0.002, r_percent=.4, abort=False):
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
        self._r_percent = r_percent
        self._c = count(0)
        self._stop_voltage = stop_voltage
        self._steps = steps

    def measure_resistance(self):
        values = np.zeros((self._steps+1, 2))
        for n, i in enumerate(np.linspace(0, self._stop_voltage, self._steps+1)):
            self._sourcemeter.set_voltage(i)
            v, j, _, _, _ = self._sourcemeter.read_points()
            values[n] = v, j
            time.sleep(self._wait_time)
            self._ax1.scatter(i, j)
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

    def break_junction(self):
        while not self._abort:
            current_break_voltage = self._break_voltage
            passes = count(0)
            while not self._current_dropped:
                currents = []
                voltages = []
                points = []
                j = self._start_voltage / self._sweep_resistance
                for n, v_applied in enumerate(np.arange(self._start_voltage, current_break_voltage,
                                                        self._delta_voltage)):
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
                    if n > 1:
                        upper = (1 + self._r_percent / 100) * voltages[n-1] / currents[n-1]
                        lower = (1 - self._r_percent / 100) * voltages[n-1] / currents[n-1]
                        if not lower < v / j < upper:
                            self._current_dropped = True
                            print('current dropped')
                            break
                linspace = np.linspace(self._start_voltage, current_break_voltage, 100)
                m, b, _, _ = linear_fit(voltages, currents)
                self._sweep_resistance = 1/m
                ln, = self._ax2.plot(linspace, linear(linspace, m, b))
                self._ax2.title.set_text('Breaking resistance: %s ohms\n ' % np.ceil(self._sweep_resistance))
                self._fig.canvas.draw()
                self._sourcemeter.set_voltage(0)
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
            self._sourcemeter.set_voltage(0)





















