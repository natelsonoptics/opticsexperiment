import csv
import time

import matplotlib.pyplot as plt
import numpy as np

from optics.defunct import npc3sg_analog
from optics.hardware_control import sr7270, hardware_addresses_and_constants


def linear(x, M, B):
    return M * x + B

def write_header(w):
    w.writerow(['gain:', args.gain])
    w.writerow(['notes:', args.notes])
    w.writerow(['osc amplitude:', sr7270_top.read_oscillator_amplitude()[0]])
    w.writerow(['osc frequency:', sr7270_top.read_oscillator_frequency()[0]])
    w.writerow(['time constant:', sr7270_bottom.read_tc()[0]])
    w.writerow(['top time constant:', sr7270_top.read_tc1()[0]])
    w.writerow(['end:', 'end of header'])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='sweep scan iphotoX. Press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-gain", metavar='gain', type=float, help='amplifier gain')
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    args = parser.parse_args()

    with open(args.f, 'w', newline='') as fn, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as (sr7270_top, sr7270_bottom):
        w = csv.writer(fn)
        write_header(w)
        current = []
        voltage = []
        for applied_voltage in np.arange(30, 200, 10):
            sr7270_top.change_applied_voltage(applied_voltage)
            time.sleep(0.3)
            sr7270_top.change_applied_voltage(applied_voltage)
            time.sleep(0.3)
            voltage.append(sr7270_top.read_applied_voltage()[0])
            time.sleep(0.3)
            current.append(sr7270_top.read_xy1()[0])

        plt.scatter(voltage, current)
        plt.ylim(np.amin(current), np.amax(current))
        plt.show()



