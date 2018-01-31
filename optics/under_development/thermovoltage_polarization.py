import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions
import os
from os import path


class ThermovoltagePolarization:
    def __init__(self, filepath, notes, device, scan, gain, npc3sg_input, sr7270_bottom, powermeter,
                 polarizer):
        self._writer = None
        self._npc3sg_input = npc3sg_input
        self._gain = gain
        self._powermeter = powermeter
        self._notes = notes
        self._filepath = filepath
        self._scan = scan
        self._device = device
        self._polarizer = polarizer
        self._sr7270_bottom = sr7270_bottom
        self._imagefile = None
        self._filename = None
        self._start_time = None
        self._fig = plt.figure()
        self._ax1 = self._fig.add_subplot(211, projection='polar')
        self._ax2 = self._fig.add_subplot(212, projection='polar')
        self._max_voltage_x = 0
        self._min_voltage_x = 0
        self._max_voltage_y = 0
        self._min_voltage_y = 0
        self._voltages = None
        self._waveplate_angle = int(round(float(str(polarizer.read_position())))) % 360
        self._max_waveplate_angle = self._waveplate_angle + 180
        self._start_time = None

    def write_header(self):
        position = self._npc3sg_input.read()
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['x laser position:', position[0]])
        self._writer.writerow(['y laser position:', position[1]])
        self._writer.writerow(['power (W):', self._powermeter.read_power()])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['time', 'polarization', 'x_raw', 'y_raw', 'x_v', 'y_v'])

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'polarization_scan', index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'polarization_scan', index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'polarization_scan', index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'polarization_scan', index, '.png'))

    def setup_plots(self):
        self._ax1.title.set_text('|X_1| (uV)')
        self._ax2.title.set_text('|Y_1| (uV)')
        self._fig.show()

    def measure(self):
        for i in range(self._waveplate_angle, self._max_waveplate_angle):
            if i > 360:
                i = i - 360
            self._polarizer.move(i)
            time.sleep(1.5)
            polarization = float(str(self._polarizer.read_position())) * 2
            # converts waveplate angle to polarizaiton angle
            raw = self._sr7270_bottom.read_xy()
            self._voltages = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
            time_now = time.time() - self._start_time
            self._writer.writerow([time_now, polarization, raw[0], raw[1], self._voltages[0], self._voltages[1]])
            self._ax1.scatter(conversions.degrees_to_radians(polarization), abs(self._voltages[0]) * 1000000, c='c', s=2)
            self._ax2.scatter(conversions.degrees_to_radians(polarization), abs(self._voltages[1]) * 1000000, c='c', s=2)
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
                while time.time() - self._start_time < self.maxtime:
                    self.measure()
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data