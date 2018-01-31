import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions
import os
from os import path

class ThermovoltageIntensity:
    def __init__(self, filepath, notes, device, scan, gain, maxtime, polarization, steps,
                 npc3sg_input, sr7270_top, sr7270_bottom, powermeter, attenuatorwheel):
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._steps = steps
        self._polarization = polarization
        self._npc3sg_input = npc3sg_input
        self._sr7270_top = sr7270_top
        self._sr7270_bottom = sr7270_bottom
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._maxtime = maxtime
        self._writer = None
        self._fig, (self._ax1, self._ax2, self._ax3) = plt.subplots(3)
        self._max_voltage_x = 0
        self._min_voltage_x = 0
        self._max_voltage_y = 0
        self._min_voltage_y = 0
        self._max_power = 0
        self._min_power = 0
        self._start_time = None
        self._voltages = None
        self._power = None
        self._filename = None
        self._imagefile = None

    def write_header(self):
        position = self._npc3sg_input.read()
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['x laser position:', position[0]])
        self._writer.writerow(['y laser position:', position[1]])
        self._writer.writerow(['polarization:', self._polarization])
        self._writer.writerow(['time constant:', self._sr7270_bottom.read_tc()[0]])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['time', 'power', 'x_raw', 'y_raw', 'x_v', 'y_v'])

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
        self._ax3.title.set_text('Power on sample')
        self._ax1.set_ylabel('voltage (uV)')
        self._ax2.set_ylabel('voltage (uV)')
        self._ax3.set_ylabel('power (mW)')
        self._ax1.set_xlabel('time (s)')
        self._ax2.set_xlabel('time (s)')
        self._ax3.set_xlabel('time (s)')
        self._fig.show()

    def set_limits(self):
        if self._voltages[0] > self._max_voltage_x:
            self._max_voltage_x = self._voltages[0]
        if self._voltages[0] < self._min_voltage_x:
            self._min_voltage_x = self._voltages[0]
        if 0 < self._min_voltage_x < self._max_voltage_x:
            self._ax1.set_ylim(self._min_voltage_x * 1000000 / 2, self._max_voltage_x * 2 * 1000000)
        if self._min_voltage_x < 0 < self._max_voltage_x:
            self._ax1.set_ylim(self._min_voltage_x * 2 * 1000000, self._max_voltage_x * 2 * 1000000)
        if self._min_voltage_x < self._max_voltage_x < 0:
            self._ax1.set_ylim(self._min_voltage_x * 2 * 1000000, self._max_voltage_x * 1 / 2 * 1000000)
        if self._voltages[1] > self._max_voltage_y:
            self._max_voltage_y = self._voltages[1]
        if self._voltages[1] < self._min_voltage_y:
            self._min_voltage_y = self._voltages[1]
        if self._min_voltage_y > 0 < self._max_voltage_y:
            self._ax2.set_ylim(self._min_voltage_y * 1000000 / 2, self._max_voltage_y * 2 * 1000000)
        if self._min_voltage_y < 0 < self._max_voltage_y:
            self._ax2.set_ylim(self._min_voltage_y * 2 * 1000000, self._max_voltage_y * 2 * 1000000)
        if self._min_voltage_y > self._max_voltage_y > 0:
            self._ax2.set_ylim(self._min_voltage_y * 2 * 1000000, self._max_voltage_y * 1 / 2 * 1000000)
        if self._power > self._max_power:
            self._max_power = self._power
        if self._power < self._min_power:
            self._min_power = self._power
        self._ax3.set_ylim(self._min_power * 1 / 2 * 1000, self._max_power * 2 * 1000)

    def measure(self):
        self._attenuatorwheel.step(self._steps, 0.005)
        time.sleep(0.1)
        time_now = time.time() - self._start_time
        self._power = self._powermeter.read_power()
        raw = self._sr7270_bottom.read_xy()
        self._voltages = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        self._writer.writerow([time_now, self._power, raw[0], raw[1], self._voltages[0], self._voltages[1]])
        self._ax1.scatter(time_now, self._voltages[0] * 1000000, c='b', s=2)
        self._ax2.scatter(time_now, self._voltages[1] * 1000000, c='b', s=2)
        self._ax3.scatter(time_now, self._power * 1000, c='b', s=2)
        self.set_limits()
        plt.tight_layout()
        self._fig.canvas.draw()

    def main(self):
        self.makefile()
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._start_time = time.time()
                self._writer = csv.writer(inputfile)
                self.write_header()
                self.setup_plots()
                while time.time() - self._start_time < self._maxtime:
                    self.measure()
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data

