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
        return output

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
