import numpy as np
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt


class MidpointNormalize(Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        #  I'm ignoring masked values and all kind of edge cases for simplicity sake
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))


def plot(ax, im, voltage, max_val, min_val, plotlabel=None):
    norm = MidpointNormalize(midpoint=0, vmin=min_val, vmax=max_val)
    ax.imshow(voltage.T, norm=norm, cmap=plt.cm.coolwarm, interpolation='none', vmax=max_val, vmin=min_val, origin='lower')
    im.set_clim(min_val, max_val)


class ColorMapPlot:
    def __init__(self, fig, ax, data, norm=None, min_val=None, max_val=None, xlabel='x pixel', ylabel='y pixel',
                 plotlabel='', colorbar_label='', origin='lower'):
        self.fig = fig
        self.ax = ax
        self.data = data
        self.norm = norm
        self.min_val = min_val
        self.max_val = max_val
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.plotlabel = plotlabel
        self.colorbar_label = colorbar_label
        self.origin = origin
        self.im = self.ax.imshow(self.data.T, norm=self.norm, cmap=plt.cm.coolwarm, interpolation='nearest',
                                 origin=self.origin)
        self.im.set_clim(vmin=self.min_val)
        self.im.set_clim(vmax=self.max_val)
        self.clb = self.fig.colorbar(self.im, orientation='vertical', ax=self.ax)
        self.clb.set_label(self.colorbar_label, rotation=270, labelpad=20)
        self.ax.title.set_text(self.plotlabel)

    def show(self):
        self.fig.show()








