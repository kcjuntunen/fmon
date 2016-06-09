"""
Log timeseries sensor data from serial.
Copyright (C) 2016 Amstore Corp.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import json
import logging
import pymongo
import serial
from threading import Timer, Thread
from .mongoconnection import MongoConnection
from .fmonconfig import FMonConfiguration

from fmon import LOGGING_FORMAT
from fmon import DC2

class Fmon():
    def __init__(self):
        # set up logging
        logging.basicConfig(format=LOGGING_FORMAT)
        fmt = logging.Formatter(LOGGING_FORMAT)
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.WARNING)
        fh = logging.FileHandler('fmon.log')
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)

        self.logger = logging.getLogger('FMon')
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
        self.logger.debug('Connecting to db')
        self.mc = MongoConnection('localhost', 27017, '', '')
        self.fmc = FMonConfiguration(self.mc)
        self.logger.debug('Opening serial')
        self.ser = serial.Serial(port=self.fmc.port, baudrate=self.fmc.baudrate)

    def poll(self):
        self.ser.write(DC2)
        self.ser.flush()
        self.logger.debug("Polling arduino")

    def poll_loop(self):
        self.poll()
        Timer(5, self.poll, ()).start()

    def get_line(self):
        line = self.ser.readline().decode('utf-8').strip()
        self.logger.debug(line)
        return line

    def listen(self):
        json_ob = None
        while True:
            try:
                json_ob = json.loads(self.get_line())
            except ValueError as ve:
                self.logger.error('Probably not JSON: {0}'.format(ve))
            self.process_data(json_ob)

    def process_data(self, json_ob):
        try:
            if 'Poll' in json_ob:
                self.mc.timeseries_insert(json_ob['Poll'])
            if 'Event' in json_ob:
                self.mc.event_insert(json_ob['Event'])
        except pymongo.errors.ConnectionFailure as cf:
            self.logger.error('Connection Failure: {0}'.format(cf))
        except pymongo.errors.ConfigurationError as ce:
            self.logger.error('Configuration Error: {0}'.format(ce))

def start():
    Timer(10, exit, (0,)).start()
    f = Fmon()
    f.poll_loop()
    f.listen()
