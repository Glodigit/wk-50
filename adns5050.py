# Based on KMK's adns9800.py and pimoroni_trackball.py implementations

import time
from micropython import const
import bitbangio
import digitalio
import microcontroller

from kmk.keys import AX
from kmk.modules import Module


class REG:
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
    # Wait timings (microseconds)
    tsww = const(30)
    tswr = const(20)
    tsrw = tsrr = tbexit = const(1)
    tsrad = const(4)
    # SPI Settings
    baud = const(100000)
    cpol = const(1)
    cpha = const(1)
    DIR_WRITE = const(0x80)
    DIR_READ = const(0x7F)

    def __init__(self, cs, sclk, sdio, invert_x=False, invert_y=False, north=0,):
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.north = north  # Angle offset. Not yet implemented.
        
        self.cs = digitalio.DigitalInOut(cs)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.spi = bitbangio.SPI(clock=sclk, MOSI=sdio, MISO=sdio)

    def twos_comp(val, bits=8):
        if (val & (1 << (bits - 1))) != 0: # if sign bit is set
            val = val - (1 << bits)        # compute negative value
        return val
    
    def adns_start(self):
        self.cs.value = False

    def adns_stop(self):
        self.cs.value = True
    
    def adns_write(self, reg, data):
        while not self.spi.try_lock():
            pass
        try:
            self.spi.configure(baudrate=self.baud, polarity=self.cpol, phase=self.cpha)
            self.adns_start()
            self.spi.write(bytes([reg | self.DIR_WRITE, data]))
        finally:
            self.spi.unlock()
            self.adns_stop()
    
    def adns_read(self, reg):
        result = bytearray(1)
        while not self.spi.try_lock():
            pass
        try:
            self.spi.configure(baudrate=self.baud, polarity=self.cpol, phase=self.cpha)
            self.adns_start()
            self.spi.write(bytes([reg & self.DIR_READ]))
            microcontroller.delay_us(self.tsrad)
            self.spi.readinto(result)
        finally:
            self.adns_stop()
            self.spi.unlock()

        return result[0]

    def adns_read_motion(self):
        result = bytearray(2) # Only need to capture Delta_X/Y
        while not self.spi.try_lock():
            pass
        try:
            self.spi.configure(baudrate=self.baud, polarity=self.cpol, phase=self.cpha)
            self.adns_start()
            self.spi.write(bytes([REG.Motion_Burst & self.DIR_READ]))
            microcontroller.delay_us(self.tsrad)
            self.spi.readinto(result)
        finally:
            self.adns_stop()
            self.spi.unlock()
        microcontroller.delay_us(self.tbexit)
        #self.adns_write(REG.Motion, 0x0) # Clear Delta_X/Y registers
        return result

    def during_bootup(self, keyboard):

        self.adns_write(REG.Chip_Reset, 0x5A)
        time.sleep(0.1)

        self.adns_read_motion()

        if keyboard.debug_enabled:
            print('ADNS: Product ID ', hex(self.adns_read(REG.Product_ID)))
            microcontroller.delay_us(self.tsrr)
            print('ADNS: Revision ID ', hex(self.adns_read(REG.Revision_ID)))
            microcontroller.delay_us(self.tsrr)

        return

    def before_matrix_scan(self, keyboard):
        return
        motion = self.adns_read_motion()
        #if motion[0] & 0x80:
        delta_x = self.twos_comp(motion[0])
        delta_y = self.twos_comp(motion[1])

        return
        
        if keyboard.debug_enabled & (delta_x | delta_y):
            print('Delta: ', delta_x, ' ', delta_y)

        if delta_x:
            if self.invert_x:
                delta_x *= -1
            AX.X.move(keyboard, delta_x)

        if delta_y:
            if self.invert_y:
                delta_y *= -1
            AX.Y.move(keyboard, delta_y)

        

    def after_matrix_scan(self, keyboard):
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return
    
    def adns_get_cpi(self, keyboard):
        return
    def adns_set_cpi(self, keyboard):
        return
    def adns_set_north_offset(self, keyboard):
        return
