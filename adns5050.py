# Based on KMK's adns9800.py and pimoroni_trackball.py implementations

import busio
import digitalio
import microcontroller

import time

from kmk.keys import AX
from kmk.modules import Module


class REG:
    Product_ID = 0x0
    Revision_ID = 0x1
    Motion = 0x2
    Delta_X = 0x3
    Delta_Y = 0x4
    SQUAL = 0x5
    Shutter_Upper = 0x6
    Shutter_Lower = 0x7
    Maximum_Pixel = 0x8
    Pixel_Sum = 0x9
    Minimum_Pixel = 0xA
    Pixel_Grab = 0xB
    Mouse_Control = 0xD
    Mouse_Control2 = 0x19
    LED_DC_Mode = 0x22
    Chip_Reset = 0x3A
    Product_ID2 = 0x3E
    Inv_Rev_ID = 0x3F
    Motion_Burst = 0x63


class ADNS5050(Module):
    # Wait timings (microseconds)
    twakeup = 55
    tsww = 30
    tswr = 20
    tsrw = tsrr = tbexit = 1
    tsrad = 5
    # SPI Settings
    baud = 2000000
    cpol = 1
    cpha = 0
    DIR_WRITE = 0x80
    DIR_READ = 0x7F

    def __init__(self, cs, sclk, mosi, invert_x=False, invert_y=False):
        self.cs = digitalio.DigitalInOut(cs)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.spi = busio.SPI(clock=sclk, MOSI=mosi,)
        self.invert_x = invert_x
        self.invert_y = invert_y

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
            self.spi.unlock()
            self.adns_stop()

        return result[0]

    def delta_to_int(self, high, low):
        comp = (high << 8) | low
        if comp & 0x8000:
            return (-1) * (0xFFFF + 1 - comp)
        return comp

    def adns_read_motion(self):
        result = bytearray(14)
        while not self.spi.try_lock():
            pass
        try:
            self.spi.configure(baudrate=self.baud, polarity=self.cpol, phase=self.cpha)
            self.adns_start()
            self.spi.write(bytes([REG.Motion_Burst & self.DIR_READ]))
            microcontroller.delay_us(self.tsrad)
            self.spi.readinto(result)
        finally:
            self.spi.unlock()
            self.adns_stop()
        microcontroller.delay_us(self.tbexit)
        self.adns_write(REG.MOTION, 0x0)
        return result

    def during_bootup(self, keyboard):

        self.adns_write(REG.Power_Up_Reset, 0x5A)
        #time.sleep(0.1)
        microcontroller.delay_us(self.twakeup)
        self.adns_read(REG.Motion)
        microcontroller.delay_us(self.tsrr)
        self.adns_read(REG.DELTA_X_L)
        microcontroller.delay_us(self.tsrr)
        self.adns_read(REG.DELTA_X_H)
        microcontroller.delay_us(self.tsrr)
        self.adns_read(REG.DELTA_Y_L)
        microcontroller.delay_us(self.tsrr)
        self.adns_read(REG.DELTA_Y_H)
        microcontroller.delay_us(self.tsrw)

        # Code to write stuff [9800]

       

        if keyboard.debug_enabled:
            print('ADNS: Product ID ', hex(self.adns_read(REG.Product_ID)))
            microcontroller.delay_us(self.tsrr)
            print('ADNS: Revision ID ', hex(self.adns_read(REG.Revision_ID)))
            microcontroller.delay_us(self.tsrr)

        return

    def before_matrix_scan(self, keyboard):
        motion = self.adns_read_motion()
        if motion[0] & 0x80:
            delta_x = self.delta_to_int(motion[3], motion[2])
            delta_y = self.delta_to_int(motion[5], motion[4])

            if self.invert_x:
                delta_x *= -1
            if self.invert_y:
                delta_y *= -1

            if delta_x:
                AX.X.move(keyboard, delta_x)

            if delta_y:
                AX.Y.move(keyboard, delta_y)

            if keyboard.debug_enabled:
                print('Delta: ', delta_x, ' ', delta_y)

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
