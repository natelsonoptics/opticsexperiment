import matplotlib
matplotlib.use('TkAgg')
from optics.hardware_control import sr7270, npc3sg_analog, polarizer_controller, hardware_addresses_and_constants
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions


def write_header(w):
    w.writerow(['gain:', args.gain])
    w.writerow(['x laser position:', npc3sg_input.read()[0]])
    w.writerow(['y laser position:', npc3sg_input.read()[1]])
    w.writerow(['notes:', args.notes])
    w.writerow(['end:', 'end of header'])
    w.writerow(['time', 'polarization', 'x_v', 'y_v'])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='iphotoX vs polarization. press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-imf", metavar='image filepath', type=str, help='filepath for image. must end'
                                                                         ' with .png also you must use two \\ '
                                                                         'in filepaths')
    parser.add_argument("-gain",metavar='gain', type=float, help="gain of amplifier")
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    args = parser.parse_args()

    with sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as (sr7270_top, sr7270_bottom), \
        open(args.f, 'w', newline='') as fn,  \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input, \
            polarizer_controller.connect_tdc001(hardware_addresses_and_constants.tdc001_serial_number) as polarizer:
        try:
            start_time = time.time()
            w = csv.writer(fn)
            write_header(w)
            fig = plt.figure()
            ax1 = fig.add_subplot(211, projection='polar')
            ax2 = fig.add_subplot(212, projection='polar')
            ax1.title.set_text('X_1 (uV)')
            ax2.title.set_text('Y_1 (uV)')
            fig.show()
            max_voltage_x = 0
            min_voltage_x = 0
            max_voltage_y = 0
            min_voltage_y = 0
            waveplate_angle = int(round(float(str(polarizer.read_position())))) % 360
            max_angle = waveplate_angle + 180
            for i in range(waveplate_angle, max_angle):
                if i > 360:
                    i = i - 360
                polarizer.move(i)
                time.sleep(1.5)
                polarization = float(str(polarizer.read_position())) * 2  #  converts waveplate angle to polarizaiton angle
                voltages = [conversions.convert_x_to_iphoto(x, args.gain) for x in sr7270_bottom.read_xy()]
                time_now = time.time()- start_time
                w.writerow([time_now, polarization, voltages[0], voltages[1]])
                ax1.scatter(conversions.degrees_to_radians(polarization), abs(voltages[0]) * 1000000, c='c', s=2)
                ax2.scatter(conversions.degrees_to_radians(polarization), abs(voltages[1]) * 1000000, c='c', s=2)
                plt.tight_layout()
                fig.canvas.draw()
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
        except KeyboardInterrupt:
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
            exit