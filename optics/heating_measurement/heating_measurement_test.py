import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import time
import csv
from optics.misc_utility import conversions
import os
from os import path


def conditional_function(field, func, *args):
    if field:
        return getattr(field, func)(*args)


class Measurements:
    def __init__(self, npc3sg_input, npc3sg_x, npc3sg_y, sr7270_dual_harmonic, sr7270_single_reference, powermeter,
                 attenuatorwheel, polarizer):
        self._npc3sg_input = npc3sg_input
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._sr7270_dual_harmonic = sr7270_dual_harmonic
        self._sr7270_single_reference = sr7270_single_reference
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._polarizer = polarizer


class Maps(Measurements):
    def __init__(self):
        super().__init__()






