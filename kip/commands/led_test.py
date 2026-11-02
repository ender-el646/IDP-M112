from machine import ADC, Pin
import time


yellow_led_pin = 2
green_led_pin = 27
red_led_pin = 28


yellow_led = Pin(yellow_led_pin, Pin.OUT)
green_led = Pin(green_led_pin, Pin.OUT)
red_led = Pin(red_led_pin, Pin.OUT)

red_led.value(0)
yellow_led.value(0)
green_led.value(1)
time.sleep(5)