import ctypes
co_initialize = ctypes.windll.ole32.CoInitialize
import matplotlib

matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
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
from optics.current_vs_voltage.current_vs_voltage_vs_gate import CurrentVoltageGateSweep
from contextlib import ExitStack
from optics.current_vs_voltage.current_vs_voltage import CurrentVoltageSweep
from optics.electromigrate.daq_break import DAQBreak
import datetime
import csv
import os
from os import path
from optics.gui.base_gui import BaseGUI
from optics.electromigrate.k2400_break import KeithleyBreak
from optics.hardware_control import keithley_k2400
from optics.hardware_control import hardware_addresses_and_constants
from optics.hardware_control import toptica_ibeam_smart
from optics.raman.raman_gui import RamanBaseGUI


class BaseLockinGUI(BaseGUI):
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_dual_harmonic=None, sr7270_single_reference=None, powermeter=None, attenuatorwheel=None,
                 waveplate=None,
                 daq_input=None, daq_switch_ai=None, daq_switch_ao=None, keithley=None, laser=None, polarizer=None):
        self._master = master
        super().__init__(self._master)
        self._master.title('Optics setup measurements')
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._keithley = keithley
        self._laser = laser
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._waveplate = waveplate
        self._daq_input = daq_input
        self._daq_switch_ai = daq_switch_ai
        self._daq_switch_ao = daq_switch_ao
        self._newWindow = None
        self._app = None
        self._polarizer = polarizer

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)
        self._app = LockinMeasurementGUI(self._newWindow, npc3sg_x=self._npc3sg_x, npc3sg_y=self._npc3sg_y,
                                         npc3sg_input=self._npc3sg_input,
                                         sr7270_dual_harmonic=self._sr7270_dual_harmonic,
                                         sr7270_single_reference=self._sr7270_single_reference,
                                         powermeter=self._powermeter, attenuatorwheel=self._attenuatorwheel,
                                         waveplate=self._waveplate, daq_input=self._daq_input,
                                         daq_switch_ai=self._daq_switch_ai,
                                         daq_switch_ao=self._daq_switch_ao, keithley=self._keithley, laser=self._laser)
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
                       'ivsweepgate': self._app.build_sweep_iv_gate_gui,
                       'singlereference': self._app.build_single_reference_gui,
                       'dualharmonic': self._app.build_dual_harmonic_gui,
                       'electromigrate': self._app.build_daqbreak_gui,
                       'k2400electromigrate': self._app.build_k2400_break_gui,
                       'measureresistance': self._app.build_measure_resistance_gui,
                       'laserparameters': self._app.build_laser_paramaters_gui,
                       'raman': ''}
        if measurementtype != 'raman':
            measurement[measurementtype]()
        else:
            RamanBaseGUI(self._newWindow, self._sr7270_single_reference, self._sr7270_dual_harmonic, self._waveplate,
                         self._powermeter, self._npc3sg_input, self._polarizer).build()

    def build(self):
        row = self.makerow('map scans')
        self.make_measurement_button(row, 'thermovoltage', 'ptemap')
        self.make_measurement_button(row, 'heating', 'heatmap')
        row = self.makerow('DC map scans')
        self.make_measurement_button(row, 'thermovoltage map', 'ptemapdc')
        if self._waveplate:
            self.make_measurement_button(row, 'pte polarization', 'ptepolarizationdc')
        row = self.makerow('I-V curves')
        self.make_measurement_button(row, 'current', 'ivsweep')
        if self._keithley:
            self.make_measurement_button(row, 'gate', 'ivsweepgate')
        row = self.makerow('polarization scans')
        if self._waveplate:
            self.make_measurement_button(row, 'thermovoltage', 'ptepolarization')
            self.make_measurement_button(row, 'heating', 'heatpolarization')
        else:
            row = self.makerow('Waveplate not connected', side=None, width=20)
        row = self.makerow('intensity scans')
        if self._powermeter and self._attenuatorwheel:
            self.make_measurement_button(row, 'thermovoltage', 'pteintensity')
            self.make_measurement_button(row, 'heating', 'heatintensity')
        if not self._powermeter:
            self.makerow('Power detector not connected', side=None, width=25)
        if not self._attenuatorwheel:
            self.makerow('Attenuator wheel not connected', side=None, width=25)
        row = self.makerow('time scans')
        self.make_measurement_button(row, 'thermovoltage', 'ptetime')
        self.make_measurement_button(row, 'heating', 'heattime')
        row = self.makerow('electromigrate')
        self.make_measurement_button(row, 'DAQ break', 'electromigrate')
        if self._keithley:
            self.make_measurement_button(row, 'Keithley break', 'k2400electromigrate')
        row = self.makerow('Raman')
        self.make_measurement_button(row, 'Raman', 'raman')
        row = self.makerow('change parameters')
        self.make_measurement_button(row, 'position', 'position')
        self.make_measurement_button(row, 'intensity', 'intensity')
        self.make_measurement_button(row, 'polarization', 'polarization')
        self.make_measurement_button(row, 'laser', 'laserparameters')
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


class LockinMeasurementGUI(BaseGUI):
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, npc3sg_input=None,
                 sr7270_dual_harmonic=None, sr7270_single_reference=None, powermeter=None, attenuatorwheel=None,
                 waveplate=None,
                 daq_input=None, daq_switch_ai=None, daq_switch_ao=None, keithley=None, laser=None):
        self._master = master
        super().__init__(self._master)
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._npc3sg_input = npc3sg_input
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._daq_switch_ai = daq_switch_ai
        self._daq_switch_ao = daq_switch_ao
        self._keithley = keithley
        self._laser = laser
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._waveplate = waveplate
        self._daq_input = daq_input
        self._direction = tk.StringVar()
        self._direction.set('Forward')
        self._axis = tk.StringVar()
        self._axis.set('y')
        self._current_gain = tk.StringVar()
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

    def electromigrate(self, event=None):
        self.fetch(event)
        run = DAQBreak(tk.Toplevel(self._master), self._daq_switch_ao, self._daq_switch_ai, self._inputs['file path'],
                       self._inputs['device'], steps=int(self._inputs['steps']),
                       stop_voltage=float(self._inputs['stop voltage (resistance measurement)']),
                       desired_resistance=float(self._inputs['desired resistance']),
                       break_voltage=float(self._inputs['break voltage']), passes=float(self._inputs['passes']),
                       increase_break_voltage=self.string_to_bool(self._increase.get()), delta_break_voltage=float(self._inputs['delta break voltage']),
                       start_voltage=float(self._inputs['start voltage']),
                       delta_voltage=float(self._inputs['delta voltage']),
                       current_drop=float(self._inputs['current drop']), abort=self.string_to_bool(self._abort.get()),
                       gain=float(self._current_amplifier_gain_options[self._current_gain.get()]))
        run.main()

    def thermovoltage_scan(self, event=None):
        self.fetch(event)
        if self._direction.get() == 'Reverse':
            direction = False
        else:
            direction = True
        run = ThermovoltageScan(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                self._inputs['device'],
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
        run = ThermovoltageScanDC(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                  self._inputs['device'],
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
        run = HeatingScan(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                          self._inputs['device'],
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
        run = ThermovoltageTime(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                self._inputs['device'],
                                int(self._inputs['scan']), float(self._voltage_gain.get()),
                                float(self._inputs['rate (per second)']), float(self._inputs['max time (s)']),
                                self._npc3sg_input, self._sr7270_single_reference,
                                self._powermeter, self._waveplate)
        run.main()

    def heating_time(self, event=None):
        self.fetch(event)
        run = HeatingTime(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                          self._inputs['device'],
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
        self._textbox2.insert(tk.END, (self._waveplate.read_position() % 180) * 2)
        self._textbox2.pack()

    def homewaveplate(self):
        self._waveplate.home()

    def thermovoltage_intensity(self, event=None):
        self.fetch(event)
        run = ThermovoltageIntensity(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                     self._inputs['device'],
                                     int(self._inputs['scan']), float(self._voltage_gain.get()),
                                     float(self._inputs['max time (s)']), int(self._inputs['steps']),
                                     self._npc3sg_input, self._sr7270_single_reference,
                                     self._powermeter, self._attenuatorwheel, self._waveplate)
        run.main()

    def heating_intensity(self, event=None):
        self.fetch(event)
        run = HeatingIntensity(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                               self._inputs['device'],
                               int(self._inputs['scan']),
                               float(self._current_amplifier_gain_options[self._current_gain.get()]),
                               float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                               float(self._inputs['max time (s)']), int(self._inputs['steps']), self._npc3sg_input,
                               self._sr7270_dual_harmonic, self._sr7270_single_reference, self._powermeter,
                               self._attenuatorwheel, self._waveplate)
        run.main()

    def iv_sweep_gate(self, event=None):
        self.fetch(event)
        run = CurrentVoltageGateSweep(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                      self._inputs['device'], int(self._inputs['index']),
                                      float(self._current_amplifier_gain_options[self._current_gain.get()]),
                                      float(self._inputs['oscillator amplitude (mV)']),
                                      float(self._inputs['start voltage (mV)']),
                                      float(self._inputs['stop voltage (mV)']), int(self._inputs['steps']),
                                      int(self._inputs['# to average']), self._sr7270_dual_harmonic,
                                      self._sr7270_single_reference, float(self._inputs['wait time (ms)']),
                                      int(self._inputs['scans']), int(self._inputs['tick spacing (mV)']),
                                      self._keithley, float(self._inputs['min gate (V)']),
                                      float(self._inputs['max gate (V)']), int(self._inputs['gate steps']))
        run.main()

    def iv_sweep(self, event=None):
        self.fetch(event)
        if self._keithley:
            run = CurrentVoltageSweep(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                      self._inputs['device'], int(self._inputs['index']),
                                      float(self._current_amplifier_gain_options[self._current_gain.get()]),
                                      float(self._inputs['oscillator amplitude (mV)']),
                                      float(self._inputs['start voltage (mV)']),
                                      float(self._inputs['stop voltage (mV)']), int(self._inputs['steps']), int(self._inputs['# to average']),
                                      self._sr7270_dual_harmonic, self._sr7270_single_reference, float(self._inputs['wait time (ms)']),
                                      int(self._inputs['scans']), int(self._inputs['tick spacing (mV)']), self._keithley,
                                      float(self._inputs['gate (V)']), int(self._inputs['gate ramp spacing (mV)']))
        else:
            run = CurrentVoltageSweep(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                    self._inputs['device'], int(self._inputs['index']),
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
                                        self._sr7270_single_reference, self._powermeter, self._waveplate, int(self._inputs['polarization steps']))
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
        run = HeatingPolarization(tk.Toplevel(self._master), self._inputs['file path'], self._inputs['notes'],
                                  self._inputs['device'],
                                  int(self._inputs['scan']),
                                  float(self._current_amplifier_gain_options[self._current_gain.get()]),
                                  float(self._inputs['bias (mV)']), float(self._inputs['oscillator amplitude (mV)']),
                                  self._npc3sg_input, self._sr7270_dual_harmonic, self._sr7270_single_reference,
                                  self._powermeter, self._waveplate, int(self._inputs['polarization steps']))
        run.main()

    def changeposition(self, event=None):
        self.fetch(event)
        self._npc3sg_x.move(int(self._inputs['x']))
        self._npc3sg_y.move(int(self._inputs['y']))
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def center_beam(self):
        self._npc3sg_x.move(80)
        self._npc3sg_y.move(80)
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

    def build_thermovoltage_scan_gui(self):
        caption = "Thermovoltage map scan"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'x pixel density': 20,
                        'y pixel density': 20, 'x range': 160, 'y range': 160, 'x center': 80, 'y center': 80}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, self._voltage_gain_options)
        self.make_option_menu('direction', self._direction, ['Forward', 'Reverse'])
        self.make_option_menu('cutthrough axis', self._axis, ['x', 'y'])
        self.endform(self.thermovoltage_scan)

    def build_thermovoltage_scan_dc_gui(self):
        caption = "DC thermovoltage map scan"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'x pixel density': 20,
                        'y pixel density': 20, 'x range': 160, 'y range': 160, 'x center': 80, 'y center': 80}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, self._voltage_gain_options)
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
        self.make_option_menu('gain', self._voltage_gain, self._voltage_gain_options)
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

    def build_change_polarization_gui(self):  # TODO fix this
        caption = "Change laser polarization"
        self._fields = {'desired polarization': 90}
        self.beginform(caption, False)
        self.maketextbox('current position', self._waveplate.read_polarization())
        self.maketextbox2('modulus polarization', (self._waveplate.read_position() % 90) * 2)
        self.makebutton('Change polarization', self.changepolarization)
        self.makebutton('Read polarization', self.readpolarization)
        self.makebutton('Home', self.homewaveplate)
        self.makebutton('Quit', self._master.destroy)

    def build_thermovoltage_intensity_gui(self):
        caption = "Thermovoltage vs. laser intensity"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'steps': 2, 'max time (s)': 300}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, self._voltage_gain_options)
        self.endform(self.thermovoltage_intensity)

    def build_thermovoltage_polarization_gui(self):
        caption = "Thermovoltage vs. polarization"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'polarization steps': 5}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, self._voltage_gain_options)
        self.endform(self.thermovoltage_polarization)

    def build_thermovoltage_polarization_dc_gui(self):
        caption = "Thermovoltage DC vs. polarization"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': ""}
        self.beginform(caption)
        self.make_option_menu('gain', self._voltage_gain, self._voltage_gain_options)
        self.endform(self.thermovoltage_polarization_dc)

    def build_heating_polarization_gui(self):
        caption = "Heating vs. polarization"
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'bias (mV)': 5,
                        'oscillator amplitude (mV)': 7, 'polarization steps': 5}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.endform(self.heating_polarization)

    def moveup(self, event=None):
        x, y = self._npc3sg_input.read()
        self._npc3sg_y.move(y + 1)
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def movedown(self, event=None):
        x, y = self._npc3sg_input.read()
        self._npc3sg_y.move(y - 1)
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def moveleft(self, event=None):
        x, y = self._npc3sg_input.read()
        self._npc3sg_x.move(x - 1)
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def moveright(self, event=None):
        x, y = self._npc3sg_input.read()
        self._npc3sg_x.move(x + 1)
        self._textbox.delete(1.0, tk.END)
        self._textbox.insert(tk.END, [np.round(x, 1) for x in self._npc3sg_input.read()])
        self._textbox.pack()

    def build_change_position_gui(self):
        caption = "Change laser position"
        self._fields = {'x': 80, 'y': 80}
        self.beginform(caption, False)
        self.maketextbox('Current Position', [np.round(x, 1) for x in self._npc3sg_input.read()])
        self.makebutton('Go to center', self.center_beam)
        self.makebutton('Change Position', self.changeposition)
        self._master.bind('<Left>', self.moveleft)
        self._master.bind('<Right>', self.moveright)
        self._master.bind('<Up>', self.moveup)
        self._master.bind('<Down>', self.movedown)
        self._master.bind('<Return>', self.changeposition)
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

    def build_sweep_iv_gate_gui(self):
        caption = "Current vs. Voltage vs. Gate waterfall"
        self._fields = {'file path': "", 'device': "", 'index': 0, 'notes': "", 'start voltage (mV)': -250,
                        'stop voltage (mV)': 250, 'steps': 251, '# to average': 10, 'wait time (ms)': 10,
                        'oscillator amplitude (mV)': 7, 'tick spacing (mV)': 25, 'scans': 1, 'min gate (V)': -100,
                        'max gate (V)': 100, 'gate steps': 11}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.endform(self.iv_sweep_gate)

    def build_sweep_iv_gui(self):
        caption = "Current vs. Voltage curves"
        if self._keithley:
            self._fields = {'file path': "", 'device': "", 'index': 0, 'notes': "", 'start voltage (mV)': -250,
                            'stop voltage (mV)': 250, 'steps': 251, '# to average': 20, 'wait time (ms)': 10,
                            'oscillator amplitude (mV)': 7, 'tick spacing (mV)': 25, 'scans': 1, 'gate (V)': 0,
                            'gate ramp spacing (mV)': 250}
        else:
            self._fields = {'file path': "", 'device': "", 'index': 0, 'notes': "", 'start voltage (mV)': -250,
                            'stop voltage (mV)': 250, 'steps': 251, '# to average': 20, 'wait time (ms)': 10,
                            'oscillator amplitude (mV)': 7, 'tick spacing (mV)': 25, 'scans': 1}
        self.beginform(caption)
        self.make_option_menu('gain', self._current_gain, self._current_amplifier_gain_options.keys())
        self.endform(self.iv_sweep)

    def build_single_reference_gui(self):
        caption = "Change single reference lock in parameters"
        self.beginform(caption, False)
        self.make_option_menu('time constant (s)', self._tc, self._time_constant_options)
        self.make_option_menu('sensitivity (mV)', self._sen, self._lockin_sensitivity_options)
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
        self.make_option_menu('time constant 1 (s)', self._tc1, self._time_constant_options)
        self.make_option_menu('time constant 2 (s)', self._tc2, self._time_constant_options)
        self.make_option_menu('sensitivity 1 (mV)', self._sen1, self._lockin_sensitivity_options)
        self.make_option_menu('sensitivity 2 (mV)', self._sen2, self._lockin_sensitivity_options)
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

    def build_k2400_break_gui(self):
        caption = 'Keithley K2400 electromigration'
        self._fields = {'file path': '', 'device': '', 'desired resistance': 100,
                        'stop voltage (resistance measurement)': 0.05, 'steps': 10, 'start voltage': 0.1,
                        'break voltage': 0.7, 'delta break voltage': 0.005, 'delta voltage': 0.002,
                        'percent current drop': 0.4, 'passes': 1}
        self.beginform(caption, True)
        self.make_option_menu('abort', self._abort, ['True', 'False'])
        self.make_option_menu('increase break voltage', self._increase, ['True', 'False'])
        self._master.bind('<Return>', self.k2400electromigrate)
        self.endform(self.k2400electromigrate)

    def k2400electromigrate(self, event=None):
        self.fetch(event)
        run = KeithleyBreak(tk.Toplevel(self._master), self._keithley, self._inputs['file path'],
                            self._inputs['device'],
                            steps=int(self._inputs['steps']),
                            stop_voltage=float(self._inputs['stop voltage (resistance measurement)']),
                            desired_resistance=float(self._inputs['desired resistance']),
                            break_voltage=float(self._inputs['break voltage']), passes=float(self._inputs['passes']),
                            increase_break_voltage=self.string_to_bool(self._increase.get()),
                            delta_break_voltage=float(self._inputs['delta break voltage']),
                            start_voltage=float(self._inputs['start voltage']),
                            delta_voltage=float(self._inputs['delta voltage']),
                            r_percent=float(self._inputs['percent current drop']), abort=self.string_to_bool(self._abort.get()))
        run.main()

    def build_coming_soon(self):
        caption = "Coming soon"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self.makebutton('Quit', self._master.destroy)

    def build_laser_paramaters_gui(self):
        from optics.hardware_control.hardware_addresses_and_constants import laser_log_path
        caption = 'Laser parameters'
        self._fields = {'file path': laser_log_path}
        self.beginform(caption, True)
        self.makebutton('Laser on', self._laser.turn_on)
        self.makebutton('Laser off', self._laser.turn_off)
        self.makebutton('Fine mode', self._laser.set_fine_status)
        self.makebutton('Record status', self.record_laser_status)
        self.makebutton('Quit', self._master.destroy)

    def record_laser_status(self, event=None):
        self.fetch(event)
        filename = os.path.join(self._inputs['file path'], '{} laser log.csv'.format(str(datetime.date.today())))
        if os.path.exists(filename):
            with open(filename, 'a', newline='') as inputfile:
                writer = csv.writer(inputfile)
                writer.writerow(
                    [str(datetime.datetime.now()), 'ok', self._laser.read_laser_status(), self._laser.read_system_temperature(),
                     self._laser.read_temperature(),
                     self._laser.read_fine_status(), self._laser.read_current(),
                     self._laser.read_power_level()[0], self._laser.read_power_level()[1]])
        else:
            with open(filename, 'w', newline='') as inputfile:
                writer = csv.writer(inputfile)
                writer.writerow(
                    ['time', 'communication status', 'laser status', 'system temperature (C)', 'laser temperature (C)',
                     'FINE mode status',
                     'current (mA)', 'channel 1 power level (mW)', 'channel 2 power level (mW)'])
                writer.writerow(
                    [str(datetime.datetime.now()), 'ok', self._laser.read_laser_status(), self._laser.read_system_temperature(),
                     self._laser.read_temperature(),
                     self._laser.read_fine_status(), self._laser.read_current(),
                     self._laser.read_power_level()[0], self._laser.read_power_level()[1]])



def main():
    sr7270_dual_harmonic = None
    sr7270_single_reference = None
    print('connecting hardware')
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
            try:
                powermeter = cm.enter_context(pm100d.connect(hw.pm100d_address))
            except Exception as err:
                if 'NFOUND' in str(err):
                    print('Warning: PM100D power detector not connected')
                else:
                    print('Warning: {}'.format(err))
                powermeter = None
            try:
                waveplate = cm.enter_context(polarizercontroller.connect_tdc001(hw.tdc001_serial_number, waveplate=True))
            except Exception:
                waveplate = None
                print('Warning: Waveplate controller not connected')
            try:
                polarizer = cm.enter_context(polarizercontroller.connect_kdc101(hw.kdc101_serial_number, waveplate=False))
            except Exception:
                polarizer = None
                print('Warning: Polarizer controller not connected')
            attenuatorwheel = cm.enter_context(attenuator_wheel.create_do_task(hw.attenuator_wheel_outputs))
            daq_input = cm.enter_context(daq.create_ai_task([hw.ai_dc1, hw.ai_dc2], points=1000))
            daq_switch_ai = cm.enter_context(daq.create_ai_task(hw.ai_switch, sleep=0))
            daq_switch_ao = cm.enter_context(daq.create_ao_task(hw.ao_switch))
            laser = cm.enter_context(toptica_ibeam_smart.connect_laser())
            keithley = cm.enter_context(keithley_k2400.connect(hardware_addresses_and_constants.keithley_address))
            try:
                keithley.reset()
            except Exception:
                keithley = None
                print('Warning: Keithley K2400 not connected')
            print('hardware connection complete')
            root = tk.Tk()
            app = BaseLockinGUI(root, npc3sg_x=npc3sg_x, npc3sg_y=npc3sg_y, npc3sg_input=npc3sg_input,
                                sr7270_dual_harmonic=sr7270_dual_harmonic,
                                sr7270_single_reference=sr7270_single_reference,
                                powermeter=powermeter, attenuatorwheel=attenuatorwheel, waveplate=waveplate,
                                daq_input=daq_input, daq_switch_ai=daq_switch_ai, daq_switch_ao=daq_switch_ao,
                                keithley=keithley, laser=laser, polarizer=polarizer)
            app.build()
            root.mainloop()
    except Exception as err:
        if 'VI_ERROR_NLISTENERS' in str(err):  # this error occurs if Keithley isn't connected and you exit the stack
            pass
        else:
            print(err)
            input('Press enter to exit')


if __name__ == '__main__':
    main()
