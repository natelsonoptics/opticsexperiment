from optics.measurements.base_measurement import LockinBaseMeasurement
import numpy as np
import time
import csv
from optics.misc_utility.tkinter_utilities import tk_sleep


class PolarizationMeasurement(LockinBaseMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, npc3sg_input,
                 sr7270_single_reference, powermeter, waveplate, steps, sr7270_dual_harmonic=None):
        super().__init__(master=master, filepath=filepath, device=device, npc3sg_input=npc3sg_input,
                         sr7270_dual_harmonic=sr7270_dual_harmonic, sr7270_single_reference=sr7270_single_reference,
                         powermeter=powermeter, waveplate=waveplate, notes=notes, gain=gain)
        self._scan = scan
        self._writer = None
        self._start_time = None
        if self._waveplate:
            self._waveplate_angle = int(round(float(str(self._waveplate.read_position())))) % 360
        self._steps = steps / 2  # 1/2 wave plate
        self._gain = gain
        self._vmax_x = 0
        self._vmax_y = 0

    def load(self):
        self._ax1 = self._fig.add_subplot(211, polar=True)
        self._ax2 = self._fig.add_subplot(212, polar=True)

    def start(self):
        pass

    def stop(self):
        pass

    def do_measurement(self, polarization):
            pass

    def measure(self):
        for i in np.arange(self._waveplate_angle, self._waveplate_angle + 180, self._steps):
            if self._abort:
                break
            self._master.update()
            if i > 360:
                i = i - 360
            self._waveplate.move(i)
            tk_sleep(self._master, 1500)
            self._master.update()
            polarization = float(str(self._waveplate.read_polarization()))
            self.do_measurement(polarization)
            self._fig.tight_layout()
            self._canvas.draw()
            self._master.update()

    def setup_plots(self):
        pass

    def main(self):
        self.pack_buttons(self._master)
        filename, imagefile, self._scan = self.make_file('polarization scan', self._scan, record_polarization=False)
        with open(filename, 'w', newline='') as inputfile:
            self.start()
            self._start_time = time.time()
            self._writer = csv.writer(inputfile)
            self.write_header(self._writer, record_polarization=False)
            self.setup_plots()
            self._canvas.draw()
            self.measure()
            self._fig.savefig(imagefile, format='png', bbox_inches='tight')
            self.stop()
