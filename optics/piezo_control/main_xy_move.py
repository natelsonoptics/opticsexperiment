from optics.hardware_control import npc3sg_analog, hardware_addresses_and_constants

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='move x and y piezo position')
    parser.add_argument("-x", metavar='x', type=float, help='x position', default=80)
    parser.add_argument("-y", metavar='y', type=float, help='y position', default=80)
    args = parser.parse_args()
    with npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input:
            npc3sg_x.move(args.x)
            npc3sg_y.move(args.y)
            print(npc3sg_input.read())
