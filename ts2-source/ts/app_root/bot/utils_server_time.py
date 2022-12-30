from datetime import timedelta

import pytz
from dateutil import parser
from django.conf import settings
from django.utils import timezone


class ServerTimeHelper:
    """
        adjust local time via response of api
    """

    offset_ms: float  # additional microseconds for

    def __init__(self):
        self.offset_ms = 0.0
        self.endpoints = {}
        self.init_data_urls = []

    def adjust_time(self, ret_time: str, now):
        srv_time = parser.parse(ret_time)
        if not srv_time.tzinfo:
            srv_time = srv_time.replace(tzinfo=pytz.utc)

        if srv_time.year >= 2022:
            diff = (srv_time - now).total_seconds()

            if abs(self.offset_ms) < 0.1**6 or abs(self.offset_ms) > abs(diff):
                self.offset_ms = diff

    def get_curr_time(self):
        return (timezone.now() + timedelta(seconds=self.offset_ms)).astimezone(pytz.utc).isoformat(sep='T', timespec='milliseconds').replace('+00:00', 'Z')

