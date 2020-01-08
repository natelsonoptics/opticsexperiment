import clr  # installs DOTNET DLLs
import contextlib
import sys
import time

from optics.hardware_control.hardware_addresses_and_constants import polarizer_offset, waveplate_offset

sys.path.append("C:\\Program Files (x86)\\Thorlabs\\Kinesis") #  adds DLL path to PATH

#  DOTNET (x64) DLLs. These need to be UNBLOCKED to be found (right click -> properties -> unblock
#  This uses Python For DotNet NOT IronPython

clr.AddReference("Thorlabs.MotionControl.TCube.DCServoCLI")  # TDC001 DLL
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI")  # KDC101 DLL
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
clr.AddReference("Thorlabs.MotionControl.TCube.DCServoUI")
clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
clr.AddReference("System")

#  Import the namespaces as modules - they are going to look like these are invalid,  but they aren't

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.TCube.DCServoCLI import TCubeDCServo  # TDC001
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo  # KDC101
from System import Decimal


@contextlib.contextmanager
def connect_tdc001(serial_number, waveplate=False):
    device = None
    try:
        DeviceManagerCLI.BuildDeviceList()
        # Tell the device manager to get the list of all devices connected to the computer
        serial_numbers = DeviceManagerCLI.GetDeviceList(TCubeDCServo.DevicePrefix)
        # get available TCube DC Servos and check our serial number is correct
        if str(serial_number) not in serial_numbers:
            raise ValueError("Device is not connected.")
        device = TCubeDCServo.CreateTCubeDCServo(str(serial_number))
        device.Connect(str(serial_number))
        device.WaitForSettingsInitialized(5000)
        if not device.IsSettingsInitialized():
            raise ValueError("Device initialization timeout")
        device.LoadMotorConfiguration(str(serial_number))
        device.StartPolling(250)
        device.EnableDevice()
        motorSettings = device.LoadMotorConfiguration(str(serial_number))
        currentDeviceSettings = device.MotorDeviceSettings
        if waveplate:
            yield WaveplateController(device)
        else:
            yield PolarizerController(device)
    finally:
        if device:
            device.Disconnect()
        else:
            print('TDC101 waveplate controller communication error')
            raise ValueError


@contextlib.contextmanager
def connect_kdc101(serial_number, waveplate=True):
    device = None
    try:
        DeviceManagerCLI.BuildDeviceList() # Tell the device manager to get the list of all devices connected to the computer
        serial_numbers = DeviceManagerCLI.GetDeviceList(KCubeDCServo.DevicePrefix)
        # get available KCube Servos and check our serial number is correct
        if str(serial_number) not in serial_numbers:
            raise ValueError("Device is not connected.")
        device = KCubeDCServo.CreateKCubeDCServo(str(serial_number))
        device.Connect(str(serial_number))
        device.WaitForSettingsInitialized(5000)
        if not device.IsSettingsInitialized():
            raise ValueError("Device initialization timeout")
        device.LoadMotorConfiguration(str(serial_number))
        device.StartPolling(250)
        device.EnableDevice()
        motorSettings = device.LoadMotorConfiguration(str(serial_number))  # This is important to leave in, but I'm not sure
        # why
        currentDeviceSettings = device.MotorDeviceSettings  # This is important to leave in, but I'm not sure why
        if waveplate:
            yield WaveplateController(device)
        else:
            yield PolarizerController(device)
    finally:
        if device:
            device.Disconnect()
        else:
            print('KDC101 waveplate controller communication error')
            raise ValueError

class RotatorMountController:
    def __init__(self, device):
        self._device = device

    def read_position(self, wait_ms=0):
        time.sleep(wait_ms/1000)
        position = float(str(self._device.Position))
        return position

    def home(self):
        self._device.Home(self._device.InitializeWaitHandler())

    def move(self, position):
        while position > 360:
            position -= 360
        self._device.MoveTo(Decimal(position), self._device.InitializeWaitHandler())
        # this is a System.Decimal!


class WaveplateController(RotatorMountController):
    def __init__(self, device):
        self._device = device
        super().__init__(self._device)

    def move_nearest(self, position):
        current_position = self.read_position()
        i = 0
        for i in range(180):
            if position % 90 - 0.5 < (current_position + i) % 90 < position % 90 + 0.5:
                break
        self.move(current_position + i)

    def read_polarization(self, wait_ms=0):
        return self.read_position(wait_ms) * 2


class PolarizerController(RotatorMountController):
    def __init__(self, device):
        self._device = device
        super().__init__(self._device)
        self._polarizer_offset = polarizer_offset

    def move(self, position):
        calibrated_position = self._polarizer_offset * position  # There is an offset of around 1.183 times the value
        # due to slipping of the CR1Z6 mount
        # This should be changed once a new motor is purchased
        self._device.MoveTo(Decimal(calibrated_position), self._device.InitializeWaitHandler())
        # this is a System.Decimal!

    def move_nearest(self, position):
        calibrated_position = self._polarizer_offset * position
        current_position = float(str(self._device.Position))
        if position in (0, 45):
            if calibrated_position - 1.1 < current_position % (90 * self._polarizer_offset) < calibrated_position + 1.1:
                return None
            for i in range(180):
                if calibrated_position - 1.1 < (current_position + i) % (90 * self._polarizer_offset) \
                        < calibrated_position + 1.1:
                    break
        else:
            if calibrated_position - 1.1 < current_position % (180 * self._polarizer_offset) \
                    < calibrated_position + 1.1:
                return None
            for i in range(180):
                if calibrated_position - 1.1 < (current_position + i) % (180 * self._polarizer_offset) \
                        < calibrated_position + 1.1:
                    break
        #self._device.MoveRelative(MotorDirection.Forward, Decimal(i), self._device.InitializeWaitHandler())
        new_position = current_position + i
        self._device.MoveTo(Decimal(new_position), self._device.InitializeWaitHandler())
        # this is a System.Decimal!

    def read_polarization(self, wait_ms=0):
        return self.read_position(wait_ms) / self._polarizer_offset

