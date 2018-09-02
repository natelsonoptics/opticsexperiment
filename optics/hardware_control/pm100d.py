import visa
from ThorlabsPM100 import ThorlabsPM100
import contextlib
from optics.hardware_control.hardware_addresses_and_constants import  power_factor

@contextlib.contextmanager
def connect(address):
    rm = visa.ResourceManager()
    inst = rm.open_resource(address)
    try:
        yield PowerMeter(ThorlabsPM100(inst=inst))
    finally:
        inst.close()


class PowerMeter:
    def __init__(self, power_meter):
        self._power_meter = power_meter

    def read_raw(self):
        return self._power_meter.read

    def read_power(self):
        return self._power_meter.read * power_factor  # reads power on sample




