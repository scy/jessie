# Default to my test Arduino Duemilanove.
MCU = atmega168

# gcc options.
OPTS = -mmcu=${MCU} -Wall

.PHONY: clean flash install-deps

# Works on Debian Stretch.
install-deps:
	sudo apt-get install avr-libc avrdude gcc-avr

homn.o: homn.c
	avr-gcc ${OPTS} -Os -std=c99 -c $^

homn.elf: homn.o
	avr-gcc ${OPTS} -o $@ $^

homn.hex: homn.elf
	avr-objcopy -O ihex $^ $@

flash: homn.hex
	sudo avrdude -c avrisp2 -p ${MCU} -P usb -U flash:w:$< -v

clean:
	rm -f homn.o homn.elf homn.hex
