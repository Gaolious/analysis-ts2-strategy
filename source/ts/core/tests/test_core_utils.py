import json
import os
import shutil
import timeit
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pytest

from core.utils import Logger, retry, hash10, download_file, YearMonthHelper, uncompress_file, extract_hangul, \
    convert_number_as_int, convert_number_as_string, convert_money, convert_date, convert_trim, create_datetime, \
    human_days, download_file_with_post_data, download_file_with_get_param


@pytest.mark.parametrize(
    'func', ['debug', 'info', 'warn', 'error', 'critical']
)
def test_logger(func):

    with patch('core.utils._logger') as mock:
        kwargs = {
            'menu': 'menu',
            'action': 'action',
            'kwargs': 1
        }
        caller = getattr(Logger, func)
        caller(request='request', **kwargs)

        assert mock.log.call_count == 1
        str_args = mock.log.call_args_list[0].args[1]

        assert json.loads(str_args) == kwargs


def test_retry_raise_exception():

    @retry(times=3, delay=0, exceptions=ZeroDivisionError)
    def fn():
        a = 1 / 0

    with pytest.raises(ZeroDivisionError):
        fn()


def test_retry_no_exception():

    data = []

    @retry(times=3, delay=0, exceptions=ZeroDivisionError)
    def fn(param):
        param.append(0)
        if len(param) == 3:
            return True
        else:
            return 1 / 0

    fn(data)


def test_retry_delay():

    @retry(times=3, delay=0.1, exceptions=ZeroDivisionError)
    def fn():
        return 1 / 0

    start = timeit.default_timer()
    with pytest.raises(ZeroDivisionError):
        fn()
    stop = timeit.default_timer()

    assert stop-start > 0.3


@pytest.mark.parametrize(
    'text, expected', [
        ('asdf', 2684434056780363120),
        ('가나다라', 1798796126228311480),
        ('1~][}{|+_-=`😁.,/?><가나-*/+', 6682807140857884430),
        ('None', 6099743825554519892),
        (None, 7602086723416769150),  # replace to ''
        ('', 7602086723416769150),
    ]
)
def test_hash10(text, expected):
    ret = hash10(text)

    assert ret > 0
    assert ret < 2**63
    assert ret == expected


@pytest.fixture(scope='function')
def fixture_session():
    with mock.patch('core.utils.requests.Session') as patch:
        yield patch


@pytest.mark.parametrize(
    'url, path', [
        ('https://www.juso.go.kr/dn.do?reqType=ALLRDNM&regYmd=2021&ctprvnCd=00&gubun=RDNM&stdde=202105&fileName=202105_%EA%B1%B4%EB%AC%BCDB_%EC%A0%84%EC%B2%B4%EB%B6%84.zip&realFileName=202105ALLRDNM00.zip&indutyCd=999&purpsCd=999&indutyRm=%EC%88%98%EC%A7%91%EC%A2%85%EB%A3%8C&purpsRm=%EC%88%98%EC%A7%91%EC%A2%85%EB%A3%8C', '/tmp/download.zip')
    ]
)
def test_download_all(url, path, fixture_session):
    class FakeResp():
        status_code = 200
        def iter_content(self, chunk):
            yield b'1'

    class FakeSession():
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get(self, *args, **kwargs):
            return FakeResp()

    fixture_session.side_effect = lambda: FakeSession()

    file_size = download_file(url=url, download_filename=Path(path))
    assert file_size == 1


@pytest.mark.parametrize(
    'url, path', [
        ('https://www.juso.go.kr/dn.do?reqType=ALLRDNM&regYmd=2021&ctprvnCd=00&gubun=RDNM&stdde=202105&fileName=202105_%EA%B1%B4%EB%AC%BCDB_%EC%A0%84%EC%B2%B4%EB%B6%84.zip&realFileName=202105ALLRDNM00.zip&indutyCd=999&purpsCd=999&indutyRm=%EC%88%98%EC%A7%91%EC%A2%85%EB%A3%8C&purpsRm=%EC%88%98%EC%A7%91%EC%A2%85%EB%A3%8C', '/tmp/download.zip')
    ]
)
def test_download_file_with_post_data(url, path, fixture_session):
    class FakeResp():
        status_code = 200
        def iter_content(self, chunk):
            yield b'1'

    class FakeSession():
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def post(self, *args, **kwargs):
            return FakeResp()

    fixture_session.side_effect = lambda: FakeSession()

    file_size = download_file_with_post_data(url=url, download_filename=Path(path), headers={}, payload={}, params={}, cookies={}, timeout=1)
    assert file_size == 1


@pytest.mark.parametrize(
    'url, path', [
        ('https://www.juso.go.kr/dn.do?reqType=ALLRDNM&regYmd=2021&ctprvnCd=00&gubun=RDNM&stdde=202105&fileName=202105_%EA%B1%B4%EB%AC%BCDB_%EC%A0%84%EC%B2%B4%EB%B6%84.zip&realFileName=202105ALLRDNM00.zip&indutyCd=999&purpsCd=999&indutyRm=%EC%88%98%EC%A7%91%EC%A2%85%EB%A3%8C&purpsRm=%EC%88%98%EC%A7%91%EC%A2%85%EB%A3%8C', '/tmp/download.zip')
    ]
)
def test_download_file_with_get_param(url, path, fixture_session):
    class FakeResp():
        status_code = 200
        def iter_content(self, chunk):
            yield b'1'

    class FakeSession():
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get(self, *args, **kwargs):
            return FakeResp()

    fixture_session.side_effect = lambda: FakeSession()

    file_size = download_file_with_get_param(url=url, download_filename=Path(path), headers={}, payload={}, params={}, cookies={}, timeout=1)
    assert file_size == 1


@pytest.mark.parametrize(
    'year, month, expect_year, expect_month, expect_day', [
        (2000, m, 2000, m, 1) for m in range(1, 12)
    ]
)
def test_year_month_helper_first_day(year, month, expect_year, expect_month, expect_day):
    dt = YearMonthHelper.first_day(year, month)
    assert dt.year == expect_year
    assert dt.month == expect_month
    assert dt.day == expect_day


@pytest.mark.parametrize(
    'year, month, expect_year, expect_month, expect_day', [
        (2000, 1, 2000, 1, 31),
        (2000, 2, 2000, 2, 29),
        (2000, 3, 2000, 3, 31),
        (2000, 4, 2000, 4, 30),
        (2000, 5, 2000, 5, 31),
        (2000, 6, 2000, 6, 30),
        (2000, 7, 2000, 7, 31),
        (2000, 8, 2000, 8, 31),
        (2000, 9, 2000, 9, 30),
        (2000, 10, 2000, 10, 31),
        (2000, 11, 2000, 11, 30),
        (2000, 12, 2000, 12, 31),
        (2001, 1, 2001, 1, 31),
        (2001, 2, 2001, 2, 28),
        (2001, 3, 2001, 3, 31),
        (2001, 4, 2001, 4, 30),
        (2001, 5, 2001, 5, 31),
        (2001, 6, 2001, 6, 30),
        (2001, 7, 2001, 7, 31),
        (2001, 8, 2001, 8, 31),
        (2001, 9, 2001, 9, 30),
        (2001, 10, 2001, 10, 31),
        (2001, 11, 2001, 11, 30),
        (2001, 12, 2001, 12, 31),
    ]
)
def test_year_month_helper_last_day(year, month, expect_year, expect_month, expect_day):
    dt = YearMonthHelper.last_day(year, month)
    assert dt.year == expect_year
    assert dt.month == expect_month
    assert dt.day == expect_day



@pytest.mark.parametrize(
    'year, month, delta_month, expect_year, expect_month', [
        (2000, 1, -13, 1998, 12),
        (2000, 1, -12, 1999, 1),
        (2000, 1, -1, 1999, 12),
        (2000, 1, 0, 2000, 1),
        (2000, 1, 1, 2000, 2),
        (2000, 1, 12, 2001, 1),
        (2000, 1, 13, 2001, 2),
    ]
)
def test_year_month_helper_add_month_firstday(year, month, delta_month, expect_year, expect_month):
    dt = YearMonthHelper.add_month_firstday(year, month, delta_month)
    assert dt.year == expect_year
    assert dt.month == expect_month

@pytest.mark.parametrize(
    'address, expected', [
        ('우 : 13911 경기도 안양시 만안구 예술공원로 164-1 (안양동)', '우경기도안양시만안구예술공원로안양동'),
        ('	우 : 33 rue du Puits Romain, Boite 6, L-8070 Bertrange, Luxembourg', '우'),
    ]
)
def test_extract_hangul(address, expected):

    ret = extract_hangul(address)

    assert ret == expected



@pytest.mark.parametrize(
    'in_data, default, expected', [
        ('a', None, 'a'),
        (' ', None, ''),
        (' a ', None, 'a'),
        ('\t\t\t\t\t\t\t\t\t\t\b a ', None, 'a'),
        (1, None, '1'),
        ('\n\r\t\b\ \u200b가\n\r\t\b\ \u200b나\n\r\t\b\ \u200b다\n\r\t\b\ \u200b라\n\r\t\b\ \u200b', None, '가나다라')
    ]
)
def test_convert_trim(in_data, expected, default):
    ret = convert_trim(text=in_data, default=default)

    assert ret == expected


@pytest.mark.parametrize(
    'in_data, default, expected', [
        ('', None, None),
        (' - - ', None, None),
        ('1-1-1', None, '1-1-1'),
        ('2000-01-01', None, create_datetime(2000, 1, 1).date()),
        ('2000-1-1', None, create_datetime(2000, 1, 1).date()),
        ('2000.01.01', None, create_datetime(2000, 1, 1).date()),
        ('2018\xa0 - \xa003\xa0 - \xa029', None, create_datetime(2018, 3, 29).date())
    ]
)
def test_convert_date(in_data, default, expected):
    ret = convert_date(text=in_data, default=default)

    assert ret == expected


@pytest.mark.parametrize(
    'in_data, default, expected', [
        ('', None, None),
        (' - - ', None, None),
        ('1-1-1', None, '111'),
        ('2000-01-01', None, '20000101'),
        ('2000-1-1', None, '200011'),
        ('2000.01.01', None, '20000101'),
        ('02  -  930  -  6665', None, '029306665'),
        ('02  -  6918  -  6152', None, '0269186152'),
    ]
)
def test_convert_number_as_string(in_data, default, expected):
    ret = convert_number_as_string(text=in_data, default=default)

    assert ret == expected


@pytest.mark.parametrize(
    'in_data, default, expected', [
        ('', None, None),
        (' - - ', None, None),
        ('1-1-1', None, 111),
        ('2000-01-01', None, 20000101),
        ('2000-1-1', None, 200011),
        ('2000.01.01', None, 20000101),
        ('02  -  930  -  6665', None, 29306665),
        ('02  -  6918  -  6152', None, 269186152),
    ]
)
def test_convert_number_as_int(in_data, default, expected):
    ret = convert_number_as_int(text=in_data, default=default)

    assert ret == expected


@pytest.mark.parametrize(
    'in_data, unit, default, expected', [
        ('', 10, None, None),
        (' - - ', 10, None, None),
        ('1-1-1', 10, None, None),
        ('2000-01-01', 10, None, None),
        ('2000-1-1', 10, None, None),
        ('2000.01.01', 10, None, None),
        ('02  -  930  -  6665', 10, None, None),
        ('02  -  6918  -  6152', 10, None, None),
        ('2000.010.020', 10, None, None),
        ('2000.010020', 10, None, 20000),
        ('2,000.010020', 10, None, 20000),
        ('2,000,010,020', 10, None, 20000100200),
    ]
)
def test_convert_money(in_data, unit, default, expected):
    ret = convert_money(text=in_data, unit=unit, default=default)

    assert ret == expected


@pytest.mark.parametrize(
    'seconds, expected', [
        (1, '1초 후'),
        (60, '1분 후'),
        (3600, '1시간 후'),
        (86400, '1일 후'),
        (2592000, '1개월 후'),
        (31104000, '1년 후'),
        (62208000, '2년 후'),
        (-1, '1초 전'),
        (-60, '1분 전'),
        (-3600, '1시간 전'),
        (-86400, '1일 전'),
        (-2592000, '1개월 전'),
        (-31104000, '1년 전'),
        (-62208000, '2년 전'),
    ]
)
def test_human_days(seconds, expected):
    assert human_days(seconds) == expected
