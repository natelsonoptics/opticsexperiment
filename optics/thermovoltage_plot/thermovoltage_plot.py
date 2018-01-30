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
    ax.imshow(voltage.T, norm=norm, cmap=plt.cm.coolwarm, interpolation='nearest', vmax=max_val, vmin=min_val, origin='lower')
    im.set_clim(min_val, max_val)


class ColorMapPlot:
    def __init__(self, data, fig=None, ax=None, norm=None, min_val=None, max_val=None, xlabel='x pixel', ylabel='y pixel',
                 plotlabel='', colorbar_label='', origin='lower', plotlabelsize=12, axesfontsize=12):
        self.fig = fig
        self.ax = ax
        if not self.fig or not self.ax:
            self.fig, self.ax = plt.subplots()
        self.data = data
        self.norm = norm
        self.min_val = min_val
        self.max_val = max_val
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.plotlabel = plotlabel
        self.colorbar_label = colorbar_label
        self.axesfontsize = axesfontsize
        self.plotlabelsize = plotlabelsize
        self.origin = origin
        self.im = self.ax.imshow(self.data.T, norm=self.norm, cmap=plt.cm.coolwarm, interpolation='nearest',
                                 origin=self.origin)
        self.im.set_clim(vmin=self.min_val, vmax=self.max_val)
        self.clb = self.fig.colorbar(self.im, orientation='vertical', ax=self.ax)
        self.clb.set_label(self.colorbar_label, rotation=270, labelpad=20)
        self.ax.title.set_text(self.plotlabel)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.title.set_fontsize(self.plotlabelsize)
        self.ax.xaxis.label.set_fontsize(self.axesfontsize)
        self.ax.yaxis.label.set_fontsize(self.axesfontsize)

    def show(self):
        self.fig.show()

class ScatterPlot:
    def __init__(self, x, y, fig=None, ax=None, xmin=None, xmax=None, ymin=None, ymax=None, plotlabel='', xlabel='',
                 ylabel='', color='k', shape='o', size=10, plotlabelsize=12, axesfontsize=12):
        self.x = x
        self.y = y
        self.fig = fig
        self.ax = ax
        if not self.fig or not self.ax:
            self.fig, self.ax = plt.subplots()
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.plotlabel = plotlabel
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.color = color
        self.shape = shape
        self.size = size
        self.plotlabelsize = plotlabelsize
        self.axesfontsize = axesfontsize
        if self.ymin or self.ymax:
            self.ax.set_ylim(self.ymin, self.ymax)
        if self.xmin or self.xmax:
            self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.scatter(self.x, self.y, c=self.color, s=self.size, marker=self.shape)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.title.set_text(self.plotlabel)
        self.ax.title.set_fontsize(self.plotlabelsize)
        self.ax.xaxis.label.set_fontsize(self.axesfontsize)
        self.ax.yaxis.label.set_fontsize(self.axesfontsize)

    def show(self):
        self.fig.show()










