# Based on QMK's adns5050.c and KMK's adns9800.py implementations

import time
from micropython import const
import digitalio
import microcontroller

from kmk.keys import AX
from kmk.modules import Module


class REG: # Only 5 of these registers are used
    Product_ID = const(0x0) 
    Revision_ID = const(0x1)
    Motion = const(0x2)
    Delta_X = const(0x3)
    Delta_Y = const(0x4)
    SQUAL = const(0x5)
    Shutter_Upper = const(0x6)
    Shutter_Lower = const(0x7)
    Maximum_Pixel = const(0x8)
    Pixel_Sum = const(0x9)
    Minimum_Pixel = const(0xA)
    Pixel_Grab = const(0xB)
    Mouse_Control = const(0xD)
    Mouse_Control2 = const(0x19)
    LED_DC_Mode = const(0x22)
    Chip_Reset = const(0x3A)
    Product_ID2 = const(0x3E)
    Inv_Rev_ID = const(0x3F)
    Motion_Burst = const(0x63)


class ADNS5050(Module):
    tsrad = const(4) # Wait timings (microseconds)
    DIR_WRITE = const(0x80)
    DIR_READ = const(0x7F)

    # Not compatible with standard SPI bus, so slightly different names used
    def __init__(self, ncs, clk, dio, invert_x=True, invert_y=True, north=0,):
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.north = north # degrees
        
        self.ncs = digitalio.DigitalInOut(ncs)
        self.clk = digitalio.DigitalInOut(clk)
        self.dio = digitalio.DigitalInOut(dio)
        self.ncs.direction = self.clk.direction = digitalio.Direction.OUTPUT
        self.ncs.value = self.clk.value = True

    def twos_comp(self, data):
        if (data & 0x80) == 0x80:
            return -128 + (data & 0x7F)
        else:
            return data
    
    def adns_start(self):
        self.ncs.value = False

    def adns_stop(self):
        self.ncs.value = True

    def adns_serial_write(self, data):
        self.dio.direction = digitalio.Direction.OUTPUT
        for b in reversed(range(8)):
            self.clk.value = False
            if data & (1 << b):
                self.dio.value = True
            else:
                self.dio.value = False
            microcontroller.delay_us(1)
            self.clk.value = True
            microcontroller.delay_us(1)
        microcontroller.delay_us(self.tsrad) # Usually the amount of time needed between operations
    
    def adns_serial_read(self):
        self.dio.direction = digitalio.Direction.INPUT
        byte = 0
        for b in range(8):
            self.clk.value = False
            microcontroller.delay_us(1)
            byte = (byte << 1) | self.dio.value
            self.clk.value = True
            microcontroller.delay_us(1)
        return byte
        
    def adns_write(self, reg, data):
        self.adns_start()
        self.adns_serial_write(reg | self.DIR_WRITE)
        self.adns_serial_write(data)
        self.adns_stop()

    def adns_read(self, reg):
        byte = 0
        self.adns_start()
        self.adns_serial_write(reg & self.DIR_READ)
        byte = self.adns_serial_read()
        self.adns_stop()
        return byte

    def get_motion(self):
        motion = [0, 0]
        self.adns_start()
        self.adns_serial_write(REG.Motion_Burst & self.DIR_READ)
        motion[0] = self.adns_serial_read()
        motion[1] = self.adns_serial_read()
        self.adns_stop() # Cancel rest of burst output
        return motion
    
    def get_cpi(self):
        cpi = self.adns_read(REG.Mouse_Control2)
        return (cpi & 0xF) * 125
    
    # Accepts values from 0 to 10 inclusive
    def set_cpi(self, cpi_mode=7): # Default - 1000 CPI
        cpi = range(1, 12)
        self.adns_write(REG.Mouse_Control2, cpi[cpi_mode] | 0x10)
    
    def during_bootup(self, keyboard):
        self.adns_write(REG.Chip_Reset, 0x5A)
        time.sleep(0.1) # Datasheet minimum is 0.055
        self.set_cpi()
        # Disable LED dimming slightly when inactive. Can cause mouse to jiggle +/- 1px.
        self.adns_write(REG.LED_DC_Mode, 1<<7) 

        if keyboard.debug_enabled:
            # Product ID should read 0x12
            print('ADNS:   Product ID ', hex(self.adns_read(REG.Product_ID)))
            print('ADNS:  Revision ID ', hex(self.adns_read(REG.Revision_ID)))
            print('ADNS: MouseControl ', '2' if self.adns_read(REG.Mouse_Control2) & (1<<4) else '1')
            print('ADNS: Control2 CPI ', self.get_cpi())

        return

    def before_matrix_scan(self, keyboard):
        motion = self.get_motion()
        delta_x = self.twos_comp(motion[0])
        delta_y = self.twos_comp(motion[1])

        if self.north: # Apply north correction
            delta_xy = complex(delta_x, delta_y) * 1j**(self.north/90)
            delta_x = round(delta_xy.real)
            delta_y = round(delta_xy.imag)
        
        if delta_x:
            if self.invert_x:
                delta_x *= -1
            AX.X.move(keyboard, delta_x)

        if delta_y:
            if self.invert_y:
                delta_y *= -1
            AX.Y.move(keyboard, delta_y)
        
        if keyboard.debug_enabled & (delta_x | delta_y):
            print('Delta: ', delta_x, ' ', delta_y)
        

    def after_matrix_scan(self, keyboard):
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        # could write bit to mousecontrol register 
        return

    def on_powersave_disable(self, keyboard):
        return
