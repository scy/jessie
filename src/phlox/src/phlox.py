import json
import machine
from machine import Pin, SDCard, Signal
import microtonic
import os
from perthensis import MQTTClient, Scheduler, Watchdog, WLANClient
from sys import print_exception
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
        self.logfile = None
        try:
            os.mount(SDCard(slot=3, sck=14, miso=12, mosi=13, cs=15), '/sd')
            self.logfile = open('/sd/phlox.log', 'a')
        except Exception as e:
            print_exception(e)
        self.log('Phlox initializing...')

        # Default sleep state is "enable everything".
        self.set_sleepstate(0)

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
        self.votronic.on_packet = self.votronic_packet
        sch(self.votronic.read)

        # Sleep state background tasks.
        self.intermittent_report_interval = 5 * 60
        self.intermittent_run_duration = 3 * 60
        sch(self._pi_controller)
        sch(self._intermittent_reporter)

        # Prepare WLAN and MQTT.
        self.wlan = self.mqtt = None
        try:
            with open('wlan.json') as f:
                self.wlan = WLANClient(**json.load(f))
        except Exception as e:
            print_exception(e)

        if self.wlan is not None:
            # Add WLAN client to scheduler.
            sch(self.wlan.watch)
            # Set up MQTT.
            self.mqtt = MQTTClient(
                '10.115.106.254', client_id='phlox', keepalive=30)
            self.mqtt.set_last_will('jessie/phlox/up', '0', True)
            self.mqtt.on_connect = self.mqtt_connected
            self.mqtt.set_callback(self.mqtt_msg)
            self.mqtt.subscribe('jessie/sleepstate')
            sch(self.mqtt.watch)

        self.log('Initialized.')

    async def _pi_controller(self, sch):
        prev = None
        while True:
            if self.enable_pi == prev:
                await sch.sleep(1)
                continue
            print('Enable Pi was {0}, is now {1}'.format(prev, self.enable_pi))
            # When we're here, desired sleep state has changed.
            prev = self.enable_pi
            if self.enable_pi:
                self.log('Powering on the Pi')
                self.pi.power_on()
            else:
                self.log('Shutting down the Pi')
                self.pi.shutdown()
                await sch.sleep(30)
                self.log('Cutting power')
                self.pi.power_off()
                await sch.sleep(2)

    async def _intermittent_reporter(self, sch):
        prev_pi = None
        while True:
            await sch.sleep(1)
            # Whether the Pi should be on according to sleepstate.
            pi = not bool(self.sleepstate & 0x01)
            if pi != prev_pi:
                # Sleepstate changed, update countdown.
                countdown = self.intermittent_report_interval
                print('Sleepstate was {0}, is now {1}'.format(prev_pi, pi))
                prev_pi = pi
                continue
            if not pi:
                # Pi should _not_ be on, according to sleepstate.
                countdown -= 1
                print(countdown)
                if countdown <= 0:
                    countdown = self.intermittent_report_interval
                    # Enable the Pi, no matter what sleep state says.
                    self.enable_pi = True
                    # Let it run for some time.
                    await sch.sleep(self.intermittent_run_duration)
                    # Set it to on or off depending on the sleepstate.
                    self.enable_pi = not bool(self.sleepstate & 0x01)

    def log(self, msg):
        now = time.localtime()
        msg = ('{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}  {6}\n'.format(
            now[0], now[1], now[2], now[3], now[4], now[5], msg))
        if self.logfile:
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

    def mqtt_connected(self, mqtt):
        self.mqtt.publish('jessie/phlox/up', '1', True)

    def mqtt_msg(self, topic, msg):
        if topic == b'jessie/sleepstate':
            self.set_sleepstate(int(msg))

    def votronic_packet(self, packet):
        self.mqtt.publish('jessie/' + packet.mqtt_name(), str(packet.value()), True)

    def set_sleepstate(self, state):
        self.sleepstate = state
        self.enable_pi = not bool(state & 0x01)  # Turn Pi off if bit 1 is set

    def run(self):
        # Enable watchdog timer.
        self.sch(Watchdog(60_000).watch)

        if self.wlan is not None:
            self.wlan.enable()

        self.sch.run_forever()


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
