# =====================================================================
# table_map.py - the table as the robot sees it, and route planning.
#
# The table is symmetric. Each SIDE line ('A' = left half, 'B' = right
# half, looking from the start box towards the racks) has branches
# numbered from the bottom:
#
#     slot 1, 2  -> loading areas       (A: loading area 2, 1 / B: loading area 3, 4)
#     slot 3..8  -> lower rack bays 1..6 (e.g. B side slot 4 = B2L)
#
#     B side, drawn from above:              robot facing north on the
#                                            B side line sees every
#        B2L  <------------+  slot 4         branch on its LEFT
#        B1L  <------------+  slot 3
#        LA4  <------------+  slot 2
#        LA3  <------------+  slot 1
#                          |
#     ----[box]------------+   bottom (main) line, right corner
#
# A route is a plain list of steps; nav does the driving. Keeping routes
# as data makes it easy to print, check, and add new routes later
# (upper racks via the centre line, crossing between halves, ...).
# =====================================================================
from agv import config as C

LOADING_SLOTS = (1, 2)
RACK_SLOTS = (3, 4, 5, 6, 7, 8)

# names used in the task sheet -> (side, slot)
PLACES = {
    'LA1': ('A', 2), 'LA2': ('A', 1), 'LA3': ('B', 1), 'LA4': ('B', 2),   # [CHECK] A-side numbering
    'A1L': ('A', 3), 'A2L': ('A', 4), 'A3L': ('A', 5), 'A4L': ('A', 6), 'A5L': ('A', 7), 'A6L': ('A', 8),
    'B1L': ('B', 3), 'B2L': ('B', 4), 'B3L': ('B', 5), 'B4L': ('B', 6), 'B5L': ('B', 7), 'B6L': ('B', 8),
}


def outward(side):
    """Turn direction pointing away from the centre on this half."""
    return 'R' if side == 'B' else 'L'


def inward(side):
    return 'L' if side == 'B' else 'R'


# Step helpers --------------------------------------------------------
def FOLLOW(n, **kw):
    return ('follow', n, kw)


def TURN(direction, expect_line=True):
    return ('turn', direction, expect_line)


AXLE = ('axle',)
SPIN = ('spin180',)
CORNER = ('corner',)       # follow past branches, stop with the axle on the corner


def ARRIVE(slot):
    """Drive into the bay: loading areas end at a white border (a junction),
    rack bays end where the line stops."""
    return ('arrive_loading',) if slot in LOADING_SLOTS else ('arrive_rack',)


# Routes --------------------------------------------------------------
def start_to(place):
    """From the start box (below the main line, facing the racks) into a bay."""
    side, slot = PLACES[place]
    return [
        FOLLOW(1, lost_ok_ms=3000), AXLE, TURN(outward(side)),     # out of the box, onto the main line
        CORNER, TURN(inward(side)),                                # corner -> face north
        FOLLOW(slot), AXLE, TURN(inward(side)),                    # count branches, turn in
        ARRIVE(slot),
    ]


def bay_to_bay(src, dst):
    """From inside one bay to another (same or opposite half)."""
    s_side, s_slot = PLACES[src]
    d_side, d_slot = PLACES[dst]
    steps = [SPIN, FOLLOW(1), AXLE]                  # turn round, back to the side line
    if s_side == d_side:
        if d_slot > s_slot:                          # go north
            steps += [TURN(inward(s_side)), FOLLOW(d_slot - s_slot), AXLE, TURN(inward(s_side))]
        else:                                        # go south
            steps += [TURN(outward(s_side)), FOLLOW(s_slot - d_slot), AXLE, TURN(outward(s_side))]
    else:                                            # down, along the bottom line, up
        steps += [TURN(outward(s_side)), CORNER, TURN(outward(s_side)),
                  CORNER, TURN(outward(s_side)),
                  FOLLOW(d_slot), AXLE, TURN(inward(d_side))]
    return steps + [ARRIVE(d_slot)]


def bay_to_start(src):
    """From inside a bay back into the start box and park."""
    side, slot = PLACES[src]
    return [
        SPIN, FOLLOW(1), AXLE, TURN(outward(side)),                # back to the side line, face south
        CORNER, TURN(outward(side)),                               # pass the lower branches, corner
        FOLLOW(C.JUNCTIONS_CORNER_TO_CENTRE), AXLE,                # box edge, centre junction
        TURN(inward(side), expect_line=C.CENTRE_LINE_IN_BOX),      # face south into the box
        ('park',),
    ]
