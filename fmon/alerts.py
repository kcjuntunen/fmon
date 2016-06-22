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
import logging
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
        """
        a_id should be an ObjecdID() from Mongo
        collection is a collection that contains the a_id
        """
        self.logger = logging.getLogger('Fmon')
        self._id = a_id
        self._collection = collection
        self._alert = self._collection.find_one({"_id": self._id})
        self.logger.debug('__init__: {}'.format(self.friendly_name))
        self.sent = False

    def get_val(self, field):
        """ Return this alert's values. """
        try:
            doc = self._collection.find_one({"_id": self._id})[field]
            if doc is not None:
                return doc
        except Exception as ex:
            self.logger.error("Problem with collection: {}".format(ex))
            self.logger.error("Couldn't find {}".format(field))

    @property
    def sensor(self):
        """ Name of sensor """
        return self.get_val('sensor')

    @property
    def friendly_name(self):
        """ A friendly name for the sensor """
        return self.get_val('friendly_name')

    @property
    def range(self):
        """ Range within which the alert is triggered. """
        return self.get_val('ltgt')

    @property
    def recipients(self):
        """ Array of recipients """
        return self.get_val('recipients')

    @property
    def active(self):
        """ Is the alert turned on or off? """
        return self.get_val('active')

    @property
    def message(self):
        """ 
        An HTML email message to send in the event of an alert.
        There should be four fields in the format string.
        send_email is going to pass the time, location, fixure name, and
        raw value to __format__.
        """
        return self.get_val('msg')

    @property
    def limits(self):
        """
        Returns a dictionary:
        'days' is a binary field. An example: 0b1111100 = M-F
        'daystart' and 'dayend' are each minutes after midnight. Between them,
        sending is allowed.
        """
        return self.get_val('limits')

    @property
    def ok_to_send(self):
        """ Check to see if it's a good day and time for email. """
        dow = datetime.today().weekday()
        nw = datetime.now()
        t = float((nw.hour * 60) + nw.minute)

        if self.sent:
            return False
    
        return (self.agreeable_day(dow) and
                self.within_workday(t))

    def agreeable_day(self, day_of_week):
        """ 
        Looking for a datetime.today().weekday() to compare bitwise
        against allowed days from the config data.
        """
        dayval = DAYS[day_of_week]
        return (int(self.limits['days']) & dayval) > 0

    def within_workday(self, minute_of_day):
        """
        Looking for the minute of day past 00:00 to compare against
        an allowed range in the config file.
        """
        if (minute_of_day > self.limits['daystart'] and
            minute_of_day < self.limits['dayend']):
            return True
        return False

    def transgressing_range(self, dict_ob):
        return ((dict_ob[self.sensor] < self.range[0]) and
               (dict_ob[self.sensor] > self.range[1])) and self.active

    # def __eq__(self, other):
    #     return (self.sensor == other.sensor &
    #             self.range == other.range &
    #             self.recipients == other.recipients &
    #             self.limits == other.limits)

    def __repr__(self):
        return ("<sensor:{!r}, range: {!r}, recipients: {!r}>"
                .format(self.sensor, self.range, self.recipients))

    def __str__(self):
        return "{} alert".format(self.friendly_name)

class Alerts():
    def __init__(self, DbClass, config):
        self.logger = logging.getLogger('Fmon')
        self.logger.debug('Alerts.__init__')
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
            rnge = alert.range.sort()
            if (value < rnge[0] and
                value > rnge[1] and
                alert.active):
                return True
            return False

    def send_alerts(self, json_ob):
        emailconf = self._config.email_data
        nw = datetime.now().strftime('%H:%M %B %d, %Y')
        for alert in self.alert_list:
            self.logger.debug('({}).sent is set to {}'.
                              format(alert.split(' ')[0], alert.sent))
            if alert.transgressing_range(json_ob):
                self.logger.debug('send_alerts: {} transgressing'.
                                  format(alert))
                if alert.ok_to_send:
                    self.logger.debug('send_alerts: ok_to_send')
                    alert.sent = True
                    msg = str(alert.message).format(nw,
                                                    self._config.location,
                                                    self._config.fixture,
                                                    json_ob[alert.sensor])
                    send_email(emailconf['server'], emailconf['sender'],
                               emailconf['passwd'], alert.recipients,
                               str(alert), msg)
            else:
                self.logger.debug('send_alerts: {} not transgressing'.
                                  format(alert))
                alert.sent = False
