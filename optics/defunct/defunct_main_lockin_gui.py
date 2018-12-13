import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
import tkinter.filedialog
import numpy as np
from optics.hardware_control import attenuator_wheel, pm100d, sr7270, npc3sg, polarizercontroller, daq
import optics.hardware_control.hardware_addresses_and_constants as hw
from optics.heating_measurement.heating_map import HeatingScan
from optics.thermovoltage_measurement.thermovoltage_intensity import ThermovoltageIntensity
from optics.thermovoltage_measurement.thermovoltage_polarization import ThermovoltagePolarization
from optics.thermovoltage_measurement.thermovoltage_map import ThermovoltageScan
from optics.thermovoltage_measurement.thermovoltage_time import ThermovoltageTime
from optics.heating_measurement.heating_time import HeatingTime
from optics.heating_measurement.heating_intensity import HeatingIntensity
from optics.heating_measurement.heating_polarization import HeatingPolarization
from optics.thermovoltage_measurement.thermovoltage_map_dc import ThermovoltageScanDC
from optics.thermovoltage_measurement.thermovoltage_polarization_dc import ThermovoltagePolarizationDC
from contextlib import ExitStack
from optics.current_vs_voltage.current_vs_voltage import CurrentVoltageSweep
from optics.electromigrate.daq_break import DAQBreak
import datetime
import csv
import os
from os import path


class BaseLockinGUI:
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_dual_harmonic=None, sr7270_single_reference=None, powermeter=None, attenuatorwheel=None, waveplate=None,
                 daq_input=None, daq_switch_ai=None, daq_switch_ao=None):
        self._master = master
        self._master.title('Optics setup measurements')
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._waveplate = waveplate
        self._daq_input = daq_input
        self._daq_switch_ai = daq_switch_ai
        self._daq_switch_ao = daq_switch_ao
        self._newWindow = None
        self._app = None

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)
        self._app = LockinMeasurementGUI(self._newWindow, npc3sg_x=self._npc3sg_x, npc3sg_y=self._npc3sg_y,
                                         npc3sg_input=self._npc3sg_input,
                                         sr7270_dual_harmonic=self._sr7270_dual_harmonic,
                                         sr7270_single_reference=self._sr7270_single_reference,
                                         powermeter=self._powermeter, attenuatorwheel=self._attenuatorwheel,
                                         waveplate=self._waveplate, daq_input=self._daq_input, daq_switch_ai=self._daq_switch_ai,
                                         daq_switch_ao=self._daq_switch_ao)
        measurement = {'heatmap': self._app.build_heating_scan_gui,
                       'ptemap': self._app.build_thermovoltage_scan_gui,
                       'ptemapdc': self._app.build_thermovoltage_scan_dc_gui,
                       'ptepolarizationdc': self._app.build_thermovoltage_polarization_dc_gui,
                       'heatpolarization': self._app.build_heating_polarization_gui,
                       'ptepolarization': self._app.build_thermovoltage_polarization_gui,
                       'heatintensity': self._app.build_heating_intensity_gui,
                       'pteintensity': self._app.build_thermovoltage_intensity_gui,
                       'heattime': self._app.build_heating_time_gui,
                       'ptetime': self._app.build_thermovoltage_time_gui,
                       'position': self._app.build_change_position_gui,
                       'intensity': self._app.build_change_intensity_gui,
                       'polarization': self._app.build_change_polarization_gui,
                       'ivsweep': self._app.build_sweep_iv_gui,
                       'singlereference': self._app.build_single_reference_gui,
                       'dualharmonic': self._app.build_dual_harmonic_gui,
                       'electromigrate': self._app.build_daqbreak_gui,
                       'measureresistance': self._app.build_measure_resistance_gui}
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
        row = self.makerow('map scans')
        self.make_measurement_button(row, 'thermovoltage', 'ptemap')
        self.make_measurement_button(row, 'heating', 'heatmap')
        row = self.makerow('DC map scans')
        self.make_measurement_button(row, 'thermovoltage map', 'ptemapdc')
        self.make_measurement_button(row, 'pte polarization', 'ptepolarizationdc')
        row = self.makerow('I-V curves')
        self.make_measurement_button(row, 'current', 'ivsweep')
        row = self.makerow('polarization scans')
        self.make_measurement_button(row, 'thermovoltage', 'ptepolarization')
        self.make_measurement_button(row, 'heating', 'heatpolarization')
        row = self.makerow('intensity scans')
        self.make_measurement_button(row, 'thermovoltage', 'pteintensity')
        self.make_measurement_button(row, 'heating', 'heatintensity')
        row = self.makerow('time scans')
        self.make_measurement_button(row, 'thermovoltage', 'ptetime')
        self.make_measurement_button(row, 'heating', 'heattime')
        row = self.makerow('electromigrate')
        self.make_measurement_button(row, 'DAQ break', 'electromigrate')
        row = self.makerow('change parameters')
        self.make_measurement_button(row, 'position', 'position')
        self.make_measurement_button(row, 'intensity', 'intensity')
        self.make_measurement_button(row, 'polarization', 'polarization')
        row = self.makerow('measure resistance')
        self.make_measurement_button(row, 'lock in', 'measureresistance')
        row = self.makerow('single reference lock in')
        b1 = tk.Button(row, text='auto phase',
                       command=lambda lockin=self._sr7270_single_reference: self.autophase(lockin))
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        self.make_measurement_button(row, 'change parameters', 'singlereference')
        row = self.makerow('dual harmonic lock in')
        b1 = tk.Button(row, text='auto phase',
                       command=lambda lockin=self._sr7270_dual_harmonic: self.autophase(lockin))
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)
        self.make_measurement_button(row, 'change parameters', 'dualharmonic')
        b12 = tk.Button(self._master, text='Quit all windows', command=self._master.quit)
        b12.pack()

    def autophase(self, lockin, event=None):
        lockin.auto_phase()

class LockinMeasurementGUI:
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_dual_harmonic=None, sr7270_single_reference=None, powermeter=None, attenuatorwheel=None, waveplate=None,
                 daq_input=None, daq_switch_ai=None, daq_switch_ao=None):
        self._master = master
        self._fields = {}
        self._entries = []
        self._inputs = {}
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._daq_switch_ai = daq_switch_ai
        self._daq_switch_ao = daq_switch_ao
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._waveplate = waveplate
        self._textbox = None
        self._textbox2 = None
        self._filepath = tk.StringVar()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._daq_input = daq_input
        self._direction = tk.StringVar()
        self._direction.set('Forward')
        self._axis = tk.StringVar()
        self._axis.set('y')
        self._current_gain = tk.StringVar()
        self._current_amplifier_gain_options = {'1 mA/V': 1e3, '500 uA/V': 2e3,'200 uA/V': 5e3,
                                                '100 uA/V': 1e4, '50 uA/V': 2e4,'20 uA/V': 5e4,
                                                '10 uA/V': 1e5, '5 uA/V': 2e5,'2 uA/V': 5e5,
                                                '1 uA/V': 1e6, '500 nA/V': 2e6,'200 nA/V': 5e6,
                                                '100 nA/V': 1e7, '50 nA/V': 2e7,'20 nA/V': 5e7,
                                                '10 nA/V': 1e8, '5 nA/V': 2e8,'2 nA/V': 5e8,
                                                '1 nA/V': 1e9, '500 pA/V': 2e9,'200 pA/V': 5e9,
                                                '100 pA/V': 1e10, '50 pA/V': 2e10,'20 pA/V': 5e10,
                                                '10 pA/V': 1e11, '5 pA/V': 2e11,'2 pA/V': 5e11,
                                                '1 pA/V': 1e12}
        self._current_gain.set('1 mA/V')
        self._voltage_gain = tk.StringVar()
        self._voltage_gain.set(1000)
        self._tc = tk.StringVar()
        self._sen = tk.StringVar()
        self._tc1 = tk.StringVar()
        self._tc2 = tk.StringVar()
        self._sen1 = tk.StringVar()
        self._sen2 = tk.StringVar()
        self._abort = tk.StringVar()
        self._increase = tk.StringVar()

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

    def makebutton(self, caption, run_command, master=None):
        if not master:
            master = self._master
        b1 = tk.Button(master, text=caption, command=run_command)
        b1.pack(side=tk.LEFT, padx=5, pady=5)

    def maketextbox(self, title, displaytext):
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text=title, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox = tk.Text(row, height=1, width=10)
        self._textbox.insert(tk.END, displaytext)
        self._textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def make_option_menu(self, label, parameter, option_list):
        row = tk.Frame(self._master)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text=label, anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, parameter, *option_list)
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def maketextbox2(self, title, displaytext):  # TODO fix this
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text=title, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox2 = tk.Text(row, height=1, width=10)
        self._textbox2.insert(tk.END, displaytext)
        self._textbox2.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def electromigrate(self, event=None):
        self.fetch(event)
        if self._abort.get() == 'True':
            abort = True
        else:
            abort = False
        if self._increase.get() == 'True':
            increase = True
        else:
            increase = False

        run = DAQBreak(tk.Toplevel(self._master), self._daq_switch_ao, self._daq_switch_ai, self._inputs['file path'],
                       self._inputs['device'], steps=int(self._inputs['steps']),
                       stop_voltage=float(self._inputs['stop voltage (resistance measurement)']),
                       desired_resistance=float(self._inputs['desired resistance']),
                       break_voltage=float(self._inputs['break voltage']), passes=float(self._inputs['passes']),
                       increase_break_voltage=increase, delta_break_voltage=float(self._inputs['delta break voltage']),
                       start_voltage=float(self._inputs['start voltage']),
                       delta_voltage=float(self._inputs['delta voltage']),
                       current_drop=float(self._inputs['current drop']), abort=abort,
                       gain=float(self._current_amplifier_gain_options[self._current_gain.get()]))
        run.main()

    def thermovoltage_scan(self, event=None):
        self.fetch(event)
        if self._direction.get() == 'Reverse':
            direction = False
        else:
            direction = True
        run = ThermovoltageScan(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                int(self._inputs['scan']), float(self._voltage_gain.get()),
                                int(self._inputs['x pixel density']), int(self._inputs['y pixel density']),
                                int(self._inputs['x range']), int(self._inputs['y range']),
                                int(self._inputs['x center']), int(self._inputs['y center']), self._npc3sg_x,
                                self._npc3sg_y, self._npc3sg_input, self._sr7270_single_reference, self._powermeter,
                                self._waveplate, direction, self._axis.get())
        run.main()

    def thermovoltage_scan_dc(self, event=None):
        self.fetch(event)
        if self._direction.get() == 'Reverse':
            direction = False
        else:
            direction = True
        run = ThermovoltageScanDC(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                  int(self._inputs['scan']), float(self._voltage_gain.get()),
                                  int(self._inputs['x pixel density']),
                                  int(self._inputs['y pixel density']), int(self._inputs['x range']),
                                  int(self._inputs['y range']), int(self._inputs['x center']),
                                  int(self._inputs['y center']), self._npc3sg_x, self._npc3sg_y, self._daq_input,
                                  self._powermeter, self._waveplate, direction)
        run.main()

    def heating_scan(self, event=None):
        self.fetch(event)
        if self._direction.get() == 'Reverse':
            direction = False
        else:
            direction = True
        run = HeatingScan(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                          int(self._inputs['scan']),
                          float(self._current_amplifier_gain_options[self._current_gain.get()]),
                          float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                          int(self._inputs['x pixel density']), int(self._inputs['y pixel density']),
                          int(self._inputs['x range']), int(self._inputs['y range']), int(self._inputs['x center']),
                          int(self._inputs['y center']), self._npc3sg_x, self._npc3sg_y, self._npc3sg_input,
                          self._sr7270_dual_harmonic, self._sr7270_single_reference, self._powermeter, self._waveplate,
                          direction)
        run.main()

    def thermovoltage_time(self, event=None):
        self.fetch(event)
        run = ThermovoltageTime(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                int(self._inputs['scan']), float(self._voltage_gain.get()),
                                float(self._inputs['rate (per second)']), float(self._inputs['max time (s)']),
                                self._npc3sg_input, self._sr7270_single_reference,
                                self._powermeter, self._waveplate)
        run.main()

    def heating_time(self, event=None):
        self.fetch(event)
        run = HeatingTime(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                          int(self._inputs['scan']),
                          float(self._current_amplifier_gain_options[self._current_gain.get()]),
                          float(self._inputs['rate (per second)']), float(self._inputs['max time (s)']),
                          float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                          self._npc3sg_input, self._sr7270_dual_harmonic, self._sr7270_single_reference,
                          self._powermeter, self._waveplate)
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
        self._waveplate.move_nearest(float(float(self._inputs['desired polarization']) / 2))
        self.readpolarization()

    def readpolarization(self):
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, self._waveplate.read_polarization())
        self._textbox.pack()
        self._textbox2.delete(1.0, tk.END)
        self._textbox2.insert(tk.END, (self._waveplate.read_waveplate_position() % 180) * 2)
        self._textbox2.pack()

    def home_waveplate(self):
        self._waveplate.home()

    def thermovoltage_intensity(self, event=None):
        self.fetch(event)
        run = ThermovoltageIntensity(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                     int(self._inputs['scan']), float(self._voltage_gain.get()),
                                     float(self._inputs['max time (s)']), int(self._inputs['steps']),
                                     self._npc3sg_input, self._sr7270_single_reference,
                                     self._powermeter, self._attenuatorwheel, self._waveplate)
        run.main()

    def heating_intensity(self, event=None):
        self.fetch(event)
        run = HeatingIntensity(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                               int(self._inputs['scan']),
                               float(self._current_amplifier_gain_options[self._current_gain.get()]),
                               float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                               float(self._inputs['max time (s)']), int(self._inputs['steps']), self._npc3sg_input,
                               self._sr7270_dual_harmonic, self._sr7270_single_reference, self._powermeter,
                               self._attenuatorwheel, self._waveplate)
        run.main()

    def iv_sweep(self, event=None):
        self.fetch(event)
        run = CurrentVoltageSweep(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                  self._inputs['device'],int(self._inputs['index']),
                                  float(self._current_amplifier_gain_options[self._current_gain.get()]),
                                  float(self._inputs['oscillator amplitude (mV)']),
                                  float(self._inputs['start voltage (mV)']),
                                  float(self._inputs['stop voltage (mV)']), int(self._inputs['steps']),
                                  int(self._inputs['# to average']), self._sr7270_dual_harmonic,
                                  self._sr7270_single_reference, float(self._inputs['wait time (ms)']),
                                  int(self._inputs['scans']), int(self._inputs['tick spacing (mV)']))
        run.main()

    def thermovoltage_polarization(self, event=None):
        self.fetch(event)
        run = ThermovoltagePolarization(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                        self._inputs['device'], int(self._inputs['scan']),
                                        float(self._voltage_gain.get()), self._npc3sg_input,
                                        self._sr7270_single_reference, self._powermeter, self._waveplate)
        run.main()

    def thermovoltage_polarization_dc(self, event=None):
        self.fetch(event)
        run = ThermovoltagePolarizationDC(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                          self._inputs['device'], int(self._inputs['scan']),
                                          float(self._voltage_gain.get()),
                                          self._npc3sg_input, self._powermeter, self._waveplate, self._daq_input)
        run.main()

    def heating_polarization(self, event=None):
        self.fetch(event)
        run = HeatingPolarization(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                  int(self._inputs['scan']),
                                  float(self._current_amplifier_gain_options[self._current_gain.get()]),
                                  float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                                  self._npc3sg_input, self._sr7270_dual_harmonic, self._sr7270_single_reference,
                                  self._powermeter,
                                  self._waveplate)
        run.main()

    def changeposition(self, event=None):
        self.fetch(event)
        self._npc3sg_x.move(int(self._inputs['x']))
        self._npc3sg_y.move(int(self._inputs['y']))
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def change_single_reference_lockin_parameters(self, event=None):
        self.fetch(event)
        if self._tc.get() != '':
            self._sr7270_single_reference.change_tc(float(self._tc.get()))
        if self._sen.get() != '':
            self._sr7270_single_reference.change_sensitivity(float(self._sen.get()))
        print('lock in parameters: \ntime constant: {} ms\nsensitivity: {} '
              'mV'.format(self._sr7270_single_reference.read_tc() * 1000,
                          self._sr7270_single_reference.read_sensitivity() * 1000))


    def change_dual_harmonic_lockin_parameters(self, event=None):
        self.fetch(event)
        if self._inputs['bias (mV)'] != '':
            self._sr7270_dual_harmonic.change_applied_voltage(float(self._inputs['bias (mV)']))
        if self._inputs['oscillator amplitude (mV)'] != '':
            self._sr7270_dual_harmonic.change_oscillator_amplitude(float(self._inputs['oscillator amplitude (mV)']))
        if self._inputs['oscillator frequency (Hz)'] != '':
            self._sr7270_dual_harmonic.change_oscillator_frequency(float(self._inputs['oscillator frequency (Hz)']))
        if self._tc1.get() != '':
            self._sr7270_dual_harmonic.change_tc(float(self._tc1.get()))
        if self._tc2.get() != '':
            self._sr7270_dual_harmonic.change_tc(float(self._tc2.get()), channel=2)
        if self._sen1.get() != '':
            self._sr7270_dual_harmonic.change_sensitivity(float(self._sen1.get()), channel=1)
        if self._sen2.get() != '':
            self._sr7270_dual_harmonic.change_sensitivity(float(self._sen2.get()), channel=2)
        print('lock in parameters: \ntime constant 1: {} ms\ntime constant 2: {} ms\nsensitivity 1: {} mV\nsensitivity '
              '2: {} mV\napplied bias (dac3): {} mV\nreference frequency: {} Hz\noscillator amplitude: '
              '{} mV'.format(self._sr7270_dual_harmonic.read_tc() * 1000,
                             self._sr7270_dual_harmonic.read_tc(channel=2) * 1000,
                             self._sr7270_dual_harmonic.read_sensitivity() * 1000,
                             self._sr7270_dual_harmonic.read_sensitivity(channel=2) * 1000,
                             self._sr7270_dual_harmonic.read_applied_voltage() * 1000,
                             self._sr7270_dual_harmonic.read_oscillator_frequency(),
                             self._sr7270_dual_harmonic.read_oscillator_amplitude() * 1000))

    def onclick_browse(self):
        self._filepath.set(tkinter.filedialog.askdirectory())

    def build_thermovoltage_scan_gui(self):
        caption = "Thermovoltage map scan"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'x pixel density': 20,
                        'y pixel density': 20, 'x range': 160, 'y range': 160, 'x center': 80, 'y center': 80}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, [1, 10, 100, 1000, 10000])
        self.make_option_menu('direction', self._direction, ['Forward', 'Reverse'])
        self.make_option_menu('cutthrough axis', self._axis, ['x', 'y'])
        self.endform(self.thermovoltage_scan)

    def build_thermovoltage_scan_dc_gui(self):
        caption = "DC thermovoltage map scan"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'x pixel density': 20,
                        'y pixel density': 20, 'x range': 160, 'y range': 160, 'x center': 80, 'y center': 80}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, [1, 10, 100, 1000, 10000])
        self.make_option_menu('direction', self._direction, ['Forward', 'Reverse'])
        self.endform(self.thermovoltage_scan_dc)

    def build_heating_scan_gui(self):
        caption = "Heating map scan"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'x pixel density': 20,
                        'y pixel density': 20, 'x range': 160, 'y range': 160, 'x center': 80,
                        'y center': 80, 'bias (mV)': 5, 'oscillator amplitude (mV)': 7}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.make_option_menu('direction', self._direction, ['Forward', 'Reverse'])
        self.endform(self.heating_scan)

    def build_thermovoltage_time_gui(self):
        caption = "Thermovoltage vs. time"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'rate (per second)': 3,
                        'max time (s)': 300}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, [1, 10, 100, 1000, 10000])
        self.endform(self.thermovoltage_time)

    def build_change_intensity_gui(self):
        caption = "Change laser intensity"
        self._fields = {'steps': 10}
        self.beginform(caption, False)
        self.maketextbox('Power (mW)', str('None'))
        self.makebutton('Forward', lambda: self.step(True))
        self.makebutton('Backward', lambda: self.step(False))
        self.makebutton('Read power', self.power)
        self.makebutton('Quit', self._master.destroy)

    def build_change_polarization_gui(self): # TODO fix this
        caption = "Change laser polarization"
        self._fields = {'desired polarization': 90}
        self.beginform(caption, False)
        self.maketextbox('current position', self._waveplate.read_polarization())
        self.maketextbox2('modulus polarization', (self._waveplate.read_waveplate_position() % 90) * 2)
        self.makebutton('Change polarization', self.changepolarization)
        self.makebutton('Read polarization', self.readpolarization)
        self.makebutton('Home', self.home_waveplate)
        self.makebutton('Quit', self._master.destroy)

    def build_thermovoltage_intensity_gui(self):
        caption = "Thermovoltage vs. laser intensity"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'steps': 2, 'max time (s)': 300}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, [1, 10, 100, 1000, 10000])
        self.endform(self.thermovoltage_intensity)

    def build_thermovoltage_polarization_gui(self):
        caption = "Thermovoltage vs. polarization"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': ""}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, [1, 10, 100, 1000, 10000])
        self.endform(self.thermovoltage_polarization)

    def build_thermovoltage_polarization_dc_gui(self):
        caption = "Thermovoltage DC vs. polarization"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': ""}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, [1, 10, 100, 1000, 10000])
        self.endform(self.thermovoltage_polarization_dc)

    def build_heating_polarization_gui(self):
       caption = "Heating vs. polarization"
       self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'bias (mV)': 5,
                       'oscillator amplitude (mV)': 7}
       self.beginform(caption)
       self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
       self.endform(self.heating_polarization)

    def build_change_position_gui(self):
        caption = "Change laser position"
        self._fields = {'x': 80, 'y': 80}
        self.beginform(caption, False)
        self.maketextbox('Current Position', [np.round(x, 1) for x in self._npc3sg_input.read()])
        self.makebutton('Change Position', self.changeposition)
        self.makebutton('Quit', self._master.destroy)

    def build_heating_time_gui(self):
        caption = "Heating vs. time"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'rate (per second)': 3,
                        'max time (s)': 300, 'bias (mV)': 5, 'oscillator amplitude (mV)': 7}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.endform(self.heating_time)

    def build_heating_intensity_gui(self):
        caption = "Heating vs. intensity"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'steps': 2,
                        'rate (per second)': 3, 'max time (s)': 300, 'bias (mV)': 5, 'oscillator amplitude (mV)': 7}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.endform(self.heating_intensity)

    def build_sweep_iv_gui(self):
        caption = "Current vs. Voltage curves"
        self._fields = {'file path': "", 'device': "", 'index': 0, 'notes': "", 'start voltage (mV)': -300,
                        'stop voltage (mV)': 300, 'steps': 301, '# to average': 20, 'wait time (ms)': 10,
                        'oscillator amplitude (mV)': 7, 'tick spacing (mV)': 25, 'scans': 1}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.endform(self.iv_sweep)

    def build_single_reference_gui(self):
        caption = "Change single reference lock in parameters"
        self.beginform(caption, False)
        self.make_option_menu('time constant (s)', self._tc,
                              [1e-3, 2e-3, 5e-3, 10e-03, 20e-03, 50e-03, 100e-03, 200e-03, 500e-03, 1, 2, 5, 10])
        self.make_option_menu('sensitivity (mV)', self._sen, [1e-2, 2e-2, 5e-2, 0.1, 0.2,
                                                                       0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500])
        self.endform(self.change_single_reference_lockin_parameters)

    def build_daqbreak_gui(self):
        caption = 'DAQ electromigration'
        self._fields = {'file path': '', 'device': '', 'desired resistance': 100,
                        'stop voltage (resistance measurement)': 0.05, 'steps': 10, 'start voltage': 0.3,
                        'break voltage': 1, 'delta break voltage': 0.005, 'delta voltage': 0.002,
                        'current drop': 50e-6, 'passes': 1}
        self.beginform(caption)
        self.make_option_menu('Gain', self._current_gain, self._current_amplifier_gain_options)
        self.make_option_menu('Abort', self._abort, ['True', 'False'])
        self.make_option_menu('Increase break voltage', self._increase, ['True', 'False'])
        self._master.bind('<Return>', self.electromigrate)
        self.endform(self.electromigrate)

    def build_dual_harmonic_gui(self):
        caption = "Change dual harmonic lock in parameters"
        self._fields = {'bias (mV)': '', 'oscillator amplitude (mV)': '',
                        'oscillator frequency (Hz)': ''}
        self.beginform(caption, False)
        self.make_option_menu('time constant 1 (s)', self._tc1,
                              [1e-3, 2e-3, 5e-3, 10e-03, 20e-03, 50e-03, 100e-03, 200e-03, 500e-03, 1, 2, 5, 10])
        self.make_option_menu('time constant 2 (s)', self._tc2,
                              [1e-3, 2e-3, 5e-3, 10e-03, 20e-03, 50e-03, 100e-03, 200e-03, 500e-03, 1, 2, 5, 10])
        self.make_option_menu('sensitivity 1 (mV)', self._sen1, [1e-2, 2e-2, 5e-2, 0.1, 0.2,
                                                                       0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500])
        self.make_option_menu('sensitivity 2 (mV)', self._sen2, [1e-2, 2e-2, 5e-2, 0.1, 0.2,
                                                                       0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500])
        self.endform(self.change_dual_harmonic_lockin_parameters)

    def build_measure_resistance_gui(self):
        caption = 'Measure lock in resistance'
        self._fields = {'file path': '', 'file name': str(datetime.date.today()) + ' resistance measurements',
                        'device': '', 'notes': ''}
        self.beginform(caption, True)
        self.make_option_menu('Current amplifier gain', self._current_gain, self._current_amplifier_gain_options)
        self.maketextbox('Resistance (ohms)', str(''))
        self.maketextbox2('Corrected resistance (ohms)', str(''))
        self.endform(self.resistance)

    def resistance(self, event=None):
        self.fetch(event)
        gain = float(self._current_amplifier_gain_options[self._current_gain.get()])
        osc = self._sr7270_dual_harmonic.read_oscillator_amplitude()
        x, y = self._sr7270_dual_harmonic.read_xy1()
        resistance = osc / x * gain
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, resistance)
        self._textbox2.delete(1.0, tk.END)
        self._textbox2.insert(tk.END, resistance - 51)
        self._textbox.pack()
        if path.exists(path.join(self._inputs['file path'], self._inputs['file name'] + '.csv')):
            file_type = 'a'
        else:
            file_type = 'w'
        with open(path.join(self._inputs['file path'], self._inputs['file name'] + '.csv'), file_type, newline='') as q:
            writer = csv.writer(q)
            if file_type == 'w':
                writer.writerow(['device', 'notes', 'total resistance (ohms)', 'corrected resistance (ohms)',
                                 'osc. amplitude (V)', 'gain', 'raw x', 'raw y'])
            writer.writerow([self._inputs['device'], self._inputs['notes'], resistance,
                             resistance - 51, osc, gain, x, y])

    def build_coming_soon(self):
        caption = "Coming soon"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self.makebutton('Quit', self._master.destroy)


def main():
    sr7270_dual_harmonic = None
    sr7270_single_reference = None
    try:
        with ExitStack() as cm:
            npc3sg_x = cm.enter_context(daq.create_ao_task(hw.ao_x))
            npc3sg_y = cm.enter_context(daq.create_ao_task(hw.ao_y))
            npc3sg_input = cm.enter_context(npc3sg.connect_input([hw.ai_x, hw.ai_y]))
            lock_ins = cm.enter_context(sr7270.create_endpoints(hw.vendor, hw.product))
            for lock_in in lock_ins:
                mode = lock_in.check_reference_mode()
                if mode == 0.0:
                    sr7270_single_reference = lock_in
                if mode == 1.0:
                    sr7270_dual_harmonic = lock_in
            if not sr7270_dual_harmonic or not sr7270_single_reference:
                print('Lock in amplifiers not configured correctly. Make sure that two are connected with one in'
                      ' dual harmonic mode and the other in single reference mode')
                raise ValueError
            powermeter = cm.enter_context(pm100d.connect(hw.pm100d_address))
            try:
                waveplate = cm.enter_context(polarizercontroller.connect_kdc101(hw.kdc101_serial_number))
            except Exception:
                waveplate = None
            attenuatorwheel = cm.enter_context(attenuator_wheel.create_do_task(hw.attenuator_wheel_outputs))
            daq_input = cm.enter_context(daq.create_ai_task([hw.ai_dc1, hw.ai_dc2], points=1000))
            daq_switch_ai = cm.enter_context(daq.create_ai_task(hw.ai_switch, sleep=0))
            daq_switch_ao = cm.enter_context(daq.create_ao_task(hw.ao_switch))
            root = tk.Tk()
            app = BaseLockinGUI(root, npc3sg_x=npc3sg_x, npc3sg_y=npc3sg_y, npc3sg_input=npc3sg_input,
                                sr7270_dual_harmonic=sr7270_dual_harmonic, sr7270_single_reference=sr7270_single_reference,
                                powermeter=powermeter, attenuatorwheel=attenuatorwheel, waveplate=waveplate,
                                daq_input=daq_input, daq_switch_ai=daq_switch_ai, daq_switch_ao=daq_switch_ao)
            app.build()
            root.mainloop()
    except Exception as err:
        if 'NFOUND' in str(err):
            print('PM100D power detector communication error')
        else:
            print(err)
        input('Press enter to exit')


if __name__ == '__main__':
    main()