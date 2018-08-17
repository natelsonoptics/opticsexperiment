from scipy.optimize import curve_fit
import numpy as np

def linear(x, m, b):
    return m * x + b

def linear_fit(xdata, ydata):
    p, pcov = curve_fit(linear, xdata, ydata)
    m, b = p
    m_error, b_error = np.diag(pcov)
    return m, b, m_error, b_error


