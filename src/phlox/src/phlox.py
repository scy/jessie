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
                 pi_powered_pin=25, pi_powered_inv=False,
                 pi_heartbeat_pin=26,
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

        # We're using the Perthensis scheduler for multitasking.
        self.sch = sch = Scheduler()

        # Raspberry Pi controller object.
        # It will automatically switch the Pi on when initializing.
        self.pi = Pi(
            Signal(pi_powered_pin, Pin.IN, invert=pi_powered_inv),
            # Signal class inverts the constructor value if invert is True.
            Signal(pi_shutdown_pin, Pin.OUT, invert=pi_shutdown_inv, value=0),
            Signal(pi_heartbeat_pin, Pin.IN, Pin.PULL_DOWN),
            LatchingRelay(pi_set_pin, pi_unset_pin),
            sch, self.log,
        )

        # Default sleep state is "enable everything".
        self.set_sleepstate(0)

        # Initialize Votronic RS485 interface via Arduino MKR 485 shield.
        self.votronic = microtonic.UART(
            votronic_port,
            Signal(votronic_re_pin, Pin.OUT, invert=votronic_re_inv),
            Signal(votronic_de_pin, Pin.OUT, invert=votronic_de_inv),
        )
        self.votronic.on_packet = self.votronic_packet
        sch(self.votronic.read)

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

    def log(self, msg):
        now = time.localtime()
        msg = ('{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}  {6}'.format(
            now[0], now[1], now[2], now[3], now[4], now[5], msg))
        if self.logfile:
            self.logfile.write(msg)
            self.logfile.write('\n')
            self.logfile.flush()
        print(msg)

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
        state = int(state)
        self.sleepstate = state
        self.pi.run_mode = self.pi.RUN_INTERMITTENT if (state & 0x01) \
            else self.pi.RUN_PERMANENT
        # Until there is a stable implementation, we do nothing with that value.

    def run(self):
        # Enable watchdog timer.
        self.sch(Watchdog(60_000).watch)

        if self.wlan is not None:
            self.wlan.enable()

        self.sch.run_forever()


class Pi:
    RUN_PERMANENT = const(0)
    RUN_INTERMITTENT = const(1)

    STATE_UNKNOWN = const(2)
    STATE_PERM_ON = const(3)

    def __init__(self, powered_sig, shutdown_sig, heartbeat_sig,
                 power_relay, scheduler, log=print):
        self.powered_sig = powered_sig
        self.shutdown_sig = shutdown_sig
        self.relay = power_relay
        self.log = log

        self.run_mode = self.RUN_PERMANENT
        self.intermittent_sleep_len = 4 * 60 * 60  # 4 hours
        self.intermittent_report_len = 10 * 60     # 10 minutes
        self.intermittent_wants_power = False
        # TODO: Remove
        self.intermittent_sleep_len = 60
        self.intermittent_report_len = 60
        self._fake_running_req = None
        self._fake_running = True

        scheduler(self._control)
        scheduler(self._intermittent)
        scheduler(self._fake_running_task)

    def is_powered(self):
        return bool(self.powered_sig.value())

    def is_running(self):
        # TODO: This should react to an incoming heartbeat.
        # For now, simply return whether the Pi is powered.
        return (self._fake_running and self.is_powered())  # TODO: Remove
        return self.is_powered()

    def power_off(self):
        self.log('Would cut power to the Pi.')

        # TODO: Remove
        self._fake_running_req = (0, False)
        return

        self.relay.unset()

    def power_on(self):
        self.log('Powering up the Pi.')
        self.relay.set()

        # TODO: Remove
        self._fake_running_req = (20, True)

    def shutdown(self):
        self.log('Would send shutdown request to the Pi.')

        # TODO: Remove
        self._fake_running_req = (10, False)
        return

        self.shutdown_sig.on()
        time.sleep_ms(350)
        self.shutdown_sig.off()

    # TODO: Remove
    async def _fake_running_task(self, sch):
        while True:
            await sch.sleep(1)
            req = self._fake_running_req
            if isinstance(req, tuple):
                self.log('Will fake running {1} in {0}'.format(*req))
                self._fake_running_req = None
                await sch.sleep(req[0])
                self._fake_running = req[1]

    async def _control(self, sch):
        '''Background task that controls power and shutdown of the Pi.'''
        last_state = None
        while True:
            await sch.sleep(1)  # Only tick once a second to save CPU cycles.

            # Determine whether the Pi should be powered or not.
            should_be_powered = \
                (self.run_mode == self.RUN_PERMANENT) \
                or self.intermittent_wants_power

            # If there's no change, do nothing.
            if should_be_powered is last_state:
                continue

            if should_be_powered:
                self.power_on()
                # Wait until it actually did boot up (but with a timeout).
                for _ in range(90):
                    await sch.sleep(1)
                    if self.is_running():
                        break
                # Wait 10 more seconds, just to be sure.
                for _ in range(10):
                    await sch.sleep(1)
            else:
                # It's on purpose that the shutdown procedure doesn't check for
                # mode changes or whether power has been requested again while
                # it's running: The shutdown has to complete cleanly before
                # booting the Pi up again.
                self.log('Starting shutdown procedure.')
                # Send shutdown signal.
                self.shutdown()
                # Wait until it actually did shut down (but with a timeout).
                for _ in range(30):
                    await sch.sleep(1)
                    if not self.is_running():
                        break
                # Wait 5 more seconds for lingering SD card writes etc.
                for _ in range(5):
                    await sch.sleep(1)
                # Kill power.
                self.power_off()

            # Remember the state to check for a difference next iteration.
            last_state = should_be_powered

    async def _intermittent_was_cancelled_while_sleeping_for(
            self, seconds, sch):
        '''Sleep for given time, but abort if no longer in intermittent mode.

        Return True if cancelled by a mode change, False when having slept for
        the whole time specified.'''
        for _ in range(seconds):
            if self.run_mode != self.RUN_INTERMITTENT:
                self.log('Intermittent mode was cancelled while sleeping.')
                return True
            await sch.sleep(1)
        return False

    async def _intermittent(self, sch):
        '''Background task that requests the Pi to turn on/off in intervals.'''
        mode = target_running_state = None
        while True:
            await sch.sleep(1)

            # If the runmode changes, react to that.
            if mode != self.run_mode:
                mode = self.run_mode
                if mode == self.RUN_INTERMITTENT:
                    # Switching to intermittent mode. First, shut down.
                    self.log('Intermittent mode enabled.')
                    target_running_state = self.intermittent_wants_power = False
                else:
                    # Switching to permanent mode, disengage our logic.
                    self.log('Intermittent mode disabled.')
                    # Give other control logic time to ask for Pi power.
                    await sch.sleep(2)
                    self.intermittent_wants_power = False
                    target_running_state = None

            # If intermittent mode is not active, do nothing.
            if mode != self.RUN_INTERMITTENT:
                continue

            # If we're waiting for a running state that has not yet been
            # reached, do nothing.
            if target_running_state is not None \
                    and self.is_running() != target_running_state:
                continue

            # After the Pi has booted up, keep it running for some time.
            if target_running_state:
                self.log('Giving the Pi time to report.')
                if await self._intermittent_was_cancelled_while_sleeping_for(
                        self.intermittent_report_len, sch):
                    continue
                self.log('Report time expired.')
                # Then, switch it off.
                target_running_state = self.intermittent_wants_power = False

            # After the Pi has shut down, wait for a rather long time.
            else:
                self.log('Letting the Pi sleep until report is scheduled.')
                if await self._intermittent_was_cancelled_while_sleeping_for(
                        self.intermittent_sleep_len, sch):
                    continue
                self.log('Time for the next report.')
                # Then, switch it on again.
                target_running_state = self.intermittent_wants_power = True


# TODO: Move to Perthensis.
class LatchingRelay:

    def __init__(self, set_pin_id, unset_pin_id):
        self.set_pin = Pin(set_pin_id, Pin.OUT, value=0)
        self.unset_pin = Pin(unset_pin_id, Pin.OUT, value=0)
        self.state = None

    def _pulse(self, pin):
        pin.value(1)
        time.sleep_ms(10)
        pin.value(0)

    def is_state_known(self):
        return self.state is not None

    def is_set(self):
        return self.state

    def is_unset(self):
        return None if self.state is None else not self.state

    def set(self):
        self._pulse(self.set_pin)
        self.state = True

    def unset(self):
        self._pulse(self.unset_pin)
        self.state = False
