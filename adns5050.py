# Based on QMK's adns5050.c and KMK's adns9800.py implementations
# SPDX-FileCopyrightText: © 2024 Kelvin Afolabi @glodigit

import time
import digitalio
import microcontroller
from   micropython import const

from   kmk.keys    import AX, make_key
from   kmk.modules import Module


class REG: # Only 7 of these registers are used, marked with '#'
    Product_ID = const(0x0)         #
    Revision_ID = const(0x1)        #
    Motion = const(0x2)             #
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
    Mouse_Control2 = const(0x19)    #
    LED_DC_Mode = const(0x22)       #
    Chip_Reset = const(0x3A)        #
    Product_ID2 = const(0x3E)
    Inv_Rev_ID = const(0x3F)
    Motion_Burst = const(0x63)      #


class ADNS5050(Module):
    tsrad = const(4) # Wait timings (microseconds)
    DIR_WRITE = const(0x80)
    DIR_READ = const(0x7F)

    # Not compatible with standard SPI bus, so slightly different names used
    def __init__(self, ncs, clk, dio, 
                 cpi=7, dimLED=False, 
                 north=0, leftright = [45, 45], 
                 invert_x=True, invert_y=True, invert_s=False, 
                 scroll_speed=[1/2, 1/32]):
        self.ncs = digitalio.DigitalInOut(ncs)
        self.clk = digitalio.DigitalInOut(clk)
        self.dio = digitalio.DigitalInOut(dio)
        self.ncs.direction = self.clk.direction = digitalio.Direction.OUTPUT
        self.ncs.value = self.clk.value = True

        self.invert_x = invert_x
        self.invert_y = invert_y
        self.invert_s = invert_s
        self.cpi = cpi
        self.dimLED = dimLED

        self.scroll_enabled = False
        self.scroll_speed = scroll_speed # pan not working, so moves mouse x in meantime
        self.scroll_accu = [0.0, 0.0]

        make_key(names=('TB_TSCR',), on_press=self._tb_tscr) # Toggle Scroll
        make_key(names=('TB_HSCR',), # Hold to Scroll (or descroll, depending on toggle)
                 on_press=self._tb_tscr,
                 on_release=self._tb_tscr) 

        self.north = north 
        self.delta_err = [0.0, 0.0] # fractional part of delta ints
        self.leftright = leftright # adjustment angle for specific hands
        self.lr_enabled = False
        self.is_left = True

        make_key(names=('TB_NOR',), on_press=self._tb_nor)
        make_key(names=('TB_LHA',), on_press=self._tb_lha)
        make_key(names=('TB_RHA',), on_press=self._tb_rha)

    # Helper functions
    def get_sign(self, val):
        return 1 if val > 0 else 0 if val == 0 else -1
    
    def get_fractional(self, val):
        return self.get_sign(val) * (abs(val) % 1)

    def twos_comp(self, data):
        if (data & 0x80) == 0x80:
            return -128 + (data & 0x7F)
        else:
            return data
    
    # ADNS read/write
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
    
    def adns5050_init(self, keyboard):
        self.adns_write(REG.Chip_Reset, 0x5A)
        time.sleep(0.1) # Datasheet minimum is 0.055
        self.set_cpi(cpi_mode=self.cpi)
        
        # Disables LED dimming slightly when inactive. Can cause mouse to jiggle +/- 1px.
        if not self.dimLED:
            self.adns_write(REG.LED_DC_Mode, 1<<7) 

        if keyboard.debug_enabled:
            # Product / Revision ID should read 0x12 / 0x01
            print('ADNS:   Product ID ', hex(self.adns_read(REG.Product_ID)))
            print('ADNS:  Revision ID ', hex(self.adns_read(REG.Revision_ID)))
            print('ADNS: MouseControl ', '2' if self.adns_read(REG.Mouse_Control2) & (1<<4) else '1')
            print('ADNS: Control2 CPI ', self.get_cpi())
    
    def get_cpi(self):
        cpi = self.adns_read(REG.Mouse_Control2)
        return (cpi & 0xF) * 125
    
    def set_cpi(self, cpi_mode=7): # Default - 1000 CPI. Accepts values from 0 to 10 inclusive
        cpi = range(1, 12)
        self.adns_write(REG.Mouse_Control2, cpi[cpi_mode] | 0x10)
    
    # Toggles / settings
    def set_leftright(self, hand=0, enable=True):
        if not hand:
            self.lr_enabled = False
        elif enable:            
            if hand == 1 and self.leftright[0] != 0:
                self.is_left = self.lr_enabled = True
            elif hand == 2 and self.leftright[1] != 0:
                self.is_left = False
                self.lr_enabled = True
    def toggle_scroll(self):
        self.scroll_enabled = not self.scroll_enabled


    # Keyboard
    def during_bootup(self, keyboard):
        self.adns5050_init(keyboard)

    def before_matrix_scan(self, keyboard):
        if not self.adns_read(REG.Motion) >> 7:
            return
        motion = self.get_motion()
        delta_x = self.twos_comp(motion[0])
        delta_y = self.twos_comp(motion[1])

        north = self.north
        if self.lr_enabled:
            if self.is_left:
                north -= self.leftright[0]
            else:
                north += self.leftright[1]

        if north: # Apply north correction
            delta_xy = complex(delta_x + self.delta_err[0], delta_y + self.delta_err[0]) * 1j**(north/90)
            self.delta_err[0] = self.get_fractional(delta_xy.real)
            self.delta_err[1] = self.get_fractional(delta_xy.imag)
            delta_x = (int)(delta_xy.real)
            delta_y = (int)(delta_xy.imag)

        if self.scroll_enabled:
            delta_s = complex(delta_x * self.scroll_speed[0] + self.scroll_accu[0],
                              delta_y * self.scroll_speed[1] + self.scroll_accu[1])
            self.scroll_accu[0] = self.get_fractional(delta_s.real)
            self.scroll_accu[1] = self.get_fractional(delta_s.imag)
            scroll_x = (int)(delta_s.real)
            scroll_y = (int)(delta_s.imag)

            if scroll_x:
                if self.invert_x: scroll_x *= -1 
                AX.X.move(keyboard, scroll_x)

            if scroll_y:
                if self.invert_s: scroll_y *= -1 
                AX.W.move(keyboard, scroll_y)

        else:    
            if delta_x:
                if self.invert_x: delta_x *= -1 
                AX.X.move(keyboard, delta_x)

            if delta_y:
                if self.invert_y: delta_y *= -1 
                AX.Y.move(keyboard, delta_y)
                    
        
        if 1 & keyboard.debug_enabled & (delta_x | delta_y):
            print('   Delta: %7.0f %7.0f' % (delta_x, delta_y))
            print(' Delta-E: %7.4f %7.4f' % (self.delta_err[0],  self.delta_err[1]))
            print('Scroll-E: %7.4f %7.4f' % (self.scroll_accu[0], self.scroll_accu[1]))
        

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
    
    # Custom keys
    def _tb_tscr(self, *args, **kwargs):    # toggle scroll
        self.toggle_scroll()    
    
    def _tb_nor(self, *args, **kwargs):     # use north
        self.set_leftright(0)

    def _tb_lha(self, *args, **kwargs):     #angle north for left hand
        self.set_leftright(1)

    def _tb_rha(self, *args, **kwargs):     #angle north for right hand
        self.set_leftright(2)

