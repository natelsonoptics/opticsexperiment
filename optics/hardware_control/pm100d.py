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

if __name__ == '__main__':
    import csv
    import os
    import datetime
    from optics.hardware_control.hardware_addresses_and_constants import power_log_path, pm100d_address

    filename = os.path.join(power_log_path, '{} laser log.csv'.format(str(datetime.date.today())))
    try:
        with connect(pm100d_address) as powermeter:
            if os.path.exists(filename):
                with open(filename, 'a', newline='') as inputfile:
                    writer = csv.writer(inputfile)
                    writer.writerow([str(datetime.datetime.now()), powermeter.read_raw()])
            else:
                with open(filename, 'w', newline='') as inputfile:
                    writer = csv.writer(inputfile)
                    writer.writerow(['time', 'raw power'])
                    writer.writerow([str(datetime.datetime.now()), powermeter.read_raw()])
    except:
        if os.path.exists(filename):
            with open(filename, 'a', newline='') as inputfile:
                writer = csv.writer(inputfile)
                writer.writerow([str(datetime.datetime.now()), 'not connected'])
        else:
            with open(filename, 'w', newline='') as inputfile:
                writer = csv.writer(inputfile)
                writer.writerow(['time', 'raw power'])
                writer.writerow(
                    [str(datetime.datetime.now()), 'not connected'])





