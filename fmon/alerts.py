"""
Email etc. alerts
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
from fmon.emailer import send_email
from fmon.fmon import logging
from datetime import datetime
import json

DAYS = { 0: 0x40,  # Monday
         1: 0x20,  # Tuesday
         2: 0x10,  # Wednesday
         3: 0x8,   # Thursday
         4: 0x4,   # Friday
         5: 0x2,   # Saturday
         6: 0x1 }  # Sunday

class Alert():
    def __init__(self, a_id, collection):
        logger = logging.getLogger('Fmon')
        self._id = a_id
        self._collection = collection
        self._alert = self._collection.find_one({"_id": self._id})
        self.sent = False

    def get_val(self, field):
        """ Return this alert's values. """
        try:
            doc = self._collection.find_one({"_id": self._id})[field]
            return doc
        except Exception as ex:
            print(ex.args)

    @property
    def sensor(self):
        return self.get_val('sensor')

    @property
    def range(self):
        return self.get_val('ltgt')

    @property
    def recipients(self):
        return self.get_val('recipients')

    @property
    def active(self):
        return self.get_val('active')

    @property
    def message(self):
        return self.get_val('msg')

    @property
    def limits(self):
        return self.get_val('limits')

    @property
    def ok_to_send(self):
        dow = datetime.today().weekday()
        nw = datetime.now()
        t = float((nw.hour * 60) + nw.minute)
        return (self.agreeable_day(dow) and
                self.within_range(t) and
                not self.sent)

    def agreeable_day(self, day_of_week):
        dayval = DAYS[day_of_week]
        return (int(self.limits['days']) & dayval) > 0

    def within_range(self, minute_of_day):
        if (minute_of_day > self.limits['daystart'] and
            minute_of_day < self.limits['dayend']):
            return True
        return False

    def __repr__(self):
        return "{} alert".format(self.sensor)

class Alerts():
    def __init__(self, DbClass, config):
        self.__alerts = DbClass.alerts
        self._config = config
        self._alerts = None
        self._count = 0
        if self._alerts is None:
            a = set()
            for alert_id in self.__alerts.find({}):
                a.add(Alert(alert_id["_id"], self.__alerts))
                self._count += 1
                self._alerts = a

    @property
    def alert_list(self):
        return self._alerts

    def __len__(self):
        return self._count

    def __iter__(self):
        for alert in self.alert_list:
            yield alert

    def __repr__(self):
        return 'Alerts: {} items'.format(self._count)

    def check_alerts(self, alert, value):
        if alert is not None:
            if (value < alert.range[0] and
                value > alert.range[1] and
                alert.active):
                return True
            return False

    def send_alerts(self, json_ob):
        emailconf = self._config.email_data
        nw = datetime.now().strftime('%H:%M %B %d, %Y')
        for alert in self.alert_list:
            if (json_ob[alert.sensor] < alert.range[0] and
                json_ob[alert.sensor] > alert.range[1] and
                alert.active and alert.ok_to_send):
                msg = str(alert.message).format(nw, self._config.location,
                                                self._config.fixture,
                                                json_ob[alert.sensor])
                send_email(emailconf['server'], emailconf['sender'],
                           emailconf['passwd'], alert.recipients,
                           str(alert), msg)
                alert.sent = True
