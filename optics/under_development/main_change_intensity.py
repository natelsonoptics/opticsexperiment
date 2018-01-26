import time

from optics.hardware_control import pm100d, stepper, hardware_addresses_and_constants

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='moves attenuator wheel to desired power on sample')
    parser.add_argument("-power", metavar='power', type=float, help='lowest desired power in mW. '
                                                                    'typical max value is ~7.5 mW')
    parser.add_argument("-max_power", metavar='power', type=float, help='highest desired power in mW. '
                                                                        'optional.')
    args = parser.parse_args()

    # This program moves the attenuator wheel in small iterations and checks the power on the
    # sample and stops when the power is in the desired range


    with pm100d.connect(hardware_addresses_and_constants.pm100_address) as pm, \
            stepper.create_do_task(hardware_addresses_and_constants.stepper_outputs) as motor:
        if not args.max_power:
            max_power = 10
        else:
            max_power = args.max_power
        for i in range(100):  # large number of iterations so that you don't get early truncation
            #  check: is my power within this range? If yes, return the value. Otherwise, take a step and measure again
            if max_power/1000 >= pm.read_power() > args.power/1000:
                break
            motor.step(2, 0.005)  # move two steps but quickly. because of backlash, I chose small step value so you
            # don't get a big dip in power near the max position
            time.sleep(0.05)
        print(str(pm.read_power()*1000)+ ' mW on sample')