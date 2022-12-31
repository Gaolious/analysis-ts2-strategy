from datetime import timedelta, datetime

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

    def convert_strtime_to_datetime(self, str_datetime):

        server_resp_datetime = parser.parse(timestr=str_datetime)
        if not server_resp_datetime.tzinfo:
            server_resp_datetime = server_resp_datetime.replace(tzinfo=pytz.utc)
        return server_resp_datetime
    
    def adjust_time(self, server_datetime: datetime, now):
        if server_datetime.year >= 2022:
            diff = (server_datetime - now).total_seconds()

            if abs(self.offset_ms) < 0.1**6 or abs(self.offset_ms) > abs(diff):
                self.offset_ms = diff

    def get_curr_time(self):
        return (timezone.now() + timedelta(seconds=self.offset_ms)).astimezone(pytz.utc).isoformat(sep='T', timespec='milliseconds').replace('+00:00', 'Z')

