from utime import sleep, ticks_ms, ticks_diff
import motor
import line_sensor

CORRECTION = 10  # how much to slow a motor by when drifting off the line


def follow_line(duration=10, base_speed=100, interval=0.01):
    # Follow the line for `duration` seconds.
    # Sensors (jumper 24, 25, 26, 27): [outer, inner, inner, outer]
    #   0,0,0,0 -> on the line, both motors at base_speed
    #   0,1,0,0 -> slow motor 3 by CORRECTION until back on the line
    #   0,0,1,0 -> slow motor 4 by CORRECTION until back on the line
    # The outer sensors mark turning points and are ignored for now.
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < duration * 1000:
        _, inner_left, inner_right, _ = line_sensor.read_sensors()

        speed3 = base_speed
        speed4 = base_speed
        if inner_left and not inner_right:
            speed3 = base_speed - CORRECTION
        elif inner_right and not inner_left:
            speed4 = base_speed - CORRECTION

        motor.set_motor3(motor.FORWARD, speed3)
        motor.set_motor4(motor.FORWARD, speed4)
        sleep(interval)

    motor.motors_off()


if __name__ == "__main__":
    follow_line()
