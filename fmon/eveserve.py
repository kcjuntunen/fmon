#!/usr/bin/env python3

import logging
from eve import Eve
from threading import Thread, Timer

def start_eve():
    logger = logging.getLogger('Fmon')
    logger.info('Starting Eve...')
    Thread(target=_start).start()

def _start():
    app = Eve()
    app.run(host='0.0.0.0', port=5000)
    
if __name__ == "__main__":
    start_eve()
