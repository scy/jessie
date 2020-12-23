# Phlox

_(Because he's basically always awake.)_

Phlox is going to be the ESP32-based always-on system in my van.
It's supposed to check power levels and switch other components on or off.

The initial plan was to have a Raspberry Pi running 24/7, but it proved to be too power hungry:
Especially during the winter months, when there's not much solar power coming in, it would drain the house battery in about a week or so.

Phlox therefore has a "lower power" mode, where the Pi will be off most of the time, only woken up at predefined intervals in order to provide an internet uplink to push the latest stats.

## Connected devices

* An [Arduino MKR 485 shield](https://store.arduino.cc/arduino-mkr-485-shield) that connects to the van's [Votronic bus](https://codeberg.org/scy/votonic) and also converts 12V power to 5V.
* An [Adafruit Latching Mini Relay FeatherWing](https://www.adafruit.com/product/2923) to switch the Pi on or off.
* An [Adafruit MicroSD card breakout board+](https://www.adafruit.com/product/254) for data logging while there is no uplink.

Later on, it should also be connected to another ESP32 via SPI.
That one will be called Aziz, because it'll mostly manage the lights in the van.

## Pin configuration

Phlox has to communicate with and control quite a few other devices, therefore basically all the pins are in use:

* 1: TX0 (to USB)
* 2: RS485 RE (inv.)
* 3: RX0 (from USB)
* 4: RS485 DE
* 5: Pi relay set
* 6 to 11: on-board flash
* 12: HSPI MISO (SD)
* 13: HSPI MOSI (SD)
* 14: HSPI CLK (SD)
* 15: HSPI CS (SD)
* 16: RX2 (from RS485)
* 17: TX2 (to RS485)
* 18: VSPI CLK (reserved for Aziz)
* 19: VSPI MISO (reserved for Aziz)
* 21: I2C SDA (reserved)
* 22: I2C SCL (reserved)
* 23: VSPI MOSI (reserved for Aziz)
* 25: 3V3 from Pi (via 1k resistor against backpowering) to sense whether it's on
* 26: heartbeat from Pi
* 27: shutdown signal to Pi
* 32: reserved for touch
* 33: Pi relay unset
* 34: reserved for push button (requires ext. pull-up)
* 35: reserved for SD card detect (requires 10k pull-up)
