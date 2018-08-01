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

    def reset(self):
        self._inst.write('*RST')

    def configure_source(self, source_mode=0, compliance_level=0.1, output_level=0):
        """source_mode: 0 for voltage, 1 for current"""
        self._inst.write(':SOUR:FUNC {}'.format('VOLT' if source_mode == 0 else 'CURR'))
        self._inst.write(':SOUR:{} {}'.format('VOLT' if source_mode == 0 else 'CURR', output_level))
        self._inst.write(':{}:PROT {}'.format('CURR' if source_mode == 0 else 'VOLT', compliance_level))

    def configure_measurement(self, measurement_mode=0, auto_range=True, manual_range=1):
        """measurement_mode: 0 for voltage, 1 for current, 2 for resistance"""
        values = {0: 'VOLT', 1: 'CURR', 2: 'RES'}
        self._inst.write('SENS:{}:RANG:AUTO {}'.format(values[measurement_mode], 'ON' if auto_range else 'OFF'))
        if not auto_range:
            self._inst.write(':{}:RANG {}'.format(values[measurement_mode], manual_range))

    def display_measurement(self, displayed_measurement_mode=0):
        """displayed_measurement_mode: 0 for voltage, 1 for current, 2 for resistance"""
        values = {0: 15, 1: 22, 2: 29}
        self._inst.write(':SYST:KEY {}'.format(values[displayed_measurement_mode]))

    def enable_output(self, enabled=True):
        self._inst.write(':OUTP {}'.format('ON' if enabled else 'OFF'))

    def configure_multipoint(self, output_mode=0, arm_count=1, trigger_count=1):
        """output mode: 0 for fix, 1 for sweep, 2 for list"""
        values = {0: 'FIX', 1: 'SWE', 2: 'LIST'}
        self._inst.write(':ARM:COUN {}'.format(arm_count))
        self._inst.write(':TRIG:COUN {}'.format(trigger_count))
        self._inst.write(':SOUR:VOLT:MODE {}'.format(values[output_mode]))
        self._inst.write(':SOUR:CURR:MODE {}'.format(values[output_mode]))

    def configure_trigger(self, arming_source=0, timer_setting=0.01, trigger_source=0, trigger_delay=0):
        """arming_source: 0: immediate, 1: bus, 2: tim, 3: man, 4: tlin, 5: nst, 6L pst, 7:bst
        trigger_source: 0: immediate, 1 tlin"""
        arming_values = {0: 'IMM', 1: 'BUS', 2: 'TIM', 3: 'MAN', 4: 'TLIN', 5: "NST", 6: 'PST', 7: 'BST'}
        trigger_values = {0: 'IMM', 1: 'TLIN'}
        self._inst.write(':ARM:SOUR {}'.format(arming_values[arming_source]))
        self._inst.write(':ARM:TIM {}'.format(timer_setting))
        self._inst.write(':TRIG:SOUR {}'.format(trigger_values[trigger_source]))
        self._inst.write(':TRIG:DEL {}'.format(trigger_delay))

    def initiate(self):
        self._inst.write(':TRIG:CLE')  # clears trigger first
        self._inst.write(':INIT')  # initiates

    def fetch(self):
        self._inst.write(':FETC?')
        return self._inst.read()




