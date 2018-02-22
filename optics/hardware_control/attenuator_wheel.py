import contextlib
import time

import PyDAQmx
import numpy as np
from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxFunctions import *


class Stepper:
    def __init__(self, task):
        self._task = task

    def step(self, steps, wait=0.1, direction=True):
        # True moves forward, False moves backward
        if wait < 0.005:
            wait = 0.005
        data1 = np.array([1, 0, 1, 0], dtype=np.uint8)
        data2 = np.array([0, 1, 1, 0], dtype=np.uint8)
        data3 = np.array([0, 1, 0, 1], dtype=np.uint8)
        data4 = np.array([1, 0, 0, 1], dtype=np.uint8)
        forward = [data1, data2, data3, data4]
        time.sleep(0.5)
        for i in range(steps):
            if direction:
                for data in forward:
                    self._task.WriteDigitalLines(1, 1, 10.0, PyDAQmx.DAQmx_Val_GroupByChannel, data, None, None)
                    time.sleep(wait)
            else:
                for data in reversed(forward):
                    self._task.WriteDigitalLines(1, 1, 10.0, PyDAQmx.DAQmx_Val_GroupByChannel, data, None, None)
                    time.sleep(wait)


@contextlib.contextmanager
def create_do_task(lines):
    task = Task()
    task.CreateDOChan(lines, "", PyDAQmx.DAQmx_Val_ChanForAllLines)
    task.StartTask()
    try:
        yield Stepper(task)
    finally:
        task.StopTask()




