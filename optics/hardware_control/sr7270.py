import contextlib

import usb.core
import usb.util

from optics.misc_utility import parser_tool


@contextlib.contextmanager
def create_endpoints(vendor, product):
    devices = tuple(usb.core.find(find_all=True, idVendor=vendor, idProduct=product))
    dev_bottom = devices[0]
    dev_bottom.set_configuration()
    cfg = dev_bottom.get_active_configuration()
    intf = cfg[(0, 0)]
    ep0_bottom = intf[0]
    ep1_bottom = intf[1]
    dev_top = devices[1]
    dev_top.set_configuration()
    cfg2 = dev_top.get_active_configuration()
    intf2 = cfg2[(0, 0)]
    ep0_top = intf2[0]
    ep1_top = intf2[1]
    try:
        yield LockIn(dev_top, ep0_top, ep1_top), LockIn(dev_bottom, ep0_bottom, ep1_bottom)
    finally:
        usb.util.dispose_resources(dev_bottom)
        usb.util.dispose_resources(dev_top)


@contextlib.contextmanager
def create_endpoints_single(vendor, product):
    dev = usb.core.find(idVendor = vendor, idProduct = product)
    dev.set_configuration()
    cfg = dev.get_active_configuration()
    intf = cfg[(0,0)]
    ep0 = intf[0]
    ep1 = intf[1]
    try:
        yield LockIn(dev, ep0, ep1)
    finally:
        usb.util.dispose_resources(dev)


class LockIn:
    def __init__(self, dev, ep0, ep1):
        self._dev = dev
        self._ep0 = ep0
        self._ep1 = ep1

    def read(self):
        return parser_tool.parse(''.join(chr(x) for x in self._dev.read(self._ep1, 100, 100)))

    #def read_dev(self):
    #    return self._dev.read(self._ep1, 100, 100)

    def change_applied_voltage(self, millivolts):
        self._ep0.write('dac 3 ' + str(millivolts / 10))
        LockIn.read(self)  # throws away junk

    def read_applied_voltage(self):
        self._ep0.write('dac. 3')
        return LockIn.read(self)

    def change_oscillator_frequency(self, millihertz):
        self._ep0.write('of ' + str(millihertz))
        LockIn.read(self)  # throws away junk

    def read_oscillator_frequency(self):
        self._ep0.write('of.')
        return LockIn.read(self)

    def change_oscillator_amplitude(self, millivolts):
        value = millivolts
        self._ep0.write('oa ' + str(value * 100))
        LockIn.read(self)

    def read_oscillator_amplitude(self):
        self._ep0.write('oa.')
        return LockIn.read(self)

    def read_xy1(self):
        self._ep0.write('xy1.')
        return LockIn.read(self)

    def read_xy2(self):
        self._ep0.write('xy2.')
        return LockIn.read(self)

    def read_xy(self):
        self._ep0.write('xy.')
        return LockIn.read(self)

    def read_tc(self):  # this is used for bottom lock-in
        self._ep0.write('tc.')
        return LockIn.read(self)

    def read_tc1(self):  # this is used for top lock-in
        self._ep0.write('tc1.')
        return LockIn.read(self)

    def change_tc(self, seconds):
        tc_value = {10e-06: 0, 20e-06: 1, 50e-06: 2, 100e-06: 3, 200e-06: 4, 500e-06: 5, 1e-03: 6, 2e-03: 7, 5e-03: 8,
                    10e-03: 9, 20e-03: 10, 50e-03: 11, 100e-03: 12, 200e-03: 13, 500e-03: 14, 1: 15, 2: 16, 5: 17,
                    10: 18, 20: 19, 50: 20, 100: 21, 200: 22, 500: 23, 1000: 24, 2000: 25, 5000: 26, 10000: 27,
                    20000: 28, 50000: 29, 100000: 30}
        if seconds not in tc_value:
            seconds = min(tc_value.items(), key=lambda x: abs(seconds - x[0]))[0]
        self._ep0.write('tc ' + str(tc_value[seconds]))
        LockIn.read(self)  # throws away junk

    def change_tc1(self, seconds):
        tc_value = {10e-06: 0, 20e-06: 1, 50e-06: 2, 100e-06: 3, 200e-06: 4, 500e-06: 5, 1e-03: 6, 2e-03: 7, 5e-03: 8,
                    10e-03: 9, 20e-03: 10, 50e-03: 11, 100e-03: 12, 200e-03: 13, 500e-03: 14, 1: 15, 2: 16, 5: 17,
                    10: 18, 20: 19, 50: 20, 100: 21, 200: 22, 500: 23, 1000: 24, 2000: 25, 5000: 26, 10000: 27,
                    20000: 28, 50000: 29, 100000: 30}
        if seconds not in tc_value:
            seconds = min(tc_value.items(), key=lambda x: abs(seconds - x[0]))[0]
        self._ep0.write('tc1 ' + str(tc_value[seconds]))
        LockIn.read(self)  # throws away junk

    def read_r_theta(self):
        self._ep0.write('mp.')
        return LockIn.read(self)
















