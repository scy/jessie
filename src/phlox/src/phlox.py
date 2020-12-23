from machine import Pin
import time


class Phlox:

    def __init__(self, pi_set_pin=5, pi_unset_pin=33):
        # When booting, enable the Pi.
        self.pi = LatchingRelay(pi_set_pin, pi_unset_pin)
        self.pi.set()


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
