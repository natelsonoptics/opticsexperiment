import tkinter as tk

from optics.defunct import npc3sg_analog
from optics.gui.gui_builds import SetupGUI
from optics.hardware_control import sr7270, hardware_addresses_and_constants, pm100d, polarizercontroller

if __name__ == '__main__':
    root = tk.Tk()
    fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000}
    title = 'Thermovoltage vs polarization'
    with npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) \
                    as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) \
                    as (sr7270_top, sr7270_bottom), \
            pm100d.connect(hardware_addresses_and_constants.pm100d_address) as powermeter,\
            polarizercontroller.connect_kdc101(hardware_addresses_and_constants.kdc101_serial_number) as polarizer:
        try:
            thermovoltage_polarization_gui = SetupGUI(root, title, fields, npc3sg_input=npc3sg_input,
                                                      sr7270_bottom=sr7270_bottom, powermeter=powermeter,
                                                      polarizer=polarizer)
            thermovoltage_polarization_gui.build_thermovoltage_polarization_gui()
            root.mainloop()
        except KeyboardInterrupt:
            print('aborted via keyboard interrupt')