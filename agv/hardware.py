# =====================================================================
# hardware.py - thin wrappers around the PicoBot I/O.
# Only this file talks to machine.Pin / PWM / Timer, so the rest of the
# code reads like "drive", "sensors", "button".
# =====================================================================
from machine import Pin, PWM, Timer
from agv import config as C


class StopRequested(Exception):
    """Raised inside any motion loop when the stop button is pressed."""


class Motor:
    def __init__(self, dir_pin, pwm_pin, invert, trim):
        self.dir = Pin(dir_pin, Pin.OUT)
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(1000)
        self.pwm.duty_u16(0)
        self.invert = invert
        self.trim = trim

    def set(self, speed):
        """speed: -100..100 (%). Negative = backwards."""
        forward = speed >= 0
        if self.invert:
            forward = not forward
        mag = min(100, abs(speed)) * self.trim
        if 0 < mag < C.MIN_DUTY:
            mag = C.MIN_DUTY
        self.dir.value(C.MOTOR_FORWARD if forward else 1 - C.MOTOR_FORWARD)
        self.pwm.duty_u16(int(65535 * mag / 100))

    def off(self):
        self.pwm.duty_u16(0)


class Drive:
    """Two-wheel differential drive. left/right in % (-100..100)."""

    def __init__(self):
        self.left = Motor(C.LEFT_MOTOR_DIR_PIN, C.LEFT_MOTOR_PWM_PIN, C.LEFT_MOTOR_INVERT, C.LEFT_TRIM)
        self.right = Motor(C.RIGHT_MOTOR_DIR_PIN, C.RIGHT_MOTOR_PWM_PIN, C.RIGHT_MOTOR_INVERT, C.RIGHT_TRIM)

    def set(self, left, right):
        self.left.set(left)
        self.right.set(right)

    def spin(self, side, speed):
        """Spin on the spot towards side ('L' or 'R')."""
        if side == 'R':
            self.set(speed, -speed)
        else:
            self.set(-speed, speed)

    def stop(self):
        self.left.off()
        self.right.off()


class LineSensors:
    def __init__(self):
        self.pins = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in C.LINE_SENSOR_PINS]

    def read(self):
        """Tuple of 4 values, 1 = white line under that sensor. Order: LO, LI, RI, RO."""
        return tuple(1 if p.value() == C.LINE_WHITE else 0 for p in self.pins)


class NoButton:
    """Used while no button is fitted: never pressed, never stops the run."""
    armed = False

    def pressed(self):
        return False

    def check(self):
        pass


class Button:
    def __init__(self):
        self.pin = Pin(C.BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        self.stop_flag = False
        self.armed = False
        self.pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._irq)

    def pressed(self):
        return self.pin.value() == C.BUTTON_PRESSED

    def _irq(self, pin):
        if self.armed and C.BUTTON_STOPS_RUN and pin.value() == C.BUTTON_PRESSED:
            self.stop_flag = True

    def check(self):
        """Call from every motion loop: raises StopRequested after a press."""
        if self.stop_flag:
            raise StopRequested()


class Rangefinder:
    """VL53L0X time-of-flight sensor at the front (only for RACK_STOP_MODE = 'tof')."""

    def __init__(self):
        from machine import I2C
        from libs.VL53L0X.VL53L0X import VL53L0X     # same library as test_vl53l0x.py
        self.dev = VL53L0X(I2C(id=0, sda=Pin(8), scl=Pin(9)))
        self.dev.start()

    def mm(self):
        return self.dev.read()


class AmberLight:
    """Flashing amber light driven by a hardware timer, so it keeps
    flashing while the main code is busy in a loop or a sleep."""

    def __init__(self):
        self.pin = Pin(C.AMBER_LED_PIN, Pin.OUT, value=0)
        self.timer = Timer()

    def flash(self):
        self.timer.init(freq=2 * C.AMBER_FLASH_HZ, mode=Timer.PERIODIC,
                        callback=lambda t: self.pin.toggle())

    def off(self):
        self.timer.deinit()
        self.pin.value(0)
