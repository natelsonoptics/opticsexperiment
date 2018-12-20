import numpy as np


def convert_pixels_to_wavelength(groove_density, center_wavelength=785, xpixels=1024):
    wavelengths = np.zeros(1024)
    #  these constants are for the iHR 320
    F = 318.719  # mm
    LB = F  # mm
    G = -5.5  # degrees
    PIXEL_WIDTH = 0.026 # mm
    DV = 10.63 * 2  # degrees  # deviation angle
    LAMBDA = center_wavelength  # nm  # wavelength in vacuum
    K = 1  # refractive index (air)
    GN = groove_density  # grooves / mm

    # these equations follow Horiba's Optics of Spectroscopy tutorial:
    # https://www.horiba.com/en_en/wavelength-pixel-position/

    alpha = np.arcsin((1e-6 * K * GN * LAMBDA) / (2 * np.cos(DV / 2 * np.pi / 180))) - DV * np.pi / 180 / 2
    blc = DV * np.pi / 180 + alpha

    for i in range(xpixels):
        lh = F * np.cos(G * np.pi / 180)
        bh = blc + G * np.pi / 180
        hblc = F * np.sin(G * np.pi / 180)   # radians
        hbln = PIXEL_WIDTH * (i - (xpixels / 2)) + hblc
        bln = bh - np.arctan(hbln / lh)  # radians
        lambdan = ((np.sin(alpha) + np.sin(bln)) * 1e6) / (K * GN)
        wavelengths[xpixels-1-i] = lambdan

    return wavelengths


def convert_nm_to_wavenumber(nm, laser_wavelength=785):
    return 1 / (laser_wavelength * 1e-7) - 1 / (nm * 1e-7)  # cm^-1


def convert_nm_to_ev(nm):
    hc = 1.2398424468e-6
    return hc / (nm * 1e-9)


def convert_wavenumber_to_nm(wavenumber, laser_wavelength=785):
    return 1 / (1 / laser_wavelength - wavenumber / 1e7)


def convert_ev_to_nm(ev):
    hc = 1.2398424468e-6
    return hc / (ev * 1e-9)


def convert_pixels_to_unit(unit, groove_density, center_wavelength, laser_wavelength=785, pixels=1024):
    nm = convert_pixels_to_wavelength(groove_density, center_wavelength, pixels)
    if unit == 'nm':
        return nm
    if unit == 'eV':
        return convert_nm_to_ev(nm)
    if unit == 'cm^-1':
        return convert_nm_to_wavenumber(nm, laser_wavelength)



