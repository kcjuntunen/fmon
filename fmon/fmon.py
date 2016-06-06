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
import ip
from threading import Timer, Thread

class Fmon():
    def __init__(self):
        # set up logging
        self.logger = logging.Logger(format=LOGGING_FORMAT)
        self.device_info = {'clientip': ip.get_ip_address(), 'user': 'OfficePi'}
        # read settings file for db connection info
        client = pymongo.MongoClient('localhost', 27017)
        db = client.test_database
        # read db for serial info
        self.ser = serial.Serial(port='/dev/ttyAMA0', baudrate=115200)
        pass

    def poll(self):
        self.ser.write(DC2)
        self.ser.flush()
        self.logger.debug("Polling arduino")
        Timer(5, poll, (self)).start()

    def listen(self):
        while True:
            line = ser.readline().decode('utf-8')
            json_ob = None
            try:
                json_ob = json.loads(line)
            except Exception as ex:
                print('Probably not JSON: {0}'.format(ex.__str__()))

            self.process_data(json_ob)

    def process_data(self, json_ob):
        try:
            if 'Poll' in json_ob:
                ss = self.db.snapshots
                ss.insert(json_ob['Poll'])
        except pymongo.errors.ConnectionFailure as cf:
            print('Connection Failure: {0}'.format(cf.__str__()))
        except pymongo.errors.ConfigurationError as ce:
            print('Configuration Error: {0}'.format(ce.__str__()))
