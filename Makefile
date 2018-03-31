# Default to my test Arduino Duemilanove.
MCU = atmega168

# gcc options.
OPTS = -mmcu=${MCU} -Wall

# Optional additional gcc flags.
FLAGS =

# Directory where Optiboot lives.
OPTIBOOT = thirdparty/optiboot/optiboot/bootloaders/optiboot

.PHONY: clean flash install-deps

# Works on Debian Stretch.
install-deps:
	sudo apt-get install avr-libc avrdude gcc-avr

# For building Optiboot hex files from source.
${OPTIBOOT}/%.hex: ${OPTIBOOT}/optiboot.c
	$(MAKE) -C ${OPTIBOOT} BAUD_RATE=56700 $(patsubst optiboot_%.hex,%,$(notdir $@))

# For copying an Optiboot hex file to the top level directory.
optiboot_%.hex: ${OPTIBOOT}/optiboot_%.hex
	cp thirdparty/optiboot/optiboot/bootloaders/optiboot/$@ .

# I'm using an AVRISP MkII to flash the bootloader (if I need to).
flash-bootloader: optiboot_${MCU}.hex
	sudo avrdude -c avrisp2 -p ${MCU} -P usb -U flash:w:$^ -v

homn.o: homn.c
	avr-gcc ${OPTS} ${FLAGS} -Os -std=c99 -c $^

homn.elf: homn.o
	avr-gcc ${OPTS} -o $@ $^

homn.hex: homn.elf
	avr-objcopy -O ihex $^ $@

flash: homn.hex
	sudo avrdude -c arduino -p ${MCU} -P /dev/ttyUSB0 -U flash:w:$< -v

clean:
	rm -f homn.o homn.elf homn.hex optiboot_*.hex
