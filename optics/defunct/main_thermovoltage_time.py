from optics.hardware_control import sr7270, npc3sg_analog, hardware_addresses_and_constants
from optics.thermovoltage_measurement.thermovoltage_time import ThermovoltageTime

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='iphotoX vs time. press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-rate", metavar='rate', type=float, help='optional. samples/second. do not exceed 50')
    parser.add_argument("-max", metavar='max', type=float, help='max time (seconds)')
    parser.add_argument("-gain",metavar='gain', type=float, help="gain of amplifier")
    parser.add_argument("-pol", metavar='polarization', type=float, help='polarization of light in degrees')
    parser.add_argument("-device", metavar='device', type=str, help='device name')
    parser.add_argument("-scan", metavar='scan', type=int, help="scan number", default=0)
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    args = parser.parse_args()

    with sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) \
            as (sr7270_top, sr7270_bottom), \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) \
                    as npc3sg_input:
        try:
            thermovoltage_time = ThermovoltageTime(args.f, args.notes, args.device, args.scan, args.gain, args.rate,
                                                   args.max, args.pol, npc3sg_input, sr7270_bottom)
            thermovoltage_time.main()
        except KeyboardInterrupt:
            print('aborted via keyboard interrupt')
