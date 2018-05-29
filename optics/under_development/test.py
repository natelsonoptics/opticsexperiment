import tkinter as tk
import tkinter.filedialog
import os
import csv
import random

class GUI:
    def __init__(self, master, powermeter=None):
        self._filepath = tk.StringVar()
        self._power = tk.StringVar()
        self._powermeter = powermeter
        self._master = master
        self._browse_button = tk.Button(self._master, text="Browse", command=self.onclick_browse)
        self._textbox = None
        self._entries = []
        self._fields = {'file path': '', 'position (in)': '', 'power (W)': ''}
        self._inputs = {}

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

    def onclick_browse(self, event=None):
        self._filepath.set(tkinter.filedialog.asksaveasfilename())

    def random_number(self):
        return random.random()

    def fetch(self, event=None):  # stop trying to make fetch happen. It's not going to happen. -Regina, Mean Girls
        for entry in self._entries:
            field = entry[0]
            text = entry[1].get()
            self._inputs[field] = text

    def record(self, event=None):
        self._power.set(self.random_number())
        self.fetch(event)
        if not os.path.exists(self._inputs['file path']):
            with open(self._inputs['file path'], 'w', newline='') as outputfile:
                writer = csv.writer(outputfile)
                writer.writerow(['position (in)', 'power (W)'])
        with open(self._inputs['file path'], 'a', newline='') as outputfile:
            writer = csv.writer(outputfile)
            writer.writerow([float(self._inputs['position (in)']), float(self._inputs['power (W)'])])

    def make_gui(self):
        caption = 'power vs. position'
        self._master.title(caption)
        label = tk.Label(self._master, text=caption)
        label.pack()
        self._browse_button.pack()
        for key in self._fields:
            row = tk.Frame(self._master)
            lab = tk.Label(row, width=15, text=key, anchor='w')
            if key == 'power (W)':
                ent = tk.Entry(row, textvariable=self._power)
            elif key == 'file path':
                ent = tk.Entry(row, textvariable=self._filepath)
            else:
                ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            ent.insert(0, str(self._fields[key]))
            self._entries.append((key, ent))
        self._master.bind('<Return>', self.record)
        self.makebutton('Read power and record', self.record)
        self.makebutton('Quit', self._master.destroy)

root = tk.Tk()
q = GUI(root)
q.make_gui()
root.mainloop()









