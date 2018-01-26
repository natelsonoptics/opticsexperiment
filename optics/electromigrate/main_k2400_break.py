import matplotlib
matplotlib.use('TkAgg')
from optics.hardware_control import keithley_k2400, hardware_addresses_and_constants
import time
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import numpy as np
from itertools import count
import csv
import os


def measure_current_resistance(steps, stop_voltage):
    resistance = []
    voltages = []
    currents = []
    for i in range(steps):
        voltage = stop_voltage * (i + 1) / steps
        keithley.set_voltage(voltage)
        time.sleep(0.1)
        currents.append(keithley.measure_current())
        time.sleep(0.1)
        voltages.append(keithley.measure_voltage())
        resistance.append(voltages[i] / currents[i])
        ax1.scatter(voltages[i], currents[i])
        ax1.set_ylim(np.amin(currents) * 0.9, np.amax(currents) * 1.1)
        ax1.title.set_text('Measuring resistance\nCurrent resistance: %s ohms' % np.ceil(resistance[i]))
        fig.canvas.draw()
    return resistance, voltages, currents, ax1


def linear(x, M, B):
    return M * x + B

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='iphotoX vs time. press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str,
                        help='filepath for data. '
                             'you must use two \\ in file path. filename WILL autoincrement', default='test')
    parser.add_argument("-desired_resistance", metavar='desired resistance', type=float,
                        help='resistance to stop program', default=100)
    parser.add_argument("-start_voltage_resistance", metavar='start voltage for measuring resistance',
                        help='optional. minimum voltage for measuring resistance', default=0.1)
    parser.add_argument("-stop_voltage_resistance", metavar='stop voltage for measuring resistance',
                        help='optional. max voltage for measuring resistance', default=0.5)
    parser.add_argument("-steps", metavar='steps', type=int, help='optional. steps to measure resistance', default=10)
    parser.add_argument("-break_voltage", metavar='break voltage', type=float,
                        help="optional. starting break voltage", default=1)
    parser.add_argument("-max_break_voltage", metavar='max break voltage', type=float,
                        help="optional. maximum break voltage", default=1.5)
    parser.add_argument("-delta_break_voltage", metavar=' delta break voltage', type=float,
                        help="optional. break voltage step size", default=0.05)
    parser.add_argument("-delta_voltage", metavar=' delta voltage', type=float,
                        help="optional. voltage step size", default=0.02)
    parser.add_argument("-percent_drop", metavar='percent drop', type=float,
                        help='optional. percent drop in current before aborting', default=0.4)
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    args = parser.parse_args()

    current_drop = False
    c = count(0)
    j = count(0)

    file = os.path.splitext(args.f)[0]

    while os.path.exists(file+'0') or os.path.exists(file+'0.csv'):
        file = file + '(1)'

    with keithley_k2400.connect(hardware_addresses_and_constants.keithley_address) as keithley:
        fig, (ax1, ax2, ax3) = plt.subplots(3)
        ax3.barh(1, 1, 0.35, color='w')
        ax1.title.set_text('Measured resistance: \nCurrent resistance: ')
        ax2.title.set_text('Breaking resistance: \nCurrent resistance: ')
        ax3.title.set_text('Percent of maximum current: ')
        ax3.set_xlim(0, 1)
        plt.tight_layout()
        fig.show()
        keithley.configure()
        while True:
            with open(file + '%s.csv' % next(j), 'w', newline='') as fn:
                w = csv.writer(fn)
                w.writerow(['resistance'])
                current_break_voltage = args.break_voltage
                # measure resistance
                current_resistance, voltage, current, ax1 = measure_current_resistance(args.steps, args.stop_voltage_resistance)
                p, pcov = curve_fit(linear, voltage, current)
                keithley.set_voltage(0)
                sweep_resistance = 1 / p[0]
                w.writerow([sweep_resistance])
                voltage_linspace = np.linspace(np.amin(voltage), np.amax(voltage), 100)
                ln2, = ax1.plot(voltage_linspace, linear(voltage_linspace, p[0], p[1]))
                ax1.title.set_text('Measured resistance: %s ohms\n ' % np.ceil(sweep_resistance))
                fig.canvas.draw()
                if sweep_resistance >= args.desired_resistance:
                    print('resistance reached desired resistance')
                    print('Final resistance: %s ohms' % np.ceil(sweep_resistance))
                    w.writerow([sweep_resistance])
                    keithley.set_voltage(0)
                    break
                if sweep_resistance < 0:
                    print('slope was negative')
                    print('Final resistance: %s ohms' % np.ceil(sweep_resistance))
                    w.writerow([sweep_resistance])
                    keithley.set_voltage(0)
                    break
                if current_drop:
                    print('current dropped')
                    print('Final resistance: %s ohms' % np.ceil(sweep_resistance))
                    w.writerow([sweep_resistance])
                    keithley.set_voltage(0)
                    break
                if args.break_voltage > args.max_break_voltage:
                    print('break voltage exceeded maximum value')
                    print('Final resistance: %s ohms' % np.ceil(sweep_resistance))
                    w.writerow([sweep_resistance])
                    keithley.set_voltage(0)
                    break

                #  break junction
                currents = []
                voltages = []
                while not current_drop:
                    for i, v in enumerate(np.arange(args.start_voltage_resistance, current_break_voltage,
                                                    args.delta_voltage)):
                        keithley.set_voltage(v)
                        ax3.barh(1, 1, 0.35, color='white')
                        currents.append(keithley.measure_current())
                        voltages.append(keithley.measure_voltage())
                        percent_max = currents[i] / np.amax(currents)
                        ax2.title.set_text('Breaking junction\nCurrent resistance: %s ohms'
                                           % np.ceil(voltages[i]/currents[i]))
                        ax3.barh(1, percent_max, 0.35)
                        ax3.set_xlim(0, 1)
                        ax2.scatter(voltages[i], currents[i])
                        ax2.set_ylim(np.amin(currents) * 0.5, np.amax(currents) * 1.5)
                        ax3.title.set_text('Percent of maximum current: %s %%' % np.ceil(percent_max * 100))
                        fig.canvas.draw()
                        if i > 0:
                            lower = (1 - args.percent_drop / 100) * voltages[i - 1] / currents[i - 1]
                            upper = (args.percent_drop / 100 + 1) * voltages[i - 1] / currents[i - 1]
                            if not lower < voltages[i] / currents[i] < upper:
                                current_drop = True
                                print('current dropped')
                                break
                    voltage_linspace = np.linspace(np.amin(voltages), np.amax(voltages), 100)
                    p, pcov = curve_fit(linear, voltages, currents)
                    ln, = ax2.plot(voltage_linspace, linear(voltage_linspace, p[0], p[1]))
                    fig.canvas.draw()
                    time.sleep(0.5)
                    keithley.set_voltage(0)
                    resistance = 1 / p[0]
                    ax2.title.set_text('Breaking resistance: %s ohms\n ' % np.ceil(resistance))
                    currents = []
                    voltages = []
                    ln.remove()
                    if resistance >= args.desired_resistance or resistance < 0:
                        plt.savefig(file + '%s.png' % next(c), format='png', bbox_inches='tight')
                        # saves an image of the completed data
                        ln2.remove()
                        break
                    current_break_voltage += args.delta_break_voltage
                    if current_break_voltage > args.max_break_voltage:
                        args.break_voltage += args.delta_break_voltage
                        plt.savefig(file + '%s.png' % next(c), format='png', bbox_inches='tight')
                        ln2.remove()
                        break


