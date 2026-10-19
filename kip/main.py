from utime import sleep, ticks_ms, ticks_diff
from robot_types import Section, Goal, State, Position, Side
from execution_machine import move, pick_up, place_lower

START_TIME = ticks_ms()

FINISH_TIME = 300
THRESHOLD_TIME = 240

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

position1 = Position(1, Section.RIGHT)
position2 = Position(3, Section.RIGHT)
position3 = Position(0, Section.INITIAL)

while elapsed() < FINISH_TIME:
    go(state, position1)
    pick_up(state)

    go(state, position2)
    place_lower(state)

    go(state, position3)

    break

'''
# Full planner loop, to re-enable once pick_up returns (result, direction)
# and place_upper exists:

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