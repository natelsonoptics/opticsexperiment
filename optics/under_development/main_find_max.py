import time

import numpy as np

from optics.defunct import npc3sg_analog
from optics.hardware_control import sr7270, hardware_addresses_and_constants
from optics.misc_utility import parser_tool, conversions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='move x and y piezo position')
    parser.add_argument("-x", metavar='x', type=float, help='x center position')
    parser.add_argument("-y", metavar='y', type=float, help='y center position')
    parser.add_argument("-width", metavar='width',type=float,help='width of scan')
    parser.add_argument("-gain", metavar="gain", type=float, help="gain")
    args = parser.parse_args()

    with npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as (sr7270_top, sr7270_bottom):
        max_voltage = 0
        max_position = [0, 0, 0]
        for i in np.arange(args.y-args.width/2, args.y+args.width/2, 0.25):
            npc3sg_y.move(i)
            for j in np.arange(args.x-args.width/2, args.x+args.width/2, 0.25):
                npc3sg_x.move(j)
                time.sleep(0.2)
                voltages = [conversions.convert_x_to_iphoto(x, args.gain) for x in
                            parser_tool.parse(sr7270_bottom.read_xy())]
                if np.abs(voltages[0]) > max_voltage:
                    max_voltage = np.abs(voltages[0])
                    max_position = npc3sg_input.read()
        # npc3sg_x.move(max_position[0])
        # npc3sg_y.move(max_position[1])
        npc3sg_x.move(80)
        npc3sg_y.move(80)
        print(max_voltage)




