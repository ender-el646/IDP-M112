"""Desktop simulator for the agv package (run with normal Python 3 on a laptop,
NOT on the Pico).  It fakes machine/utime, drives a 2D robot over an
approximate copy of the table and checks that the line test route finishes
inside the start box.  Use it to check route/logic changes before going to the table.

    python3 tools/sim_line_test.py                       # default route LA3 -> B2L
    python3 tools/sim_line_test.py pickup=LA1 drop=A3L noise=0.01 plot=run.png

Options: seed, centre_in_box, mismatch (left/right motor), noise (sensor glitch
probability), head_err (deg), d (sensor-to-axle mm), track, vmax, axle_ms, plot.
The table geometry below is approximate - it tests logic, not the real numbers.
Needs Pillow only for plot=.
"""
import sys, math, random, types

ARGS = dict(seed=0, centre_in_box=False, mismatch=1.04, noise=0.003, head_err=3.0,
            d=90.0, track=110.0, vmax=150.0, pickup='LA3', drop='B2L', plot=None, axle_ms=0)
for a in sys.argv[1:]:
    k, v = a.split('=')
    ARGS[k] = type(ARGS[k])(v) if ARGS[k] is not None and not isinstance(ARGS[k], bool) else (v == 'True' if isinstance(ARGS[k], bool) else v)
random.seed(ARGS['seed'])

# ------------------------------------------------------------ map (mm)
W = 20.0
SEG = []
def seg(x1, y1, x2, y2): SEG.append((x1, y1, x2, y2))
def square(cx, cy, s):
    h = s / 2; seg(cx-h, cy-h, cx+h, cy-h); seg(cx+h, cy-h, cx+h, cy+h); seg(cx+h, cy+h, cx-h, cy+h); seg(cx-h, cy+h, cx-h, cy-h)
MAIN_Y = 300
seg(150, MAIN_Y, 2250, MAIN_Y)                 # bottom main line
seg(150, MAIN_Y, 150, 2300); seg(2250, MAIN_Y, 2250, 2300)   # side lines
seg(1200, MAIN_Y if not ARGS['centre_in_box'] else 100, 1200, 2000)   # centre line
seg(1050, 100, 1350, 100); seg(1350, 100, 1350, 400); seg(1350, 400, 1050, 400); seg(1050, 400, 1050, 100)  # start box
for y in (800, 1100):                          # loading areas, both halves
    seg(2250, y, 2000, y); square(1925, y, 150)
    seg(150, y, 400, y); square(475, y, 150)
for i in range(6):                             # lower rack bays
    y = 1700 + 100 * i
    seg(1800, y, 2250, y); seg(150, y, 600, y)
RACK_X = {'B': 1800, 'A': 600}

def dist_seg(px, py, s):
    x1, y1, x2, y2 = s
    dx, dy = x2 - x1, y2 - y1
    L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-x1)*dx + (py-y1)*dy) / L))
    return math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))

def white(px, py):
    return any(dist_seg(px, py, s) <= W/2 for s in SEG)

# ------------------------------------------------------------ robot
R = dict(x=1200.0, y=270.0 - ARGS['d'], th=math.radians(90 + ARGS['head_err']), t=0)
SENS_LAT = (-40, -10, 10, 40)    # left outer ... right outer (negative = left)
pins = {}
pwm = {}
trace = []

def sensor_values():
    out = []
    c, s = math.cos(R['th']), math.sin(R['th'])
    for lat in SENS_LAT:
        # left of heading = (-s, c)
        px = R['x'] + ARGS['d']*c - lat*(-s)
        py = R['y'] + ARGS['d']*s - lat*c
        v = 1 if white(px, py) else 0
        if random.random() < ARGS['noise']: v = 1 - v
        out.append(v)
    return out

def wheel(dirpin, pwmpin, gain):
    duty = pwm.get(pwmpin, 0) / 65535
    sgn = 1 if pins.get(dirpin, 0) == 1 else -1
    return sgn * duty * ARGS['vmax'] * gain

def step(ms):
    for _ in range(int(ms)):
        vl = wheel(4, 5, ARGS['mismatch'])
        vr = wheel(7, 6, 1.0)
        v = (vl + vr) / 2
        w = (vr - vl) / ARGS['track']
        R['th'] += w / 1000
        R['x'] += v * math.cos(R['th']) / 1000
        R['y'] += v * math.sin(R['th']) / 1000
        R['t'] += 1
        if R['t'] % 50 == 0: trace.append((R['x'], R['y']))

# ------------------------------------------------------------ fakes
machine = types.ModuleType('machine')
class Pin:
    IN, OUT, PULL_DOWN, IRQ_RISING, IRQ_FALLING = 0, 1, 2, 4, 8
    def __init__(self, n, mode=0, pull=None, value=None):
        self.n = n
        if value is not None: pins[n] = value
    def value(self, v=None):
        if v is None:
            if self.n in (18, 19, 20, 21):
                return sensor_values()[self.n - 18]
            return pins.get(self.n, 0)
        pins[self.n] = v
    def toggle(self): pins[self.n] = 1 - pins.get(self.n, 0)
    def irq(self, **kw): pass
class PWM:
    def __init__(self, pin): self.n = pin.n
    def freq(self, f): pass
    def duty_u16(self, d): pwm[self.n] = d
class Timer:
    PERIODIC = 1
    def __init__(self, *a, **k): pass
    def init(self, **k): pass
    def deinit(self): pass
machine.Pin, machine.PWM, machine.Timer = Pin, PWM, Timer
utime = types.ModuleType('utime')
utime.ticks_ms = lambda: R['t']
utime.ticks_diff = lambda a, b: a - b
utime.ticks_add = lambda a, b: a + b
utime.sleep_ms = step
utime.sleep = lambda s: step(s * 1000)
sys.modules['machine'] = machine
sys.modules['utime'] = utime

import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from agv import config as C
C.WAIT_FOR_BUTTON = False
C.CENTRE_LINE_IN_BOX = ARGS['centre_in_box']
if ARGS['axle_ms']: C.SENSOR_TO_AXLE_MS = ARGS['axle_ms']
from agv import mission
_orig_log = print
import agv.nav as N
_ol = N.Navigator.__init__
def _init(self, *a, **k):
    _ol(self, *a, **k)
    self.log = lambda m: print('%-28s pose (%.0f, %.0f) %.0f deg  t=%.1f' % (m, R['x'], R['y'], math.degrees(R['th']) % 360, R['t']/1000))
N.Navigator.__init__ = _init

marks = {}
orig_pickup = mission.Robot.pickup
def pk(self): marks['pickup'] = (R['x'], R['y']); print('   pickup at (%.0f, %.0f)' % (R['x'], R['y']))
def ul(self): marks['unload'] = (R['x'], R['y']); print('   unload at (%.0f, %.0f)' % (R['x'], R['y']))
mission.Robot.pickup = pk
mission.Robot.unload = ul
mission.run_line_test(ARGS['pickup'], ARGS['drop'])
c, s = math.cos(R['th']), math.sin(R['th'])
corners = [(R['x'] + a*c - b*(-s), R['y'] + a*s - b*c) for a in (-60, 110) for b in (-90, 90)]
in_box = all(1050 - 10 <= x <= 1350 + 10 and 100 - 10 <= y <= 400 + 10 for x, y in corners)
print('END pose (%.0f, %.0f) heading %.0f deg, t=%.1fs, robot fully in box: %s' % (R['x'], R['y'], math.degrees(R['th']) % 360, R['t']/1000, in_box))
print('RESULT', 'PASS' if in_box and 'unload' in marks else 'FAIL', marks)
if ARGS['plot']:
    from PIL import Image, ImageDraw
    sc = 0.3
    im = Image.new('RGB', (int(2400*sc), int(2400*sc)), 'black'); dr = ImageDraw.Draw(im)
    f = lambda x, y: (x*sc, (2400-y)*sc)
    for x1, y1, x2, y2 in SEG: dr.line([f(x1, y1), f(x2, y2)], fill='white', width=max(1, int(W*sc)))
    dr.line([f(*p) for p in trace], fill='orange', width=2)
    im.save(ARGS['plot'])
