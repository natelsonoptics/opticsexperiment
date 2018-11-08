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


class RamanGUI:
    def __init__(self, master, mono=None, ccd=None, raman_gain=None):
        self._mono = mono
        self._ccd = ccd
        self._master = master
        self._raman_gain = raman_gain
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._fields = {}
        self._filepath = tk.StringVar()
        self._entries = []
        self._inputs = {}
        self._shutter = tk.StringVar()
        self._shutter.set('True')

    def beginform(self, caption, browse_button=True):
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        if browse_button:
            self._browse_button.pack()
        for key in self._fields:
            row = tk.Frame(self._master)
            lab = tk.Label(row, width=15, text=key, anchor='w')
            if key == 'file path':
                ent = tk.Entry(row, textvariable=self._filepath)
            else:
                ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            ent.insert(0, str(self._fields[key]))
            self._entries.append((key, ent))
        return self._entries

    def endform(self, run_command):
        self._master.bind('<Return>', run_command)
        self.makebutton('Run', run_command)
        self.makebutton('Quit', self._master.destroy)

    def make_option_menu(self, label, parameter, option_list):
        row = tk.Frame(self._master)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text=label, anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, parameter, *option_list)
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def makebutton(self, caption, run_command, master=None):
        if not master:
            master = self._master
        b1 = tk.Button(master, text=caption, command=run_command)
        b1.pack(side=tk.LEFT, padx=5, pady=5)

    def onclick_browse(self):
        self._filepath.set(askdirectory())

    def build_single_spectrum_gui(self):
        caption = "Single Raman spectrum"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'integration time (s)': 1,
                        'acquisitions to average': 1}
        self.beginform(caption)
        self.make_option_menu('shutter open', self._shutter, ['True', 'False'])
        self.endform(self.single_spectrum)

    def single_spectrum(self, event=None):
        self.fetch(event)
        raw, data = self._ccd.take_spectrum(float(self._inputs['integration time (s)']), self._raman_gain,
                                            int(self._inputs['acquisitions to average']), self._shutter)
        print(np.shape(data))
        plt.plot([i for i in range(len(data))], data)
        plt.show()


class RamanBaseGUI:
    def __init__(self, master):
        self._master = master
        self._master.title('Optics Raman setup measurements')
        self._mono = MonoController()
        self._mono.set_wavelength(785)
        self._ccd = CCDController2()
        self._gain = 1
        self._gain_options = tk.StringVar()
        self._gain_options.set(1)
        self._newWindow = None
        self._app = None

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)
        self._app = RamanGUI(self._newWindow, self._mono, self._ccd, self._gain)
        measurement = {'singlespectrum': self._app.build_single_spectrum_gui}
        measurement[measurementtype]()

    def make_measurement_button(self, master, text, measurement_type):
        b1 = tk.Button(master, text=text,
                       command=lambda measurementtype=measurement_type: self.new_window(measurementtype))
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

    def makerow(self, title):
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text=title, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        return row

    def build(self):
        row = self.makerow('single spectrum')
        self.make_measurement_button(row, 'Raman', 'singlespectrum')
        row = self.makerow('change paramaters')
        b1 = tk.Button(row, text='Raman gain',
                       command=self.change_gain)
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b12 = tk.Button(self._master, text='Quit all windows', command=self._master.quit)
        b12.pack()

    def makebutton(self, caption, run_command, master=None):
        if not master:
            master = self._master
        b1 = tk.Button(master, text=caption, command=run_command)
        b1.pack(side=tk.LEFT, padx=5, pady=5)

    def change_gain(self):
        self._newWindow = tk.Toplevel(self._master)
        self._newWindow.title('hello')
        label = tk.Label(self._newWindow, text='hello')
        label.pack()
        gain_options = {0: 'high light', 1: 'best dynamic range', 2: 'high sensitivity'}
        self._gain_options.set(gain_options[self._gain])
        row = tk.Frame(self._newWindow)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text='gain', anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, self._gain_options, *['high light', 'best dynamic range', 'high sensitivity'])
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        self._newWindow.bind('<Return>', self.changeit)
        self.makebutton('Run', self.changeit, master=self._newWindow)
        self.makebutton('Quit', self._newWindow.destroy, master=self._newWindow)

    def changeit(self):
        gain_options = {'high light': 0, 'best dynamic range': 1, 'high sensitivity': 2}
        self._gain = gain_options[self._gain_options.get()]
        print(self._gain)


def main():
    root = tk.Tk()
    app = RamanBaseGUI(root)
    app.build()
    root.mainloop()

main()
