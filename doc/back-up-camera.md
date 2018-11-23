# Back-up camera

What I wanted: 
To be able to stream the image of the (analog) rear camera wirelessly to an Android device.

What I got: 
An ugly hack that works half of the time. 
(But I'll improve on that.)

## Current setup

**This section is a bit outdated.**

_[This image](https://pbs.twimg.com/media/DcXTzYQXcAAc-eb.jpg:large) will have to suffice to give you an impression for the moment, I'll provide a better one soon._

At the back of the van, there's a [Carmedien Rear Light Back-up Camera](https://www.bewado.de/carmedien-rueckfahrkamera-fuer-ducato-jumper-boxer.html). 
It's mounted around the original back light. 
(Cameras that replace the original back light are usually illegal, at least in Germany.) 
The image quality is kinda crappy, but that's the case with all of the analog cameras. 
Its angle of view is very sufficient, you can definitely see where you're going. 
The infrared illumination at night alone is sometimes too weak, but in combination with the white reversing light of the van it's okay.

I have a Huawei MediaPad M5 8" mounted in the front. 
It's connected via USB-C to one of these USB hubs that have a USB-C socket for receiving additional power (to forward it). 
Connected to that hub is a USB video capture dongle. 
Its CVBS RCA connector is connected to the camera's output.

The camera is switched on or off by plugging or unplugging a barrel connector near the glove box. 
This has no effect on the USB capture though: 
If the camera's power is unplugged, the capture card will simply return a blank image.

The particular capture card I've bought from Conrad (Basetech BR116) has a loose connection though: 
When hitting a pothole, it'll disconnect and not come back until you re-plug the hub and restart the app. 
It also doesn't work about 30% of the time when plugging it in, and it's really sensitive to movement. 
And since the symptoms are way worse when it's in its plastic enclosure, I've removed that and now have the naked circuit board hanging around.

The cigarette lighter to USB power gizmos I've tried also don't supply enough power for the hub, the capture card and charging the tablet running on full brightness.

My plan is to replace the capture card with a less sensitive one and beef up the power supply. 
Also, the hub (that's currently dangling on my dashboard) is supposed to be hidden somewhere with just a single USB-C cable running to the tablet.

## What about the streaming?

I've invested several days in finding ways to do that. 
Nothing worked really well. 
Here's what I've tried and what failed about it.

### The Raspberry Pi 3 H.264 hardware encoder

Don't get me started on that one. 
To be clear: It can compress H.264 in PAL resolution without bugging the CPU too much. 
That's nice.

However, the driver comes with literally no documentation and no options. 
I wasn't even able to set the quality when using ffmpeg, and I got the impression that even the bitrate parameter is ignored.

You can try it out yourself: 
A line like

```sh
ffmpeg -y -t 120 -f v4l2 -i /dev/video0 -vcodec h264_omx -b 1024k -pix_fmt yuv420p -an test.mp4
```

should capture some video from the USB capture card. 
Now have fun trying to set any options like `-quality realtime` or something.

### Delay and frame rate when streaming

A back-up camera that has a latency of 5 seconds is pretty much useless. 
That's why most streaming software that's not optimized for latency won't help you.

### Janus

I've had _some_ positive results with using [Janus](https://janus.conf.meetecho.com/) as a streaming proxy, based on [Building a Rasperry Pi 2 WebRTC camera](https://www.rs-online.com/designspark/building-a-raspberry-pi-2-webrtc-camera) and something like this to set it up on Raspbian:

```sh
sudo apt install libmicrohttpd-dev libjansson-dev libnice-dev libssl-dev libsrtp2-dev libsofia-sip-ua-dev libglib2.0-dev libopus-dev libogg-dev libini-config-dev libcollection-dev pkg-config gengetopt libtool automake dh-autoreconf
./configure --disable-websockets --disable-data-channels --disable-rabbitmq --disable-docs --disable-plugin-lua --prefix=/home/pi/janus
```

Janus comes with some demo web pages that you can use to try viewing the stream in the browser, and they worked with Chrome on Android. 
Setting the pixel format to `yuv420p` seems to be really important for some devices though.

This setup gave me 30 frames per second with about 250ms of latency (I've [tweeted about it happily](https://twitter.com/timwohnt/status/982323490031390720)). 
However, it had one serious drawback: 
The stream in the browser would only start if the `ffmpeg` invocation to start streaming into Janus would happen _after_ the page load.

I didn't write down everything I did to make this work, so I don't have the Janus config anymore, but I think I've used a command like this to stream the video into it:

```sh
ffmpeg -y -f v4l2 -i /dev/video0 -quality realtime -error-resilient default -vcodec h264_omx -b:v 512k -vf format=yuv420p -an -f rtp rtp://10.0.0.123:8004
```

Looking back, this was nevertheless the most promising attempt, and I'll likely revisit it at a later time.

### RTSP

My next attempt was using an unknown, but lightweight RTSP server written in Perl: [revmischa/rtsp-server](https://github.com/revmischa/rtsp-server). 
I've used something like this line to stream into it:

```sh
ffmpeg -y -f v4l2 -standard PAL -i /dev/video0 -vcodec h264_omx -b:v 512k -an -f rtsp rtsp://localhost:5545/cam
```

But now I had to choose: 
Using [IP Cam Viewer](https://play.google.com/store/apps/details?id=com.rcreations.ipcamviewe) on Android, I got about 250ms of latency, but only 10 frames per seoncd. 
[VLC for Android](https://play.google.com/store/apps/details?id=org.videolan.vlc), on the other hand, gave me 25fps, but about 1250ms of latency, and even though the latency simply _had_ to be a client issue, I didn't find ways to reduce it further.

And that's when I resorted to directly connecting the camera to the tablet.

### Other resources

Some random pointers that I looked at during my journey and found either useful or interesting:

* A [Raspberry Pi Stack Exchange question](https://raspberrypi.stackexchange.com/questions/42881/how-to-stream-low-latency-video-from-the-rpi-to-a-web-browser-in-realtime) where somebody suggests [sending raw H.264 frames to the browser and decoding them in JavaScript](https://raspberrypi.stackexchange.com/a/58058). They also suggest UV4L on that page, but that's closed source software.
* [Hints for minimizing ffmpeg delay.](https://stackoverflow.com/questions/16658873/how-to-minimize-the-delay-in-a-live-streaming-with-ffmpeg)
* [GStreamer natively supports WebRTC in ≥1.14](http://blog.nirbheek.in/2018/02/gstreamer-webrtc.html) and people are building [tech demos](https://github.com/centricular/gstwebrtc-demos/), but I don't know jack about GStreamer and didn't want to learn yet another technology. Plus, it's very bleeding edge (or at least was back then).
