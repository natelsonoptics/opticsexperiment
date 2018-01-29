import matplotlib.pyplot as plt


def plot(ax, im, voltage, max_val, min_val, plotlabel=None):
    ax.imshow(voltage.T, cmap=plt.cm.coolwarm, interpolation='none', vmax=max_val, vmin=min_val, origin='lower')
    im.set_clim(min_val, max_val)