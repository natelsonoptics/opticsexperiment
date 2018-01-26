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
