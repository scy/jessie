import machine
from machine import Pin, SDCard, Signal
import microtonic
import os
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
        # Mount the SD card and open a log file for debugging.
        os.mount(SDCard(slot=3, sck=14, miso=12, mosi=13, cs=15), '/sd')
        self.logfile = open('/sd/phlox.log', 'a')
        self.log('Phlox initializing...')

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

        self.log('Initialized.')

    def log(self, msg):
        now = time.localtime()
        msg = ('{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}  {6}\n'.format(
            now[0], now[1], now[2], now[3], now[4], now[5], msg))
        self.logfile.write(msg)
        self.logfile.flush()
        print(msg[:-1])

    def print_log(self):
        with open('/sd/phlox.log', 'r') as log:
            while True:
                line = log.readline()
                if not len(line):
                    break
                print(line.strip())

    def truncate_log(self):
        self.logfile.close()
        self.logfile = open('/sd/phlox.log', 'w')

    def run(self):
        self.check_powercycle()
        # Enable watchdog timer.
        self.sch(Watchdog(60_000).watch)

        self.sch.run_forever()

    def enable_powercycle(self):
        with open('/sd/do_powercycle', 'w') as f:
            pass

    def check_powercycle(self):
        try:
            os.remove('/sd/do_powercycle')
        except OSError:
            print('Powercycle file does not exist.')
            return
        self.sch(self.powercycle_pi)

    async def powercycle_pi(self, sch):
        try:
            self.log('Signalling shutdown to Pi.')
            self.pi.shutdown()
            for s in range(30):
                if not self.pi.is_powered():
                    self.log('Pi powered down after {0}s!'.format(s))
                    break
                await sch.sleep_ms(1_000)
            self.log('Waiting another 10s.')
            await sch.sleep_ms(10_000)
            self.log('Pi power state is {0}.'.format(int(self.pi.is_powered())))
            self.log('Cutting power.')
            self.pi.power_off()
            self.log('Waiting 5s.')
            await sch.sleep_ms(5_000)
            self.log('Pi power state is {0}.'.format(int(self.pi.is_powered())))
            self.log('Turning power back on.')
            self.pi.power_on()
            for s in range(30):
                if self.pi.is_powered():
                    self.log('Pi powered back up after {0}s!'.format(s))
                    break
                await sch.sleep_ms(1_000)
        except Exception as e:
            try:
                self.log('Exception: {0}: {1}'.format(e.__class__.__name__, str(e)))
            except:
                pass
            machine.reset()


class Pi:

    def __init__(self, status_sig, shutdown_sig, power_relay):
        self.status_sig = status_sig
        self.shutdown_sig = shutdown_sig
        self.relay = power_relay

    def is_powered(self):
        return bool(self.status_sig.value())

    def power_off(self):
        self.relay.unset()

    def power_on(self):
        self.relay.set()

    def shutdown(self):
        self.shutdown_sig.on()
        time.sleep_ms(350)
        self.shutdown_sig.off()


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
