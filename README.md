# KMK + Pog + Taipo for the Debroglie / Weekin WK-50 Trackball Keyboard
KMK firmware files for the WK-50 I got from AliExpress.
A modified version of Taipo is implemented to be able to have an ambidextrous keyboard and "16-button programmable" trackball.

# Setup
Copy the files into CIRCUITPY after pog has installed KMK onto it. 

# Tetaip (not yet implemented)
Like Taipo Posh, this Taipo layout is modified enough to warrant a new name. I'll call it Tetaip, the Tetent-themed version of Taipo (with some similarities to Posh).

The main change is that space/bksp/shift are on the smallest finger, Finger4 (aka "pinky"). Aditionally, chording a character with the spacekey will add a space after it (e.g. "e " since space is pressed the most often), and backspace will act as shift (e.g. "E").

Speaking of 'e', I've swapped 'e' and 't' so that 'the' rolls away from the centre.

There's also some unicode characters that I feel should've been on a standard keyboard layout by now, such as the degree or plus/minus symbol.

In taipo.py, I've renamed the variables and added unicode diagrams so that it's easier to see what key a chord corresponds to.
