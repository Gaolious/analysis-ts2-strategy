import json
import uuid
from hashlib import md5

from django.conf import settings

from app_root.bot.utils_abstract import BaseBotHelper
from app_root.bot.utils_request import CrawlingHelper
from core.utils import disk_cache, Logger

LOGGING_MENU = 'utils.login'


@disk_cache(prefix='login_with_remember_token', smt='{android_id}_{sent_at}.json')
def login_with_remember_token(*, url: str, android_id: str, remember_me_token: str, sent_at: str):
    """
    Header :
                     0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
          01d818c0  60 93 91 88 00 00 00 00 00 00 00 00 ac 01 00 00  `...............
          01d818d0  50 4f 53 54 20 2f 6c 6f 67 69 6e 20 48 54 54 50  POST /login HTTP
          01d818e0  2f 31 2e 31 0d 0a 50 58 46 44 2d 52 65 71 75 65  /1.1..PXFD-Reque
          01d818f0  73 74 2d 49 64 3a 20 35 61 38 65 35 38 39 32 2d  st-Id: 5a8e5892-
          01d81900  62 64 62 32 2d 34 36 64 30 2d 62 32 38 37 2d 30  bdb2-46d0-b287-0
          01d81910  33 39 31 39 32 66 64 31 62 34 37 0d 0a 50 58 46  39192fd1b47..PXF
          01d81920  44 2d 52 65 74 72 79 2d 4e 6f 3a 20 30 0d 0a 50  D-Retry-No: 0..P
          01d81930  58 46 44 2d 53 65 6e 74 2d 41 74 3a 20 32 30 32  XFD-Sent-At: 202
          01d81940  32 2d 31 32 2d 32 39 54 30 39 3a 31 31 3a 35 34  2-12-29T09:11:54
          01d81950  2e 30 30 30 5a 0d 0a 50 58 46 44 2d 43 6c 69 65  .000Z..PXFD-Clie
          01d81960  6e 74 2d 49 6e 66 6f 72 6d 61 74 69 6f 6e 3a 20  nt-Information:
          01d81970  7b 22 53 74 6f 72 65 22 3a 22 67 6f 6f 67 6c 65  {"Store":"google
          01d81980  5f 70 6c 61 79 22 2c 22 56 65 72 73 69 6f 6e 22  _play","Version"
          01d81990  3a 22 32 2e 36 2e 32 2e 34 30 32 33 22 2c 22 4c  :"2.6.2.4023","L
          01d819a0  61 6e 67 75 61 67 65 22 3a 22 65 6e 22 7d 0d 0a  anguage":"en"}..
          01d819b0  50 58 46 44 2d 43 6c 69 65 6e 74 2d 56 65 72 73  PXFD-Client-Vers
          01d819c0  69 6f 6e 3a 20 32 2e 36 2e 32 2e 34 30 32 33 0d  ion: 2.6.2.4023.
          01d819d0  0a 50 58 46 44 2d 44 65 76 69 63 65 2d 54 6f 6b  .PXFD-Device-Tok
          01d819e0  65 6e 3a 20 33 30 62 32 37 30 63 61 36 34 65 38  en: 30b270ca64e8
          01d819f0  30 62 62 62 66 34 62 31 38 36 66 32 35 31 62 61  0bbbf4b186f251ba
          01d81a00  33 35 38 61 0d 0a 43 6f 6e 74 65 6e 74 2d 54 79  358a..Content-Ty
          01d81a10  70 65 3a 20 61 70 70 6c 69 63 61 74 69 6f 6e 2f  pe: application/
          01d81a20  6a 73 6f 6e 0d 0a 43 6f 6e 74 65 6e 74 2d 4c 65  json..Content-Le
          01d81a30  6e 67 74 68 3a 20 34 30 38 36 0d 0a 48 6f 73 74  ngth: 4086..Host
          01d81a40  3a 20 67 61 6d 65 2e 74 72 61 69 6e 73 74 61 74  : game.trainstat
          01d81a50  69 6f 6e 32 2e 63 6f 6d 0d 0a 41 63 63 65 70 74  ion2.com..Accept
          01d81a60  2d 45 6e 63 6f 64 69 6e 67 3a 20 67 7a 69 70 2c  -Encoding: gzip,
          01d81a70  20 64 65 66 6c 61 74 65 0d 0a 0d 0a               deflate....
    Body :
                     0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
          01dd0010  7b 22 4c 6f 67 69 6e 54 79 70 65 22 3a 22 72 65  {"LoginType":"re
          01dd0020  6d 65 6d 62 65 72 5f 6d 65 5f 74 6f 6b 65 6e 22  member_me_token"
          01dd0030  2c 22 49 64 65 6e 74 69 74 79 22 3a 22 65 79 4a  ,"Identity":"eyJ
          01dd0040  6c 63 47 73 69 4f 6e 73 69 61 33 52 35 49 6a 6f  lcGsiOnsia3R5Ijo
          01dd0050  69 52 55 4d 69 4c 43 4a 6a 63 6e 59 69 4f 69 4a  iRUMiLCJjcnYiOiJ
          ....
          01dd0390  43 46 47 37 53 6f 61 54 52 34 38 4b 32 4c 34 44  CFG7SoaTR48K2L4D
          01dd03a0  46 4f 62 71 41 44 43 39 4f 50 4e 7a 67 6b 4a 74  FObqADC9OPNzgkJt
          01dd03b0  44 39 59 56 35 4e 32 43 56 65 44 78 34 74 32 6c  D9YV5N2CVeDx4t2l
          01dd03c0  68 72 73 76 6a 53 30 65 42 6c 4c 43 64 4c 4a 52  hrsvjS0eBlLCdLJR
          01dd03d0  43 67 70 39 47 32 34 63 2e 62 49 63 56 33 42 55  Cgp9G24c.bIcV3BU
          01dd03e0  43 31 4e 79 49 64 38 53 6a 79 37 58 51 63 73 41  C1NyId8Sjy7XQcsA
          01dd03f0  4e 75 44 6c 47 72 78 37 42 56 59 65 41 4e 76 66  NuDlGrx7BVYeANvf
          01dd0400  74 6b 6f 4d 22 7d 00 00 00 00 00 00 00 00 00 00  tkoM"}

    :param android_id:
    :param remember_me_token:
    :param sent_at:
    :return:
    """

    client_info = {
        "Store": str(settings.CLIENT_INFORMATION_STORE),
        "Version": str(settings.CLIENT_INFORMATION_VERSION),
        "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
    }
    device_id = md5(android_id.encode('utf-8')).hexdigest()
    headers = {
        'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
        'PXFD-Retry-No': '0',
        'PXFD-Sent-At': str(sent_at),
        'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
        'PXFD-Device-Token': device_id,
        'Content-Type': 'application/json',
        # 'Host': 'game.trainstation2.com',
        'Accept-Encoding': 'gzip, deflate',
    }
    payload = {
        'LoginType': 'remember_me_token',
        'Identity': remember_me_token,
    }
    Logger.info(menu=LOGGING_MENU, action='login_with_remember_token', msg='before request', url=url, headers=headers)
    resp = CrawlingHelper.post(
        url=url,
        headers=headers,
        payload=json.dumps(payload, separators=(',', ':')),
        cookies={},
        params={},
    )
    resp_status_code = resp.status_code
    resp_body = resp.content.decode('utf-8')
    resp_headers = {k: v for k, v in resp.headers.items()}
    resp_cookies = {k: v for k, v in resp.cookies.items()}

    Logger.info(
        menu=LOGGING_MENU, action='login_with_remember_token', msg='after request',
        status_code=str(resp_status_code),
        body=str(resp_body),
        headers=str(resp_headers),
        cookies=str(resp_cookies),
    )
    return resp_body


@disk_cache(prefix='login_with_device_id', smt='{android_id}_{sent_at}.json')
def login_with_device_id(*, url: str, android_id: str, sent_at: str):
    """
    header :
                     0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
          01cd5a90  50 4f 53 54 20 2f 6c 6f 67 69 6e 20 48 54 54 50  POST /login HTTP
          01cd5aa0  2f 31 2e 31 0d 0a 50 58 46 44 2d 52 65 71 75 65  /1.1..PXFD-Reque
          01cd5ab0  73 74 2d 49 64 3a 20 65 34 62 33 32 36 64 62 2d  st-Id: e4b326db-
          01cd5ac0  39 31 65 33 2d 34 63 39 34 2d 38 36 62 65 2d 37  91e3-4c94-86be-7
          01cd5ad0  64 37 35 63 39 63 64 61 62 65 32 0d 0a 50 58 46  d75c9cdabe2..PXF
          01cd5ae0  44 2d 52 65 74 72 79 2d 4e 6f 3a 20 30 0d 0a 50  D-Retry-No: 0..P
          01cd5af0  58 46 44 2d 53 65 6e 74 2d 41 74 3a 20 32 30 32  XFD-Sent-At: 202
          01cd5b00  32 2d 31 32 2d 32 39 54 30 39 3a 30 33 3a 32 36  2-12-29T09:03:26
          01cd5b10  2e 30 30 30 5a 0d 0a 50 58 46 44 2d 43 6c 69 65  .000Z..PXFD-Clie
          01cd5b20  6e 74 2d 49 6e 66 6f 72 6d 61 74 69 6f 6e 3a 20  nt-Information:
          01cd5b30  7b 22 53 74 6f 72 65 22 3a 22 67 6f 6f 67 6c 65  {"Store":"google
          01cd5b40  5f 70 6c 61 79 22 2c 22 56 65 72 73 69 6f 6e 22  _play","Version"
          01cd5b50  3a 22 32 2e 36 2e 32 2e 34 30 32 33 22 2c 22 4c  :"2.6.2.4023","L
          01cd5b60  61 6e 67 75 61 67 65 22 3a 22 65 6e 22 7d 0d 0a  anguage":"en"}..
          01cd5b70  50 58 46 44 2d 43 6c 69 65 6e 74 2d 56 65 72 73  PXFD-Client-Vers
          01cd5b80  69 6f 6e 3a 20 32 2e 36 2e 32 2e 34 30 32 33 0d  ion: 2.6.2.4023.
          01cd5b90  0a 50 58 46 44 2d 44 65 76 69 63 65 2d 54 6f 6b  .PXFD-Device-Tok
          01cd5ba0  65 6e 3a 20 33 30 62 32 37 30 63 61 36 34 65 38  en: 30b270ca64e8
          01cd5bb0  30 62 62 62 66 34 62 31 38 36 66 32 35 31 62 61  0bbbf4b186f251ba
          01cd5bc0  33 35 38 61 0d 0a 43 6f 6e 74 65 6e 74 2d 54 79  358a..Content-Ty
          01cd5bd0  70 65 3a 20 61 70 70 6c 69 63 61 74 69 6f 6e 2f  pe: application/
          01cd5be0  6a 73 6f 6e 0d 0a 43 6f 6e 74 65 6e 74 2d 4c 65  json..Content-Le
          01cd5bf0  6e 67 74 68 3a 20 37 31 0d 0a 48 6f 73 74 3a 20  ngth: 71..Host:
          01cd5c00  67 61 6d 65 2e 74 72 61 69 6e 73 74 61 74 69 6f  game.trainstatio
          01cd5c10  6e 32 2e 63 6f 6d 0d 0a 41 63 63 65 70 74 2d 45  n2.com..Accept-E
          01cd5c20  6e 63 6f 64 69 6e 67 3a 20 67 7a 69 70 2c 20 64  ncoding: gzip, d
          01cd5c30  65 66 6c 61 74 65 0d 0a 0d 0a                    eflate....
    body :
                     0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
          01d1c010  7b 22 4c 6f 67 69 6e 54 79 70 65 22 3a 22 64 65  {"LoginType":"de
          01d1c020  76 69 63 65 5f 69 64 22 2c 22 49 64 65 6e 74 69  vice_id","Identi
          01d1c030  74 79 22 3a 22 33 30 62 32 37 30 63 61 36 34 65  ty":"30b270ca64e
          01d1c040  38 30 62 62 62 66 34 62 31 38 36 66 32 35 31 62  80bbbf4b186f251b
          01d1c050  61 33 35 38 61 22 7d 00 00 00 00 00 00 00 00 00  a358a"}.........
          01d1c060  00 00 00 00 00 00 00                             .......
    :return:
    """
    client_info = {
        "Store": str(settings.CLIENT_INFORMATION_STORE),
        "Version": str(settings.CLIENT_INFORMATION_VERSION),
        "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
    }
    device_id = md5(android_id.encode('utf-8')).hexdigest()
    headers = {
        'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
        'PXFD-Retry-No': '0',
        'PXFD-Sent-At': str(sent_at),
        'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
        'PXFD-Device-Token': device_id,
        'Content-Type': 'application/json',
        # 'Host': 'game.trainstation2.com',
        'Accept-Encoding': 'gzip, deflate',
    }
    payload = {
        'LoginType': 'device_id',
        'Identity': device_id,
    }
    Logger.info(menu=LOGGING_MENU, action='login_with_device_id', msg='before request', url=url, headers=headers)
    resp = CrawlingHelper.post(
        url=url,
        headers=headers,
        payload=json.dumps(payload, separators=(',', ':')),
        cookies={},
        params={},
    )
    resp_status_code = resp.status_code
    resp_body = resp.content.decode('utf-8')
    resp_headers = {k: v for k, v in resp.headers.items()}
    resp_cookies = {k: v for k, v in resp.cookies.items()}

    Logger.info(
        menu=LOGGING_MENU, action='login_with_device_id', msg='after request',
        status_code=str(resp_status_code),
        body=str(resp_body),
        headers=str(resp_headers),
        cookies=str(resp_cookies),
    )
    return resp_body


class LoginHelper(BaseBotHelper):

    def get_data(self, url) -> str:
        """

        :param url:
        :return:
        """
        if self.user.remember_me_token:
            data = login_with_remember_token(
                url=url,
                android_id=self.user.android_id,
                remember_me_token=self.user.remember_me_token,
                sent_at=self.server_time.get_curr_time(),
            )
        else:
            data = login_with_device_id(
                url=url,
                android_id=self.user.android_id,
                sent_at=self.server_time.get_curr_time(),
            )

        return data

    def parse_data(self, data) -> str:
        """

        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)
        self.check_response(json_data=json_data)

        server_time = json_data.get('Time')
        server_data = json_data.get('Data', {})

        if server_data:
            self.user.player_id = server_data.get('PlayerId', '') or ''
            self.user.game_access_token = server_data.get('GameAccessToken', '') or ''
            self.user.authentication_token = server_data.get('AuthenticationToken', '') or ''
            self.user.remember_me_token = server_data.get('RememberMeToken', '') or ''
            self.user.device_id = server_data.get('DeviceId', '') or ''
            self.user.support_url = server_data.get('SupportUrl', '') or ''
            self.user.save(update_fields=[
                'player_id',
                'game_access_token',
                'authentication_token',
                'remember_me_token',
                'device_id',
                'support_url',
            ])

        return server_time
