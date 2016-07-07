#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pymongo import MongoClient
from datetime import datetime
from dateutil import parser
from math import ceil, trunc
import numpy as np
import argparse

SPM = 12
SPH = SPM * 60


def current_hour():
    now = datetime.now()
    y, m, d, h = (now.year, now.month, now.day, now.hour)
    return datetime(y, m, d, h, 0)


def round_to_hour(dt):
    gt = datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0)
    lt = datetime(dt.year, dt.month, dt.day, dt.hour + 1, 0, 0)
    return gt, lt


def calculate_time(sample_number):
    minute = sample_number / SPM
    second = ceil((minute - trunc(minute)) * 60)
    return int(minute), int(second)


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
    def __init__(self):
        self._client = None
        self._database = None
        self._tsdata = None
        self._evdata = None
        self._client = MongoClient('localhost', 27017)

    @property
    def mc(self):
        if self._client is None:
            self._client = MongoClient('localhost', 27017)
        return self._client

    @property
    def db(self):
        if self._database is None:
            self._database = self.mc.arduinolog
        return self._database

    @property
    def ts(self):
        if self._tsdata is None:
            self._tsdata = self.db.timeseriesdata
        return self._tsdata

    @property
    def ev(self):
        if self._evdata is None:
            self._evdata = self.db.eventdata
        return self._evdata

    @property
    def ts_sensors(self):
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

    def hour_cursor(self, sensor, dt=current_hour()):
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
        return [x for x in self.hour_cursor(sensor, dt)['values']]

    def hour_events(self, sensor, dt=current_hour()):
        gt = datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0)
        lt = datetime(dt.year, dt.month, dt.day, dt.hour + 1, dt.minute, 0)
        dat = self.ev.find({'name': sensor,
                            'ts': {'$gt': gt, '$lt': lt}})
        return dat

    def hour_event_list(self, sensor, dt=current_hour()):
        return [x for x in self.hour_events(sensor, dt)]

    def avg_hour(self, sensor, dt=current_hour()):
        return self.hour_stats(sensor, dt)['avg']

    def min_hour(self, sensor, dt=current_hour()):
        return self.hour_stats(sensor, dt['min'])

    def max_hour(self, sensor, dt=current_hour()):
        return self.hour_stats(sensor, dt['max'])

    def std_hour(self, sensor, dt=current_hour()):
        return(np.std(self.hour_list(sensor, dt)))

    def print_events(self, dt=current_hour()):
        header = ('Sensor', 'Time', 'Values')
        hfmt = "{:^15s}|{:^10s}|{:^10s}"
        fmt = "{:15s}|{:10s}|{:10f}"
        labelline = hfmt.format(*header)
        print(labelline)
        print('-' * len(labelline))
        cnt = 0
        for sensor in self.ev_sensors:
            for event in self.hour_event_list(sensor, dt):
                ev_ts = event['ts']
                timestring = "{:2d}:{:02d}:{:02d}".format(ev_ts.hour,
                                                          ev_ts.minute,
                                                          ev_ts.second)
                data = (sensor, timestring, event['value'])
                print(fmt.format(*data))
                cnt += 1

    def print_values(self, sensor, dt=current_hour()):
        header = ('Sensor', 'Time', 'Values')
        hfmt = "{:^15s}|{:^10s}|{:^10s}"
        fmt = "{:15s}|{:10s}|{:10f}"
        datestring = "{:2d}:{:02d}".format(dt.hour, dt.minute)
        print(hfmt.format(*header))
        for v in self.hour_list(sensor, dt):
            print(fmt.format(sensor, datestring, v))

    def print_hour_table(self, dt=current_hour()):
        header = ('Sensor', 'Time', 'σ', 'Avg', 'Max', 'Min')
        hfmt = "{:^15s}|{:^10s}|{:^10s}|{:^10s}|{:^10s}|{:^10s}"
        fmt = "{:15s}|{:10s}|{:10f}|{:10f}|{:10f}|{:10f}"
        labelline = hfmt.format(*header)
        print(labelline)
        print('-' * len(labelline))
        for sensor in self.ts_sensors:
            stats = self.hour_stats(sensor)
            data = (sensor,
                    dt.strftime('%Y/%m/%d'),
                    self.std_hour(sensor, dt),
                    stats['avg'], stats['max'], stats['min'])
            print(fmt.format(*data))

    # def std_hour(self, sensor, dt=current_hour()):
    #     return(np.std(self.hour_list(sensor, dt)))

    def hour_stats(self, sensor, dt=current_hour()):
        pipeline = [
            {
                "$match": {
                    "name": sensor
                }
            },
            {
                "$match": {
                    "ts_hour": {
                        "$gte": dt
                    }
                }
            },
            {
                "$unwind": "$values"
            },
            {
                "$group": {
                    "_id": "$name",
                    "min": {
                        "$min": "$values"
                    },
                    "max": {
                        "$max": "$values"
                    },
                    "avg": {
                        "$avg": "$values"
                    }
                }
            }
        ]
        d = self.mc.arduinolog
        return d.command('aggregate',
                         'timeseriesdata',
                         pipeline=pipeline,
                         explain=False)['result'][0]

    def __str__(self):
        return self.db.name

if __name__ == "__main__":
    execute(parse_args())
