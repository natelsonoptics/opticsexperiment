import clr  # installs DOTNET DLLs
import sys

sys.path.append("C:\\Users\\NatLabUser\\Desktop\\python") #  adds DLL path to PATH

#  DOTNET (x64) DLLs. These need to be UNBLOCKED to be found (right click -> properties -> unblock
#  This uses Python For DotNet NOT IronPython

clr.AddReference("System")
clr.AddReference("Interop.JYCCDLib")
clr.AddReference("Interop.JYCONFIGBROWSERCOMPONENTLib")
clr.AddReference("Interop.JYSYSTEMLIBlib")

#  Import the namespaces as modules - they are going to look like these are invalid,  but they aren't

import JYCCDLib
import JYSYSTEMLIBLib
import time
import JYCONFIGBROWSERCOMPONENTLib


class CCDController:
    def __init__(self):
        self._ccd = JYCCDLib.JYMCDClass()
        self._name = None
        self._ypixels = None
        self._xpixels = None
        self._firmware_version = None
        self._out_parameter_integer = 1

    def initialize(self):
        self._ccd.Uniqueid = "CCD1"
        self._ccd.Load()
        self._ccd.OpenCommunications()
        self._ccd.Initialize(False, False)
        _, self._xpixels, self._ypixels = self._ccd.GetChipSize(self._out_parameter_integer,
                                                                self._out_parameter_integer)
        self._ccd.SetDefaultUnits(JYSYSTEMLIBLib.jyUnitsType.jyutTime, JYSYSTEMLIBLib.jyUnits.jyuMilliseconds)
        self._firmware_version = self._ccd.FirmwareVersion
        self._name = self._ccd.Name

    def get_ccd_temperature(self):
        return self._ccd.CurrentTemperature

    def disable_all_output_triggers(self):
        self._ccd.DisableAllOutputTriggers()

    def disable_input_triggers(self):
        self._ccd.DisableAllInputTriggers()

    def open_shutter(self):
        self._ccd.OpenShutter()

    def close_shutter(self):
        self._ccd.CloseShutter()

    def stop_acquisition(self):
        self._ccd.StopAcquisition()

    def start_acquisition(self, shutter_open):  # Bool
        self._ccd.StartAcquisition(shutter_open)












    #  TODO acquire single spectrum, get min max wavelength range, calculate pixels to wavelength,
    #  TODO enable output triggers, enable input triggers,
    #  TODO take time stamp, prepare single spectrum acquisition,
    #  TODO is spectrum ready for acquisition, start single spectrum acquisition, start single spectrum acquisition
    #  TODO is acquisition ready, stop single spectrum acquisition, read single spectrum acquisition
















