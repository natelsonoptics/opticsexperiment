import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions
import os
from os import path


class ThermovoltagePolarization:
    def __init__(self, filepath, notes, device, scan, gain, maxtime, npc3sg_input, sr7270_bottom, powermeter,
                 polarizercontroller):
        self.writer = None
        self.npc3sg_input = npc3sg_input
        self.gain = gain
        self.powermeter = powermeter
        self.notes = notes
        self.filepath = filepath
        self.scan = scan
        self.device = device
        self.polarizercontroller = polarizercontroller
        self.sr7270_bottom = sr7270_bottom
        self.imagefile = None
        self.maxtime = maxtime
        self.file = None
        self.start_time = None
        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(211, projection='polar')
        self.ax2 = self.fig.add_subplot(212, projection='polar')
        self.max_voltage_x = 0
        self.min_voltage_x = 0
        self.max_voltage_y = 0
        self.min_voltage_y = 0
        self.voltages = None
        self.waveplate_angle = int(round(float(str(polarizercontroller.read_position())))) % 360
        self.max_waveplate_angle = self.waveplate_angle + 180
        self.start_time = None

    def write_header(self):
        position = self.npc3sg_input.read()
        self.writer.writerow(['gain:', self.gain])
        self.writer.writerow(['x laser position:', position[0]])
        self.writer.writerow(['y laser position:', position[1]])
        self.writer.writerow(['power (W):', self.powermeter.read_power()])
        self.writer.writerow(['notes:', self.notes])
        self.writer.writerow(['end:', 'end of header'])
        self.writer.writerow(['time', 'polarization', 'x_raw', 'y_raw', 'x_v', 'y_v'])

    def makefile(self):
        os.makedirs(self.filepath, exist_ok=True)
        index = self.scan
        self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, 'polarization_scan', index, '.csv'))
        self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, 'polarization_scan', index, '.png'))
        while path.exists(self.file):
            index += 1
            self.file = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, 'polarization_scan', index, '.csv'))
            self.imagefile = path.join(self.filepath, '{}_{}_{}{}'.format(self.device, 'polarization_scan', index, '.png'))

    def setup_plots(self):
        self.ax1.title.set_text('|X_1| (uV)')
        self.ax2.title.set_text('|Y_1| (uV)')
        self.fig.show()

    def measure(self):
        for i in range(self.waveplate_angle, self.max_waveplate_angle):
            if i > 360:
                i = i - 360
            self.polarizercontroller.move(i)
            time.sleep(1.5)
            polarization = float(str(self.polarizercontroller.read_position())) * 2
            # converts waveplate angle to polarizaiton angle
            raw = self.sr7270_bottom.read_xy()
            self.voltages = [conversions.convert_x_to_iphoto(x, self.gain) for x in raw]
            time_now = time.time() - self.start_time
            self.writer.writerow([time_now, polarization, raw[0], raw[1], self.voltages[0], self.voltages[1]])
            self.ax1.scatter(conversions.degrees_to_radians(polarization), abs(self.voltages[0]) * 1000000, c='c', s=2)
            self.ax2.scatter(conversions.degrees_to_radians(polarization), abs(self.voltages[1]) * 1000000, c='c', s=2)
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