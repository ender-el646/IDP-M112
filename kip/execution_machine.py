from robot_types import Section, Goal, State, Position, Side
import motor
import servo
import hall
from utime import sleep, ticks_ms, ticks_diff
import line_sensor
from machine import Pin
import distance_sensor
import ir_sensor

def elapsed(start):
    # seconds since program start
    return ticks_diff(ticks_ms(), start) / 1000

FORWARD = 1
REVERSE = 0

REACH_LINE_MID = 0.15
REVERSE_CUT_FACTOR = 0.75
PICK_UP_CUT_FACTOR = 1.1

RAMP_FACTOR = 0.7
RAMP_FACTOR_UP = 0.7
UP_SPEED_FACTOR = 0.9
UP_MOVEMENT_FACTOR = 0.9
PICK_UP_SPEED = 0.5

# debug constants
DROP_WAIT_TIME = 0.5
WAIT_TIME = 0.03

# line follow constants
LINE_FOLLOW_INTERVAL = 0.005
WAIT_INTERVAL = 0.005
SMALL_CORRECTION = 30
LARGE_CORRECTION = 40
LINE_FOLLOW_SPEED = 100

TURNING_SPEED = 70
ROTATE_SLEEP = 0.001

REVERSE_FACTOR = 0.5
LINE_FOLLOW_REVERSE_SPEED = 100

LINE_LOST_SAMPLES = 1

# need to calibrate

# maneuvers
SENSORS_TO_AXIS_DURATION = 0.59
ROTATION_90_DURATION = 1.0

ROTATION_90_DURATION_MIN = 0.75
ROTATION_90_DURATION_MAX = 1.2

ROTATION_180_DURATION_MIN = 1.5
ROTATION_180_DURATION_MAX = 2.2

ROTATION_270_DURATION = 2.6
ROTATION_270_DURATION_MIN = 2.2
ROTATION_270_DURATION_MAX = 2.9

ROTATION_CORRECTION_TIME = 0.15

GO_UP_DURATION = 6.0

INTIAL_HEIGHT = 270
PICK_UP_HEIGHT = 0
HOLD_HEIGHT = 110
RAISE_UP_HEIGHT = 210
INITIAL_WIDTH = 270
PICK_UP_WIDTH = 130
DROP_WIDTH = 170

CHECK_LINE_FOLLOW_DURATION = 1.0
DISTANCE_WITH_BOX_LOWER = 340
DISTANCE_WITH_BOX_UPPER = 270

RACK_BACK_UP = 0.4

orange_led_value = 0

yellow_led_pin = 2
green_led_pin = 27
red_led_pin = 28

yellow_led = Pin(yellow_led_pin, Pin.OUT)
green_led = Pin(green_led_pin, Pin.OUT)
red_led = Pin(red_led_pin, Pin.OUT)

counter = 0

def init():
    servo.servo_height.set_angle(INTIAL_HEIGHT)
    sleep(1)
    servo.servo_clamp.set_angle(INITIAL_WIDTH)
    sleep(1)

def wait(wait_duration=WAIT_TIME):
    global counter
    global orange_led_value

    if wait_duration == ROTATE_SLEEP:
        sleep(ROTATE_SLEEP)
        counter = counter + 1
        if counter > 500:
            if orange_led_value == 1:
                orange_led_value = 0
            else: 
                orange_led_value = 1
            counter = 0
            yellow_led.value(orange_led_value)
        return
    
    for i in range(int(wait_duration/WAIT_INTERVAL)):
        sleep(WAIT_INTERVAL)
        counter = counter + 5
        if counter > 500:
            if orange_led_value == 1:
                orange_led_value = 0
            else: 
                orange_led_value = 1
            counter = 0

            yellow_led.value(orange_led_value)


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

def follow_straight_line_sensors_to_axis_duration(direction=1):
    motor.motors_off()

    start = ticks_ms()
    duration_ms = int(SENSORS_TO_AXIS_DURATION * 1000)
    while ticks_diff(ticks_ms(), start) < duration_ms:
        drive_on_line(direction, line_sensor.read_sensors(), UP_SPEED_FACTOR)
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()

def u_turn():
    wait()
    follow_straight_line_sensors_to_axis_duration()  # put axle on the junction
    wait()
    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(Side.RIGHT, REVERSE, TURNING_SPEED)
    motor.set_motor(Side.LEFT, FORWARD, TURNING_SPEED)

    wait(ROTATION_180_DURATION_MIN)

    while elapsed(start) <= ROTATION_180_DURATION_MAX:
            sensors = line_sensor.read_sensors()
    
            if sensors[1] == 1 and sensors[2] == 1:
                motor.motors_off()
                follow_straight_line_sensors_to_axis_duration(REVERSE)
                wait()
                motor.motors_off()
                return
    
            wait(ROTATE_SLEEP)

    motor.motors_off()
    wait()
    follow_straight_line_sensors_to_axis_duration(REVERSE)
    wait()

def stationary_u_turn():
    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(Side.RIGHT, REVERSE, TURNING_SPEED)
    motor.set_motor(Side.LEFT, FORWARD, TURNING_SPEED)

    wait(ROTATION_180_DURATION_MIN)


    cur_time = ROTATION_180_DURATION_MIN

    while elapsed(start) <= ROTATION_180_DURATION_MAX:
            sensors = line_sensor.read_sensors()
    
            if sensors[1] == 1 and sensors[2] == 1:
                motor.motors_off()
                return
    
            wait(ROTATE_SLEEP)

    motor.motors_off()
    wait()

def drive_on_line(direction, sensors, factor=1.0, cut_factor=1.0):
    cut_left, cut_right = correction(sensors)

    cut_left = cut_left*cut_factor
    cut_right = cut_right*cut_factor

    if direction == REVERSE:
        cut_right = cut_right*REVERSE_CUT_FACTOR
        cut_left = cut_left*REVERSE_CUT_FACTOR

    speed = LINE_FOLLOW_SPEED

    if direction == REVERSE:
        cut_left, cut_right = cut_right, cut_left

        cut_left *= REVERSE_FACTOR
        cut_right *= REVERSE_FACTOR

        speed = LINE_FOLLOW_REVERSE_SPEED*factor

    motor.set_motor(Side.RIGHT, direction, speed - cut_right)
    motor.set_motor(Side.LEFT, direction, speed - cut_left)


def follow_straight_line(duration, direction=FORWARD, speed_factor=1.0):
    motor.motors_off()

    start = ticks_ms()
    duration_ms = int(duration * 1000)

    counter = 1

    while ticks_diff(ticks_ms(), start) < duration_ms:
        drive_on_line(direction, line_sensor.read_sensors(), speed_factor)
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()


def at_junction(sensors):
    return bool((sensors[1] or sensors[2]) and (sensors[0] or sensors[3]))

def back_up(count):
    u_turn()
    for _ in range(count):
        reach_line(FORWARD, speed_factor=UP_MOVEMENT_FACTOR)
    wait()
    follow_straight_line_sensors_to_axis_duration(FORWARD)
    wait()
    stationary_u_turn()
    wait()
    reach_line(REVERSE, SENSORS_TO_AXIS_DURATION/2, speed_factor=UP_MOVEMENT_FACTOR)
    follow_straight_line(REACH_LINE_MID, REVERSE)

def reach_line(direction=FORWARD, cooldown=0.35, speed_factor=1.0, gaps=999.0, cut_factor=1.0):
    wait()
    motor.motors_off()

    left_junction = False

    start = ticks_ms()

    counter = 1

    while True:
        sensors = line_sensor.read_sensors()

        if at_junction(sensors) and elapsed(start) >= cooldown:
            if left_junction:
                break
        else:
            left_junction = True

        if counter*gaps < elapsed(start):
            counter += 1
            motor.motors_off()
            wait()

        drive_on_line(direction, sensors, speed_factor, cut_factor=cut_factor)
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()
    wait()
    return True


def reach_line_end(cooldown=1.0, speed_factor=1.0):
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

        drive_on_line(FORWARD, sensors, speed_factor)
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()
    wait()

def rotate_bot_by_set_amount(duration):
    
    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(Side.RIGHT, FORWARD, TURNING_SPEED)
    motor.set_motor(Side.LEFT, REVERSE, TURNING_SPEED)

    wait(duration)

    motor.motors_off()

def rotate_bot(side, three_sensors=0):

    motor.motors_off()

    start = ticks_ms()

    motor.set_motor(side, REVERSE, TURNING_SPEED)
    motor.set_motor(opposite(side), FORWARD, TURNING_SPEED)

    wait(ROTATION_90_DURATION_MIN)

    cur_time = ROTATION_90_DURATION_MIN

    while elapsed(start) <= ROTATION_90_DURATION_MAX:
            sensors = line_sensor.read_sensors()

            if sensors[1] == 1 and sensors[2] == 1 and three_sensors == 0:
                motor.motors_off()
                return
            if sensors[1] == 1 and sensors[2] == 1 and three_sensors == 1:
                wait(ROTATION_CORRECTION_TIME)
                motor.motors_off()
                return
        
            wait(ROTATE_SLEEP)

    motor.motors_off()

def rotate_bot_270(side, three_sensors=0):

    if three_sensors == 1:
        motor.motors_off()

        start = ticks_ms()

        motor.set_motor(side, REVERSE, TURNING_SPEED)
        motor.set_motor(opposite(side), FORWARD, TURNING_SPEED)

        wait(ROTATION_270_DURATION)

        motor.motors_off()
    else:
        motor.motors_off()

        start = ticks_ms()

        motor.set_motor(side, REVERSE, TURNING_SPEED)
        motor.set_motor(opposite(side), FORWARD, TURNING_SPEED)

        wait(ROTATION_270_DURATION_MIN)

        cur_time = ROTATION_270_DURATION_MIN

        while elapsed(start) <= ROTATION_270_DURATION_MAX:
                sensors = line_sensor.read_sensors()

                if sensors[1] == 1 and sensors[2] == 1 and three_sensors == 0:
                    motor.motors_off()
                    return
                if sensors[1] == 1 and sensors[2] == 1 and three_sensors == 1 and (sensors[0] == 1 or sensors[3] == 1):
                    motor.motors_off()
                    return
        
                wait(ROTATE_SLEEP)

        motor.motors_off()


def rotation_from_front(side, three_sensors=0):
    wait()
    follow_straight_line_sensors_to_axis_duration(FORWARD)
    wait()
    rotate_bot(side, three_sensors)
    wait()

def rotation_from_front_270(side, three_sensors=0):
    wait()
    follow_straight_line_sensors_to_axis_duration(FORWARD)
    wait()
    rotate_bot_270(side, three_sensors)
    wait()


def check_for_box():
    return True


def pick_up_box():

    servo.servo_clamp.set_angle(INITIAL_WIDTH)
    wait(1)
    raise_slowly(servo.servo_height, INTIAL_HEIGHT, PICK_UP_HEIGHT)
    wait(1)
    servo.servo_clamp.set_angle(PICK_UP_WIDTH)
    wait(1)
    raise_slowly(servo.servo_height, PICK_UP_HEIGHT, HOLD_HEIGHT)
    wait(1)



def spot_not_taken():
    return True

def reset_servo():
    raise_slowly(servo.servo_height, 0, INTIAL_HEIGHT)
    servo.servo_clamp.set_angle(INITIAL_WIDTH)
    wait()


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
            reach_line(FORWARD, speed_factor=UP_MOVEMENT_FACTOR)
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
    reach_line(REVERSE, cooldown=0.0)

    rotation_from_front(to_side)

    reach_line(FORWARD)
    reach_line(FORWARD)

    rotation_from_front(opposite(to_side))
    for _ in range(end.position):
        reach_line(FORWARD)


def move_to_initial(start):

    if start.section == Section.UP:
        u_turn()
        for _ in range(start.position-1):
            reach_line(FORWARD, speed_factor=RAMP_FACTOR)
        wait()
        reach_line_end(5.0, RAMP_FACTOR)
        wait()
        follow_straight_line(0.15, REVERSE)
        wait()
        u_turn()
        wait()
        follow_straight_line(0.4, FORWARD)
        wait()

    else:

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
        follow_straight_line_sensors_to_axis_duration()
        wait()
        rotate_bot(side)
        wait()
        # along the bottom line to the centre, then face up the centre line
        reach_line(FORWARD)
        reach_line(FORWARD)
        rotation_from_front(side)


def move_from_initial_up(end):

    ir_sensor.wait_until_green_light()

    follow_straight_line(GO_UP_DURATION, FORWARD, speed_factor=RAMP_FACTOR_UP)
    reach_line(FORWARD, speed_factor=RAMP_FACTOR_UP, gaps=0.7)
    wait()
    for _ in range(end.position-1):
        reach_line(FORWARD)
    wait()


def leave_branch(return_side, entered):
    if entered:
        reach_line(REVERSE)                  # back out until the main line
        rotation_from_front(return_side, 0)     # face up again (A-state)
    else:
        rotate_bot(return_side, 0)              # axis is still on the junction
        wait()

    wait()
    follow_straight_line_sensors_to_axis_duration(REVERSE)
    wait()

def leave_branch_rack_u_turn(return_side, entered):
    if entered:
        '''
        follow_straight_line(RACK_BACK_UP, REVERSE)
        wait()
        stationary_u_turn()
        wait()
        reach_line(FORWARD)  # back out until the main line
        wait()
        rotation_from_front(opposite(return_side), 1)
        '''

        reach_line(REVERSE)
        wait()                 
        rotation_from_front(return_side, 1)     # face up again (A-state)
    else:
        rotate_bot(return_side, 1)              # axis is still on the junction
        wait()

    wait()
    reach_line(REVERSE)
    wait()

def leave_branch_rack(return_side, entered):
    if entered:
        reach_line(REVERSE)
        wait()                 
        rotation_from_front(return_side, 1)     # face up again (A-state)
    else:
        rotate_bot(return_side, 1)              # axis is still on the junction
        wait()

    wait()
    follow_straight_line_sensors_to_axis_duration(REVERSE)
    wait()


def pick_up(state):
    current_side = section_side(state.section)

    # go up to the box
    rotation_from_front(opposite(current_side))

    reach_line(FORWARD, speed_factor=PICK_UP_SPEED, cut_factor=PICK_UP_CUT_FACTOR)

    wait()

    motor.motors_off()

    start = ticks_ms()
    duration_ms = int(0.35 * 1000)
    while ticks_diff(ticks_ms(), start) < duration_ms:
        drive_on_line(FORWARD, line_sensor.read_sensors())
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()

    wait()

    start = ticks_ms()
    duration_ms = int(0.15 * 1000)
    while ticks_diff(ticks_ms(), start) < duration_ms:
        drive_on_line(REVERSE, line_sensor.read_sensors())
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()

    pick_up_box()

    field = hall.get_magnetic_field()

    if field == 1:
        red_led.value(1)
        green_led.value(0)
    elif field == -1:
        red_led.value(0)
        green_led.value(1)

    motor.motors_off()

    start = ticks_ms()
    duration_ms = int(0.5 * 1000)
    while ticks_diff(ticks_ms(), start) < duration_ms:
        drive_on_line(REVERSE, line_sensor.read_sensors())
        wait(LINE_FOLLOW_INTERVAL)

    motor.motors_off()

    # go back
    leave_branch(current_side, True)

    return field


def place_lower(state):

    current_side = section_side(state.section)

    rotation_from_front(opposite(current_side))

    wait()

    follow_straight_line(1.0, FORWARD)

    wait()

    raise_slowly(servo.servo_height, HOLD_HEIGHT, RAISE_UP_HEIGHT)

    wait()
    
    reach_line_end()

    wait()

    servo.servo_clamp.set_angle(DROP_WIDTH)

    red_led.value(0)
    green_led.value(0)

    wait(DROP_WAIT_TIME)

    leave_branch_rack_u_turn(current_side, True)

    raise_slowly(servo.servo_height, RAISE_UP_HEIGHT, INTIAL_HEIGHT)
    wait(1)
    servo.servo_clamp.set_angle(INITIAL_WIDTH)

    wait()

    #raise_slowly(servo.servo_height, RAISE_UP_HEIGHT, INTIAL_HEIGHT)
    #servo.servo_clamp.set_angle(INITIAL_WIDTH)
    #wait()
    



def place_upper(state, side):

    current_side = side

    if current_side == Side.RIGHT:
        opposite_side = Side.LEFT
    elif current_side == Side.LEFT:
        opposite_side = Side.RIGHT
    else:
        return

    rotation_from_front(current_side)

    wait()

    # check if the spot is not taken and if it's not taken place it down
    #if spot_not_taken():
    reach_line_end()

    wait()

    servo.servo_clamp.set_angle(DROP_WIDTH)

    red_led.value(0)
    green_led.value(0)

    wait(DROP_WAIT_TIME)

    leave_branch_rack_u_turn(opposite_side, True)

    raise_slowly(servo.servo_height, HOLD_HEIGHT, INTIAL_HEIGHT)

    wait(1)

    servo.servo_clamp.set_angle(INITIAL_WIDTH)

    wait(1)



def raise_slowly(cur_servo, cur_angle, final_angle):

    cur_servo.set_angle(final_angle)

    return

def check_spot(side, is_up):

    current_side = side

    if current_side == Side.RIGHT:
        opposite_side = Side.LEFT
    elif current_side == Side.LEFT:
        opposite_side = Side.RIGHT
    else:
        return

    rotation_from_front(current_side)
    
    wait()

    # check if the spot is not taken and if it's not taken place it down
    #if spot_not_taken():
    follow_straight_line(CHECK_LINE_FOLLOW_DURATION, FORWARD)

    wait()

    distance = distance_sensor.get_average_dist()

    print(distance)

    #distance_diff_box = abs(distance - DISTANCE_WITH_BOX)
    #distance_diff_no_box = abs(distance - DISTANCE_WITHOUT_BOX)

    empty = False

    if distance > DISTANCE_WITH_BOX_UPPER and is_up == True:
        empty = True
    if distance > DISTANCE_WITH_BOX_LOWER and is_up == False:
        empty = True

    leave_branch_rack(opposite_side, True)

    return empty