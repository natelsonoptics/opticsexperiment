import contextlib
import time
import numpy as np
import PyDAQmx
from PyDAQmx import Task
from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.DAQmxConstants import *

# if you get errors, make sure that these are your imported modules after you commit because "optimizing imports" means
# that some of these will get skipped:
# import contextlib
# import time
# import PyDAQmx
# import numpy as np
# from PyDAQmx import Task
# from PyDAQmx.DAQmxFunctions import *
# from PyDAQmx.DAQmxConstants import *


class MultiChannelAnalogInput:
    """Class to create a multi-channel analog input

    Usage: AI = MultiChannelInput(physicalChannel)
        physicalChannel: a string or a list of strings
    optional parameter: limit: tuple or list of tuples, the AI limit values
                        reset: Boolean
    Methods:
        read(name), return the value of the input name
        readAll(), return a dictionary name:value
    """

    def __init__(self, physicalChannel, limit=None, reset=False, points=1, average=True):
        self._points = points
        self._average = average
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
        data = numpy.zeros(self._points)
        #        data = AI_data_type()
        read = int32()
        DAQmxReadAnalogF64(taskHandle, self._points, 10.0, DAQmx_Val_GroupByChannel, data, self._points, byref(read),
                           None)
        DAQmxStopTask(taskHandle)
        if self._average:
            return np.average(data)
        else:
            return data


class AnalogInput:
    def __init__(self, multiple_ai, sleep=0.1):
        self._multiple_ai = multiple_ai
        self._sleep = sleep

    def read(self):
        time.sleep(self._sleep)
        voltage = self._multiple_ai.readAll()
        return [voltage[i] for i in voltage]


@contextlib.contextmanager
def create_ai_task(ai_channels, points=1):
    multiple_ai = MultiChannelAnalogInput(ai_channels, points=1)
    multiple_ai.configure()
    try:
        yield AnalogInput(multiple_ai)
    finally:
        print('done')


class AnalogOutput:
    def __init__(self, task):
        self._task = task

    def move(self, position):
        voltage = np.clip((position / 160 * 10), 0, 10)  # converts to the voltage to analog control
        # voltage range is 0-10 V
        self._task.WriteAnalogScalarF64(1, 10.0, voltage, None)


@contextlib.contextmanager
def create_ao_task(ao_channel):
    task = Task()
    task.CreateAOVoltageChan(ao_channel, "", -10.0, 10.0, PyDAQmx.DAQmx_Val_Volts, None)
    task.StartTask()
    try:
        yield AnalogOutput(task)
    finally:
        task.StopTask()