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

import pymongo

class MongoConnection():
    def __init__(self, server, port, username, passwd):
        self.server = server
        self.port = port
        self.client = None

    @property
    def connection(self):
        if self.client is None:
            try:
                self.client = pymongo.MongoClient(self.server,
                                                  self.port)
                
            except pymongo.errors.ConnectionFailure as e:
                print('Err: {0}'.format(e.__str__()))
        return self.client
