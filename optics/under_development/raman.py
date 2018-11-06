from optics.under_development.ccd_controller import CCDController2
from optics.under_development.mono_controller import MonoController

class RamanSystem:
    def __init__(self):
        self._mono = MonoController()
        self._ccd = CCDController2()
        self._gain = {'high light': 0, 'best dynamic range': 1, 'high sensitivity': 2}

