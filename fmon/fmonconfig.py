"""
Conveniently return config items as properties.
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

class FMonConfiguration():
    def __init__(self, DbClass):
        self._config_data = DbClass.config_data

    @property
    def config(self):
        return self._config_data.find_one() 
        
    @property
    def port(self):
        return self.config['serial']['port']

    @property
    def baudrate(self):
        return int(self.config['serial']['baudrate'])

    @property
    def sensors(self):
        return self.config['sensors']

    @property
    def email_data(self):
        return self.config['email']

    @property
    def email_server(self):
        return self.email_data['server']
    
    @property
    def email_sender(self):
        return self.email_data['sender']

    @property
    def email_passwd(self):
        return self.email_data['passwd']

    @property
    def email_recipients(self):
        return self.email_data['recipients']

