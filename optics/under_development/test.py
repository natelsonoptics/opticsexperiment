import tkinter as tk



class Stuff:
    def __init__(self):
        self._idx = 0
        self._running = False
        self._root = tk.Tk()
        self._root.title("Title")
        self._root.geometry('500x500')
        self._app = tk.Frame(self._root)
        self._app.grid()

    def scanning(self):
        if self._running:
            print(self._idx)
            self._idx += 1
            self._root.after(1000, self.scanning)

    def start(self):
        self._running = True
        self.scanning()

    def stop(self):
        self._running = False

    def main(self):
        start = tk.Button(self._app, text='start', command=self.start)
        stop = tk.Button(self._app, text='stop', command=self.stop)
        start.grid()
        stop.grid()
        self._root.mainloop()


h = Stuff()
h.main()












