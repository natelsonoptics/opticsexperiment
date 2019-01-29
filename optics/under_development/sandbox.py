from optics.under_development.test import RamanLockinOutgoingPolarization
import numpy as np
import tkinter as tk

class RamanLockinOutgoingPolarizationSweepBias():
    def __init__(self, master, filepath, notes, device, scan, gain, start_bias, stop_bias, bias_steps, osc,
                 npc3sg_input, sr7270_dual_harmonic, sr7270_single_reference, powermeter, waveplate, steps, polarizer,
                 number_measurements, wait_time_ms, ccd, integration_time, raman_gain, acquisitions, units, grating,
                 center_wavelength, raman_start, raman_stop, darkcurrent, darkcorrected):
        self._biases = np.arange(start_bias, stop_bias, bias_steps)
        self._master = master
        self._filepath = filepath
        self._notes = notes
        self._device = device
        self._scan = scan
        self._gain = gain
        self._osc = osc
        self._npc3sg_input = npc3sg_input
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._powermeter = powermeter
        self._waveplate = waveplate
        self._steps = steps
        self._polarizer = polarizer
        self._number_measurements = number_measurements
        self._wait_time_ms = wait_time_ms
        self._ccd = ccd
        self._integration_time = integration_time
        self._raman_gain = raman_gain
        self._acquisitions =acquisitions
        self._units = units
        self._grating = grating
        self._center_wavelength = center_wavelength
        self._raman_start = raman_start
        self._raman_stop = raman_stop
        self._darkcurrent = darkcurrent
        self._darkcorrected = darkcorrected
        print(self._polarizer)

    def main(self):
        for bias in self._biases:
            measurement = RamanLockinOutgoingPolarization(tk.Toplevel(self._master), self._filepath, self._notes, self._device, self._scan, self._gain, bias,
                                            self._osc, self._npc3sg_input, self._sr7270_dual_harmonic, self._sr7270_single_reference,
                                            self._powermeter, self._waveplate, self._steps, self._polarizer, self._number_measurements,
                                            self._wait_time_ms, self._ccd, self._integration_time, self._raman_gain,
                                            self._acquisitions, self._units, self._grating, self._center_wavelength, self._raman_start,
                                            self._raman_stop, self._darkcurrent, self._darkcorrected)
            measurement.main()
