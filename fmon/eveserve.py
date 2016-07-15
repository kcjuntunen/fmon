#!/usr/bin/env python3

import sys
import logging
from fmon import query
from eve import Eve
from threading import Thread, Timer
from datetime import datetime

app = Eve()
al = query.ArduinoLog()

@app.route('/sensors')
def sensor_list():
    return '\n'.join(al.all_sensors)

@app.route('/sensorcount')
def sensor_count():
    return str(len([x for x in al.all_sensors]))

@app.route('/lastreading/<sensor>')
def lastreading(sensor):
    if sensor in al.ts_sensors:
        return str(al.last_value(sensor))
    else:
        msg = 'Unacceptible sensors. Please try: ' + ', '.join(al.ts_sensors)
        code = xml_wrap('code', '406')
        message = xml_wrap('message', msg)
        xmlerr = xml_wrap('_error', code + message)
        status = xml_wrap('_status', 'ERR')
        output =  xml_wrap('resource', xmlerr + status)
        now = datetime.now()
        print(now)
        exp = datetime(now.year, now.month, now.day,
                       now.hour, now.minute, now.second + 20)
        print(exp)
        header = {
            'Content-Type': 'application/xml',
            'Content-Length': len(output),
            'Cache-Control': 'max-age=20',
            'Expires': exp,
            'Server': 'Eve/0.6.4 Werkzeug/0.11.3 Python/' + str(
                sys.version.split()[0]),
            'Date': now}
        h = ''
        for k in header:
            h += '{}: {}\n'.format(k, header[k])
        return '{}\n\n{}'.format(h, output)

def xml_wrap(tag, text):
    return '<' + tag + '>' + text + '</' + tag + '>'

def start_eve():
    logger = logging.getLogger('Fmon')
    logger.info('Starting Eve...')
    Thread(target=_start).start()

def _start():
    app.run(host='0.0.0.0', port=5000)
    
if __name__ == "__main__":
    start_eve()
