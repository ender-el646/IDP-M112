from machine import Pin, PWM
from utime import sleep

FORWARD = 0
REVERSE = 1


class Motor:
    def __init__(self, dirPin, PWMPin):
        self.mDir = Pin(dirPin, Pin.OUT)  # set motor direction pin
        self.pwm = PWM(Pin(PWMPin))  # set motor pwm pin
        self.pwm.freq(1000)  # set PWM frequency
        self.pwm.duty_u16(0)  # set duty cycle - 0=off

    def off(self):
        self.pwm.duty_u16(0)

    def set(self, direction=FORWARD, speed=100):
        # direction: FORWARD (0) or REVERSE (1); speed: 0-100 (%)
        speed = max(0, min(100, speed))
        self.mDir.value(direction)
        self.pwm.duty_u16(int(65535 * speed / 100))

    def Forward(self, speed=100):
        self.set(FORWARD, speed)

    def Reverse(self, speed=100):
        self.set(REVERSE, speed)


# Create each motor once so the pins are only set up a single time
motor3 = Motor(dirPin=4, PWMPin=5)  # Motor 3 is controlled from Motor Driver 2 #1, on GP4/5
motor4 = Motor(dirPin=7, PWMPin=6)  # Motor 4 is controlled from Motor Driver 2 #2, on GP7/6


def set_motor3(direction=FORWARD, speed=100):
    motor3.set(direction, speed)


def set_motor4(direction=FORWARD, speed=100):
    motor4.set(direction, speed)


def motor3_off():
    motor3.off()


def motor4_off():
    motor4.off()


def motors_off():
    motor3.off()
    motor4.off()


if __name__ == "__main__":
    set_motor3(FORWARD, 50)
    set_motor4(REVERSE, 75)
    sleep(2)
    motors_off()
