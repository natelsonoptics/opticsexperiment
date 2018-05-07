#!/usr/bin/env python3
import socket


class CryoComm:
    "Class to provide python communication with a Cryostation"

    def __init__(self, ip='localhost', port=7773):
        "CryoComm - Constructor"

        self.ip = ip
        self.port = port
        self.socket = None

        # Connect to the Cryostation
        try:
            self.socket = socket.create_connection((ip, port), timeout=10)
        except Exception as err:
            print("CryoComm:Connection error - {}".format(err))
            raise err

        self.socket.settimeout(5)

    def __send(self, message):
        "CryoComm - Send a message to the Cryostation"

        total_sent = 0

        # Prepend the message length to the message.
        message = str(len(message)).zfill(2) + message

        # Send the message
        while total_sent < len(message):
            try:
                sent = self.socket.send(message[total_sent:].encode())
            except Exception as err:
                print("CryoComm:Send communication error - {}".format(err))
                raise err

            # If sent is zero, there is a communication issue
            if sent == 0:
                raise RuntimeError("CryoComm:Cryostation connection lost on send")
            total_sent = total_sent + sent

    def __receive(self):
        "CryoComm - Receive a message from the Cryostation"

        chunks = []
        received = 0

        # Read the message length
        try:
            message_length = int(self.socket.recv(2).decode('UTF8'))
        except Exception as err:
            print("CryoComm:Receive message length communication error - {}".format(err))
            raise err

        # Read the message
        while received < message_length:
            try:
                chunk = self.socket.recv(message_length - received)
            except Exception as err:
                print("CryoComm:Receive communication error - {}".format(err))
                raise err

            # If an empty chunk is read, there is a communication issue
            if chunk == '':
                raise RuntimeError("CryoComm:Cryostation connection lost on receive")
            chunks.append(chunk)
            received += len(chunk)

        return ''.join([x.decode('UTF8') for x in chunks])

    def send_command_get_response(self, message):
        "CryoComm - Send a message to the Cryostation and receive a response"

        self.__send(message)
        return self.__receive()

    def __del__(self):
        "CryoComm - Destructor"

        if self.socket:
            self.socket.shutdown(1)
            self.socket.close()