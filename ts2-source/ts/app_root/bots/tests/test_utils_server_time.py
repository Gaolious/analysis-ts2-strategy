from unittest import mock

import pytest

from app_root.bots.utils_server_time import ServerTimeHelper
from core.utils import create_datetime as dt


@pytest.mark.parametrize('ret_time, now, diff, expected_curr_time', [
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 0, 1), -0.000001, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 8, 59, 59, 999999), 0.000001, '2022-12-29T00:00:00.000Z'),

    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00.000Z'),

    ('2022-12-29T00:00:00', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00.000Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00.000Z'),
])
def test_utils_server_time_helper(ret_time, now, diff, expected_curr_time):
    helper = ServerTimeHelper()

    server_resp_datetime = helper.convert_strtime_to_datetime(ret_time)
    helper.adjust_time(server_datetime=server_resp_datetime, now=now)

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        assert abs(helper.offset_ms - diff) < 0.1**6
        assert helper.get_curr_time() == expected_curr_time


@pytest.mark.parametrize('ret_time, now, diff, expected_curr_time', [
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 0, 1), -0.000001, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 8, 59, 59, 999999), 0.000001, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00Z'),
])
def test_utils_server_time_helper_ymdhis(ret_time, now, diff, expected_curr_time):
    helper = ServerTimeHelper()

    server_resp_datetime = helper.convert_strtime_to_datetime(ret_time)
    helper.adjust_time(server_datetime=server_resp_datetime, now=now)

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        assert abs(helper.offset_ms - diff) < 0.1**6
        assert helper.get_curr_time_ymdhis() == expected_curr_time


@pytest.mark.parametrize('ret_time, now, diff, expected_curr_time', [
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 0, 1), -0.000001, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00.000Z', dt(2022, 12, 29, 8, 59, 59, 999999), 0.000001, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00Z', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 9, 0, 0), 0, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 9, 0, 1), -1, '2022-12-29T00:00:00.000000Z'),
    ('2022-12-29T00:00:00', dt(2022, 12, 29, 8, 59, 59), 1, '2022-12-29T00:00:00.000000Z'),
])
def test_utils_server_time_helper_micro(ret_time, now, diff, expected_curr_time):
    helper = ServerTimeHelper()

    server_resp_datetime = helper.convert_strtime_to_datetime(ret_time)
    helper.adjust_time(server_datetime=server_resp_datetime, now=now)

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        assert abs(helper.offset_ms - diff) < 0.1**6
        assert helper.get_curr_time_micro() == expected_curr_time
