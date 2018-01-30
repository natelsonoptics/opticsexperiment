#!/usr/bin/python3

import tkinter as tk
import tkinter.filedialog

from optics.hardware_control.change_intensity import ChangeIntensity
from optics.heating_measurement.heating_scan import HeatingScan
from optics.thermovoltage_measurement.thermovoltage_intensity import ThermovoltageIntensity
from optics.thermovoltage_measurement.thermovoltage_scan import ThermovoltageScan
from optics.thermovoltage_measurement.thermovoltage_time import ThermovoltageTime


class SetupGUI:
    def __init__(self, master, caption, fields, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_top=None, sr7270_bottom=None, powermeter=None, attenuatorwheel=None):
        self.master = master
        self.master.title(caption)
        self.fields = fields
        self.entries = []
        self.inputs = {}
        self.filepath = tk.StringVar()  # this is a global variable - this needs to change
        if 'file path' in self.fields:
            self.filepath.set(self.fields['file path'])
        self.label = tk.Label(master, text=caption)
        self.label.pack()
        self.browse_button = tk.Button(self.master, text="Browse", command=self.onclick_browse)
        self.npc3sg_x = npc3sg_x
        self.npc3sg_y = npc3sg_y
        self.npc3sg_input = npc3sg_input
        self.sr7270_top = sr7270_top
        self.sr7270_bottom = sr7270_bottom
        self.powermeter = powermeter
        self.attenuatorwheel = attenuatorwheel
        self.textbox = None

    def makeform(self):
        for key in self.fields:
            row = tk.Frame(self.master)
            lab = tk.Label(row, width=15, text=key, anchor='w')
            if key == 'file path':
                ent = tk.Entry(row, textvariable=self.filepath)
            else:
                ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            ent.insert(0, str(self.fields[key]))
            self.entries.append((key, ent))
        return self.entries

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        # You need to have "event" input even though it isn't used as an input. If this method was only fetch(self), it
        # only expects one input parameter, which would be fine except you also pass self.fetch to self.master.bind when
        # binding the <Return> key, which means that self.fetch('<Return>') is being called, which is TWO inputs due to
        # 'self'. This event=None allows you to both bind using <Return> but also use the "run" button
        for entry in self.entries:
            field = entry[0]
            text = entry[1].get()
            self.inputs[field] = text

    def thermovoltage_scan(self, event=None):
        self.fetch(event)
        run = ThermovoltageScan(self.inputs['file path'], self.inputs['notes'], self.inputs['device'],
                                int(self.inputs['scan']), float(self.inputs['gain']), int(self.inputs['x pixel density']),
                                int(self.inputs['y pixel density']), int(self.inputs['x range']),
                                int(self.inputs['y range']), int(self.inputs['x center']), int(self.inputs['y center']),
                                float(self.inputs['polarization']), self.npc3sg_x, self.npc3sg_y, self.npc3sg_input,
                                self.sr7270_top, self.sr7270_bottom, self.powermeter)
        run.main()

    def heating_scan(self, event=None):
        self.fetch(event)
        run = HeatingScan(self.inputs['file path'], self.inputs['notes'], self.inputs['device'],
                          int(self.inputs['scan']), float(self.inputs['gain']), float(self.inputs['bias (mV)']),
                          float(self.inputs['oscillator amplitude (mV)']), int(self.inputs['x pixel density']),
                          int(self.inputs['y pixel density']), int(self.inputs['x range']),
                          int(self.inputs['y range']), int(self.inputs['x center']), int(self.inputs['y center']),
                          float(self.inputs['polarization']), self.npc3sg_x, self.npc3sg_y, self.npc3sg_input,
                          self.sr7270_top, self.sr7270_bottom, self.powermeter)
        run.main()

    def thermovoltage_time(self, event=None):
        self.fetch(event)
        run = ThermovoltageTime(self.inputs['file path'], self.inputs['notes'], self.inputs['device'],
                                int(self.inputs['scan']), float(self.inputs['gain']),
                                float(self.inputs['rate (per second)']), float(self.inputs['max time (s)']),
                                float(self.inputs['polarization']), self.npc3sg_input, self.sr7270_bottom,
                                self.powermeter)
        run.main()

    def step(self, direction):
        self.fetch()
        run = ChangeIntensity(self.attenuatorwheel, self.powermeter)
        run.step(int(self.inputs['steps']), direction=direction)
        self.power()

    def power(self):
        self.textbox.delete(1.0, tk.END)
        run = ChangeIntensity(self.attenuatorwheel, self.powermeter)
        self.textbox.insert(tk.END, run.read_power()*1000)
        self.textbox.pack()

    def thermovoltage_intensity(self, event=None):
        self.fetch(event)
        run = ThermovoltageIntensity(self.inputs['file path'], self.inputs['notes'], self.inputs['device'],
                                     int(self.inputs['scan']), float(self.inputs['gain']),
                                     float(self.inputs['max time (s)']), float(self.inputs['polarization']),
                                     int(self.inputs['steps']), self.npc3sg_input, self.sr7270_top, self.sr7270_bottom,
                                     self.powermeter, self.attenuatorwheel)
        run.main()

    def onclick_browse(self):
        self.filepath.set(tkinter.filedialog.askdirectory())

    def build_thermovoltage_scan_gui(self):
        self.browse_button.pack()
        self.makeform()
        self.master.bind('<Return>', self.thermovoltage_scan)
        b1 = tk.Button(self.master, text='Run', command=self.thermovoltage_scan)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.master, text='Quit', command=self.master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_heating_scan_gui(self):
        self.browse_button.pack()
        self.makeform()
        self.master.bind('<Return>', self.heating_scan)
        b1 = tk.Button(self.master, text='Run', command=self.heating_scan)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.master, text='Quit', command=self.master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_time_gui(self):
        self.browse_button.pack()
        self.makeform()
        self.master.bind('<Return>', self.thermovoltage_time)
        b1 = tk.Button(self.master, text='Run', command=self.thermovoltage_time)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.master, text='Quit', command=self.master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_intensity_gui(self):
        self.makeform()
        row = tk.Frame(self.master)
        lab = tk.Label(row, width=15, text='Power (mW)', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self.textbox = tk.Text(row, height=1, width=10)
        self.textbox.insert(tk.END, str('None'))
        self.textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        b1 = tk.Button(self.master, text='Forward', command=lambda: self.step(True))
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.master, text='Backward', command=lambda: self.step(False))
        b2.pack(side=tk.LEFT, padx=5, pady=5)
        b3 = tk.Button(self.master, text='Read power', command=self.power)
        b3.pack(side=tk.LEFT, padx=5, pady=5)
        b4 = tk.Button(self.master, text='Quit', command=self.master.quit)
        b4.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_intensity_gui(self):
        self.browse_button.pack()
        self.makeform()
        self.master.bind('<Return>', self.thermovoltage_intensity)
        b1 = tk.Button(self.master, text='Run', command=self.thermovoltage_intensity)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.master, text='Quit', command=self.master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)



