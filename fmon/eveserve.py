#!/usr/bin/env python3

import sys
import logging
from pymongo import MongoClient
from dateutil.parser import parse
from dateutil.tz import gettz
from pytz import utc, timezone
from os import linesep
from fmon import query
from eve import Eve
from multiprocessing import Process
from datetime import datetime
from flask import request

TZst = 'US/Eastern'

def pre_wrap(text):
    return ('<pre>\n' + text + '</pre>')

def parsedt(dt, tzs):
    # In [271]: lp = pytz.timezone('US/Eastern').localize(p)
    # In [272]: pytz.utc.normalize(lp)
    # Out[272]: datetime.datetime(2011, 7, 17, 8, 53, tzinfo=<UTC>)
    lp = timezone(tzs).localize(dt)
    return utc.normalize(lp)

class EveServer():
    def __init__(self,
                 mongoclient=MongoClient(host='localhost', port=27017),
                 name='arduinolog'):
        self.al = query.ArduinoLog(db=mongoclient, name=name)
        self.app = Eve(settings='../settings.py')
        self.tz = gettz(TZst)

        def route(self, rule, **options):
            def decorator(f):
                endpoint = options.pop('endpoint', None)
                self.app.add_url_rule(rule, endpoint, f, **options)
                return f
            return decorator

        @route(self, '/sensors')
        def sensor_list():
            return '\n'.join(self.al.all_sensors)

        @route(self, '/sensorcount')
        def sensor_count():
            return str(len([x for x in self.al.all_sensors]))

        @route(self, '/timeseriesdata/lastreading/<sensor>')
        def lastreading(sensor):
            if sensor in self.al.ts_sensors:
                return str(self.al.last_value(sensor))
            else:
                sl = ',\n'.join(self.al.ts_sensors)
                msg = ('Unacceptible sensors. Please try:\n' + sl)
                return msg

        @route(self, '/eventdata/table/')
        def table_events():
            return pre_wrap(self.al._print_events())

        @route(self, '/eventdata/table/<dt>')
        def events_date(dt):
            d = datetime.utcnow()
            mesg = ''
            try:
                d = parse(dt.split('(')[1].split(')')[0])
            except ValueError as ve:
                mesg = ('ERR: Invalid date ({}), '
                        'showing table for {}').format(ve, d) + linesep
            output = (mesg + self.al._print_events(parsedt(d, TZst)))
            return pre_wrap(output)

        @route(self, '/timeseriesdata/table/hourstats')
        def table_hourstats():
            return pre_wrap(self.al._print_hour_table())

        @route(self, '/timeseriesdata/table/hourstats/<dt>')
        def hour_stats_date(dt):
            d = datetime.utcnow()
            mesg = ''
            try:
                d = parse(dt.split('(')[1].split(')')[0])
            except ValueError as ve:
                mesg = ('ERR: Invalid date ({}), '
                        'showing table for {}').format(ve, d)  + linesep
            output = (mesg + self.al._print_hour_table(parsedt(d, TZst)))
            return pre_wrap(output)

        @route(self, '/timeseriesdata/table/<sensor>')
        def table(sensor):
            if sensor in self.al.ts_sensors:
                return pre_wrap(self.al._print_values(sensor))
            else:
                sl = ',\n'.join(self.al.ts_sensors)
                msg = pre_wrap('Unacceptible sensors. Please try:\n' + sl)
                return msg

        @route(self, '/timeseriesdata/table/<sensor>/<dt>')
        def table_date(sensor, dt):
            d = datetime.utcnow()
            mesg = ''
            try:
                d = parse(dt.split('(')[1].split(')')[0])
            except ValueError as ve:
                mesg = ('ERR: Invalid date ({}), '
                        'showing table for {}').format(ve, d)  + linesep
            if sensor in self.al.ts_sensors:
                return pre_wrap(self.al._print_values(sensor, parsedt(d, TZst)))
            else:
                sl = ',\n'.join(self.al.ts_sensors)
                msg = pre_wrap('Unacceptible sensors. Please try:\n' + sl)
                return msg

            
    def eve_start(self):
        logger = logging.getLogger('Fmon')
        logger.info('Starting Eve...')
        self._start()

        # def stop():
        #     self._stop()

    def _start(self):
        self.app.run(host='0.0.0.0', port=5000)

    def _stop():
        _proc.terminate()
        _proc.join()

if __name__ == "__main__":
    e = EveServer()
    e.eve_start()
