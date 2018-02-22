import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
import tkinter.filedialog
from optics.electromigrate.k2400_break import K2400Break

class KeithleyGUI:
    def __init__(self, master, keithley):
        self._keithley = keithley
        self._master = master
        self._master.title('Keithley K2400 electromigration')
        self._fields = {'file path': '', 'device': '', 'notes': '', 'desired resistance': 100, 'start voltage': 0.01,
                        'stop voltage': 0.05, 'steps': 10, 'start break voltage': 0.5, 'break voltage': 0.8,
                        'maximum break voltage': 1.5, 'delta break voltage': 0.05, 'percent current drop': 0.4}
        self._entries = []
        self._inputs = {}
        self._filepath = tk.StringVar()  # this is a global variable - this needs to change
        self._filepath.set(self._fields['file path'])
        self._label = tk.Label(master, text='Keithley K2400 electromigration')
        self._label.pack()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)

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

    def electromigrate(self, event=None):
        self.fetch(event)
        run = K2400Break(self._inputs['file path'], self._inputs['device'], float(self._inputs['desired resistance']),
                         float(self._inputs['start voltage']), float(self._inputs['stop voltage']),
                         int(self._inputs['steps']), float(self._inputs['start break voltage']),
                         float(self._inputs['break voltage']), float(self._inputs['maximum break voltage']),
                         float(self._inputs['delta break voltage']), float(self._inputs['percent current drop']),
                         self._inputs['notes'], self._keithley)
        run.main()

    def build_k2400_gui(self):
        self._browse_button.pack()
        self.makeform()
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
