import numpy as np


def do_nothing():
    pass


def tk_sleep(master, ms):
    master.after(int(np.round(ms, 0)), do_nothing())

