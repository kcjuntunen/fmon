#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Queries for sensor data
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
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from dateutil import parser
from math import ceil, trunc
import numpy as np
import argparse

SPM = 12
SPH = SPM * 60


def current_hour():
    """
    Return the current hour with the least significant
    time segments set to 0
    """
    now = datetime.now()
    y, m, d, h = (now.year, now.month, now.day, now.hour)
    return datetime(y, m, d, h, 0)


def round_to_hour(dt):
    """
    Create a range for querying over an hour.
    """
    gt = datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0)
    lt = datetime(dt.year, dt.month, dt.day, dt.hour + 1, 0, 0)
    return gt, lt


def calculate_time(sample_number):
    """
    Estimate the second a sample was taken based on
    the index (SAMPLE_NUMBER) of a sample.
    """
    minute = sample_number / SPM
    second = ceil((minute - trunc(minute)) * 60)
    return int(minute), int(second)


def print_header(fmt, header):
    labelline = fmt.format(*header)
    print('-' * len(labelline))
    print(labelline)
    print('-' * len(labelline))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--datetime', help='specify an hour')
    parser.add_argument('-e', '--events', help='list events',
                        action='store_true')
    return parser.parse_args()


def execute(parsed_args):
    al = ArduinoLog()
    if parsed_args.datetime is not None:
        dt = parser.parse(parsed_args.datetime)
    else:
        dt = current_hour()

    if parsed_args.events:
        al.print_events(dt)
    else:
        al.print_hour_table(dt)


class ArduinoLog():
    def __init__(self, db=MongoClient('localhost', 27017)):
        """
        If a MongoClient isn't provided, we'll guess 127.0.0.1:27017.
        """
        self._client = None
        self._database = None
        self._tsdata = None
        self._evdata = None
        self._client = db

    @property
    def mc(self):
        """
        Returns a MongoClient object.
        """
        if self._client is None:
            self._client = MongoClient('localhost', 27017)
        return self._client

    @property
    def db(self):
        """
        Returns a Mongo database object.
        """
        if self._database is None:
            self._database = self.mc.arduinolog
        return self._database

    @property
    def ts(self):
        """
        Returns the timeseriesdata collection.
        """
        if self._tsdata is None:
            self._tsdata = self.db.timeseriesdata
        return self._tsdata

    @property
    def ev(self):
        """
        Returns the eventdata collection.
        """
        if self._evdata is None:
            self._evdata = self.db.eventdata
        return self._evdata

    @property
    def ts_sensors(self):
        """
        Returns a list of timeseries-type sensors.
        """
        pipeline = [
            {
                '$group': {
                    '_id': {'name': '$name'}}}
        ]
        d = self.mc.arduinolog
        res = d.command('aggregate',
                        'timeseriesdata',
                        pipeline=pipeline,
                        explain=False)['result']
        s_list = [x['_id']['name'] for x in res]
        return s_list

    @property
    def ev_sensors(self):
        """
        Returns a list of event-type sensors.
        """
        pipeline = [
            {
                '$group': {
                    '_id': {'name': '$name'}}}
        ]
        d = self.mc.arduinolog
        res = d.command('aggregate',
                        'eventdata',
                        pipeline=pipeline,
                        explain=False)['result']
        s_list = [x['_id']['name'] for x in res]
        return s_list

    def sample_count(self, sensor, dt=current_hour()):
        """
        Returns the number of samples in a particular hour.
        """
        pipeline = [
            {
                '$match': {
                    'ts_hour': dt,
                    'name': sensor
                }
            },
            {
                '$unwind': '$values'
            },
            {
                '$group': {
                    '_id': None,
                    'count': {
                        '$sum': 1
                    }
                }
            }
        ]
        d = self.mc.arduinolog
        res = d.command('aggregate',
                        'timeseriesdata',
                        pipeline=pipeline,
                        explain=False)['result']
        return res[0]['count']

    def latest_documents(self):
        """
        Returns the most recent documents for each timeseries-type sensor.
        """
        filter = {}
        limit = len(self.ts_sensors)
        sort = [('ts_hour', DESCENDING),
                ('name', ASCENDING)]
        cursor = self.ts.find(filter=filter, limit=limit, sort=sort)
        return [d for d in cursor]

    def hour_cursor(self, sensor, dt=current_hour()):
        """
        Returns a Mongo cursor pointing to a range of timeseries data.
        """
        gt, lt = round_to_hour(dt)
        criteria = {
            'name': sensor,
            'ts_hour': {
                '$gte': gt,
                '$lte': lt
            }
        }
        dat = self.ts.find(criteria)[0]
        return dat

    def hour_list(self, sensor, dt=current_hour()):
        """
        Converts the cursor from hour_cursor() to a list.
        """
        return [x for x in self.hour_cursor(sensor, dt)['values']]

    def hour_events_cursor(self, sensor, dt=current_hour()):
        """
        Returns a Mongo cursor pointing to an hour range of event data.
        """
        gt, lt = round_to_hour(dt)
        dat = self.ev.find({'name': sensor,
                            'ts': {'$gt': gt, '$lt': lt}})
        return dat

    def hour_event_list(self, sensor, dt=current_hour()):
        """
        Converts the cursor from hour_events_cursor() to a list.
        """
        return [x for x in self.hour_events_cursor(sensor, dt)]

    def avg_hour(self, sensor, dt=current_hour()):
        """
        Returns the average of an hour on a timeseries-type sensor.
        """
        return self.hour_stats(sensor, dt)['avg']

    def min_hour(self, sensor, dt=current_hour()):
        """
        Returns the min value from an hour on a timeseries-type sensor.
        """
        return self.hour_stats(sensor, dt['min'])

    def max_hour(self, sensor, dt=current_hour()):
        """
        Returns the max value from an hour on a timeseries-type sensor.
        """
        return self.hour_stats(sensor, dt['max'])

    def std_hour(self, sensor, dt=current_hour()):
        """
        Returns the standard deviation for an hour on a timeseries-type sensor.
        """
        return(np.std(self.hour_list(sensor, dt)))

    def count_matches(self, filter, collection):
        pipeline = [
            {
                '$match': filter
                },
            {
                '$group':
                {
                    '_id': None,
                    'count':
                    {
                        '$sum': 1
                        }
                    }
                }
            ]
        d = self.mc.arduinolog
        try:
            res = d.command('aggregate',
                            collection,
                            pipeline=pipeline,
                            explain=False)['result'][0]
            return res['count']
        except IndexError as ie:
            return 0

    def hour_stats(self, sensor, dt=current_hour()):
        pipeline = [
            {
                '$match': {
                    'name': sensor
                }
            },
            {
                '$match': {
                    'ts_hour': {
                        '$gte': dt
                    }
                }
            },
            {
                '$unwind': '$values'
            },
            {
                '$group': {
                    '_id': '$name',
                    'min': {
                        '$min': '$values'
                    },
                    'max': {
                        '$max': '$values'
                    },
                    'avg': {
                        '$avg': '$values'
                    }
                }
            }
        ]
        d = self.mc.arduinolog
        return d.command('aggregate',
                         'timeseriesdata',
                         pipeline=pipeline,
                         explain=False)['result'][0]

    def list_events(self, dt=current_hour()):
        res = []
        for sensor in self.ev_sensors:
            for event in self.hour_event_list(sensor, dt):
                ev_ts = event['ts']
                data = (sensor, ev_ts, event['value'])
                res.append(data)
        return res

    def list_values(self, sensor, dt=current_hour()):
        """
        Return a list of dicts with estimated timestamps.
        """
        res = []
        cnt = 0
        for v in self.hour_list(sensor, dt):
            minute, second = calculate_time(cnt)
            datestring = '{:d}-{:d}-{:d} {:2d}:{:02d}:{:02d}'.format(dt.year,
                                                                     dt.month,
                                                                     dt.day,
                                                                     dt.hour,
                                                                     minute,
                                                                     second)
            dt = parser.parse(datestring)
            res.append({'name': sensor, 'ts': dt, 'value': v})
            cnt += 1
        return res

    def print_values(self, sensor, dt=current_hour()):
        header = ('Sensor', 'Time', 'Values')
        hfmt = '{:^15s}|{:^19s}|{:^10s}'
        print_header(hfmt, header)
        fmt = '{:15s}|{:19s}|{:10f}'
        for v in self.list_values(sensor, dt):
            dt = v['ts']
            datestring = '{:d}-{:d}-{:d} {:2d}:{:02d}:{:02d}'.format(dt.year,
                                                                     dt.month,
                                                                     dt.day,
                                                                     dt.hour,
                                                                     dt.minute,
                                                                     dt.second)
            print(fmt.format(sensor, datestring, v['value']))

    def print_hour_table(self, dt=current_hour()):
        """
        Print a table of statistics for a given (DT) hour from all sensors.
        """
        header = ('Sensor', 'Time', 'σ', 'Avg', 'Max', 'Min')
        hfmt = '{:^15s}|{:^10s}|{:^10s}|{:^10s}|{:^10s}|{:^10s}'
        fmt = '{:15s}|{:10s}|{:10.3f}|{:10.3f}|{:10.3f}|{:10.3f}'
        labelline = hfmt.format(*header)
        print_header(hfmt, header)
        for sensor in self.ts_sensors:
            stats = self.hour_stats(sensor, dt)
            data = (sensor,
                    dt.strftime('%Y/%m/%d'),
                    self.std_hour(sensor, dt),
                    stats['avg'], stats['max'], stats['min'])
            print(fmt.format(*data))

    def print_events(self, dt=current_hour()):
        """
        Print a table of events in a given (DT) hour.
        """
        header = ('Sensor', 'Time', 'Values')
        hfmt = '{:^15s}|{:^10s}|{:^10s}'
        print_header(hfmt, header)
        fmt = '{:15s}|{:10s}|{:10f}'
        for sensor in self.ev_sensors:
            for event in self.hour_event_list(sensor, dt):
                ev_ts = event['ts']
                timestring = '{:2d}:{:02d}:{:02d}'.format(ev_ts.hour,
                                                          ev_ts.minute,
                                                          ev_ts.second)
                data = (sensor, timestring, event['value'])
                print(fmt.format(*data))

    def __str__(self):
        return self.db.name

if __name__ == '__main__':
    execute(parse_args())
