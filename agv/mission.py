# =====================================================================
# mission.py - what the robot does, step by step.
#
# Line following test:  start box -> loading area (pickup) -> turn round
#                       -> rack bay (unload) -> back into the start box.
# Change PICKUP / DROP to use another loading area or rack bay.
# =====================================================================
from utime import sleep_ms
from agv import config as C
from agv.hardware import Drive, LineSensors, Button, NoButton, Rangefinder, AmberLight, StopRequested
from agv.nav import Navigator, NavError
from agv import table_map as M

PICKUP = 'LA3'     # loading area 3 (route in "Line Test 1.png")
DROP = 'B2L'       # lower rack B2


class Robot:
    def __init__(self):
        self.drive = Drive()
        self.drive.stop()
        self.sensors = LineSensors()
        self.button = Button() if C.USE_BUTTON else NoButton()
        self.rangefinder = Rangefinder() if C.RACK_STOP_MODE == 'tof' else None
        self.amber = AmberLight()
        self.nav = Navigator(self.drive, self.sensors, self.button)

    # ---------------------------------------------------- run a route
    def execute(self, steps):
        nav = self.nav
        for step in steps:
            kind = step[0]
            if kind == 'follow':
                nav.follow(step[1], **step[2])
            elif kind == 'axle':
                nav.to_axle()
            elif kind == 'corner':
                nav.follow_to_corner()
            elif kind == 'turn':
                nav.turn(step[1], expect_line=step[2])
            elif kind == 'spin180':
                nav.spin180()
            elif kind == 'arrive_loading':
                nav.follow(1, speed=C.SLOW_SPEED)                 # stop on the white border
                if C.BAY_STOP_EXTRA_MS:
                    nav.run_for(C.BAY_STOP_EXTRA_MS, C.SLOW_SPEED, C.SLOW_SPEED)
            elif kind == 'arrive_rack':
                nav.follow_into_rack(self.rangefinder)
                if C.RACK_STOP_BACKOFF_MS:
                    nav.run_for(C.RACK_STOP_BACKOFF_MS, -C.SLOW_SPEED, -C.SLOW_SPEED)
            elif kind == 'park':
                # drive into the box until its far edge (white) is seen, or for PARK_MAX_MS
                try:
                    nav.follow(1, speed=C.SLOW_SPEED, lost_ok_ms=C.PARK_MAX_MS, timeout_ms=C.PARK_MAX_MS)
                except NavError:
                    pass                                          # no edge seen: time is up, stop here
                else:
                    nav.run_for(C.PARK_BACKOFF_MS, -C.SLOW_SPEED, -C.SLOW_SPEED)
            else:
                raise ValueError(step)
            nav.stop()

    # -------------------------------------- jobs at a bay (stubs for now)
    def pickup(self):
        """Grab test / competition: replace with gripper + magnet sensing."""
        print('pickup (simulated)')
        sleep_ms(C.PICKUP_PAUSE_MS)

    def unload(self):
        """Competition: replace with release mechanism."""
        print('unload (simulated)')
        sleep_ms(C.UNLOAD_PAUSE_MS)

    def wait_for_start(self):
        if not (C.USE_BUTTON and C.WAIT_FOR_BUTTON):
            print('starting in %d ms' % C.START_DELAY_MS)
            sleep_ms(C.START_DELAY_MS)
            return
        print('press the button to start')
        while not self.button.pressed():
            sleep_ms(10)
        while self.button.pressed():          # wait for release so it does not count as "stop"
            sleep_ms(10)
        sleep_ms(300)


def run_line_test(pickup=PICKUP, drop=DROP):
    robot = Robot()
    try:
        robot.wait_for_start()
        robot.button.armed = True
        robot.amber.flash()
        print('-> loading area', pickup)
        robot.execute(M.start_to(pickup))
        robot.pickup()
        print('-> rack', drop)
        robot.execute(M.bay_to_bay(pickup, drop))
        robot.unload()
        print('-> start box')
        robot.execute(M.bay_to_start(drop))
        print('line test done')
    except StopRequested:
        print('stopped by button')
    except NavError as e:
        print('navigation error:', e)
    finally:
        robot.drive.stop()                    # whatever happened, the motors stop
        robot.amber.off()                     # light must be off in the start area
