from datetime import timedelta, datetime

import pytz
from django.utils import timezone

from core.utils import convert_datetime


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
        return convert_datetime(str_datetime)
    
    def adjust_time(self, server_datetime: datetime, now):
        if server_datetime.year >= 2022:
            diff = (server_datetime - now).total_seconds()

            if abs(self.offset_ms) < 0.1**6 or abs(self.offset_ms) > abs(diff):
                self.offset_ms = diff

    def get_curr_time(self) -> str:
        return self.get_curr_time_dt().isoformat(sep='T', timespec='milliseconds').replace('+00:00', 'Z')

    def get_curr_time_micro(self) -> str:
        return self.get_curr_time_dt().isoformat(sep='T', timespec='microseconds').replace('+00:00', 'Z')

    def get_curr_time_ymdhis(self) -> str:
        return self.get_curr_time_dt().isoformat(sep='T', timespec='seconds').replace('+00:00', 'Z')

    def get_curr_time_dt(self) -> datetime:
        return (timezone.now() + timedelta(seconds=self.offset_ms)).astimezone(pytz.utc)

