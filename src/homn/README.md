# Mr. Homn

This is the software running on [Jessie](https://github.com/scy/jessie)’s Arduino Mega controlling switches and relays.

## Status

* done
  * interrupt-driven main loop that blinks the on-board LED in a heartbeat animation (proud of the keyframe array based implementation)
* to do
  * handling of button/switch input and relay output
  * UART handling and commands
  * UART heartbeat and host heartbeat checking

## How to Flash

Use `flash.sh`. Tested on Raspbian. Documentation could be better, but it does the job.
