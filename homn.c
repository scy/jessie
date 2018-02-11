// Both the Arduino Duemilanove I use for testing and the MEGA I use in production run at 16 MHz.
#define F_CPU 16000000UL
// I'd rather have used 115.2K, but it's not possible with 16 MHz, see <http://wormfood.net/avrbaudcalc.php>.
#define BAUD 57600UL

#include <stdbool.h>
#include <stdio.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <avr/sleep.h>

#ifdef __AVR_ATmega168__
	#define ONBOARD_LED 0b00100000

	#define NUM_INPORTS 2
	#define MAX_OUTPORT 1

	#define IN0_PORT PORTC
	#define IN0_DDR  DDRC
	#define IN0_MASK 0b00111111
	#define IN0_VAL  PINC

	#define IN1_PORT PORTB
	#define IN1_DDR  DDRB
	#define IN1_MASK 0b00000001
	#define IN1_VAL  PINB

	#define OUT0_PORT PORTD
	#define OUT0_DDR  DDRD
	#define OUT0_MASK 0b11111100

	#define OUT1_PORT PORTB
	#define OUT1_DDR  DDRB
	#define OUT1_MASK 0b00000110
#else
	#error Unknown MCU type, please define LED port.
#endif

// After how many ticks (here: ms) of having the same value should we consider an input stable/debounced? May not be
// larger than 255, since it has to fit into uint8_t.
#define DEBOUNCE_AT 50

#define ARRAY_SIZE(X) (sizeof(X) / sizeof(*(X)))



// Simple mappings of switches to relays.
#define UNMAPPED            0
#define PUSH_BTN            0x40
#define TGGL_BTN            0x80
// "Special" buttons are not implemented yet.
#define SPECIAL             0xc0
#define IS_MAPPED(map)      ((map & 0xc0) != 0)
#define MAPPED_TYPE(map)    (map & 0xc0)
#define MAPPED_PORT(map)    ((map >> 3) & 0x07)
#define MAPPED_PIN(map)     (map & 0x07)
#define PORT_PIN(port, pin) (((port & 0x07) << 3) | (pin & 0x07))
const uint8_t INOUTMAP[2][8] PROGMEM = {
	{ PUSH_BTN | PORT_PIN(0,4),   TGGL_BTN | PORT_PIN(0,7),   PUSH_BTN | PORT_PIN(1,1),   TGGL_BTN | PORT_PIN(0,7),   UNMAPPED,   UNMAPPED,   UNMAPPED,   UNMAPPED },
	{ PUSH_BTN | PORT_PIN(1,1),   UNMAPPED,                   UNMAPPED,                   UNMAPPED,                   UNMAPPED,   UNMAPPED,   UNMAPPED,   UNMAPPED },
};



struct timer;

typedef void (*callback_t)(struct timer*);

struct timer {
	int        ms;
	callback_t function;
};

bool timer_int_occured = false;



// Since how many ticks does the input pin return the same state? When this reaches DEBOUNCE_AT, the state is considered
// stable. [0] is pin 0 of a port, [1] is pin 1 and so on.
uint8_t debounce_counter[NUM_INPORTS][8];
// Bitmask of pins that are currently switching from one state to the other. 1 means debouncing is active.
uint8_t debounce_active[NUM_INPORTS];
// Debounced (i.e. stable) values of the input pins. Please don't write to this unless you're debounce().
uint8_t debounced[NUM_INPORTS];



void uart_putc(char c) {
	loop_until_bit_is_set(UCSR0A, UDRE0);
	UDR0 = c;
}

FILE uart_out_buf = FDEV_SETUP_STREAM(uart_putc, NULL, _FDEV_SETUP_WRITE);

void uart_init() {
	// Baud rate setup.
	#include <util/setbaud.h>
	UBRR0 = UBRR_VALUE;
	#if USE_2X
		UCSR0A |= _BV(U2X0);
	#else
		UCSR0A &= ~_BV(U2X0);
	#endif
	// Enable RX and TX.
	UCSR0B = /* (1<<RXCIE) | (1<<TXCIE) | (1<<UDRIE) | */ _BV(RXEN0) | _BV(TXEN0);
	UCSR0C = _BV(UCSZ01) | _BV(UCSZ00);
	stdout = &uart_out_buf;
}



struct led_animation_step {
	bool         active;
	unsigned int duration;
};

const struct led_animation_step led_animation[] = {
	{true,   50},
	{false, 100},
	{true,  100},
	{false, 900},
};

void init_led() {
	// Set the LED pin to be an output.
	DDRB |= ONBOARD_LED;
}

void toggle_led() {
	PORTB ^= ONBOARD_LED; // Toggle the LED.
}

void led_loop(struct timer *t) {
	static uint8_t step = 0;
	if (led_animation[step].active) {
		PORTB |= ONBOARD_LED;
	} else {
		PORTB &= ~ONBOARD_LED;
	}
	t->ms = led_animation[step].duration;
	if (step < (ARRAY_SIZE(led_animation) - 1)) {
		step++;
	} else {
		step = 0;
	}
}



bool toggle_out_pin(const uint8_t out_port, const uint8_t out_pin) {
	// Always make sure to apply the OUTn_MASK so that we can't write to a non-output pin.
	switch (out_port) {
		case 0:
			if (((1 << out_pin) & OUT0_MASK) == 0) { return false; }
			OUT0_PORT ^= 1 << out_pin;
			break;
		case 1:
			if (((1 << out_pin) & OUT1_MASK) == 0) { return false; }
			OUT1_PORT ^= 1 << out_pin;
			break;
	}
	return true;
}

bool set_out_pin(const uint8_t out_port, const uint8_t out_pin, const bool enable) {
	// Always make sure to apply the OUTn_MASK so that we can't write to a non-output pin.
	switch (out_port) {
		case 0:
			if (((1 << out_pin) & OUT0_MASK) == 0) { return false; }
			OUT0_PORT = ((enable ? 1 : 0) << out_pin) | (OUT0_PORT & ~OUT0_MASK);
			break;
		case 1:
			if (((1 << out_pin) & OUT1_MASK) == 0) { return false; }
			OUT1_PORT = ((enable ? 1 : 0) << out_pin) | (OUT1_PORT & ~OUT1_MASK);
			break;
	}
	return true;
}

void handle_button(const uint8_t in_port, const uint8_t in_pin, const bool high) {
	// Get the mapping definition for this button.
	const uint8_t mapping = pgm_read_byte(&(INOUTMAP[in_port][in_pin]));

	switch (MAPPED_TYPE(mapping)) {
		case PUSH_BTN: // While pushed, turn on. Turn off when let go.
			set_out_pin(MAPPED_PORT(mapping), MAPPED_PIN(mapping), !high);
			break;
		case TGGL_BTN: // When pushed, toggle the state of the output pin. Do nothing when let go.
			if (!high) {
				toggle_out_pin(MAPPED_PORT(mapping), MAPPED_PIN(mapping));
			}
			break;
	}
}



void init_inputs() {
	IN0_DDR  &= ~IN0_MASK; // Set DDR for allowed pins.
	IN0_PORT |=  IN0_MASK; // Enable pull-ups for input pins.
	// Same for other ports.
	IN1_DDR  &= ~IN1_MASK;
	IN1_PORT |=  IN1_MASK;
}

void debounce(const uint8_t port, const uint8_t port_mask, const uint8_t states) {
	// Create a bitmask of all pins where the measured value is not equal to the one we consider stable.
	uint8_t changed = debounced[port] ^ states;
	// Number of the pin. Required for indexing in debounce_counter[].
	uint8_t pin = 0;
	// Bitmask that only selects the current pin, i.e. 1 << pin. Will be set in the for loop below.
	uint8_t mask;

	for (pin = 0; pin < 8; pin++) {
		mask = 1 << pin;
		if ((port_mask & mask) == 0) continue; // Skip pins that are no inputs.
		if (changed & mask) { // The pin seems to change.
			if (debounce_active[port] & mask) { // This pin is already debouncing, increase the counter.
				if (debounce_counter[port][pin] >= DEBOUNCE_AT) { // This pin is stable enough.
					// Set its value.
					debounced[port] = (debounced[port] & ~mask) | (states & mask);
					// Stop debouncing it.
					debounce_active[port] &= ~mask;
					// Handle the change.
					handle_button(port, pin, (states & mask) != 0);
				} else { // Not stable enough, keep counting.
					debounce_counter[port][pin]++;
				}
			} else { // This pin is not debouncing yet, start the process.
				debounce_active[port] |= mask;
				debounce_counter[port][pin] = 1;
			}
		} else { // The measured state equals the debounced one.
			if (debounce_active[port] & mask) { // This pin is currently debouncing, but returned to its original state.
				// Stop debouncing it.
				debounce_active[port] &= ~mask;
			}
		}
	}
}

void scan_inputs(struct timer *t) {
	debounce(0, IN0_MASK, IN0_VAL);
	debounce(1, IN1_MASK, IN1_VAL);
	t->ms = 0; // Call me again at the next tick.
}



void init_outputs() {
	OUT0_DDR  |=  OUT0_MASK; // Set DDR for allowed pins.
	OUT0_PORT &= ~OUT0_MASK; // Set all outputs to off, keeping other pins untouched.
	// Same for other ports.
	OUT1_DDR  |=  OUT1_MASK;
	OUT1_PORT &= ~OUT1_MASK;
}

void output_test(struct timer *t) {
	static uint8_t port = MAX_OUTPORT + 1; // Will automatically be fixed on the first iteration.
	static uint8_t pin  = 0;

	// Disable the pin that was active before. If that was not a valid pin, nothing will happen.
	toggle_out_pin(port, pin);

	// Go to the next pin. If we are done with the pins on this port, go to pin 0 of the next port instead.
	if (++pin > 7) {
		port++;
		pin = 0;
	}

	// If we are beyond the last valid output port, start again from the beginning.
	if (port > MAX_OUTPORT) {
		port = pin = 0;
	}

	// Enable the new pin and, depending on whether that was a valid pin, come back in a second or instantly.
	t->ms = toggle_out_pin(port, pin) ? 1000 : 0;
}



struct timer timers[] = {
	{0, led_loop},
	#ifdef DO_OUTPUTTEST
		{1000, output_test},
	#else
		{0, scan_inputs},
	#endif
};

void init_timer() {
	// We use timer 0 to generate an interrupt every 1ms. For this to work, the prescaler will be set to 64 (250 kHz).
	// The CTC feature will be used to interrupt after counting to 250, not to 255.
	TCCR0A = _BV(WGM01); // CTC mode
	TCCR0B = _BV(CS00) | _BV(CS01); // prescale 64
	OCR0A = (F_CPU / 64 / 1000) - 1; // Comparison value. Calculation will be done by the compiler (I guess).
	TIMSK0 |= _BV(OCIE0A); // interrupt on compare match for OCR0A
}

ISR(TIMER0_COMPA_vect) {
	timer_int_occured = true;
}

void handle_timers() {
	for (uint8_t i = 0; i < ARRAY_SIZE(timers); i++) {
		struct timer *t = &timers[i];
		if (t->ms == 0) {
			t->ms = -1;
			t->function(t);
		} else if (t->ms > 0) {
			t->ms--;
		}
	}
}



int main() {
	init_led();
	init_inputs();
	init_outputs();
	init_timer();
	sei();
	set_sleep_mode(SLEEP_MODE_IDLE);
	while(true) {
		sleep_mode(); // This program is completely interrupt driven.
		if (timer_int_occured) {
			timer_int_occured = false;
			handle_timers();
		}
	}
}
