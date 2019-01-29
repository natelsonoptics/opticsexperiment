import matplotlib
matplotlib.use('TkAgg')
from optics.misc_utility.tkinter_utilities import tk_sleep
from optics.misc_utility import conversions
import time  # DO NOT USE TIME.SLEEP IN TKINTER MAINLOOP
from optics.measurements.base_polarization import PolarizationMeasurement
from optics.misc_utility.conversions import convert_x1_to_didv, convert_adc_to_idc
import numpy as np
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import csv
from optics.raman.single_spectrum import BaseRamanMeasurement


class RamanLockinOutgoingPolarization(PolarizationMeasurement):
    def __init__(self, master, filepath, notes, device, scan, gain, bias, osc, npc3sg_input, sr7270_dual_harmonic,
                 sr7270_single_reference, powermeter, waveplate, steps, polarizer, number_measurements, wait_time_ms,
                 ccd, integration_time, raman_gain, acquisitions, units, grating, center_wavelength, raman_start,
                 raman_stop, darkcurrent=False, darkcorrected=False):
        super().__init__(master, filepath, notes, device, scan, gain, npc3sg_input,
                         sr7270_single_reference, powermeter, waveplate, steps,
                         sr7270_dual_harmonic=sr7270_dual_harmonic)
        self._raman_measurement = BaseRamanMeasurement(master, ccd, grating, raman_gain, center_wavelength, units,
                                                 integration_time, acquisitions,
                                                 True, darkcurrent, darkcorrected, device, filepath,
                                                 notes, scan, powermeter=powermeter, single_plot=False)
        self._bias = bias
        self._osc = osc
        #self._ax5 = None
        self._wait_time_ms = wait_time_ms
        self._raman_writer = None
        self._center_wavelength = center_wavelength
        self._polarizer = polarizer
        self._polarizer_angle = self._polarizer.read_polarization()
        self._number_measurements = number_measurements
        self._raman_start = raman_start
        self._raman_stop = raman_stop
        self._raman_data = []
        self._line = None

    def start(self):
        self._sr7270_dual_harmonic.change_applied_voltage(self._bias)
        tk_sleep(self._master, 300)
        self._sr7270_dual_harmonic.change_oscillator_amplitude(self._osc)
        tk_sleep(self._master, 300)

    def load(self):
        self._ax1 = self._fig.add_subplot(321, polar=True)
        self._ax2 = self._fig.add_subplot(322, polar=True)
        self._ax3 = self._fig.add_subplot(323, polar=True)
        self._ax4 = self._fig.add_subplot(324, polar=True)
        self._ax5 = self._fig.add_subplot(313)

    def stop(self):
        #self._sr7270_dual_harmonic.change_applied_voltage(0)
        pass

    def setup_plots(self):
        self._fig.suptitle('Applied bias: {}'.format(self._bias))
        self._ax1.title.set_text('|X1|')
        self._ax2.title.set_text('|Y1|')
        self._ax3.title.set_text('|Idc|')
        self._ax4.title.set_text('Raman (counts)')
        self._ax5.title.set_text('Raman')
        self._fig.tight_layout()

    def end_header(self, writer):
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['time', 'outgoing polarization', 'x1_raw', 'y1_raw', 'adc', 'didvx', 'didvy',
                               'idc'])

    def do_measurement(self, outgoing_polarization):
        xy1 = []
        adc = []
        #if self._line:
        #    self._line.remove()
        for k in range(self._number_measurements):
            xy1.append(self._sr7270_dual_harmonic.read_xy1())
            adc.append(self._sr7270_dual_harmonic.read_adc(3))
            tk_sleep(self._master, self._wait_time_ms)
        idc = convert_adc_to_idc(np.average([k[0] for k in adc]), self._gain)
        didvx = convert_x1_to_didv(np.average([k[0] for k in xy1]), self._gain, self._osc)
        didvy = convert_x1_to_didv(np.average([k[1] for k in xy1]), self._gain, self._osc)
        _, self._raman_data = self._raman_measurement.take_spectrum()
        time_now = time.time() - self._start_time
        self._writer.writerow([time_now, outgoing_polarization, np.average([k[0] for k in xy1]),
                              np.average([k[1] for k in xy1]), np.average([k[0] for k in adc]), didvx, didvy, idc])
        self._raman_writer.writerow([time_now, outgoing_polarization, 'counts', *[i for i in self._raman_data]])
        self._ax1.plot(conversions.degrees_to_radians(outgoing_polarization), np.average([k[0] for k in xy1]), linestyle='',
                       color='blue', marker='o', markersize=2)
        self._ax2.plot(conversions.degrees_to_radians(outgoing_polarization), np.average([k[1] for k in xy1]), linestyle='',
                       color='blue', marker='o', markersize=2)
        self._ax3.plot(conversions.degrees_to_radians(outgoing_polarization), idc, linestyle='',
                       color='blue', marker='o', markersize=2)
        self._ax4.plot(conversions.degrees_to_radians(outgoing_polarization), self._raman_measurement.integrate_spectrum(self._raman_data, self._raman_start, self._raman_stop), linestyle='',
                       color='blue', marker='o', markersize=2)
        self._line, = self._ax5.plot(self._raman_measurement._xvalues, self._raman_data)

    def measure(self):
        for i in np.arange(self._polarizer_angle, self._polarizer_angle + 360, self._steps * 2):
            if self._abort:
                break
            self._master.update()
            if i > 360:
                i = i - 360
            self._polarizer.move(i)
            tk_sleep(self._master, 5000)
            self._master.update()
            self.do_measurement(i)
            self._fig.tight_layout()
            self._canvas.draw()
            self._master.update()

    def write_raman_header(self):
        self._raman_writer.writerow(['laser wavelength:', laser_wavelength])
        self._raman_writer.writerow(['polarization:', self._polarization])
        self._raman_writer.writerow(['power (W):', self._power])
        self._raman_writer.writerow(['bias:', self._bias])
        self._raman_writer.writerow(['osc:', self._osc])
        gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
        self._raman_writer.writerow(['raman gain:', gain_options[self._raman_measurement._raman_gain]])
        self._raman_writer.writerow(['center wavelength:', self._center_wavelength])
        self._raman_writer.writerow(['acquisitions:', self._raman_measurement._acquisitions])
        self._raman_writer.writerow(['integration time:', self._raman_measurement._integration_time])
        self._raman_writer.writerow(['shutter open:', 'True'])
        self._raman_writer.writerow(['dark current corrected:', self._raman_measurement._dark_current])
        self._raman_writer.writerow(['dark corrected:', self._raman_measurement._dark_corrected])
        self._raman_writer.writerow(['grating:', self._raman_measurement._grating])
        self._raman_writer.writerow(['notes:', self._notes])
        self._raman_writer.writerow(['x value units:', self._raman_measurement._units])
        self._raman_writer.writerow(['end:', 'end of header'])
        self._raman_writer.writerow(['time', 'outgoing polarization', 'x values', *self._raman_measurement._xvalues])

    def main(self):
        self.pack_buttons(self._master)
        filename, imagefile, self._scan = self.make_file('polarization scan with {} bias'.format(self._bias),
                                                         self._scan, record_polarization=False)
        raman_filename = '{} raman.csv'.format(filename.split('.csv')[0])
        with open(filename, 'w', newline='') as inputfile, open(raman_filename, 'w', newline='') as raman_inputfile:
            self.start()
            self._start_time = time.time()
            self._writer = csv.writer(inputfile)
            self.write_header(self._writer, record_polarization=False)
            self._raman_writer = csv.writer(raman_inputfile)
            self.write_raman_header()
            self.setup_plots()
            self._canvas.draw()
            self.measure()
            self._fig.savefig(imagefile, format='png', bbox_inches='tight')
            self.stop()