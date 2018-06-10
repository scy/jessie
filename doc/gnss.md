# Global Navigation Satellite System

Because you shouldn't call it "GPS" if it can do GLONASS and GALILEO as well.

## What I wanted

* high quality and precision
* multiple standards (at least GPS, GLONASS and GALILEO)
* untethered dead reckoning, improving precision where satellite coverage is spotty or not available
* time pulse, providing extremely accurate time information (about 5ns)

The u-blox NEO-M8 series of GNSS chips provides all of this. 
If you want something cheaper, without UDR but with support for an external antenna, check out the NavSpark-GL module.

## What I have now

I've bought the Navilock NL-82002U receiver at Jacob. 
It offers everything from my "want" list except for the time pulse (which it can't have, since it's a USB device; however, it does have 10Hz NMEA). 
It also lacks the possibility to attach an external antenna, but this didn't cause any problems yet. 
Setup is plug-and-play.

However, I'm not using it for navigation yet, only to play around using [gpsd](http://www.catb.org/gpsd/). 
The reason for that is that I'm using an Android tablet for navigation, and it has its own GPS(?) receiver.

It seems to be possible to forward its positioning data to Android using geo mocking apps like [MockGeoFix](https://play.google.com/store/apps/details?id=github.luv.mockgeofix) (using Wi-Fi or even USB adb networking), but I didn't build that yet.

## What didn't work

My first idea was getting the USB receiver I've now ended up buying, but at first I decided against it and instead buying the raw module (Navilock 62571 module), since it was cheaper and had a dedicated time pulse pin.
However, I think I've bricked the module I've bought by short-circuiting it somewhere. 
Rest in peace. 
If you want to have it, contact me.

The second plan was to use the Navilock NL-82004P receiver. 
It's placed on the roof by drilling a hole, and it connects via a serial protocol, enabling it to provide a time pulse signal as well. 
But since its enclosure is only certified IPX7 and doesn't guarantee being sealed in heavy rain (wtf…), I've decided against putting it on my roof.

## External antenna

There's a Panorama "Sharkee" multi-technology antenna on the roof, but it's currently not used for navigation, since my receiver doesn't have an antenna input.
