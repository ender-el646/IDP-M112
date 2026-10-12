from utime import sleep, ticks_ms, ticks_diff
import motor
import line_sensor

SMALL = 30  # small correction: how much to slow a motor by
LARGE = 50  # large correction

STRAIGHT = None
RIGHT_TURN = "right turn"
LEFT_TURN = "left turn"
CROSSROAD = "crossroad"

# Sensor reading (jumper 24, 25, 26, 27) -> (junction, slow motor 3 by, slow motor 4 by)
# Readings not listed are ignored (go straight).
ACTIONS = {
    (0, 0, 0, 0): (STRAIGHT, 0, 0),
    (0, 0, 0, 1): (STRAIGHT, 0, LARGE),
    (0, 0, 1, 0): (STRAIGHT, 0, SMALL),
    (0, 0, 1, 1): (RIGHT_TURN, 0, 0),
    (0, 1, 0, 0): (STRAIGHT, SMALL, 0),
    (0, 1, 1, 1): (RIGHT_TURN, 0, SMALL),
    (1, 0, 0, 0): (STRAIGHT, LARGE, 0),
    (1, 0, 0, 1): (CROSSROAD, 0, 0),
    (1, 1, 0, 0): (LEFT_TURN, 0, 0),
    (1, 1, 1, 0): (LEFT_TURN, SMALL, 0),
    (1, 1, 1, 1): (CROSSROAD, 0, 0),
}


def read_action():
    # Returns (junction, slow motor 3 by, slow motor 4 by) for the current reading
    return ACTIONS.get(tuple(line_sensor.read_sensors()), (STRAIGHT, 0, 0))


def follow_line(duration=10, base_speed=100, interval=0.01):
    # Follow the line for `duration` seconds, printing any junction when first seen
    last_junction = STRAIGHT
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < duration * 1000:
        junction, cut3, cut4 = read_action()
        if junction != last_junction and junction is not STRAIGHT:
            print(junction)
        last_junction = junction

        motor.set_motor3(motor.FORWARD, base_speed - cut3)
        motor.set_motor4(motor.FORWARD, base_speed - cut4)
        sleep(interval)

    motor.motors_off()


def follow_to_junction(base_speed=100, timeout=30, interval=0.01):
    # Follow the line until the next junction and return its name, leaving the motors running.
    # If already on a junction, first drives past it. Returns None (motors off) on timeout.
    leaving = True
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout * 1000:
        junction, cut3, cut4 = read_action()
        if junction is STRAIGHT:
            leaving = False
        elif not leaving:
            print(junction)
            motor.motors_off()
            return junction

        motor.set_motor3(motor.FORWARD, base_speed - cut3)
        motor.set_motor4(motor.FORWARD, base_speed - cut4)
        sleep(interval)

    motor.motors_off()
    return None


def turn_left(speed=80):
    # Drive forward onto the junction, then spin left (motor 3 = left, motor 4 = right)
    motor.set_motor3(motor.FORWARD, speed)
    motor.set_motor4(motor.FORWARD, speed)
    sleep(0.8)
    motor.set_motor3(motor.REVERSE, speed)
    motor.set_motor4(motor.FORWARD, speed)
    sleep(0.82)
    motor.motors_off()

def left180(speed=80):
    motor.set_motor3(motor.REVERSE, speed)
    motor.set_motor4(motor.FORWARD, speed)
    sleep(1.5)
    motor.motors_off()


if __name__ == "__main__":
    follow_line()
