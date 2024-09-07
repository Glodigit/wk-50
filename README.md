# KMK + Pog + Taipo for the Debroglie / Weekin WK-50 Trackball Keyboard
KMK firmware files for the WK-50 I got from AliExpress.
A modified version of Taipo is implemented to be able to have an ambidextrous keyboard and "16-button programmable" trackball.

# Setup
Copy the files into CIRCUITPY after pog has installed KMK onto it. I'd recommend a diffchecker for files that are already on the keyboard to see if anything's changed since.

# Tetaip
Like Taipo Posh, this Taipo layout is modified enough to warrant a new name. I'll call it Tetaip, the Tetent-themed version of Taipo (with some similarities to Posh).

The main change is that space/bksp/shift are on the smallest finger, Finger4 (aka "pinky"). Aditionally, chording a character with the spacekey will add a space after it (e.g. "e " since space is pressed the most often). Like Taipo, chording with backspace will act as shift (e.g. "E").

There's also some unicode characters that I feel should've been on a standard keyboard layout by now, such as the degree or plus/minus symbol. 

In taipo.py, I've renamed the variables and added unicode diagrams so that it's easier to see what key a chord corresponds to. Like F0, F4 keys are horizontally placed because I find it much easier to move F4 to a side key than hit a key above/below. Thus, the outer keys look like:
```
In taipo.py: 
    ⬖⬘⬘⬘⬗

On keyboard: 
    ⬖⬘⬘⬘
         ⬗
```
Currently works on circuitpython 8.2.x but not 9.1.3 due to `MemoryError`.