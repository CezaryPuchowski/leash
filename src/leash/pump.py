"""Manager for controlling and reading pressure from pumps."""

import re
import time
from logging import Logger


class Pump:
    """Class for controlling pump."""

    def __init__(self, index:str, sm:str, log:Logger)->None:
        """Initialize of Pump class."""
        self.index = index
        self.sm = sm
        self.log = log

    def get_pressure(self):
        """Read pressure from pump."""
        try:
            if self.index == "LEFT":
                #selects vac 1 through multiplexer
                self.sm.send("M260 A112 B1 S1")

            elif self.index == "RIGHT":

                #selects vac 2 through multiplexer
                self.sm.send("M260 A112 B2 S1")

            self.sm.send("M260 A109")
            self.sm.send("M260 B48")
            self.sm.send("M260 B27")
            self.sm.send("M260 S1")

            time.sleep(0.03)

            #read addresses 0x06 0x07 and 0x08 for pressure reading
            self.sm.send("M260 A109 B6 S1")
            msb = re.search("data:(..)", self.sm.send("M261 A109 B1 S1"))

            self.sm.send("M260 A109 B7 S1")
            csb = re.search("data:(..)", self.sm.send("M261 A109 B1 S1"))

            self.sm.send("M260 A109 B8 S1")
            lsb = re.search("data:(..)", self.sm.send("M261 A109 B1 S1"))

            val = msb.group(1)+csb.group(1)+lsb.group(1)

            result = int(val, 16)

            if(result & (1 << 23)):
                result = result - 2**24

            return result

        except Exception as e:
            self.log.error(e)
            return False



        # try:


        #     #read addresses 0x06 0x07 and 0x08 for pressure reading
        #     self.sm.send("M260 A109 B6 S1")
        #     msb = re.search("data:(..)", self.sm.send("M261 A109 B1 S1"))

        #     self.sm.send("M260 A109 B7 S1")
        #     csb = re.search("data:(..)", self.sm.send("M261 A109 B1 S1"))

        #     self.sm.send("M260 A109 B8 S1")
        #     lsb = re.search("data:(..)", self.sm.send("M261 A109 B1 S1"))

        #     val = msb.group(1)+csb.group(1)+lsb.group(1)

        #     result = int(val, 16)

        #     if(result & (1 << 23)):
        #         result = result - 2**24

        #     return result
        # except Exception as e:
        #     print(e)
        #     return False

    def get_temperature(self)->bool:
        """Read temperature from pomp."""
        try:
            if self.index == "LEFT":
                #selects vac 1 through multiplexer
                self.sm.send("M260 A112 B1 S1")
            elif self.index == "RIGHT":
                self.sm.send("M260 A112 B2 S1")

            # Assuming sensor is an object or interface to communicate with the sensor

            # Read REG0x09 and REG0x0A
            self.sm.send("M260 A109 B9 S1")
            reg0x09 = re.search("data:(..)", self.sm.send("M261 A109 B1 S1")).group(1)

            self.sm.send("M260 A109 B10 S1")
            reg0x0a = re.search("data:(..)", self.sm.send("M261 A109 B1 S1")).group(1)

            # Calculate the temperature ADC value
            adc_value = int(reg0x09, base=16) * 256 + int(reg0x0a, base=16)

            # Determine if temperature is positive or negative
            if adc_value < 2**15:
                # Temperature is positive
                return adc_value / 256.0
            else:
                # Temperature is negative, apply the formula
                return (adc_value - 2**16) / 256.0

        except Exception as e:
            self.log.error(e)
            return False

    def off(self)->None:
        """Turn pump off."""
        if self.index == "LEFT":
            self.sm.send("M107")
            self.sm.send("M107 P1")

        elif self.index == "RIGHT":
            self.sm.send("M107 P2")
            self.sm.send("M107 P3")

    def on(self)->None:
        """Turn pump on."""
        if self.index == "LEFT":
            # turn on pump
            self.sm.send("M106")
            # turn on valve
            self.sm.send("M106 P1 S255")
            # self.sm.send("G4 50")
            # self.sm.send("M106 P1 S150")

        elif self.index == "RIGHT":
            #turn on pump
            self.sm.send("M106 P2 S255")
            #turn on valve
            self.sm.send("M106 P3 S255")
            # self.sm.send("G4 50")
            # self.sm.send("M106 P3 S150")
