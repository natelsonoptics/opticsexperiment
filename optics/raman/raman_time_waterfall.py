from optics.raman.single_spectrum import BaseRamanMeasurement
import csv
from optics.hardware_control.hardware_addresses_and_constants import laser_wavelength
import time
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
import numpy as np
import matplotlib.pyplot as plt


class RamanTimeWaterfall(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, device, filepath, notes, index, sleep_time, number_scans,
                 waveplate=None, powermeter=None):
        super().__init__(master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter)
        self._sleep_time = sleep_time
        self._number_scans = number_scans
        self._wf = np.zeros((self._number_scans, len(self._xvalues)))
        self._im = self._single_ax1.imshow(self._wf, interpolation='nearest', origin='lower', aspect='auto',
                                            extent=[self._xvalues[0], self._xvalues[-1], 0, self._number_scans])
        self._single_ax1.set_xlabel(self._units)
        self._single_ax1.set_ylabel('scan')
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
            for scan in range(self._number_scans):
                now = time.time() - start_time
                self.take_spectrum()
                writer.writerow(['time scan {}'.format(now), *[i for i in self._data]])
                self._wf[scan] = self._data
                self.update_plot(self._im, self._wf)
                self._master.update()
                tk_sleep(self._master, self._sleep_time * 1000)
                if self._abort:
                    break

    def onpick(self, event):
        ydata = int(np.ceil(event.ydata - 1))
        with open(self._filename) as inputfile:
            reader = csv.reader(inputfile, delimiter=',')
            for row in reader:
                if 'end:' in row:
                    break
            for i, row in enumerate(reader):
                if i == ydata + 1:
                    title = row[0]
                    data = [float(i) for i in row[1::]]
                    fig = plt.figure()
                    ax = fig.add_subplot(111)
                    ax.set_title('{}, {} polarization, {} seconds'.format(self._device, self._polarization, title))
                    ax.set_xlabel(self._units)
                    ax.set_ylabel('counts')
                    ax.plot(self._xvalues, data)
                    fig.show()

    def main(self):
        button = tk.Button(master=self._master, text="Abort", command=self.abort)
        button.pack(side=tk.BOTTOM)
        self._single_ax1.set_title('{} time waterfall, {} polarization'.format(self._device, self._polarization))
        self._single_fig.tight_layout()
        self.make_file(measurement_title='time waterfall measurement')
        self.write_header()
        self.measure()
        self._single_fig.savefig(self._imagefile, format='png', bbox_inches='tight')
        cid = self._single_fig.canvas.mpl_connect('button_press_event',
                                                  self.onpick)  # click on pixel to move laser position there