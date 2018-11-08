import numpy as np
import math
from optics.hardware_control.hardware_addresses_and_constants import low_pass_filter_factor


def convert_x_to_iphoto(x, gain, square_wave=True):
    if square_wave:
        return convert_square_wave(x) / gain
    else:
        return x / gain

def convert_square_wave(x):
    #  This factor is because we are using a square wave for the reference signal and reading in
    #  a square wave, but the lock in amplifier is reading it not only as a sine wave, but also
    #  as the VRMS of that sine wave. This converts the read VRMS of the lock in to the peak-to-peak
    #  value of the square wave
    #
    #  2 V peak to peak square wave is read as the first term of the Fourier transform
    #  4/pi*sin(wt) (amplitude 4/pi) and is displayed as the VRMS of that sine wave
    #  4/(pi*sqrt(2)) = 0.9 VRMS. So A 2 V peak to peak square wave is read in 0.9 VRMS sine wave
    #  To read the total magnitude of the signal you must multiply by that factor: 2/0.9 = 2.22
    return x * 2.22


def degrees_to_radians(degree):
    return degree / 180 * math.pi


def convert_x1_to_didv(x1, gain, osc):
    return x1 / (gain * osc)


def convert_x2_to_d2idv2(x2, gain, osc):
    return x2 / (gain * 1/4 * osc ** 2)


def normalize_dgdv_from_didv(vdc, didv, d2idv2):
    return np.abs(vdc * d2idv2 / didv)


def normalize_dgdv_from_x1(vdc, x1, x2, gain, osc):
    return normalize_dgdv_from_didv(vdc, convert_x1_to_didv(x1, gain, osc), convert_x2_to_d2idv2(x2, gain, osc))


def normalize_iets_from_x1(x1, x2, gain, osc):
    return normalize_iets_from_didv(convert_x1_to_didv(x1, gain, osc), convert_x2_to_d2idv2(x2, gain, osc))


def normalize_iets_from_didv(didv, d2idv2):
    return np.abs(d2idv2 / didv)


def convert_adc_to_idc(adc, gain, lpf_factor=low_pass_filter_factor):
    return adc / (gain * lpf_factor)


def differentiate_d2idv2(didv1, didv2):
    return np.diff([didv1, didv2])[0]