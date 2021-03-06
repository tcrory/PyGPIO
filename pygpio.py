#!/usr/bin/env python3
#  Back Side (HDMI/microUSB)
#    -------------   [] 17 - Shutdown / Reboot
#   |    PiTFT    |  [] 22 - IP Address / VNC Server
#   |   Display   |  [] 23 - Pixel Desktop ("startx") / RetroPie ("emulationstation")
#    -------------   [] 27 - Toggle Backlight

import RPi.GPIO as GPIO
import os, subprocess, time, textwrap

# Input GPIO Button Settings
ShutdownRebootChannelIn = 17
IfconfigVncChannelIn    = 22
PixelRetroPieChannelIn  = 23
DisplayBacklightIn      = 27
# Button Press Duration Requirements
ShortButtonTimeReq      = 1     # sec
LongButtonTimeReq       = 3     # secs
# Display Backlight Output GPIO
DisplayBacklightOut     = 18
DisplayBacklightTimeout = 1800  # secs (30 mins)

pywrap  = textwrap.TextWrapper(width=52, initial_indent=" ", subsequent_indent="        ")
pywrap2 = textwrap.TextWrapper(width=52, initial_indent="        ", subsequent_indent="        ")
ipwrap  = textwrap.TextWrapper(width=52, initial_indent=" ", subsequent_indent=" ")

# GPIO Button Base Class
class PyGPIO:
    def __init__(self, channel: int):
        self.channel = channel
        self.timeDown = None
        self.timeUp = None
        self.shortTime = ShortButtonTimeReq
        self.longTime = LongButtonTimeReq
        self.usageDisplayed = None
        # Open GPIO for input, pulled up to avoid false detection.
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Create an event handler for button presses on the GPIO channel.
        GPIO.add_event_detect(self.channel, GPIO.FALLING, callback=self.callbackPress, bouncetime=300)
    def usage(self):
        print(' Override the usage method in {}.'.format(self.__class__))
    def shortpress(self):
        print(' Override the shortpress method in {}.'.format(self.__class__))
    def longpress(self):
        print(' Override the longpress method in {}'.format(self.__class__))
    def callbackPress(self, channel):
        """Button pressed event handler."""
        # Capture the time of the button press.
        self.timeDown = time.time()
        # Remove the button press event handler, create a button release handler.
        GPIO.remove_event_detect(self.channel)
        GPIO.add_event_detect(self.channel, GPIO.RISING, callback=self.callbackRelease, bouncetime=300)
    def callbackRelease(self, channel):
        """Button released event handler."""
        # Capture the time of the button release.
        self.timeUp = time.time()
        # Remove the button release event handler, create a button press handler.
        GPIO.remove_event_detect(self.channel)
        GPIO.add_event_detect(self.channel, GPIO.FALLING, callback=self.callbackPress, bouncetime=300)
        # If there is a button press time, determine whether it was a long, short, or instant press.
        if self.timeDown:
            timeDelta = int(self.timeUp - self.timeDown)
            self.timeUp = None
            self.timeDown = None
            #print('Time Delta: {}'.format(timeDelta))   # DEBUG
            if timeDelta >= self.longTime:
                #print('Calling longpress')              # DEBUG
                self.longpress()
            elif timeDelta >= self.shortTime:
                #print('Calling shortpress')             # DEBUG
                self.shortpress()
            else:
                # Limit the usage display to once per second per button.
                if not self.usageDisplayed or int(time.time() - self.usageDisplayed) >= 1:
                    self.usage()
                    self.usageDisplayed = time.time()
        else:
            print(' Button press not recorded on channel {}.'.format(self.channel))
            self.timeUp = None
            return

# Shutdown/Reboot Class
class ShutdownReboot(PyGPIO):
    """Shutdown on short press. Reboot on long press."""
    def usage(self):
        print('')
        print(pywrap.fill('Usage: Hold button for {} second{} to shutdown.'.format(self.shortTime, '' if self.shortTime == 1 else 's')))
        print(pywrap2.fill('Hold button for {} seconds to reboot.\n'.format(self.longTime)))
    def shortpress(self):
        print('\n System is shutting down.')
        time.sleep(2)
        os.system('sudo shutdown -h now "System is shutting down."')
    def longpress(self):
        print('\n System is rebooting.')
        time.sleep(2)
        os.system('sudo shutdown -r now "System is rebooting."')

# IP Address / VNC Server Class
class IpVnc(PyGPIO):
    """Display IP Address on press. Start/Kill VNC Server on short/long press."""
    def usage(self):
        """Display button usage and IP addresses."""
        # IP addresses.
        with subprocess.Popen('ifconfig', stdout=subprocess.PIPE) as ipAddr, subprocess.Popen(
                ['grep', '-o', 'inet addr:[0-9,\.]*'], stdin=ipAddr.stdout, stdout=subprocess.PIPE) as grep:
            out, err = grep.communicate()
            out = out.decode('utf-8').split('\n')
            print("\n Current IP Address:")
            print(" -------------------")
            for line in out:
                if line: print(ipwrap.fill(line))
            print('')
        # Usage message.
        print('')
        print(pywrap.fill('Usage: Hold button for {} second{} to start a VNC server on display 1.'.format(self.shortTime, '' if self.shortTime == 1 else 's')))
        print(pywrap2.fill('Hold button for {} seconds to shutdown the VNC server on display 1.\n'.format(self.longTime)))
    def shortpress(self):
        """Start VNC server on display 1."""
        self.startVNC()
    def longpress(self):
        """Stop VNC server on display 1."""
        self.endVNC()
    def startVNC(self):
        """Try to start the VNC Server on display 1."""
        try:
            subprocess.check_call(['vncserver', '-geometry', '1920x1080', ':1'], timeout=30)
        except subprocess.CalledProcessError as err:
            print('')
            print(pywrap.fill('Error: Unable to start the VNC server.'))
            print(pywrap2.fill('"{}" Command returned ({}).'.format(err.cmd, err.returncode)))
        except subprocess.TimeoutExpired as err:
            print('')
            print(pywrap.fill('Error: Unable to start the VNC server.'))
            print(pywrap2.fill('"{}" Command timed out after {} seconds.'.format(err.cmd, err.timeout)))
    def endVNC(self):
        """Try to stop the VNC Server on display 1."""
        try:
            subprocess.check_call(['vncserver', '-kill', ':1'], timeout=30)
            print('\n VNC server stopped successfully.\n')
        except subprocess.CalledProcessError as err:
            print('')
            print(pywrap.fill('Error: Unable to stop the VNC server.'))
            print(pywrap2.fill('"{}" Command returned ({}).'.format(' '.join(err.cmd), err.returncode)))
        except subprocess.TimeoutExpired as err:
            print('')
            print(pywrap.fill('Error: Unable to stop the VNC server.'))
            print(pywrap2.fill('"{}" Command timed out after {} seconds.'.format(' '.join(err.cmd), err.timeout)))

# Pixel Desktop ("startx") / RetroPie ("emulationstation")
class PixelRetroPie(PyGPIO):
    """Start Pixel desktop on short press, start RetroPie on long press."""
    def usage(self):
        print('')
        print(pywrap.fill('Usage: Hold button for {} second{} to start the Pixel desktop.'.format(self.shortTime, '' if self.shortTime == 1 else 's')))
        print(pywrap2.fill('Hold button for {} seconds to start RetroPie.\n'.format(self.longTime)))
    def shortpress(self):
        self.startPixel()
    def longpress(self):
        self.startRetroPie()
    def startPixel(self):
        """Try to start the Pixel desktop."""
        try:
            # Copy the steps that startx performs.
            my_env = os.environ.copy()
            my_env['XAUTHORITY'] = '/home/pi/.Xauthority'
            xserverauthfile = subprocess.check_output(['mktemp', '--tmpdir', 'serverauth.XXXXXXXXXX']).strip()
            subprocess.call(['xauth', '-q', '-f', xserverauthfile, '<<', 'EOF'])
            subprocess.check_call(['xinit', '/etc/X11/xinit/xinitrc', '--', '/etc/X11/xinit/xserverrc',
                                   ':0', 'vt1', '-auth', xserverauthfile], env=my_env)
        except subprocess.CalledProcessError as err:
            print('')
            print(pywrap.fill('Error: Unable to start the Pixel desktop.'))
            print(pywrap2.fill('"{}" Command returned ({}).'.format(err.cmd, err.returncode)))
        finally:
            # Clean up the temp files and vt.
            if xserverauthfile:
                subprocess.call(['rm', '-f', '"{}"'.format(xserverauthfile)])
            subprocess.call(['deallocvt'])
    def startRetroPie(self):
        """Try to start RetroPie."""
        try:
            subprocess.check_call(['emulationstation'])
        except subprocess.CalledProcessError as err:
            print('')
            print(pywrap.fill('Error: Unable to start RetroPie.'))
            print(pywrap2.fill('"{}" Command returned ({}).'.format(err.cmd, err.returncode)))

# Display Backlight Class
class Display(PyGPIO):
    """Disabled Screen Blanking by setting BLANK_TIME=0 in the /etc/kbd/config file.
       Override on the callbackPress method to turn this switch into a simple toggle.
    """
    def __init__(self, channel: int, displayChannel: int, displayTimeout: int):
        super().__init__(channel)
        self.output = displayChannel
        self.timeout = displayTimeout
        self.timeOn = None
        # Create the display GPIO
        GPIO.setup(self.output, GPIO.OUT)
        # Turn the display's backlight on.
        self.on()
    def usage(self):
        pass
    def shortpress(self):
        pass
    def longpress(self):
        pass
    def callbackPress(self, channel):
        """Button pressed event handler."""
        if self.timeOn:
            self.off()
        else:
            self.on()
    def callbackRelease(self, channel):
        pass
    def on(self):
        #print('Turning on display on channel {}.'.format(self.output))        # DEBUG
        GPIO.output(self.output, True)
        self.timeOn = time.time()
    def off(self):
        #print('Turning off display on channel {}.'.format(self.output))       # DEBUG
        GPIO.output(self.output, False)
        self.timeOn = None
    def timeoutCheck(self):
        """Compare the current time to the time that the display was turned on
           in order to determine if the display should timeout.
        """
        if self.timeOn:
            if int(time.time() - self.timeOn) >= self.timeout:
                self.off()

def main():
    # Set GPIO mode.
    GPIO.setmode(GPIO.BCM)
    # Create class instance for each button (instance includes event handlers).
    shutdownReboot  = ShutdownReboot(ShutdownRebootChannelIn)
    ipVnc           = IpVnc(IfconfigVncChannelIn)
    pixelRetroPie   = PixelRetroPie(PixelRetroPieChannelIn)
    display         = Display(DisplayBacklightIn, DisplayBacklightOut, DisplayBacklightTimeout)
    # Loop indefinitely in the background, checking the display timeout.
    while True:
        try:
            display.timeoutCheck()
            time.sleep(0.03)
        except KeyboardInterrupt:
            print('\n Disabling PiTFT GPIO Handling')
            break
    # Clean up GPIO on normal exit.
    GPIO.cleanup()           # clean up GPIO on normal exit

if __name__ == "__main__":
    import fcntl
    lockpath = '/tmp/pygpio.lock'
    with open(lockpath, 'w') as lockfile:
        try:
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            lockfile.write(str(os.getpid()))
            main()
        except OSError:
            # Daemon already running.
            pass
