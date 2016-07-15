#!/usr/bin/env python3

import logging
from fmon import query
from eve import Eve
from threading import Thread, Timer

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
        opening = """<html><head></head><body>"""
        closing = """</body></html>"""
        msg = ''.join((opening, '<h1>Error 406</h1>',
               'Bad sensor name.<br>Choose from:<ul><li>',
               '<li>'.join(al.ts_sensors),
               '</ul>',
               closing))
        return msg

def start_eve():
    logger = logging.getLogger('Fmon')
    logger.info('Starting Eve...')
    Thread(target=_start).start()

def _start():
    app.run(host='0.0.0.0', port=5000)
    
if __name__ == "__main__":
    start_eve()
