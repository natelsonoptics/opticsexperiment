import matplotlib

from optics.defunct import npc3sg_analog
from optics.hardware_control import sr7270, pm100d, attenuator_wheel, hardware_addresses_and_constants

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions


def write_header(w):
    w.writerow(['gain:', args.gain])
    w.writerow(['x laser position:', npc3sg_input.read()[0]])
    w.writerow(['y laser position:', npc3sg_input.read()[1]])
    w.writerow(['applied voltage:', sr7270_top.read_applied_voltage()[0]])
    w.writerow(['osc amplitude:', sr7270_top.read_oscillator_amplitude()[0]])
    w.writerow(['osc frequency:', sr7270_top.read_oscillator_frequency()[0]])
    w.writerow(['time constant:', sr7270_bottom.read_tc()[0]])
    w.writerow(['top time constant:', sr7270_top.read_tc1()[0]])
    w.writerow(['notes:', args.notes])
    w.writerow(['end:', 'end of header'])
    w.writerow(['time', 'power', 'x_raw', 'y_raw', 'x_v', 'y_v'])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='iphotoX vs intensity. press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-imf", metavar='image filepath', type=str, help='filepath for image. must end'
                                                                         ' with .png also you must use two \\ '
                                                                         'in filepaths')
    parser.add_argument("-steps", metavar='step', type=int, help='steps of attenuator stepper motor per sample')
    parser.add_argument("-max", metavar='max', type=float, help='max time (seconds)')
    parser.add_argument("-gain",metavar='gain', type=float, help="gain of amplifier")
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    parser.add_argument("-bias", metavar='bias', type=float, help="DC bias in millivolts. optional")
    parser.add_argument("-osc", metavar='osc', type=float, help="oscillator amplitude in mV. optional")
    args = parser.parse_args()

    with attenuator_wheel.create_do_task(hardware_addresses_and_constants.attenuator_wheel_outputs) as motor, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as (sr7270_top, sr7270_bottom), \
            open(args.f, 'w', newline='') as fn,  \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input, \
            pm100d.connect(hardware_addresses_and_constants.pm100d_address) as power_meter:
        try:
            start_time = time.time()
            w = csv.writer(fn)
            if args.bias:
                sr7270_top.change_applied_voltage(args.bias)
            if args.osc:
                sr7270_top.change_oscillator_amplitude(args.osc)
            write_header(w)
            fig, (ax1, ax2, ax3) = plt.subplots(3)
            ax1.title.set_text('X')
            ax2.title.set_text('Y')
            ax3.title.set_text('Power on sample')
            ax1.set_ylabel('voltage (uV)')
            ax2.set_ylabel('voltage (uV)')
            #ax1.set_ylabel('iphoto (mA)')
            #ax2.set_ylabel('iphoto (mA)')
            ax3.set_ylabel('power (mW)')
            ax1.set_xlabel('time (s)')
            ax2.set_xlabel('time (s)')
            ax3.set_xlabel('time (s)')
            fig.show()
            max_voltage_x = 0
            min_voltage_x = 0
            max_voltage_y = 0
            min_voltage_y = 0
            max_power = 0
            min_power = 0
            while time.time()-start_time < args.max:
                motor.step(args.steps, 0.005)
                time.sleep(0.1)
                time_now = time.time() - start_time
                power = power_meter.read_power()
                raw = sr7270_bottom.read_xy()
                voltages = [conversions.convert_x_to_iphoto(x, args.gain) for x in raw]
                w.writerow([time_now, power, raw[0], raw[1], voltages[0], voltages[1]])
                #if args.main_thermovoltage_measurement:
                ax1.scatter(time_now, voltages[0] * 1000000, c='b', s=2)
                ax2.scatter(time_now, voltages[1] * 1000000, c='b', s=2)
                #else:
                #ax1.scatter(time_now, voltages[0] * 1000, c='b', s=2)
                #ax2.scatter(time_now, voltages[1] * 1000, c='b', s=2)
                ax3.scatter(time_now, power * 1000, c='b', s=2)

                if voltages[0] > max_voltage_x:
                    max_voltage_x = voltages[0]
                if voltages[0] < min_voltage_x:
                    min_voltage_x = voltages[0]

                if min_voltage_x > 0 < max_voltage_x:
                    ax1.set_ylim(min_voltage_x * 1000000 / 2, max_voltage_x * 2 * 1000000)
                if min_voltage_x < 0 < max_voltage_x:
                    ax1.set_ylim(min_voltage_x * 2 * 1000000, max_voltage_x * 2 * 1000000)
                if min_voltage_x > max_voltage_x > 0:
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

                if power > max_power:
                    max_power = power
                if power < min_power:
                    min_power = power
                ax3.set_ylim(min_power * 1 / 2 * 1000, max_power * 2 * 1000)

                plt.tight_layout()
                fig.canvas.draw()
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
        except KeyboardInterrupt:
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
            exit


