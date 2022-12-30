from unittest import mock

import pytest

from app_root.bot.utils_server_time import ServerTimeHelper
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

    helper.adjust_time(ret_time=ret_time, now=now)

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        assert abs(helper.offset_ms - diff) < 0.1**6
        assert helper.get_curr_time() == expected_curr_time
