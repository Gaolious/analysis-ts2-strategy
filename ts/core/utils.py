"""
    core > utils
    
    전역으로 사용되는 함수들 모음
"""
import codecs
import csv
import hashlib
import json
import logging
import re
import string
import sys
import time
import unicodedata
from datetime import timedelta, datetime
from decimal import Decimal
from math import floor
from pathlib import Path
import random
from typing import Type, Generator, List
from unicodedata import normalize

import requests
from django.conf import settings
from django.utils import timezone
import zipfile
import pytz
from dateutil import parser

trim_chars_pattern = re.compile(r'(\s*)')
date_pattern = re.compile(r'\d{1,4}-\d{1,2}-\d{1,2}')
number_pattern = re.compile(r'[^0-9\-\.]')

_logger = logging.getLogger('default')

class Logger(object):

    @classmethod
    def make_message(cls, menu, action, **kwargs):
        kwargs.update({
            'menu': str(menu or ''),
            'action': str(action or ''),
        })
        return json.dumps(kwargs)

    @classmethod
    def debug(cls, menu, action, **kwargs):
        msg = cls.make_message(menu, action, **kwargs)
        if msg:
            _logger.log(logging.DEBUG, msg)

    @classmethod
    def info(cls, menu, action, **kwargs):
        msg = cls.make_message(menu, action, **kwargs)
        if msg:
            _logger.log(logging.INFO, msg)

    @classmethod
    def warn(cls, menu, action, **kwargs):
        msg = cls.make_message(menu, action, **kwargs)
        if msg:
            _logger.log(logging.WARN, msg)

    @classmethod
    def error(cls, menu, action, **kwargs):
        msg = cls.make_message(menu, action, **kwargs)
        if msg:
            _logger.log(logging.ERROR, msg)

    @classmethod
    def critical(cls, menu, action, **kwargs):
        msg = cls.make_message(menu, action, **kwargs)
        if msg:
            _logger.log(logging.CRITICAL, msg)



def retry(times: int, delay: float, exceptions: Type[Exception]):
    """
    exceptions의 예외 발생시 재시도

    Args:
        times: N 회
        delay: N 초
        exceptions: (Exception, Exception, ...)

    Returns:
        nothing.

    Examples:

        @retry(3, 0.1, Exception)
        def test_function():
            pass

        @retry(3, 0.1, (Exception1, Exception2) )
        def test_function():
            pass

    """

    def decorator(func):
        def caller(*args, **kwargs):
            attempt = 0

            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    print(f"Retry #{attempt} Exception : {e}")
                    time.sleep(delay)

            return func(*args, **kwargs)

        return caller

    return decorator


def hash10(text):
    """

    Args:
        text:

    Returns:

    """
    MAX_INT = 9223372036854775808  # 2^63
    if not isinstance(text, str):
        text = ''
    try:
        text = bytes(text, 'utf-8')
        m = hashlib.md5(text)
        # max 2**64 and modular with 2**63
        return int(m.hexdigest(), 16) % MAX_INT
    except:
        pass

    return 0


class FailedDownloadFile(Exception):
    """
    file download 실패 exception
    """
    message = ''

    def __init__(self, url, ret_status):
        self.message = f'Failed to download "{url}" with status_code={ret_status}'

    def __str__(self):
        return self.message


@retry(times=3, delay=0.1, exceptions=FailedDownloadFile)
def download_file(url: str, download_filename: Path):
    """
    url을 download_to 에 다운로드

    Args:
        url: url
        download_filename: download path

    Returns:
        downloaded file size
    """

    chunk = 2048

    path = download_filename.parent
    if not path.exists():
        path.mkdir(0o755, True, True)

    with requests.Session() as session:
        resp = session.get(url, stream=True)

        if resp.status_code == 200:
            with open(download_filename, 'wb') as f:
                for data in resp.iter_content(chunk):
                    f.write(data)
                file_size = f.tell()
                f.close()
        else:
            raise FailedDownloadFile(url=url, ret_status=resp.status_code)

        return file_size

    raise FailedDownloadFile(url=url, ret_status=-1)


@retry(times=3, delay=0.1, exceptions=FailedDownloadFile)
def download_file_with_post_data(*, url: str, headers, payload, params, cookies, timeout, download_filename: Path):
    """
    url을 download_to 에 다운로드

    Args:
        url: url
        download_filename: download path

    Returns:
        downloaded file size
    """

    chunk = 2048

    path = download_filename.parent
    if not path.exists():
        path.mkdir(0o755, True, True)

    with requests.Session() as session:
        session.headers = headers

        resp = session.post(
            url=url,
            data=payload,
            headers=headers,
            timeout=timeout,
            cookies=cookies or {},
            params=params or {},
            stream=True,
            verify=False,
        )
        if resp.status_code == 200:
            with open(download_filename, 'wb') as f:
                for data in resp.iter_content(chunk):
                    f.write(data)
                file_size = f.tell()
                f.close()
        else:
            raise FailedDownloadFile(url=url, ret_status=resp.status_code)

        return file_size

    raise FailedDownloadFile(url=url, ret_status=-1)


@retry(times=3, delay=0.1, exceptions=FailedDownloadFile)
def download_file_with_get_param(*, url: str, headers, payload, params, cookies, timeout, download_filename: Path):
    """
    url을 download_to 에 다운로드

    Args:
        url: url
        download_filename: download path

    Returns:
        downloaded file size
    """

    chunk = 2048

    path = download_filename.parent
    if not path.exists():
        path.mkdir(0o755, True, True)

    with requests.Session() as session:
        session.headers = headers

        resp = session.get(
            url=url,
            data=payload,
            headers=headers,
            timeout=timeout,
            cookies=cookies or {},
            params=params or {},
            stream=True,
            verify=False,
        )
        if resp.status_code == 200:
            with open(download_filename, 'wb') as f:
                for data in resp.iter_content(chunk):
                    f.write(data)
                file_size = f.tell()
                f.close()
        else:
            raise FailedDownloadFile(url=url, ret_status=resp.status_code)

        return file_size

    raise FailedDownloadFile(url=url, ret_status=-1)


# def filename_to_utf8(filename: str):
#     try:
#         filename = filename.encode('cp437').decode('cp949')
#     except Exception as e:
#         pass
#
#     filename = normalize("NFC", filename)
#
#     return filename
#
#
# def uncompress_zipfile(filename: Path, extract_to: Path):
#     with zipfile.ZipFile(filename, 'r') as instance:
#         zipInfo = instance.infolist()
#
#         for member in zipInfo:
#             member.filename = filename_to_utf8(member.filename)
#             instance.extract(member, extract_to)
#     return True

#
# def uncompress_7z(filename: Path, extract_to: Path):
#     with py7zr.SevenZipFile(filename, 'r') as instance:
#         #
#         # for member in instance.files:
#         #     member.filename = filename_to_utf8(member.filename)
#         instance.extractall(extract_to)
#     return True


# def uncompress_file(filename: Path, extract_to: Path):
#     if not extract_to.exists():
#         extract_to.mkdir(0o755, True, True)
#
#     if filename.suffix == '.zip':
#         return uncompress_zipfile(filename, extract_to)
#     # elif filename.suffix == '.7z':
#     #     return uncompress_7z(filename, extract_to)
#
#     return True


class YearMonthHelper(object):
    """
        Year Month Helper
    """

    @classmethod
    def first_day(cls, year, month):
        now = timezone.now().astimezone(settings.KST).replace(
            year=year, month=month, day=1
        )
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @classmethod
    def last_day(cls, year, month):
        if month == 12:
            first_datetime_of_next_month = cls.first_day(year + 1, 1)
        else:
            first_datetime_of_next_month = cls.first_day(year, month + 1)

        return first_datetime_of_next_month + timedelta(microseconds=-1)

    @classmethod
    def add_month_firstday(cls, year, month, delta_month):

        if delta_month != 0:
            m = month + delta_month - 1
            delta_year = m // 12
            year += delta_year
            m -= delta_year * 12

            month = m + 1

        return cls.first_day(year=year, month=month)

    @classmethod
    def is_last_date(cls, date):
        return cls.last_day(date.year, date.month).date() == date

    @classmethod
    def add_month_lastday(cls, year, month, delta_month):

        if delta_month != 0:
            m = month + delta_month - 1
            delta_year = m // 12
            year += delta_year
            m -= delta_year * 12

            month = m + 1

        return cls.last_day(year=year, month=month)


def extract_hangul(s: str):
    ret = re.compile('[가-힣|ㄱ-ㅎ|ㅏ-ㅣ]+').findall(s)
    return ''.join(ret)


def convert_trim(text: str, default=None):
    """
    '\n', '\r', '\t', '\b', ' ', '\u200b'(zero space width) 요소를 제거합니다.
    Args:
        text:
        default:

    Returns:
        str: trim text

    Tests:
        text_strip_pattern = re.compile(r'[\n\r\t\b\ \u200b]', re.UNICODE)

        def fn_replace(text: str):
            pattern = r'\n\r\t\b\ \u200b'
            for p in pattern:
                text = text.replace(p, '')
            return text


        def fn_regex(text: str):
            return text_strip_pattern.sub('', text)

        >>> timeit.timeit(stmt=lambda: fn_replace(text), number=1000000 )
        11.80325703699998

        >>> timeit.timeit(stmt=lambda: fn_regex(text), number=1000000 )
        31.42367754700001

    """
    try:
        pattern = '\n\r\t\b\ \u200b'

        if not isinstance(text, str):
            text = str(text)

        for p in pattern:
            text = text.replace(p, '')
        return text
    except:
        pass

    return default


# def convert_text(text: str, default=None):
#     """
#         text 반환.
#     Args:
#         text:
#         default:
#
#     Returns:
#
#     """
#     try:
#         return ' '.join(
#             a for a in text.strip('\r\n\t\ \u200b\ufeff').replace('\xa0', ' ').split() if a
#         )
#     except Exception:
#         pass
#
#     return default


def convert_date(text: str, default=None) -> datetime.date:
    """

    Args:
        text:
        default:

    Returns:

    """
    try:
        text = trim_chars_pattern.sub('', text)
        text = convert_trim(text, default)
        text = text.replace('.', '-').replace('\xa0', '')
        try:
            if '-' not in text and len(text) == 8 and str(int(text)) == text:
                text = f'{text[:4]}-{text[4:6]}-{text[6:8]}'
        except:
            pass

        search = date_pattern.search(text)
        if not search:
            return default

        group = search.group()
        if not group:
            return default

        year, month, day = tuple(map(int, group.split('-')))

        return settings.KST.localize(
            datetime(
                year=year,
                month=month,
                day=day,
            )
        ).date()

    except Exception as e:
        pass

    return text


def convert_datetime(str_datetime: str, default=None):
    try:
        server_resp_datetime = parser.parse(timestr=str_datetime)

        if not server_resp_datetime.tzinfo:
            server_resp_datetime = server_resp_datetime.replace(tzinfo=pytz.utc)

        return server_resp_datetime
    except:
        pass

    return default


def convert_time(text: str, default=None) -> int:
    """

    Args:
        text:
        default:

    Returns:

    """

    try:
        text = trim_chars_pattern.sub('', text)
        text = convert_trim(text, default)

        ret = text.split(':')
        h, m, s = tuple(map(int, ret))
        return ((h * 60) + m) * 60 + s

    except Exception as e:
        pass

    return default


def convert_number_as_string(text: str, default=None):
    """
        숫자로 구성된 문자열
    Args:
        text:
        default:

    Returns:

    """
    try:
        text = number_pattern.sub('', text)
        text = convert_trim(text, default).replace('.', '').replace('-', '').replace(',', '')
        if text:
            return text

    except Exception:
        pass

    return default


# def convert_number_as_decimal(text: str, default=None):
#     try:
#         num = Decimal(str(text))
#         if num.is_finite():
#             return num
#     except:
#         pass
#
#     return default


def convert_number_as_int(text: str, default=None):
    """
        숫자 반환.
    Args:
        text:
        default:

    Returns:

    """
    try:
        return int(convert_number_as_string(str(text), default))

    except Exception:
        pass

    return default


def convert_bool(text: str, default=None):
    """
        숫자 반환.
    Args:
        text:
        default:

    Returns:

    """
    T = {'1', 'T', 'TRUE', 'Y'}
    F = {'0', 'F', 'FALSE', 'N'}
    try:
        ut = str(text).upper()
        if ut in T:
            return True
        if ut in F:
            return False
    except Exception:
        pass

    return default


def convert_money(text: str, unit: int = 1, default=None):
    """
        문자열을 금액으로 반환.
    Args:
        text: 문자열 금액
        unit: 단위
        default:

    Returns:

    """
    try:
        val = convert_trim(text, default).split('.')

        if len(val) <= 2:
            val[0] = val[0].replace(',', '')
            return int(val[0]) * unit

    except Exception:
        pass

    return default


def create_datetime(y=0, m=0, d=0, h=0, i=0, s=0, us=0):
    """
        KST datetime 생성

    Args:
        y: year
        m: month
        d: day
        h: hour
        i: minute
        s: second
        us: microsecond

    Returns:
        datetime: datetime with KST timezone

    """
    ret = datetime(year=y, month=m, day=d, hour=h, minute=i, second=s, microsecond=us)
    return settings.KST.localize(ret)

#
# def human_filesize(num, suffix="B"):
#     for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
#         if abs(num) < 1024.0:
#             return f"{num:3.1f}{unit}{suffix}"
#         num /= 1024.0
#     return f"{num:.1f} Yi{suffix}"

def short_name(msg, msg_len):
    msg = str(msg) if msg else ''
    if len(msg) > msg_len:
        if msg_len > 3:
            msg = msg[:msg_len-3] + '...'
        else:
            msg = msg[:msg_len]
    format = '{' + ':' + str(msg_len) + 's}'
    return format.format(msg)

def human_days(seconds):
    if seconds <= 0:
        future = '전'
        seconds = -seconds
    else:
        future = '후'

    unit = [1, 60, 60, 24, 30, 12]
    suffix = ['초', '분', '시간', '일', '개월', '년']

    ret = ''
    for u, s in zip(unit, suffix):
        if seconds >= u:
            seconds /= u
            ret = '{0}{1} {2}'.format(int(seconds), s, future)
        else:
            break

    return ret


if settings.DEBUG and 'conf.settings.local' in settings.SETTINGS_MODULE and "pytest" not in sys.modules:
    def disk_cache(prefix, smt):
        def decorator(func):
            def caller(*args, **kwargs):
                # return func(*args, **kwargs)
                name = smt.format(**kwargs)

                path = settings.SITE_PATH / 'disk_cache' / prefix
                if not path.exists():
                    path.mkdir(0o755, True, True)

                name = unicodedata.normalize('NFKC', name)
                filepath = path / name

                if not filepath.exists():
                    ret = func(*args, **kwargs)
                    if ret:
                        filepath.write_text(ret, encoding='utf-8')
                    else:
                        return ret
                return filepath.read_text(encoding='utf-8')

            return caller

        return decorator
else:
    def disk_cache(*args, **kwargs):
        def decorator(func):
            def caller(*args, **kwargs):
                return func(*args, **kwargs)

            return caller

        return decorator

