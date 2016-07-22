#!/usr/bin/env python3
import json, urllib, http.client, time
#from threading import Timer, Lock
import query, mongoconnection, fmonconfig
from pymongo.errors import PyMongoError
from sys import stderr, stdout
from emailer import TagStripper
from datetime import datetime

class ThingspeakInterface():

    def __init__(self, config_data_file):
        with open(config_data_file, 'r') as cfh:
            config_data = json.load(cfh)
            self.key = config_data['key']
            self.api_key = config_data['api_key']
            self.collection = 'timeseriesdata'
            self.timespec = config_data['thingspeak_freq']
            mc = mongoconnection.MongoConnection('localhost',
                                                 27017, '', '',
                                                 'arduinolog')
            self._client = query.ArduinoLog(db=mc._client, name='arduinolog')
            self.conf = fmonconfig.FMonConfiguration(mc)
            self._prev_dict = {}
            self.count = 0
            self.oldcount = 0

    def tweet(self, message):
        if self.api_key == '':
            return False

        ts = TagStripper()
        ts.feed(message)
        params = urllib.parse.urlencode(
            {'api_key': self.api_key,
             'status': ts.get_collected_data()})
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}
        conn = http.client.HTTPConnection('api.thingspeak.com:80')

        try:
            conn.request('POST',
                         '/apps/thingtweet/1/statuses/update',
                         params,
                         headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            return True, ts.get_collected_data()
        except http.client.HTTPException as he:
            return False, str(he)

    def create_datadict(self):
        data = {}
        for sensor in self._client.ts_sensors:
            url = 'http://localhost:5000/lastreading/{}'.format(sensor)
            conn = http.client.HTTPConnection('localhost:5000')
            try:
                conn.request('GET',
                             '/lastreading/{}'.format(sensor))
                res = conn.getresponse()
                d = res.read()
                conn.close()
                data[sensor] = float(d.decode('utf-8'))
            except http.client.HTTPException as he:
                print('HTTPConnection error: {}'.format(he), file=stderr)
        return data


    def create_url(self, data_dict):
        data = {}
        count = 1
        for field in [s['sensor'] for s in self.conf.sensors
                      if s['type'] == 'timeseries']:
            data['field' + str(count)] = data_dict[field]
            count += 1
            if count > 8:
                break

        data['key'] = self.key
        return urllib.parse.urlencode(data)

    def send_data(self):
        if self.key == '':
            return False
        self.count += 1
        lv = self._client.last_values()
        dd = {}
        #dd = {k: lv[k] for k in self._client.ts_sensors}
        for i in range(len(self._client.ts_sensors)):
            vs = lv[i]['values']
            dd[lv[i]['name']] = vs[len(vs) - 1]

        if dd == self._prev_dict:
            print('{:4d} ({}): old {:4d}'
                  ', {} cursor(s)'.format(self.count,
                                          datetime.now(),
                                          self.oldcount,
                                          '?'), file=stderr)
            #self.s.enter(self.timespec, 1, self.send_data, ())
            stderr.flush()
            self.oldcount += 1
            return self.oldcount < 5

        print('{:4d} ({}): new dict, {} cursor(s)'.format(self.count,
                                                          datetime.now(),
                                                          '?'))
        self._prev_dict = dd
        self.oldcount = 0

        try:
            params = self.create_url(dd)

            headers = {'Content-type': 'application/x-www-form-urlencoded',
                       'Accept': 'text/plain'}
            conn = http.client.HTTPConnection('api.thingspeak.com:80')
            conn.request('POST', '/update', params, headers)

            response = conn.getresponse()
            data = response.read()

            conn.close()
            #stdout.writelines(params)
            stdout.flush()
            return True
            #self.s.enter(self.timespec, 1, self.send_data, ())
        except http.client.HTTPException as he:
            #self.s.enter(300, 1, self.send_data, ())
            print(str(he), file=stderr)
            stderr.flush()
        except Exception as e:
            #self.s.enter(300, 1, self.send_data, ())
            print(str(e), file=stderr)
            stderr.flush()

    def start_loop(self):
        while True:
            try:
                if self.send_data():
                    time.sleep(self.timespec)
                else:
                    exit(0xFF)
            except PyMongoError as p:
                print('PyMongoError => {}'.format(p.args), file=stderr)
            except Exception as e:
                print('General Exception => {}'.format(str(e.args)), file=stderr)
                exit(0xff)

def start(config_file):
    thsp = ThingspeakInterface(config_file)
    thsp.start_loop()

if __name__ == "__main__":
    import sys
    start(sys.argv[1])
