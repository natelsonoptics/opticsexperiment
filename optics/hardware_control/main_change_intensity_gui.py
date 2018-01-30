#!/usr/bin/python3

import tkinter as tk

from optics.gui.gui_builds import SetupGUI
from optics.hardware_control import attenuator_wheel, pm100d, hardware_addresses_and_constants

if __name__ == '__main__':
    root = tk.Tk()
    fields = {'steps': 10}
    with pm100d.connect(hardware_addresses_and_constants.pm100d_address) as q, attenuator_wheel.create_do_task(hardware_addresses_and_constants.stepper_outputs) as r:
        my_gui = SetupGUI(root, 'Change laser power', fields, attenuatorwheel=r, powermeter=q)
        my_gui.build_change_intensity_gui()
        root.mainloop()
