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

import datetime
import logging
import pymongo

class MongoConnection():
    def __init__(self, server, port, username, passwd):
        self._server = server
        self._port = port
        self._client = None
        self._mongdb = None
        self._timeseries_data = None
        self._event_data = None
        self._config_data = None
        self._alerts = None
        self.logger = logging.getLogger('FMon')

    @property
    def connection(self):
        if self._client is None:
            try:
                self._client = pymongo.MongoClient(self._server,
                                                   self._port)
            except pymongo.errors.ConnectionFailure as cf:
                self.logger.error('Mongo connection failure: {0}'.format(cf))
            except pymongo.errors.PyMongoError as pme:
                self.logger.error('Mongo connection failure: {0}'.format(cf))
                exit(-1)
        return self._client

    @property
    def database(self):
        if self._mongdb is None:
            try:
                db = self.connection.arduinolog
                self._mongdb = db
            except pymongo.errors.PyMongoError as pme:
                self.logger.error('PyMongo error: {0}'.format(pme))
        return self._mongdb

    @property
    def config_data(self):
        if self._config_data is None:
            try:
                self._config_data = self.database.config
            except pymongo.errors.PyMongoError as pme:
                self.logger.error('PyMongo error: {0}'.format(pme))
        return self._config_data

    @property
    def alerts(self):
        if self._alerts is None:
            try:
                self._alerts = self.database.alerts
            except pymongo.errors.PyMongoError as pme:
                self.logger.error('PyMongo error: {0}'.format(pme))
        return self._alerts

    @property
    def timeseries_data(self):
        if self._timeseries_data is None:
            try:
                td = self.database.timeseriesdata
                self._timeseries_data = td
            except pymongo.errors.PyMongoError as pme:
                self.logger.error('PyMongo error: {0}'.format(pme))
        return self._timeseries_data

    def has_hour(self, hour):
        res = self.timeseries_data.find_one({'ts_hour': hour})
        if res is not None:
            return True
        return False

    @property
    def event_data(self):
        if self._event_data is None:
            try:
                ed = self.database.eventdata
                self._event_data = ed
            except pymongo.errors.PyMongoError as pme:
                self.logger.error('PyMongo error: {0}'.format(pme))
        return self._event_data

    @property
    def current_hour(self):
        now = datetime.datetime.now()
        y = now.year
        m = now.month
        d = now.day
        h = now.hour
        return datetime.datetime(y, m, d, h)

    @property
    def current_minute(self):
        m = datetime.datetime.now().minute
        return m

    @property
    def current_second(self):
        s = datetime.datetime.now().second
        return s

    def create_insert_payloads(self, json_ob):
        payloads = []
        config = self.config_data.find_one()
        for sensor in config['sensors']:
            name = sensor['sensor']
            h = self.current_hour
            m = self.current_minute
            s = self.current_second
            payload = {
                'ts_hour': h,
                'name': name,
                'values': { str(m): 
                    [ json_ob[name], ] }
            }
            payloads.append(payload)
        return payloads

    def timeseries_insert(self, data):
        self._update(data)
        # if self.has_hour(self.current_hour):
        #     self._update(data)
        # else:
        #     self._insert(data)
    
    def _update(self, json_ob):
        payloads = []
        config = self.config_data.find_one()
        bulkoperation = self.timeseries_data.initialize_unordered_bulk_op()
        for sensor in config['sensors']:
            name = sensor['sensor']
            h = self.current_hour
            m = str(self.current_minute)
            s = str(self.current_second)
            criteria = { 'ts_hour': h, 'name': name}
            update = { '$push': { 'values.{}'.format(m): json_ob[name] } }
            r = bulkoperation.find(criteria).upsert().update(update)
        try:
            bulkoperation.execute()
        except pymongo.errors.PyMongoError as pme:
            self.logger.error('PyMongoError: {0}'.format(pme))

    def _insert(self, data):
        payloads = self.create_insert_payloads(data)
        try:
            self.timeseries_data.insert_many(payloads)
        except pymongo.errors.PyMongoError as pme:
            self.logger.error('PyMongoError: {0}'.format(pme))

    def event_insert(self, data):
        if 'Event' in data:
            data = data['Event']
        data['ts'] = datetime.datetime.now()
        self.logger.debug('Inserting {0}'.format(data))
        self.event_data.insert_one(data)
