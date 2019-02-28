import matplotlib
matplotlib.use('TkAgg')
from optics.misc_utility import conversions
from optics.measurements.base_time import TimeMeasurement
import time
from optics.misc_utility.tkinter_utilities import tk_sleep


class HeatingTime(TimeMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, rate, maxtime, bias, osc, npc3sg_input,
                 sr7270_dual_harmonic, sr7270_single_reference, powermeter, waveplate):
        super().__init__(master, filepath, notes, device, scan, rate, maxtime, npc3sg_input=npc3sg_input,
                         sr7270_single_reference=sr7270_single_reference, powermeter=powermeter, gain=gain,
                         waveplate=waveplate, sr7270_dual_harmonic=sr7270_dual_harmonic)
        self._bias = bias
        self._osc = osc
        self._iphoto = []

    def start(self):
        self._sr7270_dual_harmonic.change_applied_voltage(self._bias)
        tk_sleep(self._master, 300)
        self._sr7270_dual_harmonic.change_oscillator_amplitude(self._osc)
        tk_sleep(self._master, 300)

    def stop(self):
        self._sr7270_dual_harmonic.change_applied_voltage(0)

    def end_header(self, writer):
        writer.writerow(['end:', 'end of header'])
        writer.writerow(['time', 'x_raw', 'y_raw', 'iphoto_x', 'iphoto_y'])

    def setup_plots(self):
        self._ax1.title.set_text('X_1')
        self._ax2.title.set_text('Y_1')
        self._ax1.set_ylabel('current (mA)')
        self._ax2.set_ylabel('current (mA)')
        self._ax1.set_xlabel('time (s)')
        self._ax2.set_xlabel('time (s)')
        self._canvas.draw()

    def do_measurement(self):
        raw = self._sr7270_single_reference.read_xy()
        self._iphoto = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        tk_sleep(self._master, self._sleep)
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, raw[0], raw[1], self._iphoto[0], self._iphoto[1]])
        self._ax1.plot(time_now, self._iphoto[0] * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self._ax2.plot(time_now, self._iphoto[1] * 1000, linestyle='', color='blue', marker='o', markersize=2)
        self._fig.tight_layout()
        self._fig.canvas.draw()

