import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
import csv
from optics.misc_utility import conversions
import os
from os import path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP

class HeatingPolarization:
    def __init__(self, master, filepath, notes, device, scan, gain, bias, osc, npc3sg_input, sr7270_dual_harmonic,
                 sr7270_single_reference, powermeter, waveplate):

        self._fig = Figure()
        self._ax1 = self._fig.add_subplot(211, polar=True)
        self._ax2 = self._fig.add_subplot(212, polar=True)
        self._max_iphoto_x = 0
        self._min_iphoto_x = 0
        self._max_iphoto_y = 0
        self._min_iphoto_y = 0
        self._iphoto = None
        self._fig.tight_layout()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)  # A tk.DrawingArea.
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._abort = False


    def measure(self):
        for i in range(self._waveplate_angle, self._max_waveplate_angle):
            if self._abort:
                break
            self._master.update()
            if i > 360:
                i = i - 360
            self._waveplate.move(i)
            tk_sleep(self._master, 1500)
            self._master.update()
            polarization = float(str(self._waveplate.read_polarization()))
            # converts waveplate angle to polarizaiton angle
            raw = self._sr7270_single_reference.read_xy()
            self._iphoto = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
            if abs(self._iphoto[0]) > self._max_iphoto_x:
                self._max_iphoto_x = abs(self._iphoto[0])
            if abs(self._iphoto[1]) > self._max_iphoto_y:
                self._max_iphoto_y = abs(self._iphoto[1])
            time_now = time.time() - self._start_time
            self._writer.writerow([time_now, polarization, raw[0], raw[1], self._iphoto[0], self._iphoto[1]])
            self._ax1.plot(conversions.degrees_to_radians(polarization), abs(self._iphoto[0]) * 1000, linestyle='',
                           color='blue', marker='o', markersize=2)
            self._ax1.set_rmax(self._max_iphoto_x * 1.1 * 1000)
            self._ax2.plot(conversions.degrees_to_radians(polarization), abs(self._iphoto[1]) * 1000, linestyle='',
                           color='blue', marker='o', markersize=2)
            self._ax2.set_rmax(self._max_iphoto_y * 1.1 * 1000)
            self._fig.tight_layout()
            self._canvas.draw()
            self._master.update()

