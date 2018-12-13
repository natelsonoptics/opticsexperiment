from optics.raman.single_spectrum import BaseRamanMeasurement
import csv
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
import numpy as np
import matplotlib.pyplot as plt


class RamanVoltageWaterfall(BaseRamanMeasurement):
    def __init__(self, master, ccd, sr7270_dual_harmonic, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, number_scans, start_voltage,
                 stop_voltage, waveplate=None, powermeter=None):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter)
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sleep_time = sleep_time
        self._voltages = np.linspace(start_voltage, stop_voltage, number_scans)
        self._wf = np.zeros((number_scans, len(self._xvalues)))
        self._im = self._single_ax1.imshow(self._wf, interpolation='nearest', origin='lower', aspect='auto',
                                            extent=[self._xvalues[0], self._xvalues[-1], self._voltages[0],
                                                    self._voltages[-1]])
        self._single_ax1.set_xlabel(self._units)
        self._single_ax1.set_ylabel('applied voltage (mV)')
        self._clb1 = self._single_fig.colorbar(self._im, ax=self._single_ax1)
        self._single_fig.tight_layout()
        self._single_canvas.draw()
        self._single_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def write_header(self):
        with open(self._filename, 'w', newline='') as inputfile:
            writer = csv.writer(inputfile)
            writer.writerow(['laser wavelength:', laser_wavelength])
            writer.writerow(['polarization:', self._polarization])
            writer.writerow(['power (W):', self._power])
            gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
            writer.writerow(['raman gain:', gain_options[self._raman_gain]])
            writer.writerow(['center wavelength:', self._center_wavelength])
            writer.writerow(['acquisitions:', self._acquisitions])
            writer.writerow(['integration time:', self._integration_time])
            writer.writerow(['shutter open:', self._shutter])
            writer.writerow(['dark current corrected:', self._dark_current])
            writer.writerow(['dark corrected:', self._dark_corrected])
            writer.writerow(['grating:', self._grating])
            writer.writerow(['time between scans:', self._sleep_time])
            writer.writerow(['notes:', self._notes])
            writer.writerow(['x value units:', self._units])
            writer.writerow(['end:', 'end of header'])
            writer.writerow(['x values', *self._xvalues])

    def update_plot(self, im, data):
        im.set_data(data)
        values = np.unique(data)
        im.set_clim(vmin=sorted(values)[1])
        im.set_clim(vmax=np.amax(data))
        self._single_canvas.draw()

    def measure(self):
        start_time = time.time()
        with open(self._filename, 'a', newline='') as inputfile:
            writer = csv.writer(inputfile)
            for i, voltage in enumerate(self._voltages):
                self._sr7270_dual_harmonic.change_applied_voltage(voltage)
                self.take_spectrum()
                writer.writerow(['applied voltage {}'.format(voltage), *[i for i in self._data]])
                self._wf[i] = self._data
                self.update_plot(self._im, self._wf)
                self._master.update()
                tk_sleep(self._master, self._sleep_time * 1000)
                if self._abort:
                    break
            self._sr7270_dual_harmonic.change_applied_voltage(0)

    def onpick(self, event):
        ydata = int(np.ceil(event.ydata))
        idx = (np.abs(self._voltages - ydata)).argmin()
        ydata = self._voltages[idx]
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'end:' in row:
                    break
            for row in reader:
                if 'applied voltage {}'.format(ydata) in row:
                    title = row[0]
                    data = [float(i) for i in row[1::]]
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    ax.set_title('{}, {} polarization, {} mV'.format(self._device, self._polarization, title))
                    ax.set_xlabel(self._units)
                    ax.set_ylabel('counts')
                    ax.plot(self._xvalues, data)
                    fig.show()

    def main(self):
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        self._single_ax1.set_title('{} applied voltage waterfall, {} polarization'.format(self._device, self._polarization))
        self._single_fig.tight_layout()
        self.make_file(measurement_title='applied voltage waterfall measurement')
        self.write_header()
        self.measure()
        self._single_fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        cid = self._single_fig.canvas.mpl_connect('button_press_event',
                                                  self.onpick)  # click on pixel to move laser position there