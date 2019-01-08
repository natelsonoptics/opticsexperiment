import clr  # installs DOTNET DLLs
import sys

sys.path.append("C:\\Users\\NatLabUser\\Desktop\\python") #  adds DLL path to PATH

#  DOTNET (x64) DLLs. These need to be UNBLOCKED to be found (right click -> properties -> unblock
#  This uses Python For DotNet NOT IronPython

clr.AddReference("System")
clr.AddReference("Interop.JYCONFIGBROWSERCOMPONENTLib")
clr.AddReference("Interop.JYMONOLib")
clr.AddReference("Interop.JYSYSTEMLIBlib")

#  Import the namespaces as modules - they are going to look like these are invalid,  but they aren't

import JYMONOLib
import JYSYSTEMLIBLib
import time
import JYCONFIGBROWSERCOMPONENTLib

class MonoController:
    def __init__(self):
        self._cb = JYCONFIGBROWSERCOMPONENTLib.JYConfigBrowerInterfaceClass()
        self._out_parameter_string = str(1)
        self._cb.Load()
        self._unique_id = self._cb.GetFirstMono(self._out_parameter_string)
        self._mono = JYMONOLib.MonochromatorClass()
        self._mono.Uniqueid = self._unique_id[0]
        self._mono.Load()
        self._mono.OpenCommunications()
        self._mono.Initialize(False, False)
        time.sleep(1)
        self._current_turret = self._mono.GetCurrentTurret()
        _, grating_density, self._grating, self._blazes, self._description = \
            self._mono.GetCurrentGratingWithDetails(1, 1, 1, 1)
        self._current_grating = self._grating[self._current_turret]
        self._current_blazes = self._blazes[self._current_turret]
        self._current_description = self._description[self._current_turret]
        self._mono.SetDefaultUnits(JYSYSTEMLIBLib.jyUnitsType.jyutWavelength, JYSYSTEMLIBLib.jyUnits.jyuNanometers)
        self._wavelength = self._mono.GetCurrentWavelength()
        self._mono.SetDefaultUnits(JYSYSTEMLIBLib.jyUnitsType.jyutSlitWidth, JYSYSTEMLIBLib.jyUnits.jyuMillimeters)
        self._slit_width = self._mono.GetCurrentSlitWidth(JYSYSTEMLIBLib.SlitLocation.Front_Entrance)

    def get_current_turret(self):
        self._current_turret = self._mono.GetCurrentTurret()
        _, density, grating, blazes, description = self._mono.GetCurrentGratingWithDetails(1, 1, 1, 1)
        self._current_grating = grating[self._current_turret]
        self._current_blazes = blazes[self._current_turret]
        self._current_description = description[self._current_turret]
        return density, self._current_grating, self._current_blazes, self._current_description

    def set_wavelength(self, wavelength):
        self._mono.MovetoWavelength(wavelength)
        self._wavelength = wavelength

    def read_wavelength(self):
        self._wavelength = self._mono.GetCurrentWavelength()
        return self._wavelength

    def set_front_slit_width(self, width):
        self._mono.MovetoSlitWidth(JYSYSTEMLIBLib.SlitLocation.Front_Entrance, width)

    def read_front_slit_width(self):
        return self._mono.GetCurrentSlitWidth(JYSYSTEMLIBLib.SlitLocation.Front_Entrance)

    def set_turret(self, turret_index):
        self._current_turret = turret_index
        self._current_grating = self._grating[self._current_turret]
        self._current_blazes = self._blazes[self._current_turret]
        self._current_description = self._description[self._current_turret]
        while not self.is_ready():
            time.sleep(2)
        self._mono.MovetoTurret(turret_index)
        while self.is_busy():
            time.sleep(2)
        return self._current_turret, self._current_grating, self._current_blazes, self._current_description

    def is_busy(self):
        return self._mono.IsBusy()

    def is_ready(self):
        return self._mono.IsReady()

    def stop(self):
        return self._mono.Stop()

    def reboot(self):
        self._mono.RebootDevice()

    #TODO GetMinMaxRange
