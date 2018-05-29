import visa
from ThorlabsPM100 import ThorlabsPM100
import contextlib

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
        return self._power_meter.read * 4.8  # reads power on sample




