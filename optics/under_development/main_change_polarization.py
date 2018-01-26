from optics.hardware_control import polarizer_controller, hardware_addresses_and_constants

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Change laser polarization')
    parser.add_argument("-waveplate", metavar='waveplate', type=float, help='waveplate angle')
    args = parser.parse_args()

    with polarizer_controller.connect_tdc001(hardware_addresses_and_constants.tdc001_serial_number) as polarizer:
        waveplate = args.waveplate % 180
        polarizer.move(waveplate)
        print('Polarization: ' + str(float(str(polarizer.read_position(1000))) * 2) + ' degrees')