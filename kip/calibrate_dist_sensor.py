from execution_machine import follow_straight_line, wait
import distance_sensor

CHECK_LINE_FOLLOW_DURATION = 1
FORWARD = 1

follow_straight_line(CHECK_LINE_FOLLOW_DURATION, FORWARD)

wait()

distance = distance_sensor.get_average_dist(50)

print(distance)
