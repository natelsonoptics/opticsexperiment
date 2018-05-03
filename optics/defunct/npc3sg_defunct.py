import serial


def initialize(port = 'COM4') -> object:
    ser = serial.Serial(port, 19200, xonxoff=False, timeout=0.4, write_timeout=0.1)
    ser.write(('setk,0,1\r').encode())  # activates remote control for channel 1
    ser.write(('setk,1,1\r').encode())  # activates remote control for channel 2
    ser.write(('cloop,0,1\r').encode())  # switches channel 1 to closed loop
    ser.write(('cloop,1,1\r').encode())  # switches channel 2 to closed loop
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser


def move_x(ser, i):
    ser.write(('set,0,' + str(i) + '\r').encode())


def move_y(ser, i):
    ser.write(('set,1,' + str(i) + '\r').encode())


def read(ser):
    ser.write(('measure\r').encode())
    return (ser.read(50).decode())


def close(ser):
    move_x(ser, 0)
    move_y(ser, 0)
    ser.close()


