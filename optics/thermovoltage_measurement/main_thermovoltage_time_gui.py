from optics.hardware_control import sr7270, npc3sg_analog, hardware_addresses_and_constants
import tkinter as tk
from optics.gui.gui_builds import SetupGUI

if __name__ == '__main__':
    root = tk.Tk()
    fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'polarization': 90, 'gain': 1000,
              'rate (per second) Default = None': None, 'max time (s)': 600}
    title = 'Thermovoltage scan'
    with npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x, hardware_addresses_and_constants.ai_y) \
                    as npc3sg_input, \
            sr7270.create_endpoints(hardware_addresses_and_constants.vendor, hardware_addresses_and_constants.product) \
                    as (sr7270_top, sr7270_bottom):
        try:
            thermovoltage_time_gui = SetupGUI(root, title, fields, npc3sg_input, sr7270_top, sr7270_bottom)
            thermovoltage_time_gui.build_thermovoltage_time_gui()
            root.mainloop()
        except KeyboardInterrupt:
            print('aborted via keyboard interrupt')