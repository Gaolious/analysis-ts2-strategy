from datetime import timedelta

import pytz
from dateutil import parser
from django.utils import timezone


class ServerTime:
    time_offset: timedelta

    def __init__(self):
        self.time_offset = timedelta(0)
        self.endpoints = {}
        self.init_data_urls = []

    def adjust_time(self, ret_time: str, now):
        new_offset = parser.parse(ret_time) - now

        if self.time_offset == timedelta(0) or self.time_offset > new_offset:
            self.time_offset = new_offset

    def get_curr_time(self):
        return (timezone.now() + self.time_offset).astimezone(pytz.utc).isoformat(sep='T', timespec='milliseconds').replace('+00:00', 'Z')

