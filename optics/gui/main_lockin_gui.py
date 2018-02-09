import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
import tkinter.filedialog
import numpy as np
from optics.hardware_control import attenuator_wheel, pm100d, hardware_addresses_and_constants, sr7270, npc3sg_analog, \
    polarizercontroller, daq
from optics.heating_measurement.heating_map import HeatingScan
from optics.thermovoltage_measurement.thermovoltage_intensity import ThermovoltageIntensity
from optics.thermovoltage_measurement.thermovoltage_polarization import ThermovoltagePolarization
from optics.thermovoltage_measurement.thermovoltage_map import ThermovoltageScan
from optics.thermovoltage_measurement.thermovoltage_time import ThermovoltageTime
from optics.heating_measurement.heating_time import HeatingTime
from optics.heating_measurement.heating_intensity import HeatingIntensity
from optics.heating_measurement.heating_polarization import HeatingPolarization
from optics.thermovoltage_measurement.thermovoltage_map_dc import ThermovoltageScanDC

class BaseGUI:
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_top=None, sr7270_bottom=None, powermeter=None, attenuatorwheel=None, polarizer=None,
                 daq_input=None):
        self._master = master
        self._master.title('Optics setup measurements')
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_top = sr7270_top
        self._sr7270_bottom = sr7270_bottom
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._polarizer = polarizer
        self._daq_input = daq_input
        self._newWindow = None
        self._app = None

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)
        self._app = LockinMeasurementGUI(self._newWindow, npc3sg_x=self._npc3sg_x, npc3sg_y=self._npc3sg_y,
                                         npc3sg_input=self._npc3sg_input, sr7270_top=self._sr7270_top,
                                         sr7270_bottom=self._sr7270_bottom, powermeter=self._powermeter,
                                         attenuatorwheel=self._attenuatorwheel, polarizer=self._polarizer,
                                         daq_input=self._daq_input)
        measurement = {'heatmap': self._app.build_heating_scan_gui,
                       'ptemap': self._app.build_thermovoltage_scan_gui,
                       'ptemapdc': self._app.build_thermovoltage_scan_dc_gui,
                       'heatpolarization': self._app.build_heating_polarization_gui,
                       'ptepolarization': self._app.build_thermovoltage_polarization_gui,
                       'heatintensity': self._app.build_heating_intensity_gui,
                       'pteintensity': self._app.build_thermovoltage_intensity_gui,
                       'heattime': self._app.build_heating_time_gui,
                       'ptetime': self._app.build_thermovoltage_time_gui,
                       'position': self._app.build_change_position_gui,
                       'intensity': self._app.build_change_intensity_gui,
                       'polarization': self._app.build_change_polarization_gui}
        measurement[measurementtype]()

    def build(self):
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='map scans', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b1 = tk.Button(row, text='thermovoltage',
                       command=lambda measurementtype='ptemap': self.new_window(measurementtype))
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b2 = tk.Button(row, text='heating',
                       command=lambda measurementtype='heatmap': self.new_window(measurementtype))
        b2.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='DC map scans', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b13 = tk.Button(row, text='thermovoltage',
                       command=lambda measurementtype='ptemapdc': self.new_window(measurementtype))
        b13.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='polarization scans', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b3 = tk.Button(row, text='thermovoltage',
                       command=lambda measurementtype='ptepolarization': self.new_window(measurementtype))
        b3.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b4 = tk.Button(row, text='heating',
                       command=lambda measurementtype='heatpolarization': self.new_window(measurementtype))
        b4.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='intensity scans', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b5 = tk.Button(row, text='thermovoltage',
                       command=lambda measurementtype='pteintensity': self.new_window(measurementtype))
        b5.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b6 = tk.Button(row, text='heating',
                       command=lambda measurementtype='heatintensity': self.new_window(measurementtype))
        b6.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='time scans', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b7 = tk.Button(row, text='thermovoltage',
                       command=lambda measurementtype='ptetime': self.new_window(measurementtype))
        b7.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b8 = tk.Button(row, text='heating',
                       command=lambda measurementtype='heattime': self.new_window(measurementtype))
        b8.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='change parameters', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b9 = tk.Button(row, text='position',
                       command=lambda measurementtype='position': self.new_window(measurementtype))
        b9.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b10 = tk.Button(row, text='intensity',
                       command=lambda measurementtype='intensity': self.new_window(measurementtype))
        b10.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        b11 = tk.Button(row, text='polarization',
                       command=lambda measurementtype='polarization': self.new_window(measurementtype))
        b11.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        b12 = tk.Button(self._master, text='Quit all windows', command=self._master.quit)
        b12.pack()


class LockinMeasurementGUI:
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_top=None, sr7270_bottom=None, powermeter=None, attenuatorwheel=None, polarizer=None,
                 daq_input=None):
        self._master = master
        self._fields = {}
        self._entries = []
        self._inputs = {}
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
        self._filepath = tk.StringVar()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._daq_input = daq_input

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
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def thermovoltage_scan(self, event=None):
        self.fetch(event)
        run = ThermovoltageScan(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                int(self._inputs['scan']), float(self._inputs['gain']),
                                int(self._inputs['x pixel density']), int(self._inputs['y pixel density']),
                                int(self._inputs['x range']), int(self._inputs['y range']),
                                int(self._inputs['x center']), int(self._inputs['y center']), self._npc3sg_x,
                                self._npc3sg_y, self._npc3sg_input, self._sr7270_top, self._sr7270_bottom,
                                self._powermeter, self._polarizer)
        run.main()

    def thermovoltage_scan_dc(self, event=None):
        self.fetch(event)
        run = ThermovoltageScanDC(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                  int(self._inputs['scan']), float(self._inputs['gain']),
                                  int(self._inputs['x pixel density']),
                                  int(self._inputs['y pixel density']), int(self._inputs['x range']),
                                  int(self._inputs['y range']), int(self._inputs['x center']),
                                  int(self._inputs['y center']), self._npc3sg_x, self._npc3sg_y, self._daq_input,
                                  self._powermeter, self._polarizer)
        run.main()

    def heating_scan(self, event=None):
        self.fetch(event)
        run = HeatingScan(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                          int(self._inputs['scan']), float(self._inputs['gain']), float(self._inputs['bias (mV)']),
                          float(self._inputs['oscillator amplitude (mV)']), int(self._inputs['x pixel density']),
                          int(self._inputs['y pixel density']), int(self._inputs['x range']),
                          int(self._inputs['y range']), int(self._inputs['x center']), int(self._inputs['y center']),
                          self._npc3sg_x, self._npc3sg_y, self._npc3sg_input,
                          self._sr7270_top, self._sr7270_bottom, self._powermeter, self._polarizer)
        run.main()

    def thermovoltage_time(self, event=None):
        self.fetch(event)
        run = ThermovoltageTime(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                int(self._inputs['scan']), float(self._inputs['gain']),
                                float(self._inputs['rate (per second)']), float(self._inputs['max time (s)']),
                                self._npc3sg_input, self._sr7270_bottom,
                                self._powermeter, self._polarizer)
        run.main()

    def heating_time(self, event=None):
        self.fetch(event)
        run = HeatingTime(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                          int(self._inputs['scan']), float(self._inputs['gain']),
                          float(self._inputs['rate (per second)']), float(self._inputs['max time (s)']),
                          float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                          self._npc3sg_input, self._sr7270_top, self._sr7270_bottom, self._powermeter, self._polarizer)
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
        self._textbox.insert(tk.END, self._polarizer.read_polarization())
        self._textbox.pack()
        self._textbox2.delete(1.0, tk.END)
        self._textbox2.insert(tk.END, (self._polarizer.read_waveplate_position() % 180) * 2)
        self._textbox2.pack()

    def homepolarizer(self):
        self._polarizer.home()

    def thermovoltage_intensity(self, event=None):
        self.fetch(event)
        run = ThermovoltageIntensity(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                     int(self._inputs['scan']), float(self._inputs['gain']),
                                     float(self._inputs['max time (s)']),
                                     int(self._inputs['steps']), self._npc3sg_input, self._sr7270_top, self._sr7270_bottom,
                                     self._powermeter, self._attenuatorwheel, self._polarizer)
        run.main()

    def heating_intensity(self, event=None):
        self.fetch(event)
        run = HeatingIntensity(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                               int(self._inputs['scan']), float(self._inputs['gain']), float(self._inputs['bias (mV)']),
                               float(self._inputs['oscillator amplitude (mV)']), float(self._inputs['max time (s)']),
                               int(self._inputs['steps']), self._npc3sg_input, self._sr7270_top, self._sr7270_bottom,
                               self._powermeter, self._attenuatorwheel, self._polarizer)
        run.main()

    def thermovoltage_polarization(self, event=None):
        self.fetch(event)
        run = ThermovoltagePolarization(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                        int(self._inputs['scan']), float(self._inputs['gain']), self._npc3sg_input,
                                        self._sr7270_bottom, self._powermeter, self._polarizer)
        run.main()

    def heating_polarization(self, event=None):
        self.fetch(event)
        run = HeatingPolarization(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                  int(self._inputs['scan']), float(self._inputs['gain']),
                                  float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                                  self._npc3sg_input, self._sr7270_top, self._sr7270_bottom, self._powermeter,
                                  self._polarizer)
        run.main()

    def changeposition(self, event=None):
        self.fetch(event)
        self._npc3sg_x.move(int(self._inputs['x']))
        self._npc3sg_y.move(int(self._inputs['y']))
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def onclick_browse(self):
        self._filepath.set(tkinter.filedialog.askdirectory())

    def build_thermovoltage_scan_gui(self):
        caption = "Thermovoltage map scan"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000,
                        'x pixel density': 15, 'y pixel density': 15, 'x range': 160, 'y range': 160, 'x center': 80,
                        'y center': 80}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_scan)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_scan)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_scan_dc_gui(self):
        caption = "DC thermovoltage map scan"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000, 'x pixel density': 15,
                        'y pixel density': 15, 'x range': 160, 'y range': 160, 'x center': 80, 'y center': 80}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_scan_dc)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_scan_dc)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_heating_scan_gui(self):
        caption = "Heating map scan"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000,
                        'x pixel density': 15, 'y pixel density': 15, 'x range': 160, 'y range': 160, 'x center': 80,
                        'y center': 80, 'bias (mV)': 5, 'oscillator amplitude (mV)': 7}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.heating_scan)
        b1 = tk.Button(self._master, text='Run', command=self.heating_scan)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_time_gui(self):
        caption = "Thermovoltage vs. time"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000,
                        'rate (per second)': 3, 'max time (s)': 600}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_time)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_time)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_change_intensity_gui(self):
        caption = "Change laser intensity"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'steps': 10}
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
        b4 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b4.pack(side=tk.LEFT, padx=5, pady=5)

    def build_change_polarization_gui(self):
        caption = "Change laser polarization"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'desired polarization': 90}
        self.makeform()
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='current polarization', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox = tk.Text(row, height=1, width=10)
        self._textbox.insert(tk.END, self._polarizer.read_polarization())
        self._textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='modulus polarization', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox2 = tk.Text(row, height=1, width=10)
        self._textbox2.insert(tk.END, (self._polarizer.read_waveplate_position() % 90) * 2)
        self._textbox2.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        b1 = tk.Button(self._master, text='Change polarization', command=self.changepolarization)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Read polarization', command=self.readpolarization)
        b2.pack(side=tk.LEFT, padx=5, pady=5)
        b4 = tk.Button(self._master, text='Home', command=self.homepolarizer)
        b4.pack(side=tk.LEFT, padx=5, pady=5)
        b3 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b3.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_intensity_gui(self):
        caption = "Thermovoltage vs. laser intensity"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000,
                        'steps': 2, 'max time (s)': 600}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_intensity)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_intensity)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_thermovoltage_polarization_gui(self):
        caption = "Thermovoltage vs. polarization"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_polarization)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_polarization)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_heating_polarization_gui(self):
       caption = "Heating vs. polarization"
       self._master.title(caption)
       label = tk.Label(self._master, text=caption)
       label.pack()
       self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000, 'bias (mV)': 5,
                       'oscillator amplitude (mV)': 7}
       self._browse_button.pack()
       self.makeform()
       self._master.bind('<Return>', self.heating_polarization)
       b1 = tk.Button(self._master, text='Run', command=self.heating_polarization)
       b1.pack(side=tk.LEFT, padx=5, pady=5)
       b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
       b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_change_position_gui(self):
        caption = "Change laser position"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'x': 80, 'y': 80}
        self.makeform()
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text='Current Position', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox = tk.Text(row, height=1, width=10)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        b1 = tk.Button(self._master, text='Change Position', command=self.changeposition)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_heating_time_gui(self):
        caption = "Heating vs. time"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000,
                        'rate (per second)': 3, 'max time (s)': 600, 'bias (mV)': 5, 'oscillator amplitude (mV)': 7}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.heating_time)
        b1 = tk.Button(self._master, text='Run', command=self.heating_time)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_heating_intensity_gui(self):
        caption = "Heating vs. intensity"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000, 'steps': 2,
                        'rate (per second)': 3, 'max time (s)': 600, 'bias (mV)': 5, 'oscillator amplitude (mV)': 7}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.heating_intensity)
        b1 = tk.Button(self._master, text='Run', command=self.heating_intensity)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

    def build_coming_soon(self):
        caption = "Coming soon"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)


def main():
    with npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) \
                    as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) \
                    as (sr7270_top, sr7270_bottom), \
            pm100d.connect(hardware_addresses_and_constants.pm100d_address) as powermeter, \
            polarizercontroller.connect_kdc101(hardware_addresses_and_constants.kdc101_serial_number) as polarizer, \
            attenuator_wheel.create_do_task(hardware_addresses_and_constants.attenuator_wheel_outputs) as \
                    attenuatorwheel, daq.create_ai_task(hardware_addresses_and_constants.ai_dc1,
                                                        hardware_addresses_and_constants.ai_dc2) as daq_input:
        root = tk.Tk()
        app = BaseGUI(root, npc3sg_x=npc3sg_x, npc3sg_y=npc3sg_y, npc3sg_input=npc3sg_input,
                      sr7270_top=sr7270_top, sr7270_bottom=sr7270_bottom, powermeter=powermeter,
                      attenuatorwheel=attenuatorwheel, polarizer=polarizer, daq_input=daq_input)
        app.build()
        root.mainloop()

if __name__ == '__main__':
    main()