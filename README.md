# Jessie

In 2018, [@scy](https://github.com/scy) will move into a custom-built Fiat Ducator campervan and live in it.
This repository consists of documentation about the van and its systems, about plans that I've made and plans that I've already rejected, but it also contains software that’s used for controlling various parts of the van.

You can also check out [my (German) YouTube channel](https://www.youtube.com/c/timwohnt%C3%BCberall).
I haven't updated it for far too long though; more recent updates can be found on my Twitter account [@timwohnt](https://twitter.com/timwohnt).

## Contents

A high-level overview of what you can find in here:

* **[data](data):** manually maintained lists like fuel usage and money spent
  * **[accessories.csv](data/accessories.csv), [automation.csv](data/automation.csv), [radio.csv](data/radio.csv):** things I've bought, and for what price
  * **[fuel.csv](data/fuel.csv):** fuel consumption and prices
* **[doc](doc):** human-readable documentation for various systems as well as evaluation notes: why did I choose X over Y?
  * **[back-up camera](doc/back-up-camera.md):** digital capture to display the image on a tablet or even stream it over WiFi
  * **[bikes](doc/bikes.md):** pros and cons of different ways to transport a bike
  * **[dashcam](doc/dashcam.md):** although I've currently settled on a commercial dashcam, I had plans to use a webcam and a Raspberry Pi instead
  * **[GNSS](doc/gnss.md):** using a dedicated GPS/GLONASS/Galileo receiver for satellite navigation
  * **[ideas](doc/ideas.md):** this document is a bit older and contains rough sketches or ideas for how to do things
  * **[network](doc/network.md):** how my internal Gigabit Ethernet network looks like
  * **[radio](doc/radio.md):** antenna mounts on the roof, CB and PMR radio
  * **[sensors](doc/sensors.md):** mostly temperature sensor evaluation
  * **[storage](doc/storage.md):** evaluation of storage container systems and load security
  * **[van life](doc/vanlife.md):** some basic hints on where to park and how to live in a van in general
* **[infra](infra):** configuration for hosts and devices; not sure whether I'll continue maintaining this, it's also outdated
* **[src](src):** source code for custom-built software
  * **[api](src/api):** draft of a van API
  * **[homn](src/homn):** C code for the Arduino that controls lights and water
  * **[tasker](src/tasker):** a Tasker project to display the van's uplink quality on an Android smartphone
