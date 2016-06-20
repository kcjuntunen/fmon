"""
startpoint
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
import sys
print(sys.path)

import json
import bson
import logging
import pymongo
import serial
from threading import Timer, Thread
from .mongoconnection import MongoConnection
from .fmonconfig import FMonConfiguration

from fmon import LOGGING_FORMAT
from fmon import CONSOLE_FORMAT
from fmon import DC2
from fmon import DC4

poll_args = {"comm": "go", "unrequited_messages": 0, "sig": DC2}
missed_message_limit = 5

class Fmon():
    def __init__(self):
        # set up logging
        self.start_logging()
        self.logger.debug('Connecting to db')
        self.mc = MongoConnection('localhost', 27017, '', '')
        self.fmc = FMonConfiguration(self.mc)

        self.logger.debug('Opening serial')
        self.ser = serial.Serial(port=self.fmc.port,
                                 baudrate=self.fmc.baudrate)

    def start_logging(self):
        self.logger = logging.getLogger('Fmon')
        self.logger.setLevel(logging.DEBUG)
        ffmt = logging.Formatter(LOGGING_FORMAT)
        cfmt = logging.Formatter(CONSOLE_FORMAT)
        ch = logging.StreamHandler()
        ch.setFormatter(cfmt)
        ch.setLevel(logging.ERROR)
        
        fh = logging.FileHandler('fmon.log')
        fh.setFormatter(ffmt)
        fh.setLevel(logging.DEBUG)
        
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
        
    def poll(self):
        self.ser.write(poll_args['sig'])
        self.ser.flush()
        poll_args['unrequited_messages'] += 1
        self.logger.debug("Polling arduino")

    def poll_loop(self):
        if poll_args['unrequited_messages'] < missed_message_limit:
            self.poll()
            if poll_args['comm'] != 'stop':
                Timer(5, self.poll_loop, ()).start()
        else:
            poll_args['sig'] = DC4
            self.poll()
            if poll_args['comm'] != 'stop':
                Timer(15, self.poll_loop, ()).start()

    def get_line(self):
        return self.ser.readline().decode('utf-8').strip()

    def listen(self):
        json_ob = None
        line = None
        while True:
            try:
                line = self.get_line()
                if line is not None:
                    poll_args['unrequited_messages'] = 0
                json_ob = json.loads(line)
                self.process_data(json_ob)
            except ValueError as ve:
                self.logger.error('Probably not JSON: {0}\n'.format(ve) +
                                  'Offending line: {0}'.format(line))

    def process_data(self, json_ob):
        self.logger.debug(json.dumps(json_ob))
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
    f = Fmon()
    l = logging.getLogger('FMon')
    l.debug('Starting loop')
    f.poll_loop()
    f.listen()

if __name__ == "__main__":
    start()
