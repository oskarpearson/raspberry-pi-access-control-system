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
import logging
import re
import time

# Associated Packages
import quick2wire.i2c as i2c

###############################################################################
# Strong Link SL 030 i2c Card Reader
# http://www.stronglink-rfid.com/en/rfid-modules/sl030.html
###############################################################################
class StrongLinkSl030Reader:
    
    # Instance Variables
    
    reader_type = "Stronglink SL 030 Card Reader"
    name = 'NOT DEFINED'

    # This pin indicates that a card is near the reader
    trigger_pin = None

    # Used for enabling/disabling
    associated_device = None

    # How to communicate with the card reader
    i2c_address = None


    # This device is instantiated and configured based on a config file. The
    # object is passed a 'configparser' fragment, and needs to set the
    # appropriate parameters
    def  __init__(self, config):
        """Reader Constructor"""
        # Read config parameters dictionary. Note that if someone supplies
        # an unsupported parameter, we raise error
        for o, a in config:
            if o == 'trigger pin':
                self.trigger_pin = int(a)
            elif o == 'i2c address':
                if not re.match(r'^0x', a):
                    assert False, "i2c address must be in hex format"
                self.i2c_address = int(a, 16)
            elif o == 'associated device':
                self.associated_device = a
            else:
                if o != 'reader type':
                    assert False, "Unsupported parameter '%s'" % o

        # Check that everything makes sense in the supplied config
        # file, so that if someone leaves out a critical parameter or
        # similar, we raise an appropriate error
        if self.trigger_pin is None:
            assert False, "%s - trigger_pin not set" % self.name
        if not self.associated_device:
            assert False, "%s - associated_device not set" % self.name
        if not self.i2c_address:
            assert False, "%s - i2c address not set" % self.name

    # Callback - called when the state of the 'trigger pin'
    # goes either high or low. Then either disables or enables
    # the associated devices
    def trigger_pin_state_change(self, new_state, devices_by_name):
        logging.debug("State change - %s" % new_state)
        device = devices_by_name[self.associated_device]
        logging.debug("Device - %s" % self.associated_device)
        # If the pin state drops to false, then it means a card has been
        # presented - try and read the card
        if new_state == False:
            logging.debug("Reading card on reader %s" % self.name)
            card = self.read_card()
            device.check_for_card_in_db(card)
        else:
            logging.debug("Disabling device %s" % self.associated_device)
            # The card has been removed - we need to ensure that the
            # associated device is turned off
            devices_by_name[self.associated_device].disable()
            logging.debug("Device %s disabled" % self.associated_device)

    # Read the card via the i2c protocol. See the user manual at
    # http://www.stronglink-rfid.com/en/rfid-modules/sl030.html
    def read_card(self):
        logging.info("Fetching card id from %0X" % self.i2c_address)
        # Fetch the card ID by sending 1/1 to the SL030 card reader
        with i2c.I2CMaster() as bus:
            bus.transaction(
                i2c.writing_bytes(0x50, 0x1, 0x1))
            time.sleep(0.1)      # SL030 requires this time to respond reliably
            read_results = bus.transaction(
                i2c.reading(0x50, 10))

        returned_len = read_results[0][0]
        status = read_results[0][2]

        if returned_len == 0:
            logging.info("Error fetching from card reader")
            return(None)

        if status == 0x1:       # No Tag
            logging.info("No tag detected")
            return(None)
        else:
            # Format the read card ID as a hex string
            card_as_hex = []
            for x in range(3, returned_len):
                card_as_hex.append('{1:02x}'.format(x,
                        read_results[0][x]).upper())
            logging.debug("Card presented: " % card_as_hex)
            return(''.join(card_as_hex))
