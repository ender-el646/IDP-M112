from machine import Pin, I2C
from libs.VL53L0X.VL53L0X import VL53L0X
from utime import sleep_ms

i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9)) # I2C0 on GP8 & GP9
# print(i2c_bus.scan())  # Get the address (nb 41=0x29, 82=0x52)
    
# Setup vl53l0 object
vl53l0 = VL53L0X(i2c_bus)
vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)

def get_average_dist(sample=25):
    vl53l0.start()


    distance_sum = 0
    count = 0

    for _ in range(sample):
        reading = vl53l0.read()
        if reading is not None and reading < 8000:  # skip failed/out-of-range reads
            distance_sum += reading
            count += 1
        sleep_ms(10)
    
    vl53l0.stop()

    if count == 0:
        return 8000  

    distance = int(distance_sum / count)

    return distance


