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

## Bugs and Quirks

* It might behave unexpectedly if you configure it to have no input or no output port.
* Because of [optiboot#177](https://github.com/Optiboot/optiboot/issues/177), building `optiboot_atmega1280.hex` from source might not be possible easily on your system. 
  Luckily, that file is provided as a complete binary in the Optiboot repo, so we can simply copy it. 
  The problem with compiling seems to be the EEPROM writing; you should be able to build it if you _don't_ enable `-DBIGBOOT`, but the Optiboot makefile won't let you (`CFLAGS` is overridden, `DEFS` (where you could do `-UBIGBOOT`) comes _before_ the builtin `-DBIGBOOT`).
  
## How to Flash

Use `make clean flash` to flash it to the Duemilanove. 
Use `make MCU=atmega1280 clean flash` to flash it to the Mega. 
If you want to flash the output test routine instead of the normal button behavior, use `make FLAGS=-DDO_OUTPUTTEST clean flash` (combined with `MCU=atmega1280` for the Mega).

Tested on Debian Stretch. 
You can use `make install-deps` to install avr-libc and avrdude.

## Hardware Specs and Limits

I'm using six C-Control relay boards (Conrad SKU 1488848) with 4 relays on each one. 
These can run on 12V DC, the Arduinos as well. 
Each relay can switch up to 30V DC or 250V AC, both up to 10A, and each board eats up to 20 mA power.

Since I didn't specify my needs well enough to the company that built the van's interior, the physical push buttons in my furniture supply 5V when pushed instead of connecting to ground, i.e. they are active high. 
This keeps me from using the AVR's internal pull-up resistors; I had to build external pull-downs instead. 
The software supports both, depending on whether the constant `ACTIVE_HIGH` is defined when building. 
The Makefile defines it by default.

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

| Pin | Type | Internal | Label | Color  | Relay | Connected To                       |
| --- | ---- | -------- | ----- | ------ | ----- | ---------------------------------- |
|     |      |          |       | black  |       |                                    |
|     |      |          |       | white  |       |                                    |
|     |      |          | 5V    | gray   |       |                                    |
|     |      |          | 5V    | purple |       |                                    |
| PA1 | Out  | 0,1      | 23    | blue   | 1-2   | drinking water pump                |
| PA0 | Out  | 0,0      | 22    | green  | 1-1   | **planned:** main water pump       |
| PA3 | Out  | 0,3      | 25    | yellow | 1-4   |                                    |
| PA2 | Out  | 0,2      | 24    | orange | 1-3   |                                    |
| PA5 | Out  | 0,5      | 27    | red    | 2-2   | 2: foot light bed                  |
| PA4 | Out  | 0,4      | 26    | brown  | 2-1   | 1: ceiling light back              |
| PA7 | Out  | 0,7      | 29    | black  | 2-4   | 4: kitchen light                   |
| PA6 | Out  | 0,6      | 28    | white  | 2-3   | 3: ceiling mood light kitchen/desk |
| PC6 | Out  | 1,6      | 31    | gray   | 4-3   | 7: ceiling mood light bed          |
| PC7 | Out  | 1,7      | 30    | purple | 4-4   | 8: ceiling light front             |
| PC4 | Out  | 1,4      | 33    | blue   | 4-1   | 5: head light bed                  |
| PC5 | Out  | 1,5      | 32    | green  | 4-2   | 6: bathroom light                  |
| PC2 | Out  | 1,2      | 35    | yellow | 3-3   |                                    |
| PC3 | Out  | 1,3      | 34    | orange | 3-4   |                                    |
| PC0 | Out  | 1,0      | 37    | red    | 3-1   |                                    |
| PC1 | Out  | 1,1      | 36    | brown  | 3-2   |                                    |
| PG2 | In   | 2,2      | 39    | black  |       | see *Input Ribbon Cable*           |
| PD7 |      |          | 38    | white  |       |                                    |
| PG0 | In   | 2,0      | 41    | gray   |       | see *Input Ribbon Cable*           |
| PG1 | In   | 2,1      | 40    | purple |       | see *Input Ribbon Cable*           |
| PL6 | Out  | 2,6      | 43    | blue   | 6-3   |                                    |
| PL7 | Out  | 2,7      | 42    | green  | 6-4   |                                    |
| PL4 | Out  | 2,4      | 45    | yellow | 6-1   |                                    |
| PL5 | Out  | 2,5      | 44    | orange | 6-2   |                                    |
| PL2 | Out  | 2,2      | 47    | red    | 5-3   | 11: wall light (bathroom door)     |
| PL3 | Out  | 2,3      | 46    | brown  | 5-4   | 12: step light                     |
| PL0 | Out  | 2,0      | 49    | black  | 5-1   | 9: desk light                      |
| PL1 | Out  | 2,1      | 48    | white  | 5-2   | 10: door light                     |
| PB2 | In   | 1,2      | 51    | gray   |       | see *Input Ribbon Cable*           |
| PB3 | In   | 1,3      | 50    | purple |       | see *Input Ribbon Cable*           |
| PB0 | In   | 1,0      | 53    | blue   |       | see *Input Ribbon Cable*           |
| PB1 | In   | 1,1      | 52    | green  |       | see *Input Ribbon Cable*           |
|     |      |          | GND   | yellow |       | GND brown (input ribbon cable)     |
|     |      |          | GND   | orange |       | GND black (input ribbon cable)     |
|     |      |          |       | red    |       |                                    |
|     |      |          |       | brown  |       |                                    |

#### Input Ribbon Cable

There's a second box that contains screw terminals for input push buttons and the like. It is connected to the relay box via a 20-wire ribbon cable. Each of the wires corresponds to one screw terminal, with the exception of the first and the last, which both carry ground. The following table lists the connections in the ribbon cable's order.

Some wires of the ribbon cable are directly connected to the Arduino's ports (PK), others connect to the big Arduino cable described in the previous section. For those, the corresponding wire color is listed under *Arduino cable color*. *Label* refers to the Arduino pin labeling, *Button* to the push button numbering of the choc block where the light buttons terminate.

| Pin | Internal | Label        | Color  | Arduino cable color | Button | Connected To (button or pin) | Function                                                  |
| --- | -------- | ------------ | ------ | ------------------- | ------ | ---------------------------- | --------------------------------------------------------- |
|     |          | GND          | black  | orange              |        | GND                          |                                                           |
| PK7 | 0,7      | Analog In 15 | white  | -                   | 8      | bed innermost                | **planned:** toggle between bed head, bed foot, both, off |
| PK6 | 0,6      | Analog In 14 | gray   | -                   | 7      | bed center                   | ceiling mood bed                                          |
| PK5 | 0,5      | Analog In 13 | purple | -                   | 6      | bed foot end                 | **planned:** global toggle                                |
| PK4 | 0,4      | Analog In 12 | blue   | -                   | 5      | desk innermost               | ceiling mood door (**planned:** and step)                 |
| PK3 | 0,3      | Analog In 11 | green  | -                   | 4      | bathroom                     | bathroom light                                            |
| PK2 | 0,2      | Analog In 10 | yellow | -                   | 3      | kitchen center               | ceiling back                                              |
| PK1 | 0,1      | Analog In 9  | orange | -                   | 2      | sliding door                 | **planned:** global toggle                                |
| PK0 | 0,0      | Analog In 8  | red    | -                   | 1      | desk center                  | ceiling front                                             |
| PB3 | 1,3      | Digital 50   | brown  | purple              | 12     | desk outermost               | desk light                                                |
| PB2 | 1,2      | Digital 51   | black  | gray                | 11     | bed outermost                | alarm system                                              |
| PB1 | 1,1      | Digital 52   | white  | green               | 10     | kitchen innermost            | kitchen light                                             |
| PB0 | 1,0      | Digital 53   | gray   | blue                | 9      | kitchen outermost            | ceiling mood kitchen/desk (**planned:** and door)         |
| PB4 | 1,4      | PWM 10       | purple | -                   |        |                              |                                                           |
| PB5 | 1,5      | PWM 11       | blue   | -                   |        |                              |                                                           |
| PB6 | 1,6      | PWM 12       | green  | -                   |        |                              |                                                           |
| PG0 | 2,0      | Digital 41   | yellow | gray                |        | **planned:** sink (faucet)   |                                                           |
| PG1 | 2,1      | Digital 40   | orange | purple              |        | **planned:** shower          |                                                           |
| PG2 | 2,2      | Digital 39   | red    | black               |        | sink (foot switch)           | drinking water pump                                       |
|     |          | GND          | brown  | yellow              |        | GND                          |                                                           |
