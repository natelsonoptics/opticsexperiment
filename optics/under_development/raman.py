import ctypes

co_initialize = ctypes.windll.ole32.CoInitialize
import tkinter as tk
from tkinter.filedialog import askdirectory
import numpy as np
import matplotlib.pyplot as plt

co_initialize(None)
from optics.under_development.ccd_controller import CCDController2
from optics.under_development.mono_controller import MonoController
import time
from optics.raman import unit_conversions
from optics.gui.base_gui import BaseGUI
import time


class RamanGUI(BaseGUI):
    def __init__(self, master, mono=None, ccd_controller=None, raman_gain=None, grating=None, center_wavelength=785):
        self._master = master
        super().__init__(self._master)
        self._mono = mono
        self._ccd_controller = ccd_controller
        self._raman_gain = raman_gain
        self._grating = grating
        self._shutter = tk.StringVar()
        self._shutter.set('True')
        self._center_wavelength = center_wavelength
        self._units = tk.StringVar()
        self._units.set('cm^-1')

    def build_single_spectrum_gui(self):
        caption = "Single Raman spectrum"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'integration time (s)': 1,
                        'acquisitions to average': 1}
        self.beginform(caption)
        self.make_option_menu('shutter open', self._shutter, ['True', 'False'])
        self.make_option_menu('units', self._units, ['cm^-1', 'nm', 'eV'])
        self.endform(self.single_spectrum)

    def single_spectrum(self, event=None):
        from optics.raman.single_spectrum import take_single_spectrum
        self.fetch(event)
        if self._shutter.get() == 'True':
            shutter = True
        else:
            shutter = False
        take_single_spectrum(self._ccd_controller, self._grating, self._raman_gain,
                             self._center_wavelength, self._units.get(),
                             float(self._inputs['integration time (s)']), int(self._inputs['acquisitions to average']),
                             shutter)


class RamanBaseGUI(BaseGUI):
    def __init__(self, master):
        self._master = master
        super().__init__(self._master)
        self._master.title('Optics Raman setup measurements')
        self._mono = MonoController()
        self._ccd_controller = CCDController2()
        self._gain = self._ccd_controller.read_gain()
        self._gain_options = tk.StringVar()
        gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
        self._gain_options.set(gain_options[self._gain])
        _, self._current_grating, _, _ = self._mono.get_current_turret()
        self._grating = tk.StringVar()
        self._newWindow = None
        self._app = None
        self._width = tk.StringVar()
        self._center_wavelength = self._mono.read_wavelength()

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)
        self._app = RamanGUI(self._newWindow, self._mono, self._ccd_controller, self._gain, self._current_grating,
                             self._center_wavelength)
        measurement = {'singlespectrum': self._app.build_single_spectrum_gui}
        measurement[measurementtype]()

    def build(self):
        row = self.makerow('single spectrum')
        self.make_measurement_button(row, 'Raman', 'singlespectrum')
        row = self.makerow('change paramaters')
        b1 = tk.Button(row, text='Raman gain',
                       command=self.change_gain_gui)
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b = tk.Button(row, text='Grating', command=self.change_grating_gui)
        b.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b = tk.Button(row, text='Slit width', command=self.change_slit_width_gui)
        b.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b = tk.Button(row, text='Center wavelength', command=self.change_center_wavelength_gui)
        b.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b12 = tk.Button(self._master, text='Quit all windows', command=self._master.quit)
        b12.pack()

    def change_gain_gui(self):
        self._newWindow = tk.Toplevel(self._master)
        self._newWindow.title('Change Raman gain')
        label = tk.Label(self._newWindow, text='Change Raman gain')
        label.pack()
        gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
        self._gain_options.set(gain_options[self._gain])
        row = tk.Frame(self._newWindow)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text='gain', anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, self._gain_options, *['high light', 'best dynamic range', 'high sensitivity'])
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        self._newWindow.bind('<Return>', self.change_gain)
        self.makebutton('Run', self.change_gain, master=self._newWindow)
        self.makebutton('Quit', self._newWindow.destroy, master=self._newWindow)

    def change_gain(self):
        gain_options = {'high light': 0, 'best dynamic range': 1, 'high sensitivity': 2}
        self._gain = float(gain_options[self._gain_options.get()])
        self._ccd_controller.set_gain(self._gain)
        print('Raman gain set to {}'.format(self._gain_options.get()))

    def change_grating_gui(self):
        self._newWindow = tk.Toplevel(self._master)
        self._newWindow.title('Change Raman grating')
        label = tk.Label(self._newWindow, text='Change Raman grating')
        label.pack()
        self._grating.set(int(self._current_grating))
        row = tk.Frame(self._newWindow)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text='grating', anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, self._grating, *[1200, 300, 150])
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        self._newWindow.bind('<Return>', self.change_grating)
        self.makebutton('Run', self.change_grating, master=self._newWindow)
        self.makebutton('Quit', self._newWindow.destroy, master=self._newWindow)

    def change_grating(self):
        grating_options = {'1200': 0, '300': 1, '150': 2}
        turret, self._current_grating, blazes, description = self._mono.set_turret(
            int(grating_options[self._grating.get()]))
        now = time.time()
        while self._mono.is_busy():
            print('Moving turret')
            time.sleep(10)
            if time.time() > now + 90:
                print('Mono timeout')
                break
        print('Turret movement complete')
        print('Current turret: {}\nCurrent grating: {}\nCurrent blazes: {}\nCurrent description {}'.format(turret,
                                                                                                           self._current_grating,
                                                                                                           blazes,
                                                                                                           description))

    def change_slit_width_gui(self):
        print(self._mono.read_front_slit_width())

    def change_center_wavelength_gui(self):
        self._newWindow = tk.Toplevel(self._master)
        self._newWindow.title('Change center wavelength')
        self._fields = {'Center wavelength (nm)': '785'}
        self.beginform('Change center wavelength', False, self._newWindow)
        self.makebutton('Run', self.change_center_wavelength, master=self._newWindow)
        self.makebutton('Quit', self._newWindow.destroy, master=self._newWindow)

    def change_center_wavelength(self, event=None):
        self.fetch(event)
        self._center_wavelength = float(self._inputs['Center wavelength (nm)'])
        self._mono.set_wavelength(self._center_wavelength)
        now = time.time()
        while self._mono.is_busy():
            if time.time() > now + 30:
                print('timed out')
                break
            time.sleep(1)
            print('monochrometer moving to center position')
        print('Center wavelength set to {}'.format(self._mono.read_wavelength()))


def main():
    root = tk.Tk()
    app = RamanBaseGUI(root)
    app.build()
    root.mainloop()


main()
