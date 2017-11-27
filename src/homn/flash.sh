#!/bin/sh
mcu='atmega168'
opts="-mmcu=$mcu -Wall"

avr-gcc $opts -Os -std=c99 -c homn.c && \
avr-gcc $opts -o homn.elf homn.o && \
avr-objcopy -O ihex homn.elf homn.hex && \
sudo avrdude -c avrisp2 -p "$mcu" -P usb -U flash:w:homn.hex -v && \
rm homn.o homn.elf homn.hex
