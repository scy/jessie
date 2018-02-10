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
	#define RELAYTEST_PORT PORTD
	#define RELAYTEST_DDR DDRD
	#define SWITCH_A_PORT PORTC
	#define SWITCH_A_DDR  DDRC
	#define SWITCH_A_MASK 0b00111111
	#define SWITCH_A_IN   PINC
	#define RELAY_A_PORT  PORTD
	#define RELAY_A_DDR   DDRD
	#define RELAY_A_MASK  0b11110000
#else
	#error Unknown MCU type, please define LED port.
#endif

// After how many ticks (here: ms) of having the same value should we consider an input stable/debounced? May not be
// larger than 255, since it has to fit into uint8_t.
#define DEBOUNCE_AT 50

#define ARRAY_SIZE(X) (sizeof(X) / sizeof(*(X)))



// Simple mappings of switches to relays.
#define UNMAPPED            0
#define PUSH_BTN            0x40 |
// TGGL_BTNs are not implemented yet.
#define TGGL_BTN            0x80 |
#define SPECIAL             0xc0 |
#define IS_MAPPED(map)      ((map & 0xc0) != 0)
#define MAPPED_PORT(map)    ((map >> 3) & 0x07)
#define MAPPED_PIN(map)     (map & 0x07)
#define PORT_PIN(port, pin) (((port & 0x07) << 3) | (pin & 0x07))
const uint8_t INOUTMAP[1][8] PROGMEM = {
	{ PUSH_BTN PORT_PIN(0,4), TGGL_BTN PORT_PIN(0,5), PUSH_BTN PORT_PIN(0,6), TGGL_BTN PORT_PIN(0,7), UNMAPPED, UNMAPPED, UNMAPPED, UNMAPPED }
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
uint8_t debounce_counter[8];
// Bitmask of pins that are currently switching from one state to the other. 1 means debouncing is active.
uint8_t debounce_active;
// Debounced (i.e. stable) values of the input pins. Please don't write to this unless you're debounce().
uint8_t debounced;



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



void handle_button(const uint8_t in_port, const uint8_t in_pin, const bool high) {
	const uint8_t mapping = pgm_read_byte(&(INOUTMAP[in_port][in_pin]));
	uint8_t outpinmask = (1 << MAPPED_PIN(mapping)) & RELAY_A_MASK;
	RELAY_A_PORT = (((high ? 0 : 1) << MAPPED_PIN(mapping)) & outpinmask) | (RELAY_A_PORT & ~outpinmask);
}



void init_inputs() {
	SWITCH_A_DDR  &= ~SWITCH_A_MASK; // Set DDR for allowed pins.
	SWITCH_A_PORT |=  SWITCH_A_MASK; // Enable pull-ups for input pins.
}

void debounce(struct timer *t) {
	// Make sure the values don't change while we're looping over them.
	uint8_t inputs = SWITCH_A_IN;
	// Create a bitmask of all pins where the measured value is not equal to the one we consider stable.
	uint8_t changed = debounced ^ inputs;
	// Number of the pin. Required for indexing in debounce_counter[].
	uint8_t pin = 0;
	// Bitmask that only selects the current pin, i.e. 1 << pin. Will be set in the for loop below.
	uint8_t mask;

	t->ms = 0; // Call me again at the next tick.
	for (pin = 0; pin < 8; pin++) {
		mask = 1 << pin;
		if ((SWITCH_A_MASK & mask) == 0) continue; // Skip pins that are no inputs.
		if (changed & mask) { // The pin seems to change.
			if (debounce_active & mask) { // This pin is already debouncing, increase the counter.
				if (debounce_counter[pin] >= DEBOUNCE_AT) { // This pin is stable enough.
					// Set its value.
					debounced = (debounced & ~mask) | (inputs & mask);
					// Stop debouncing it.
					debounce_active &= ~mask;
					// Handle the change.
					handle_button(0, pin, (inputs & mask) != 0);
				} else { // Not stable enough, keep counting.
					debounce_counter[pin]++;
				}
			} else { // This pin is not debouncing yet, start the process.
				debounce_active |= mask;
				debounce_counter[pin] = 1;
			}
		} else { // The measured state equals the debounced one.
			if (debounce_active & mask) { // This pin is currently debouncing, but returned to its original state.
				// Stop debouncing it.
				debounce_active &= ~mask;
			}
		}
	}
}



void init_outputs() {
	#ifdef DO_RELAYTEST
		RELAYTEST_DDR |= 0xf0;
		RELAYTEST_PORT = 0x10 | (RELAYTEST_PORT & 0x0f);
	#else
		RELAY_A_DDR  |=  RELAY_A_MASK; // Set DDR for allowed pins.
		RELAY_A_PORT &= ~RELAY_A_MASK; // Set all outputs to off, keeping other pins untouched.
	#endif
}

void relay_test(struct timer *t) {
	uint8_t states = (RELAYTEST_PORT & RELAYTEST_DDR) >> 4;
	states <<= 1;
	if (states > 0x0f) {
		states = 0x01;
	}
	RELAYTEST_PORT = (states << 4) | (RELAYTEST_PORT & 0x0f);
	t->ms = 1000;
}



struct timer timers[] = {
	{0, led_loop},
	{0, debounce},
	#ifdef DO_RELAYTEST
		{1000, relay_test},
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
