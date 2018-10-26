import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from optics.misc_utility import parser_tool, conversions
import time
from optics.thermovoltage_plot import thermovoltage_plot


def find_scan_values(x_center, y_center, x_range, y_range, x_scan_density, y_scan_density):
    x_min = x_center - (x_range / 2) if x_center - (x_range / 2) >= 0 else 0
    x_max = x_center + (x_range / 2) if x_center + (x_range / 2) <= 160 else 160
    y_min = y_center - (y_range / 2) if y_center - (y_range / 2) >= 0 else 0
    y_max = y_center + (y_range / 2) if y_center + (y_range / 2) <= 160 else 160

    x_val = np.round(np.linspace(x_min, x_max, x_scan_density), 2)
    y_val = np.round(np.linspace(y_min, y_max, y_scan_density), 2)
    return x_val, y_val


def scan(x_val, y_val, w, z1, z2, fig, ax1, ax2, im1, im2, npc3sg_x, npc3sg_y, sr7270_bottom, gain):
    for y_ind, i in enumerate(y_val):
        npc3sg_y.move(i)
        for x_ind, j in enumerate(x_val):
            npc3sg_x.move(j)
            time.sleep(0.3)
            voltages = [conversions.convert_x_to_iphoto(x, gain) for x in
                        parser_tool.parse(sr7270_bottom.read_xy())]
            w.writerow([voltages[0], voltages[1], x_ind, y_ind])
            z1[x_ind][y_ind] = voltages[0] * 1000000
            z2[x_ind][y_ind] = voltages[1] * 1000000
            thermovoltage_plot.plot(ax1, im1, z1, np.amax(np.abs(z1)), -np.amax(np.abs(z1)))
            thermovoltage_plot.plot(ax2, im2, z2, np.amax(np.abs(z2)), -np.amax(np.abs(z2)))
            plt.tight_layout()
            fig.canvas.draw()  # dynamically plots the data and closes automatically after completing the scan
    return z1, z2
