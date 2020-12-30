from machine import Pin, Signal
import microtonic
from perthensis import Scheduler
import time


class Phlox:

    def __init__(self, pi_set_pin=5, pi_unset_pin=33,
                 votronic_port=2,
                 votronic_de_pin=4, votronic_de_inv=False,
                 votronic_re_pin=2, votronic_re_inv=True):
        # We're using the Perthensis scheduler for multitasking.
        self.sch = sch = Scheduler()

        # When booting, enable the Pi.
        self.pi = LatchingRelay(pi_set_pin, pi_unset_pin)
        self.pi.set()

        # Initialize Votronic RS485 interface via Arduino MKR 485 shield.
        self.votronic = microtonic.UART(
            votronic_port,
            Signal(votronic_re_pin, Pin.OUT, invert=votronic_re_inv),
            Signal(votronic_de_pin, Pin.OUT, invert=votronic_de_inv),
        )
        sch(self.votronic.read)

    def run(self):
        self.sch.run_forever()


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
