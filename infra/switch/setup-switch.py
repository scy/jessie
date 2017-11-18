import pexpect, subprocess, sys

# There's a server that does NTP, routing, DNS etc.
SERVER_IP = '10.10.1.254'
NTP_SERVER = SERVER_IP

HOSTNAME = 'tabr' # How the switch should be called.

# Login credentials.
USER = 'admin'
PASS = USER
# The default IP of the switch.
SWITCH_INITIAL_IP = '192.168.0.1'

PROMPT_HOST_REGEX = '(TL-SG2008|{0})'.format(HOSTNAME)
USER_PROMPT = PROMPT_HOST_REGEX + '>'
PRIV_PROMPT = PROMPT_HOST_REGEX + '#'
GLOB_PROMPT = PROMPT_HOST_REGEX + '\(config\)#'

'''Send and expect a prompt.'''
def sne(self, to_send, expect=None):
    if expect is not None:
        self.expect_default = expect
    if self.expect is None:
        raise RuntimeError('no default expect regex has been defined yet, please pass an expect parameter')
    self.sendline(to_send)
    self.expect(self.expect_default)

# Enhance Pexpect with our sne method.
pexpect.spawn.sne = sne

t = pexpect.spawn('telnet', ['-E', SWITCH_INITIAL_IP], timeout=5, encoding='ascii')
t.logfile_read = sys.stdout # Echo what we receive.
t.linesep = '\r\n' # Sending linefeeds only is not supported by the switch.

# Login.
t.expect('User:')
t.sne(USER, 'Password:')
t.sne(PASS, USER_PROMPT)
t.sne(t.linesep)

# Change to privileged mode.
t.sne('enable', PRIV_PROMPT)

# Change to global configuration mode.
t.sne('configure', GLOB_PROMPT)

# Set basic information.
t.sne('hostname tabr')
t.sne('location Jessie')
t.sne('contact-info -')
t.sne('system-time ntp UTC+01:00 {0} {0} 1'.format(NTP_SERVER))
t.sne('system-time dst predefined Europe')

# While developing, change to interactive mode.
t.logfile_read = None # Seems to have issues with Python 3.
t.interact()
