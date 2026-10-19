# =====================================================================
# calibrate.py - one small test per number in config.py.
# Run in the MicroPico / Thonny REPL, for example:
#     from agv import calibrate as cal
#     cal.sensors()          # Ctrl-C to stop
# Every test stops the motors when it ends or when you press Ctrl-C.
# =====================================================================
from utime import sleep_ms, ticks_ms, ticks_diff
from agv import config as C
from agv.hardware import Drive, LineSensors, Button, NoButton, AmberLight
from agv.nav import Navigator

drive = Drive()
line = LineSensors()
button = Button() if C.USE_BUTTON else NoButton()
nav = Navigator(drive, line, button)


def _safe(fn):
    def wrapped(*a, **k):
        try:
            return fn(*a, **k)
        finally:
            drive.stop()
    return wrapped


@_safe
def sensors(period_ms=100):
    """Move a line under each sensor by hand: the order must be LO LI RI RO
    and white must read 1. Also find the best sensor height here."""
    while True:
        print(line.read())
        sleep_ms(period_ms)


@_safe
def straight(ms=3000, speed=None):
    """Both wheels forward. Must go forward (else fix *_INVERT) and straight
    (else change LEFT_TRIM / RIGHT_TRIM). Also measure speed: mm / s."""
    speed = speed or C.BASE_SPEED
    nav.run_for(ms, speed, speed)


@_safe
def spin(side='R', ms=None):
    """Timed spin at TURN_SPEED. Adjust TURN_90_MS (and TURN_180_MS with
    spin('R', C.TURN_180_MS)) until the robot turns exactly 90 / 180 deg."""
    ms = ms or C.TURN_90_MS
    nav.run_for(ms, *nav._spin_speeds(side))


@_safe
def axle():
    """Put the sensors just ON a crossing line, then run. The wheel axle must
    end exactly over that line; otherwise change SENSOR_TO_AXLE_MS."""
    nav.to_axle()


@_safe
def follow(ms=10000):
    """Pure line following for ms. Tune KP first (KD = 0), then add KD."""
    nav.last_err = 0
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < ms:
        nav._steer(line.read(), C.BASE_SPEED)
        sleep_ms(C.LOOP_MS)


@_safe
def junctions(n=3):
    """Follow and print every junction (L / R / LR). Each junction must be
    counted exactly once: if not, tune JUNCTION_CONFIRM / CLEAR / MIN_GAP."""
    for _ in range(n):
        nav.follow(1)
        nav.to_axle()


@_safe
def turn(side='L'):
    """Sensors on a junction: creep onto it and turn. It must stop with the
    new line between the two inner sensors."""
    nav.to_axle()
    nav.turn(side)


@_safe
def rack():
    """Turned into a rack bay line (sensors just past the side line): runs the
    rack approach. Tune RACK_APPROACH_MS until it stops a safe gap before the rack."""
    from agv.hardware import Rangefinder
    nav.follow_into_rack(Rangefinder() if C.RACK_STOP_MODE == 'tof' else None)


@_safe
def corner():
    """Start on a side line facing the bottom corner: must stop with the axle on the corner."""
    nav.follow_to_corner()


def button_test():
    while True:
        print('pressed' if button.pressed() else '-')
        sleep_ms(200)


def amber(ms=5000):
    a = AmberLight()
    a.flash()
    sleep_ms(ms)
    a.off()
