# Custom boot settings
from kmk.bootcfg import bootcfg
import board
bootcfg(    sense  = board.ROW0,
            source = board.COL0,
            #pan    = True,
            #nkro   = True,
            )

# boot.py - v1.0.5
import usb_cdc
import supervisor
import storage
import microcontroller

# optional
# supervisor.set_next_stack_limit(4096 + 4096)
usb_cdc.enable(console=True, data=True)
# used to identify pog compatible keyboards while scanning com ports
supervisor.set_usb_identification("Pog", "WK-50 Trackball Keyboard")

# index configs
# 0 - show usb drive | 0 false, 1 true
if microcontroller.nvm[0] == 0:
    storage.disable_usb_drive()
    storage.remount("/", False)

