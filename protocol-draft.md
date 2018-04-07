# DRAFT

**Note that the contents of this file are from November 2017. Instead of using a custom protocol, I'm thinking about using protobuf instead -- if that doesn't bloat the resulting binary too much.**

## Things Homn Cares About

* Relays. These can be controlled by sending a `RO` (relay open), `RC` (relay close) or `RT` (relay toggle) message to Homn or by pushing a physical switch attached to the board.
* Switches. Changes in their status are published by Homn by `SC` (switch close) or `SO` (switch open) messages.
* Status Heartbeats. Every second, Homn sends a `<3` message dumping the status of all attached switches and relays.

## Message Format

The Homn protocol is ASCII-based. To simplify parsing done in the AVR, messages sent to Homn are always 6 octets in length:

* Message Type (2 octets)
* Space (`0x20`)
* Relay Identifier (2 octets)
* CR (`0x0D`), LF (`0x0A`) or NUL (`0x00`)

Unknown message types or identifiers will be ignored, as will messages not conforming to this format. When Homn encounters CR, LF or NUL, it assumes that the next byte will start a new message. This allows automatic re-synchronizing of the input stream.

Messages sent by Homn can have a variable length:

* Message Type (2 octets)
* Space
* Payload (variable)
* CR, LF _and_ NUL one after another to allow for easy display in a variety of terminals.

The receiver should handle CR, LF or NUL as marking the end of a message.

## Identifiers

Switches and relays have two-byte identifiers. They should be printable ASCII characters. My suggestion is to use a letter-digit combination to group them. Switch and relay names are related: A switch called `L1` will control a relay called `L1`.

In order to allow multiple switches to control the same relay, the input-pin-to-identifier mapping allows for suffixes. For example, the relay `L1`, which controls a room light, can be toggled by the switch `L1a` on one side of the room and the switch `L1b` on the other side. Since Homn only sends these identifiers but never receives them, the incoming message length is still constant.

## Message Types

### To Homn

#### Relay Open/Close (RO, RC)

The named relay will be set to either the open or the closed state.

#### Relay Toggle (RT)

The named relay will be set to the state that it’s currently not in.

### From Homn

#### Switch Open/Close (SO, SC)

This switch changed its state to the one specified. Note that this message will be sent only after it has settled on a state long enough (debouncing).

#### Heartbeat (<3)

These are best explained by example:

    <3 2A R(L1O L2C W1O) S(L1aO L1bO L2C W1O)

The `2A` is a two-byte hexadecimal number counting from `00` to `FF` and wrapping around. It increases by one for each heartbeat sent and enables the receiver to detect when messages were lost.

It is followed by an `R(…)` and an `S(…)` block, listing all known relays and switches and their states (`O` for open, `C` for closed).
