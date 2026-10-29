import motor
from utime import sleep



motor.motor_left.Forward(70)
motor.motor_right.Reverse(70)
sleep(1.6)
motor.motors_off()

