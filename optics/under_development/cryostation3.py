import socket
from optics.hardware_control.hardware_addresses_and_constants import cryostation_ip_address, cryostation_port
import contextlib
import time


@contextlib.contextmanager
def connect_socket(ip, port, connecttimeout=10, sockettimeout=5):
    sock = socket.create_connection((ip, port), timeout=connecttimeout)
    try:
        yield SocketCommunication(sock, sockettimeout)
    finally:
        sock.shutdown(1)
        sock.close()

class SocketCommunication:
    def __init__(self, sock, sockettimeout):
        self._sock = sock
        self._sock.settimeout(sockettimeout)

    def send(self, message):
        message = str(len(message)).zfill(2) + message
        total_sent = 0
        while total_sent < len(message):
            try:
                sent = self._sock.send(message[total_sent:].encode())
            except Exception as err:
                print("Socket Communication: Send communication error - {}".format(err))
                raise err
            # If sent is zero, there is a communication issue
            if sent == 0:
                raise RuntimeError("Socket connection lost on send")
            total_sent += sent

    def receive(self):
        chunks = []
        received = 0

        try:
            message_length = int(self._sock.recv(2).decode('UTF8'))
        except Exception as err:
            print("Socket Communication: Receive message length communication error - {}".format(err))
            raise err

        while received < message_length:
            try:
                chunk = self._sock.recv(message_length - received)
            except Exception as err:
                print("CryoComm:Receive communication error - {}".format(err))
                raise err

            # If an empty chunk is read, there is a communication issue
            if chunk == '':
                raise RuntimeError("CryoComm:Cryostation connection lost on receive")
            chunks.append(chunk)
            received += len(chunk)

        return ''.join([x.decode('UTF8') for x in chunks])

class CryostationCommuncation:
    def __init__(self, socketcommunication):
        self._socketcommunication = socketcommunication

    def get_alarm_state(self):
        # Returns true or false indicating the presence or absence of a system error
        self._socketcommunication.send('GAS')
        return self._socketcommunication.receive()

    def get_chamber_pressure(self):
        # Returns the current chamber pressure or -0.1 to indicate the chamber pressure is not
        # available.
        # Units: mTorr
        self._socketcommunication.send('GCP')
        return self._socketcommunication.receive()

    def get_compressor_run_state(self):
        # Returns the current run state of the compressor (on/off)
        self._socketcommunication.send('GCRS')
        return self._socketcommunication.receive()

    def get_compressor_speed(self):
        # Returns the current compressor speed or -0.1 to indicate the compressor speed is not
        # available.
        # Units: Hz
        self._socketcommunication.send('GSC')
        return self._socketcommunication.receive()

    def get_case_valve_state(self):
        # Returns the current case valve state (open/closed)
        self._socketcommunication.send('GCVS')
        return self._socketcommunication.receive()

    def get_cold_head_speed(self):
        #  Returns the current cold head speed or -0.1 to indicate the cold head speed is not
        # available.
        # Units: Hz
        self._socketcommunication.send('GHS')
        return self._socketcommunication.receive()

    def get_magnet_state(self):
        #  Returns the current magnet state
        #  MAGNET ENABLED/MAGNET DISABLED/System not able to execute command at this time.
        # Activate the magnet module first.
        self._socketcommunication.send('GMS')
        return self._socketcommunication.receive()

    def get_magnet_target_field(self):
        #  Returns the current set point for magnetic field or -9.999999 if the magnet is no
        #  enabled or the magnet module is not activated.
        #  Units: Tesla
        self._socketcommunication.send('GMTF')
        return self._socketcommunication.receive()

    def get_platform_heater_power(self):
        #   Returns the current platform heater power reading or -0.100 to indicate the platform
        # heater power is not available.
        #  Units: Watts
        self._socketcommunication.send('GPHP')
        return self._socketcommunication.receive()

    def get_platform_stability(self):
        #  Returns the current platform stability or -0.10000 to indicate the platform stability
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GPS')
        return self._socketcommunication.receive()

    def get_platform_temperature(self):
        #  Returns the current platform temperature or -0.100 to indicate the platform temperature
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GPT')
        return self._socketcommunication.receive()

    def get_stage_1_heating_power(self):
        #  Returns the current stage 1 heater power reading or -0.100 to indicate the stage 1
        #  heater power is not available.
        #  Units: Watts
        self._socketcommunication.send('GS1HP')
        return self._socketcommunication.receive()

    def get_stage_1_temperature(self):
        #  Returns the current stage 1 temperature or -0.10 to indicate the stage 1 temperature
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GS1T')
        return self._socketcommunication.receive()

    def get_stage_2_temperature(self):
        #  Returns the current stage 2 temperature or -0.10 to indicate the stage 2 temperature
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GS2T')
        return self._socketcommunication.receive()

    def get_sample_stability(self):
        #  Returns the current sample stability or -0.10000 to indicate the sample stability
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GSS')
        return self._socketcommunication.receive()

    def get_sample_temperature(self):
        #  Returns the current sample temperature or -0.100 to indicate the sample temperature
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GST')
        return self._socketcommunication.receive()

    def get_temperature_set_point(self):
        #  Returns the current temperature set point
        #  Units: Kelvin
        self._socketcommunication.send('GTSP')
        return self._socketcommunication.receive()

    def get_user_stability(self):
        #  Returns the current user stability or -0.10000 to indicate the user stability
        #  is not available.
        #  Units: Kelvin
        self._socketcommunication.send('GUS')
        return self._socketcommunication.receive()

    def get_user_temperature(self):
        #  Returns the current user temperature or -0.100 to indicate the user temperature
        #  is not available
        #  Units: Kelvin
        self._socketcommunication.send('GUT')
        return self._socketcommunication.receive()

    def get_user_temperature_set_point(self):
        #  Returns the current User module temperature set point
        #  Units: Kelvin
        self._socketcommunication.send('GUTSP')
        return self._socketcommunication.receive()

    def get_vacuum_pump_state(self):
        #  Returns the current vacuum pump state
        #  On/Off
        self._socketcommunication.send('GVPS')
        return self._socketcommunication.receive()

    def get_vent_valve_state(self):
        #  Returns the current vent valve state
        #  On/Off
        self._socketcommunication.send('GVVS')
        return self._socketcommunication.receive()

    def start_cool_down(self):
        #  returns status of command (OK/System not able to cool down at this time)
        self._socketcommunication.send('SCD')
        return self._socketcommunication.receive()

    def set_magnet_disabled(self):

        self._socketcommunication.send('SMD')
        return self._socketcommunication.receive()










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




