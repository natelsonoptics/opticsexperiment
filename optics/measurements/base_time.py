from optics.measurements.base_measurement import LockinBaseMeasurement
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

    def do_measurement(self):
        pass

    def measure(self):
        self._master.update()
        self.do_measurement()
        self._master.update()
        if not self._abort and time.time() - self._start_time < self._maxtime:
            self.measure()

    def main(self):
        self.pack_buttons(self._master)
        filename, imagefile, self._scan = self.make_file('time scan', self._scan)
        with open(filename, 'w', newline='') as inputfile:
            self.start()
            self._start_time = time.time()
            self._writer = csv.writer(inputfile)
            self.write_header(self._writer)
            self.setup_plots()
            self._canvas.draw()
            self.measure()
            self._fig.savefig(imagefile, format='png', bbox_inches='tight')
            self.stop()

