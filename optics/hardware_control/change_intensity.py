class ChangeIntensity:
    def __init__(self, attenuatorwheel, powermeter):
        self.attenuatorwheel = attenuatorwheel
        self.powermeter = powermeter

    def step(self, steps, direction=True):
        self.attenuatorwheel.step(steps, direction=direction)

    def read_power(self):
        return self.powermeter.read_power()