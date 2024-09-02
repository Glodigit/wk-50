# Based on taipo.py from github.com/dlip/chouchou
# SPDX-FileCopyrightText: © 2023 Dane Lipscombe @dlip
# SPDX-FileCopyrightText: © 2024 Kelvin Afolabi @glodigit

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

from customkeys import toggle_drive

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

        # Outer Finger 4---0: ⬖⬘⬘⬘⬗
        self.keymap = {
            # ⬖⬦⬦⬦⬦ ┊backspace┊
            o4 : KC.BSPC,

            # ⬗⬦⬦⬦⬦ ┊space┊
            i4 : KC.SPC,

            # ◆⬦⬦⬦⬦
            o4 | i4 : KC.NO,

            # ⬦⬘⬦⬦⬦ ┊A┊ ┊}┊
            o3 : KC.A,
            o3 | o4 : KC.LSFT(KC.A),
            o3 | i4 : KC.MACRO("a "),
            o3 | o4 | i4 : KC.RCBR,

            # ⬦⬦⬘⬦⬦ ┊N┊ ┊]┊
            o2 : KC.N,   
            o2 | o4 : KC.LSFT(KC.N),
            o2 | i4 : KC.MACRO("n "),
            o2 | o4 | i4 : KC.RBRC,

            # ⬦⬦⬦⬘⬦ ┊I┊ ┊)┊
            o1 : KC.I,   
            o1 | o4 : KC.LSFT(KC.I),
            o1 | i4 : KC.MACRO("i "),
            o1 | o4 | i4 : KC.RPRN,

            # ⬦⬦⬦⬦⬗ ┊S┊ ┊>┊
            o0 : KC.S,
            o0 | o4 : KC.LSFT(KC.S),
            o0 | i4 : KC.MACRO("s "),
            o0 | o4 | i4 : KC.RABK,

            # ⬦⬙⬦⬦⬦ ┊O┊ ┊{┊
            i3 : KC.O,   
            i3 | o4 : KC.LSFT(KC.O), 
            i3 | i4 : KC.MACRO("o "),   
            i3 | o4 | i4 : KC.LCBR,

            # ⬦⬦⬙⬦⬦ ┊T┊ ┊[┊
            i2 : KC.T,
            i2 | o4 : KC.LSFT(KC.T),
            i2 | i4 : KC.MACRO("t "),
            i2 | o4 | i4 : KC.LBRC,

            # ⬦⬦⬦⬙⬦ ┊E┊ ┊(┊
            i1 : KC.E,
            i1 | o4 : KC.LSFT(KC.E),
            i1 | i4 : KC.MACRO("e "),
            i1 | o4 | i4 : KC.LPRN,

            # ⬦⬦⬦⬦⬖ ┊R┊ ┊<┊
            i0 : KC.R,   
            i0 | o4 : KC.LSFT(KC.R), 
            i0 | i4 : KC.MACRO("r "),
            i0 | o4 | i4 : KC.LABK,

            # ⬦⬘⬘⬦⬦ ┊C┊ ┊copy┊
            o2 | o3 : KC.P,
            o2 | o3 | o4 : KC.LSFT(KC.C),
            o2 | o3 | i4 : KC.MACRO("c "),
            o2 | o3 | o4 | i4 : KC.LCTL(KC.C),

            # ⬦⬘⬦⬘⬦ ┊F┊ ┊find┊
            o1 | o3 : KC.F,
            o1 | o3 | o4 : KC.LSFT(KC.F),
            o1 | o3 | i4 : KC.MACRO("f "),
            o1 | o3 | o4 | i4 : KC.LCTL(KC.F),

            # ⬦⬘⬦⬦⬗ ┊B┊ ┊select all┊
            o3 | o0 : KC.B,
            o3 | o0 | o4 : KC.LSFT(KC.B),
            o3 | o0 | i4 : KC.MACRO("b "),
            o3 | o0 | o4 | i4 : KC.LCTL(KC.A), # mnemonic: blue all

            # ⬦⬙⬙⬦⬦ ┊U┊
            i2 | i3 : KC.U,
            i2 | i3 | o4 : KC.LSFT(KC.U),
            i2 | i3 | i4 : KC.MACRO("u "),
            i2 | i3 | o4 | i4 : KC.NO,
            
            # ⬦⬙⬦⬙⬦ ┊P┊ ┊onenote find┊
            i1 | i3 : KC.C,
            i1 | i3 | o4 : KC.LSFT(KC.P),
            i1 | i3 | i4 : KC.MACRO("p "),
            i1 | i3 | o4 | i4 : KC.LCTL(KC.E),
            
            # ⬦⬙⬦⬦⬖ ┊L┊
            i3 | i0 : KC.L,
            i3 | i0 | o4 : KC.LSFT(KC.L),
            i3 | i0 | i4 : KC.MACRO("l "),
            i3 | i0 | o4 | i4 : KC.NO,

            # ⬦⬦⬘⬘⬦ ┊G┊
            o1 | o2 : KC.G,
            o1 | o2 | o4 : KC.LSFT(KC.G),
            o1 | o2 | i4 : KC.MACRO("g "),
            o1 | o2 | o4 | i4 : KC.NO,

            # ⬦⬦⬘⬦⬗ ┊Z┊ ┊undo┊
            o2 | o0 : KC.Z,
            o2 | o0 | o4 : KC.LSFT(KC.Z),
            o2 | o0 | i4 : KC.MACRO("z "),
            o2 | o0 | o4 | i4 : KC.LCTL(KC.Z),

            # ⬦⬦⬙⬙⬦ ┊H┊
            i1 | i2 : KC.H,
            i1 | i2 | o4 : KC.LSFT(KC.H),
            i1 | i2 | i4 : KC.MACRO("h "),
            i1 | i2 | o4 | i4 : KC.NO,

            # ⬦⬦⬙⬦⬖ ┊Q┊
            i2 | i0 : KC.Q,
            i2 | i0 | o4 : KC.LSFT(KC.Q),
            i2 | i0 | i4 : KC.MACRO("q "),
            i2 | i0 | o4 | i4 : KC.NO,

            # ⬦⬦⬦⬘⬗ ┊Y┊ ┊redo┊
            o1 | o0 : KC.Y,
            o1 | o0 | o4 : KC.LSFT(KC.Y),
            o1 | o0 | i4 : KC.MACRO("y "),
            o1 | o0 | o4 | i4 : KC.LCTL(KC.Y),

            # ⬦⬦⬦⬙⬖ ┊D┊ 
            i1 | i0 : KC.D,
            i1 | i0 | o4 : KC.LSFT(KC.D),
            i1 | i0 | i4 : KC.MACRO("d "),
            i1 | i0 | o4 | i4 : KC.NO,

            # ⬦⬘⬙⬦⬦ ┊X┊ ┊cut┊
            i2 | o3 : KC.X,
            i2 | o3 | o4 : KC.LSFT(KC.X),
            i2 | o3 | i4 : KC.MACRO("x "),
            i2 | o3 | o4 | i4 : KC.LCTL(KC.X),

            # ⬦⬘⬦⬙⬦ ┊V┊ ┊paste┊
            i1 | o3 : KC.V,
            i1 | o3 | o4 : KC.LSFT(KC.V),
            i1 | o3 | i4 : KC.MACRO("v "),
            i1 | o3 | o4 | i4 : KC.LCTL(KC.V),

            # ⬦⬘⬦⬦⬖ ┊'┊ ┊`┊ ┊"┊ ┊°┊
            o0 | o3 : KC.QUOTE,
            o0 | o3 | o4 : KC.GRAVE,
            o0 | o3 | i4 : KC.DQUO, #KC.AT,
            o0 | o3 | o4 | i4 : KC.MACRO("°"),

            # ⬦⬙⬘⬦⬦ ┊_┊ ┊+┊ ┊-┊ ┊±┊
            o2 | i3 : KC.UNDS,
            o2 | i3 | o4 : KC.PLUS,
            o2 | i3 | i4 : KC.MINS,
            o2 | i3 | o4 | i4 : KC.MACRO("±"),

            # ⬦⬙⬦⬘⬦ ┊|┊ ┊/┊ ┊\┊ ┊%┊
            o1 | i3 : KC.PIPE,
            o1 | i3 | o4 : KC.BSLS,
            o1 | i3 | i4 : KC.SLSH,
            o1 | i3 | o4 | i4 : KC.PERC,

            # ⬦⬙⬦⬦⬗ ┊,┊ ┊;┊ ┊.┊ ┊:┊
            o0 | i3 : KC.COMMA,
            o0 | i3 | o4 : KC.SCOLON,
            o0 | i3 | i4 : KC.DOT,
            o0 | i3 | o4 | i4 : KC.COLON,

            # ⬦⬦⬘⬙⬦ ┊?┊ ┊@┊ ┊!┊ ┊&┊
            i1 | o2: KC.QUES,
            i1 | o2 | o4 : KC.AT, #KC.DQUO,
            i1 | o2 | i4 : KC.EXCLAIM,
            i1 | o2 | o4 | i4 : KC.AMPERSAND,

            # ⬦⬦⬘⬦⬖ ┊J┊
            o2 | i0 : KC.J,
            o2 | i0 | o4 : KC.LSFT(KC.J),
            o2 | i0 | i4 : KC.MACRO("j "),
            o2 | i0 | o4 | i4 : KC.NO,

            # ⬦⬦⬙⬘⬦ ┊=┊ ┊~┊ ┊≈┊ ┊≠┊
            o1 | i2 : KC.EQUAL,
            o1 | i2 | o4 : KC.TILDE,
            o1 | i2 | i4 : KC.MACRO("≈"),
            o1 | i2 | o4 | i4 : KC.MACRO("≠"),

            # ⬦⬦⬙⬦⬗ ┊K┊
            o0 | i2: KC.K,
            o0 | i2 | o4 : KC.LSFT(KC.K),
            o0 | i2 | i4 : KC.MACRO("k "),
            o0 | i2 | o4 | i4 : KC.NO,

            # ⬦⬦⬦⬘⬖ ┊W┊
            o1 | i0: KC.W,
            o1 | i0 | o4 : KC.LSFT(KC.W),
            o1 | i0 | i4 : KC.MACRO("w "),
            o1 | i0 | o4 | i4 : KC.NO,

            # ⬦⬦⬦⬙⬗ ┊M┊
            i1 | o0: KC.M,
            i1 | o0 | o4 : KC.LSFT(KC.M),
            i1 | o0 | i4 : KC.MACRO("m "),
            i1 | o0 | o4 | i4 : KC.NO,

            # ⬦⬘⬘⬘⬦ ┊tab┊ ┊shift+tab┊ ┊alt+tab┊ ┊gui+tab┊
            o1 | o2 | o3: KC.TAB,
            o1 | o2 | o3 | o4 : KC.LSFT(KC.TAB),
            o1 | o2 | o3 | i4 : KC.LALT(KC.TAB),
            o1 | o2 | o3 | o4 | i4 : KC.LGUI(KC.TAB),

            # ⬦⬘⬘⬦⬗

            # ⬦⬘⬦⬘⬗

            # ⬦⬦⬘⬘⬗ ┊del┊ ┊ctrl+bkspace┊ ┊ctrl+del┊
            o0 | o1 | o2 : KC.DEL,
            o0 | o1 | o2 | o4 : KC.LCTRL(KC.BSPC),
            o0 | o1 | o2 | i4 : KC.LCTRL(KC.DEL),

            # ⬦⬙⬙⬙⬦ ┊enter┊ ┊none┊ ┊right alt┊ 
            i1 | i2 | i3: KC.ENTER,
            i1 | i2 | i3 | o4 : KC.NO,
            i1 | i2 | i3 | i4 : KC.RALT,
            i1 | i2 | i3 | o4 | i4 : KC.NO,

            # ⬦⬙⬙⬦⬖

            # ⬦⬙⬦⬙⬖ ┊desktop┊
            i0 | i1 | i3 : KC.LGUI(KC.D),

            # ⬦⬦⬙⬙⬖ ┊esc┊
            i0 | i1 | i3 : KC.ESC,

            # ⬦⬘⬙⬘⬦ ┊£┊ ┊€┊ ┊$┊  (mnemonic: v for value)
            o1 | i2 | o3 : KC.MACRO("£"),
            o1 | i2 | o3 | o4 : KC.MACRO("€"),
            o1 | i2 | o3 | i4 : KC.DOLLAR,

            # ⬦⬘⬙⬦⬗

            # ⬦⬘⬦⬙⬗           

            # ⬦⬦⬘⬙⬗ ┊mute┊ ┊-vol┊ ┊+vol┊
            o0 | i1 | o2 : KC.MUTE,
            o0 | i1 | o2 | o4 : KC.VOLD,
            o0 | i1 | o2 | i4 : KC.VOLU,
            o0 | i1 | o2 | o4 | i4 : KC.NO,

            # ⬦⬙⬘⬙⬦ ┊^┊
            i1 | o2 | i3 : KC.CIRC,

            # ⬦⬙⬘⬦⬖

            # ⬦⬙⬦⬘⬖

            # ⬦⬦⬙⬘⬖ ┊printscreen┊
            i0 | o1 | i2 : KC.PSCREEN,

            # ⬦⬘⬘⬙⬦ ┊explorer┊
            i1 | o2 | o3 : KC.LGUI(KC.E),

            # ⬦⬘⬘⬦⬖ ┊circuitpy visible┊
            i0 | o2 | o3 : KC.MACRO(toggle_drive),

            # ⬦⬘⬦⬘⬖

            # ⬦⬦⬘⬘⬖ ┊pgup┊ ┊none┊ ┊ctrl+pgup┊
            i0 | o1 | o2 : KC.PGUP,
            i0 | o1 | o2 | i4 : KC.LCTRL(KC.PGUP),

            # ⬦⬙⬙⬘⬦ ┊home┊ ┊none┊ ┊ctrl+home┊
            o1 | i2 | i3 : KC.HOME,
            o1 | i2 | i3 | i4 : KC.LCTRL(KC.HOME),

            # ⬦⬙⬦⬙⬗

            # ⬦⬦⬙⬙⬗ ┊pgdn┊ ┊none┊ ┊ctrl+pgdn┊
            o0 | i1 | i2 : KC.PGDN,
            o0 | i1 | i2 | i4 : KC.LCTRL(KC.PGDN),

            # ⬦⬘⬙⬙⬦ ┊end┊ ┊none┊ ┊ctrl+end┊
            i1 | o2 | o3 : KC.END,
            i1 | o2 | o3 | i4 : KC.LCTRL(KC.END),

            # ⬦⬘⬙⬦⬖

            # ⬦⬘⬦⬙⬖ 

            # ⬦⬦⬘⬙⬖ ┊insert┊
            i0 | i1 | o2 : KC.INSERT,

            # ⬦⬙⬘⬘⬦ ┊#┊ ┊none┊ ┊#+space┊
            o1 | o2 | i3 : KC.HASH,
            o1 | o2 | i3 | i4 : KC.MACRO("# "),

            # ⬦⬙⬘⬦⬗

            # ⬦⬙⬦⬘⬗

            # ⬦⬦⬙⬘⬗ ┊num-lock┊ ┊scroll-lock┊ ┊caps-lock┊
            o0 | o1 | i2 : KC.NUMLOCK,
            o0 | o1 | i2 | o4 : KC.SCROLLLOCK,
            o0 | o1 | i2 | i4 : KC.CAPSLOCK,

            # ⬦⬘⬘⬘⬗ ┊0┊ ┊num0┊ ┊F20┊ (numbers are binary chords)
            o0 | o1 | o2 | o3 : KC.N0,
            o0 | o1 | o2 | o3 | o4 : KC.P0,
            o0 | o1 | o2 | o3 | i4 : KC.F20,

            # ⬦⬘⬘⬘⬖ ┊1┊ ┊num1┊ ┊F1┊
            i0 | o1 | o2 | o3 :      KC.N1,
            i0 | o1 | o2 | o3 | o4 : KC.P1,
            i0 | o1 | o2 | o3 | i4 : KC.F1,

            # ⬦⬘⬘⬙⬗ ┊2┊ ┊num2┊ ┊F2┊
            o0 | i1 | o2 | o3 :      KC.N2,
            o0 | i1 | o2 | o3 | o4 : KC.P2,
            o0 | i1 | o2 | o3 | i4 : KC.F2,

            # ⬦⬘⬘⬙⬖ ┊3┊ ┊num3┊ ┊F3┊
            i0 | i1 | o2 | o3 :      KC.N3,
            i0 | i1 | o2 | o3 | o4 : KC.P3,
            i0 | i1 | o2 | o3 | i4 : KC.F3,

            # ⬦⬘⬙⬘⬗ ┊4┊ ┊num4┊ ┊F4┊
            o0 | i1 | o2 | o3 :      KC.N4,
            o0 | i1 | o2 | o3 | o4 : KC.P4,
            o0 | i1 | o2 | o3 | i4 : KC.F4,

            # ⬦⬘⬙⬘⬖ ┊5┊ ┊num5┊ ┊F5┊
            i0 | o1 | i2 | o3 :      KC.N5,
            i0 | o1 | i2 | o3 | o4 : KC.P5,
            i0 | o1 | i2 | o3 | i4 : KC.F5,

            # ⬦⬘⬙⬙⬗ ┊6┊ ┊num6┊ ┊F6┊
            o0 | i1 | i2 | o3 :      KC.N6,
            o0 | i1 | i2 | o3 | o4 : KC.P6,
            o0 | i1 | i2 | o3 | i4 : KC.F6,

            # ⬦⬘⬙⬙⬖ ┊7┊ ┊num7┊ ┊F7┊
            i0 | i1 | i2 | o3 :      KC.N7,
            i0 | i1 | i2 | o3 | o4 : KC.P7,
            i0 | i1 | i2 | o3 | i4 : KC.F7,

            # ⬦⬙⬘⬘⬗ ┊8┊ ┊num8┊ ┊F8┊
            o0 | o1 | o2 | i3 :      KC.N8,
            o0 | o1 | o2 | i3 | o4 : KC.P8,
            o0 | o1 | o2 | i3 | i4 : KC.F8,

            # ⬦⬙⬘⬘⬖ ┊9┊ ┊num9┊ ┊F9┊
            i0 | o1 | o2 | i3 :      KC.N9,
            i0 | o1 | o2 | i3 | o4 : KC.P9,
            i0 | o1 | o2 | i3 | i4 : KC.F9,

            # ⬦⬙⬘⬙⬗ ┊F10┊ ┊none┊ ┊F14┊
            i0 | o1 | i2 | o3 : KC.F10,
            i0 | o1 | i2 | o3 | i4: KC.F14,

            # ⬦⬙⬘⬙⬖ ┊F11┊ ┊none┊ ┊F15┊
            i0 | o1 | i2 | i3 : KC.F11,
            i0 | o1 | i2 | i3 | i4 : KC.F15,

            # ⬦⬙⬙⬘⬗ ┊F12┊ ┊none┊ ┊F16┊
            i0 | i1 | o2 | o3 : KC.F12,
            i0 | i1 | o2 | o3 | i4 : KC.F16,

            # ⬦⬙⬙⬘⬖ ┊F13┊ ┊none┊ ┊F17┊
            i0 | i1 | o2 | i3 : KC.F13,
            i0 | i1 | o2 | i3 | i4 : KC.F17,
            
            # Onenote 
            # ⬦⬙⬙⬙⬗ ┊datestamp┊ ┊datestamp+bkspace┊ ┊datestamp+dash┊
            i0 | i1 | o2 | o3 : KC.LSFT(KC.LALT(KC.D)),
            i0 | i1 | o2 | o3 | o4 : KC.MACRO(KC.LSFT(KC.LALT(KC.D)), KC.BSPC),
            i0 | i1 | o2 | o3 | i4 : KC.MACRO(KC.LSFT(KC.LALT(KC.D)), KC.DASH),

            # ⬦⬙⬙⬙⬖ ┊timestamp┊ ┊timestamp+bkspace┊ ┊timestamp+dash┊
            i0 | i1 | o2 | i3 : KC.LSFT(KC.LALT(KC.T)),
            i0 | i1 | o2 | i3 | o4 : KC.MACRO(KC.LSFT(KC.LALT(KC.T)), KC.BSPC),
            i0 | i1 | o2 | i3 | i4 : KC.MACRO(KC.LSFT(KC.LALT(KC.T)), KC.DASH),

            # Modifiers / Layers
            # ⬦◆⬦⬦⬦
            i3 | o3: KC.LALT,
            i3 | o3 | o4 : KC.NO,
            i3 | o3 | i4 : KC.LAYER3,
            i3 | o3 | o4 | i4 : KC.NO,

            # ⬦⬦◆⬦⬦
            i2 | o2: KC.LCTL,
            i2 | o2 | o4 : KC.NO,
            i2 | o2 | i4 : KC.LAYER2,
            i2 | o2 | o4 | i4 : KC.NO,

            # ⬦⬦⬦◆⬦
            i1 | o1: KC.LSFT,
            i1 | o1 | o4 : KC.NO,
            i1 | o1 | i4 : KC.LAYER1,
            i1 | o1 | o4 | i4 : KC.NO,

            # ⬦⬦⬦⬦◆
            i0 | o0: KC.LGUI,
            i0 | o0 | o4 : KC.NO,
            i0 | o0 | i4 : KC.LAYER0,
            i0 | o0 | o4 | i4 : KC.NO,

            o0 | i0 | o3 | i3: KC.MOD_GA,
            o0 | i0 | o2 | i2: KC.MOD_GC,
            o0 | i0 | o1 | i1: KC.MOD_GS,
            o3 | i3 | o2 | i2: KC.MOD_AC,
            o3 | i3 | o1 | i1: KC.MOD_AS,
            o2 | i2 | o1 | i1: KC.MOD_CS,
            o0 | i0 | o3 | i3 | o2 | i2: KC.MOD_GAC,
            o0 | i0 | o3 | i3 | o1 | i1: KC.MOD_GAS,
            o0 | i0 | o2 | i2 | o1 | i1: KC.MOD_GCS,
            o3 | i3 | o2 | i2 | o1 | i1: KC.MOD_ACS,
            o0 | i0 | o3 | i3 | o2 | i2 | o1 | i1: KC.MOD_GACS,
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

