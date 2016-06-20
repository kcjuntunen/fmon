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
from datetime import datetime
import json

class Alert():
    def __init__(self, alert):
        self._alert = alert

    @property
    def sensor(self):
        return self._alert['sensor']

    @property
    def range(self):
        return self._alert['ltgt']

    @property
    def recipients(self):
        return self._alert['recipients']

    @property
    def active(self):
        return self._alert['active']

    @property
    def message(self):
        return self._alert['msg']

    @property
    def limits(self):
        return self._alert['limits']

    @property
    def ok_to_send(self):
        dow = datetime.today().weekday()
        nw = datetime.now()
        t = (nw.hour * 60) + nw.minute
        if (int(self.limits['days']) & dow) != dow:
            return False
        if (t > self.limits['daystart'] and
            t < self.limits['dayend']):
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
            a = []
            for alert in self.__alerts.find():
                a.append(Alert(alert))
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
        if self.alert_list[alert] is not None:
            if (value < self.alert_list[alert]['ltgt'][0] and
                value > self.alert_list[alert]['ltgt'][1] and
                self.alert_list[alert]['active']):
                return True
            return False

    def send_alerts(self, json_ob):
        emailconf = self._config.email_data
        for alert in self.alert_list:
            if (json_ob[alert.sensor] < alert.range[0] and
                json_ob[alert.sensor] > alert.range[1] and
                alert.active and alert.ok_to_send):
                send_email(emailconf['server'], emailconf['sender'],
                           emailconf['passwd'], alert.recipients,
                           str(alert), alert.message)
