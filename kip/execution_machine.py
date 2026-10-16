from robot_types import Section, Goal, State, Position, Side
from dataclasses import replace
import motor
from utime import sleep, ticks_ms, ticks_diff
import line_sensor


FORWARD = 1
REVERSE = 0

#debug constants
WAIT_TIME = 0.2

#line follow constants
LINE_FOLLOW_INTERVAL = 0.05
SMALL_CORRECTION = 20
LARGE_CORRECTION = 40
LINE_FOLLOW_SPEED = 100

LINE_LOST_SAMPLES = 2

#need to calibrate

#maneuvers 
SENSORS_TO_AXIS_DURATION = 0.6
ROTATION_90_DURATION = 0.81

def wait():
    sleep(WAIT_TIME)

def opposite(side: Side):
    return Side.LEFT if side == Side.RIGHT else Side.RIGHT

def section_side(section: Section):
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

def drive_on_line(direction, sensors):
    cut_left, cut_right = correction(sensors)
 
    if direction == REVERSE:
        cut_left, cut_right = cut_right, cut_left
 
    motor.set_motor(Side.RIGHT, direction, LINE_FOLLOW_SPEED - cut_right)
    motor.set_motor(Side.LEFT, direction, LINE_FOLLOW_SPEED - cut_left)
 

def follow_straight_line(duration, direction=FORWARD):
    motor.motors_off()
 
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < duration * 1000:
        drive_on_line(direction, line_sensor.read_sensors())
        sleep(LINE_FOLLOW_INTERVAL)
 
    motor.motors_off()

def at_junction(sensors):
    return bool((sensors[1] or sensors[2]) and (sensors[0] or sensors[3]))

def reach_line(direction=FORWARD):

    wait()

    motor.motors_off()
 
    left_junction = False
 
    while True:
        sensors = line_sensor.read_sensors()
 
        if at_junction(sensors):
            if left_junction:
                break
        else:
            left_junction = True
 
        drive_on_line(direction, sensors)

        sleep(LINE_FOLLOW_INTERVAL)
 
    motor.motors_off()
    wait()
    return True

def reach_line_end():

    wait()

    motor.motors_off()
 
    lost = 0
    start = ticks_ms()
 
    while lost < LINE_LOST_SAMPLES:
        sensors = line_sensor.read_sensors()
 
        if sum(sensors) == 0:
            lost += 1
        else:
            lost = 0
 
        drive_on_line(FORWARD, sensors)
        sleep(LINE_FOLLOW_INTERVAL)
 
    motor.motors_off()
    wait()

def rotate_bot(side: Side):
    motor.motors_off()
 
    motor.set_motor(side, REVERSE)
    motor.set_motor(opposite(side), FORWARD)
 
    sleep(ROTATION_90_DURATION)
 
    motor.motors_off()

def rotation_from_front(side: Side):
    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION)
    wait()
    rotate_bot(side)
    wait()

def check_for_box():
    return True

def pick_up_box():
    return 

def spot_not_taken():
    return True

def move(start: Position, end: Position):
 
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


def move_from_initial(end: Position):
    if end.section == Section.UP:
        move_from_initial_up(end)
    else:
        move_from_initial_side(end)

def move_in_section(start: Position, end: Position):
    if end.position > start.position:
        for _ in range(end.position - start.position):
            reach_line(FORWARD)
    else:
        for _ in range(start.position - end.position):
            reach_line(REVERSE)


    return

def move_from_initial_side(end: Position):
    to_side = section_side(end.section)      # side of the robot the section is on
 
    # back up until the bottom line, turn towards the section, drive to the corner
    reach_line(REVERSE)
    rotation_from_front(to_side)
    reach_line(FORWARD)
 
    rotation_from_front(opposite(to_side))
    for _ in range(end.position):
        reach_line(FORWARD)

def move_to_initial(start: Position):
 
    side = section_side(start.section)
 
    # back down the vertical line to the corner
    for _ in range(start.position):
        reach_line(REVERSE)
 
    # along the bottom line to the centre, then face up the centre line
    rotation_from_front(opposite(side))
    reach_line(FORWARD)
    rotation_from_front(side)


def move_from_initial_up(end: Position):

    return


def leave_branch(return_side: Side, entered: bool): 
    if entered:
        reach_line(REVERSE)                  # back out until the main line
        rotation_from_front(return_side)     # face up again (A-state)
    else:
        rotate_bot(return_side)              # axis is still on the junction
        wait()
 
    wait()
    follow_straight_line(SENSORS_TO_AXIS_DURATION, REVERSE)
    wait()

def pick_up(state: State):

    current_side = section_side(state.section)
 
    # go up to the box
    rotation_from_front(opposite(current_side))
    reach_line(FORWARD)
 
    sleep(2)

    # go back
    leave_branch(current_side, True)


def place_lower(state: State):
 
    current_side = section_side(state.section)
 
    rotation_from_front(opposite(current_side))
 
    reach_line_end()

    sleep(2)
 
    leave_branch(current_side, True)

'''
def place_upper(state: State):
    place_upper_side(state, Side.RIGHT)
    place_upper_side(state, Side.LEFT)


def place_upper_side(state: State, side: Side):

    current_side = side
    opposite_side = Side.LEFT

    if current_side == Side.RIGHT:
        opposite_side = Side.LEFT
    elif current_side == Side.LEFT:
        opposite_side = Side.RIGHT
    else:
        return

    rotation_from_front(opposite_side)

    #check if the spot is not taken and if it's not taken place it down
    if spot_not_taken():
        #go up to the box
        reach_no_line()

        #place the box
        place_box_upper()

        back_up_until_line()

    #go back

    rotation_from_front(current_side)
    back_up_until_line()
'''