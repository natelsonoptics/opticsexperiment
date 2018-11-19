from optics.hardware_control.hardware_addresses_and_constants import keithley_address
from optics.hardware_control.keithley_k2400 import connect
import time

with connect(keithley_address) as q:
    q.reset()
    for i in range(25):
        q.set_voltage(i*4)
        time.sleep(3)
        print(i)

