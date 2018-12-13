import contextlib
import serial
import time

@contextlib.contextmanager
def connect_laser(serial_port='COM7'):
    ser = None
    try:
        ser = serial.Serial(serial_port, 115200, xonxoff=False, timeout=0.4, write_timeout=0.1)
        yield Laser(ser)
    finally:
        if ser:
            ser.close()


class Laser:
    def __init__(self, ser):
        self._ser = ser

    def write(self, message):
        self._ser.write(('{}\r'.format(message)).encode())
        return self.read()

    def read_raw(self):
        return self._ser.read(50).decode().split('\r\n')

    def read(self):
        message = self._ser.read(50).decode().split('\r\n')
        return [i for i in message if i != 'CMD>' if i != '' if i != 'CMD> ' if '%' not in i]

    def read_temperature(self):
        data = self.write('sh temp')[0]
        return float((data.split(' = ')[1]).split(' C')[0])

    def read_fine_status(self):
        return self.write('sta fine')[0]

    def read_power_level(self):
        data = self.write('sh level pow')
        ch1 = float((data[0].split(':')[1]).split(' mW')[0])
        ch2 = float((data[1].split(':')[1]).split(' mW')[0])
        return ch1, ch2

    def read_system_temperature(self):
        data = self.write('sh temp sys')[0]
        return float(((data.split(' = '))[1]).split(' C')[0])

    def read_current(self):
        data = self.write('sh curr')[0]
        return float(data.split(' = ')[1].split(' mA')[0])

    def turn_off(self):
        self.write('la off')
        print('laser {}'.format(self.read_laser_status()))

    def turn_on(self):
        self.write('la on')
        print('laser {}'.format(self.read_laser_status()))

    def set_fine_status(self, on=True, a=80, b=10, power=120):
        if on:
            self.set_power(2, 0)
            time.sleep(0.5)
            self.set_power(1, 0)
            time.sleep(0.5)
            self.write('fine a 0')
            time.sleep(0.5)
            self.write('fine b 0')
            time.sleep(0.5)
            self.write('fine on')
            time.sleep(0.5)
            self.write('fine a {}'.format(a))
            time.sleep(0.5)
            self.write('fine b {}'.format(b))
            time.sleep(0.5)
            self.set_power(1, power)
        else:
            self.write('fine off')

    def set_power(self, channel, power):
        self.write('ch {} pow {}'.format(channel, power))

    def read_laser_status(self):
        return self.write('sta la')[0]


if __name__ == '__main__':
    import csv
    import os
    import datetime
    from optics.hardware_control.hardware_addresses_and_constants import laser_log_path

    filename = os.path.join(laser_log_path, '{} laser log.csv'.format(str(datetime.date.today())))
    try:
        with connect_laser() as laser:
            if os.path.exists(filename):
                with open(filename, 'a', newline='') as inputfile:
                    writer = csv.writer(inputfile)
                    writer.writerow([str(datetime.datetime.now()), 'ok', laser.read_laser_status(), laser.read_system_temperature(), laser.read_temperature(),
                                     laser.read_fine_status(), laser.read_current(),
                                     laser.read_power_level()[0], laser.read_power_level()[1]])
            else:
                with open(filename, 'w', newline='') as inputfile:
                    writer = csv.writer(inputfile)
                    writer.writerow(['time', 'communication status', 'laser status', 'system temperature (C)', 'laser temperature (C)', 'FINE mode status',
                                     'current (mA)', 'channel 1 power level (mW)', 'channel 2 power level (mW)'])
                    writer.writerow([str(datetime.datetime.now()), 'ok', laser.read_laser_status(), laser.read_system_temperature(), laser.read_temperature(),
                                     laser.read_fine_status(), laser.read_current(),
                                     laser.read_power_level()[0], laser.read_power_level()[1]])
    except:
        if os.path.exists(filename):
            with open(filename, 'a', newline='') as inputfile:
                writer = csv.writer(inputfile)
                writer.writerow([str(datetime.datetime.now()), 'not connected'])
        else:
            with open(filename, 'w', newline='') as inputfile:
                writer = csv.writer(inputfile)
                writer.writerow(['time', 'communication status', 'laser status', 'system temperature (C)', 'laser temperature (C)',
                                 'FINE mode status',
                                 'current (mA)', 'channel 1 power level (mW)', 'channel 2 power level (mW)'])
                writer.writerow(
                    [str(datetime.datetime.now()), 'not connected'])






