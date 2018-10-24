import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='plot iphoto vs time')
    parser.add_argument("-f", metavar='data filepath', type=str, help='filepath for data. must end '
                                                                      'with .csv also you must use two \\ '
                                                                      'in filepaths')
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
    plt.scatter(data["power"]*1000, data['x_v']*1000000)
    plt.suptitle(args.plotlabel)
    plt.xlabel('power (mW)')
    plt.ylabel('voltage (uV)')
    plt.xlim(np.amin(data['power']) * 1000 * 0.95, np.amax(data['power'] * 1000 * 1.05))
    if np.amin(data["x_v"]) < 0 < np.amax(data["x_v"]):
        plt.ylim(3 * np.amin(data["x_v"]) * 1000000, 3 * np.amax(data["x_v"])* 1000000)
    if np.amin(data["x_v"]) > 0 :
        plt.ylim(1/3 * np.amin(data["x_v"])* 1000000, 3 * np.amax(data["x_v"])* 1000000)
    if 0 > np.amax(data["x_v"]):
        plt.ylim(3 * np.amin(data["x_v"])* 1000000, 1/3 * np.amax(data["x_v"])* 1000000)
    plt.show()