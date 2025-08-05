"""Manager for communicating with a Photon Feeder Bus."""

import enum
import re
from logging import Logger

from .serial import SerialManager

MAX_ADDRESS = 0x0FF

class Commands(enum.IntEnum):
    """Enum class with commands."""

    GET_FEEDER_ID = 0x01
    INITIALIZE_FEEDER = 0x02
    GET_VERSION = 0x03
    MOVE_FEED_FORWARD = 0x04
    MOVE_FEED_BACKWARD = 0x05
    MOVE_FEED_STATUS = 0x06
    VENDOR_OPTIONS = 0xbf
    GET_FEEDER_ADDRESS = 0xc0
    IDENTIFY_FEEDER = 0xc1
    PROGRAM_FEEDER_FLOOR = 0xc2
    UNINITIALIZED_FEEDERS_RESPOND = 0xc3

class Photon:
    """Photon feeder class."""

    def __init__(self, sm:SerialManager, log:Logger)->None:
        """Initialize Photon feeder."""
        self.sm = sm
        self.log = log
        self._packetID = 0x00
        self._outstandingPackets = []
        self.activeFeeders = []

    def crc(self, data:list) -> int:
        """Calculate CRC."""
        crc: int = 0
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc ^= (0x1070 << 3)
                crc <<= 1
        return (crc >> 8) & 0xFF

    def byte_array_to_string(self, byte_array:list)->str:
        """Convert byte array to string."""
        hex_string = ""
        for i in byte_array:
            converted = hex(i)[2:]
            if len(converted) == 1:
                converted = "0" + converted
            hex_string += converted
        return hex_string

    def increment_packet_id(self)->None:
        """Increment id of packet."""
        hex_max_value = 0xFF
        if self._packetID == hex_max_value:
            self._packetID = 0x00
        else:
            self._packetID = self._packetID + 1

    def build_packet_from_bytes(self, packet:list)->str:
        """Build packet from given list of parts."""
        crc = self.crc(packet)
        packet.insert(4, crc)
        packet_string = "M485 "
        # convert byte to string and append to packetString
        for i in packet:
            converted = hex(i)[2:]
            if len(converted) == 1:
                converted = "0" + converted
            packet_string = packet_string + converted

        return packet_string

    def build_bytes_from_packet(self, response:str)->list:
        """Build byte list from packet."""
        byte_array = []
        for i in range(int(len(response)/2)):
            index = i*2
            sliced = response[index:index+2]
            hexed = int(sliced, 16)
            byte_array.append(hexed)
        return byte_array


    def send_packet(self, address:int, command: Commands,
                    payload:list|None = None)->list:
        """Send packet to LumenPnP."""
        self.log.debug("Sending packet payload: " + str(payload))
        # builds a packet without crc
        if payload is None:
            packet = [address, 0x00, self._packetID, 1, command]
        else:
            packet = [address, 0, self._packetID,
                      len(payload) + 1, command, *payload]
        sent_packet_id = self._packetID
        gcode = self.build_packet_from_bytes(packet)
        self.log.debug("Gcode to send: " + str(gcode))
        # open serial, send packet, close it
        self.sm.ser.read_all()
        response = self.sm.send(gcode).strip()
        self.increment_packet_id()
        re_match = re.search("rs485-reply: (.*)", response).group(1)

        if re_match in {None, "TIMEOUT"}:
            return -1
        byte_array = self.build_bytes_from_packet(re_match)

        if byte_array[0] != 0x00:
            self.log.error("Received packet not addressed to host.")
            return False

        if byte_array[1] != address and address != MAX_ADDRESS:
            self.log.error("Received packet not from intended recipient.")
            return False

        if byte_array[2] != sent_packet_id:
            self.log.error("Received packet with wrong packet id.")
            return False

        if byte_array[3] != len(byte_array) - 5:
            self.log.error("Received packet has wrong payload length.")
            return False

        sacrificial_crc = byte_array
        received_crc = sacrificial_crc[4]
        del sacrificial_crc[4]
        calc_crc = self.crc(sacrificial_crc)

        if received_crc != calc_crc:
            self.log.error("Received packet with wrong crc.")
            return False

        return byte_array[4:]

    ## UNICAST

    def get_feeder_uuid(self, address):

        self.log.debug("Requesting UUID from address: " + str(address))
        resp = self.send_packet(address, Commands.GET_FEEDER_ID)

        if resp == -1:
            return -1
        if not resp:
            return False
        if resp[0] != 0x00:
            return -2
        if len(resp[1:]) == 12:
            return resp[1:]
        return False

    def initialize_feeder(self, address, uuid)->bool:

        self.log.debug("Requesting init at address: " + str(address))
        resp = self.send_packet(address, Commands.INITIALIZE_FEEDER, payload = uuid)
        return bool(resp != -1 and resp[0] == 0)

    def get_version(address):
        raise NotImplementedError

    def move_feed_forward(self, address, tenths)->bool:

        self.log.debug("Requesting " + str(tenths) + " feed from address: " + str(address))
        resp = self.send_packet(address, Commands.MOVE_FEED_FORWARD, payload = [tenths])
        return resp[0] == 0

    def move_feed_backward(self, address, tenths)->bool:

        resp = self.send_packet(address, Commands.MOVE_FEED_BACKWARD, payload = [tenths])
        return resp[0] == 0

    def move_feed_status(self, address)->bool:

        resp = self.send_packet(address, Commands.MOVE_FEED_STATUS)
        return resp[0] == 0

    def vendor_options(self, address, payload)->bool:

        resp = self.send_packet(address, Commands.MOVE_FEED_FORWARD, payload = payload)
        return resp[0] == 0

    def scan(self, min = 1, max = 50):

        for i in range(min, max):

            #see if a feeder is there
            uuid = self.get_feeder_uuid(i)

            #if we got a response
            if uuid is not None and uuid != -1 and uuid != -2:

                #initialize
                if self.initialize_feeder(i, uuid):

                    self.log.debug("Initialized feeder " + str(uuid) + " at address " + str(i))

                    # add to list of active feeders
                    self.activeFeeders.append(uuid)

                else:
                    self.log.error("Found feeder at " + str(i) + " but couldn't initialize")

    ## BROADCAST

    def get_feeder_address(uuid):
        raise NotImplementedError

    def identify_feeder(self, uuid)->bool:

        message = f"Requesting identify from UUID: {uuid!s}"
        self.log.debug(message)
        resp = self.send_packet(0xFF, Commands.IDENTIFY_FEEDER, payload = uuid)
        return resp[0] == 0

    def program_feeder_floor(uuid, addressToProgram):
        raise NotImplementedError

    def uninitialized_feeders_respond():
        raise NotImplementedError
