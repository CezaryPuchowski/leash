"""Initialization file of Lumen module."""
import logging
import time

from .camera import Camera
from .photon import Photon
from .pump import Pump
from .serial import SerialManager

CMD_NAME = "leash"  # Lower case command and module name
APP_NAME = "Leash"  # Application name in texts meant to be human readable
APP_URL = "https://github.com/opulo-inc/"

class Lumen:
    """Lumen object, containing all other subsystems."""

    def __init__(self, *,
                 top_cam:bool = False,
                 bot_cam:bool = False
                 )->None:
        """Initialize of Lumen class object."""
        self.log = logging.getLogger("Lumen")
        self.sm = SerialManager(self.log)
        self.photon = Photon(self.sm, self.log)
        self.leftPump = Pump("LEFT", self.sm, self.log)
        self.rightPump = Pump("RIGHT", self.sm, self.log)
        self.position = {
            "x": None,
            "y": None,
            "z": None,
            "a": 0,
            "b": 0
        }
        if top_cam is not False:
            self.topCam = Camera(top_cam, self.log)
        if bot_cam is not False:
            self.botCam = Camera(bot_cam, self.log)
        self._boot_commands = [
            "G90",
            "M260 A112 B1 S1",
            "M260 A109",
            "M260 B48",
            "M260 B27",
            "M260 S1",
            "M260 A112 B2 S1",
            "M260 A109",
            "M260 B48",
            "M260 B27",
            "M260 S1",
            "G0 F50000",
            "M204 T4000",
            "G90"
        ]
        self._pre_home_commands = [
            "M204 T2000"
        ]
        self._post_home_commands = [
            "M204 T4000"
        ]
        self.parkX = 220
        self.parkY = 400
        self.parkZ = 31.5


    #####################
    # Serial
    #####################

    def connect(self)->bool:
        """Connect to LumenPnP. Returns True if successfully."""
        if self.sm.scan_ports() and self.sm.open_serial():
            self.send_boot_commands()
            return True
        return False

    def disconnect(self)->bool:
        """Disconnect from LumenPnP. Returns True if successfully."""
        self.sm.ser.close()
        return not self.sm.ser.is_open

    def finish_moves(self)->None:
        """Wait until all commands from Lumen queue are finish."""
        self.sm.clear_queue()

    def sleep(self, seconds:float)->None:
        """Wait additional amount of seconds after all commands are finish."""
        self.finish_moves()
        time.sleep(seconds)

    def get_hardware_id(self)->None:
        """Return hardware id."""
        # probe for all hardware pull-up pins, plus chimera jumper
        # if any of these commands fail, it means is probably v3 or earlier
        # this also uses M115 to learn about the firmware
        raise NotImplementedError

    #####################
    # Movement
    #####################

    def goto(self, *,
             x:float | None = None,
             y:float | None = None,
             z:float | None = None,
             a:float | None = None,
             b:float | None = None
             )->None:
        """Move Lumen head to given coordinates."""
        command = "G0"
        if x is not None:
            command = command + " X" + str(x)
            self.position["x"] = x
        if y is not None:
            command = command + " Y" + str(y)
            self.position["y"] = y
        if z is not None:
            command = command + " Z" + str(z)
            self.position["z"] = z
        if a is not None:
            command = command + " A" + str(a)
            self.position["a"] = a
        if b is not None:
            command = command + " B" + str(b)
            self.position["b"] = b
        self.log.info(command)
        self.sm.send(command)

    def set_speed(self, f:float | None = None)->None:
        """Set speed for Lumen head."""
        if f is not None:
            command = "G0 F" + str(f)
            self.sm.send(command)

    def send_boot_commands(self)->None:
        """Send boot commands to Lumen."""
        for i in self._boot_commands:
            if not self.sm.send(i):
                message = "Halted sending boot commands "
                message += "because sending failed."
                self.log.error(message)
                break


    def send_pre_homing_commands(self)->None:
        """Send pre homing commands to Lumen."""
        for i in self._pre_home_commands:
            if not self.sm.send(i):
                message = "Halted sending pre homing commands "
                message += "because sending failed."
                self.log.error(message)
                break

    def idle(self)->None:
        """Put Lumen in idle mode.

        Idle mode turns off pumps and lights, moves z axis to safe position
        and moves head to parking place.
        """
        self.leftPump.off()
        self.rightPump.off()
        self.light_off("TOP")
        self.light_off("BOT")
        self.safe_z()
        self.goto(x=self.parkX, y=self.parkY)


    def home(self, *, x:bool = True, y:bool = True, z:bool = True)->None:
        """Perform homing on given axis. Default on all axis."""
        self.log.info("Homing")
        self.send_pre_homing_commands()
        if x and y and z:
            self.sm.send("G28")
            self.position["x"] = 0
            self.position["y"] = 0
            self.position["z"] = 0
        elif x or y or z:
            command = "G28"
            if x:
                command = command + " X"
            if y:
                command = command + " Y"
            if z:
                command = command + " Z"
            self.sm.send(command)
        self.finish_moves()
        self.send_post_homing_commands()

    def send_post_homing_commands(self)->None:
        """Send post homing commands to Lumen."""
        for i in self._post_home_commands:
            if not self.sm.send(i):
                message = "Halted sending post homing commands "
                message += "because sending failed."
                self.log.error(message)
                break
    def safe_z(self)->None:
        """Move Z axis to safe position."""
        self.goto(z=self.parkZ)


    #####################
    # Leds
    #####################

    def light_off(self, index:str)->None:
        """Turn light off for given camera index."""
        s = 0 if index == "BOT" else 1
        self.sm.send(f"M150 P0 R0 U0 B0 S{s}")

    def light_on(self,
                 index:str,
                 r:int=255,
                 g:int=255,
                 b:int=255,
                 a:int=255
                 )->None:
        """Turn light on for given camera index, with given color settings."""
        s = 0 if index == "BOT" else 1
        self.sm.send(f"M150 P{a} R{r} U{g} B{b} S{s}")
        self.log.info("turned on light yo")
