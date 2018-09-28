import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
import tkinter.filedialog
from optics.defunct.k2400_break import KeithleyBreak

class KeithleyGUI:
    def __init__(self, master, keithley):
        self._keithley = keithley
        self._master = master
        self._master.title('Keithley K2400 electromigration')
        self._fields = {'file path': '', 'device': '', 'desired resistance': 100,
                        'stop voltage (resistance measurement)': 0.05, 'steps': 10, 'start voltage': 0.1,
                        'break voltage': 1.5, 'delta break voltage': 0.005, 'delta voltage': 0.002,
                        'percent current drop': 0.4, 'passes': 1}
        self._entries = []
        self._inputs = {}
        self._filepath = tk.StringVar()  # this is a global variable - this needs to change
        self._filepath.set(self._fields['file path'])
        self._label = tk.Label(master, text='Keithley K2400 electromigration')
        self._label.pack()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._abort = tk.StringVar()
        self._abort.set('False')
        self._increase = tk.StringVar()
        self._increase.set('True')

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

        run = KeithleyBreak(self._keithley, self._inputs['file path'], self._inputs['device'],
                            steps=int(self._inputs['steps']),
                            stop_voltage=float(self._inputs['stop voltage (resistance measurement)']),
                            desired_resistance=float(self._inputs['desired resistance']),
                            break_voltage=float(self._inputs['break voltage']), passes=float(self._inputs['passes']),
                            increase_break_voltage=increase,
                            delta_break_voltage=float(self._inputs['delta break voltage']),
                            start_voltage=float(self._inputs['start voltage']),
                            delta_voltage=float(self._inputs['delta voltage']),
                            r_percent=float(self._inputs['percent current drop']), abort=abort)
        run.main()

    def build_k2400_gui(self):
        self._browse_button.pack()
        self.makeform()
        self.make_option_menu('Abort', self._abort, ['True', 'False'])
        self.make_option_menu('Increase break voltage', self._increase, ['True', 'False'])
        self._master.bind('<Return>', self.electromigrate)
        b1 = tk.Button(self._master, text='Run', command=self.electromigrate)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

if __name__ is '__main__':
    from optics.hardware_control import hardware_addresses_and_constants, keithley_k2400

    root = tk.Tk()
    with keithley_k2400.connect(hardware_addresses_and_constants.keithley_address) as keithley:
        app = KeithleyGUI(root, keithley)
        app.build_k2400_gui()
        root.mainloop()

from optics.hardware_control import hardware_addresses_and_constants, keithley_k2400

root = tk.Tk()
with keithley_k2400.connect(hardware_addresses_and_constants.keithley_address) as keithley:
    app = KeithleyGUI(root, keithley)
    app.build_k2400_gui()
    root.mainloop()
