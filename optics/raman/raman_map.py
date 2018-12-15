class RamanMapScan(BaseRamanMeasurement):
    def __init__(self, master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                 shutter, darkcurrent, darkcorrected, filepath, notes, device, index, xd, yd, xr, yr, xc, yc,
                 npc3sg_x, npc3sg_y, npc3sg_input, start, stop, sleep_time, powermeter, waveplate, direction=True):
        self._master = master
        self._notes = notes
        self._device = device
        super().__init__(self._master, ccd, grating, raman_gain, center_wavelength, units, integration_time, acquisitions,
                         shutter, darkcurrent, darkcorrected, device, filepath, notes, index, waveplate, powermeter)
        self._xd = xd  # x pixel density
        self._yd = yd  # y pixel density
        self._yr = yr  # y range
        self._xr = xr  # x range
        self._xc = xc  # x center position
        self._yc = yc  # y center position
        self._start = start
        self._stop = stop
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._powermeter = powermeter
        self._z1 = np.zeros((self._xd, self._yd))
        self._z2 = np.zeros((self._xd, self._yd))
        self._im1 = self._single_ax1.imshow(self._z1.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
        self._clb1 = self._single_fig.colorbar(self._im1, ax=self._single_ax1)
        self._writer = None
        self._x_val, self._y_val = scanner.find_scan_values(self._xc, self._yc, self._xr, self._yr, self._xd, self._yd)
        self._direction = direction
        if not self._direction:
            self._y_val = self._y_val[::-1]
        self._sleep_time = sleep_time

    def abort(self):
        self._abort = True

    def write_header(self):
        self._writer.writerow(['x scan density:', self._xd])
        self._writer.writerow(['y scan density:', self._yd])
        self._writer.writerow(['x range:', self._xr])
        self._writer.writerow(['y range:', self._yr])
        self._writer.writerow(['x center:', self._xc])
        self._writer.writerow(['y center:', self._yc])
        self._writer.writerow(['polarization:', self._polarization])
        if self._powermeter:
            self._writer.writerow(['power (W):', self._powermeter.read_power()])
        else:
            self._writer.writerow(['power (W):', 'not measured'])
        self._writer.writerow(['laser wavelength:', laser_wavelength])
        gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
        self._writer.writerow(['raman gain:', gain_options[self._raman_gain]])
        self._writer.writerow(['center wavelength:', self._center_wavelength])
        self._writer.writerow(['acquisitions:', self._acquisitions])
        self._writer.writerow(['integration time:', self._integration_time])
        self._writer.writerow(['shutter open:', self._shutter])
        self._writer.writerow(['dark current corrected:', self._dark_current])
        self._writer.writerow(['dark corrected:', self._dark_corrected])
        self._writer.writerow(['grating:', self._grating])
        self._writer.writerow(['time between scans:', self._sleep_time])
        self._writer.writerow(['x value units:', self._units])
        self._writer.writerow(['notes:', self._notes])
        self._writer.writerow(['end:', 'end of header'])
        self._writer.writerow(['x values', *self._xvalues])


    def setup_plots(self):
        self._clb1.set_label('counts', rotation=270, labelpad=20)
        self._single_ax1.title.set_text('Raman signal {} - {} {}'.format(self._start, self._stop, self._units))

    def update_plot(self, im, data, min_val, max_val):
        im.set_data(data.T)
        im.set_clim(vmin=min_val)
        im.set_clim(vmax=max_val)

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

    def run_scan(self):
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
                tk_sleep(self._master, 1000 * self._sleep_time)  # DO NOT USE TIME.SLEEP IN TKINTER LOOP
                _, data = self.take_spectrum()
                integrated = self.integrate_spectrum(data, self._start, self._stop)
                self._writer.writerow([(x_ind, y_ind), *integrated])
                self._z1[x_ind][y_ind] = integrated
                self.update_plot(self._im1, self._z1, np.amin(self._z1), np.amax(self._z1))
                self._single_fig.tight_layout()
                self._single_canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
                self._master.update()
                if self._abort:
                    self._npc3sg_x.move(0)
                    self._npc3sg_y.move(0)
                    break
        self._npc3sg_x.move(0)
        self._npc3sg_y.move(0)  # returns piezo controller position to 0,0

    def main(self):
        self.pack_buttons(True, False, False)
        self.make_file('Raman map')
        with open(self._filename, 'w', newline='') as inputfile:
            try:
                self._writer = csv.writer(inputfile)
                self.setup_plots()
                self._single_canvas.draw()
                self.write_header()
                self.run_scan()
                heating_plot.plot(self._single_ax1, self._im1, self._z1, np.amax(self._z1), np.amin(self._z1))
                self._single_canvas.draw()
                self._single_fig.savefig(self._imagefile, format='png',
                                  bbox_inches='tight')  # saves an image of the completed data
                heating_plot.plot(self._single_ax1, self._im1, self._z1, np.amax(self._z1), np.amin(self._z1))
                self._single_canvas.draw()  # shows the completed scan
                warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
                # that was never written
                cid = self._single_fig.canvas.mpl_connect('button_press_event',
                                                   self.onclick)  # click on pixel to move laser position there
                self._npc3sg_x.move(0)
                self._npc3sg_y.move(0)
            except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
                pass
