from machine import Pin, I2C
from libs.VL53L0X.VL53L0X import VL53L0X
from utime import sleep_ms

i2c_bus = I2C(id=0, sda=Pin(8), scl=Pin(9))
vl53l0 = VL53L0X(i2c_bus)

# Same settings as your application
vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)

vl53l0.start()

def avg_reading(n=50, skip=5):
    vals = []
    for i in range(n + skip):
        r = vl53l0.read()
        if i >= skip and r is not None and 0 < r < 8190:
            vals.append(r)
        sleep_ms(30)
    if not vals:
        return None
    vals.sort()
    k = len(vals) // 10                     # trim 10% from each end
    if len(vals) > 2 * k:
        vals = vals[k:len(vals) - k]
    return sum(vals) / len(vals)

while True:
    true_mm = input("True distance in mm (blank to quit): ")
    if not true_mm:
        break
    print(true_mm, "->", avg_reading())

vl53l0.stop()