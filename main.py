from utime import sleep, ticks_ms, ticks_diff
from robot_types import Section, Goal, State, Position, Side
from execution_machine import move, pick_up, place_lower, place_upper, reach_line, check_spot, init
from machine import Pin
import hall

START_TIME = ticks_ms()

FINISH_TIME = 300
THRESHOLD_TIME = 265

def elapsed():
    # seconds since program start
    return ticks_diff(ticks_ms(), START_TIME) / 1000

INITIAL_PLACE = Position(0, Section.INITIAL)

PICK_UPS = [Position(1, Section.RIGHT),
            Position(2, Section.RIGHT),
            Position(1, Section.LEFT),
            Position(2, Section.LEFT)]

RIGHT_PLACES = [Position(i, Section.RIGHT) for i in range(3, 9)]
LEFT_PLACES = [Position(i, Section.LEFT) for i in range(3, 9)]
UP_PLACES = [Position(i, Section.UP) for i in range(1, 7)]

def go(state, target):
    # drive to target, then update the tracked state
    move(state, target)
    state.position = target.position
    state.section = target.section


state = State()

position1 = Position(1, Section.LEFT)
position2 = Position(4, Section.LEFT)
position3 = Position(3, Section.UP)
position5 = Position(0, Section.INITIAL)

button_pin = 10
button = Pin(button_pin, Pin.IN, Pin.PULL_UP)

yellow_led_pin = 2
green_led_pin = 27
red_led_pin = 28


yellow_led = Pin(yellow_led_pin, Pin.OUT)
green_led = Pin(green_led_pin, Pin.OUT)
red_led = Pin(red_led_pin, Pin.OUT)

yellow_led.value(1)
green_led.value(0)
red_led.value(0)

empty_up_left = Position(1, Section.UP)
empty_up_right = Position(1, Section.UP)
empty_right = Position(3, Section.RIGHT)
empty_left = Position(3, Section.LEFT)

while True:
    
    sleep(0.05)

    if button.value() == 0:

        init()

        START_TIME = ticks_ms()

        #left checks and left 1 box        
        if elapsed() < THRESHOLD_TIME:
            for i in range(1, 7):
                go(state, Position(i, Section.UP))
                empty = check_spot(Side.LEFT, True)
                if empty:
                    empty_up_left = Position(state.position, state.section)
                    break

            for i in range(1, 7):
                go(state, Position(i, Section.UP))
                empty = check_spot(Side.RIGHT, True)
                if empty:
                    empty_up_right = Position(state.position, state.section)
                    break
            
            for i in range(3, 9):
                go(state, Position(i, Section.LEFT))
                empty = check_spot(Side.RIGHT, False)
                if empty:
                    empty_left = Position(state.position, state.section)
                    break

            go(state, Position(1, Section.LEFT))
            field = pick_up(state)
            
            if field == 1:
                go(state, empty_up_left)
                place_upper(state, Side.LEFT)

                for i in range(state.position+1, 7):
                    go(state, Position(i, Section.UP))
                    empty = check_spot(Side.LEFT, True)
                    if empty:
                        empty_up_left = Position(state.position, state.section)
                        break

            if field == -1:
                go(state, empty_left)
                place_lower(state)
                
                for i in range(state.position+1, 9):
                    go(state, Position(i, Section.LEFT))
                    empty = check_spot(Side.RIGHT, False)
                    if empty:
                        empty_left = Position(state.position, state.section)
                        break
        
        #left 2 box        
        if elapsed() < THRESHOLD_TIME:
            go(state, Position(2, Section.LEFT))
            field = pick_up(state)

            if field == 1:
                go(state, empty_up_left)
                place_upper(state, Side.LEFT)

                '''
                for i in range(state.position+1, 7):
                    go(state, Position(i, Section.UP))
                    empty = check_spot(Side.LEFT, True)
                    if empty:
                        empty_up_left = Position(state.position, state.section)
                        break
                '''
        
        

            if field == -1:
                go(state, empty_left)
                place_lower(state)


                '''
                for i in range(state.position+1, 9):
                    go(state, Position(i, Section.LEFT))
                    empty = check_spot(Side.RIGHT, False)
                    if empty:
                        empty_left = Position(state.position, state.section)
                        break
                '''

        #right checks and right 1 box        
        if elapsed() < THRESHOLD_TIME:
            
            for i in range(3, 9):
                go(state, Position(i, Section.RIGHT))
                empty = check_spot(Side.LEFT, False)
                if empty:
                    empty_right = Position(state.position, state.section)
                    break

            go(state, Position(1, Section.RIGHT))
            field = pick_up(state)

            if field == 1:
                go(state, empty_up_right)
                place_upper(state, Side.RIGHT)
        
            if field == -1:
                go(state, empty_right)
                place_lower(state)


        go(state, Position(0, Section.INITIAL))

        break


'''

while elapsed() < FINISH_TIME:

    if state.goal == Goal.GET_BOX:
        for p in PICK_UPS:
            go(state, p)
            result, direction = pick_up(state)
            if result:
                state.goal = Goal.PLACE_BOX_UP if direction else Goal.PLACE_BOX_DOWN
                break

    if state.goal == Goal.PLACE_BOX_DOWN:
        if state.section == Section.RIGHT:
            places = RIGHT_PLACES + LEFT_PLACES
        else:
            places = LEFT_PLACES + RIGHT_PLACES
        for p in places:
            go(state, p)
            if place_lower(state):
                state.goal = Goal.RETURN_TO_INITIAL
                break

    if state.goal == Goal.RETURN_TO_INITIAL:
        if elapsed() < THRESHOLD_TIME:
            state.goal = Goal.GET_BOX
        else:
            go(state, INITIAL_PLACE)
            break
            
'''

#rotate_bot_by_set_amount(0.8)
#rotate_bot_by_set_amount(1.3)

#rotate_bot_by_set_amount(2.1)
#rotate_bot_by_set_amount(0.6)
#sleep(10)
#rotate_bot_by_set_amount(1.1)
#sleep(10)
#rotate_bot_by_set_amount(1.4)
#sleep(10)
#rotate_bot_by_set_amount(1.9)
#sleep(10)

