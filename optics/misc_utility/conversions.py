
def convert_x_to_iphoto(x, gain, square_wave=True):
    if square_wave:
        return convert_square_wave(x)/gain
    else:
        return x / gain

def convert_square_wave(x):
    return x * 2.22

def degrees_to_radians(degree):
    import math
    return degree / 180 * math.pi

