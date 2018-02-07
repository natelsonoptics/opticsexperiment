import tkinter as tk

from optics.gui.gui_builds import SetupGUI
from optics.hardware_control import sr7270, npc3sg_analog, hardware_addresses_and_constants, pm100d

if __name__ == '__main__':
    root = tk.Tk()
    fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'polarization': 90, 'gain': 1000,
              'rate (per second)': 3, 'max time (s)': 600}
    title = 'Thermovoltage vs time'
    with npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) \
                    as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) \
                    as (sr7270_top, sr7270_bottom), \
            pm100d.connect(hardware_addresses_and_constants.pm100d_address) as powermeter:
        try:
            thermovoltage_time_gui = SetupGUI(root, title, fields, npc3sg_input=npc3sg_input, sr7270_top=sr7270_top,
                                              sr7270_bottom=sr7270_bottom, powermeter=powermeter)
            thermovoltage_time_gui.build_thermovoltage_time_gui()
            root.mainloop()
        except KeyboardInterrupt:
            print('aborted via keyboard interrupt')