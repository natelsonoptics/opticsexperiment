from optics.measurements.base_measurement import LockinBaseMeasurement
import time


class IntensityMeasurement(LockinBaseMeasurement):
    def __init__(self, master, filepath, notes, device, scan, maxtime, steps, npc3sg_input=None,
                 sr7270_dual_harmonic=None, sr7270_single_reference=None, powermeter=None, attenuator_wheel=None,
                 waveplate=None, gain=None, ccd=None, mono=None, daq_input=None):
        super().__init__(master=master, filepath=filepath, device=device, npc3sg_input=npc3sg_input,
                         sr7270_dual_harmonic=sr7270_dual_harmonic, sr7270_single_reference=sr7270_single_reference,
                         powermeter=powermeter, waveplate=waveplate, notes=notes, gain=gain, daq_input=daq_input,
                         ccd=ccd, mono=mono, attenuator_wheel=attenuator_wheel)
        self._maxtime = maxtime
        self._scan = scan
        self._steps = steps

    def load(self):
        self._ax1 = self._fig.add_subplot(311)
        self._ax2 = self._fig.add_subplot(312)
        self._ax3 = self._fig.add_subplot(313)

    def measure(self):
        self._master.update()
        self._attenuator_wheel.step(self._steps, 0.005)
        self.do_measurement()
        self._master.update()
        if not self._abort and time.time() - self._start_time < self._maxtime:
            self.measure()

    def main(self):
        self.main2('intensity scan')
