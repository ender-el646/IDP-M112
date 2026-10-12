from dataclasses import dataclass, replace
from enum import Enum

class Section(Enum):
    INITIAL = 1
    UP = 2
    RIGHT = 3
    LEFT = 4

class Goal(Enum):
    GET_BOX = 1
    PLACE_BOX_UP = 2
    PLACE_BOX_DOWN = 3
    RETURN_TO_INITIAL = 4

@dataclass(frozen=True)
class State:
    position: int = 0
    section: Section = Section.INITIAL
    goal: Goal = Goal.GET_BOX

@dataclass(frozen=True)
class Position:
    position: int = 0
    section: Section = Section.INITIAL