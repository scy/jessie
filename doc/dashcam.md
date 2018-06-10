# Dashcam

I'm currently using an iTracker DC-A119S dash cam (with GPS module and polarizing filter) when I'm driving. 
It's pretty much the Viofo A119S v2. 
The image quality is decent, it's got good reviews from the experts, for example on [Car Cam Central](https://www.youtube.com/watch?v=mMvRSV8XLrA), a YouTube channel I can really recommend.

Right now, I'm connecting it to a USB socket on the on-board Raspberry Pi when I start driving and plug it out once I stop, but of course this is supposed to be automated at some point.

## Webcam as dashcam

Before deciding to save the time and just buy something off the shelf, I actually wanted to use a Logitech C920 that should also double as a webcam. 
(I might still come back to that.)

There's a [nice article on how to stream H.264 from it](https://wiki.matthiasbock.net/index.php/Logitech_C920,_streaming_H.264). 
You can control exposure and focus point from V4L2, something like this worked pretty good for me:

```sh
v4l2-ctl -c exposure_auto=1,exposure_auto_priority=0,focus_auto=0
ffmpeg -f v4l2 -framerate 25 -video_size 640x480 -i /dev/video0 -c:v copy -t 00:00:05 output.avi && mplayer -vo fbdev -fs output.avi
```

(Slightly modified based on my notes, not tested.)
