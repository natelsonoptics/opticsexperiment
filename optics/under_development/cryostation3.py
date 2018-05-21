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
        # Prepend the message length to the message.
        message = str(len(message)).zfill(2) + message
        total_sent = 0

        # Send the message
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

        # Read the message length
        try:
            message_length = int(self._sock.recv(2).decode('UTF8'))
        except Exception as err:
            print("Socket Communication: Receive message length communication error - {}".format(err))
            raise err

        #  Read the message
        while received < message_length:
            try:
                chunk = self._sock.recv(message_length - received)
            except Exception as err:
                print("CryoComm:Receive communication error - {}".format(err))
                raise err

            # If an empty chunk is read, there is a communication issue
            if chunk == '':
                raise RuntimeError("Socket connection lost on receive")
            chunks.append(chunk)
            received += len(chunk)

        return ''.join([x.decode('UTF8') for x in chunks])


class CryostationCommuncation:
    def __init__(self, socketcommunication):
        self._socketcommunication = socketcommunication

    def get_alarm_state(self):
        """Returns true or false indicating the presence or absence of a system error"""
        self._socketcommunication.send('GAS')
        return self._socketcommunication.receive()

    def get_chamber_pressure(self):
        """Returns the current chamber pressure or -0.1 to indicate the chamber pressure is not available.
        Units: mTorr"""
        self._socketcommunication.send('GCP')
        return self._socketcommunication.receive()

    def get_compressor_run_state(self):
        """Returns the current run state of the compressor (on/off)"""
        self._socketcommunication.send('GCRS')
        return self._socketcommunication.receive()

    def get_compressor_speed(self):
        """Returns the current compressor speed or -0.1 to indicate the compressor speed is not available. Units: Hz"""
        self._socketcommunication.send('GSC')
        return self._socketcommunication.receive()

    def get_case_valve_state(self):
        """Returns the current case valve state (open/closed)"""
        self._socketcommunication.send('GCVS')
        return self._socketcommunication.receive()

    def get_cold_head_speed(self):
        """Returns the current cold head speed or -0.1 to indicate the cold head speed is not available. Units: Hz"""
        self._socketcommunication.send('GHS')
        return self._socketcommunication.receive()

    def get_magnet_state(self):
        """Returns the current magnet state. MAGNET ENABLED/MAGNET DISABLED/System not able to
        execute command at this time. Activate the magnet module first."""
        self._socketcommunication.send('GMS')
        return self._socketcommunication.receive()

    def get_magnet_target_field(self):
        """Returns the current set point for magnetic field or -9.999999 if the magnet is no enabled or
        the magnet module is not activated. Units: Tesla"""
        self._socketcommunication.send('GMTF')
        return self._socketcommunication.receive()

    def get_platform_heater_power(self):
        """Returns the current platform heater power reading or -0.100 to indicate the platform heater power
        is not available. Units: Watts"""
        self._socketcommunication.send('GPHP')
        return self._socketcommunication.receive()

    def get_platform_stability(self):
        """Returns the current platform stability or -0.10000 to indicate the platform stability is not
        available. Units: Kelvin"""
        self._socketcommunication.send('GPS')
        return self._socketcommunication.receive()

    def get_platform_temperature(self):
        """Returns the current platform temperature or -0.100 to indicate the platform temperature is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GPT')
        return self._socketcommunication.receive()

    def get_stage_1_heating_power(self):
        """Returns the current stage 1 heater power reading or -0.100 to indicate the stage 1 heater
        power is not available. Units: Watts"""
        self._socketcommunication.send('GS1HP')
        return self._socketcommunication.receive()

    def get_stage_1_temperature(self):
        """Returns the current stage 1 temperature or -0.10 to indicate the stage 1 temperature is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GS1T')
        return self._socketcommunication.receive()

    def get_stage_2_temperature(self):
        """Returns the current stage 2 temperature or -0.10 to indicate the stage 2 temperature is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GS2T')
        return self._socketcommunication.receive()

    def get_sample_stability(self):
        """Returns the current sample stability or -0.10000 to indicate the sample stability is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GSS')
        return self._socketcommunication.receive()

    def get_sample_temperature(self):
        """Returns the current sample temperature or -0.100 to indicate the sample temperature is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GST')
        return self._socketcommunication.receive()

    def get_temperature_set_point(self):
        """Returns the current temperature set point. Units: Kelvin"""
        self._socketcommunication.send('GTSP')
        return self._socketcommunication.receive()

    def get_user_stability(self):
        """Returns the current user stability or -0.10000 to indicate the user stability is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GUS')
        return self._socketcommunication.receive()

    def get_user_temperature(self):
        """Returns the current user temperature or -0.100 to indicate the user temperature is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GUT')
        return self._socketcommunication.receive()

    def get_user_temperature_set_point(self):
        """Returns the current User module temperature set point. Units: Kelvin"""
        self._socketcommunication.send('GUTSP')
        return self._socketcommunication.receive()

    def get_vacuum_pump_state(self):
        """Returns the current vacuum pump state (on/off)"""
        self._socketcommunication.send('GVPS')
        return self._socketcommunication.receive()

    def get_vent_valve_state(self):
        """Returns the current vent valve state (open/closed)"""
        self._socketcommunication.send('GVVS')
        return self._socketcommunication.receive()

    def start_cool_down(self):
        """Returns status of the command"""
        self._socketcommunication.send('SCD')
        return self._socketcommunication.receive()

    def set_magnet_disabled(self):
        """Returns status of the command"""
        self._socketcommunication.send('SMD')
        return self._socketcommunication.receive()

    def set_magnet_enabled(self):
        """Returns status of the command"""
        self._socketcommunication.send('SME')
        return self._socketcommunication.receive()

    def set_magnet_target_field(self, tesla):
        """Returns status of the set command and current value of the target magnetic field. Units: Tesla.
        Decimal value in range of -2.000000 to 2.000000"""
        self._socketcommunication.send('SMTF' + str(tesla))
        return self._socketcommunication.receive()

    def start_magnet_true_zero(self):
        """Returns status of the command"""
        self._socketcommunication.send('SMTZ')
        return self._socketcommunication.receive()

    def start_standby(self):
        """Returns status of the command"""
        self._socketcommunication.send('SSB')
        return self._socketcommunication.receive()

    def stop(self):
        """Returns status of the command"""
        self._socketcommunication.send("STP")
        return self._socketcommunication.receive()

    def set_temperature_set_point(self, temperature):
        """Takes a decimal value between 2.00 and 350.00. Units: Kelvin. Returns status of the set command and current
        temperature set point"""
        self._socketcommunication.send("STSP" + str(temperature))
        return self._socketcommunication.receive()

    def set_user_temperature_set_point(self, temperature):
        """Takes a decimal value in the user module temperature range. Units: Kelvin. Returns status of the command
        and current user module temperature set point"""
        self._socketcommunication.send("SUTSP" + str(temperature))
        return self._socketcommunication.receive()

    def start_warm_up(self):
        """Returns status of the command"""
        self._socketcommunication.send("SWU")
        return self._socketcommunication.receive()

    def set_target_platform_temperature(self, temperature, timeout=10):
        timeout = time.time() + timeout
        target_temperature = self.send_target_platform_temperature(temperature)
        while round(target_temperature, 2) != round(temperature, 2):
            if timeout > 0:
                if time.time() > timeout:
                    return False
            time.sleep(1)
            target_temperature = self.send_target_platform_temperature(temperature)
        return True

    def send_target_platform_temperature(self, temperature):
        target_temperature = 0
        try:
            if self.set_temperature_set_point(temperature).startswith("OK"):
                target_temperature = self.get_temperature_set_point()
        except Exception as err:
            print("Failed to send target temperature")
            exit(1)
        return float(target_temperature)

    def initialize_cooldown(self, temperature):
        if not self.set_target_platform_temperature(temperature):
            print("Timed out setting cooldown target platform temperature")
            exit(1)
        try:
            if self.start_cool_down() != "OK":
                print("cooldown did not initiate")
                exit(1)
        except Exception as err:
            print("Failed to initiate cooldown")
            exit(1)

    def wait_for_cooldown_and_stability(self, temperature, target_stability, cooldown_timeout, stability_timeout):
        if cooldown_timeout > 0:
            cooldown_timeout = time.time() + cooldown_timeout
        while True:
            time.sleep(3)
            if time.time() > cooldown_timeout:
                return False
            try:
                current_temperature = float(self.get_platform_temperature())
            except Exception as err:
                current_temperature = 0
            if current_temperature <= temperature and current_temperature > 0:
                break
        if stability_timeout > 0:
            stability_timeout = stability_timeout + time.time()
        while True:
            time.sleep(3)
            if stability_timeout > 0:
                if time.time() > stability_timeout:
                    print("Timed out waiting for cooldown stability")
                    return False
            try:
                current_stability = float(self.get_platform_stability())
            except Exception as err:
                current_stability = 0
            if current_stability <= target_stability and current_stability > 0:
                return True

    def step_up(self, step_size, max_temperature, timeout, target_stability, stability_timeout):
        step_target = -1

        while step_target < 0:
            try:
                step_target = float(self.get_temperature_set_point())
            except Exception as err:
                step_target = -1
            time.sleep(1)

        step_target += step_size
        while round(step_target, 2) <= round(max_temperature, 2):
            if not self.set_target_platform_temperature(step_target):
                print("Timed out setting step-up platform temperature")
                exit(1)
        if timeout > 0:
            timeout = time.time() + timeout
        while True:
            if timeout > 0:
                if time.time() > timeout:
                    print("Timed out waiting for step-up target platform temperature")
                    return False
            try:
                current_temperature = float(self.get_platform_temperature())
            except Exception as err:
                current_temperature = 0
            if current_temperature >= step_target and current_temperature > 0:
                break
            time.sleep(3)

            if stability_timeout > 0:
                stability_timeout = time.time() + stability_timeout
            while True:
                if stability_timeout > 0:
                    if time.time() > stability_timeout:
                        print("Timed out waiting for step-up target platform stability")
                        return False
                try:
                    current_stability = float(self.get_platform_stability())
                except Exception as err:
                    current_stability = 0
                if current_stability <= target_stability and current_stability > 0:
                    break
                time.sleep(3)
            step_target += step_size
        return True



























