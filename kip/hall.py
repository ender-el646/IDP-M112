from machine import ADC, Pin
import time

hall = ADC(Pin(26))

MV_PER_GAUSS = 0.5      
baseline = 2.067389

def read_voltage(samples=16):
    total = 0
    for _ in range(samples):
        total += hall.read_u16()
    return (total / samples) * 3.3 / 65535



def get_magnetic_field():
    v = read_voltage()
    gauss = (v - baseline) * 1000 / MV_PER_GAUSS
    #"north" +1 "south" -1 "none" 0
    print(gauss)
    state = 1 if gauss > 20 else -1 if gauss < -20 else 0
    #print("%.3f V  %7.1f G  magnet: %s" % (v, gauss, state))
    return state