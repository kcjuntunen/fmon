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
import argparse
import json
import logging
import pymongo
import serial
from threading import Timer, Thread
from .mongoconnection import MongoConnection
from .fmonconfig import FMonConfiguration
from .alerts import Alerts

from fmon import LOGGING_FORMAT
from fmon import CONSOLE_FORMAT
from fmon import DC2
from fmon import DC4

poll_args = {"comm": "go", "unrequited_messages": 0, "sig": DC2}
missed_message_limit = 5

class Fmon():
    def __init__(self, server='localhost', port=27017,
                 username='', passwd='', db='arduinolog', args=None):
        # set up logging
        self.args = args
        self.start_logging()
        self.logger.info('Connecting to db')
        self.mc = MongoConnection(server, port, username, passwd, db)
        self.fmc = FMonConfiguration(self.mc)
        self.alerts = Alerts(self.mc, self.fmc)

        self.logger.info('Opening serial')
        self.ser = serial.Serial(port=self.fmc.port,
                                 baudrate=self.fmc.baudrate)

    def start_logging(self):
        self.logger = logging.getLogger('Fmon')
        self.logger.setLevel(logging.DEBUG)
        ffmt = logging.Formatter(LOGGING_FORMAT)
        cfmt = logging.Formatter(CONSOLE_FORMAT)
        self.ch = logging.StreamHandler()
        self.fh = logging.FileHandler('fmon.log')
        ch = self.ch
        ch.setFormatter(cfmt)
        ch.setLevel(logging.ERROR)

        if self.args and self.args.verbose:
            ch.setLevel(int(self.args.verbose))

        fh = self.fh
        fh.setFormatter(ffmt)
        fh.setLevel(logging.INFO)

        if self.args and self.args.loglevel:
            fh.setLevel(int(self.args.loglevel))

        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def poll(self):
        self.ser.write(poll_args['sig'])
        self.ser.flush()
        poll_args['unrequited_messages'] += 1
        self.logger.debug("Polling arduino: {}".format(poll_args['unrequited_messages']))

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
                self.alerts.send_alerts(json_ob['Poll'])
            if 'Event' in json_ob:
                self.mc.event_insert(json_ob['Event'])
        except pymongo.errors.ConnectionFailure as cf:
            self.logger.error('Connection Failure: {0}'.format(cf))
        except pymongo.errors.ConfigurationError as ce:
            self.logger.error('Configuration Error: {0}'.format(ce))

    def start_eve(self):
        from .eveserve import EveServer
        e = EveServer(mongoclient=self.mc._client, name=self.mc._db)
        e.app.logger.addHandler(self.fh)
        e.app.logger.addHandler(self.ch)
        t = Thread(target=e.eve_start, args=(), name=e.eve_start, daemon=True)
        t.start()

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--eve', help='expose resources via REST api',
                        action='store_true')
    parser.add_argument('-l', '--loglevel', help='set log level')
    parser.add_argument('-v', '--verbose', help='set verbosity')
    return parser.parse_args()

def start():
    f = Fmon(args=args())

    if f.args and f.args.eve:
        f.start_eve()

    f.poll_loop()
    f.listen()

if __name__ == "__main__":
    start()
