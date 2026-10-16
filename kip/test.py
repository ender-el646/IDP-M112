import motor
from utime import sleep



motor.motor_left.Forward(100)
motor.motor_right.Forward(100)
sleep(1)
motor.motors_off()

