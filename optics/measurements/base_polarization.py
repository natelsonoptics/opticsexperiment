from optics.measurements.base_measurement import LockinBaseMeasurement
import numpy as np
from optics.misc_utility.tkinter_utilities import tk_sleep


class PolarizationMeasurement(LockinBaseMeasurement):
    def __init__(self, master, filepath, notes, device, scan, steps, gain=None, npc3sg_input=None,
                 sr7270_single_reference=None, powermeter=None, waveplate=None, sr7270_dual_harmonic=None, ccd=None,
                 mono=None, daq_input=None):
        super().__init__(master=master, filepath=filepath, device=device, npc3sg_input=npc3sg_input,
                         sr7270_dual_harmonic=sr7270_dual_harmonic, sr7270_single_reference=sr7270_single_reference,
                         powermeter=powermeter, waveplate=waveplate, notes=notes, gain=gain, scan=scan, ccd=ccd,
                         mono=mono, daq_input=daq_input)
        self._waveplate_angle = int(round(float(str(self._waveplate.read_position())))) % 360
        self._steps = steps / 2  # 1/2 wave plate
        self._gain = gain
        self._vmax_x = 0
        self._vmax_y = 0
        self._polarization = float(str(self._waveplate.read_polarization()))

    def load(self):
        self._ax1 = self._fig.add_subplot(211, polar=True)
        self._ax2 = self._fig.add_subplot(212, polar=True)

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
            self._polarization = float(str(self._waveplate.read_polarization()))
            self.do_measurement()
            self._fig.tight_layout()
            self._canvas.draw()
            self._master.update()

    def main(self):
        self.main2('polarization scan', record_polarization=False)
