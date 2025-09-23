"""Manager for serial communications."""

import re
import time
from logging import Logger

import serial
import serial.tools.list_ports


class SerialManager:
    """Class for serial communications."""

    def __init__(self, log:Logger)->None:
        """Initialize serial connection."""
        self.ser = serial.Serial()
        self.ser.baudrate = 119200
        self.ser.timeout = 1
        self.log = log

    def clear_queue(self, timeout:float=3)->bool:
        """Wait until queue are clear or timeout runs out."""
        messages = [
            "M400",
            "M118 E1 done"
        ]

        # send messages
        for i in messages:
            self.log.debug("Clear queue request send.")
            response = self.send(i)
            re_match = re.search("echo:done", response)
            if re_match is not None:
                return True

        #wait for done to arrive with timeout
        start = time.perf_counter()

        while True:
            response = self.ser.readline().decode("utf-8")
            re_match = re.search("echo:done", response)
            if re_match is not None:
                return True

            if time.perf_counter() - start > timeout:
                self.log.warning("Clear queue timeout!")
                return False

    def scan_ports(self)->bool:
        """Scan ports to find Lumen device."""
        comports = serial.tools.list_ports.comports()

        device_id = "0483:5740"

        for port, desc, hwid in sorted(comports):
            if device_id in hwid:
                try:
                    s = serial.Serial(port)
                    s.close()
                    self.log.debug("Found motherboard at port: " + " with hwid: " + hwid)
                    self.ser.port = port
                    return True

                except (OSError, serial.SerialException):
                    pass

        self.log.error("Was unable to find a connected Lumen")
        return False

    def open_serial(self)->bool:
        """Try open serial port."""
        if self.ser.is_open:
            self.log.debug("Serial port already open")
            return True

        if self.ser.port != "":
            self.ser.open()
            self.ser.timeout = 1
        else:
            self.log.error("No serial port selected")
            return False

        if self.ser.is_open:
            log_message = f"Connected to Lumen over serial port: {self.ser.port}"
            self.log.debug(log_message)
            self.ser.read_all()
            return True
        self.log.error("Couldn't open serial port")
        return False

    def send(self, message:str)->bool|str:
        """Send data to open port.

        Send can return two things
        it can return bool False if port isn't open
        or it can respond with marlin's response
        """
        #check to see if serial port is open
        if self.ser.is_open:
            self.ser.reset_input_buffer()
            encoded = message.encode("utf-8")
            self.ser.write(encoded + b"\n")
            resp = self.ser.readline().decode("utf-8")
            log_message = f"Sended command: {message} and received: {resp}"
            self.log.debug(log_message)
            return resp
        self.log.error("Serial port isn't open.")
        return False

    def send_blind(self, message:str)->bool:
        """Send data to port without waiting for respond."""
        if self.ser.is_open:
            self.ser.reset_input_buffer()
            encoded = message.encode("utf-8")
            self.ser.write(encoded + b"\n")
            log_message = f"Sended command: {message} without waiting for "
            log_message+= "response."
            self.log.debug(log_message)
            return True
        self.log.error("Serial port isn't open.")
        return False

    def send_rtn_lines(self, message:str)->bool|str:
        """Send data to port and receive multiline respond.

        Send can return two things
        it can return bool False if port isn't open
        or it can respond with marlin's response
        """
        #check to see if serial port is open
        if self.ser.is_open:
            self.ser.reset_input_buffer()
            encoded = message.encode("utf-8")
            self.ser.write(encoded + b"\n")
            resp = self.ser.readlines()
            decoded_resp = ""
            i = 0
            while i < len(resp):
                decoded_resp = decoded_resp + resp[i].decode("utf-8")
                i = i + 1
            return decoded_resp
        self.log.error("Serial port isn't open.")
        return False
