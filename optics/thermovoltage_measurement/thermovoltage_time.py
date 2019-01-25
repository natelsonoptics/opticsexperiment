import matplotlib
matplotlib.use('TkAgg')
from optics.misc_utility.tkinter_utilities import tk_sleep
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
from optics.misc_utility import conversions
from optics.measurements.base_time import TimeMeasurement


class ThermovoltageTime(TimeMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, rate, maxtime,
                 npc3sg_input, sr7270_single_reference, powermeter, waveplate):
        super().__init__(master, filepath, notes, device, scan, gain, rate, maxtime, npc3sg_input,
                         sr7270_single_reference, powermeter, waveplate)
        self._max_voltage_x = 0
        self._min_voltage_x = 0
        self._max_voltage_y = 0
        self._min_voltage_y = 0
        self._voltages = [0, 0]

    def do_measurement(self):
        raw = self._sr7270_single_reference.read_xy()
        self._voltages = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        tk_sleep(self._master, self._sleep)
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, raw[0], raw[1], self._voltages[0], self._voltages[1]])
        self._ax1.plot(time_now, self._voltages[0] * 1000000, linestyle='', color='blue', marker='o', markersize=2)
        self._ax2.plot(time_now, self._voltages[1] * 1000000, linestyle='', color='blue', marker='o', markersize=2)
        self.set_limits()
        self._fig.tight_layout()
        self._fig.canvas.draw()

    def setup_plots(self):
        self._ax1.title.set_text('X_1')
        self._ax2.title.set_text('Y_1')
        self._ax1.set_ylabel('voltage (uV)')
        self._ax2.set_ylabel('voltage (uV)')
        self._ax1.set_xlabel('time (s)')
        self._ax2.set_xlabel('time (s)')
        self._canvas.draw()

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

