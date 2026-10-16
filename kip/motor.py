from machine import Pin, PWM
from utime import sleep
from robot_types import Side

FORWARD = 1
REVERSE = 0

class Motor:
    def __init__(self, dirPin, PWMPin):
        self.mDir = Pin(dirPin, Pin.OUT)  # set motor direction pin
        self.pwm = PWM(Pin(PWMPin))  # set motor pwm pin
        self.pwm.freq(1000)  # set PWM frequency
        self.pwm.duty_u16(0)  # set duty cycle - 0=off

    def off(self):
        self.pwm.duty_u16(0)

    def set(self, direction=FORWARD, speed=100):
        # direction: FORWARD (1) or REVERSE (0); speed: 0-100 (%)
        speed = max(0, min(100, speed))
        self.mDir.value(direction)
        self.pwm.duty_u16(int(65535 * speed / 100))

    def Forward(self, speed=100):
        self.set(FORWARD, speed)

    def Reverse(self, speed=100):
        self.set(REVERSE, speed)


# Create each motor once so the pins are only set up a single time
motor_right = Motor(dirPin=7, PWMPin=6)  # Motor 3 is controlled from Motor Driver 2 #1, on GP4/5
motor_left = Motor(dirPin=4, PWMPin=5)  # Motor 4 is controlled from Motor Driver 2 #2, on GP7/6


def set_motor_right(direction=FORWARD, speed=100):
    motor_right.set(direction, speed)


def set_motor_left(direction=FORWARD, speed=100):
    motor_left.set(direction, speed)

def set_motor(side: Side, direction=FORWARD, speed=100):
    
    if side == Side.RIGHT:
        set_motor_right(direction, speed)
    else:
        set_motor_left(direction, speed)


def motor_right_off():
    motor_right.off()


def motor_left_off():
    motor_left.off()


def motors_off():
    motor_left.off()
    motor_right.off()

def set_motor_off(side: Side):

    if side == Side.RIGHT:
        motor_right.off()
    else:
        motor_left.off()
    