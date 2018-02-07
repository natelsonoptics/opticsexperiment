import tkinter as tk

from optics.gui.gui_builds import SetupGUI
from optics.hardware_control import npc3sg_analog, hardware_addresses_and_constants

if __name__ == '__main__':
    with npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
            npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
            npc3sg_analog.create_ai_task(hardware_addresses_and_constants.ai_x,
                                         hardware_addresses_and_constants.ai_y) as npc3sg_input:
        root = tk.Tk()
        title = 'Move piezo position'
        fields = {'x': 80, 'y': 80}
        piezo_gui = SetupGUI(root, title, fields, npc3sg_input=npc3sg_input, npc3sg_x=npc3sg_x, npc3sg_y=npc3sg_y)
        piezo_gui.build_change_position_gui()
        root.mainloop()