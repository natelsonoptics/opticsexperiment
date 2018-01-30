#!/usr/bin/python3

import tkinter as tk
import tkinter.filedialog
from optics.thermovoltage_measurement.thermovoltage_scan import ThermovoltageScan
from optics.heating_measurement.heating_scan import HeatingScan
from optics.thermovoltage_measurement.thermovoltage_time import ThermvolageTime


class SetupGUI:
    def __init__(self, master, caption, fields, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_top=None, sr7270_bottom=None):
        self.master = master
        self.master.title(caption)
        self.fields = fields
        self.entries = []
        self.inputs = {}
        self.filepath = tk.StringVar()  # this is a global variable - this needs to change
        self.filepath.set(self.fields['file path'])
        self.label = tk.Label(master, text=caption)
        self.label.pack()
        self.browse_button = tk.Button(self.master, text="Browse", command=self.onclick_browse)
        self.npc3sg_x = npc3sg_x
        self.npc3sg_y = npc3sg_y
        self.npc3sg_input = npc3sg_input
        self.sr7270_top = sr7270_top
        self.sr7270_bottom = sr7270_bottom

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

    def fetch(self, event=None):
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
                                self.sr7270_top, self.sr7270_bottom)
        run.main()

    def heating_scan(self, event=None):
        self.fetch(event)
        run = HeatingScan(self.inputs['file path'], self.inputs['notes'], self.inputs['device'],
                          int(self.inputs['scan']), float(self.inputs['gain']), float(self.inputs['bias (mV)']),
                          float(self.inputs['oscillator amplitude (mV)']), int(self.inputs['x pixel density']),
                          int(self.inputs['y pixel density']), int(self.inputs['x range']),
                          int(self.inputs['y range']), int(self.inputs['x center']), int(self.inputs['y center']),
                          float(self.inputs['polarization']), self.npc3sg_x, self.npc3sg_y, self.npc3sg_input,
                          self.sr7270_top, self.sr7270_bottom)
        run.main()

    def thermovoltage_time(self, event=None):
        self.fetch(event)
        run = ThermvolageTime(self.inputs['file path'], self.inputs['notes'], self.inputs['device'],
                              int(self.inputs['scan']), float(self.input['gain']),
                              float(self.input['rate (per second) Default = None']), float(self.input['max time (s)']),
                              float(self.input['polarization']), self.npc3sg_input, self.sr7270_bottom)
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



