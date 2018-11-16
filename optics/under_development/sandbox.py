import tkinter as tk

main = tk.Tk()

def leftkey(event=None):
    print('left key pressed')

def rightkey(event=None):
    print('right key pressed')

def upkey(event=None):
    print('up')

def downkey(event=None):
    print('down')


frame = tk.Frame(main, width=100, height=100)
button = tk.Button(master=main, text="↑", command=upkey)
button.pack()
button = tk.Button(master=main, text="←", command=leftkey)
button.pack(side=tk.LEFT)
button = tk.Button(master=main, text="→", command=rightkey)
button.pack(side=tk.LEFT)
button = tk.Button(master=main, text="↓", command=downkey)
button.pack(side=tk.LEFT)
main.bind('<Left>', leftkey)
main.bind('<Right>', rightkey)
main.bind('<Up>', upkey)
main.bind('<Down>', downkey)
frame.pack()
main.mainloop()
