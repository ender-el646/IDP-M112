from machine import Pin
import time 

ir = Pin(22, Pin.IN)

yellow_led_pin = 27
yellow_led = Pin(yellow_led_pin, Pin.OUT)

MAX_WAIT_TIME = 20
WAIT_TIME_US = 100
US_CONVERSION = int(1e6)
YELLOW_LIGHT_WAIT_TIME = 0.5

cur_yellow_light = 0

def wait_until_green_light():
    counter = 0
    while True:
        v = ir.value()
        counter = counter + 1
        if counter % (YELLOW_LIGHT_WAIT_TIME*US_CONVERSION/WAIT_TIME_US) == 0:
            if cur_yellow_light == 1:
                cur_yellow_light = 0
            elif cur_yellow_light == 0:
                cur_yellow_light = 1
            yellow_led.value(cur_yellow_light)
        if v == 0 or counter > (MAX_WAIT_TIME*US_CONVERSION/WAIT_TIME_US):
            return 1
        time.sleep_us(WAIT_TIME_US)