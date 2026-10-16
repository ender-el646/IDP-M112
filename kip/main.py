from utime import sleep
import time
from robot_types import Section, Goal, State, Position, Side
from dataclasses import replace
from planning_machine import plan
from execution_machine import move, pick_up, place_lower, place_upper

START_TIME = time.perf_counter()

FINISH_TIME = 300
THRESHOLD_TIME = 240

INITIAL_PLACE = Position(Position=0, Section=Section.INITIAL)

PICK_UPS = [Position(Position=1, Section=Section.RIGHT), 
            Position(Position=2, Section=Section.RIGHT),
            Position(Position=1, Section=Section.LEFT),
            Position(Position=2, Section=Section.LEFT)]

RIGHT_PLACES = [Position(Position=3, Section=Section.RIGHT), 
                Position(Position=4, Section=Section.RIGHT), 
                Position(Position=5, Section=Section.RIGHT), 
                Position(Position=6, Section=Section.RIGHT), 
                Position(Position=7, Section=Section.RIGHT), 
                Position(Position=8, Section=Section.RIGHT)]

LEFT_PLACES = [Position(Position=3, Section=Section.LEFT), 
                Position(Position=4, Section=Section.LEFT), 
                Position(Position=5, Section=Section.LEFT), 
                Position(Position=6, Section=Section.LEFT), 
                Position(Position=7, Section=Section.LEFT), 
                Position(Position=8, Section=Section.LEFT)]

UP_PLACES = [Position(Position=1, Section=Section.UP), 
                Position(Position=2, Section=Section.UP), 
                Position(Position=3, Section=Section.UP), 
                Position(Position=4, Section=Section.UP), 
                Position(Position=5, Section=Section.UP), 
                Position(Position=6, Section=Section.UP)]




state = State()

position1 = Position(Position=1, Section=Section.RIGHT)
position2 = Position(Position=3, Section=Section.RIGHT)
position3 = Position(Position=0, Section=Section.INITIAL)

while time.perf_counter() - START_TIME < FINISH_TIME:

    move(state, position1)
    
    replace(state.position, position1.position)
    replace(state.section, position1.section)

    pick_up(state)

    move(state, position2)

    replace(state.position, position2.position)
    replace(state.section, position2.section)

    place_lower(state)

    move(state, position3)

    replace(state.position, position3.position)
    replace(state.section, position3.section)
    

    '''

    if state.goal == Goal.GET_BOX:

        for i in PICK_UPS:

            #move to new state
            move(state, i)

            #update state
            replace(state.position, i.position)
            replace(state.section, i.section)

            #try to pickup
            result, direction = pick_up(state)
            if result == True:
                if direction == True:
                    replace(state.goal, Goal.PLACE_BOX_UP)
                else:
                    replace(state.goal, Goal.PLACE_BOX_DOWN)
                    
                break

    if state.goal == Goal.PLACE_BOX_UP:

        for i in UP_PLACES:
        
            #move to new state
            move(state, i)
        
            #update state
            replace(state.position, i.position)
            replace(state.section, i.section)

            #try to place
            result = place_upper(state)
            if result == True:
                replace(state.goal, Goal.RETURN_TO_INITIAL)
                break

    if state.goal == Goal.PLACE_BOX_DOWN:

        PLACES = []

        if state.section == Section.RIGHT:
            PLACES = RIGHT_PLACES + LEFT_PLACES

        if state.section == Section.LEFT:
            PLACES = LEFT_PLACES + RIGHT_PLACES

        for i in PLACES:
            
            #move to new state
            move(state, i)
            
            #update state
            replace(state.position, i.position)
            replace(state.section, i.section)

            #try to place
            result = place_lower(state)
            if result == True:
                placed = True
                replace(state.goal, Goal.RETURN_TO_INITIAL)
                break

    if state.goal == Goal.RETURN_TO_INITIAL:
        if time.perf_counter() - START_TIME < THRESHOLD_TIME:
            replace(state.goal, Goal.GET_BOX)
        else:
            move(state, INITIAL_PLACE)
            break
    
    '''

    