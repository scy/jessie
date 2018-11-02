# Sensors

I am planning to deploy a number of sensors (mostly temperature) in the van.
Currently, I have not decided on a technology.
This page lists the possible candidates and their pros and cons.

## The hub

As far as I'm concerned, the sensor data can end up either on the always-running Raspberry Pi above the front seats, or on the (also always-running) Arduino Mega behind the driver's seat.
I haven't yet decided on a software suite to use, but [Home Assistant](https://www.home-assistant.io/) seems to be quite popular.

## Wired sensors

Simply attaching a DHT22 sensor to one end of a long wire and then pulling that wire through the van would possibly be an option.
However, since these sensors have no security impact and since I don't want to pull a wire from the front of the car to the back for aesthetic reasons (and because it's a lot of work), I don't consider this option.

## Power consumption

So the sensors need to be wireless.
And even though getting some kind of 12V power to each of the sensors _might_ be easier than a data cable, it's still probably a hassle.
Also, the van itself doesn't have unlimited power to supply them either.

Which means the sensors need to run on batteries.
And of course I don't want to replace or recharge the batteries every week.

## Espressif-based systems

When googling _"inexpensive wireless temperature sensor"_, the most interesting result was a Gearbest page with a [bundle consisting of an ESP8266 module and a matching DHT11 module called ESP-01S DHT11](https://www.gearbest.com/other-accessories/pp_1176241.html).
It looked compact and interesting, and it even could run on 12V power.
(I hadn't settled on batteries yet.)
But then I went down the rabbit hole which is power consumption of auxiliary components and deep sleep.

First, [linear voltage regulators leak power](https://www.sparkfun.com/tutorials/217).
The more input/output difference (and the more power required on the output), the more heat they generate from the precious electrons in your power source.
That was when I thought "okay, so maybe I'll use batteries instead of 12V".
Which brought me to the [ESPmobe](https://hackaday.io/project/20588-espmobe-battery-powered-esp8266-iot-sensor), an (unfinished) Hackaday project that discusses [running without a voltage regulator and which batteries to use](https://hackaday.io/project/20588-espmobe-battery-powered-esp8266-iot-sensor/log/60267-the-batteries) in detail.
They're using two Eneloop (NiMH) batteries and a [Wemos D1 mini](https://wiki.wemos.cc/products:d1:d1_mini) board.

In addition to the ESP8266, there's also the ESP8285, which has internal flash memory instead of the external flash chips the ESP8266 modules usually contain.
I've found a good [German article about both of these chips](http://stefanfrings.de/esp8266/) with lots of background information and tricks.
They also mention the [NodeMCU](https://en.wikipedia.org/wiki/NodeMCU) family of development boards, so I began to look into these.

So I googled _"nodemcu battery"_ and … well, basically, you don't.
At least not with a normal, commercial NodeMCU board.
There's this [article about running NodeMCU on a battery](https://tinker.yeoman.com.au/2016/05/29/running-nodemcu-on-a-battery-esp8266-low-power-consumption-revisited/), and it's like "yeah, sure, just provide 3.3V via an external regulator, desolder the on-board one, cut off the USB-UART chip, solder a switch or jumper to the µC itself" and so on.
Every single one of these steps alone would be a reason for me not to choose NodeMCU.
So, nope.
Not gonna happen.

(Also, apparently whenever you want to use the deep sleep mode on the ESP8266 or ESP8285 (and you _want_ that when on battery), you're required to add additional wiring from one particular pin to the reset pin that will actually _reset_ your controller once the sleep timer is up.
I've heard that this is a design bug in the chip.
Well, it certainly is inconvenient.)

What else is there?

## Non-WiFi 2.4 GHz devices

One of the articles from my original Google search was [Mapping Household Temperature Flow with Cheap Sensors](https://www.hackster.io/humblehacker/mapping-household-temperature-flow-with-cheap-sensors-6a36c3), and it mentioned the [nRF24L01](https://www.nordicsemi.com/eng/Products/2.4GHz-RF/nRF24L01) line of RF modules.
These are supposedly low-power, but since they don't access WiFi directly, they need some kind of a gateway.
Also, the L01 is _just_ an RF module, it needs to be controlled by a separate microcontroller.

Nordic Semiconductor, their manufacturer, lists them as deprecated though, but among their replacement suggestions is the [nRF24LE1](https://www.nordicsemi.com/eng/Products/2.4GHz-RF/nRF24LE1), which includes a 8-bit CPU and some memory.
Sounds good, right?
Well, yeah, but apparently nobody uses these.
[According to German community site mikrocontroller.net](https://www.mikrocontroller.net/topic/348698), this is because the CPU is outdated and there's not a lot of development tools (or libraries!) available.

## ESP32

So I revisited the ESP8266 modules.
There are a lot of them, for example [Adafruit's Feather HUZZAH](https://www.adafruit.com/product/2821) or the [Wemos D1 mini](https://wiki.wemos.cc/products:d1:d1_mini).
They come in different sizes and with slightly different features, but none of them seem really optimized for power consumption.
But then, when browsing YouTube videos for battery-powered sensor boards, I came across this [Comparison of 10 ESP32 Battery powered Boards](https://youtu.be/-769_YIeGmI), and the "current on deep sleep" values in [the comparison table](https://docs.google.com/spreadsheets/d/1Mu-bNwpnkiNUiM7f2dx8-gPnIAFMibsC2hMlWhIHbPQ/edit) sounded promising.
Also, when you're using an ESP32, you don't need to do these nasty "additional reset wire" hacks for deep sleep anymore, you can just buy a commercial board and be done.

Right now, I'm seriously considering using either [Wemos LOLIN32](https://wiki.wemos.cc/products:lolin32:lolin32) (they were measured using just 125 µA in deep sleep, but are listed as "retired" on the Wemos website) or [TTGO ESP32](http://s.click.aliexpress.com/e/EUrFMjA) boards.
The latter use a bit more power in deep sleep (172 µA), but are smaller.
There's also the [FireBeetle](https://www.dfrobot.com/product-1590.html) which uses just 53 µA, but according to that table, it's using the "revision 0" version of the ESP32, while all other boards use revision 1.

I also found a video about [powering the LOLIN32 using 3.3 V](https://youtu.be/k_7eZ5ZpSMY) and one that talks about [powering 3.3 V electronics using batteries in general](https://youtu.be/heD1zw3bMhw).

None of these boards were available to me short-term (same week) though, and they are about 15 € each, so I kept looking for alternatives.

## Xiaomi

A suggestion I got on Twitter was to use cheap Xiaomi Aqara ZigBee temperature sensor in combination with a custom ZigBee receiver instead of Xiaomi's original smart home hub.
There's a German [article](https://forum.fhem.de/index.php?topic=84790.0) and [video](https://youtu.be/F89oYY29rJ8) explaining the procedure.
However, it involves having to buy (or borrow) a debugging/flashing device for the ZigBee dongle they use.

An alternative to this (at least in and around Germany) seems to be the [ConBee](https://www.dresden-elektronik.de/conbee/) by Dresden Elektronik.
I haven't read up on it thoroughly, but it basically seems to be a ZigBee dongle with a different firmware.
Dresden Elektronik also provides [deCONZ](https://www.dresden-elektronik.de/funktechnik/products/software/pc/deconz/), a software to manage that ZigBee network.
If I understood it correctly, you use it to pair the Xiaomi (and other) sensors into your network.
You're then able to use deCONZ to access the sensor data, or integrate it via an [API](http://dresden-elektronik.github.io/deconz-rest-doc/) into whatever smart home software you're using.

According to quite some reports, deCONZ isn't the best or most stable software, though.
They are working to fix it, but at least at the time of writing it seems to require an X server (i.e. no headless installs) and root access to work.
As long as deCONZ isn't improved, I'd prefer to stay away from this solution.

## FS20

My temporary workaround will be to resurrect some [FS20](https://www.elv.de/fs20-funkschaltsystem.html) (German link) hardware that I still have.
It's an [SRD860](https://en.wikipedia.org/wiki/Short-range_device#SRD860) based "home automation" system from back in the days.
The duty cycle limitation means that there are minutes between each sensor update and delivery isn't guaranteed (also, the protocol is insecure), but the sensors run for years on two AA batteries.

You need a [CUL](https://wiki.fhem.de/wiki/CUL) (German link), basically a CC1101 receiver, if you want to interface with it using USB, or a commercial device.
Thankfully, I have bought a FHZ 1000 PC interface years ago, and apparently there are ways to integrate this into Home Assistant, for example [Luzifer/culmqtt](https://github.com/Luzifer/culmqtt).
I'll look into it.

## Honorary mentions

* [How to Run Your ESP8266 for Years on a Battery](https://openhomeautomation.net/esp8266-battery) provides a good overview on what has to be done to tune the ESP for power saving. It recommends the [SparkFun ESP8266 Thing](https://www.sparkfun.com/products/13231), because it has little features that you don't want anyway.
* [Matthias mentioned](https://twitter.com/mattsches/status/1058068949584265216) his [ESP32 based sensor](https://blog.sperrobjekt.de/content/1000514-BME680-Sensor-auf-ESP32-mit-esphomelib-konfigurieren.html) (German), but the most interesting part of that article for me was that he used [esphomeyaml](https://esphomelib.com/esphomeyaml/index.html) to automatically generate firmware for his sensors. Write a YAML file and be done. Nice!
* There's the [TinyTX](https://nathan.chantrell.net/tinytx-wireless-sensor/) project by Nathan Chantrell, using ATtiny84 µCs and RFM12 radio chips, and [a German project](http://roxxs.org/index.php/hausautomatisierung/batteriebetriebene-funk-sensoren/) loosely based on it. However, I'm too lazy for custom PCBs or soldering lots of components by hand.
* You could build your own ZigBee sensors as well, for example using [MOD-ZIGBEE](https://www.olimex.com/Products/Modules/RF/MOD-ZIGBEE/) modules.
* DHT11 sensors seem to be of low accuracy, while [DHT22 sensors reportedly have problems with deep sleep](https://tzapu.com/minimalist-battery-powered-esp8266-wifi-temperature-logger/).
* The [MySensors](https://www.mysensors.org/) community provides howtos, instructions and tips for setting up a DIY IoT home. (I find their website confusing though.)
* Thanks to everyone in [the Twitter thread](https://twitter.com/scy/status/1057962543489187840), and sorry that I couldn't mention each of you individually.
