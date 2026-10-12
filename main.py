'''from test_led import test_led
from test_pwm import test_pwm
from test_input import test_input_poll

from test_linear_actuator import test_actuator1
from test_tcs3472 import test_tcs3472
from test_vl53l0x import test_vl53l0x
from test_mfrc522 import test_mfrc522
from test_TMF8x01_get_distance import test_TMF8x01_get_distance
from test_STU_22L_IO_Mode import test_STU_22L_IO_Mode
from test_STU_22L_UART import test_STU_22L_UART
from test_tiny_code_reader import test_tiny_code_reader'''
import motor
from utime import sleep, sleep_ms
print("Start Running")

# Uncomment the test to run
# test_led()
# test_led_pwm()
# test_input_poll()
# test_motor3()
# test_tcs3472()
# test_actuator1()
# test_vl53l0x()
# test_mfrc522()
# test_TMF8x01_get_distance()
# test_STU_22L_IO_Mode()
# test_STU_22L_UART()
# test_tiny_code_reader()
motor.set_motor3(motor.FORWARD, 80)
motor.set_motor4(motor.FORWARD, 80)
sleep(2) 
motor.motors_off()         
print("main.py Done!")
