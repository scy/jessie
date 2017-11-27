// Both the Arduino Duemilanove I use for testing and the MEGA I use in production run at 16 MHz.
#define F_CPU 16000000UL
// I'd rather have used 115.2K, but it's not possible with 16 MHz, see <http://wormfood.net/avrbaudcalc.php>.
#define BAUD 57600UL

#include <stdbool.h>
#include <stdio.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>

#ifdef __AVR_ATmega168__
	#define ONBOARD_LED 0b00100000
#else
	#error Unknown MCU type, please define LED port.
#endif

#define ARRAY_SIZE(X) (sizeof(X) / sizeof(*(X)))



struct timer;

typedef void (*callback_t)(struct timer*);

struct timer {
	int        ms;
	callback_t function;
};

bool timer_int_occured = false;



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
	// PORTB = ONBOARD_LED;
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



struct timer timers[] = {
	{0, led_loop},
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
