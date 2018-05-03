from optics.defunct import npc3sg_analog
from optics.hardware_control import sr7270, hardware_addresses_and_constants, pm100d
from optics.heating_measurement.heating_map import HeatingScan

if __name__ == "__main__":
    import argparse
    import argparse
    parser = argparse.ArgumentParser(description='sweep scan iphotoX. Press CTRL+C to quit')
    parser.add_argument("-f", metavar='data directory', type=str, help='directory for data files')
    parser.add_argument("-xc", metavar='x_center', type=float, help='x center position. default: 80', default=80)
    parser.add_argument("-yc", metavar='y_center', type=float, help='y center position. default: 80', default=80)
    parser.add_argument("-xr", metavar='x_range', type=float, help='x range. default: 160', default=160)
    parser.add_argument("-yr", metavar='y_range', type=float, help='y range. default: 160', default=160)
    parser.add_argument("-xd", metavar='x_scan_density', type=int, help='x pixel density. default: 15', default=15)
    parser.add_argument("-yd", metavar='y_scan_density', type=int, help='y pixel density. default: 15', default=15)
    parser.add_argument("-gain", metavar='gain', type=float, help="gain of amplifier")
    parser.add_argument("-pol", metavar='polarization', type=float, help='polarization of light in degrees')
    parser.add_argument("-device", metavar='device', type=str, help='device name')
    parser.add_argument("-scan", metavar='scan', type=int, help="scan number", default=0)
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    parser.add_argument("-bias", metavar='bias', type=float, help="DC bias in millivolts")
    parser.add_argument("-osc", metavar='osc', type=float, help="oscillator amplitude in mV")
    args = parser.parse_args()

    with npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) \
                    as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) \
                    as (sr7270_top, sr7270_bottom), \
            pm100d.connect(hardware_addresses_and_constants.pm100d_address) as powermeter:
        try:
            heating_scan = HeatingScan(args.f, args.notes, args.device, args.scan, args.gain, args.bias, args.osc,
                                       args.xd, args.yd, args.xr, args.yr, args.xc, args.yc, args.pol, npc3sg_x,
                                       npc3sg_y, npc3sg_input, sr7270_top, sr7270_bottom, powermeter)
            heating_scan.main()
        except KeyboardInterrupt:
            print('aborted via keyboard interrupt')
