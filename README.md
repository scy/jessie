# Mr. Homn

This is the software running on [Jessie](https://github.com/scy/jessie)’s Arduino Mega controlling switches and relays.

## Status

I'm in a bit of a hurry. Documentation will improve.

* done
  * interrupt-driven main loop that blinks the on-board LED in a heartbeat animation (proud of the keyframe array based implementation)
  * handling of button/switch input and relay output
* to do
  * UART handling and commands
  * UART heartbeat and host heartbeat checking

## Bugs

* It might behave unexpectedly if you configure it to have no input or no output port.
  
## How to Flash

Use `make clean flash` to flash it to the Duemilanove. 
Use `make MCU=atmega1280 clean flash` to flash it to the Mega. 
If you want to flash the output test routine instead of the normal button behavior, use `make FLAGS=-DDO_OUTPUTTEST clean flash` (combined with `MCU=atmega1280` for the Mega).

Tested on Debian Stretch. 
You can use `make install-deps` to install avr-libc and avrdude.

## Port/Pin Mapping

This code is designed to run on two devices: 
An Arduino Duemilanove (`MCU=atmega168`) that I use for testing and an older Arduino Mega (`MCU=atmega1280`) that's built into the van (read: the production system).

Since the two controllers have a different number of ports, there is no universal pin mapping for both. 
Instead, each one has its own.

For easier handling in the code (array indexes!), I map the AVR port names (A, B, C etc.) to numbers internally. 
To simplify things further, each port on the Mega is only used for input _or_ for output, i.e. I won't use four pins as input and four as output. 
This is not true for the Duemilanove: 
Since it only has three ports, I had to use port B for both input and output in order to let it have two input and two output ports. 

Not all pins of a port are necessarily available for GPIO, for example if they're the UART pins.

### On the Duemilanove

| Port  | Usage                 | Notes                                                                                |
|:-----:| --------------------- | ------------------------------------------------------------------------------------ |
| **B** | **In 1**/**Out 1**    | (pin 0 input, labelled _Digital_ 8; pin 1 and 2 output, labelled _Digital_ 9 and 10) |
| **C** | **In 0**              | (low 6 pins only, labelled _Analog In_ 0 to 5)                                       |
| **D** | **Out 0**             | (high 6 pins only, labelled _Digital_ 2 to 7)                                        |

That's 7 inputs and 8 outputs. 
I haven't used PB3 to PB5 (digital 11 to 13), since they double as ISP ports.

### On the Mega

The ports are kind of a mess here. 
Some are scattered all over the board, others are labelled in the opposite direction (i.e. pin 0 labelled 37, pin 7 labelled 30). 
I've tried to reflect this in the table below.

| Port  | Usage     | Notes                                                             |
|:-----:| --------- | ----------------------------------------------------------------- |
| **A** | **Out 0** | (labelled _Digital_ 22 to 29)                                     |
| **B** | **In 1**  | (low 7 bits only, labelled _Digital_ 53 to 50 and _PWM_ 10 to 12) |
| **C** | **Out 1** | (labelled _Digital_ 37 to 30)                                     |
| **F** | reserved  | (labelled _Analog In_ 0 to 7) reserved for actual analog input    |
| **G** | **In 2**  | (low 3 pins only, labelled _Digital_ 41 to 39)                    |
| **K** | **In 0**  | (labelled _Analog In_ 8 to 15)                                    |
| **L** | **Out 2** | (labelled _Digital_ 49 to 42)                                     |

That's 18 inputs and 24 outputs, with 8 pins reserved for analog input (e.g. temperature or water tank). 
I haven't used PB7 (digital 13), since it doubles as the LED.

#### Ribbon Cable

I'm using a 40-wire rainbow ribbon cable by Joy-IT (RB-CB2-030) to connect the 2x18-pin female port of the Mega to six 4-relay boards and some inputs. 
The great thing with this cable is that on one end it ends in 40 single Dupont jacks that can easily be removed from their plastic housing and grouped together as you wish. 
However, since the IDE-style connector it has at the other end is female as well, it doesn't couple nicely with the Mega. 
(It's certainly made for a Raspberry Pi's GPIO pins.)

To work around that, I've crimped a cutting 40-pin male IDE connector to the end of the cable directly adjacent to the female one. 
When you remove some of its plastic housing, it fits nicely on the Mega, even though two pins on either side stay unconnected.

These are the pins of the Mega's port and how they map to the cable and the peripherals connected to it. 
It's ordered by the wires on the cable (the _color_ column).

| Pin | Type | Internal | Label | Color  | Relay | Connected To         |
| --- | ---- | -------- | ----- | ------ | ----- | -------------------- |
|     |      |          |       | black  |       |                      |
|     |      |          |       | white  |       |                      |
|     |      |          | 5V    | gray   |       |                      |
|     |      |          | 5V    | purple |       |                      |
| PA1 | Out  | 0,1      | 23    | blue   | 1-2   | drinking water pump  |
| PA0 | Out  | 0,0      | 22    | green  | 1-1   | main water pump      |
| PA3 | Out  | 0,3      | 25    | yellow | 1-4   |                      |
| PA2 | Out  | 0,2      | 24    | orange | 1-3   |                      |
| PA5 | Out  | 0,5      | 27    | red    | 2-2   |                      |
| PA4 | Out  | 0,4      | 26    | brown  | 2-1   |                      |
| PA7 | Out  | 0,7      | 29    | black  | 2-4   |                      |
| PA6 | Out  | 0,6      | 28    | white  | 2-3   |                      |
| PC6 | Out  | 1,6      | 31    | gray   | 4-3   |                      |
| PC7 | Out  | 1,7      | 30    | purple | 4-4   |                      |
| PC4 | Out  | 1,4      | 33    | blue   | 4-1   |                      |
| PC5 | Out  | 1,5      | 32    | green  | 4-2   |                      |
| PC2 | Out  | 1,2      | 35    | yellow | 3-3   |                      |
| PC3 | Out  | 1,3      | 34    | orange | 3-4   |                      |
| PC0 | Out  | 1,0      | 37    | red    | 3-1   |                      |
| PC1 | Out  | 1,1      | 36    | brown  | 3-2   |                      |
| PG2 | In   | 2,2      | 39    | black  |       | sink (foot switch)   |
| PD7 |      |          | 38    | white  |       |                      |
| PG0 | In   | 2,0      | 41    | gray   |       | sink (faucet)        |
| PG1 | In   | 2,1      | 40    | purple |       | shower               |
| PL6 | Out  | 2,6      | 43    | blue   | 6-3   |                      |
| PL7 | Out  | 2,7      | 42    | green  | 6-4   |                      |
| PL4 | Out  | 2,4      | 45    | yellow | 6-1   |                      |
| PL5 | Out  | 2,5      | 44    | orange | 6-2   |                      |
| PL2 | Out  | 2,2      | 47    | red    | 5-3   |                      |
| PL3 | Out  | 2,3      | 46    | brown  | 5-4   |                      |
| PL0 | Out  | 2,0      | 49    | black  | 5-1   |                      |
| PL1 | Out  | 2,1      | 48    | white  | 5-2   |                      |
| PB2 | In   | 1,2      | 51    | gray   |       | free input           |
| PB3 | In   | 1,3      | 50    | purple |       | free input           |
| PB0 | In   | 1,0      | 53    | blue   |       | free input           |
| PB1 | In   | 1,1      | 52    | green  |       | free input           |
|     |      |          | GND   | yellow |       |                      |
|     |      |          | GND   | orange |       |                      |
|     |      |          |       | red    |       |                      |
|     |      |          |       | brown  |       |                      |
