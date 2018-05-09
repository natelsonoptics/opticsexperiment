#!/usr/bin/env python3
import optics.under_development.cryostation as CryostationComm
import sys
import time
from time import sleep
from decimal import Decimal

# This is an example that demonstrates external communication with a Cryostation.  It is not intended to
# be a production worthy python script.

# This script will cool the Cryostation system to a target platform temperature, wait for the target platform
# stability, and then initiate a step-up routine.  The step-up routine increments the platform set point,
# waits to achieve the new target temperature, and then waits to achieve the target stability, up to a maximum
# platform temperature.


# User defined parameters:  Modify these parameter values for the specific Cryostation under operation.

cryostation_ip = "192.168.45.47"  # Cryostation IP address
cryostation_port = 7773  # Cryostation external control port from the PREFERENCES tabpage

target_cooldown_platform_temperature = 5.000  # Target cooldown platform temperature (K)
target_platform_stability = 0.04  # Target cooldown and step-up platform stability (K)
temperature_stepup_size = 5.00  # Platform temperature step-up increment (K)
maximum_platform_stepup_target_temperature = 100.00  # Maximum platform step-up target temperature (K)
cooldown_timeout = 18000  # Time limit for reaching the cooldown platform temperature (seconds)
stepup_timeout = 3000  # Time limit for reaching each step-up platform temperature (seconds)
stability_timeout = 1800  # Time limit for reaching platform stability for cooldown and step-up (seconds)


def set_target_platform_temperature(cryostation_connection, set_point, timeout=10):
    "Set the target platform temperature."

    print("Set target platform temperature {0}".format(set_point))

    timeout = time.time() + timeout  # Determine timeout

    target_temperature = send_target_platform_temperature(cryostation_connection, set_point)
    while round(target_temperature, 2) != round(set_point, 2):
        if timeout > 0:
            if time.time() > timeout:  # If we pass the timeout, give up.
                return False
        sleep(1)
        target_temperature = send_target_platform_temperature(cryostation_connection, set_point)

    return True


def send_target_platform_temperature(cryostation_connection, set_point):
    "Send the target platform temperature to the Cryostation.  Read it back to verify the set operation"

    print("Send target platform temperature {0}".format(set_point))

    target_temperature_decimal = 0.0
    target_temperature_string = ''

    try:
        if cryostation_connection.send_command_get_response("STSP" + str(set_point)).startswith("OK"):
            target_temperature_string = cryostation_connection.send_command_get_response("GTSP")
    except Exception as err:
        print("Failed to send target platform temperature")
        exit(1)
    try:
        target_temperature_decimal = Decimal(target_temperature_string)
    except Exception as err:
        target_temperature_decimal = 0.0
    return target_temperature_decimal


def initiate_cooldown(cryostation_connection):
    "Set the target platform temperature and initiate cooldown."

    print("Set cooldown target temperature")
    if not set_target_platform_temperature(cryostation_connection, target_cooldown_platform_temperature):
        print("Timed out setting cooldown target platform temperature")
        exit(1)

    print("Initiate cooldown")
    try:
        if cryostation_connection.send_command_get_response("SCD") != "OK":
            print("Cooldown did not initiate")
            exit(1)
    except Exception as err:
        print("Failed to initiate cooldown")
        exit(1)


def wait_for_cooldown_and_stability(cryostation_connection):
    "Wait for the Cryostation system to cooldown and stabilize."

    print("Wait for cooldown temperature")
    if cooldown_timeout > 0:  # If cooldown timeout enabled
        cooldown_max_time = time.time() + cooldown_timeout  # Determine cooldown timeout
    while True:
        sleep(3)
        if cooldown_timeout > 0:
            if time.time() > cooldown_max_time:  # If we pass the cooldown timeout, give up.
                print("Timed out waiting for cooldown temperature")
                return False
        try:
            current_temperature = float(cryostation_connection.send_command_get_response("GPT"))
        except Exception as err:
            current_temperature = 0.0
        if current_temperature <= target_cooldown_platform_temperature and current_temperature > 0:  # Wait until platform temperature reaches target
            break

    print("Wait for cooldown stability")
    if stability_timeout > 0:  # If stability timeout enabled
        stability_max_time = time.time() + stability_timeout  # Determine stability timeout
    while True:
        sleep(3)
        if stability_timeout > 0:
            if time.time() > stability_max_time:  # If we pass the stability timeout, give up.
                print("Timed out waiting for cooldown stability")
                return False
        try:
            current_stability = float(cryostation_connection.send_command_get_response("GPS"))
        except Exception as err:
            current_stability = 0.0
        if current_stability <= target_platform_stability and current_stability > 0:  # Wait until platform stability reaches target
            return True


def step_up(cryostation_connection):
    "Step-up the temperature, waiting for stability at each step."

    current_temperature = 0.0

    # Get current target to step-up from
    step_target = -1.0
    while step_target < 0:
        try:
            step_target = float(cryostation_connection.send_command_get_response("GTSP"))  # Get target set point
        except Exception as err:
            step_target = -1.0
        sleep(1)

    # Calculate initial step-up target
    step_target += temperature_stepup_size
    # Step-up until the maximum is reached
    while round(step_target, 2) <= round(maximum_platform_stepup_target_temperature, 2):

        # Set the step-up target platform temperature
        print("\nStep-up the target platform temperature")
        if not set_target_platform_temperature(cryostation_connection, step_target):
            print("Timed out setting step-up target platform temperature {0}".format(step_target))
            exit(1)

        # Wait for the step-up target platform temperature to be reached
        print("Wait for step-up target temperature of {0}".format(step_target))
        if stepup_timeout > 0:  # If step-up timeout enabled
            stepup_max_time = time.time() + stepup_timeout  # Determine step-up timeout
        while True:
            if stepup_timeout > 0:
                if time.time() > stepup_max_time:  # If we pass the timeout, give up.
                    print("Timed out waiting for step-up target platform temperature")
                    return False
            try:
                current_temperature = float(cryostation_connection.send_command_get_response("GPT"))
            except Exception as err:
                current_temperature = 0.0
            if current_temperature >= step_target and current_temperature > 0.0:
                break
            sleep(3)

        # Wait for the step-up target platform temperature to stabilize
        print("Wait for step-up target temperature stability")
        if stability_timeout > 0:  # If stability timeout enabled
            stability_max_time = time.time() + stability_timeout  # Determine stability timeout
        while True:
            if stability_timeout > 0:
                if time.time() > stability_max_time:  # If we pass the timeout, give up.
                    print("Timed out waiting for step-up target platform stability")
                    return False
            try:
                current_stability = float(cryostation_connection.send_command_get_response("GPS"))
            except Exception as err:
                current_stability = 0.0
            if current_stability <= target_platform_stability and current_stability > 0.0:
                break
            sleep(3)

        # Calculate next step-up target
        step_target += temperature_stepup_size

    return True;


if __name__ == "__main__":

    # Establish Cryostation communication
    try:
        cryostation_connection = CryostationComm.CryoComm("169.254.116.144", "7773")
        print(float(cryostation_connection.send_command_get_response("GPT")))
    except:
        print("Could not connect to Cryostation IP: {0}, Port: {1}".format(cryostation_ip, cryostation_port))
        exit(1)


    ## Initiate cooldown
    initiate_cooldown(cryostation_connection)

    # Wait for the system to cooldown to the target platform temperature and reach the target platform stability
    if wait_for_cooldown_and_stability(cryostation_connection):
        print("Done with cooldown.")
    else:
        print("Timed out during cooldown.")
        exit(1)

    # Step-up the platform temperature, stabilizing at each step
    if step_up(cryostation_connection):
        print("\nDone with step-up.")
    else:
        print("\nTimed out during step-up.")
        exit(1)