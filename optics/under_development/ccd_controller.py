import clr  # installs DOTNET DLLs
import sys
import datetime
import numpy as np
import time
import matplotlib.pyplot as plt


sys.path.append("C:\\Users\\NatLabUser\\Desktop\\python") #  adds DLL path to PATH

#  DOTNET (x64) DLLs. These need to be UNBLOCKED to be found (right click -> properties -> unblock
#  This uses Python For DotNet NOT IronPython

clr.AddReference("System")
clr.AddReference("Interop.JYCONFIGBROWSERCOMPONENTLib")
clr.AddReference("Interop.JYCCDLib")
clr.AddReference("Interop.JYSYSTEMLIBlib")

import JYCCDLib
import JYSYSTEMLIBLib

class CCDController:
    def __init__(self, unique_id='CCD1'):
        self._ccd = JYCCDLib.JYMCDClass()
        self._unique_id = unique_id

    def set_unique_id(self):
        self._ccd.Uniqueid = self._unique_id

    def load(self):
        self._ccd.Load()

    def open_communications(self):
        self._ccd.OpenCommunications()

    def initialize(self):
        self._ccd.Initialize(False, False)

    def read_chip_size(self):
        _, xpixels, ypixels = self._ccd.GetChipSize(1, 1)
        return xpixels, ypixels

    def set_default_units(self):
        self._ccd.SetDefaultUnits(JYSYSTEMLIBLib.jyUnitsType.jyutTime, JYSYSTEMLIBLib.jyUnits.jyuMilliseconds)

    def read_firmware_version(self):
        return self._ccd.FirmwareVersion

    def read_ccd_name(self):
        return self._ccd.Name

    def set_integration_time(self, seconds):
        self._ccd.IntegrationTime = seconds * 1000  #  milliseconds

    def set_adc(self):
        self._ccd.SelectADC(JYSYSTEMLIBLib.jyADCType.JY_ADC_16_BIT)

    def set_gain(self, gain):
        self._ccd.Gain = gain

    def read_gain(self):
        return self._ccd.Gain

    def set_acquisition_format(self):
        self._ccd.DefineAcquisitionFormat(JYSYSTEMLIBLib.jyCCDDataType.JYMCD_ACQ_FORMAT_SCAN, 1)

    def set_area(self, size):
        self._ccd.DefineArea(1, 1, 120, size, 16, 1, 16)

    def read_data_size(self):
        return self._ccd.DataSize

    def set_acquisition_mode(self, boolean=True):
        self._ccd.MultiAcqHardwareMode = boolean

    def set_operating_mode(self):
        self._ccd.SetOperatingModeValue(JYSYSTEMLIBLib.jyDeviceOperatingMode.jyDevOpModeNormal, False)

    def set_acquisition_count(self, counts=1):
        self._ccd.AcquisitionCount = counts

    def is_ready(self):
        return self._ccd.ReadyForAcquisition

    def is_busy(self):
        return self._ccd.AcquisitionBusy()

    def read_temperature(self):
        return self._ccd.CurrentTemperature

    def open_shutter(self):
        self._ccd.OpenShutter()

    def close_shutter(self):
        self._ccd.CloseShutter()

    def take_timestamp(self):
        return str(datetime.datetime.now())

    def start_acquisition(self, shutter_boolean=True):
        self._ccd.StartAcquisition(shutter_boolean)

    def stop_acquisition(self):
        self._ccd.StopAcquisition()

    def read_result(self):
        r = self._ccd.GetResult()
        if r:
            o = JYSYSTEMLIBLib.IJYResultsObject.GetFirstDataObject(r)
            if o:
                d = JYSYSTEMLIBLib.IJYDataObject.GetRawData(o)
                return np.array([i for i in d])
        else:
            pass

    def enable_output_triggers(self):
        """Turns on TTL trigger outputs on CCD. This is a bunch of JY COM code access"""
        trig_address, trig_address_string = self._ccd.GetFirstSupportedOutputTriggerAddress()
        event_ptr, trig_event_string = self._ccd.GetFirstSupportedOutputTriggerEvent(trig_address)
        trig_signal_type, trig_signal_type_string = self._ccd.GetFirstSupportedOutputTriggerSignalType(trig_address, event_ptr)
        event_ptr = JYSYSTEMLIBLib.jyTriggerEvent.jyTrigEventOnStart
        trig_signal_type = JYSYSTEMLIBLib.jyTriggerSignalType.jyTRigSigTypeTTLHigh
        self._ccd.EnableOutputTrigger(trig_address, event_ptr, trig_signal_type)

    def disable_output_triggers(self):
        """Turns off TTL trigger outputs on CCD"""
        self._ccd.DisableAllOutputTriggers()

    def enable_input_triggers(self):
        trig_address, trig_address_string = self._ccd.GetFirstSupportedInputTriggerAddress()
        event_ptr, trig_event_string = self._ccd.GetFirstSupportedInputTriggerEvent(trig_address)
        trig_signal_type, trig_signal_type_string = self._ccd.GetFirstSupportedInputTriggerSignalType(trig_address,
                                                                                                      event_ptr)
        event_ptr = JYSYSTEMLIBLib.jyTriggerEvent.jyTrigEventOnStart
        trig_signal_type = JYSYSTEMLIBLib.jyTriggerSignalType.jyTRigSigTypeTTLHigh
        self._ccd.EnableInputTrigger(trig_address, event_ptr, trig_signal_type)

    def disable_input_triggers(self):
        self._ccd.DisableAllInputTriggers()


class CCDController2(CCDController):
    def __init__(self):
        super().__init__()
        self.set_unique_id()
        self.load()
        self.open_communications()
        self.initialize()
        self.set_default_units()
        time.sleep(1)
        self._xpixels, _ = self.read_chip_size()

    def take_spectrum(self, integration_time_seconds=1, gain=1, scans=1, shutter_open=True):
        self.set_integration_time(integration_time_seconds)
        self.set_adc()
        self.set_gain(gain)
        self.set_acquisition_format()
        self.set_area(self._xpixels)
        data_size = self.read_data_size()
        raw_data = np.zeros([scans, data_size])
        self.set_acquisition_mode(True)
        self.set_operating_mode()
        self.set_acquisition_count(scans)
        for j in range(scans):
            while not self.is_ready():
                time.sleep(0.1)
            self.start_acquisition(shutter_open)
            while self.is_busy():
                time.sleep(0.1)
            raw_data[j] = self.read_result()
        averaged_data = np.mean(np.array([i for i in raw_data]), axis=0)
        return raw_data, averaged_data

    def stop(self):
        self.stop_acquisition()




# TODO getminmaxwavelengthrange
# TODO convert pixels to wavelength
# TODO intensity
# TODO Spectrum
