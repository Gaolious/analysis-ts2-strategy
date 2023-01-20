import json
import uuid
from hashlib import md5
from typing import Dict

from django.conf import settings
from django.utils import timezone

from app_root.servers.models import RunVersion, EndPoint
from core.requests_helper import CrawlingHelper
from core.utils import Logger, convert_datetime, hash10


#######################################################
# Base Bot Helper
#######################################################
class ImportHelperMixin:
    """
        Bot Helper
    """

    version: RunVersion
    FIELD_REQUEST_DATETIME = 'ep_sent'
    FIELD_SERVER_DATETIME = 'ep_server'
    FIELD_RESPONSE_DATETIME = 'ep_recv'

    def __init__(self, version: RunVersion):
        self.version = version

    def default_header(self) -> Dict[str, str]:
        client_info = {
            "Store": str(settings.CLIENT_INFORMATION_STORE),
            "Version": str(settings.CLIENT_INFORMATION_VERSION),
            "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
        }

        headers = {
            'PXFD-Request-Id': str(uuid.uuid4()),
            'PXFD-Retry-No': '0',
            'PXFD-Sent-At': '0001-01-01T00:00:00.000',
            'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
            'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
            'PXFD-Device-Token': md5(self.version.user.android_id.encode('utf-8')).hexdigest(),
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
        }
        return headers

    @classmethod
    def get(cls, url, headers, params):
        assert url
        assert headers
        Logger.info(
            menu=cls.__name__, action='BeforeRequest',
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
            menu=cls.__name__, action='AfterRequest',
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
            menu=cls.__name__, action='BeforeRequest',
            url=url, headers=headers
        )
        resp = CrawlingHelper.get(
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
            menu=cls.__name__, action='AfterRequest',
            status_code=str(resp_status_code),
            body=str(resp_body),
            headers=str(resp_headers),
            cookies=str(resp_cookies),
        )
        return resp_body

    def get_data(self) -> str:
        raise NotImplementedError

    def parse_data(self, data) -> str:
        raise NotImplementedError

    def run(self) -> bool:
        setattr(self.version, self.FIELD_REQUEST_DATETIME, timezone.now())
        data = self.get_data()
        setattr(self.version, self.FIELD_REQUEST_DATETIME, timezone.now())
        if data:
            ret_time = self.parse_data(data=data)

            server_resp_datetime = convert_datetime(ret_time)
            setattr(self.version, self.FIELD_SERVER_DATETIME, server_resp_datetime)

            self.version.save(
                update_fields=[
                    self.FIELD_REQUEST_DATETIME,
                    self.FIELD_SERVER_DATETIME,
                    self.FIELD_RESPONSE_DATETIME,
                ]
            )
            return True

        return False

    #
    # def _update_server_time(self, request_datetime, response_datetime, server_datetime):
    #     mid = (response_datetime - request_datetime)/2
    #     self.server_time.adjust_time(server_datetime=server_datetime, now=request_datetime + mid)
    #
    # def run(self, run_version, url, user: User, server_time: ServerTimeHelper):
    #     self.run_version = run_version
    #     self.user = user
    #     self.server_time = server_time
    #
    #     request_datetime = timezone.now()
    #     data = self.get_data(url=url)
    #     response_datetime = timezone.now()
    #     if data:
    #         ret_time = self.parse_data(data=data)
    #
    #         server_resp_datetime = self.server_time.convert_strtime_to_datetime(ret_time)
    #
    #         self._update_server_time(
    #             request_datetime=request_datetime,
    #             response_datetime=response_datetime,
    #             server_datetime=server_resp_datetime,
    #         )
    #
    # def parse_data(self, data) -> str:
    #     raise NotImplementedError
    #
    # def check_response(self, json_data):
    #     """
    #
    #     :param json_data:
    #     """
    #     success = json_data.get('Success')
    #
    #     if not success:
    #         error = json_data.get('Error')
    #         if error:
    #             msg = error.get('Message')
    #             err_msg = error.get('ErrorMessage')
    #             err_code = error.get('Code')
    #             param = {
    #                 'message': msg,
    #                 'error_message': err_msg,
    #                 'error_code': err_code
    #             }
    #             if err_msg == 'Invalid or expired session':
    #                 raise TsRespInvalidOrExpiredSession(**param)
    #             else:
    #                 raise TSRespUnknownException(**param)
    #
    #                 # Logger.error(menu='BOT', action='Server Error', msg=msg, err_msg=err_msg, err_code=err_code)
    #
    #                 # self.user.player_id = ''
    #                 # self.user.game_access_token = ''
    #                 # self.user.authentication_token = ''
    #                 # self.user.remember_me_token = ''
    #                 # self.user.device_id = ''
    #                 # self.user.support_url = ''
    #                 # self.user.save(update_fields=[
    #                 #     'player_id',
    #                 #     'game_access_token',
    #                 #     'authentication_token',
    #                 #     'remember_me_token',
    #                 #     'device_id',
    #                 #     'support_url',
    #                 # ])
    #
    #         # raise Exception('Login Error - Retry !')
    #
    #
