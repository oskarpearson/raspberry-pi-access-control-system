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

# System-Wide packages
import fileinput
import logging
import logging
import re

# Associated Packages
from quick2wire import gpio

###############################################################################
# Class - ControlledDevice
###############################################################################

# A 'Controlled Device' is some sort of hardware that we are responsible for
# access to. For example, it could be a door or a piece of machinery
class ControlledDevice:
    name = 'NOT DEFINED'
    
    # To enable a device, some hardware pins may need to have their pins set
    # 'low', while on some other devices, the pins may need to be set 'high'.
    #
    # Similarly, on a device being 'disabled', the same is true.
    #
    pin_objects = {}                # Objects that are used for interfacing with HW
    enable_set_pins_low = []
    enable_set_pins_high = []
    disable_set_pins_low = []
    disable_set_pins_high = []

    # Access to a controlled device is based on the card presented,
    # with a list of 'allowed cards' stored in a configuration file. The exact
    # filename used is supplied in the config file
    acl_filename = None

    # The 'authorised cards' are read into this in-memory array. Since the
    # use-case for the rpac system is less than 1000 cards, we read this
    # into memory
    authorised_cards = []

    # This device is instantiated and configured based on a config file. The
    # object is passed a 'configparser' fragment, and needs to set the
    # appropriate parameters
    def  __init__(self, config, acl_path):
        """Device Constructor"""
        self.acl_path = acl_path

        # Process configuration file fragment
        for o, a in config:
            if o == 'enable set pins low':
                self.enable_set_pins_low = self.parse_pin_parameters(a)
            elif o == 'enable set pins high':
                self.enable_set_pins_high = self.parse_pin_parameters(a)
            elif o == 'disable set pins low':
                self.disable_set_pins_low = self.parse_pin_parameters(a)
            elif o == 'disable set pins high':
                self.disable_set_pins_high = self.parse_pin_parameters(a)
            elif o == 'acl filename':
                self.acl_filename = a
            else:
                assert False, "Unsupported parameter '%s' for Device" % o

        # Check that everything makes sense in the supplied config
        # file, so that if someone leaves out a critical parameter or
        # similar, we raise an appropriate error
        if not (                                        \
                   len(self.enable_set_pins_low)   > 0  \
                or len(self.enable_set_pins_high)  > 0  \
                or len(self.disable_set_pins_low)  > 0  \
                or len(self.disable_set_pins_high) > 0  \
            ):
            assert False, "%s - None of the following set: " \
                "enable_set_pins_low, " \
                "enable_set_pins_high, " \
                "disable_set_pins_low, " \
                "disable_set_pins_high " % self.name
            
        if not self.acl_filename:
            assert False, "ACL filename not set"


    # The pins originally specified in the config file are text, and need
    # to be converted to numerics. There can also be more than one per
    # config file line, so clean things up and store them in an array
    def parse_pin_parameters(self, pins_as_text):
        if re.search('[^0-9\ ]+', pins_as_text):
             assert False, "Pins parameters supplied is not all-numeric," \
                + " separated by spaces (is '%s')" % pins_as_text
        pins = []
        for pin_number_as_text in pins_as_text.split():
            pin_number = int(pin_number_as_text)
            pins.append(pin_number)

            # Create a communication object
            if pin_number not in self.pin_objects:
                pin = gpio.pins.pin(pin_number)
                pin.open()
                pin.direction = gpio.Out
                self.pin_objects[pin_number] = pin

        return pins


    def check_for_card_in_db(self, card):
        logging.info("Card presented to device %s" % self.name)
        logging.info("Card id %s" % card)
        self._load_card_db()

        if card in self.authorised_cards:
            logging.info("Card IS authorised");
            return self.enable()
        else:
            logging.info("Card is NOT authorised");
            return self.disable()


    # STATE CHANGES: enable or disable this device
    def enable(self):
        self._set_pins(0, self.enable_set_pins_low)
        self._set_pins(1, self.enable_set_pins_high)
        return True

    def disable(self):
        self._set_pins(0, self.disable_set_pins_low)
        self._set_pins(1, self.disable_set_pins_high)
        return False

    # Set associated pins low or high
    def _set_pins(self, state, pin_list):
        for pin_number in pin_list:
            self.pin_objects[pin_number].value = state

    # Read the card database, and build a list of authorised cards
    def _load_card_db(self):
        acl_full_path = self.acl_path + '/' + self.acl_filename
        self.authorised_cards = []
        for line in fileinput.input(acl_full_path):
            self.authorised_cards.append(line.rstrip())

