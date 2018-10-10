import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
import csv
from optics.misc_utility import conversions
import os
from os import path
from optics.misc_utility.tkinter_utilities import tk_sleep
import tkinter as tk

class ThermovoltagePolarizationDC:
    def __init__(self, master, filepath, notes, device, scan, gain, npc3sg_input, sr7270_bottom, powermeter,
                 polarizer, q):
        self._master = master
        self._writer = None
        self._npc3sg_input = npc3sg_input
        self._q = q
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
        self._fig = Figure()
        self._ax1 = self._fig.add_subplot(111, polar=True)
        self._max_voltage = 0
        self._voltage = None
        self._waveplate_angle = int(round(float(str(polarizer.read_waveplate_position())))) % 360
        self._max_waveplate_angle = self._waveplate_angle + 180
        self._start_time = None
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
        self._writer.writerow(['power (W):', self._powermeter.read_power()])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['time', 'polarization', 'v_raw', 'v_dc'])

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'dc polarization_scan', index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'dc polarization_scan', index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'dc polarization_scan', index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'dc polarization_scan', index, '.png'))

    def setup_plots(self):
        self._ax1.title.set_text('DC thermovoltage (uV)')
        self._canvas.draw()

    def measure(self):
        for i in range(self._waveplate_angle, self._max_waveplate_angle):
            if self._abort:
                break
            self._master.update()
            if i > 360:
                i = i - 360
            self._polarizer.move(i)
            tk_sleep(self._master, 1500)
            self._master.update()
            polarization = float(str(self._polarizer.read_polarization()))
            # converts waveplate angle to polarizaiton angle
            data = self._q.read()
            raw = data[0] - data[1]
            self._voltage = raw / self._gain
            if abs(self._voltage) > self._max_voltage:
                self._max_voltage = abs(self._voltage)
            time_now = time.time() - self._start_time
            self._writer.writerow([time_now, polarization, raw, self._voltage])
            self._ax1.plot(conversions.degrees_to_radians(polarization), abs(self._voltage) * 1000000,
                           linestyle='', color='blue', marker='o', markersize=2)
            self._ax1.set_rmax(self._max_voltage * 1000000 * 1.1)
            self._fig.tight_layout()
            self._fig.canvas.draw()
            self._master.update()

    def main(self):
        self.makefile()
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._start_time = time.time()
                self._writer = csv.writer(inputfile)
                self.write_header()
                self.setup_plots()
                self.measure()
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data