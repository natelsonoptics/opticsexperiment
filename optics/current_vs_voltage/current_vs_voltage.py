import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure
import numpy as np
import csv
import os
from os import path
import tkinter as tk
from optics.misc_utility.tkinter_utilities import tk_sleep
from optics.misc_utility.conversions import convert_x_to_iphoto, convert_x1_to_didv, convert_x2_to_d2idv2, \
    convert_adc_to_idc, normalize_dgdv_from_x1, normalize_dgdv_from_didv, differentiate_d2idv2


class CurrentVoltageSweep:
    def __init__(self, master, filepath, notes, device, scan, gain, osc, start_voltage, stop_voltage, steps,
                 number_measurements, sr7270_dual_harmonic, sr7270_single_reference):
        self._master = master
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._osc = osc / 1000
        self._number_measurements = number_measurements
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        # set up the plots
        self._fig = Figure()
        self._fig.set_size_inches(14, 9)
        self._ax1 = self._fig.add_subplot(511)
        self._ax2 = self._fig.add_subplot(512)
        self._ax3 = self._fig.add_subplot(513)
        self._ax4 = self._fig.add_subplot(514)
        self._ax5 = self._fig.add_subplot(515)
        self._ax2_twin = self._ax2.twinx()
        self._ax3_twin = self._ax3.twinx()
        self._ax4_twin = self._ax4.twinx()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._master)
        self._voltages = np.linspace(start_voltage / 1000, stop_voltage / 1000, steps)
        self._writer = None
        self._sweep_writer = None
        self._filename = None
        self._imagefile = None
        self._sweep_filename = None
        self._didvx = []
        self._didvx = []
        self._didvy = []
        self._d2idvx2 = []
        self._d2idvy2 = []
        self._iphotox = []
        self._iphotoy = []
        self._idc = []
        self._dgdv_normalized = []
        self._diff_d2idvx2 = []
        self._diff_d2idvy2 = []
        self._abort = False
        self._time_constant = np.amax([self._sr7270_dual_harmonic.read_tc(), self._sr7270_dual_harmonic.read_tc(channel=2),
                                       self._sr7270_single_reference.read_tc()])

    def abort(self):
        self._abort = True

    def write_header(self):
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['osc amplitude (V):', self._sr7270_dual_harmonic.read_oscillator_amplitude()])
        self._writer.writerow(['osc frequency:', self._sr7270_dual_harmonic.read_oscillator_frequency()])
        self._writer.writerow(['time constant:', self._sr7270_single_reference.read_tc()])
        self._writer.writerow(['top time constant:', self._sr7270_dual_harmonic.read_tc()])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['applied voltage (V)', 'raw adc', 'raw X', 'raw Y', 'raw X1', 'raw Y1', 'raw X2',
                               'raw Y2', 'Idc', 'dI/dVx', 'dI/dVy', 'd2I/dVx2', 'd2I/dVy2',
                               'dG/dV*V/G', 'PhotoX', 'PhotoY', 'resistance (V/I)', 'r (dV/dI)'])
        self._sweep_writer.writerow(['gain:', self._gain])
        self._sweep_writer.writerow(['osc amplitude (V):', self._sr7270_dual_harmonic.read_oscillator_amplitude()])
        self._sweep_writer.writerow(['osc frequency:', self._sr7270_dual_harmonic.read_oscillator_frequency()])
        self._sweep_writer.writerow(['time constant:', self._sr7270_single_reference.read_tc()])
        self._sweep_writer.writerow(['top time constant:', self._sr7270_dual_harmonic.read_tc()])
        self._sweep_writer.writerow(['notes:', self._notes])
        self._sweep_writer.writerow(['end:', 'end of header'])
        self._sweep_writer.writerow(['applied voltage (V)', 'raw adc', 'raw X', 'raw Y', 'raw X1', 'raw Y1', 'raw X2',
                                     'raw Y2', 'Idc', 'dI/dVx', 'dI/dVy', 'd2I/dVx2', 'd2I/dVy2',
                                     'dG/dV*V/G', 'PhotoX', 'PhotoY', 'resistance (V/I)', 'r (dV/dI)', 'diff d2I/dVx2',
                                     'diff d2I/dVy2'])

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'raw IV sweep', index, '.csv'))
        self._sweep_filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'averaged IV sweep',
                                                                             index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'IV sweep', index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'raw IV sweep', index, '.csv'))
            self._sweep_filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'averaged IV sweep',
                                                                                 index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'IV sweep', index, '.png'))

    def setup_plots(self):
        for i in [(self._ax1, 'Idc', 'blue'), (self._ax2, 'dI/dVx', 'blue'), (self._ax3, 'd2I/dVx2', 'blue'),
                  (self._ax4, 'dG/dV*V/G', 'blue'), (self._ax5, 'numerical d2I/dVx2', 'blue'),
                  (self._ax2_twin, 'dIdVy', 'red'), (self._ax3_twin, 'd2I/dVy2', 'red'),
                  (self._ax4_twin, 'PhotoX', 'red')]:
            i[0].set_xlabel('DC Voltage (V)')
            i[0].set_xlim(self._voltages[0], self._voltages[-1])
            i[0].set_ylabel(i[1], color=i[2])
            i[0].tick_params(axis='y', labelcolor=i[2])
            i[0].plot([i for i in self._voltages], [0 for i in self._voltages], c=i[2], linestyle='--', linewidth=0.5)
            i[0].ticklabel_format(axis='1', style='sci', scilimits=(-3, 3))
            [i[0].axvline(x=q/1000, color='k', linestyle='--', linewidth=0.5) for q in
             range(int(self._voltages[0] * 1000), int(self._voltages[-1] * 1000)) if q % 100 == 0]
        self._fig.tight_layout()
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def set_limits(self):
        self._ax1.set_ylim(np.amin(self._idc), np.amax(self._idc))
        self._ax2.set_ylim(np.amin(self._didvx), np.amax(self._didvx))
        self._ax2_twin.set_ylim(np.amin(self._didvy), np.amax(self._didvy))
        self._ax3.set_ylim(np.amin(self._d2idvx2), np.amax(self._d2idvx2))
        self._ax3_twin.set_ylim(np.amin(self._d2idvy2), np.amax(self._d2idvy2))
        self._ax4.set_ylim(np.amin(self._dgdv_normalized), np.amax(self._dgdv_normalized))
        self._ax4_twin.set_ylim(np.amin(self._iphotox), np.amax(self._iphotox))

    def measure(self):
        for i, j in enumerate(self._voltages):
            if self._abort:
                break
            self._master.update()
            j = np.round(j * 1000, 0)
            vdc = j / 1000
            self._sr7270_dual_harmonic.change_applied_voltage(j)
            tk_sleep(self._master, self._time_constant * 3 * 1000)  # three times the largest time constant
            self._master.update()
            if self._abort:
                break
            xy1 = []
            xy2 = []
            xy = []
            adc = []
            for k in range(self._number_measurements):
                for q in [xy.append(self._sr7270_single_reference.read_xy()), xy1.append(self._sr7270_dual_harmonic.read_xy1()),
                          xy2.append(self._sr7270_dual_harmonic.read_xy2()), adc.append(self._sr7270_dual_harmonic.read_adc(3))]:
                    self._master.update()
                    tk_sleep(self._master, 10)
                    q
                self._writer.writerow([vdc, adc[k][0], xy[k][0], xy[k][1], xy1[k][0], xy1[k][1], xy2[k][0], xy2[k][1],
                                       convert_adc_to_idc(adc[k][0], self._gain),
                                       convert_x1_to_didv(xy1[k][0], self._gain, self._osc),
                                       convert_x1_to_didv(xy1[k][1], self._gain, self._osc),
                                       convert_x2_to_d2idv2(xy2[k][0], self._gain, self._osc),
                                       convert_x2_to_d2idv2(xy2[k][1], self._gain, self._osc),
                                       normalize_dgdv_from_x1(vdc, xy1[k][0], xy2[k][1], self._gain, self._osc),
                                       convert_x_to_iphoto(xy[k][0], self._gain),
                                       convert_x_to_iphoto(xy[k][1], self._gain),
                                       vdc / convert_adc_to_idc(adc[k][0], self._gain),
                                       1 / convert_x1_to_didv(xy1[k][0], self._gain, self._osc)])
            self._didvx.append(convert_x1_to_didv(np.average([k[0] for k in xy1]), self._gain, self._osc))
            self._didvy.append(convert_x1_to_didv(np.average([k[1] for k in xy1]), self._gain, self._osc))
            self._d2idvx2.append(convert_x2_to_d2idv2(np.average([k[0] for k in xy2]), self._gain, self._osc))
            self._d2idvy2.append(convert_x2_to_d2idv2(np.average([k[1] for k in xy2]), self._gain, self._osc))
            self._iphotox.append(convert_x_to_iphoto(np.average([k[0] for k in xy]), self._gain))
            self._iphotoy.append(convert_x_to_iphoto(np.average([k[1] for k in xy]), self._gain))
            self._idc.append(convert_adc_to_idc(np.average([k[0] for k in adc]), self._gain))
            self._dgdv_normalized.append(normalize_dgdv_from_didv(vdc, self._didvx[i], self._d2idvx2[i]))
            if i >= 1:
                self._diff_d2idvx2.append(differentiate_d2idv2(self._didvx[i], self._didvx[i-1], self._osc))
                self._diff_d2idvy2.append(differentiate_d2idv2(self._didvy[i], self._didvy[i-1], self._osc))
            self._ax1.plot(vdc, self._idc[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax2.plot(vdc, self._didvx[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax2_twin.plot(vdc, self._didvy[i], linestyle='', color='red', marker='o', markersize=2)
            self._ax3.plot(vdc, self._d2idvx2[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax3_twin.plot(vdc, self._d2idvy2[i], linestyle='', color='red', marker='o', markersize=2)
            self._ax4.plot(vdc, self._dgdv_normalized[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax4_twin.plot(vdc, self._iphotox[i], linestyle='', color='red', marker='o', markersize=2)
            if i > 1:
                self._ax5.plot(vdc, np.diff([self._didvx[i], self._didvx[i-1]]) *
                               (1/4 * self._gain * (self._osc/1000)**2), linestyle='', color='blue', marker='o',
                               markersize=2)
                self._sweep_writer.writerow([vdc, adc[-1][0], xy[-1][0], xy[-1][1], xy1[-1][0], xy1[-1][1], xy2[-1][0],
                                             xy2[-1][1], self._idc[i], self._didvx[i], self._didvy[i], self._d2idvx2[i],
                                             self._d2idvy2[i], self._dgdv_normalized[i], self._iphotox[i],
                                             self._iphotoy[i], vdc/self._idc[i], 1/self._didvx[i],
                                             self._diff_d2idvx2[i-1], self._diff_d2idvy2[i-1]])
            else:
                self._sweep_writer.writerow([vdc, adc[-1][0], xy[-1][0], xy[-1][1], xy1[-1][0], xy1[-1][1], xy2[-1][0],
                                             xy2[-1][1], self._idc[i], self._didvx[i], self._didvy[i], self._d2idvx2[i],
                                             self._d2idvy2[i], self._dgdv_normalized[i], self._iphotox[i],
                                             self._iphotoy[i], vdc / self._idc[i], 1 / self._didvx[i]])
            self._fig.tight_layout()
            self._fig.canvas.draw()

    def main(self):
        button = tk.Button(master=self._master, text='Abort', command=self.abort)
        button.pack(side=tk.BOTTOM)
        self.makefile()
        with open(self._filename, 'w', newline='') as inputfile, open(self._sweep_filename, 'w', newline='') as fin:
            try:
                self._sr7270_dual_harmonic.change_oscillator_amplitude(self._osc * 1000)
                tk_sleep(self._master, 300)
                self._writer = csv.writer(inputfile)
                self._sweep_writer = csv.writer(fin)
                self.write_header()
                self.setup_plots()
                self.measure()
                self._sr7270_dual_harmonic.change_applied_voltage(0)
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
























