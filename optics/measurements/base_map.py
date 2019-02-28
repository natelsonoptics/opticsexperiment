from optics.measurements.base_measurement import LockinBaseMeasurement
import numpy as np
from optics.misc_utility.tkinter_utilities import tk_sleep
from optics.misc_utility import scanner
import warnings
import matplotlib.pyplot as plt


class MapMeasurement(LockinBaseMeasurement):
    def __init__(self, master, filepath, notes, device, scan, xd, yd, xr, yr, xc, yc,
                 gain=None, npc3sg_input=None, sr7270_single_reference=None, powermeter=None, waveplate=None,
                 sr7270_dual_harmonic=None, ccd=None, mono=None, daq_input=None, direction=True, npc3sg_x=None,
                 npc3sg_y=None):
        super().__init__(master=master, filepath=filepath, device=device, npc3sg_input=npc3sg_input,
                         sr7270_dual_harmonic=sr7270_dual_harmonic, sr7270_single_reference=sr7270_single_reference,
                         powermeter=powermeter, waveplate=waveplate, notes=notes, gain=gain, scan=scan, ccd=ccd,
                         mono=mono, daq_input=daq_input, npc3sg_x=npc3sg_x, npc3sg_y=npc3sg_y)
        self._xd = xd  # x pixel density
        self._yd = yd  # y pixel density
        self._yr = yr  # y range
        self._xr = xr  # x range
        self._xc = xc  # x center position
        self._yc = yc  # y center position
        self._x_val, self._y_val = scanner.find_scan_values(self._xc, self._yc, self._xr, self._yr, self._xd, self._yd)
        self._z1 = np.zeros((self._xd, self._yd))
        self._z2 = np.zeros((self._xd, self._yd))
        self._direction = direction
        if not self._direction:
            self._y_val = self._y_val[::-1]
        self._time_constant = self._sr7270_single_reference.read_tc()

    def load(self):
        self._ax1 = self._fig.add_subplot(211)
        self._ax2 = self._fig.add_subplot(212)
        self._im1 = self._ax1.imshow(self._z1.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self._im2 = self._ax2.imshow(self._z2.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self._clb1 = self._fig.colorbar(self._im1, ax=self._ax1)
        self._clb2 = self._fig.colorbar(self._im2, ax=self._ax2)

    def onclick(self, event):
        try:
            points = [int(np.ceil(event.xdata - 0.5)), int(np.ceil(event.ydata - 0.5))]
            if not self._direction:
                points = [int(np.ceil(event.xdata - 0.5)), int(np.ceil(self._yd - event.ydata - 0.5 - 1))]
            self._npc3sg_x.move(self._x_val[points[0]])
            self._npc3sg_y.move(self._y_val[points[1]])
            print('pixel: ' + str(points))
            print('position: ' + str(self._x_val[points[0]]) + ', ' + str(self._y_val[points[1]]))
        except:
            print('invalid position')

    @staticmethod
    def update_plot(im, data, min_val, max_val):
        im.set_data(data.T)
        im.set_clim(vmin=min_val)
        im.set_clim(vmax=max_val)

    def finish_plots(self):
        pass

    def do_measurement(self, x_ind, y_ind):
        pass

    def stop2(self):
        pass

    def measure(self):
        for y_ind, i in enumerate(self._y_val):
            self._master.update()
            if self._abort:
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
                break
            if not self._direction:
                y_ind = len(self._y_val) - y_ind - 1
            self._npc3sg_y.move(i)
            for x_ind, j in enumerate(self._x_val):
                self._npc3sg_x.move(j)
                tk_sleep(self._master, 3 * 1000 * self._time_constant)  # DO NOT USE TIME.SLEEP IN TKINTER LOOP
                self.do_measurement(x_ind, y_ind)
                self._fig.tight_layout()
                self._canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
                self._master.update()
                if self._abort:
                    self._npc3sg_x.move(0)
                    self._npc3sg_y.move(0)
                    break
        self._npc3sg_x.move(0)
        self._npc3sg_y.move(0)  # returns piezo controller position to 0,0
        self.finish_plots()
        self._canvas.draw()

    def stop(self):
        self.finish_plots()
        self._canvas.draw()
        warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
        # that was never written
        cid = self._fig.canvas.mpl_connect('button_press_event',
                                           self.onclick)  # click on pixel to move laser position there
        self.stop2()

    def main(self):
        self.main2('map scan', colormap_rescale=True, center_laser=True, record_position=False)



