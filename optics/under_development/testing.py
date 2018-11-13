import numpy as np
import matplotlib.pyplot as plt


def temperature(x, b):
    return 5 * np.exp(-(x-b)**2/(2*4.2466**2))

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
    #    return -1/50 * k * (x + 60) + k * 30 + 1.6 + 1/2 * k * 30
    #if 60 <= x < 90:
    #    return 1/50 * k * (x - 60) + k * 30 + 1.6 + 1/2 * k * 30
    if -90 < x < 90:
        return np.abs(x)**(1/1.5) * k + 1.6
    if -150 <= x <= -90:
        return 1.6
    if 90 <= x <= 150:
        return 1.6

def lin(xo):
    return np.linspace(-150, xo, 10000)

def lin2(xo):
    return np.linspace(xo, 150, 10000)

k = 1
linspace = np.linspace(-150, 150, 10000)

q = np.linspace(-130, 130, 100)

for i in q:
#    plt.scatter(i, np.trapz([seebeck(t) for t in lin(i)[1::]] * np.diff(temperature(lin(i), i)), lin(i)[1::]) +
#                np.trapz([seebeck(t) for t in lin2(i)[1::]] * np.diff(temperature(lin2(i), i)), lin2(i)[1::]))
    plt.scatter(i, -np.trapz([seebeck(t) for t in linspace[1::]] * np.diff(temperature(linspace, i)), linspace[1::]))
    plt.plot(linspace, [0 for i in linspace])
    plt.axvline(0)
    #plt.ylim(-0.1, 0.1)
#plt.plot(linspace, [seebeck(i) for i in linspace])
plt.show()
plt.scatter(linspace, [seebeck(i) for i in linspace])
plt.axvline(0)
plt.show()
print(seebeck(0))







