import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import time
import matplotlib.pyplot as plt
import csv
import os
from os import path
from optics.hardware_control import hardware_addresses_and_constants as hw


class CurrentVoltageSweep:
    def __init__(self, filepath, notes, device, scan, gain, osc, start_voltage, stop_voltage, steps,
                 number_measurements, sr7270_top, sr7270_bottom):
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._osc = osc
        self._number_measurements = number_measurements
        self._sr7270_top = sr7270_top
        self._sr7270_bottom = sr7270_bottom
        self._fig, (self._ax1, self._ax2, self._ax3, self._ax4) = plt.subplots(4)
        self._ax2_twin = self._ax2.twinx()
        self._ax3_twin = self._ax3.twinx()
        self._ax4_twin = self._ax4.twinx()
        self._voltages = np.linspace(start_voltage, stop_voltage, steps)
        self._low_pass_filter_factor = hw.low_pass_filter_factor
        self._writer = None
        self._filename = None
        self._imagefile = None
        self._didvx = []
        self._didvx = []
        self._didvy = []
        self._d2idvx2 = []
        self._d2idvy2 = []
        self._iphotox = []
        self._iphotoy = []
        self._idc = []
        self._dgdv_normalized = []

    def write_header(self):
        self._writer.writerow(['gain:', self._gain])
        self._writer.writerow(['osc amplitude (V):', self._sr7270_top.read_oscillator_amplitude()[0]])
        self._writer.writerow(['osc frequency:', self._sr7270_top.read_oscillator_frequency()[0]])
        self._writer.writerow(['time constant:', self._sr7270_bottom.read_tc()[0]])
        self._writer.writerow(['top time constant:', self._sr7270_top.read_tc1()[0]])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['applied voltage (V)', 'Idc', 'dI/dVx', 'dI/dVy', 'd2I/dVx2', 'd2I/dVy2',
                               'dG/dV*V/G', 'PhotoX', 'PhotoY', 'resistance (V/I)', 'r (dV/dI)'])

    def makefile(self):
        os.makedirs(self._filepath, exist_ok=True)
        index = self._scan
        self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'IV sweep', index, '.csv'))
        self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'IV sweep', index, '.png'))
        while path.exists(self._filename):
            index += 1
            self._filename = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'IV sweep', index, '.csv'))
            self._imagefile = path.join(self._filepath, '{}_{}_{}{}'.format(self._device, 'IV sweep', index, '.png'))

    def setup_plots(self):
        self._ax1.set_ylabel('Idc', color='blue')
        self._ax1.tick_params(axis='y', labelcolor='blue')
        self._ax2.set_ylabel('dI/dVx', color='blue')
        self._ax2.tick_params(axis='y', labelcolor='blue')
        self._ax2_twin.set_ylabel('dI/dVy', color='red')
        self._ax2_twin.tick_params(axis='y', labelcolor='red')
        self._ax3.set_ylabel('d2I/dVx2', color='blue')
        self._ax3.tick_params(axis='y', labelcolor='blue')
        self._ax3_twin.set_ylabel('d2I/dVy2', color='red')
        self._ax3_twin.tick_params(axis='y', labelcolor='red')
        self._ax4.set_ylabel('dG/dV*V/G', color='blue')
        self._ax4.tick_params(axis='y', labelcolor='blue')
        self._ax4_twin.set_ylabel('PhotoX', color='red')
        self._ax4_twin.tick_params(axis='y', labelcolor='red')
        for i in [self._ax1, self._ax2, self._ax2_twin, self._ax3, self._ax3_twin, self._ax4, self._ax4_twin]:
            i.set_xlabel('DC Voltage (V)')
        self._fig.show()

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
            j = np.round(j, 0)
            vdc = j/1000
            self._sr7270_top.change_applied_voltage(j)
            time.sleep(0.5)
            xy1 = []
            xy2 = []
            xy = []
            adc = []
            for k in range(self._number_measurements):
                time.sleep(0.01)
                xy.append(self._sr7270_bottom.read_xy())
                time.sleep(0.01)
                xy1.append(self._sr7270_top.read_xy1())
                time.sleep(0.01)
                xy2.append(self._sr7270_top.read_xy2())
                time.sleep(0.01)
                adc.append(self._sr7270_top.read_adc(3))
            self._didvx.append(np.average([k[0] for k in xy1]) / (self._gain * (self._osc/1000)))
            self._didvy.append(np.average([k[1] for k in xy1]) / (self._gain * (self._osc/1000)))
            self._d2idvx2.append(np.average([k[0] for k in xy2]) / (self._gain * 1 / 4 * (self._osc/1000) ** 2))
            self._d2idvy2.append(np.average([k[1] for k in xy2]) / (self._gain * 1 / 4 * (self._osc/1000) ** 2))
            self._iphotox.append(np.average([k[0] for k in xy]) / self._gain)
            self._iphotoy.append(np.average([k[1] for k in xy]) / self._gain)
            self._idc.append(np.average([k[0] for k in adc]) / (self._gain * self._low_pass_filter_factor))
            self._dgdv_normalized.append(np.abs(vdc * self._d2idvx2[i] / self._didvx[i]))
            self._ax1.scatter(vdc, self._idc[i], c='b', s=2)
            self._ax2.scatter(vdc, self._didvx[i], c='b', s=2)
            self._ax2_twin.scatter(vdc, self._didvy[i], c='r', s=2)
            self._ax3.scatter(vdc, self._d2idvx2[i], c='b', s=2)
            self._ax3_twin.scatter(vdc, self._d2idvy2[i], c='r', s=2)
            self._ax4.scatter(vdc, self._dgdv_normalized[i], c='b', s=2)
            self._ax4_twin.scatter(vdc, self._iphotox[i], c='r', s=2)
            if i:
                self.set_limits()
            self._writer.writerow([vdc, self._idc[i], self._didvx[i], self._didvy[i], self._d2idvx2[i],
                                   self._d2idvy2[i], self._dgdv_normalized[i], self._iphotox[i], self._iphotoy[i],
                                   vdc/self._idc[i], 1/self._didvx[i]])
            plt.tight_layout()
            self._fig.canvas.draw()

    def main(self):
        self.makefile()
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._sr7270_top.change_oscillator_amplitude(self._osc)
                time.sleep(0.3)
                self._writer = csv.writer(inputfile)
                self.write_header()
                self.setup_plots()
                self.measure()
                self._sr7270_top.change_applied_voltage(0)
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')
            except KeyboardInterrupt:
                plt.savefig(self._imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
























