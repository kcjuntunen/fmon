#!/usr/bin/env python3

import sys
import logging
from pymongo import MongoClient
from fmon import query
from eve import Eve
from multiprocessing import Process
from datetime import datetime
from flask import request


def pre_wrap(text):
    return ('<pre>' + text + '</pre>')

class EveServer():
    def __init__(self,
                 mongoclient=MongoClient(host='localhost', port=27017),
                 name='arduinolog'):
        self.al = query.ArduinoLog(db=mongoclient, name=name)
        self.app = Eve(settings='../settings.py')

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

        @route(self, '/lastreading/<sensor>')
        def lastreading(sensor):
            if sensor in self.al.ts_sensors:
                return str(self.al.last_value(sensor))
            else:
                sl = ',\n'.join(self.al.ts_sensors)
                msg = ('Unacceptible sensors. Please try:\n' + sl)
                return msg

        @route(self, '/table/events')
        def table_events():
            return pre_wrap(self.al._print_events())

        @route(self, '/table/hourstats')
        def table_hourstats():
            return pre_wrap(self.al._print_hour_table())

        @route(self, '/table/<sensor>')
        def table(sensor):
            if sensor in self.al.ts_sensors:
                return pre_wrap(self.al._print_values(sensor))
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
