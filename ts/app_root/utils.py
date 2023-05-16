from datetime import datetime, timedelta

import pytz
from django.utils import timezone

from app_root.servers.models import RunVersion


def get_curr_server_datetime(version: RunVersion) -> datetime:
    return version.now.astimezone(pytz.utc)


def get_curr_server_str_datetime_s(version: RunVersion) -> str:
    """
    "2023-01-17T04:09:17Z"

    :param self:
    :return:
    """
    return (
        get_curr_server_datetime(version=version)
        .isoformat(sep="T", timespec="seconds")
        .replace("+00:00", "Z")
    )


def get_curr_server_str_datetime_ms(version: RunVersion) -> str:
    """
    "2023-01-17T04:09:17.207Z"
    :param version:
    :return:
    """
    return (
        get_curr_server_datetime(version=version)
        .isoformat(sep="T", timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def get_curr_server_str_datetime_us(version: RunVersion) -> str:
    """
    "2023-01-17T04:09:17.207123Z"

    :param self:
    :return:
    """
    return (
        get_curr_server_datetime(version=version)
        .isoformat(sep="T", timespec="microseconds")
        .replace("+00:00", "Z")
    )


def get_remain_time(version: RunVersion, finish_at: datetime) -> str:
    if finish_at:
        remain = int((finish_at - version.now).total_seconds())
        flag = " "
        if remain < 0:
            remain = -remain
            flag = "-"

        hours, rem = divmod(remain, 3600)
        minutes, seconds = divmod(rem, 60)
        if hours > 99:
            hours, minutes, seconds = 99, 99, 99
        return f"""{flag}{hours:02d}:{minutes:02d}:{seconds:02d}"""
    return " --:--:--"
