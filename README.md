# Mr. Homn

This is the software running on [Jessie](https://github.com/scy/jessie)’s Arduino Mega controlling switches and relays.

## Status

I'm in a bit of a hurry. Documentation will improve.

* done
  * interrupt-driven main loop that blinks the on-board LED in a heartbeat animation (proud of the keyframe array based implementation)
* mostly done
  * handling of button/switch input and relay output
* to do
  * UART handling and commands
  * UART heartbeat and host heartbeat checking

## How to Flash

Use `make flash`. 
Tested on Debian Stretch. 
You can use `make install-deps` to install avr-libc and avrdude.
