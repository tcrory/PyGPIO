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


Based upon the ideas implemented within:

pygpiod - (c) 2014-06-12 Leif Sawyer

which was loosely based on a script by Alex Eames http://RasPi.tv
