
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
    import math
    return degree / 180 * math.pi

