import matplotlib
matplotlib.use('Qt4Agg')  # this allows you to see the interactive plots!
import tkinter as tk
import tkinter.filedialog
from optics.hardware_control import attenuator_wheel, pm100d, hardware_addresses_and_constants, npc3sg_analog, \
    polarizercontroller, daq
from optics.thermovoltage_measurement.thermovoltage_map_dc import ThermovoltageScanDC

class BaseGUI:
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None,
                 powermeter=None, attenuatorwheel=None, polarizer=None,
                 daq_input=None):
        self._master = master
        self._master.title('Optics setup measurements')
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._polarizer = polarizer
        self._daq_input = daq_input
        self._newWindow = None
        self._app = None

    def new_window(self, measurementtype):
        self._newWindow = tk.Toplevel(self._master)
        self._app = LockinMeasurementGUI(self._newWindow, npc3sg_x=self._npc3sg_x, npc3sg_y=self._npc3sg_y,
                                         powermeter=self._powermeter,
                                         attenuatorwheel=self._attenuatorwheel, polarizer=self._polarizer)
        measurement = {'ptemapdc': self._app.build_thermovoltage_scan_dc_gui}
        measurement[measurementtype]()

    def build(self):
        row = tk.Frame(self._master)
        lab = tk.Label(row, width=20, text='DC map scans', anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        b13 = tk.Button(row, text='thermovoltage',
                       command=lambda measurementtype='ptemapdc': self.new_window(measurementtype))
        b13.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        b12 = tk.Button(self._master, text='Quit all windows', command=self._master.quit)
        b12.pack()

class LockinMeasurementGUI:
    def __init__(self, master, npc3sg_x=None, npc3sg_y=None, powermeter=None, attenuatorwheel=None, polarizer=None,
                 daq_input=None):
        self._master = master
        self._fields = {}
        self._entries = []
        self._inputs = {}
        self._npc3sg_x = npc3sg_x
        self._npc3sg_y = npc3sg_y
        self._powermeter = powermeter
        self._attenuatorwheel = attenuatorwheel
        self._polarizer = polarizer
        self._textbox = None
        self._textbox2 = None
        self._filepath = tk.StringVar()
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._daq_input = daq_input

    def makeform(self):
        for key in self._fields:
            row = tk.Frame(self._master)
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

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def thermovoltage_scan_dc(self, event=None):
        self.fetch(event)
        run = ThermovoltageScanDC(self._inputs['file path'], self._inputs['notes'], self._inputs['device'],
                                  int(self._inputs['scan']), float(self._inputs['gain']),
                                  int(self._inputs['x pixel density']),
                                  int(self._inputs['y pixel density']), int(self._inputs['x range']),
                                  int(self._inputs['y range']), int(self._inputs['x center']),
                                  int(self._inputs['y center']), self._npc3sg_x, self._npc3sg_y, self._daq_input,
                                  self._powermeter, self._polarizer)
        run.main()

    def onclick_browse(self):
        self._filepath.set(tkinter.filedialog.askdirectory())

    def build_thermovoltage_scan_dc_gui(self):
        caption = "DC thermovoltage map scan"
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'gain': 1000, 'x pixel density': 15,
                        'y pixel density': 15, 'x range': 160, 'y range': 160, 'x center': 80, 'y center': 80}
        self._browse_button.pack()
        self.makeform()
        self._master.bind('<Return>', self.thermovoltage_scan_dc)
        b1 = tk.Button(self._master, text='Run', command=self.thermovoltage_scan_dc)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self._master, text='Quit', command=self._master.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)


with npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_x) as npc3sg_x, \
        npc3sg_analog.create_ao_task(hardware_addresses_and_constants.ao_y) as npc3sg_y, \
        pm100d.connect(hardware_addresses_and_constants.pm100d_address) as powermeter, \
        polarizercontroller.connect_kdc101(hardware_addresses_and_constants.kdc101_serial_number) as polarizer, \
        attenuator_wheel.create_do_task(hardware_addresses_and_constants.attenuator_wheel_outputs) as \
                attenuatorwheel, daq.create_ai_task('Dev1/ai2') as daq_input:
    root = tk.Tk()
    app = BaseGUI(root, npc3sg_x=npc3sg_x, npc3sg_y=npc3sg_y, powermeter=powermeter,
                  attenuatorwheel=attenuatorwheel, polarizer=polarizer, daq_input=daq_input)
    app.build()
    root.mainloop()