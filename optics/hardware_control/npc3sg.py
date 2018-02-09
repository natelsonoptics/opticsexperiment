import optics.hardware_control.daq as daq
import contextlib
import time

# The NPC3SG piezo controller is controlled using DAQ input and output.
# To move the piezo controller, simply use daq.create_ao_task
# To convert piezo voltage to piezo position, use this function


class NPC3SGReader:
    def __init__(self, multiple_ai):
        self._multiple_ai = multiple_ai

    def read(self):
        time.sleep(0.1)
        voltage = self._multiple_ai.readAll()
        return [voltage[i] / 10 * 160 for i in voltage]


@contextlib.contextmanager
def connect_input(ai_channels):
    multiple_ai = daq.MultiChannelAnalogInput(ai_channels)
    multiple_ai.configure()
    try:
        yield NPC3SGReader(multiple_ai)
    finally:
        print('done')