# Leash

Leash is a control API for the LumenPnP written in Python. It is meant to be used as an easy way to automate actions with the LumenPnP.

It contains:

- Machine axis control
- Pump and valve control
- Ring light control
- Vacuum sensor reading
- Full Photon bus control
- Image capture from both cameras

This library is subject to change with non-backwards compatible refactoring. It is still actively in development.

## Usage

To install (ideally in a virtual environment), use:

```bash
pip install git+https://github.com/opulo-inc/leash.git
```

It can help to include the `--force-reinstall` flag in this command to make sure you're getting the latest version.

From here, it's easy to connect to a Lumen:

```python
from leash import Lumen

lumen = Lumen()

if lumen.connect():
    try:
        lumen.home()

        # Setting speed in mm/min linear travel speed
        lumen.set_speed(f=40000)

        # sending arbitrary gcode (in this example bumping current of right toolhead to 300ma)
        lumen.sm.send("M906 B300")

        # .goto() sends a move command with any optional arguments x, y, z, a, and b
        lumen.goto(x=10, y=10)
        lumen.goto(z=20)

        lumen.safe_z()

        # To make sure Lumen actions align with your code timing, use lumen.sleep()
        # This just makes sure all commands are complete before delaying
        # lumen.sleep() can be handy in situations where you want to keep a pump
        # on for a certain amount of time, for example:
        #
        #   lumen.right_pump.on()
        #   lumen.sleep(1)
        #   lumen.right_pump.read_pressure()
        #   lumen.right_pump.off()
        #

        lumen.sleep(2)

        # If you need more control, you can use lumen.finish_moves() which blocks until
        # the Lumen's command queue is empty
        lumen.finish_moves()
        # You can then use any other python specific delays or timing functions afterwards
        time.sleep(1)

        # Pumps

        lumen.left_pump.on()
        lumen.sleep(1)
        print("Left sensor pressure: " + str(lumen.left_pump.get_pressure()))
        lumen.left_pump.off()

        lumen.right_pump.on()
        lumen.sleep(1)
        print("Right sensor pressure: " + str(lumen.right_pump.getPressure()))
        lumen.right_pump.off()

        print("Left sensor temperature: " + str(lumen.left_pump.getTemperature())))
        print("Right sensor temperature: " + str(lumen.right_pump.getTemperature()))

        # Ring Lights

        lumen.light_on("TOP", 218, 165, 32, 255)
        lumen.sleep(1)
        lumen.light_off("TOP")

        lumen.light_on("BOT", 218, 165, 32, 255)
        lumen.sleep(1)
        lumen.light_off("BOT")

        # Feeders

        lumen.photon.scan()
        print(lumen.photon.active_feeders)

        # lumen.idle() disables all pumps, valves, lights, and jogs the machine back and out of the way
        lumen.idle()

    except KeyboardInterrupt:
        lumen.idle()


```

TODO

- uvc exposure support [https://github.com/jtfrey/uvc-util/tree/master]
- A few more simple vision commands (fid and rect position)
