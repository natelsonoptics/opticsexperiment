import matplotlib
matplotlib.use('TkAgg')
from optics.misc_utility import conversions
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
from optics.measurements.base_polarization import PolarizationMeasurement


class ThermovoltagePolarizationDC(PolarizationMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, npc3sg_input, powermeter, waveplate, daq_input,
                 steps):
        super().__init__(master, filepath, notes, device, scan, steps, gain=gain,
                         npc3sg_input=npc3sg_input, daq_input=daq_input, powermeter=powermeter, waveplate=waveplate)
        self._voltage = []

    def end_header(self, writer):
        writer.writerow(['end:', 'end of header'])
        writer.writerow(['time', 'polarization', 'v_raw', 'v_dc'])

    def load(self):
        self._ax1 = self._fig.add_subplot(111, polar=True)

    def setup_plots(self):
        self._ax1.title.set_text('DC thermovoltage (uV)')
        self._canvas.draw()

    def do_measurement(self):
        data = self._daq_input.read()
        raw = data[0] - data[1]
        self._voltage = raw / self._gain
        if abs(self._voltage) > self._vmax_x:
            self._vmax_x = abs(self._voltage)
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, self._polarization, raw, self._voltage])
        self._ax1.plot(conversions.degrees_to_radians(self._polarization), abs(self._voltage) * 1000000,
                           linestyle='', color='blue', marker='o', markersize=2)
        self._ax1.set_rmax(self._vmax_x * 1000000 * 1.1)

    def main(self):
        self.main2('dc polarization scan', record_polarization=False)

