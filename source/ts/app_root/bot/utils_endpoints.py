import json
import uuid
from hashlib import md5
from typing import List, Dict

from django.conf import settings

from app_root.bot.utils_abstract import BaseBotRequest
from app_root.bot.utils_request import CrawlingHelper
from app_root.bot.utils_server_time import ServerTime
from app_root.users.models import User
from core.utils import disk_cache, Logger

LOGGING_MENU = 'utils.endpoints'


@disk_cache(prefix='get_endpoints', smt='{android_id}.json')
def get_endpoints(*, url: str, android_id: str) -> str:
    client_info = {
        "Store": str(settings.CLIENT_INFORMATION_STORE),
        "Version": str(settings.CLIENT_INFORMATION_VERSION),
        "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
    }

    headers = {
        'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
        'PXFD-Retry-No': '0',
        'PXFD-Sent-At': '0001-01-01T00:00:00.000',
        'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_LANGUAGE),
        'PXFD-Device-Token': md5(android_id.encode('utf-8')).hexdigest(),
        'Accept-Encoding': 'gzip, deflate',
    }

    Logger.info(menu=LOGGING_MENU, action='get_endpoints', msg='before request', url=url, headers=headers)
    resp = CrawlingHelper.get(
        url=url,
        headers=headers,
        payload={},
        cookies={},
        params={},
    )
    resp_status_code = resp.status_code
    resp_body = resp.content.decode('utf-8')
    resp_headers = {k: v for k, v in resp.headers.items()}
    resp_cookies = {k: v for k, v in resp.cookies.items()}

    Logger.info(
        menu=LOGGING_MENU, action='get_endpoints', msg='after request',
        status_code=str(resp_status_code),
        body=str(resp_body),
        headers=str(resp_headers),
        cookies=str(resp_cookies),
    )
    return resp_body


class EndPoints(BaseBotRequest):

    ENDPOINT_LOGIN = 'login'
    ENDPOINT_DEFINITION = 'definitions'

    endpoints: Dict[str, str] = {}
    init_data_urls: List[str] = []

    def get_data(self, url, user: User, server_time: ServerTime) -> str:
        """

        :param user:
        :return:
        """
        return get_endpoints(url=url, android_id=user.android_id)

    def parse_data(self, data, user: User) -> str:
        """

        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)

        success = json_data.get('Success')
        assert success

        server_time = json_data.get('Time')
        for ep in json_data.get('Data', {}).get('Endpoints', []):
            name = ep.get('Name')
            url = ep.get('Url')

            if name and url:
                self.endpoints.update({name: url})

        for url in json_data.get('Data', {}).get('InitialDataUrls', []):
            if not isinstance(url, list):
                url = [url]
            self.init_data_urls += url

        return server_time

    def get_login_url(self) -> str:
        return self.endpoints.get(self.ENDPOINT_LOGIN, '')

    def get_init_urls(self) -> List[str]:
        return self.init_data_urls

    def get_definition_url(self) -> str:
        return self.endpoints.get(self.ENDPOINT_DEFINITION, '')
