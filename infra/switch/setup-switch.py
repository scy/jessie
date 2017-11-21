import argparse, pexpect, subprocess, sys

# There's a server that does NTP, routing, DNS etc.
SERVER_IP = '10.10.1.254'
NTP_SERVER = SERVER_IP
DEF_GATEWAY = SERVER_IP

HOSTNAME = 'tabr' # How the switch should be called.

# Login credentials.
DEFAULT_USER = 'admin'
DEFAULT_PASS = DEFAULT_USER
# The default IP of the switch.
SWITCH_INITIAL_IP = '192.168.0.1'
# The IP it should have when we're done configuring it.
SWITCH_IP = '10.10.1.250'

PROMPT_HOST_REGEX = '(TL-SG2008|{0})'.format(HOSTNAME)
USER_PROMPT = PROMPT_HOST_REGEX + '>'
PRIV_PROMPT = PROMPT_HOST_REGEX + '#'
GLOB_PROMPT = PROMPT_HOST_REGEX + '\(config\)#'
MGMT_VLAN_PROMPT = PROMPT_HOST_REGEX + '\(config-if\)#'

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

def connect_and_config(ip, user, pw):
    # Connect and configure some settings.
    t = pexpect.spawn('telnet', ['-E', ip], timeout=5, encoding='ascii')
    t.logfile_read = sys.stdout # Echo what we receive.
    t.linesep = '\r\n' # Sending linefeeds only is not supported by the switch.
    # Login.
    match = t.expect([pexpect.EOF, 'User:'])
    if match == 0:
        return None
    t.sne(user, 'Password:')
    t.sne(pw, USER_PROMPT)
    t.sne(t.linesep)
    # Change to privileged mode.
    t.sne('enable', PRIV_PROMPT)
    # Change to global configuration mode.
    t.sne('configure', GLOB_PROMPT)
    return t

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--admin-user', dest='user', required=True)
parser.add_argument('-p', '--admin-password', dest='pw', required=True)
args = parser.parse_args()

# Connect to the initial IP.
t = connect_and_config(SWITCH_INITIAL_IP, DEFAULT_USER, DEFAULT_PASS)

if t is None:
    print('Could not connect to the initial IP. This is not necessarily an error; it might already have the correct IP. Trying that.')
else:
    # Create the correct admin user.
    t.sne('user name {0} password {1}'.format(args.user, args.pw)) # passing "type admin secret cipher" resulted in "too many parameters"
    # Set management VLAN and IP address of the switch.
    t.sne('ip management-vlan 1')
    t.sne('interface vlan 1', MGMT_VLAN_PROMPT)
    t.sendline('ip address {0} 255.255.255.0 {1}'.format(SWITCH_IP, DEF_GATEWAY)) # Expecting is useless, the IP has changed.
    # Close the connection.
    t.close()
    t.wait()

# Connect to the correct IP using the correct user and password.
t = connect_and_config(SWITCH_IP, args.user, args.pw)

# Delete the default admin user.
t.sne('no user name {0}'.format(DEFAULT_USER))

# Set basic information.
t.sne('hostname tabr')
t.sne('location Jessie')
t.sne('contact-info -')
t.sne('system-time ntp UTC+01:00 {0} {0} 1'.format(NTP_SERVER))
t.sne('system-time dst predefined Europe')

# While developing, change to interactive mode.
t.logfile_read = None # Seems to have issues with Python 3.
t.interact()
