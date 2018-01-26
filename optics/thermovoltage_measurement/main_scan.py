import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
from optics.hardware_control import sr7270, npc3sg_analog, hardware_addresses_and_constants
from optics.misc_utility import scanner, conversions
import csv
import time
import numpy as np
import matplotlib.pyplot as plt
from optics.thermovoltage_plot import thermovoltage_plot
from tkinter import *
import warnings
import os
from os import path


def write_header(w):
    w.writerow(['gain:', args.gain])
    w.writerow(['x scan density:', args.xd])
    w.writerow(['y scan density:', args.yd])
    w.writerow(['x range:', args.xr])
    w.writerow(['y range:', args.yr])
    w.writerow(['x center:', args.xc])
    w.writerow(['y center:', args.yc])
    w.writerow(['polarization:', args.pol])
    w.writerow(['notes:', args.notes])
    w.writerow(['end:', 'end of header'])
    w.writerow(['x_raw', 'y_raw', 'x_v', 'y_v', 'x_pixel', 'y_pixel'])


def setup_plots():
    norm = thermovoltage_plot.MidpointNormalize(midpoint=0)
    im1 = ax1.imshow(z1.T, norm=norm, cmap=plt.cm.coolwarm, interpolation='none', origin='lower')
    clb1 = fig.colorbar(im1, ax=ax1)
    clb1.set_label('voltage (uV)', rotation=270, labelpad=20)
    im2 = ax2.imshow(z2.T, norm=norm, cmap=plt.cm.coolwarm, interpolation='none', origin='lower')
    clb2 = fig.colorbar(im2, ax=ax2)
    clb2.set_label('voltage (uV)', rotation=270, labelpad=20)
    ax1.title.set_text('X_1')
    ax2.title.set_text('Y_1')
    return ax1, ax2, im1, im2


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
    args = parser.parse_args()

    os.makedirs(args.f, exist_ok=True)
    index = args.scan
    file = path.join(args.f, '{}_{}_{}{}'.format(args.device, args.pol, index, '.csv'))
    imagefile = path.join(args.f, '{}_{}_{}{}'.format(args.device, args.pol, index, '.png'))
    while path.exists(file):
        index += 1
        file = path.join(args.f, '{}_{}_{}{}'.format(args.device, args.pol, index, '.csv'))
        imagefile = path.join(args.f, '{}_{}_{}{}'.format(args.device, args.pol, index, '.png'))

    with open(file, 'w', newline='') as inputfile, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) as (sr7270_top, sr7270_bottom):
        try:
            w = csv.writer(inputfile)
            z1 = np.zeros((args.xd, args.yd))
            z2 = np.zeros((args.xd, args.yd))
            fig, (ax1, ax2) = plt.subplots(2)
            ax1, ax2, im1, im2 = setup_plots()
            fig.show()
            write_header(w)
            x_val, y_val = scanner.find_scan_values(args.xc, args.yc, args.xr, args.yr, args.xd, args.yd)
            for y_ind, i in enumerate(y_val):
                npc3sg_y.move(i)
                for x_ind, j in enumerate(x_val):
                    npc3sg_x.move(j)
                    time.sleep(0.3)
                    raw = sr7270_bottom.read_xy()
                    voltages = [conversions.convert_x_to_iphoto(x, args.gain) for x in raw]
                    w.writerow([raw[0], raw[1], voltages[0], voltages[1], x_ind, y_ind])
                    z1[x_ind][y_ind] = voltages[0] * 1000000
                    z2[x_ind][y_ind] = voltages[1] * 1000000
                    update_plot(im1, z1, -np.amax(np.abs(z1)), np.amax(np.abs(z1)))
                    update_plot(im2, z2, -np.amax(np.abs(z2)), np.amax(np.abs(z2)))
                    plt.tight_layout()
                    fig.canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
            npc3sg_x.move(0)
            npc3sg_y.move(0)
            thermovoltage_plot.plot(ax1, im1, z1, np.amax(np.abs(z1)), -np.amax(np.abs(z1)))
            thermovoltage_plot.plot(ax2, im2, z2, np.amax(np.abs(z2)), -np.amax(np.abs(z2)))
            plt.savefig(imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
            thermovoltage_plot.plot(ax1, im1, z1, np.amax(np.abs(z1)), -np.amax(np.abs(z1)))
            thermovoltage_plot.plot(ax2, im2, z2, np.amax(np.abs(z2)), -np.amax(np.abs(z2)))
            fig.show()  # shows the completed scan
            warnings.filterwarnings("ignore", ".*GUI is implemented.*")  # this warning relates to code \
            # that was never written
            cid = fig.canvas.mpl_connect('button_press_event', onclick)  # click on pixel to move laser position there
            plt.pause(-1)  # keeps the figure open indefinitely until you close it
        except KeyboardInterrupt:
            plt.savefig(imagefile, format='png', bbox_inches='tight')  # saves an image of the completed data
            npc3sg_x.move(0)
            npc3sg_y.move(0)
        except TclError:  # this is an annoying error that requires you to have tkinter events in mainloop
            pass
