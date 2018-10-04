from scipy.optimize import curve_fit
import numpy as np

def linear(x, m, b):
    return m * x + b

def linear_fit(xdata, ydata):
    p, pcov = curve_fit(linear, xdata, ydata)
    m, b = p
    m_error, b_error = np.diag(pcov)
    return m, b, m_error, b_error

def proprotional(x, m):
    return m * x

def proprortional_fit(xdata, ydata):
    m, pcov = curve_fit(proprotional, xdata, ydata)
    return m[0], pcov[0]

