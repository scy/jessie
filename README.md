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
  
## Port/Pin Mapping

**Note: It's not implemented like this yet, but it will be.**

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

| Port  | Usage     | Notes                                                          |
|:-----:| --------- | -------------------------------------------------------------- |
| **A** | **Out 0** | (labelled _Digital_ 22 to 29)                                  |
| **B** | **In 0**  | (labelled _Digital_ 53 to 50 and _PWM_ 10 to 13)               |
| **C** | **Out 1** | (labelled _Digital_ 37 to 30)                                  |
| **F** | reserved  | (labelled _Analog In_ 0 to 7) reserved for actual analog input |
| **G** | **In 2**  | (low 3 pins only, labelled _Digital_ 41 to 39)                 |
| **K** | **In 1**  | (labelled _Analog In_ 8 to 15)                                 |
| **L** | **Out 2** | (labelled _Digital_ 49 to 42)                                  |

That's 19 inputs and 24 outputs, with 8 pins reserved for analog input (e.g. temperature or water tank).

## How to Flash

Use `make flash`. 
Tested on Debian Stretch. 
You can use `make install-deps` to install avr-libc and avrdude.
