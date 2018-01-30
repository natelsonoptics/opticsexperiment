import tkinter as tk

from optics.gui.gui_builds import SetupGUI
from optics.hardware_control import polarizercontroller, hardware_addresses_and_constants

if __name__ == '__main__':
    root = tk.Tk()
    fields = {'desired polarization': 90}
    with polarizercontroller.connect_kdc101(hardware_addresses_and_constants.kdc101_serial_number) as \
            polarizer:
        my_gui = SetupGUI(root, 'Change polarization', fields, polarizer=polarizer)
        my_gui.build_change_polarization_gui()
        root.mainloop()