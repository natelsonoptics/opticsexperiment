ai_x = 'Dev1/ai3'  # x DAQ input for piezo controller
ai_y = 'Dev1/ai4'  # y DAQ input for piezo controller
ao_x = 'Dev1/ao1'  # x DAQ output for piezo controller
ao_y = 'Dev1/ao2'  # y DAQ output for piezo controller
ai_dc1 = 'Dev1/ai1'  # DAQ input for DC measurements
ai_dc2 = 'Dev1/ai2'
vendor = 0x0A2D  # for lock in amplifier
product = 0x001B  # for lock in amplifier
pm100d_address = 'USB0::0x1313::0x8070::P0000542::INSTR'
#pm100d_address = 'USB0::0x1313::0x8078::P0017646::INSTR'
attenuator_wheel_outputs = "Dev1/port0/line8:11"  # DAQ outputs for attenuator wheel
keithley_address = 'GPIB12::12::INSTR'
tdc001_serial_number = 83825803
kdc101_serial_number = 27251504
polarizer_offset = 1.183  # set to 1 if no offset - it's multiplicative
cryostation_port = 7773
cryostation_ip_address = '169.254.116.144'