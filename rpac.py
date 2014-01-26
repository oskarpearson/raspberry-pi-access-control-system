#!/usr/bin/env python3

# NOTE: THIS IS MY FIRST EVER PYTHON CODE! Please let me know if I have
# chosen the wrong idioms or conventions in this code :) oskar@deckle.co.uk


# Raspberry Pi-based RFID Access Control System
# Copyright (C) 2012 Oskar Pearson
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.



###############################################################################
# OVERVIEW
###############################################################################
#
# This code sits in a loop waiting for cards to be presented. When the card
# is presented, the ID of the card is read and then checked against an
# access control list.
#
# If the card is in the access control list, a physical hardware GPIO pin is
# raised on the Raspberry Pi. This pin generally triggers a relay, which
# will then enable a device, open a door, or similar.
#
# When the card is removed, the GPIO pin is dropped, turning off the relay
# and disabling the door.
#

#
# Card Presentation - Hardware
# ----------------------------
#
# When an access card is presented to a hardware card-reader, it signals this
# to the Raspberry Pi by 'raising' a GPIO pin. Note that this is a different
# GPIO pin to the one referred to above (the 'control' GPIO pin).
#
# This 'card presented' pin acts as a signal to this program to execute the
# card reader code, which then reads the presented card ID through the
# i2c protocol.
#
# When the pin 'falls', it means the card has been removed from the proximity
# of the card reader. When that occurs, we call the Reader object code that
# will disable the device / close the door.
#

#
# Underlying Operating System Concepts
# ------------------------------------
#
# GPIO in Linux is managed through reading/writing files. Once opened,
# these files are effectively normal Unix filedescriptors.
# 
# The quick2wire-python-api code abstracts away the filedescriptor
# access to a 'Pin' object. These objects can be used with the 'select'
# or 'epoll' posix call to handle events, such as the pin going 'high'
# or 'low'.
#
# Most of the code in the this file relates to reading in the configuration
# file and building a series of in-memory objects that represent the desired
# config.
#
# This code then creates 'Pin' objects to match the configuration objects,
# and then uses 'epoll(7)' to watch for state changes on the Pins. When the
# pins change state, this code calls methods on the Objects, which then read
# the card and enable/disable the attached hardware Devices.
#

# System-Wide imports
import getopt
import logging
import pprint
import select
import socket
import sys
import time

# Associated Packages
import quick2wire.gpio as gpio

# Local packages
import config

# Local packages and globals
logging.basicConfig(filename='rpac.log', \
            level=logging.DEBUG)


# Displays help on how to use this program
def usage(extra_message):
    if extra_message:
        print("\nERROR: %s" % extra_message)
    print("""
Options:
    --config=/path/to/rpac.conf
    
Config option defaults to /usr/local/etc/rpac.conf)
""")
    sys.exit(2)


# Parses command-line options
def parse_command_line_arguments():
    config_filename = '/usr/local/etc/rpac.conf'
    
    # Portions of the code for parsing command-line parameters are from
    # the example at
    # http://docs.python.org/2/library/getopt.html
    # © Copyright 1990-2013, Python Software Foundation. 
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "hdn:c:", ["help", "config="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-c", "--config"):
            config_filename = a
        else:
            assert False, "Unhandled option"
    # End of example code

    return(config_filename)


# This code builds a set of 'Pin' objects relating to
# the hardware pins in the config file. These Pin objects
# are then map to the underlying card Readers, so that
# a change in state on the hardware Pin can trigger the
# configured underlying Object
def build_hardware_pin_map(readers_by_name):
    pin_objects_to_watch = {}
    for reader in readers_by_name:
        trigger_pin = readers_by_name[reader].trigger_pin
        assert trigger_pin not in pin_objects_to_watch, \
            "Pin %s is set as the 'trigger pin' for more " \
            " than one reader or button" % trigger_pin
        # In the pins-to-watch code, we set a reference to the reader
        # object itself
        pin_objects_to_watch[trigger_pin] = {}
        pin_objects_to_watch[trigger_pin]['handler_object'] = \
                    readers_by_name[reader]

        # Create an 'input' pin object from quick2wire.gpio, watching
        # both rising and falling edge transitions - for the cards arriving \
        # and leaving
        pin = gpio.pins.pin(trigger_pin)
        pin.open()

        pin.direction = gpio.In
        pin.interrupt = gpio.Both

        pin_objects_to_watch[trigger_pin]['gpio_pin'] = pin

    return pin_objects_to_watch


# LOOPS FOREVER
#
# This code sits and waits for state changes on the configured hardware pins
#
def wait_for_pin_state_changes(readers_by_name, devices_by_name):
    fds_to_pins = {}

    # Fetch a list of pins to watch, each of which maps to
    # a card reader
    pin_objects_to_watch = build_hardware_pin_map(readers_by_name)


    # Configure the select handler, setting it to watch the
    # filedescriptors that underly the hardware pins.
    # To do this, we grab the filedescriptors that underly the
    # pins, and build a map between filedescriptors and objects
    epoll_handler = select.epoll()
    for pin_num in pin_objects_to_watch:
        handler_object = pin_objects_to_watch[pin_num]['handler_object']
        gpio_pin = pin_objects_to_watch[pin_num]['gpio_pin']

        epoll_handler.register(gpio_pin, select.EPOLLET)
        fds_to_pins[gpio_pin.fileno()] = pin_num

    # Loop forever, waiting for pin state changes, and triggering the
    # pins based on their values
    while True:
        logging.debug("Waiting for event on reader pins")
        events = epoll_handler.poll()
        for filedescriptor, event in events:
            pin_no = fds_to_pins[filedescriptor]
            logging.debug("Got event on pin number %s" % pin_no)
            pin_value = pin_objects_to_watch[pin_no]['gpio_pin'].value
            pin_objects_to_watch[pin_no]['handler_object'].trigger_pin_state_change(
                        pin_value, devices_by_name)


def main():
    # Get the config file, and from it, get the readers, devices,
    # and button objects
    config_filename = parse_command_line_arguments()
    acl_path, readers_by_name, devices_by_name = \
                config.parse_config_options(config_filename)
    
    # At startup, make sure that all devices are in the 'disabled' state.
    for device_name in devices_by_name:
        devices_by_name[device_name].disable()
    
    # Loop forever waiting for state changes
    logging.info("Waiting for card to be presented")
    wait_for_pin_state_changes(readers_by_name, devices_by_name)
    # NOT REACHED

if __name__ == "__main__":
    main()

