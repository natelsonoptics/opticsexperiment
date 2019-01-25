import matplotlib
matplotlib.use('TkAgg')
from optics.misc_utility.tkinter_utilities import tk_sleep
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
from optics.misc_utility import conversions
from optics.measurements.base_time import TimeMeasurement


class HeatingTime(TimeMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, rate, maxtime, bias, osc, npc3sg_input,
                 sr7270_dual_harmonic, sr7270_single_reference, powermeter, waveplate):
        super().__init__(master, filepath, notes, device, scan, gain, rate, maxtime, npc3sg_input,
                         sr7270_single_reference, powermeter, waveplate, sr7270_dual_harmonic=sr7270_dual_harmonic)
        self._bias = bias
        self._osc = osc
        self._max_iphoto_x = 0
        self._min_iphoto_x = 0
        self._min_iphoto_y = 0
        self._max_iphoto_y = 0
        self._iphoto = [0, 0]

    def start(self):
        self._sr7270_dual_harmonic.change_applied_voltage(self._bias)
        tk_sleep(self._master, 300)
        self._sr7270_dual_harmonic.change_oscillator_amplitude(self._osc)
        tk_sleep(self._master, 300)

    def stop(self):
        self._sr7270_dual_harmonic.change_applied_voltage(0)

    def do_measurement(self):
        raw = self._sr7270_single_reference.read_xy()
        self._iphoto = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        tk_sleep(self._master, self._sleep)
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, raw[0], raw[1], self._iphoto[0], self._iphoto[1]])
        self._ax1.plot(time_now, self._iphoto[0] * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self._ax2.plot(time_now, self._iphoto[1] * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self.set_limits()
        self._fig.tight_layout()
        self._fig.canvas.draw()

    def setup_plots(self):
        self._ax1.title.set_text('X_1')
        self._ax2.title.set_text('Y_1')
        self._ax1.set_ylabel('current (mA)')
        self._ax2.set_ylabel('current (mA)')
        self._ax1.set_xlabel('time (s)')
        self._ax2.set_xlabel('time (s)')
        self._canvas.draw()

    def set_limits(self):
        if self._iphoto[0] > self._max_iphoto_x:
            self._max_iphoto_x = self._iphoto[0]
        if self._iphoto[0] < self._min_iphoto_x:
            self._min_iphoto_x = self._iphoto[0]
        if 0 < self._min_iphoto_x < self._max_iphoto_x:
            self._ax1.set_ylim(self._min_iphoto_x * 1000 / 1.3, self._max_iphoto_x * 1.3 * 1000)
        if self._min_iphoto_x < 0 < self._max_iphoto_x:
            self._ax1.set_ylim(self._min_iphoto_x * 1.3 * 1000, self._max_iphoto_x * 1.3 * 1000)
        if self._min_iphoto_x < self._max_iphoto_x < 0:
            self._ax1.set_ylim(self._min_iphoto_x * 1.3 * 1000, self._max_iphoto_x * 1 / 1.3 * 1000)
        if self._iphoto[1] > self._max_iphoto_y:
            self._max_iphoto_y = self._iphoto[1]
        if self._iphoto[1] < self._min_iphoto_y:
            self._min_iphoto_y = self._iphoto[1]
        if self._min_iphoto_y > 0 < self._max_iphoto_y:
            self._ax2.set_ylim(self._min_iphoto_y * 1000 / 1.3, self._max_iphoto_y * 1.3 * 1000)
        if self._min_iphoto_y < 0 < self._max_iphoto_y:
            self._ax2.set_ylim(self._min_iphoto_y * 1.3 * 1000, self._max_iphoto_y * 1.3 * 1000)
        if self._min_iphoto_y > self._max_iphoto_y > 0:
            self._ax2.set_ylim(self._min_iphoto_y * 1.3 * 1000, self._max_iphoto_y / 1.3 * 1000)

