import socket
from optics.hardware_control.hardware_addresses_and_constants import cryostation_ip_address, cryostation_port
import contextlib
import time
from sys import exit


@contextlib.contextmanager
def connect_socket(ip, port, connecttimeout=10, sockettimeout=5):
    sock = socket.create_connection((ip, port), timeout=connecttimeout)
    try:
        yield SocketCommunication(sock, sockettimeout)
    finally:
        sock.shutdown(1)
        sock.close()


@contextlib.contextmanager
def connect_cryostation(ip, port, connecttimeout=10, sockettimeout=5):
    with connect_socket(ip, port, connecttimeout, sockettimeout) as socketcommunication:
        yield CryostationCommuncation(socketcommunication)


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
        self._current_stability = 0
        self._current_temperature = 0

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
        return float(self._socketcommunication.receive())

    def get_platform_temperature(self):
        """Returns the current platform temperature or -0.100 to indicate the platform temperature is not available.
        Units: Kelvin"""
        self._socketcommunication.send('GPT')
        return float(self._socketcommunication.receive())

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

    def is_temperature_stable(self, target_stability):
        self._current_stability = self.get_platform_stability()
        if self._current_stability > target_stability and self._current_stability != 0:
            return True
        else:
            return False

    def is_at_temperature(self, target_temperature, cooldown=True):
        self._current_temperature = self.get_platform_temperature()
        if cooldown:
            if self._current_temperature <= target_temperature and self._current_temperature != 0:
                return True
            else:
                return False
        else:
            if self._current_temperature >= target_temperature and self._current_temperature != 0:
                return True
            else:
                return False

    def cool_down(self, target_temperature, target_stability=0.04, timeout=21600):
        max_time = time.time() + timeout
        if self.start_cool_down() != 'OK':
            print('Failed to initiate cooldown')
            self.start_warm_up()
            exit(1)
        self.set_temperature_set_point(target_temperature)
        while not self.is_at_temperature(target_temperature):
            self._current_temperature = self.get_platform_temperature()
            time.sleep(3)
            if time.time() > max_time:
                print('Timed out during cooldown')
                self.start_warm_up()
                exit(1)
        while not self.is_temperature_stable(target_stability):
            self._current_stability = self.get_platform_stability()
            time.sleep(3)
            if time.time() > max_time:
                print('Timed out during cooldown')
                self.start_warm_up()
                exit(1)
        self._current_temperature = self.get_platform_temperature()
        self._current_stability = self.get_platform_stability()
        self.start_standby()
        print(str('Cooldown successful. Current temperature: {}. '
                  'Current stability: {}').format(self._current_temperature, self._current_stability))

    def step_temperature(self, delta_temperature, target_stability=0.04, timeout=3000):
        max_time = time.time() + timeout
        self._current_temperature = self.get_platform_temperature()
        target = self._current_temperature + delta_temperature
        cooldown = True
        if target > self._current_temperature:
            cooldown = False
        self.set_temperature_set_point(target)
        while not self.is_at_temperature(target, cooldown=cooldown):
            self._current_temperature = self.get_platform_temperature()
            time.sleep(3)
            if time.time() > max_time:
                print('Timed out during step up')
                exit(1)
        while not self.is_temperature_stable(target_stability):
            self._current_stability = self.get_platform_stability()
            time.sleep(3)
            if time.time() > max_time:
                print('Timed out during step up')
                exit(1)
        self.start_standby()
        return self.get_platform_temperature(), self.get_platform_stability()
























































