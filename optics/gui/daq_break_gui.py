import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
import tkinter.filedialog
from optics.electromigrate.daq_break import DAQBreak


class DAQBreakGUI:
    def __init__(self, master, ai, ao):
        self._ai = ai
        self._ao = ao
        self._master = master
        self._master.title('DAQ electromigration')
        self._fields = {'file path': '', 'device': '', 'desired resistance': 100,
                        'stop voltage (resistance measurement)': 0.05, 'steps': 10, 'start voltage': 0.1,
                        'break voltage': 1.5, 'delta break voltage': 0.005, 'delta voltage': 0.002,
                        'current drop': 50e-6, 'passes': 1}
        self._entries = []
        self._inputs = {}
        self._filepath = tk.StringVar()  # this is a global variable - this needs to change
        self._filepath.set(self._fields['file path'])
        self._label = tk.Label(master, text='DAQ electromigration')
        self._label.pack()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._abort = tk.StringVar()
        self._abort.set('False')
        self._increase = tk.StringVar()
        self._increase.set('True')
        self._current_amplifier_gain_options = {'1 mA/V': 1000, '100 uA/V': 10000, '10 uA/V': 100000,
                                                '1 uA/V': 1000000, '100 nA/V': 10000000, '10 nA/V': 100000000,
                                                '1 nA/V': 1000000000, '100 pA/V': 10000000000, '10 pA/V': 100000000000,
                                                '1 pA/V': 1000000000000}
        self._gain = tk.StringVar()
        self._gain.set('1 mA/V')

    def makeform(self):
        for key in self._fields:
            row = tk.Frame(self._master)
            lab = tk.Label(row, width=20, text=key, anchor='w')
            if key == 'file path':
                ent = tk.Entry(row, textvariable=self._filepath)
            else:
                ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            ent.insert(0, str(self._fields[key]))
            self._entries.append((key, ent))
        return self._entries

    def onclick_browse(self):
        self._filepath.set(tkinter.filedialog.askdirectory())

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def make_option_menu(self, label, parameter, option_list):
        row = tk.Frame(self._master)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text=label, anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, parameter, *option_list)
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def electromigrate(self, event=None):
        self.fetch(event)
        if self._abort.get() == 'True':
            abort = True
        else:
            abort = False
        if self._increase.get() == 'True':
            increase = False
        else:
            increase = True

        run = DAQBreak(self._ao, self._ai, self._inputs['file path'], self._inputs['device'],
                       steps=int(self._inputs['steps']),
                       stop_voltage=float(self._inputs['stop voltage (resistance measurement)']),
                       desired_resistance=float(self._inputs['desired resistance']),
                       break_voltage=float(self._inputs['break voltage']), passes=float(self._inputs['passes']),
                       increase_break_voltage=increase, delta_break_voltage=float(self._inputs['delta break voltage']),
                       start_voltage=float(self._inputs['start voltage']),
                       delta_voltage=float(self._inputs['delta voltage']),
                       current_drop=float(self._inputs['current drop']), abort=abort,
                       gain=float(self._current_amplifier_gain_options[self._gain.get()]))
        run.main()

    def build_daqbreak_gui(self):
        self._browse_button.pack()
        self.makeform()
        self.make_option_menu('Gain', self._gain, self._current_amplifier_gain_options)
        self.make_option_menu('Abort', self._abort, ['True', 'False'])
        self.make_option_menu('Increase break voltage', self._increase, ['True', 'False'])
        self._master.bind('<Return>', self.electromigrate)
        b1 = tk.Button(self._master, text='Run', command=self.electromigrate)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)


if __name__ is '__main__':
    from optics.hardware_control import hardware_addresses_and_constants, daq

    root = tk.Tk()
    with daq.create_ai_task(hardware_addresses_and_constants.ai_switch, sleep=0) as ai, \
            daq.create_ao_task(hardware_addresses_and_constants.ao_switch) as ao:
        app = DAQBreakGUI(root, ai, ao)
        app.build_daqbreak_gui()
        root.mainloop()

from optics.hardware_control import hardware_addresses_and_constants, daq

root = tk.Tk()
with daq.create_ai_task(hardware_addresses_and_constants.ai_switch, sleep=0) as ai, \
        daq.create_ao_task(hardware_addresses_and_constants.ao_switch) as ao:
    app = DAQBreakGUI(root, ai, ao)
    app.build_daqbreak_gui()
    root.mainloop()