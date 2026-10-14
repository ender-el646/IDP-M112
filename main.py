'''from test_led import test_led
from test_pwm import test_pwm
from test_input import test_input_poll

from test_linear_actuator import test_actuator1
from test_tcs3472 import test_tcs3472
from test_mfrc522 import test_mfrc522
from test_TMF8x01_get_distance import test_TMF8x01_get_distance
from test_STU_22L_IO_Mode import test_STU_22L_IO_Mode
from test_STU_22L_UART import test_STU_22L_UART
from test_tiny_code_reader import test_tiny_code_reader'''
import motor
from test_vl53l0x import test_vl53l0x
import line_sensor
import line_follow
from utime import sleep, sleep_ms
print("Start Running")

# Uncomment the test to run
# test_led()
# test_led_pwm()
# test_input_poll()
# test_motor3()
# test_tcs3472()
# test_actuator1()
# test_mfrc522()
# test_TMF8x01_get_distance()
# test_STU_22L_IO_Mode()
# test_STU_22L_UART()
# test_tiny_code_reader()

'''
test_vl53l0x()

# 1st turning point: stop for 1 s, then go straight
line_follow.follow_to_junction()
sleep(1)

# 2nd turning point: turn left
line_follow.follow_to_junction()
line_follow.turn_left()

line_follow.follow_to_junction()
sleep(1)
line_follow.left180()

motor.motors_off()
print("main.py Done!")
'''

from machine import ADC, Pin
import time

hall = ADC(Pin(26))        # physical pin 31 = GP26 = ADC0

def read_voltage(samples=16):
    total = 0
    for _ in range(samples):
        total += hall.read_u16()
    return (total / samples) * 3.3 / 65535

# Calibrate with no magnet nearby (idle output is about half the supply)
time.sleep(1)
baseline = read_voltage(64)
print("Baseline: %.3f V" % baseline)

MV_PER_GAUSS = 1.5        # about 1.4 mV/G at 5 V for a 49E, scaled to 3.3 V. Adjust for your part.

while True:
    v = read_voltage()
    gauss = (v - baseline) * 1000 / MV_PER_GAUSS
    state = "South" if gauss > 20 else "North" if gauss < -20 else "none"
    print("%.3f V  %7.1f G  magnet: %s" % (v, gauss, state))
    time.sleep(0.1)