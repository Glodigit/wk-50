# Based on taipo.py from github.com/dlip/chouchou

try:
    from typing import Optional, Tuple, Union
except ImportError:
    pass
from micropython import const

import kmk.handlers.stock as handlers
from kmk.keys import Key, KC, make_key
from kmk.kmk_keyboard import KMKKeyboard
from kmk.modules import Module
from kmk.utils import Debug
from supervisor import ticks_ms

debug = Debug(__name__)

taipo_keycodes = {
    'TP_OL4': 0,
    'TP_OL3': 1,
    'TP_OL2': 2,
    'TP_OL1': 3,
    'TP_OL0': 4,
    'TP_OR0': 5,
    'TP_OR1': 6,
    'TP_OR2': 7,
    'TP_OR3': 8,
    'TP_OR4': 9,
    'TP_IL4': 10,
    'TP_IL3': 11,
    'TP_IL2': 12,
    'TP_IL1': 13,
    'TP_IL0': 14,
    'TP_IR0': 15,
    'TP_IR1': 16,
    'TP_IR2': 17,
    'TP_IR3': 18,
    'TP_IR4': 19,
    'LAYER0': 20,
    'LAYER1': 21,
    'LAYER2': 22,
    'LAYER3': 23,
    'MOD_GA': 24,
    'MOD_GC': 25,
    'MOD_GS': 26,
    'MOD_AC': 27,
    'MOD_AS': 28,
    'MOD_CS': 29,
    'MOD_GAC': 30,
    'MOD_GAS': 31,
    'MOD_GCS': 32,
    'MOD_ACS': 33,
    'MOD_GACS': 34,
};

o4 = 1 << 0
o3 = 1 << 1
o2 = 1 << 2
o1 = 1 << 3
o0 = 1 << 4
i4 = 1 << 5
i3 = 1 << 6
i2 = 1 << 7
i1 = 1 << 8
i0 = 1 << 9

class KeyPress:
    keycode = KC.NO
    hold = False
    hold_handled = False
    
class State:
    combo = 0
    timer = 0
    key = KeyPress()
    space = 0

class TaipoMeta:
    def __init__(self, code):
        self.taipo_code = code
    
class Taipo(Module):
    def __init__(self, tap_timeout=150, sticky_timeout=1000):
        self.tap_timeout = tap_timeout
        self.sticky_timeout=sticky_timeout
        self.state = [State(), State()]
        for key, code in taipo_keycodes.items():
            make_key( names=(key,), meta=TaipoMeta(code))

        self.keymap = {
            i2: KC.T,
            i2 | i1: KC.H,
            i0: KC.BSPC,
            o0: KC.SPC,
            o4: KC.R,
            o4 | o0: KC.LSFT(KC.R),
            o4 | i0: KC.RABK,
            o4 | o0 | i0: KC.PRINT_SCREEN,
            o3: KC.S,
            o3 | o0: KC.LSFT(KC.S),
            o3 | i0: KC.RCBR,
            o3 | o0 | i0: KC.BRIGHTNESS_UP,
            o2: KC.N,
            o2 | o0: KC.LSFT(KC.N),
            o2 | i0: KC.RBRC,
            o2 | o0 | i0: KC.BRIGHTNESS_DOWN,
            o1: KC.I,
            o1 | o0: KC.LSFT(KC.I),
            o1 | i0: KC.RPRN,
            o1 | o0 | i0: KC.MEDIA_PLAY_PAUSE,
            i4: KC.A,
            i4 | o0: KC.LSFT(KC.A),
            i4 | i0: KC.LABK,
            i4 | o0 | i0: KC.MEDIA_NEXT_TRACK,
            i3: KC.O,
            i3 | o0: KC.LSFT(KC.O),
            i3 | i0: KC.LCBR,
            i3 | o0 | i0: KC.AUDIO_VOL_UP,
            i2: KC.T,
            i2 | o0: KC.LSFT(KC.T),
            i2 | i0: KC.LBRC,
            i2 | o0 | i0: KC.AUDIO_VOL_DOWN,
            i1: KC.E,
            i1 | o0: KC.LSFT(KC.E),
            i1 | i0: KC.LPRN,
            i1 | o0 | i0: KC.MEDIA_PREV_TRACK,
            i1 | i3: KC.C,
            i1 | i3 | o0: KC.LSFT(KC.C),
            i1 | i3 | i0: KC.N1,
            i1 | i3 | o0 | i0: KC.F1,
            i2 | i3: KC.U,
            i2 | i3 | o0: KC.LSFT(KC.U),
            i2 | i3 | i0: KC.N2,
            i2 | i3 | o0 | i0: KC.F2,
            i2 | i4: KC.Q,
            i2 | i4 | o0: KC.LSFT(KC.Q),
            i2 | i4 | i0: KC.N3,
            i2 | i4 | o0 | i0: KC.F3,
            i3 | i4: KC.L,
            i3 | i4 | o0: KC.LSFT(KC.L),
            i3 | i4 | i0: KC.N4,
            i3 | i4 | o0 | i0: KC.F4,
            o1 | o2: KC.Y,
            o1 | o2 | o0: KC.LSFT(KC.Y),
            o1 | o2 | i0: KC.N5,
            o1 | o2 | o0 | i0: KC.F5,
            o1 | o3: KC.F,
            o1 | o3 | o0: KC.LSFT(KC.F),
            o1 | o3 | i0: KC.N6,
            o1 | o3 | o0 | i0: KC.F6,
            o2 | o3: KC.P,
            o2 | o3 | o0: KC.LSFT(KC.P),
            o2 | o3 | i0: KC.N7,
            o2 | o3 | o0 | i0: KC.F7,
            o2 | o4: KC.Z,
            o2 | o4 | o0: KC.LSFT(KC.Z),
            o2 | o4 | i0: KC.N8,
            o2 | o4 | o0 | i0: KC.F8,
            o3 | o4: KC.B,
            o3 | o4 | o0: KC.LSFT(KC.B),
            o3 | o4 | i0: KC.N9,
            o3 | o4 | o0 | i0: KC.F9,
            i1 | i2: KC.H,
            i1 | i2 | o0: KC.LSFT(KC.H),
            i1 | i2 | i0: KC.N0,
            i1 | i2 | o0 | i0: KC.F10,
            i1 | i4: KC.D,
            i1 | i4 | o0: KC.LSFT(KC.D),
            i1 | i4 | i0: KC.AT,
            i1 | i4 | o0 | i0: KC.F11,
            o1 | o4: KC.G,
            o1 | o4 | o0: KC.LSFT(KC.G),
            o1 | o4 | i0: KC.HASH,
            o1 | o4 | o0 | i0: KC.F12,
            i2 | o4: KC.X,
            i2 | o4 | o0: KC.LSFT(KC.X),
            i2 | o4 | i0: KC.CIRC,
            i2 | o4 | o0 | i0: KC.LCTL(KC.X),
            o1 | i3: KC.K,
            o1 | i3 | o0: KC.LSFT(KC.K),
            o1 | i3 | i0: KC.PLUS,
            o1 | i3 | o0 | i0: KC.LCTL(KC.C),
            i1 | o3: KC.V,
            i1 | o3 | o0: KC.LSFT(KC.V),
            i1 | o3 | i0: KC.ASTR,
            i1 | o3 | o0 | i0: KC.LCTL(KC.V),
            o2 | i4: KC.J,
            o2 | i4 | o0: KC.LSFT(KC.J),
            o2 | i4 | i0: KC.EQL,
            o2 | i4 | o0 | i0: KC.LCTL(KC.Z),
            i1 | o4: KC.M,
            i1 | o4 | o0: KC.LSFT(KC.M),
            i1 | o4 | i0: KC.DLR,
            # e | r | ot | it: KC.NO,
            o1 | i4: KC.W,
            o1 | i4 | o0: KC.LSFT(KC.W),
            o1 | i4 | i0: KC.AMPR,
            # i | a | ot | it: KC.NO,
            i2 | o3: KC.SLSH,
            i2 | o3 | o0: KC.BSLS,
            i2 | o3 | i0: KC.PIPE,
            # t | s | ot | it: KC.NO,
            o2 | i3: KC.MINS,
            o2 | i3 | o0: KC.UNDS,
            o2 | i3 | i0: KC.PERC,
            # n | o | ot | it: KC.NO,
            o1 | i2: KC.QUES,
            o1 | i2 | o0: KC.EXLM,
            # i | t | it: KC.NO,
            # i | t | ot | it: KC.NO,
            i1 | o2: KC.COMM,
            i1 | o2 | o0: KC.DOT,
            i1 | o2 | i0: KC.TILD,
            # e | n | ot | it: KC.NO,
            i3 | o4: KC.SCLN,
            i2 | i3 | i4: KC.SCLN,
            i3 | o4 | o0: KC.COLN,
            i2 | i3 | i4 | o0: KC.COLN,
            # o | r | it: KC.NO,
            # t | o | a | it: KC.NO,
            # o | r | ot | it: KC.NO,
            # t | o | a | ot | it: KC.NO,
            o3 | i4: KC.QUOT,
            o2 | o3 | o4: KC.QUOT,
            o3 | i4 | o0: KC.DQT,
            o2 | o3 | o4 | o0: KC.DQT,
            o3 | i4 | i0: KC.GRV,
            o2 | o3 | o4 | i0: KC.GRV,
            # s | a | ot | it: KC.NO,
            # n | s | r | ot | it: KC.NO,
            o1 | o2 | o3: KC.TAB,
            o1 | o2 | o3 | o0: KC.DEL,
            o1 | o2 | o3 | i0: KC.INS,
            # i | n | s | ot | it: KC.NO,
            i1 | i2 | i3: KC.ENTER,
            i1 | i2 | i3 | o0: KC.ESC,
            i1 | i2 | i3 | i0: KC.RALT,
            # e | t | o | ot | it: KC.NO,
            i4 | o4: KC.LGUI,
            i4 | o4 | o0: KC.RIGHT,
            i4 | o4 | i0: KC.PGUP,
            i4 | o4 | o0 | i0: KC.LAYER3,
            i3 | o3: KC.LALT,
            i3 | o3 | o0: KC.UP,
            i3 | o3 | i0: KC.HOME,
            i3 | o3 | o0 | i0: KC.LAYER2,
            i2 | o2: KC.LCTL,
            i2 | o2 | o0: KC.DOWN,
            i2 | o2 | i0: KC.END,
            i2 | o2 | o0 | i0: KC.LAYER1,
            i1 | o1: KC.LSFT,
            i1 | o1 | o0: KC.LEFT,
            i1 | o1 | i0: KC.PGDN,
            i1 | o1 | o0 | i0: KC.LAYER0,
            o4 | i4 | o3 | i3: KC.MOD_GA,
            o4 | i4 | o2 | i2: KC.MOD_GC,
            o4 | i4 | o1 | i1: KC.MOD_GS,
            o3 | i3 | o2 | i2: KC.MOD_AC,
            o3 | i3 | o1 | i1: KC.MOD_AS,
            o2 | i2 | o1 | i1: KC.MOD_CS,
            o4 | i4 | o3 | i3 | o2 | i2: KC.MOD_GAC,
            o4 | i4 | o3 | i3 | o1 | i1: KC.MOD_GAS,
            o4 | i4 | o2 | i2 | o1 | i1: KC.MOD_GCS,
            o3 | i3 | o2 | i2 | o1 | i1: KC.MOD_ACS,
            o4 | i4 | o3 | i3 | o2 | i2 | o1 | i1: KC.MOD_GACS,
        }

    def during_bootup(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        for side in [0, 1]:
            if self.state[side].timer != 0 and ticks_ms() > self.state[side].timer:
                self.state[side].key.keycode = self.determine_key(self.state[side].combo)
                self.state[side].key.hold = True
                self.handle_key(keyboard, side)
                self.state[side].timer = 0

    def after_matrix_scan(self, keyboard):
        pass

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if hasattr(key.meta, 'taipo_code'):
            side = 1 if key.meta.taipo_code / 10 >= 1 else 0
            code = key.meta.taipo_code
            if is_pressed:
                if self.state[side].key.keycode != KC.NO:
                    self.handle_key(keyboard, side)
                    self.clear_state(side)
                
                self.state[side].combo |= 1 << (key.meta.taipo_code % 10)
                self.state[side].timer = ticks_ms() + self.tap_timeout
            else:
                if not self.state[side].key.hold:
                    self.state[side].key.keycode = self.determine_key(self.state[side].combo)
                self.handle_key(keyboard, side)
                self.clear_state(side)
        else:
            return key

    def clear_state(self, side):
        # why does this not work?
        # self.state[side] = State()
        self.state[side].combo = 0
        self.state[side].timer = 0
        self.state[side].key.keycode = KC.NO
        self.state[side].key.hold = False
        self.state[side].key.hold_handled = False
        
    def handle_key(self, keyboard, side):
        key = self.state[side].key
        mods = []

        if key.keycode in [ KC.LGUI, KC.LALT, KC.RALT, KC.LCTL, KC.LSFT ]:
            mods = [key.keycode]
        elif key.keycode == KC.MOD_GA:
            mods = [KC.LGUI, KC.LALT]
        elif key.keycode == KC.MOD_GC:
            mods = [KC.LGUI,KC.LCTL]
        elif key.keycode == KC.MOD_GS:
            mods = [KC.LGUI,KC.LSFT]
        elif key.keycode == KC.MOD_AC:
            mods = [KC.LALT,KC.LSFT]
        elif key.keycode == KC.MOD_AS:
            mods = [KC.LALT,KC.LSFT]
        elif key.keycode == KC.MOD_CS:
            mods = [KC.LCTL,KC.LSFT]
        elif key.keycode == KC.MOD_GAC:
            mods = [KC.LGUI,KC.LALT,KC.LSFT]
        elif key.keycode == KC.MOD_GAS:
            mods = [KC.LGUI,KC.LALT,KC.LSFT]
        elif key.keycode == KC.MOD_GCS:
            mods = [KC.LGUI,KC.LCTL,KC.LSFT]
        elif key.keycode == KC.MOD_ACS:
            mods = [KC.LALT,KC.LCTL,KC.LSFT]
        elif key.keycode == KC.MOD_GACS:
            mods = [KC.LGUI,KC.LALT,KC.LCTL,KC.LSFT]

        if len(mods) > 0:
            for mod in mods:
                if key.hold_handled:
                    keyboard.remove_key(mod)
                elif key.hold:
                    keyboard.add_key(mod)
                    self.state[side].key.hold_handled = True
                else:
                    keyboard.tap_key(KC.OS(mod, tap_time=self.sticky_timeout))
        else:
            if key.hold_handled:
                keyboard.remove_key(key.keycode)
            elif key.hold:
                keyboard.add_key(key.keycode)
                self.state[side].key.hold_handled = True
            else:
                keyboard.tap_key(key.keycode)
        
    def determine_key(self, val):
        if val in self.keymap:
            return self.keymap[val]
        else:
            return KC.NO
       
    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

