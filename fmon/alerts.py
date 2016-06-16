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
from collections import namedtuple

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

class Alerts():
    def __init__(self, DbClass):
        self.__alerts = DbClass.alerts
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

from enum import Enum
class AlertFields(Enum):
    SENSOR = 0
    RANGE = 1
    RECIPIENTS = 2
    ACTIVE = 3
    MESSAGE = 4
