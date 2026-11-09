from machine import Pin
from utime import sleep, ticks_ms, ticks_diff

# Jumper labels 24-27 = GP18-21 (same mapping as test_input.py: GP18 is labelled 24)
SENSOR_PINS = [18, 19, 20, 21]

sensors = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in SENSOR_PINS]


def read_sensors():
    # Returns the 4 digital readings (0 or 1), in the order of jumper pins 24, 25, 26, 27
    return [s.value() for s in sensors]


def print_sensors(duration=30, interval=0.1):
    # Print all 4 readings repeatedly for `duration` seconds
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < duration * 1000:
        print(read_sensors())
        sleep(interval)


if __name__ == "__main__":
    print_sensors()
