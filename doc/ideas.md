## On-Board Computer

There will be a Raspberry Pi 3 continuously running to provide

* routing
* basic network services (DHCP, DNS, NTP)
* statistics
* camera recordings and livecam
* web interface

Although it won’t be built into the dashboard of the car, I can still draw some inspiration from the [Raspberry Pi 2 CarPC project](http://engineering-diy.blogspot.com/).

## Cameras

The van will have a rear view back-up camera, a dashcam and a third camera pointed at the driver’s seat. I’m still figuring out what hardware and software to use.

### Useful Links

* electronic switching between cameras (in German): [on uC.net](https://www.mikrocontroller.net/topic/346004), [in the ElKo](http://www.elektronik-kompendium.de/public/schaerer/anasw2.htm)
* [article about RasPi video capture](https://www.arrow.com/en/research-and-events/articles/pi-bandwidth-with-video)
* [SE question about live streaming from a Pi](https://raspberrypi.stackexchange.com/questions/42881/how-to-stream-low-latency-video-from-the-rpi-to-a-web-browser-in-realtime)
* [German shop that has interesting car cam related hardware](http://www.mobilline24.de/)

## Relays

I’m building a box containing 24 12V/10A relays to control lights, pumps etc.

It will be managed by an Arduino Mega board and communicate with the on-board computer via USB serial. The RasPi itself does not have enough I/O ports (there are also switches, not only the relays), and I want this central part to be autonomous.

You can find the software controlling it at [`src/homn`](../src/homn).

### Useful Links

* [Arduino Mega Specs](https://www.arduino.cc/en/Main/ArduinoBoardMega)
* [AVR libc UART tutorial](https://appelsiini.net/2011/simple-usart-with-avr-libc/)

