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
    convert_adc_to_idc, normalize_iets_from_x1, normalize_iets_from_didv, differentiate_d2idv2
import pandas as pd
import time


class CurrentVoltageGateSweep:
    def __init__(self, master, filepath, notes, device, index, gain, osc, start_voltage, stop_voltage, steps,
                 number_measurements, sr7270_dual_harmonic, sr7270_single_reference, wait_time_ms, scans, tick_spacing,
                 keithley, min_gate, max_gate, gate_steps):
        self._master = master
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._index = index
        self._gain = gain
        self._osc = osc / 1000
        self._number_measurements = number_measurements
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._fig = None
        self._canvas = None
        self._ax1 = None
        self._ax2 = None
        self._ax3 = None
        self._ax4 = None
        self._ax5 = None
        self._ax2_twin = None
        self._ax3_twin = None
        self._ax4_twin = None
        self._voltages = np.linspace(stop_voltage / 1000, start_voltage / 1000, steps)
        self._writer = None
        self._sweep_writer = None
        self._filename = None
        self._imagefile = None
        self._sweep_filename = None
        self._averaged_filename = None
        self._averaged_imagefile = None
        self._wf_imagefile = None
        self._wf_didvx_file = None
        self._wf_didvy_file = None
        self._wf_d2idvx2_file = None
        self._wf_d2idvy2_file = None
        self._wf_iets_file = None
        self._wf_iets_y_file = None
        self._gates = np.linspace(min_gate, max_gate, gate_steps)
        self._gate = self._gates[0]
        self._wf_fig = Figure()
        self._wf_fig.set_size_inches(14, 9)
        self._wf_ax1 = self._wf_fig.add_subplot(321)
        self._wf_ax2 = self._wf_fig.add_subplot(322)
        self._wf_ax3 = self._wf_fig.add_subplot(323)
        self._wf_ax4 = self._wf_fig.add_subplot(324)
        self._wf_ax5 = self._wf_fig.add_subplot(325)
        self._wf_ax6 = self._wf_fig.add_subplot(326)
        self._wf_1 = np.zeros((len(self._gates), len(self._voltages)))
        self._wf_2 = np.zeros((len(self._gates), len(self._voltages)))
        self._wf_3 = np.zeros((len(self._gates), len(self._voltages)))
        self._wf_4 = np.zeros((len(self._gates), len(self._voltages)))
        self._wf_5 = np.zeros((len(self._gates), len(self._voltages)))
        self._wf_6 = np.zeros((len(self._gates), len(self._voltages)))
        self._im1 = self._wf_ax1.imshow(self._wf_1, interpolation='nearest', origin='lower', aspect='auto',
                                        extent=[self._voltages[-1], self._voltages[0], self._gates[0], self._gates[-1]])
        self._im2 = self._wf_ax2.imshow(self._wf_2, interpolation='nearest',
                                     origin='lower', aspect='auto', extent=[self._voltages[-1], self._voltages[0], self._gates[0], self._gates[-1]])
        self._im3 = self._wf_ax3.imshow(self._wf_3,  interpolation='nearest',
                                     origin='lower', aspect='auto', extent=[self._voltages[-1], self._voltages[0], self._gates[0], self._gates[-1]])
        self._im4 = self._wf_ax4.imshow(self._wf_4, interpolation='nearest',
                                     origin='lower', aspect='auto', extent=[self._voltages[-1], self._voltages[0], self._gates[0], self._gates[-1]])
        self._im5 = self._wf_ax5.imshow(self._wf_5, interpolation='nearest',
                                     origin='lower', aspect='auto', extent=[self._voltages[-1], self._voltages[0], self._gates[0], self._gates[-1]])
        self._im6 = self._wf_ax6.imshow(self._wf_6, interpolation='nearest',
                                     origin='lower', aspect='auto', extent=[self._voltages[-1], self._voltages[0], self._gates[0], self._gates[-1]])
        self._wf_ax1.set_title('dIdVx')
        self._wf_ax2.set_title('dIdVy')
        self._wf_ax3.set_title('d2IdV2x')
        self._wf_ax4.set_title('d2IdV2y')
        self._wf_ax5.set_title('normalized IETS x')
        self._wf_ax6.set_title('normalized IETS y')
        for ax in [self._wf_ax1, self._wf_ax2, self._wf_ax3, self._wf_ax4, self._wf_ax5, self._wf_ax6]:
            ax.set_xlabel('applied voltage')
            ax.set_ylabel('gate (V)')
            x = np.flip(self._voltages, axis=0)
            y = self._gates
        self._clb1 = self._wf_fig.colorbar(self._im1, ax=self._wf_ax1)
        self._clb2 = self._wf_fig.colorbar(self._im2, ax=self._wf_ax2)
        self._clb3 = self._wf_fig.colorbar(self._im3, ax=self._wf_ax3)
        self._clb4 = self._wf_fig.colorbar(self._im4, ax=self._wf_ax4)
        self._clb5 = self._wf_fig.colorbar(self._im5, ax=self._wf_ax5)
        self._clb6 = self._wf_fig.colorbar(self._im6, ax=self._wf_ax6)
        self._wf_canvas = FigureCanvasTkAgg(self._wf_fig, master=tk.Toplevel(self._master))
        self._wf_fig.tight_layout()
        self._wf_canvas.draw()
        self._wf_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self._didvx = []
        self._didvx = []
        self._didvy = []
        self._d2idvx2 = []
        self._d2idvy2 = []
        self._iphotox = []
        self._iphotoy = []
        self._idc = []
        self._iets_normalized = []
        self._iets_normalized_y = []
        self._diff_d2idvx2 = []
        self._diff_d2idvy2 = []
        self._total_voltages = []
        self._abort = False
        self._time_constant = np.amax([self._sr7270_dual_harmonic.read_tc(),
                                       self._sr7270_dual_harmonic.read_tc(channel=2),
                                       self._sr7270_single_reference.read_tc()])
        self._wait_time_ms = wait_time_ms
        self._scans = scans
        self._tick_spacing = tick_spacing
        self._averaged_data_frame = pd.DataFrame(columns=['voltage', 'idc', 'didvx', 'didvy', 'd2idvx2', 'd2idvy2',
                                                          'iphotox', 'iphotoy', 'iets_normalized', 'iets_normalized_y',
                                                          'diff d2idvx2', 'diff d2idvy2'])
        self._keithley = keithley
        self._keithley.reset()
        self._keithley.enable_output()
        if self._gate:
            print('ramping the gate voltage to {} V'.format(self._gate))
            for i in np.linspace(0, self._gate, np.abs(self._gate * 4)):
                self._keithley.set_voltage_no_compliance(i)
                tk_sleep(self._master, 100)
        self._keithley.set_voltage_no_compliance(self._gate)
        self._raw_filepath = None
        self._averaged_filepath = None
        self._v = np.zeros((1, ))
        self._v = []

    def abort(self):
        self._abort = True

    def write_header(self):
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['osc amplitude (V):', self._sr7270_dual_harmonic.read_oscillator_amplitude()])
        self._writer.writerow(['osc frequency:', self._sr7270_dual_harmonic.read_oscillator_frequency()])
        self._writer.writerow(['single reference time constant:', self._sr7270_single_reference.read_tc()])
        self._writer.writerow(['dual harmonic time constant 1:', self._sr7270_dual_harmonic.read_tc()])
        self._writer.writerow(['dual harmonic time constant 2:', self._sr7270_dual_harmonic.read_tc(channel=2)])
        self._writer.writerow(['single reference reference phase:',
                               self._sr7270_single_reference.read_reference_phase()])
        self._writer.writerow(['dual harmonic reference phase 1:', self._sr7270_dual_harmonic.read_reference_phase()])
        self._writer.writerow(['dual harmonic reference phase 2:',
                               self._sr7270_dual_harmonic.read_reference_phase(channel=2)])
        self._writer.writerow(['gate (V):', self._gate])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['applied voltage (V)', 'raw adc', 'raw X', 'raw Y', 'raw X1', 'raw Y1', 'raw X2',
                               'raw Y2', 'Idc', 'dI/dVx', 'dI/dVy', 'd2I/dVx2', 'd2I/dVy2',
                               'normalized IETS (1/V)', 'normalized IETS y (1/V)', 'PhotoX', 'PhotoY', 'resistance (V/I)', 'r (dV/dI)'])
        self._sweep_writer.writerow(['gain:', self._gain])
        self._sweep_writer.writerow(['osc amplitude (V):', self._sr7270_dual_harmonic.read_oscillator_amplitude()])
        self._sweep_writer.writerow(['osc frequency:', self._sr7270_dual_harmonic.read_oscillator_frequency()])
        self._sweep_writer.writerow(['time constant:', self._sr7270_single_reference.read_tc()])
        self._sweep_writer.writerow(['top time constant:', self._sr7270_dual_harmonic.read_tc()])
        self._writer.writerow(['gate (V):', self._gate])
        self._sweep_writer.writerow(['notes:', self._notes])
        self._sweep_writer.writerow(['end:', 'end of header'])
        self._sweep_writer.writerow(['applied voltage (V)', 'raw adc', 'raw X', 'raw Y', 'raw X1', 'raw Y1', 'raw X2',
                                     'raw Y2', 'Idc', 'dI/dVx', 'dI/dVy', 'd2I/dVx2', 'd2I/dVy2',
                                     'normalized IETS (1/V)', 'normalized IETS y (1/V)', 'PhotoX', 'PhotoY', 'resistance (V/I)', 'r (dV/dI)',
                                     'diff d2I/dVx2', 'diff d2I/dVy2'])

    def makewaterfallfile(self):
        os.makedirs(self._filepath, exist_ok=True)
        f = os.path.join(self._filepath, '{}_{}'.format(self._device, self._index))
        while path.exists(f):
            self._index += 1
            f = os.path.join(self._filepath, '{}_{}'.format(self._device, self._index))
        os.makedirs(f, exist_ok=True)
        self._filepath = f
        self._wf_imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'waterfall', self._index, '.png'))
        while path.exists(self._wf_imagefile):
            self._index += 1
            self._wf_imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'waterfall', self._index, '.png'))
        self._wf_didvx_file = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'didvx waterfall', self._index, '.csv'))
        self._wf_didvy_file = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'didvy waterfall', self._index, '.csv'))
        self._wf_d2idvx2_file = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'd2idvx2 waterfall', self._index, '.csv'))
        self._wf_d2idvy2_file = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'd2idvy2 waterfall', self._index, '.csv'))
        self._wf_iets_file = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'iets waterfall', self._index, '.csv'))
        self._wf_iets_y_file = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'iets y waterfall', self._index, '.csv'))
        self._raw_filepath = path.join(self._filepath, '{}_{}_{}'.format(self._device, 'raw scans', self._index))
        os.makedirs(self._raw_filepath, exist_ok=True)
        self._averaged_filepath = path.join(self._filepath, '{}_{}_{}'.format(self._device, 'averaged scans', self._index))
        os.makedirs(self._averaged_filepath, exist_ok=True)

    def makefile(self, scan):
        index = self._index
        self._averaged_filename = path.join(self._averaged_filepath, '{}_{}_{}_{}_{}{}'.format(self._device, 'gate',
                                                                                               self._gate,
                                                                                               'total averaged IV sweep',
                                                                                               index, '.csv'))
        while path.exists(self._averaged_filename):
            index += 1
            self._averaged_filename = path.join(self._averaged_filepath, '{}_{}_{}_{}_{}{}'.format(self._device, 'gate',
                                                                                                   self._gate,
                                                                                                   'total averaged IV sweep',
                                                                                                   index, '.csv'))
        raw_filepath = path.join(self._raw_filepath, '{}_{}_{}_{}_{}'.format(self._device, 'gate', self._gate, 'raw scans', index))
        os.makedirs(raw_filepath, exist_ok=True)
        sweep_filepath = path.join(self._averaged_filepath, '{}_{}_{}_{}_{}'.format(self._device, 'gate', self._gate, 'individual scans', index))
        os.makedirs(sweep_filepath, exist_ok=True)
        self._filename = path.join(raw_filepath, '{}_{}_{}_{}_{} {} {} {}_{}{}'.format(self._device, 'gate', self._gate,
                                                                                       'raw IV sweep', 'scan',
                                                                                       scan, 'of', self._scans, index,
                                                                                       '.csv'))
        self._sweep_filename = path.join(sweep_filepath,
                                         '{}_{}_{}_{}_{} {} {} {}_{}{}'.format(self._device, 'gate', self._gate,
                                                                               'averaged IV sweep',
                                                                               'scan', scan, 'of',
                                                                               self._scans, index, '.csv'))
        self._imagefile = path.join(sweep_filepath,
                                    '{}_{}_{}_{}_{} {} {} {}_{}{}'.format(self._device, 'gate', self._gate, 'IV sweep',
                                                                          'scan',
                                                                          scan, 'of', self._scans, index,
                                                                          '.png'))
        self._averaged_imagefile = path.join(self._averaged_filepath, '{}_{}_{}_{}_{}{}'.format(self._device, 'gate', self._gate,
                                                                                       'total averaged IV sweep',
                                                                                       index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._raw_filepath, '{}_{}_{} {} {} {}_{}{}'.format(self._device, 'raw IV sweep',
                                                                                       'scan', scan, 'of',
                                                                                       self._scans, index, '.csv'))
            self._sweep_filename = path.join(self._averaged_filepath, '{}_{}_{} {} {} {}_{}{}'.format(self._device,
                                                                                             'averaged IV sweep',
                                                                                             'scan', scan, 'of',
                                                                                             self._scans, index,
                                                                                             '.csv'))
            self._imagefile = path.join(self._raw_filepath, '{}_{}_{} {} {} {}_{}{}'.format(self._device, 'IV sweep',
                                                                                        'scan', scan, 'of',
                                                                                        self._scans, index, '.png'))
            self._averaged_filename = path.join(self._averaged_filepath, '{}_{} {} {}_{}{}'.format(self._device,
                                                                                          'total averaged IV sweep of',
                                                                                          self._scans, 'scans', index,
                                                                                          '.csv'))
            self._averaged_imagefile = path.join(self._averaged_filepath, '{}_{} {} {}_{}{}'.format(self._device,
                                                                                           'total averaged IV sweep of',
                                                                                           self._scans, 'scans', index,
                                                                                           '.png'))

    def setup_plots(self):
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
        for i in [(self._ax1, 'Idc', 'blue'), (self._ax2, 'dI/dVx', 'blue'), (self._ax3, 'd2I/dVx2', 'blue'),
                  (self._ax4, 'Normalized IETS (1/V)', 'blue'), (self._ax5, 'numerical d2I/dVx2', 'blue'),
                  (self._ax2_twin, 'dIdVy', 'red'), (self._ax3_twin, 'd2I/dVy2', 'red'),
                  (self._ax4_twin, 'PhotoX', 'red')]:
            i[0].set_xlabel('DC Voltage (V)')
            i[0].set_ylabel(i[1], color=i[2])
            i[0].tick_params(axis='y', labelcolor=i[2])
            i[0].plot([i for i in self._voltages], [0 for i in self._voltages], c=i[2], linestyle='--', linewidth=0.5)
            i[0].ticklabel_format(axis='1', style='sci', scilimits=(-3, 3))
            if self._voltages[0] < self._voltages[-1]:
                [i[0].axvline(x=q / 1000, color='k', linestyle='--', linewidth=0.5) for q in
                 range(int(self._voltages[0] * 1000), int(self._voltages[-1] * 1000)) if q % self._tick_spacing == 0]
                i[0].set_xlim(self._voltages[0], self._voltages[-1])
            else:
                [i[0].axvline(x=q / 1000, color='k', linestyle='--', linewidth=0.5) for q in
                 range(int(self._voltages[-1] * 1000), int(self._voltages[0] * 1000)) if q % self._tick_spacing == 0]
                i[0].set_xlim(self._voltages[-1], self._voltages[0])
        self._fig.tight_layout()
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def set_limits(self):
        self._ax1.set_ylim(np.amin(self._idc), np.amax(self._idc))
        self._ax2.set_ylim(np.amin(self._didvx), np.amax(self._didvx))
        self._ax2_twin.set_ylim(np.amin(self._didvy), np.amax(self._didvy))
        self._ax3.set_ylim(np.amin(self._d2idvx2), np.amax(self._d2idvx2))
        self._ax3_twin.set_ylim(np.amin(self._d2idvy2), np.amax(self._d2idvy2))
        self._ax4.set_ylim(np.amin(self._iets_normalized), np.amax(self._iets_normalized))
        self._ax4_twin.set_ylim(np.amin(self._iphotox), np.amax(self._iphotox))

    def reset_values(self):
        self._didvx = []
        self._didvx = []
        self._didvy = []
        self._d2idvx2 = []
        self._d2idvy2 = []
        self._iphotox = []
        self._iphotoy = []
        self._idc = []
        self._iets_normalized = []
        self._diff_d2idvx2 = []
        self._diff_d2idvy2 = []

    def update_plot(self, im, data):
        im.set_data(data)
        im.set_clim(vmin=np.amin(data))
        im.set_clim(vmax=np.amax(data))

    def measure(self):
        for i, j in enumerate(self._voltages):
            if self._abort:
                break
            self._master.update()
            j = np.round(j * 1000, 0)
            vdc = j / 1000
            self._sr7270_dual_harmonic.change_applied_voltage(j)
            tk_sleep(self._master, self._time_constant)  # three times the largest time constant
            if self._abort:
                break
            xy1 = []
            xy2 = []
            xy = []
            adc = []
            for k in range(self._number_measurements):
                xy.append(self._sr7270_single_reference.read_xy())
                xy1.append(self._sr7270_dual_harmonic.read_xy1())
                xy2.append(self._sr7270_dual_harmonic.read_xy2())
                adc.append(self._sr7270_dual_harmonic.read_adc(3))
                tk_sleep(self._master, self._wait_time_ms)
                self._writer.writerow([vdc, adc[k][0], xy[k][0], xy[k][1], xy1[k][0], xy1[k][1], xy2[k][0], xy2[k][1],
                                       convert_adc_to_idc(adc[k][0], self._gain),
                                       convert_x1_to_didv(xy1[k][0], self._gain, self._osc),
                                       convert_x1_to_didv(xy1[k][1], self._gain, self._osc),
                                       convert_x2_to_d2idv2(xy2[k][0], self._gain, self._osc),
                                       convert_x2_to_d2idv2(xy2[k][1], self._gain, self._osc),
                                       normalize_iets_from_x1(xy1[k][0], xy2[k][0], self._gain, self._osc),
                                       normalize_iets_from_x1(xy1[k][1], xy2[k][1], self._gain, self._osc),
                                       convert_x_to_iphoto(xy[k][0], self._gain),
                                       convert_x_to_iphoto(xy[k][1], self._gain),
                                       vdc / convert_adc_to_idc(adc[k][0], self._gain),
                                       1 / convert_x1_to_didv(xy1[k][0], self._gain, self._osc) if xy1[k][0] else 0])
            self._didvx.append(convert_x1_to_didv(np.average([k[0] for k in xy1]), self._gain, self._osc))
            self._didvy.append(convert_x1_to_didv(np.average([k[1] for k in xy1]), self._gain, self._osc))
            if i >= 1:
                self._diff_d2idvx2.append(differentiate_d2idv2(self._didvx[i], self._didvx[i - 1]))
                self._diff_d2idvy2.append(differentiate_d2idv2(self._didvy[i], self._didvy[i - 1]))
            self._d2idvx2.append(convert_x2_to_d2idv2(np.average([k[0] for k in xy2]), self._gain, self._osc))
            self._d2idvy2.append(convert_x2_to_d2idv2(np.average([k[1] for k in xy2]), self._gain, self._osc))
            self._iphotox.append(convert_x_to_iphoto(np.average([k[0] for k in xy]), self._gain))
            self._iphotoy.append(convert_x_to_iphoto(np.average([k[1] for k in xy]), self._gain))
            self._idc.append(convert_adc_to_idc(np.average([k[0] for k in adc]), self._gain))
            self._iets_normalized.append(normalize_iets_from_didv(self._didvx[i], self._d2idvx2[i]))
            self._iets_normalized_y.append(normalize_iets_from_didv(self._didvy[i], self._d2idvy2[i]))
            self._averaged_data_frame.loc[len(self._averaged_data_frame)] = [vdc, self._idc[-1], self._didvx[-1],
                                                                             self._didvy[-1],
                                                                             self._d2idvx2[-1], self._d2idvy2[-1],
                                                                             self._iphotox[-1],
                                                                             self._iphotoy[-1],
                                                                             self._iets_normalized[-1], self._iets_normalized_y[-1],
                                                                             self._diff_d2idvx2[
                                                                                 -1] if self._diff_d2idvx2 else 0,
                                                                             self._diff_d2idvy2[
                                                                                 -1] if self._diff_d2idvy2 else 0]
            self._ax1.plot(vdc, self._idc[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax2.plot(vdc, self._didvx[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax2_twin.plot(vdc, self._didvy[i], linestyle='', color='red', marker='o', markersize=2)
            self._ax3.plot(vdc, self._d2idvx2[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax3_twin.plot(vdc, self._d2idvy2[i], linestyle='', color='red', marker='o', markersize=2)
            self._ax4.plot(vdc, self._iets_normalized[i], linestyle='', color='blue', marker='o', markersize=2)
            self._ax4_twin.plot(vdc, self._iphotox[i], linestyle='', color='red', marker='o', markersize=2)
            if i >= 1:
                self._ax5.plot(vdc, differentiate_d2idv2(self._didvx[i], self._didvx[i - 1]), linestyle='',
                               color='blue',
                               marker='o', markersize=2)
                self._sweep_writer.writerow([vdc, adc[-1][0], xy[-1][0], xy[-1][1], xy1[-1][0], xy1[-1][1], xy2[-1][0],
                                             xy2[-1][1], self._idc[i], self._didvx[i], self._didvy[i], self._d2idvx2[i],
                                             self._d2idvy2[i], self._iets_normalized[i], self._iphotox[i],
                                             self._iphotoy[i], vdc / self._idc[i], 1 / self._didvx[i],
                                             self._diff_d2idvx2[i - 1], self._diff_d2idvy2[i - 1]])
            else:
                self._sweep_writer.writerow([vdc, adc[-1][0], xy[-1][0], xy[-1][1], xy1[-1][0], xy1[-1][1], xy2[-1][0],
                                             xy2[-1][1], self._idc[i], self._didvx[i], self._didvy[i], self._d2idvx2[i],
                                             self._d2idvy2[i], self._iets_normalized[i], self._iphotox[i],
                                             self._iphotoy[i], vdc / self._idc[i], 1 / self._didvx[i]])
            self._fig.tight_layout()
            self._fig.canvas.draw()

    def close(self):
        self.abort()
        self._sr7270_dual_harmonic.change_applied_voltage(0)
        self._keithley.set_voltage(0)
        self._master.destroy()

    def main(self):
        button = tk.Button(master=self._master, text='Abort', command=self.abort)
        button.pack(side=tk.BOTTOM)
        self._master.protocol("WM_DELETE_WINDOW", self.close)
        self.makewaterfallfile()
        for n, gate in enumerate(self._gates):
            if self._abort:
                break
            self._gate = gate
            self._keithley.set_voltage(gate)
            for scan in range(1, self._scans + 1):
                self._voltages = np.flip(self._voltages, axis=0)
                self.makefile(scan)
                with open(self._filename, 'w', newline='') as inputfile, open(self._sweep_filename, 'w', newline='') as fin:
                    try:
                        self._sr7270_dual_harmonic.change_oscillator_amplitude(self._osc * 1000)
                        tk_sleep(self._master, 300)
                        self._writer = csv.writer(inputfile)
                        self._sweep_writer = csv.writer(fin)
                        self.write_header()
                        self.setup_plots()
                        self._ax1.set_title('Scan {} of {}, Gate = {} V'.format(scan, self._scans, self._gate))
                        self.measure()
                        self._fig.savefig(self._imagefile, format='png', bbox_inches='tight')
                        self._canvas.get_tk_widget().destroy()
                        self.reset_values()
                    except ValueError as err:
                        print(err)
                        self._fig.savefig(self._imagefile, format='png',
                                          bbox_inches='tight')  # saves an image of the completed data
            self._sr7270_dual_harmonic.change_applied_voltage(0)
            self.setup_plots()
            self._ax1.set_title('Average of {} scans, Gate = {} V'.format(self._scans, self._gate))
            averaged_data = self._averaged_data_frame.groupby('voltage', as_index=False).mean()
            self._ax1.plot(averaged_data['voltage'], averaged_data['idc'], linestyle='', color='blue', marker='o',
                           markersize=2)
            self._fig.canvas.draw()
            self._ax2.plot(averaged_data['voltage'], averaged_data['didvx'], linestyle='', color='blue', marker='o',
                           markersize=2)
            self._fig.canvas.draw()
            self._ax2_twin.plot(averaged_data['voltage'], averaged_data['didvy'], linestyle='', color='red', marker='o',
                                markersize=2)
            self._fig.canvas.draw()
            self._ax3.plot(averaged_data['voltage'], averaged_data['d2idvx2'], linestyle='', color='blue', marker='o',
                           markersize=2)
            self._fig.canvas.draw()
            self._ax3_twin.plot(averaged_data['voltage'], averaged_data['d2idvy2'], linestyle='', color='red', marker='o',
                                markersize=2)
            self._fig.canvas.draw()
            self._ax4.plot(averaged_data['voltage'], averaged_data['iets_normalized'], linestyle='', color='blue',
                           marker='o', markersize=2)
            self._fig.canvas.draw()
            self._ax4_twin.plot(averaged_data['voltage'], averaged_data['iphotox'], linestyle='', color='red', marker='o',
                                markersize=2)
            self._fig.canvas.draw()
            self._ax5.plot(averaged_data['voltage'], averaged_data['diff d2idvx2'], linestyle='', color='blue', marker='o',
                           markersize=2)
            self._fig.tight_layout()
            self._fig.canvas.draw()
            self._fig.savefig(self._averaged_imagefile, format='png', bbox_inches='tight')
            tk_sleep(self._master, 1000)
            self._canvas.get_tk_widget().destroy()
            averaged_data.to_csv(self._averaged_filename)
            self._wf_1[n] = averaged_data['didvx']
            self._wf_2[n] = averaged_data['didvy']
            self._wf_3[n] = averaged_data['d2idvx2']
            self._wf_4[n] = averaged_data['d2idvy2']
            self._wf_5[n] = averaged_data['iets_normalized']
            self._wf_6[n] = averaged_data['iets_normalized_y']
            self._v = averaged_data['voltage']
            self.update_plot(self._im1, self._wf_1)
            self.update_plot(self._im2, self._wf_2)
            self.update_plot(self._im3, self._wf_3)
            self.update_plot(self._im4, self._wf_4)
            self.update_plot(self._im5, self._wf_5)
            self.update_plot(self._im6, self._wf_6)
            self._wf_canvas.draw()
            self._master.update()
        self._wf_fig.savefig(self._wf_imagefile, format='png', bbox_inches='tight')
        for i in [(self._wf_1, self._wf_didvx_file), (self._wf_2, self._wf_didvy_file), (self._wf_3, self._wf_d2idvx2_file),
                  (self._wf_4, self._wf_d2idvy2_file), (self._wf_5, self._wf_iets_file), (self._wf_6, self._wf_iets_y_file)]:
            df = pd.DataFrame(np.concatenate((self._gates.reshape((len(self._gates), 1)), i[0]), 1), columns=['gate', *[j for j in self._v]])
            df.to_csv(i[1])
        print('ramping gate to 0 V')
        for i in np.linspace(self._gate, 0, np.abs(self._gate * 4)):
            self._keithley.set_voltage_no_compliance(i)
            tk_sleep(self._master, 100)
        self._keithley.set_voltage(0)
