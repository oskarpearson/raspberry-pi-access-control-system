# Welcome to the Raspberry Pi Access Control System (RPAC)

The Raspberry Pi is a cheap ($25) credit-card sized ARM-based computer running
Linux, built and sold by the [Raspberry Pi
foundation](http://www.raspberrypi.org)

This project allows an electronics hobbyist to connect the Raspberry Pi to
both an RFID card reader and electronic relays, and use the RFID reader to
enable/disable physical machinery/doors by presenting or removing the RFID
card.

Supported Hardware:

* Raspberry Pi - any revision should work.

* [Stronglink SL030 RFID
  Reader](http://www.stronglink-rfid.com/en/rfid-modules/sl030.html)

* [Ciseco Relay
  Board](http://shop.ciseco.co.uk/kit-relay-board-simple-to-use-3v-operation-supports-logic-level-also/)
  (Note that you can replace this with a home-built circuit if you wish)

Other i2c RFID readers could be supported, but would require additional coding.

This code uses the following technologies:

* Python 3
* The i2c hardware electronics protocol
* The 'Quick2Wire' Python i2c library
* The 'Quick2Wire' Python General Purpose I/O (GPIO) library

# Notes on Raspberry Pi and i2c problems

You may need the [i2c Raspberry Pi kernel patch](http://bengreen.eu/fancyhtml/techiestuff/i2conraspberrypi.html)
See the "SETUP" file for more info about this.


# Notes on Security:

This system was specifically built to be used in a minimal-security
environment (a shared communal space). It was also specifically designed so as
to allow the use of existing London Underground 'Oyster Cards' so as to avoid
the purchase of new RFID cards by the user.

Further, it was also designed to operate without interfering with the normal
operation of those cards. If this were not the case the contents of the cards
could be overwritten by the user to ensure secure operation.

Given these (unusual) requirements, this code operates simply based on the
unique 'ID' supplied by the card. It does NOT use the MiFare encryption
facilities provided by the card. Since a determined attacker with electronics
knowledge could be able to fake a card ID, I do not recommend you use this
where security is important.



# Installation

This code requires a Raspberry Pi to operate. It may work on other similar
hardware supported by the Quick2Wire libraries with minor modification.

1) Install required programs as per 'SETUP.txt'

2) Edit rapc.conf and configure the pin assignments for the
    card reader and relay.

2) Start the rpac.py script by running start.sh, which configures the
    requisite environment variables for you:

    ./start.sh

