import clr  # installs DOTNET DLLs
import sys

sys.path.append("C:\\Users\\NatLabUser\\Desktop\\python\\SynerJY DLL") #  adds DLL path to PATH

#  DOTNET (x64) DLLs. These need to be UNBLOCKED to be found (right click -> properties -> unblock
#  This uses Python For DotNet NOT IronPython

clr.AddReference("System")
clr.AddReference("Interop.JYCCDLib")
clr.AddReference("Interop.JYCONFIGBROWSERCOMPONENTLib")
clr.AddReference("Interop.JYMONOLib")
clr.AddReference("Interop.JYSYSTEMLIBlib")

#  Import the namespaces as modules - they are going to look like these are invalid,  but they aren't

import JYCCDLib
import JYMONOLib

integration_time = 1

gain = {'High Light': 0, 'Best Dynamic Range': 1, 'High Sensitivity': 2}

ccd = JYCCDLib.JYMCDClass()

