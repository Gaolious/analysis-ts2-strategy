import json
import uuid
from hashlib import md5
from typing import Dict, Tuple, Iterator

from django.conf import settings
from django.utils import timezone

from app_root.servers.models import RunVersion, EndPoint
from app_root.utils import get_curr_server_str_datetime_ms
from core.requests_helper import CrawlingHelper
from core.utils import Logger, convert_datetime, hash10


#######################################################
# Base Bot Helper
#######################################################
class ImportHelperMixin:
    """
        Bot Helper
    """
    HEADER_REQUEST_ID = 0x01 << 0
    HEADER_RETRY_NO = 0x01 << 1
    HEADER_SENT_AT = 0x01 << 2
    HEADER_CLIENT_INFORMATION = 0x01 << 3
    HEADER_CLIENT_VERSION = 0x01 << 4
    HEADER_DEVICE_TOKEN = 0x01 << 5
    HEADER_GAME_ACCESS_TOKEN = 0x01 << 6
    HEADER_PLAYER_ID = 0x01 << 7

    version: RunVersion

    def __init__(self, version: RunVersion, **kwargs):
        self.version = version

    def get_headers(self, *, mask) -> Dict[str, str]:

        client_info = json.dumps(
            {
                "Store": str(settings.CLIENT_INFORMATION_STORE),
                "Version": str(settings.CLIENT_INFORMATION_VERSION),
                "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
            },
            separators=(',', ':')
        )

        headers = {
            'PXFD-Sent-At': '0001-01-01T00:00:00.000',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
        }
        mapping = {
            self.HEADER_REQUEST_ID: ('PXFD-Request-Id', str(uuid.uuid4())),
            self.HEADER_RETRY_NO: ('PXFD-Retry-No', '0'),
            self.HEADER_SENT_AT: ('PXFD-Sent-At', get_curr_server_str_datetime_ms(version=self.version)),
            self.HEADER_CLIENT_INFORMATION: ('PXFD-Client-Information', client_info),
            self.HEADER_CLIENT_VERSION: ('PXFD-Client-Version', str(settings.CLIENT_INFORMATION_VERSION)),
            self.HEADER_DEVICE_TOKEN: ('PXFD-Device-Token', self.version.user.device_token),
            self.HEADER_GAME_ACCESS_TOKEN: ('PXFD-Game-Access-Token', self.version.user.game_access_token),
            self.HEADER_PLAYER_ID: ('PXFD-Player-Id', self.version.user.player_id),
        }

        for key, (field, value) in mapping.items():
            if mask & key:
                headers.update({field: value})
                assert value, f'in header, value of "{field}" is empty'

        return headers

    @classmethod
    def get(cls, url, headers, params):
        assert url
        assert headers
        Logger.info(
            menu=cls.__name__, action='Before GET',
            url=url, headers=headers
        )
        resp = CrawlingHelper.get(
            url=url,
            headers=headers,
            payload={},
            cookies={},
            params=params,
        )
        resp_status_code = resp.status_code
        resp_body = resp.content.decode('utf-8')
        resp_headers = {k: v for k, v in resp.headers.items()}
        resp_cookies = {k: v for k, v in resp.cookies.items()}

        Logger.info(
            menu=cls.__name__, action='After GET',
            status_code=str(resp_status_code),
            body=str(resp_body),
            headers=str(resp_headers),
            cookies=str(resp_cookies),
        )
        return resp_body

    @classmethod
    def post(cls, url, headers, payload):
        assert url
        assert headers

        Logger.info(
            menu=cls.__name__, action='Before POST',
            url=url, headers=headers
        )
        resp = CrawlingHelper.post(
            url=url,
            headers=headers,
            payload=payload,
            cookies={},
            params={},
        )
        resp_status_code = resp.status_code
        resp_body = resp.content.decode('utf-8')
        resp_headers = {k: v for k, v in resp.headers.items()}
        resp_cookies = {k: v for k, v in resp.cookies.items()}

        Logger.info(
            menu=cls.__name__, action='After POST',
            status_code=str(resp_status_code),
            body=str(resp_body),
            headers=str(resp_headers),
            cookies=str(resp_cookies),
        )
        return resp_body

    def get_data(self, url, **kwargs) -> str:
        raise NotImplementedError

    def parse_data(self, data, **kwargs) -> str:
        raise NotImplementedError

    def get_urls(self) -> Iterator[Tuple[str, str, str, str]]:
        """

        :return:
        """
        raise NotImplementedError

    def run(self):
        for url, req_field, server_field, resp_field in self.get_urls():
            update_fields = []
            if req_field:
                update_fields.append(req_field)
                setattr(self.version, req_field, timezone.now())
            data = self.get_data(url=url)

            if resp_field:
                update_fields.append(resp_field)
                setattr(self.version, resp_field, timezone.now())

            if data:
                ret_time = self.parse_data(data=data)

                server_resp_datetime = convert_datetime(ret_time)
                if server_field:
                    update_fields.append(server_field)
                    setattr(self.version, server_field, server_resp_datetime)

            if update_fields:
                self.version.save(update_fields=update_fields)


# class BaseCommand(object):
#     """
#         BaseCommand
#     """
#     COMMAND = ''
#     SLEEP_RANGE = (0.5, 1.5)
#
#     def get_parameters(self) -> dict:
#         return {}
#
#     def get_command(self):
#         self._start_datetime = self.helper.server_time.get_curr_datetime()
#
#         return {
#             'Command': self.COMMAND,
#             'Time': self.helper.server_time.get_curr_time_s(),
#             'Parameters': self.get_parameters()
#         }
#
#     def sleep(self):
#         self.helper._do_sleep(min_second=self.SLEEP_RANGE[0], max_second=self.SLEEP_RANGE[1])
#
#     def duration(self) -> int:
#         return 0
#
#     def end_datetime(self) -> datetime:
#         return self._start_datetime + timedelta(seconds=self.duration())
#
#     def __str__(self):
#         return f'''[{self.COMMAND}] / parameters: {self.get_parameters()}'''
#
#     def post_processing(self):
#         pass
