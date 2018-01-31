#!/usr/bin/python3

import tkinter as tk
import tkinter.filedialog

from optics.heating_measurement.heating_scan import HeatingScan
from optics.thermovoltage_measurement.thermovoltage_intensity import ThermovoltageIntensity
from optics.thermovoltage_measurement.thermovoltage_polarization import ThermovoltagePolarization
from optics.thermovoltage_measurement.thermovoltage_scan import ThermovoltageScan
from optics.thermovoltage_measurement.thermovoltage_time import ThermovoltageTime


class SetupGUI:
    def __init__(self, master, caption, fields, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_top=None, sr7270_bottom=None, powermeter=None, attenuatorwheel=None, polarizer=None):
        self._master = master
        self._master.title(caption)
        self._fields = fields
        self._entries = []
        self._inputs = {}
        self._filepath = tk.StringVar()  # this is a global variable - this needs to change
        if 'file path' in self._fields:
            self._filepath.set(self._fields['file path'])
        self._label = tk.Label(master, text=caption)
        self._label.pack()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_top = sr7270_top
        self._sr7270_bottom = sr7270_bottom
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._polarizer = polarizer
        self._textbox = None
        self._textbox2 = None

    def makeform(self):
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

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        # You need to have "event" input even though it isn't used as an input. If this method was only fetch(self), it
        # only expects one input parameter, which would be fine except you also pass self.fetch to self.master.bind when
        # binding the <Return> key, which means that self.fetch('<Return>') is being called, which is TWO inputs due to
        # 'self'. This event=None allows you to both bind using <Return> but also use the "run" button
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def thermovoltage_scan(self, event=None):
        self.fetch(event)
        run = ThermovoltageScan(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                int(self._inputs['scan']), float(self._inputs['gain']), int(self._inputs['x pixel density']),
                                int(self._inputs['y pixel density']), int(self._inputs['x range']),
                                int(self._inputs['y range']), int(self._inputs['x center']), int(self._inputs['y center']),
                                float(self._inputs['polarization']), self._npc3sg_x, self._npc3sg_y, self._npc3sg_input,
                                self._sr7270_top, self._sr7270_bottom, self._powermeter)
        run.main()

    def heating_scan(self, event=None):
        self.fetch(event)
        run = HeatingScan(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                          int(self._inputs['scan']), float(self._inputs['gain']), float(self._inputs['bias (mV)']),
                          float(self._inputs['oscillator amplitude (mV)']), int(self._inputs['x pixel density']),
                          int(self._inputs['y pixel density']), int(self._inputs['x range']),
                          int(self._inputs['y range']), int(self._inputs['x center']), int(self._inputs['y center']),
                          float(self._inputs['polarization']), self._npc3sg_x, self._npc3sg_y, self._npc3sg_input,
                          self._sr7270_top, self._sr7270_bottom, self._powermeter)
        run.main()

    def thermovoltage_time(self, event=None):
        self.fetch(event)
        run = ThermovoltageTime(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                int(self._inputs['scan']), float(self._inputs['gain']),
                                float(self._inputs['rate (per second)']), float(self._inputs['max time (s)']),
                                float(self._inputs['polarization']), self._npc3sg_input, self._sr7270_bottom,
                                self._powermeter)
        run.main()

    def step(self, direction):
        self.fetch()
        self._attenuatorwheel.step(int(self._inputs['steps']), direction=direction)
        self.power()

    def power(self):
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, self._powermeter.read_power() * 1000)
        self._textbox.pack()

    def changepolarization(self):
        self.fetch()
        self._polarizer.move_nearest(float(float(self._inputs['desired polarization']) / 2))
        self.readpolarization()

    def readpolarization(self):
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, self._polarizer.read_position() * 2)
        self._textbox.pack()
        self._textbox2.delete(1.0, tk.END)
        self._textbox2.insert(tk.END, (self._polarizer.read_position() % 180) * 2)
        self._textbox2.pack()

    def homepolarizer(self):
        self._polarizer.home()

    def thermovoltage_intensity(self, event=None):
        self.fetch(event)
        run = ThermovoltageIntensity(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                     int(self._inputs['scan']), float(self._inputs['gain']),
                                     float(self._inputs['max time (s)']), float(self._inputs['polarization']),
                                     int(self._inputs['steps']), self._npc3sg_input, self._sr7270_top, self._sr7270_bottom,
                                     self._powermeter, self._attenuatorwheel)
        run.main()

    def thermovoltage_polarization(self, event=None):
        self.fetch(event)
        run = ThermovoltagePolarization(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                        int(self._inputs['scan']), float(self._inputs['gain']), self._npc3sg_input,
                                        self._sr7270_bottom, self._powermeter, self._polarizer)
        run.main()

    def onclick_browse(self):
        self._filepath.set(tkinter.filedialog.askdirectory())

    def build_thermovoltage_scan_gui(self):
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_scan)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_scan)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_heating_scan_gui(self):
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.heating_scan)
        b1 = tk.Button(self._master, text='Run', command=self.heating_scan)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_time_gui(self):
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_time)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_time)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_change_intensity_gui(self):
        self.makeform()
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text='Power (mW)', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox = tk.Text(row, height=1, width=10)
        self._textbox.insert(tk.END, str('None'))
        self._textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        b1 = tk.Button(self._master, text='Forward', command=lambda: self.step(True))
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Backward', command=lambda: self.step(False))
        b2.pack(side=tk.LEFT, padx=5, pady=5)
        b3 = tk.Button(self._master, text='Read power', command=self.power)
        b3.pack(side=tk.LEFT, padx=5, pady=5)
        b4 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b4.pack(side=tk.LEFT, padx=5, pady=5)

    def build_change_polarization_gui(self):
        self.makeform()
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text='current polarization', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox = tk.Text(row, height=1, width=10)
        self._textbox.insert(tk.END, self._polarizer.read_position() * 2)
        self._textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text='modulus polarization', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox2 = tk.Text(row, height=1, width=10)
        self._textbox2.insert(tk.END, (self._polarizer.read_position() % 90) * 2)
        self._textbox2.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        b1 = tk.Button(self._master, text='Change polarization', command=self.changepolarization)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Read polarization', command=self.readpolarization)
        b2.pack(side=tk.LEFT, padx=5, pady=5)
        b4 = tk.Button(self._master, text='Home', command=self.homepolarizer)
        b4.pack(side=tk.LEFT, padx=5, pady=5)
        b3 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b3.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_intensity_gui(self):
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_intensity)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_intensity)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_polarization_gui(self):
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_polarization)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_polarization)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)



