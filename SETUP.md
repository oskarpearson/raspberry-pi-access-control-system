# Hardware Configuration

* Start with a blank Raspberry Pi running Raspian "2012-12-16-wheezy-raspbian" or later

* Connect a Stronglink SL030 to the i2c bus, and the SL030 'OUT' to hardware
  pin 11 on the Raspberry Pi header

* You may need to compile the Raspberry Pi kernel as per Ben Green's [i2c
  Raspberry Pi kernel
  patch](http://bengreen.eu/fancyhtml/techiestuff/i2conraspberrypi.html) but
  this appears to be unnecessary on later versions of Raspbian


# System Setup

Enable the required kernel modules. See this [SK Pang blog](http://www.skpang.co.uk/blog/archives/575)
entry for more details

    sudo -s
    echo i2c-dev >> /etc/modules
    echo blacklist spi-bcm2708 >> /etc/modprobe.d/raspi-blacklist.conf
    # Note that you will need to reboot after this step

# Install required packages/libraries
    sudo aptitude install python-pip python-virtualenv git
    
# For debugging
    sudo aptitude install i2c-tools


GPIO-ADMIN
==========

Install gpio-admin - see the [gpio-admin github
page](https://github.com/quick2wire/quick2wire-gpio-admin) for more
information. Unfortunately the quick2wire code occasionally stops being
backwards compatible, so I check-out a specific version of the code. If you
encounter bugs, you may wish to do a 'git checkout master' instead of 'git
checkout tags/1.1.10' here.

    cd ~
    git clone git://github.com/quick2wire/quick2wire-gpio-admin.git
    cd quick2wire-gpio-admin
    git checkout tags/1.1.0
    make
    sudo make install
    sudo adduser pi gpio


QUICK2WIRE LIBRARY
==================

Install the Quick2Wire Python API:

See the [Quick 2 Wire](https://github.com/quick2wire/quick2wire-python-api)
page for more information.

This library is unusual in that its default installation method is to reside
in the ~pi home directory. Note that README.txt references this at this path
through environment variables.

As with GPIO-admin above, the quick2wire code occasionally stops being
backwards compatible, so I check-out a specific version of the code. If you
encounter bugs, you may wish to do a 'git checkout master' instead of 'git
checkout c5e21e9d804012efd9d214d18909034b4b898c96' here.

    cd ~
    git clone git://github.com/quick2wire/quick2wire-python-api.git
    cd quick2wire-python-api
    git checkout c5e21e9d804012efd9d214d18909034b4b898c96
    
    sudo groupadd i2c
    sudo adduser pi i2c


FINAL CONFIGURATION
===================

Make directories for the carddb:

    sudo mkdir -p /var/local/rpac/acls/
    sudo chown -R root:root /var/local/rpac/
    sudo chmod -R 755 /var/local/rpac/

Reboot, so that the kernel drivers are loaded:

    sudo reboot

TROUBLESHOOTING
===============

## Error: gpio-admin: could not flush data to /sys/class/gpio/export: Device or resource busy

This message is related to a bug in the quick2wire-gpio-admin library, where
if you attempt to export something that's already exported, gpio-admin
crashed.

The simplest solution is to reboot. Alternatively, you can do the following,
which will un-export all items. Note that this may lead to other hardware
items on the box failing. A reboot may be the better option then.

  sudo -s
  cd /sys/class/gpio
  # This command finds all items like 'gpio23' in the /sys/class/gpio, and then
  # runs a command like 'gpio-admin unexport 23'
  ls -d gpio[0-9][0-9] | sed -e 's/gpio//g' | xargs -r -t -l1 -exec gpio-admin unexport
  exit # go back to a standard user


## Card IDs may be corrupted / transposed 

If The Stronglink reader returns the wrong card IDs, this may be related to timing issues with
either the Raspberry Pi or the Stronglink reader. In this case, you may need to apply
Ben Green's [i2c Raspberry Pi kernel patch](http://bengreen.eu/fancyhtml/techiestuff/i2conraspberrypi.html)
