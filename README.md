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
