# =====================================================================
# nav.py - driving behaviours built from the line sensors.
#
#   follow(n)        follow the line and stop at the n-th junction
#   follow_to_end()  follow the line until it ends (rack bays)
#   to_axle()        creep forward so the wheel axle sits on the junction
#   turn('L'/'R')    spin 90 deg, stopping when the sensors find the new line
#   spin180()        turn round on the spot, stopping on the line behind
#
# Every loop checks the stop button. Any problem raises an exception so
# the caller (mission.py) always stops the motors in its `finally`.
# =====================================================================
from utime import sleep_ms, ticks_ms, ticks_diff, ticks_add
from agv import config as C


class NavError(Exception):
    """Robot is lost (line gone for too long, turn never found the line...)."""


def other(side):
    return 'L' if side == 'R' else 'R'


class Navigator:
    def __init__(self, drive, sensors, button, log=print):
        self.drive = drive
        self.sensors = sensors
        self.button = button
        self.log = log
        self.last_err = 0

    # ------------------------------------------------------------ helpers
    def _tick(self):
        self.button.check()
        sleep_ms(C.LOOP_MS)

    def stop(self, settle_ms=0):
        self.drive.stop()
        if settle_ms:
            sleep_ms(settle_ms)

    def run_for(self, ms, left, right):
        """Open-loop drive for ms milliseconds (still checks the button)."""
        start = ticks_ms()
        self.drive.set(left, right)
        while ticks_diff(ticks_ms(), start) < ms:
            self._tick()
        self.drive.stop()

    def _error(self, s):
        """Line position: <0 line is left of centre, >0 right, None if no line.
        While crossing a junction the outer sensors are ignored."""
        w = C.SENSOR_WEIGHTS
        idx = (1, 2) if (s[1] or s[2]) else (0, 1, 2, 3)
        total = 0
        n = 0
        for i in idx:
            if s[i]:
                total += w[i]
                n += 1
        return total / n if n else None

    def _steer(self, s, speed, lost_straight=False):
        err = self._error(s)
        if err is None:
            # no line: keep turning the way we last saw it (or go straight)
            err = 0 if lost_straight else self.last_err
        d = err - self.last_err
        self.last_err = err
        corr = C.KP * err + C.KD * d
        self.drive.set(speed + corr, speed - corr)

    # ---------------------------------------------------- line following
    def follow(self, junctions=1, speed=None, lost_ok_ms=None, stop_at_end=False, timeout_ms=None):
        """Follow the line until the `junctions`-th junction (front sensors on it)
        and return the side(s) the last one had: 'L', 'R' or 'LR'.

        lost_ok_ms : allow driving straight with no line for this long
                     (leaving / entering the start box).
        stop_at_end: also return 'END' when the line simply ends.
        timeout_ms : raise NavError if nothing happened after this long.
        """
        speed = speed or C.BASE_SPEED
        lost_limit = lost_ok_ms if lost_ok_ms is not None else C.LINE_LOST_MS
        self.last_err = 0
        seen = 0
        confirm = 0
        clear = C.JUNCTION_CLEAR
        in_junction = False
        kl = kr = 0
        lost_since = None
        dark = 0
        t_start = ticks_ms()
        t_last = ticks_add(t_start, -C.JUNCTION_MIN_GAP_MS - 1)   # no gap needed at the very start
        while True:
            s = self.sensors.read()
            now = ticks_ms()
            if timeout_ms is not None and ticks_diff(now, t_start) > timeout_ms:
                self.drive.stop()
                raise NavError('follow timeout')
            outer = s[0] or s[3]
            inner = s[1] or s[2]

            # ---- junction detection (debounced, counted once)
            if in_junction:
                clear = clear + 1 if not outer else 0
                if clear >= C.JUNCTION_CLEAR:
                    in_junction = False
            elif outer and inner and ticks_diff(now, t_last) > C.JUNCTION_MIN_GAP_MS:
                confirm += 1
                kl = kl or s[0]          # which side(s) the junction line goes to
                kr = kr or s[3]
                if confirm >= C.JUNCTION_CONFIRM:
                    kind = ('L' if kl else '') + ('R' if kr else '')
                    seen += 1
                    in_junction = True
                    clear = 0
                    t_last = now
                    self.log('  junction %d/%d %s' % (seen, junctions, kind))
                    if seen >= junctions:
                        self.drive.stop()
                        return kind
                    kl = kr = 0
            else:
                confirm = 0
                kl = kr = 0

            # ---- line lost / line end
            if any(s):
                lost_since = None
                dark = 0
            else:
                dark += 1
                if lost_since is None:
                    lost_since = now
                if stop_at_end and dark >= C.LINE_END_CONFIRM:
                    self.drive.stop()
                    self.log('  line end')
                    return 'END'
                if ticks_diff(now, lost_since) > lost_limit:
                    self.drive.stop()
                    raise NavError('line lost')

            self._steer(s, speed, lost_straight=lost_ok_ms is not None)
            self._tick()

    def follow_into_rack(self, rangefinder=None):
        """Follow a rack bay line and stop BEFORE the rack: after RACK_APPROACH_MS
        ('time' mode) or when the rangefinder is close enough ('tof' mode).
        Stops at once if the line ends, whichever comes first."""
        self.last_err = 0
        dark = 0
        start = ticks_ms()
        while True:
            s = self.sensors.read()
            dark = 0 if any(s) else dark + 1
            if dark >= C.LINE_END_CONFIRM:
                self.log('  rack: line end')
                break
            if rangefinder is not None:
                if rangefinder.mm() <= C.RACK_STOP_DISTANCE_MM:
                    self.log('  rack: distance reached')
                    break
            elif ticks_diff(ticks_ms(), start) >= C.RACK_APPROACH_MS:
                self.log('  rack: approach time reached')
                break
            self._steer(s, C.SLOW_SPEED)
            self._tick()
        self.drive.stop()

    def follow_to_end(self, speed=None):
        """Follow a dead-end line (rack bay) until it ends or hits a stop bar."""
        return self.follow(junctions=1, speed=speed or C.SLOW_SPEED, stop_at_end=True)

    def to_axle(self, detect_end=False):
        """After stopping with the sensors on a junction, creep forward (still
        steering on the line if there is one) so the wheel axle - the spin
        centre - is on the junction.
        Returns True if the line straight ahead ended on the way (= a corner)."""
        self.last_err = 0
        dark = 0
        ended = False
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < C.SENSOR_TO_AXLE_MS:
            s = self.sensors.read()
            dark = 0 if any(s) else dark + 1
            if dark >= C.LINE_END_CONFIRM:
                ended = True
            self._steer(s, C.SLOW_SPEED, lost_straight=True)
            self._tick()
        self.stop(C.TURN_SETTLE_MS)
        return ended and detect_end

    def follow_to_corner(self):
        """Follow the line past any side branches and stop with the axle on the
        corner, i.e. the junction after which the line straight ahead ends.
        Needs no junction counting, so it does not depend on where exactly
        the start box edge or the neighbouring bays are."""
        while True:
            self.follow(1)
            if self.to_axle(detect_end=True):
                self.log('  corner')
                return

    # ------------------------------------------------------------ turning
    def _spin_until_line(self, side, nominal_ms, blind_fraction, expect_line=True):
        """Spin towards side. Ignore the sensors for the blind part of the turn,
        then stop as soon as the trailing inner sensor sees the new line.
        Without expect_line the spin is simply timed."""
        if not expect_line:
            self.run_for(nominal_ms, *self._spin_speeds(side))
            self.stop(C.TURN_SETTLE_MS)
            return
        trailing = 1 if side == 'R' else 2     # spinning right, the line arrives at RO, RI, then LI
        blind = int(nominal_ms * blind_fraction)
        limit = int(nominal_ms * C.TURN_TIMEOUT_FACTOR)
        start = ticks_ms()
        hits = 0
        self.drive.set(*self._spin_speeds(side))
        while True:
            t = ticks_diff(ticks_ms(), start)
            hits = hits + 1 if (t > blind and self.sensors.read()[trailing]) else 0
            if hits >= C.TURN_CONFIRM:      # 2 samples in a row: ignore single glitches
                break
            if t > limit:
                self.drive.stop()
                raise NavError('turn %s: line not found' % side)
            self._tick()
        self.stop(C.TURN_SETTLE_MS)

    def _spin_speeds(self, side):
        return (C.TURN_SPEED, -C.TURN_SPEED) if side == 'R' else (-C.TURN_SPEED, C.TURN_SPEED)

    def turn(self, side, expect_line=True):
        """90 deg turn at a junction. Call to_axle() first."""
        self.log('  turn %s' % side)
        self._spin_until_line(side, C.TURN_90_MS, C.TURN_BLIND_FRACTION, expect_line)

    def spin180(self, side='R'):
        """Turn round on the spot and stop on the line we came along."""
        self.log('  spin 180')
        if C.BACK_OFF_BEFORE_SPIN_MS:
            self.run_for(C.BACK_OFF_BEFORE_SPIN_MS, -C.SLOW_SPEED, -C.SLOW_SPEED)
        self._spin_until_line(side, C.TURN_180_MS, C.TURN_180_BLIND_FRACTION)
