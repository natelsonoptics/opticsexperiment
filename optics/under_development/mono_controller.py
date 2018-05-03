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
        self._unique_id = None
        self._out_parameter_string = str(1)
        self._mono = None
        self._grating = None
        self._blazes = None
        self._description = None
        self._current_grating = None
        self._current_blazes = None
        self._current_description = None
        self._wavelength = None
        self._slit_width = None
        self._current_turret = None

    def initialize(self):
        self._cb.Load()
        self._unique_id = self._cb.GetFirstMono(self._out_parameter_string)
        self._mono = JYMONOLib.MonochromatorClass()
        self._mono.Uniqueid = self._unique_id[0]
        self._mono.Load()
        self._mono.OpenCommunications()
        self._mono.Initialize(False, False)

        time.sleep(1)

        self._current_turret = self._mono.GetCurrentTurret()
        _, grating_density, self._grating, self._blazes, self._description = self._mono.GetCurrentGratingWithDetails(1, 1, 1, 1)
        self._current_grating = self._grating[self._current_turret]
        self._current_blazes = self._blazes[self._current_turret]
        self._current_description = self._description[self._current_turret]

        self._mono.SetDefaultUnits(JYSYSTEMLIBLib.jyUnitsType.jyutWavelength, JYSYSTEMLIBLib.jyUnits.jyuNanometers)
        self._wavelength = self._mono.GetCurrentWavelength()

        self._mono.SetDefaultUnits(JYSYSTEMLIBLib.jyUnitsType.jyutSlitWidth, JYSYSTEMLIBLib.jyUnits.jyuMillimeters)
        self._slit_width = self._mono.GetCurrentSlitWidth(JYSYSTEMLIBLib.SlitLocation.Front_Entrance)

    def set_wavelength(self, wavelength):
        self._mono.MovetoWavelength(wavelength)

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

        self._mono.MovetoTurret(turret_index)

    def is_busy(self): #TODO get rid of this
        return self._mono.IsBusy()

    #TODO GetMinMaxRange

mono = MonoController()
mono.initialize()
print(mono.read_wavelength())