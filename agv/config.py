# =====================================================================
# config.py - every pin number and every tunable number in one place.
#
# Anything marked  [TUNE]  has NOT been measured on the real robot.
# Measure it with agv/calibrate.py and change only this file.
# Anything marked  [CHECK] is an assumption about wiring / the table
# that must be confirmed once.
# =====================================================================

# ---------------------------------------------------------------- pins
# Physical jumper -> GPIO:  24->GP18, 25->GP19, 26->GP20, 27->GP21,
#                           29->GP22, 31->GP26, 34->GP28
LINE_SENSOR_PINS = (18, 19, 20, 21)   # left-outer, left-inner, right-inner, right-outer  [CHECK order]
LINE_WHITE = 1                         # sensor outputs HIGH on white (PicoBot guide p.14)

LEFT_MOTOR_DIR_PIN = 4                 # motor 3 (left)  on Motor Driver 2 #1
LEFT_MOTOR_PWM_PIN = 5
RIGHT_MOTOR_DIR_PIN = 7                # motor 4 (right) on Motor Driver 2 #2
RIGHT_MOTOR_PWM_PIN = 6
MOTOR_FORWARD = 1                      # value on the DIR pin that drives the wheel forward
LEFT_MOTOR_INVERT = False              # [CHECK] set True if this wheel spins backwards
RIGHT_MOTOR_INVERT = False

USE_BUTTON = False                     # no button fitted yet: the run starts START_DELAY_MS after power-up
BUTTON_PIN = 22                        # [CHECK] start/stop button when fitted (jumper 29 in board design.xlsx)
BUTTON_PRESSED = 1                     # value read when pressed (PULL_DOWN wiring)
AMBER_LED_PIN = 28                     # amber LED via transistor (jumper 34)

# ------------------------------------------------------- start / stop
WAIT_FOR_BUTTON = True                 # only used when USE_BUTTON = True
START_DELAY_MS = 3000                  # without a button: time to put the robot down in the box
BUTTON_STOPS_RUN = True                # pressing the button while running = emergency stop
AMBER_FLASH_HZ = 2                     # 1-4 Hz is clearly visible to the human eye

# ------------------------------------------------------------- motors
BASE_SPEED = 80                        # [TUNE] % duty when following a line
SLOW_SPEED = 50                        # [TUNE] % duty when creeping onto a junction / into a bay
TURN_SPEED = 60                        # [TUNE] % duty of each wheel while spinning on the spot
LEFT_TRIM = 0.95                       # [TUNE] commit "motor balance" used 95 / 100
RIGHT_TRIM = 1.00                      # [TUNE]
MIN_DUTY = 0                           # [TUNE] below this the gearbox stalls; raise if the robot hesitates

# --------------------------------------------------- line following
LOOP_MS = 10                           # control loop period
SENSOR_WEIGHTS = (-3, -1, 1, 3)        # line position estimate: negative = line is to the left
KP = 9                                 # [TUNE] % speed difference per unit of error
KD = 4                                 # [TUNE] damping; set 0 first, raise if it wobbles
LINE_LOST_MS = 1500                    # stop for safety if no sensor sees white for this long

# ---------------------------------------------------- junction logic
# A junction = an OUTER sensor sees white for JUNCTION_CONFIRM samples in a row.
# It is counted once, then ignored until both outer sensors read black for
# JUNCTION_CLEAR samples (so one wide crossing is never counted twice).
JUNCTION_CONFIRM = 3                   # [TUNE] raise if wobbling triggers false junctions
JUNCTION_CLEAR = 5                     # [TUNE]
JUNCTION_MIN_GAP_MS = 400              # [TUNE] ignore a new junction this soon after the last one
LINE_END_CONFIRM = 6                   # all-black samples in a row = end of a line

# ------------------------------------------------------------ turning
# Distance from the sensor row to the wheel axle, expressed as time at SLOW_SPEED.
# After a junction is seen, drive this long so the axle sits on the junction.
SENSOR_TO_AXLE_MS = 1200               # [TUNE] most important number for clean turns (kip: 0.6 s at 100 %)
TURN_90_MS = 950                       # [TUNE] 90 deg spin at TURN_SPEED (kip: 0.58 s at 100 %)
TURN_180_MS = 1900                     # [TUNE] 180 deg spin at TURN_SPEED
TURN_BLIND_FRACTION = 0.5              # ignore the sensors for this fraction of the nominal turn time
TURN_180_BLIND_FRACTION = 0.8          # [TUNE] larger for 180s: mid-turn the sensors sweep over the
                                       # neighbouring bay lines / the side line, which must be skipped
TURN_TIMEOUT_FACTOR = 1.8              # give up searching for the line after this x nominal time
TURN_SETTLE_MS = 100                   # pause after every spin
TURN_CONFIRM = 2                       # samples in a row that must see the new line to end a spin

# ----------------------------------------------------- bays and racks
BAY_STOP_EXTRA_MS = 0                  # [TUNE] creep further after the loading-area border is seen
# Rack bays: do NOT drive to the end of the line (the nose would hit the rack).
# 'time': after turning into the bay, follow the line for RACK_APPROACH_MS and stop.
# 'tof' : stop when the VL53L0X (I2C0, SDA GP8 / SCL GP9) reads <= RACK_STOP_DISTANCE_MM.
# In both modes the robot also stops at once if the line ends (safety backup).
RACK_STOP_MODE = 'time'
RACK_APPROACH_MS = 2500                # [TUNE] measure on the table: robot must stop short of the rack
RACK_STOP_DISTANCE_MM = 60             # [TUNE] only for 'tof'; VL53L0X readings need an offset check
RACK_STOP_BACKOFF_MS = 0               # [TUNE] optional reverse after stopping
PICKUP_PAUSE_MS = 2000                 # simulated pickup time
UNLOAD_PAUSE_MS = 2000                 # simulated unloading time
BACK_OFF_BEFORE_SPIN_MS = 0            # [TUNE] reverse a little before a 180 if the nose is too close

# ------------------------------------------------------- start box
# [CHECK] Robot starts in the start box BELOW the main (bottom) line, facing the racks.
# Coming back west along the main line from a corner, the robot crosses the
# right/left edge of the start box first, then reaches the centre junction.
JUNCTIONS_CORNER_TO_CENTRE = 2         # [CHECK] box edge + centre junction
CENTRE_LINE_IN_BOX = False             # [CHECK] True if the centre line continues down inside the start box
PARK_MAX_MS = 2500                     # [TUNE] drive into the box until its bottom edge is seen, or this long
PARK_BACKOFF_MS = 500                  # [TUNE] then reverse this long so the nose is inside the box, not on its edge
