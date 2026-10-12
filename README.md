# Motor cheat sheet

```python
import motor

motor.set_motor3(motor.FORWARD, 50)   # direction, speed 0-100
motor.set_motor4(motor.REVERSE, 30)
motor.motor3_off()
motor.motors_off()                    # stop both — always end with this
```

Motor keeps running at the last speed until changed or turned off.

# Servo cheat sheet

```python
import servo

servo.set_servo1(135)   # angle 0-270 (135 = centre)
servo.servo1_off()      # go limp
```

Servo holds its angle until changed or turned off.

# Line sensor cheat sheet

```python
import line_sensor

line_sensor.read_sensors()      # [0, 1, 1, 0] — jumper pins 24, 25, 26, 27 (GP18-21)
line_sensor.print_sensors(30)   # print readings every 0.1 s for 30 seconds
```

Each reading is 0 or 1 (black or white). Check which is which on your sensor.

# Line following cheat sheet

```python
import line_follow

line_follow.follow_line(10)                   # follow for 10 seconds at speed 100
line_follow.follow_line(10, base_speed=60)    # slower
```

| Sensors | Junction | Correction |
|---|---|---|
| `0000` | | none |
| `0001` | | motor 4 large |
| `0010` | | motor 4 small |
| `0011` | right turn | none |
| `0100` | | motor 3 small |
| `0111` | right turn | motor 4 small |
| `1000` | | motor 3 large |
| `1001` | crossroad | none |
| `1100` | left turn | none |
| `1110` | left turn | motor 3 small |
| `1111` | crossroad | none |
| anything else | | ignored (none) |

A correction slows that motor (small = 20, large = 40) until the reading changes. Junctions are printed when first seen. Edit `SMALL`, `LARGE` and the `ACTIONS` table in `line_follow.py`. Motors turn off when the time is up.

# Sleep cheat sheet

```python
from utime import sleep, sleep_ms

sleep(2)        # pause 2 seconds (floats OK: sleep(0.5))
sleep_ms(100)   # pause 100 milliseconds
```

Motors and servos keep doing their last command while sleeping. Use sleep to set how long an action runs.
