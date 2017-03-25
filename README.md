PyGPIO - (c) 2016-12-28 Timothy Crory

Requires RPi.GPIO: http://sourceforge.net/projects/raspberry-gpio-python

This is a simple daemon-esque script that is meant to be run in the background
at startup on a Raspberry Pi.

It allows for triggering of different types of events (short-press, long-press,
longer-press) in order to provide the maximum amount of functionality with the
limited number of GPIO lanes.

Configuration settings can be set at the head of the file, including changing
which channels should be used and how long buttons must be pressed to trigger
the effects.

```
The script is designed to be run from the .bashrc file as a background process.
    After logging in to the raspberry pi:
        # sudo nano ~/.bashrc
    At the end of the .bashrc file, type:
        { /usr/bin/python3 /full/path/to/script/pygpio.py & disown; }
    Save and exit by pressing:
        [Ctrl] + [X]
        [Y]
        [Enter]
```

Based upon the ideas implemented within:

pygpiod - (c) 2014-06-12 Leif Sawyer

which was loosely based on a script by Alex Eames http://RasPi.tv
