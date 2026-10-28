from robot_types import Section, Goal, State, Position, Side
import motor
import servo
from utime import sleep, ticks_ms, ticks_diff
import line_sensor

def elapsed(start):
    # seconds since program start
    return ticks_diff(ticks_ms(), start) / 1000

FORWARD = 1
REVERSE = 0

# debug constants
WAIT_TIME = 0.2

# line follow constants
LINE_FOLLOW_INTERVAL = 0.005
SMALL_CORRECTION = 20
LARGE_CORRECTION = 40
LINE_FOLLOW_SPEED = 100

TURNING_SPEED = 70
ROTATE_SLEEP = 0.001

REVERSE_FACTOR = 0.5
LINE_FOLLOW_REVERSE_SPEED = 100

LINE_LOST_SAMPLES = 2

# need to calibrate

# maneuvers
SENSORS_TO_AXIS_DURATION = 0.47
ROTATION_90_DURATION = 0.57

ROTATION_90_DURATION_MIN = 0.6
ROTATION_90_DURATION_MAX = 1.1

ROTATION_180_DURATION_MIN = 1.4
ROTATION_180_DURATION_MAX = 1.9

INTIAL_HEIGHT = 270
PICK_UP_HEIGHT = 0
RAISE_UP_HEIGHT = 210
INITIAL_WIDTH = 270
PICK_UP_WIDTH = 185
DROP_WIDTH = 230


def wait():
    sleep(WAIT_TIME)


def opposite(side):
    return Side.LEFT if side == Side.RIGHT else Side.RIGHT


def section_side(section):
    return Side.RIGHT if section == Section.RIGHT else Side.LEFT


def correction(sensors):
    cut_left = 0
    cut_right = 0

    if sensors == [1, 0, 0, 0]:
        cut_left = LARGE_CORRECTION
    elif sensors == [0, 0, 0, 1]:
        cut_right = LARGE_CORRECTION
    elif sensors[1] == 0 and sensors[2] == 1:
        cut_right = SMALL_CORRECTION
    elif sensors[2] == 0 and sensors[1] == 1:
        cut_left = SMALL_CORRECTION

    return cut_left, cut_right


def u_turn():
    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION)  # put axle on the junction
    wait()
    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(Side.RIGHT, REVERSE, TURNING_SPEED)
    motor.set_motor(Side.LEFT, FORWARD, TURNING_SPEED)

    sleep(ROTATION_180_DURATION_MIN)

    cur_time = ROTATION_180_DURATION_MIN

    while elapsed(start) <= ROTATION_180_DURATION_MAX:
            sensors = line_sensor.read_sensors()
    
            if sensors[1] == 1 and sensors[2] == 1:
                motor.motors_off()
                return
    
            sleep(ROTATE_SLEEP)

    motor.motors_off()
    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION, REVERSE)
    wait()

def drive_on_line(direction, sensors):
    cut_left, cut_right = correction(sensors)

    speed = LINE_FOLLOW_SPEED

    if direction == REVERSE:
        cut_left, cut_right = cut_right, cut_left

        cut_left *= REVERSE_FACTOR
        cut_right *= REVERSE_FACTOR

        speed = LINE_FOLLOW_REVERSE_SPEED

    motor.set_motor(Side.RIGHT, direction, speed - cut_right)
    motor.set_motor(Side.LEFT, direction, speed - cut_left)


def follow_straight_line(duration, direction=FORWARD):
    motor.motors_off()

    start = ticks_ms()
    duration_ms = int(duration * 1000)
    while ticks_diff(ticks_ms(), start) < duration_ms:
        drive_on_line(direction, line_sensor.read_sensors())
        sleep(LINE_FOLLOW_INTERVAL)

    motor.motors_off()


def at_junction(sensors):
    return bool((sensors[1] or sensors[2]) and (sensors[0] or sensors[3]))

def back_up(count):
    u_turn()
    for _ in range(count):
        reach_line(FORWARD)
    u_turn()

def reach_line(direction=FORWARD, cooldown=0.25):
    wait()
    motor.motors_off()

    left_junction = False

    start = ticks_ms()

    while True:
        sensors = line_sensor.read_sensors()

        if at_junction(sensors) and elapsed(start) >= cooldown:
            if left_junction:
                break
        else:
            left_junction = True

        drive_on_line(direction, sensors)
        sleep(LINE_FOLLOW_INTERVAL)

    motor.motors_off()
    wait()
    return True


def reach_line_end(cooldown=1):
    wait()
    motor.motors_off()

    lost = 0

    start = ticks_ms()

    while lost < LINE_LOST_SAMPLES:
        sensors = line_sensor.read_sensors()

        if sum(sensors) == 0 and elapsed(start) >= cooldown:
            lost += 1
        else:
            lost = 0

        drive_on_line(FORWARD, sensors)
        sleep(LINE_FOLLOW_INTERVAL)

    motor.motors_off()
    wait()


def rotate_bot_by_set_amount(duration):
    
    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(Side.RIGHT, FORWARD, TURNING_SPEED)
    motor.set_motor(Side.LEFT, REVERSE, TURNING_SPEED)

    sleep(duration)

    motor.motors_off()

def rotate_bot(side):
    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(side, REVERSE, TURNING_SPEED)
    motor.set_motor(opposite(side), FORWARD, TURNING_SPEED)

    sleep(ROTATION_90_DURATION_MIN)

    cur_time = ROTATION_90_DURATION_MIN

    while elapsed(start) <= ROTATION_90_DURATION_MAX:
            sensors = line_sensor.read_sensors()
    
            if sensors[1] == 1 and sensors[2] == 1:
                motor.motors_off()
                return
    
            sleep(ROTATE_SLEEP)

    motor.motors_off()


def rotation_from_front(side):
    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION)
    wait()
    rotate_bot(side)
    wait()


def check_for_box():
    return True


def pick_up_box():

    servo.servo_clamp.set_angle(INITIAL_WIDTH)
    sleep(1)
    raise_slowly(servo.servo_height, INTIAL_HEIGHT, PICK_UP_HEIGHT)
    sleep(3)
    servo.servo_clamp.set_angle(PICK_UP_WIDTH)
    sleep(1.5)
    raise_slowly(servo.servo_height, PICK_UP_HEIGHT, RAISE_UP_HEIGHT)
    sleep(1)
    servo.servo_clamp.off()
    servo.servo_height.off()


def spot_not_taken():
    return True

def reset_servo():
    raise_slowly(servo.servo_height, 0, INTIAL_HEIGHT)
    servo.servo_clamp.set_angle(INITIAL_WIDTH)
    sleep(3)


def move(start, end):
    if start.section == end.section and start.position == end.position:
        return

    if end.section == Section.INITIAL:
        if start.section != Section.INITIAL:
            move_to_initial(start)
    elif start.section == Section.INITIAL:
        move_from_initial(end)
    elif start.section == end.section:
        move_in_section(start, end)
    else:
        move_to_initial(start)
        move_from_initial(end)


def move_from_initial(end):
    if end.section == Section.UP:
        move_from_initial_up(end)
    else:
        move_from_initial_side(end)


def move_in_section(start, end):
    if end.position > start.position:
        for _ in range(end.position - start.position):
            reach_line(FORWARD)
    else:
        #u_turn()
        #for _ in range(start.position - end.position):
            #it was reach_line(REVERSE) before
        #    reach_line(FORWARD)
        #u_turn()

        back_up(start.position - end.position)


def move_from_initial_side(end):
    to_side = section_side(end.section)  # side of the robot the section is on

    # back up until the bottom line, turn towards the section, drive to the corner
    reach_line(REVERSE)

    rotation_from_front(to_side)

    reach_line(FORWARD)
    reach_line(FORWARD)

    rotation_from_front(opposite(to_side))
    for _ in range(end.position):
        reach_line(FORWARD)


def move_to_initial(start):
    side = section_side(start.section)

    # back down the vertical line to the corner
    #u_turn()
    #for _ in range(start.position):
        #it was reach_line(REVERSE) before
    #    reach_line(FORWARD)
    #u_turn()

    u_turn()
    for _ in range(start.position):
        reach_line(FORWARD)
    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION)  # put axle on the junction
    wait()
    rotate_bot(side)
    wait()
    # along the bottom line to the centre, then face up the centre line
    reach_line(FORWARD)
    reach_line(FORWARD)
    rotation_from_front(side)


def move_from_initial_up(end):
    return


def leave_branch(return_side, entered):
    if entered:
        reach_line(REVERSE)                  # back out until the main line
        rotation_from_front(return_side)     # face up again (A-state)
    else:
        rotate_bot(return_side)              # axis is still on the junction
        wait()

    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION, REVERSE)
    wait()


def pick_up(state):
    current_side = section_side(state.section)

    # go up to the box
    rotation_from_front(opposite(current_side))
    reach_line(FORWARD)

    sleep(2)

    follow_straight_line(0.05, FORWARD)

    sleep(2)

    pick_up_box()

    follow_straight_line(0.1, REVERSE)

    # go back
    leave_branch(current_side, True)


def place_lower(state):
    current_side = section_side(state.section)

    rotation_from_front(opposite(current_side))

    reach_line_end()

    sleep(2)

    servo.servo_clamp.set_angle(DROP_WIDTH)
    sleep(1)

    leave_branch(current_side, True)

    raise_slowly(servo.servo_height, RAISE_UP_HEIGHT, INTIAL_HEIGHT)
    servo.servo_clamp.set_angle(INITIAL_WIDTH)
    sleep(2)
    


'''
def place_upper(state):
    place_upper_side(state, Side.RIGHT)
    place_upper_side(state, Side.LEFT)


def place_upper_side(state, side):

    current_side = side

    if current_side == Side.RIGHT:
        opposite_side = Side.LEFT
    elif current_side == Side.LEFT:
        opposite_side = Side.RIGHT
    else:
        return

    rotation_from_front(opposite_side)

    # check if the spot is not taken and if it's not taken place it down
    if spot_not_taken():
        # go up to the box
        reach_no_line()

        # place the box
        place_box_upper()

        back_up_until_line()

    # go back
    rotation_from_front(current_side)
    back_up_until_line()
'''





def raise_slowly(cur_servo, cur_angle, final_angle):
    #for i in range(cur_angle, final_angle, 5):
    #    cur_servo.set_angle(i)
    #    sleep(0.05)

    if cur_angle > final_angle:
        for i in reversed(range(final_angle, cur_angle, 5)):
            cur_servo.set_angle(i)
            sleep(0.05)
    else:
        for i in (range(cur_angle, final_angle, 5)):
            cur_servo.set_angle(i)
            sleep(0.05)