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
        self.filepath = filepath
        self.notes = notes
        self.device = device
        self.scan = scan
        self.gain = gain
        self.steps = steps
        self.polarization = polarization
        self.npc3sg_input = npc3sg_input
        self.sr7270_top = sr7270_top
        self.sr7270_bottom = sr7270_bottom
        self.powermeter = powermeter
        self.attenuatorwheel = attenuatorwheel
        self.maxtime = maxtime
        self.writer = None
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3)
        self.max_voltage_x = 0
        self.min_voltage_x = 0
        self.max_voltage_y = 0
        self.min_voltage_y = 0
        self.max_power = 0
        self.min_power = 0
        self.start_time = None
        self.voltages = None
        self.power = None

    def write_header(self):
        position = self.npc3sg_input.read()
        self.writer.writerow(['gain:', self.gain])
        self.writer.writerow(['x laser position:', position[0]])
        self.writer.writerow(['y laser position:', position[1]])
        self.writer.writerow(['polarization:', self.polarization])
        self.writer.writerow(['time constant:', self.sr7270_bottom.read_tc()[0]])
        self.writer.writerow(['notes:', self.notes])
        self.writer.writerow(['end:', 'end of header'])
        self.writer.writerow(['time', 'power', 'x_raw', 'y_raw', 'x_v', 'y_v'])

    def makefile(self):
        os.makedirs(self.filepath, exist_ok=True)
        index = self.scan
        self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.csv'))
        self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.png'))
        while path.exists(self.file):
            index += 1
            self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.csv'))
            self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, self.polarization, index, '.png'))

    def setup_plots(self):
        self.ax1.title.set_text('X_1')
        self.ax2.title.set_text('Y_1')
        self.ax3.title.set_text('Power on sample')
        self.ax1.set_ylabel('voltage (uV)')
        self.ax2.set_ylabel('voltage (uV)')
        self.ax3.set_ylabel('power (mW)')
        self.ax1.set_xlabel('time (s)')
        self.ax2.set_xlabel('time (s)')
        self.ax3.set_xlabel('time (s)')
        self.fig.show()

    def set_limits(self):
        if self.voltages[0] > self.max_voltage_x:
            self.max_voltage_x = self.voltages[0]
        if self.voltages[0] < self.min_voltage_x:
            self.min_voltage_x = self.voltages[0]
        if 0 < self.min_voltage_x < self.max_voltage_x:
            self.ax1.set_ylim(self.min_voltage_x * 1000000 / 2, self.max_voltage_x * 2 * 1000000)
        if self.min_voltage_x < 0 < self.max_voltage_x:
            self.ax1.set_ylim(self.min_voltage_x * 2 * 1000000, self.max_voltage_x * 2 * 1000000)
        if self.min_voltage_x < self.max_voltage_x < 0:
            self.ax1.set_ylim(self.min_voltage_x * 2 * 1000000, self.max_voltage_x * 1 / 2 * 1000000)
        if self.voltages[1] > self.max_voltage_y:
            self.max_voltage_y = self.voltages[1]
        if self.voltages[1] < self.min_voltage_y:
            self.min_voltage_y = self.voltages[1]
        if self.min_voltage_y > 0 < self.max_voltage_y:
            self.ax2.set_ylim(self.min_voltage_y * 1000000 / 2, self.max_voltage_y * 2 * 1000000)
        if self.min_voltage_y < 0 < self.max_voltage_y:
            self.ax2.set_ylim(self.min_voltage_y * 2 * 1000000, self.max_voltage_y * 2 * 1000000)
        if self.min_voltage_y > self.max_voltage_y > 0:
            self.ax2.set_ylim(self.min_voltage_y * 2 * 1000000, self.max_voltage_y * 1 / 2 * 1000000)
        if self.power > self.max_power:
            self.max_power = self.power
        if self.power < self.min_power:
            self.min_power = self.power
        self.ax3.set_ylim(self.min_power * 1 / 2 * 1000, self.max_power * 2 * 1000)

    def measure(self):
        self.attenuatorwheel.step(self.steps, 0.005)
        time.sleep(0.1)
        time_now = time.time() - self.start_time
        self.power = self.powermeter.read_power()
        raw = self.sr7270_bottom.read_xy()
        self.voltages = [conversions.convert_x_to_iphoto(x, self.gain) for x in raw]
        self.writer.writerow([time_now, self.power, raw[0], raw[1], self.voltages[0], self.voltages[1]])
        self.ax1.scatter(time_now, self.voltages[0] * 1000000, c='b', s=2)
        self.ax2.scatter(time_now, self.voltages[1] * 1000000, c='b', s=2)
        self.ax3.scatter(time_now, self.power * 1000, c='b', s=2)
        self.set_limits()
        plt.tight_layout()
        self.fig.canvas.draw()

    def main(self):
        self.makefile()
        with open(self.file, 'w', newline='') as inputfile:
            try:
                self.start_time = time.time()
                self.writer = csv.writer(inputfile)
                self.write_header()
                self.setup_plots()
                while time.time() - self.start_time < self.maxtime:
                    self.measure()
                plt.savefig(self.imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                plt.savefig(self.imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data

