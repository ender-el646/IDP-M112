from machine import Pin, PWM
import time


class Servo:
    MIN_DUTY = 1638 # 0°
    MID_DUTY = 4915 # 135°
    MAX_DUTY = 8192 # 270°

    def __init__(self, ServoPin):
        self.servo = PWM(ServoPin)
        self.servo.freq(50)  # 50 Hz for servo

    # Convert angle (0–270) to duty
    def set_angle(self, angle):
        # Clamp angle
        if angle < 0:
            angle = 0
        if angle > 270:
            angle = 270

        duty = int(Servo.MIN_DUTY + (angle / 270) * (Servo.MAX_DUTY - Servo.MIN_DUTY))
        self.servo.duty_u16(duty)

    # Stop sending pulses so the servo goes limp
    def off(self):
        self.servo.duty_u16(0)

servo_clamp = Servo(Pin(15)) 
servo_height = Servo(Pin(13)) 

servo_height.off()
time.sleep(2)

#servo1 = Servo(Pin(15)) # Connected to Servo 1





