from machine import Pin, Signal
import microtonic
from perthensis import Scheduler, Watchdog
import time


class Phlox:

    def __init__(self,
                 pi_set_pin=5, pi_unset_pin=33,
                 pi_status_pin=25, pi_status_inv=False,
                 pi_shutdown_pin=27, pi_shutdown_inv=True,
                 votronic_port=2,
                 votronic_de_pin=4, votronic_de_inv=False,
                 votronic_re_pin=2, votronic_re_inv=True):
        # We're using the Perthensis scheduler for multitasking.
        self.sch = sch = Scheduler()

        # Raspberry Pi controller object.
        self.pi = Pi(
            Signal(pi_status_pin, Pin.IN, invert=pi_status_inv),
            # Signal class inverts the constructor value if invert is True.
            Signal(pi_shutdown_pin, Pin.OUT, invert=pi_shutdown_inv, value=0),
            LatchingRelay(pi_set_pin, pi_unset_pin),
        )
        self.pi.power_on()  # Power it on when we boot.

        # Initialize Votronic RS485 interface via Arduino MKR 485 shield.
        self.votronic = microtonic.UART(
            votronic_port,
            Signal(votronic_re_pin, Pin.OUT, invert=votronic_re_inv),
            Signal(votronic_de_pin, Pin.OUT, invert=votronic_de_inv),
        )
        sch(self.votronic.read)

    def run(self):
        # Enable watchdog timer.
        self.sch(Watchdog(60_000).watch)

        self.sch.run_forever()


class Pi:

    def __init__(self, status_sig, shutdown_sig, power_relay):
        self.status_sig = status_sig
        self.shutdown_sig = shutdown_sig
        self.relay = power_relay

    def is_powered(self):
        return bool(self.status_sig)

    def power_on(self):
        self.relay.set()


# TODO: Move to Perthensis.
class LatchingRelay:

    def __init__(self, set_pin_id, unset_pin_id):
        self.set_pin = Pin(set_pin_id, Pin.OUT, value=0)
        self.unset_pin = Pin(unset_pin_id, Pin.OUT, value=0)

    def _pulse(self, pin):
        pin.value(1)
        time.sleep_ms(10)
        pin.value(0)

    def set(self):
        self._pulse(self.set_pin)

    def unset(self):
        self._pulse(self.unset_pin)
