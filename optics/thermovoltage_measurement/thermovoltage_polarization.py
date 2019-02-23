import matplotlib
matplotlib.use('TkAgg')
from optics.misc_utility import conversions
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
from optics.measurements.base_polarization import PolarizationMeasurement


class ThermovoltagePolarization(PolarizationMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, npc3sg_input, sr7270_single_reference, powermeter,
                 waveplate, steps):
        super().__init__(master, filepath, notes, device, scan, steps, gain=gain,
                         npc3sg_input=npc3sg_input, sr7270_single_reference=sr7270_single_reference,
                         powermeter=powermeter, waveplate=waveplate)

    def end_header(self, writer):
        writer.writerow(['end:', 'end of header'])
        writer.writerow(['time', 'polarization', 'x_raw', 'y_raw', 'x_v', 'y_v'])

    def setup_plots(self):
        self._ax1.title.set_text('|X_1| (uV)')
        self._ax2.title.set_text('|Y_1| (uV)')

    def do_measurement(self):
        raw = self._sr7270_single_reference.read_xy()
        voltages = [conversions.convert_x_to_iphoto(x, self._gain) for x in raw]
        if abs(voltages[0]) > self._vmax_x:
            self._vmax_x = abs(voltages[0])
        if abs(voltages[1]) > self._vmax_y:
            self._vmax_y = abs(voltages[1])
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, self._polarization, raw[0], raw[1], voltages[0], voltages[1]])
        self._ax1.plot(conversions.degrees_to_radians(self._polarization), abs(voltages[0]) * 1000000,
                       linestyle='', color='blue', marker='o', markersize=2)
        self._ax1.set_rmax(self._vmax_x * 1000000 * 1.1)
        self._ax2.plot(conversions.degrees_to_radians(self._polarization), abs(voltages[1]) * 1000000,
                       linestyle='', color='blue', marker='o', markersize=2)
        self._ax2.set_rmax(self._vmax_y * 1000000 * 1.1)