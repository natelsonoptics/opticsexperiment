import contextlib

import visa


@contextlib.contextmanager
def connect(address):
    rm = visa.ResourceManager()
    rm.list_resources()
    inst = rm.open_resource(address)
    try:
        yield SourceMeter(inst)
    finally:
        pass


class SourceMeter:
    def __init__(self, inst):
        self._inst = inst

    def configure(self):
        self._inst.write(':SOUR:FUNC VOLT')
        self._inst.write(":SOUR:VOLT:MODE FIXED")
        self._inst.write(':SOUR:VOLT:RANG 1')
        self._inst.write(':SENS:CURR:PROT 0.1')  # sets compliance to 100 mA
        self._inst.write(':SENS:CURR:RANG 0.1')

    def measure_current(self):
        # self._inst.write(':SENS:CURR:RANG 0.1')
        self._inst.write(':SENS:FUNC "CURR"')
        self._inst.write(':FORM:ELEM CURR')
        self._inst.write(':OUTP ON')
        self._inst.write(':READ?')
        return float(self._inst.read())

    def measure_voltage(self):
        self._inst.write(':SENS:FUNC "VOLT"')
        self._inst.write(':FORM:ELEM VOLT')
        self._inst.write(':OUTP ON')
        self._inst.write(':READ?')
        return float(self._inst.read())

    def set_voltage(self, voltage):
        self._inst.write(':SOUR:VOLT:LEV ' + str(voltage))