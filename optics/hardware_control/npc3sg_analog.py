import contextlib
import time

import PyDAQmx
import numpy as np
from PyDAQmx import Task
from PyDAQmx.DAQmxFunctions import *


class MultiChannelAnalogInput():
    """Class to create a multi-channel analog input

    Usage: AI = MultiChannelInput(physicalChannel)
        physicalChannel: a string or a list of strings
    optional parameter: limit: tuple or list of tuples, the AI limit values
                        reset: Boolean
    Methods:
        read(name), return the value of the input name
        readAll(), return a dictionary name:value
    """

    def __init__(self, physicalChannel, limit=None, reset=False):
        if type(physicalChannel) == type(""):
            self.physicalChannel = [physicalChannel]
        else:
            self.physicalChannel = physicalChannel
        self.numberOfChannel = physicalChannel.__len__()
        if limit is None:
            self.limit = dict([(name, (-10.0, 10.0)) for name in self.physicalChannel])
        elif type(limit) == tuple:
            self.limit = dict([(name, limit) for name in self.physicalChannel])
        else:
            self.limit = dict([(name, limit[i]) for i, name in enumerate(self.physicalChannel)])
        if reset:
            DAQmxResetDevice(physicalChannel[0].split('/')[0])

    def configure(self):
        # Create one task handle per Channel
        taskHandles = dict([(name, TaskHandle(0)) for name in self.physicalChannel])
        for name in self.physicalChannel:
            DAQmxCreateTask("", byref(taskHandles[name]))
            DAQmxCreateAIVoltageChan(taskHandles[name], name, "", DAQmx_Val_RSE,
                                     self.limit[name][0], self.limit[name][1],
                                     DAQmx_Val_Volts, None)
        self.taskHandles = taskHandles

    def readAll(self):
        return dict([(name, self.read(name)) for name in self.physicalChannel])

    def read(self, name=None):
        if name is None:
            name = self.physicalChannel[0]
        taskHandle = self.taskHandles[name]
        DAQmxStartTask(taskHandle)
        data = numpy.zeros((1,), dtype=numpy.float64)
        #        data = AI_data_type()
        read = int32()
        DAQmxReadAnalogF64(taskHandle, 1, 10.0, DAQmx_Val_GroupByChannel, data, 1, byref(read), None)
        DAQmxStopTask(taskHandle)
        return data[0]


class Reader:
    def __init__(self, multiple_ai):
        self._multiple_ai = multiple_ai

    def read(self):
        time.sleep(0.1)
        voltage = self._multiple_ai.readAll()
        return [voltage[i] / 10 * 160 for i in voltage]

@contextlib.contextmanager
def create_ai_task(ai_x, ai_y):
    multiple_ai = MultiChannelAnalogInput([ai_x, ai_y])
    multiple_ai.configure()
    try:
        yield Reader(multiple_ai)
    finally:
        print('done')


class Controller:
    def __init__(self, task):
        self._task = task

    def move(self, position):
        voltage = np.clip((position / 160 * 10), 0, 10)  # converts to the voltage to analog control
        # voltage range is 0-10 V
        self._task.WriteAnalogScalarF64(1, 10.0, voltage, None)


@contextlib.contextmanager
def create_ao_task(channel):
    task = Task()
    task.CreateAOVoltageChan(channel, "", -10.0, 10.0, PyDAQmx.DAQmx_Val_Volts, None)
    task.StartTask()
    try:
        yield Controller(task)
    finally:
        task.StopTask()









