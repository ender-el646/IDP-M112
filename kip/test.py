import motor
from utime import sleep



motor.motor_left.Forward(80)
motor.motor_right.Forward(80)
sleep(0.6)
motor.motors_off()

