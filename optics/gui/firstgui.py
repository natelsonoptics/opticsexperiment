#!/usr/bin/python3

import tkinter as tk
import tkinter.filedialog

class MyFirstGUI:
    def __init__(self, master, caption, fields):
        self.master = master
        self.master.title(caption)
        self.fields = fields
        self.entries = []
        self.inputs = {}
        self.filename = None
        self.label = tk.Label(master, text=caption)
        self.label.pack()
        self.browse_button = tk.Button(self.master, text="Browse", command=self.onclick_browse)

    def makeform(self):
        for key in self.fields:
            row = tk.Frame(self.master)
            lab = tk.Label(row, width=15, text=key, anchor='w')
            if key == 'file path':
                ent = tk.Entry(row, textvariable='kitten')
            else:
                ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            ent.insert(0, str(self.fields[key]))
            self.entries.append((key, ent))
        return self.entries

    def fetch(self):
        for entry in self.entries:
            field = entry[0]
            text = entry[1].get()
            self.inputs[field] = text
        return self.inputs

    def onclick_browse(self):
        self.filename = tkinter.filedialog.askdirectory()

    def build_1(self):
        self.browse_button.pack()
        self.makeform()
        self.master.bind('<Return>', self.fetch)
        b1 = tk.Button(self.master, text='Show', command=self.fetch)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.master, text='Quit', command=self.master.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)


if __name__ == '__main__':
    root = tk.Tk()
    fields = {'file path': "", 'device': "", 'scan': 0, 'notes': "", 'polarization': 90, 'gain': 1000,
              'x pixel density': 15, 'y pixel density': 15, 'x range': 160, 'y range': 160, 'x center': 80,
              'y center': 80}
    my_gui = MyFirstGUI(root, 'hello', fields)
    my_gui.build_1()
    root.mainloop()



#if __name__ == '__main__':
#    root = Tk()

#    ents = makeform(root, fields, filename)
#    root.bind('<Return>', (lambda event, e=ents: fetch(e)))
#    b1 = Button(root, text='Show', command=(lambda w=ents: stuff(w)))
#    b1.pack(side=LEFT, padx=5, pady=5)
#   b2 = Button(root, text='Quit', command=root.quit)
#   b2.pack(side=LEFT, padx=5, pady=5)
#  root.mainloop()