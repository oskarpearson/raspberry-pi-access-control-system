#!/bin/bash

export QUICK2WIRE_API_HOME=/home/pi/quick2wire-python-api
export PYTHONPATH=$PYTHONPATH:$QUICK2WIRE_API_HOME

cd /home/pi/rpac
./rpac.py --config=rpac.conf

