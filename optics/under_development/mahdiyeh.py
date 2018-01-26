import matplotlib
matplotlib.use('TkAgg')
from optics.hardware_control import sr7270, hardware_addresses_and_constants
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions
import matplotlib.gridspec as gridspec

def write_header(w):
    w.writerow(['gain:', args.gain])
    w.writerow(['notes:', args.notes])
    w.writerow(['end:', 'end of header'])
    w.writerow(['time', 'x_v', 'y_v'])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='iphotoX vs time. press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-imf", metavar='image filepath', type=str, help='filepath for image. must end'
                                                                         ' with .png also you must use two \\ '
                                                                         'in filepaths')
    parser.add_argument("-rate", metavar='rate', type=float, help='optional. samples/second. do not exceed 50')
    parser.add_argument("-max", metavar='max', type=float, help='max time (seconds)')
    parser.add_argument("-gain",metavar='gain', type=float, help="gain of amplifier")
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    args = parser.parse_args()

    with sr7270.create_endpoints_single(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as lock_in, \
        open(args.f, 'w', newline='') as fn:
        try:
            start_time = time.time()
            w = csv.writer(fn)
            write_header(w)
            fig = plt.figure()
            gs = gridspec.GridSpec(2, 1)
            ax1 = plt.subplot(gs[0, 0])
            ax2 = plt.subplot(gs[1, 0])
            ax1.title.set_text('X_1')
            ax2.title.set_text('Y_1')
            ax1.set_ylabel('voltage (uV)')
            ax2.set_ylabel('voltage (uV)')
            ax1.set_xlabel('time (s)')
            ax2.set_xlabel('time (s)')
            fig.show()
            max_voltage_x = 0
            min_voltage_x = 0
            max_voltage_y = 0
            min_voltage_y = 0
            if not args.rate:
                sleep = 3 * lock_in.read_tc()[0]
            else:
                sleep = 1/args.rate
            while time.time()-start_time < args.max:
                voltages = [conversions.convert_x_to_iphoto(x, args.gain) for x in sr7270_bottom.read_xy()]
                time.sleep(sleep)
                time_now = time.time()- start_time
                w.writerow([time_now, voltages[0], voltages[1]])
                ax1.scatter(time_now, voltages[0] * 1000000, c='c', s=2)
                ax2.scatter(time_now, voltages[1] * 1000000, c='c', s=2)

                if voltages[0] > max_voltage_x:
                    max_voltage_x = voltages[0]
                if voltages[0] < min_voltage_x:
                    min_voltage_x = voltages[0]

                if 0 < min_voltage_x < max_voltage_x:
                    ax1.set_ylim(min_voltage_x * 1000000 / 2, max_voltage_x * 2 * 1000000)
                if min_voltage_x < 0 < max_voltage_x:
                    ax1.set_ylim(min_voltage_x * 2 * 1000000, max_voltage_x * 2 * 1000000)
                if min_voltage_x < max_voltage_x < 0:
                    ax1.set_ylim(min_voltage_x * 2 * 1000000, max_voltage_x * 1 / 2 * 1000000)

                if voltages[1] > max_voltage_y:
                    max_voltage_y = voltages[1]
                if voltages[1] < min_voltage_y:
                    min_voltage_y = voltages[1]

                if min_voltage_y > 0 < max_voltage_y:
                    ax2.set_ylim(min_voltage_y * 1000000 / 2, max_voltage_y * 2 * 1000000)
                if min_voltage_y < 0 < max_voltage_y:
                    ax2.set_ylim(min_voltage_y * 2 * 1000000, max_voltage_y * 2 * 1000000)
                if min_voltage_y > max_voltage_y > 0:
                    ax2.set_ylim(min_voltage_y * 2 * 1000000, max_voltage_y * 1 / 2 * 1000000)

                plt.tight_layout()
                fig.canvas.draw()
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
        except KeyboardInterrupt:
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
            exit
