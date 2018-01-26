import matplotlib
matplotlib.use('Qt4Agg')
from optics.hardware_control import sr7270, npc3sg_analog, hardware_addresses_and_constants
from optics.misc_utility import scanner, conversions
import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from tkinter import *
import warnings

def write_header(w, applied_voltage):
    w.writerow(['gain:', args.gain])
    w.writerow(['x scan density:', args.xd])
    w.writerow(['y scan density:', args.yd])
    w.writerow(['x range:', args.xr])
    w.writerow(['y range:', args.yr])
    w.writerow(['x center:', args.xc])
    w.writerow(['y center:', args.yc])
    w.writerow(['notes:', args.notes])
    w.writerow(['applied voltage:', applied_voltage])
    w.writerow(['osc amplitude:', sr7270_top.read_oscillator_amplitude()[0]])
    w.writerow(['osc frequency:', sr7270_top.read_oscillator_frequency()[0]])
    w.writerow(['time constant:', sr7270_bottom.read_tc()[0]])
    w.writerow(['top time constant:', sr7270_top.read_tc1()[0]])
    w.writerow(['end:', 'end of header'])
    w.writerow(['x_raw', 'y_raw', 'x_iphoto', 'y_iphoto', 'x_pixel', 'y_pixel'])


def setup_plots():
    im1 = ax1.imshow(z1.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
    clb1 = fig.colorbar(im1, ax=ax1)
    clb1.set_label('current (mA)', rotation=270, labelpad=20)
    im2 = ax2.imshow(z2.T, cmap=plt.cm.coolwarm, interpolation='nearest', origin='lower')
    clb2 = fig.colorbar(im2, ax=ax2)
    clb2.set_label('current (mA)', rotation=270, labelpad=20)
    ax1.title.set_text('iphoto X')
    ax2.title.set_text('iphoto Y')
    return ax1, ax2, im1, im2


def plot_heating(ax, im, voltage, max_val, min_val, plotlabel=None):
    ax.imshow(voltage.T, cmap=plt.cm.coolwarm, interpolation='none', vmax=max_val, vmin=min_val, origin='lower')
    im.set_clim(min_val, max_val)


def update_plot(im, data, min_val, max_val):
    im.set_data(data.T)
    im.set_clim(vmin=min_val)
    im.set_clim(vmax=max_val)


def onclick(event):
    points = [int(np.ceil(event.xdata-0.5)), int(np.ceil(event.ydata-0.5))]
    npc3sg_x.move(x_val[points[0]])
    npc3sg_y.move(y_val[points[1]])
    print('pixel: ' + str(points))
    print('position: ' + str(x_val[points[0]]) + ', ' + str(y_val[points[1]]))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='sweep scan iphotoX. Press CTRL+C to quit')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-imf", metavar='image filepath', type=str, help='filepath for image. must end'
                                                                         ' with .png also you must use two \\ '
                                                                         'in filepaths')
    parser.add_argument("-xc", metavar='x_center', type=float, help='x center position')
    parser.add_argument("-yc", metavar='y_center', type=float, help='y center position')
    parser.add_argument("-xr", metavar='x_range', type=float, help='x range')
    parser.add_argument("-yr", metavar='y_range', type=float, help='y range')
    parser.add_argument("-xd", metavar='x_scan_density', type=int, help='x pixel density')
    parser.add_argument("-yd", metavar='y_scan_density', type=int, help='y pixel density')
    parser.add_argument("-gain", metavar='gain', type=float, help="gain of amplifier")
    parser.add_argument("-bias", metavar='bias', type=float, help="DC bias in millivolts")
    parser.add_argument("-osc", metavar='osc', type=float, help="oscillator amplitude in mV")
    parser.add_argument("-notes", metavar='notes', type=str, help='notes must be in double quotation marks')
    args = parser.parse_args()

    with open(args.f, 'w', newline='') as fn, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as (sr7270_top, sr7270_bottom):
        try:
            w = csv.writer(fn)
            z1 = np.zeros((args.xd, args.yd))
            z2 = np.zeros((args.xd, args.yd))
            fig, (ax1, ax2) = plt.subplots(2)
            ax1, ax2, im1, im2 = setup_plots()
            fig.show()
            sr7270_top.change_applied_voltage(args.bias)
            time.sleep(0.1)
            write_header(w, sr7270_top.read_applied_voltage()[0])
            x_val, y_val = scanner.find_scan_values(args.xc, args.yc, args.xr, args.yr, args.xd, args.yd)
            if not args.osc:
                sr7270_top.change_oscillator_amplitude(3)
            else:
                sr7270_top.change_oscillator_amplitude(args.osc)
            for y_ind, i in enumerate(y_val):
                npc3sg_y.move(i)
                for x_ind, j in enumerate(x_val):
                    npc3sg_x.move(j)
                    time.sleep(0.3)
                    raw = sr7270_bottom.read_xy()
                    current = [conversions.convert_x_to_iphoto(x, args.gain) for x in raw]
                    w.writerow([raw[0], raw[1], current[0], current[1], x_ind, y_ind])
                    z1[x_ind][y_ind] = current[0] * 1000
                    z2[x_ind][y_ind] = current[1] * 1000
                    update_plot(im1, z1, np.amin(z1), np.amax(z1))
                    update_plot(im2, z2, np.amin(z2), np.amax(z2))
                    plt.tight_layout()
                    fig.canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
            npc3sg_x.move(0)
            npc3sg_y.move(0)
            sr7270_top.change_applied_voltage(0)
            plot_heating(ax1, im1, z1, np.amax(z1), np.amin(z1))
            plot_heating(ax2, im2, z2, np.amax(z2), np.amin(z2))
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
            plot_heating(ax1, im1, z1, np.amax(z1), np.amin(z1))
            plot_heating(ax2, im2, z2, np.amax(z2), np.amin(z2))
            fig.show()  # shows the completed scan
            warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
            # that was never written
            cid = fig.canvas.mpl_connect('button_press_event', onclick)  # click on pixel to move laser position there
            plt.pause(-1)   # keeps the figure open indefinitely until you close it
        except KeyboardInterrupt:
            plt.savefig(args.imf, format='png', bbox_inches='tight')  # saves an image of the completed data
            npc3sg_x.move(0)
            npc3sg_y.move(0)
            sr7270_top.change_applied_voltage(0)
        except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
            pass
