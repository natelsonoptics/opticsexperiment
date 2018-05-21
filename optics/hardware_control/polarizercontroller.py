import clr  # installs DOTNET DLLs
import contextlib
import sys
import time

from optics.hardware_control.hardware_addresses_and_constants import polarizer_offset

sys.path.append("C:\\Program Files\\Thorlabs\\Kinesis") #  adds DLL path to PATH

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
def connect_tdc001(serial_number):
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
        yield PolarizerController(device)
    finally:
        if device:
            device.Disconnect()
        else:
            print('TDC101 polarizer controller communication error')
            raise ValueError


@contextlib.contextmanager
def connect_kdc101(serial_number):
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
        yield PolarizerController(device)
    finally:
        if device:
            device.Disconnect()
        else:
            print('KDC101 polarizer controller communication error')
            raise ValueError


class PolarizerController:
    def __init__(self, device):
        self._device = device
        self._polarizer_offset = polarizer_offset

    def move(self, position):
        calibrated_position = self._polarizer_offset * position  # This is from Xifan and I making sure that the CR1-Z6
        # read the *same*
        # value as it displayed. There is an offset of around 1.183 times the value due to slipping.
        # This should be changed once a new motor is purchased
        self._device.MoveTo(Decimal(calibrated_position), self._device.InitializeWaitHandler())
        # this is a System.Decimal!

    def move_nearest(self, position):
        calibrated_position = self._polarizer_offset * position  # This is from Xifan and I making sure that the CR1-Z6
        # read the *same*
        # value as it displayed. There is an offset of around 1.183 times the value due to slipping.
        # This should be changed once a new motor is purchased
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

    def home(self):  # you will need to home the device to reset the new 0 because you cannot give an input position
        # value larger than 359 degrees
        self._device.Home(self._device.InitializeWaitHandler())

    def read_waveplate_position(self, wait_ms=0):
        time.sleep(wait_ms/1000)
        calibrated_position = float(str(self._device.Position)) / self._polarizer_offset
        return calibrated_position  # polarization is 2 times this value!

    def read_polarization(self, wait_ms=0):
        waveplate = self.read_waveplate_position(wait_ms)
        return waveplate * 2
