import tkinter as tk
import tkinter.filedialog


class BaseGUI:
    def __init__(self, master):
        self._master = master
        self._newWindow = None
        self._app = None
        self._entries = []
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._fields = {}
        self._inputs = {}
        self._textbox2 = None
        self._textbox = None
        self._filepath = tk.StringVar()
        self._current_amplifier_gain_options = {'1 mA/V': 1e3, '500 uA/V': 2e3,'200 uA/V': 5e3,
                                                '100 uA/V': 1e4, '50 uA/V': 2e4,'20 uA/V': 5e4,
                                                '10 uA/V': 1e5, '5 uA/V': 2e5,'2 uA/V': 5e5,
                                                '1 uA/V': 1e6, '500 nA/V': 2e6,'200 nA/V': 5e6,
                                                '100 nA/V': 1e7, '50 nA/V': 2e7,'20 nA/V': 5e7,
                                                '10 nA/V': 1e8, '5 nA/V': 2e8,'2 nA/V': 5e8,
                                                '1 nA/V': 1e9, '500 pA/V': 2e9,'200 pA/V': 5e9,
                                                '100 pA/V': 1e10, '50 pA/V': 2e10,'20 pA/V': 5e10,
                                                '10 pA/V': 1e11, '5 pA/V': 2e11,'2 pA/V': 5e11,
                                                '1 pA/V': 1e12}
        self._voltage_gain_options = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
        self._time_constant_options = [1e-3, 2e-3, 5e-3, 10e-03, 20e-03, 50e-03, 100e-03, 200e-03, 500e-03, 1, 2, 5, 10]
        self._lockin_sensitivity_options = [1e-2, 2e-2, 5e-2, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]
        self._newWindow = None

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)

    def make_measurement_button(self, master, text, measurement_type):
        b1 = tk.Button(master, text=text,
                       command=lambda measurementtype=measurement_type: self.new_window(measurementtype))
        b1.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

    def makerow(self, title, side=tk.LEFT, width=20):
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=width, text=title, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=side)
        return row

    def beginform(self, caption, browse_button=True, master=None):
        self._entries = []
        if not master:
            master = self._master
        master.title(caption)
        label = tk.Label(master, text=caption)
        label.pack()
        if browse_button:
            self._browse_button.pack()
        for key in self._fields:
            row = tk.Frame(master)
            lab = tk.Label(row, width=15, text=key, anchor='w')
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

    def endform(self, run_command, master=None):
        if not master:
            master = self._master
        master.bind('<Return>', run_command)
        self.makebutton('Run', run_command, master)
        self.makebutton('Quit', master.destroy, master=master)

    def makebutton(self, caption, run_command, master=None):
        if not master:
            master = self._master
        b1 = tk.Button(master, text=caption, command=run_command)
        b1.pack(side=tk.LEFT, padx=5, pady=5)

    def maketextbox(self, title, displaytext):
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text=title, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox = tk.Text(row, height=1, width=10)
        self._textbox.insert(tk.END, displaytext)
        self._textbox.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def make_option_menu(self, label, parameter, option_list):
        row = tk.Frame(self._master)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab = tk.Label(row, width=15, text=label, anchor='w')
        lab.pack(side=tk.LEFT)
        t = tk.OptionMenu(row, parameter, *option_list)
        t.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def maketextbox2(self, title, displaytext):  # TODO fix this
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=15, text=title, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self._textbox2 = tk.Text(row, height=1, width=10)
        self._textbox2.insert(tk.END, displaytext)
        self._textbox2.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def onclick_browse(self):
        self._filepath.set(tkinter.filedialog.askdirectory())

    def string_to_bool(self, s):
        if s == 'True':
            return True
        else:
            return False


