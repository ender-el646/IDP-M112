class Section:
    INITIAL = 1
    UP = 2
    RIGHT = 3
    LEFT = 4

class Goal:
    GET_BOX = 1
    PLACE_BOX_UP = 2
    PLACE_BOX_DOWN = 3
    RETURN_TO_INITIAL = 4

class Side:
    RIGHT = 1
    LEFT = 2

class State:
    __slots__ = ("position", "section", "goal")

    def __init__(self, position=0, section=Section.INITIAL, goal=Goal.GET_BOX):
        self.position = position
        self.section = section
        self.goal = goal

    def __repr__(self):
        return "State(pos={}, section={}, goal={})".format(
            self.position, self.section, self.goal)

class Position:
    __slots__ = ("position", "section")

    def __init__(self, position=0, section=Section.INITIAL):
        self.position = position
        self.section = section

    def __repr__(self):
        return "Position(pos={}, section={})".format(self.position, self.section)