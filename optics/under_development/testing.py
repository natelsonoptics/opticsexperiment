import numpy as np
import matplotlib.pyplot as plt


def temperature(x, a, b, d):
    #if -10 < b < 10:
    #    return (-1 * abs(b) + 15) * np.exp(-(x-b)**2/(2*fwhm(-w/ 10 + 2* w)**2))
    #else:
    return a * np.exp(-(x - b) ** 2 / (2 * fwhm(d) ** 2)) + 300

def fwhm(d):
    return d / (2.35482 * 2)


def seebeck(x):
    #if -30 < x < 0:
    #    return - k * x + 1.6
    #if 0 <= x < 30:
    #    return k * x + 1.6
    #if -60 < x <= -30:
    #    return -1/2 * k * (x + 30) + k * 30 + 1.6
    #if 30 <= x < 60:
    #    return 1/2 * k * (x - 30) + k * 30 + 1.6
    #if -90 < x <= -60:
    #    return -1/4 * k * (x + 60) + k * 30 + 1.6 + 1/2 * k * 30
    #if 60 <= x < 90:
    #    return 1/4 * k * (x - 60) + k * 30 + 1.6 + 1/2 * k * 30
    #if -90 < x < 90:
    #    return k * np.cos(1/60 * x) + 1.6
    #if -150 <= x < 0:
    #    return k1 * abs(x) + 1.6
    #    return 1.5
    #if 0 <= x <= 150:
        #return k * abs(x) + 1.6
        #return -k * np.cos(1/45 * x) + 1.6
    #    return 1.65
    #if -150 <= x <= -90:
    #    return 1.6
    #if 90 <= x <= 150:
    #    return 1.6
    return k * abs(x) + 1.6


def lin(xo):
    return np.linspace(0, 150, 10000)


def lin2(xo):
    return np.linspace(-150, 0, 10000)


k = 0.5
k1 = 0.5
linspace = np.linspace(-150, 150, 10000)


q = np.linspace(-120, 120, 1000)  # beam location
a = 5 # T(x) amplitude
w = 1 # T(x) diameter
for i in q:
    plt.scatter(i, -np.trapz([seebeck(t) for t in linspace[1::]] * np.diff(temperature(linspace, a, i, w)),
                             linspace[1::]), c='b')
    plt.scatter(i, -np.trapz([seebeck(t) for t in lin2(0)[1::]] * np.diff(temperature(linspace, a, i, w)),
                             lin2(0)[1::]) - -np.trapz([seebeck(t) for t in lin(0)[1::]] * np.diff(temperature(linspace, a, i, w)),
                             lin(0)[1::]), c='r')
plt.xlabel('um')
plt.ylabel('uV')
plt.show()
plt.plot(linspace, [seebeck(i) for i in linspace])
plt.xlabel('um')
plt.ylabel('uV/K')
plt.show()
plt.plot(np.linspace(-3 * w, 3 * w, 100), temperature(np.linspace(-3 * w, 3 * w, 100), a, 0, w))
plt.ylabel('K')
plt.show()






