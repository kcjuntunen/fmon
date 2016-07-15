#!/usr/bin/env python3
import json, urllib, http.client, sched, time
import query, mongoconnection, fmonconfig
from emailer import TagStripper


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
            self.conf = fmonconfig.FMonConfiguration(mc)
            self.client = query.ArduinoLog()
            self.s = sched.scheduler(time.time, time.sleep)

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
        
        # In [7]: for x in al.ts_sensors:
        #    ...:     print(x, al.last_value(x))

        try:
            params = self.create_url(
                {k: self.client.last_value(k) for k in self.client.ts_sensors})
            
            headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}
            conn = http.client.HTTPConnection('api.thingspeak.com:80')
            conn.request('POST', '/update', params, headers)
            
            response = conn.getresponse()
            data = response.read()
            
            conn.close()
            #print(params)
            self.s.enter(self.timespec, 1, self.send_data, ())
        except http.client.HTTPException as he:
            self.s.enter(300, 1, self.send_data, ())
            return False, str(he)
        except Exception as e:
            self.s.enter(300, 1, self.send_data, ())
            return False, str(e)

    def start_loop(self):
        self.s.enter(5, 1, self.send_data, ())
        self.s.run()


def start(config_file):
    thsp = ThingspeakInterface(config_file)
    thsp.start_loop()

if __name__ == "__main__":
    import sys
    start(sys.argv[1])