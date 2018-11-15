import tkinter as tk

main = tk.Tk()

def leftkey(event):
    print('left key pressed')

def rightkey(event):
    print('right key pressed')

def upkey(event):
    print('up')

def downkey(event):
    print('down')


frame = tk.Frame(main, width=100, height=100)
main.bind('<Left>', leftkey)
main.bind('<Right>', rightkey)
main.bind('<Up>', upkey)
main.bind('<Down>', downkey)
frame.pack()
main.mainloop()
