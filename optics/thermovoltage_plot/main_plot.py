import matplotlib.pyplot as plt
import pandas as pd

from optics.thermovoltage_plot.thermovoltage_plot import MidpointNormalize


def thermovoltagemapplot(voltage, plotlabel, max_val=None, min_val=None):
    norm = MidpointNormalize(midpoint=0, vmin=min_val, vmax=max_val)
    im = plt.imshow(voltage.T, norm=norm, cmap=plt.cm.coolwarm, interpolation='none', vmax=max_val, vmin=min_val, origin='lower')
    plt.suptitle(plotlabel)
    clb = plt.colorbar(im, orientation='vertical')
    clb.set_label('voltage (uV)', rotation=270, labelpad=20)
    im.set_clim(min_val, max_val)
    plt.show()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='plot array')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
    parser.add_argument("-min_val", metavar='min_val', type=float, help='minimum value for plot (uV)')
    parser.add_argument("-max_val", metavar='max_val', type=float, help='maximum value for plot (uV)')
    parser.add_argument("-plotlabel", metavar='plot_label', type=str, help='label for plot')
    args = parser.parse_args()

    with open(args.f) as fin:
        header={}
        for i, line in enumerate(fin):
            key, value = (token.strip() for token in line.split(":,", maxsplit=1))
            header[key] = value
            if key == 'end':
                break
        data = pd.read_csv(fin, sep=',')
        voltages = data['x_v'].values.reshape(int(header['y scan density']), int(header['x scan density']))
    thermovoltagemapplot((voltages.T) * 1000000, args.plotlabel, args.max_val, args.min_val)
