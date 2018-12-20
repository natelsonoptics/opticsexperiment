from optics.measurements.base_measurement import LockinBaseMeasurement
import numpy as np
import time
import csv
from optics.misc_utility.tkinter_utilities import tk_sleep


class TimeMeasurement(LockinBaseMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, rate, maxtime, npc3sg_input,
                 sr7270_single_reference, powermeter, waveplate, sr7270_dual_harmonic=None):
        super().__init__(master=master, filepath=filepath, device=device, npc3sg_input=npc3sg_input,
                         sr7270_dual_harmonic=sr7270_dual_harmonic, sr7270_single_reference=sr7270_single_reference,
                         powermeter=powermeter, waveplate=waveplate, notes=notes, gain=gain)
        self._maxtime = maxtime
        self._start_time = None
        self._scan = scan
        self._sleep = 1 / rate * 1000

    def start(self):
        pass

    def stop(self):
        pass

    def setup_plots(self):
        pass

    def measure(self):
        self._master.update()
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
        self._master.update()
        if not self._abort and time.time() - self._start_time < self._maxtime:
            self.measure()

    def do_measurement(self):


    def main(self):
        self.pack_buttons(self._master)
        filename, imagefile, self._scan = self.make_file('polarization scan', self._scan)
        with open(filename, 'w', newline='') as inputfile:
            self.start()
            self._start_time = time.time()
            self._writer = csv.writer(inputfile)
            self.write_header(self._writer, record_power=False)
            self.setup_plots()
            self._canvas.draw()
            self.measure()
            self._fig.savefig(imagefile, format='png', bbox_inches='tight')
            self.stop()

class HeatingTime(TimeMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, rate, maxtime, bias, osc, npc3sg_input,
                 sr7270_dual_harmonic, sr7270_single_reference, powermeter, waveplate):
        super().__init__(master, filepath, notes, device, scan, gain, rate, maxtime, npc3sg_input,
                         sr7270_single_reference, powermeter, waveplate, sr7270_dual_harmonic=sr7270_dual_harmonic)
        self._bias = bias
        self._osc = osc

    def start(self):
        self._sr7270_dual_harmonic.change_applied_voltage(self._bias)
        tk_sleep(self._master, 300)
        self._sr7270_dual_harmonic.change_oscillator_amplitude(self._osc)
        tk_sleep(self._master, 300)

    def stop(self):
        self._sr7270_dual_harmonic.change_applied_voltage(0)