import contextlib
import usb.core
import usb.util
from optics.misc_utility import parser_tool

# This module uses PyUSB which can be accessed here: https://github.com/pyusb/pyusb with documentation at:
# http://pyusb.github.io/pyusb/


@contextlib.contextmanager
def create_endpoints(vendor, product):
    """This function creates endpoints for multiple SR7270 lock in amplifiers using the idVendor and idProduct which is
    notated in the hardware_addresses_and_constants module under hardware_control. It yields instances of the LockIn
    class for each lock in amplifier of the same idVendor and idProduct"""
    devs = []
    endpoints = []
    try:
        devices = tuple(usb.core.find(find_all=True, idVendor=vendor, idProduct=product))
        for i, dev in enumerate(devices):
            devs.append(dev)
            devs[i].set_configuration()
            cfg = devs[i].get_active_configuration()
            intf = cfg[(0, 0)]  # explicitly listing out everything for documentation purposes
            ep0 = intf[0]
            ep1 = intf[1]
            endpoints.append((ep0, ep1))
        yield (LockIn(dev, ep[0], ep[1]) for dev, ep in zip(devs, endpoints))
    finally:
        if devs:
            [usb.util.dispose_resources(dev) for dev in devs]  # disposes resources
        else:
            print('SR7270 lock in amplifier communication error')
            raise ValueError


class LockIn:
    """This is a class that controls the SR7270 lock in amplifier using USB commands listed in the Ametek manual
    Appendix E "Alphabetical Listing of Commands" which can be found in here:
    https://www.ameteksi.com/-/media/ameteksi/download_links/documentations/7270/197852-a-mnl-c.pdf"""
    def __init__(self, dev, ep0, ep1):
        self._dev = dev
        self._ep0 = ep0
        self._ep1 = ep1
        self._mode = self.check_reference_mode()

    def read(self):
        """Returns the parsed lock in amplifier outputs"""
        #  Parser tool clears out garbage collected by not bothering to use proper handshaking for sake of time
        #  Every command uses this function after every input command regardless of whether or not an output is
        #  necessary because the lock in sends a non-meaningful confirmation message which would otherwise be sent
        #  in the next read command
        return parser_tool.parse(''.join(chr(x) for x in self._dev.read(self._ep1, 100, 100)))

    def check_reference_mode(self):
        """Checks the reference mode of the lock in amplifier. Returns 0 if single reference, 1 if dual harmonic, and
        2 if dual reference mode"""
        self._ep0.write('REFMODE')
        return self.read()[0]

    def change_applied_voltage(self, millivolts, channel=3):
        """Changes the applied voltage of the DAC channel. Default is channel 3."""
        self._ep0.write('dac {} {}'.format(channel, millivolts / 10))
        #  it is unclear why the input needs to be divided by 10. The manual shows mV input but the command yields a
        #  voltage 10x higher
        self.read()  # throws away junk

    def read_applied_voltage(self, channel=3):
        """Reads the applied voltage of the DAC channel. Default is channel 3"""
        self._ep0.write('dac. {}'.format(channel))
        return self.read()[0]

    def change_oscillator_frequency(self, millihertz):
        """Changes the oscillator frequency for internal reference"""
        self._ep0.write('of {}'.format(millihertz))
        self.read()  # throws away junk

    def read_oscillator_frequency(self):
        """Reads the oscillator frequency for internal reference"""
        self._ep0.write('of.')
        return self.read()[0]

    def change_oscillator_amplitude(self, millivolts):
        """Changes the oscillator amplitude for the internal reference"""
        self._ep0.write('oa {}'.format(millivolts * 100))
        self.read()

    def read_oscillator_amplitude(self):
        """Read the oscillator amplitude for the internal reference in volts"""
        self._ep0.write('oa.')
        return self.read()[0]

    def read_xy1(self):
        """Reads XY1 of dual harmonic mode. Returns a list corresponding to [X1, Y1] in volts"""
        self._ep0.write('xy1.')
        return self.read()

    def read_xy2(self):
        """Reads XY2 of dual harmonic mode. Returns a list corresponding to [X1, Y1] in volts"""
        self._ep0.write('xy2.')
        return self.read()

    def read_xy(self):
        """Reads XY of single reference mode. Returns a list corresponding to [X, Y] in volts"""
        self._ep0.write('xy.')
        return self.read()

    def read_tc(self, channel=1):
        """Reads the time constant for a lock in amplifier in either the single reference or dual harmonic mode"""
        if self._mode == 0.0:
            self._ep0.write('tc.')
        if self._mode == 1.0:
            if channel == 1:
                self._ep0.write('tc1.')
            else:
                self._ep0.write('tc2.')
        return self.read()[0]

    def change_tc(self, seconds, channel=1):
        """Changes the time constant for a lock in amplifier in either the single reference or dual harmonic mode"""
        tc_value = {10e-06: 0, 20e-06: 1, 50e-06: 2, 100e-06: 3, 200e-06: 4, 500e-06: 5, 1e-03: 6, 2e-03: 7, 5e-03: 8,
                    10e-03: 9, 20e-03: 10, 50e-03: 11, 100e-03: 12, 200e-03: 13, 500e-03: 14, 1: 15, 2: 16, 5: 17,
                    10: 18, 20: 19, 50: 20, 100: 21, 200: 22, 500: 23, 1000: 24, 2000: 25, 5000: 26, 10000: 27,
                    20000: 28, 50000: 29, 100000: 30}
        if seconds not in tc_value:
            seconds = min(tc_value.items(), key=lambda x: abs(seconds - x[0]))[0]
        if self._mode == 0.0:
            self._ep0.write('tc {}'.format(tc_value[seconds]))
        if self._mode == 1.0:
            if channel == 1:
                self._ep0.write('tc1 {}'.format(tc_value[seconds]))
            else:
                self._ep0.write('tc2 {}'.format(tc_value[seconds]))
        self.read()  # throws away junk

    def read_r_theta(self):
        """Reads the magnitude and phase output. Returns a list corresponding to [R, Theta]"""
        self._ep0.write('mp.')
        return self.read()

    def read_adc(self, channel):
        """Reads auxillary analog-to-digital inputs with output in volts"""
        self._ep0.write('adc. {}'.format(channel))
        return self.read()

    def auto_phase(self):
        self._ep0.write('AQN')
        self.read()

    def change_sensitivity(self, millivolts, channel=1):
        VALID_SENSITIVITY = {2e-6: 1, 5e-6: 2, 1e-5: 3, 2e-5: 4, 5e-5: 5, 1e-4: 6, 2e-4: 7, 5e-4: 8, 1e-3: 9,
                             2e-3: 10, 5e-3: 11, 1e-2: 12, 2e-2: 13, 5e-2: 14, 0.1: 15, 0.2: 16, 0.5: 17, 1: 18,
                             2: 19, 5: 20, 10: 21, 20: 22, 50: 23, 100: 24, 200: 25, 500: 26, 1000: 27}
        if millivolts not in VALID_SENSITIVITY:
            millivolts = min(VALID_SENSITIVITY.items(), key=lambda x: abs(millivolts - x[0]))[0]
        if self._mode == 0.0:
            self._ep0.write('sen ' + str(VALID_SENSITIVITY[millivolts]))
        if self._mode == 1.0:
            if channel == 1:
                self._ep0.write('sen1 ' + str(VALID_SENSITIVITY[millivolts]))
            else:
                self._ep0.write('sen2 ' + str(VALID_SENSITIVITY[millivolts]))
        LockIn.read(self)
















