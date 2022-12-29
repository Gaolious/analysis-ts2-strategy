import uuid
from hashlib import md5
from django.conf import settings

from app_root.bot.utils_request import CrawlingHelper
from app_root.bot.utils_server_time import ServerTime
from core.utils import disk_cache, Logger

import json

from app_root.bot.utils_abstract import BaseBotRequest
from app_root.users.models import User

LOGGING_MENU = 'utils.login'


@disk_cache(prefix='get_init_data', smt='{android_id}_{sent_at}.json')
def get_init_data(*, url: str, android_id, sent_at: str, game_access_token: str, player_id: str):
    """
    Header
                  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
        02044800  60 93 91 88 00 00 00 00 00 00 00 00 e0 01 00 00  `...............
        02044810  47 45 54 20 2f 61 70 69 2f 76 32 2f 69 6e 69 74  GET /api/v2/init
        02044820  69 61 6c 2d 64 61 74 61 2f 6c 6f 61 64 20 48 54  ial-data/load HT
        02044830  54 50 2f 31 2e 31 0d 0a 50 58 46 44 2d 52 65 71  TP/1.1..PXFD-Req
        02044840  75 65 73 74 2d 49 64 3a 20 66 37 64 35 66 37 30  uest-Id: f7d5f70
        02044850  38 2d 30 63 33 64 2d 34 32 30 36 2d 39 30 31 32  8-0c3d-4206-9012
        02044860  2d 31 39 62 35 63 62 63 66 38 34 64 38 0d 0a 50  -19b5cbcf84d8..P
        02044870  58 46 44 2d 52 65 74 72 79 2d 4e 6f 3a 20 30 0d  XFD-Retry-No: 0.
        02044880  0a 50 58 46 44 2d 53 65 6e 74 2d 41 74 3a 20 32  .PXFD-Sent-At: 2
        02044890  30 32 32 2d 31 32 2d 32 39 54 30 39 3a 31 32 3a  022-12-29T09:12:
        020448a0  30 30 2e 30 30 30 5a 0d 0a 50 58 46 44 2d 43 6c  00.000Z..PXFD-Cl
        020448b0  69 65 6e 74 2d 49 6e 66 6f 72 6d 61 74 69 6f 6e  ient-Information
        020448c0  3a 20 7b 22 53 74 6f 72 65 22 3a 22 67 6f 6f 67  : {"Store":"goog
        020448d0  6c 65 5f 70 6c 61 79 22 2c 22 56 65 72 73 69 6f  le_play","Versio
        020448e0  6e 22 3a 22 32 2e 36 2e 32 2e 34 30 32 33 22 2c  n":"2.6.2.4023",
        020448f0  22 4c 61 6e 67 75 61 67 65 22 3a 22 65 6e 22 7d  "Language":"en"}
        02044900  0d 0a 50 58 46 44 2d 43 6c 69 65 6e 74 2d 56 65  ..PXFD-Client-Ve
        02044910  72 73 69 6f 6e 3a 20 32 2e 36 2e 32 2e 34 30 32  rsion: 2.6.2.402
        02044920  33 0d 0a 50 58 46 44 2d 44 65 76 69 63 65 2d 54  3..PXFD-Device-T
        02044930  6f 6b 65 6e 3a 20 33 30 62 32 37 30 63 61 36 34  oken: 30b270ca64
        02044940  65 38 30 62 62 62 66 34 62 31 38 36 66 32 35 31  e80bbbf4b186f251
        02044950  62 61 33 35 38 61 0d 0a 50 58 46 44 2d 47 61 6d  ba358a..PXFD-Gam
        02044960  65 2d 41 63 63 65 73 73 2d 54 6f 6b 65 6e 3a 20  e-Access-Token:
        02044970  30 33 63 61 31 30 64 33 2d 35 39 32 62 2d 35 32  03ca10d3-592b-52
        02044980  65 66 2d 61 63 64 63 2d 39 36 64 33 31 36 34 63  ef-acdc-96d3164c
        02044990  38 61 30 62 0d 0a 50 58 46 44 2d 50 6c 61 79 65  8a0b..PXFD-Playe
        020449a0  72 2d 49 64 3a 20 36 32 37 39 34 37 37 30 0d 0a  r-Id: 62794770..
        020449b0  48 6f 73 74 3a 20 67 61 6d 65 2e 74 72 61 69 6e  Host: game.train
        020449c0  73 74 61 74 69 6f 6e 32 2e 63 6f 6d 0d 0a 41 63  station2.com..Ac
        020449d0  63 65 70 74 2d 45 6e 63 6f 64 69 6e 67 3a 20 67  cept-Encoding: g
        020449e0  7a 69 70 2c 20 64 65 66 6c 61 74 65 0d 0a 0d 0a  zip, deflate....
    Resp
                  0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
        02201010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
        02201020  22 52 65 71 75 65 73 74 49 64 22 3a 22 66 37 64  "RequestId":"f7d
        02201030  35 66 37 30 38 2d 30 63 33 64 2d 34 32 30 36 2d  5f708-0c3d-4206-
        02201040  39 30 31 32 2d 31 39 62 35 63 62 63 66 38 34 64  9012-19b5cbcf84d
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
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_LANGUAGE),
        'PXFD-Device-Token': device_id,
        'PXFD-Game-Access-Token': game_access_token,
        'PXFD-Player-Id': player_id,
        # 'Content-Type': 'application/json',
        # 'Host': 'game.trainstation2.com',
        'Accept-Encoding': 'gzip, deflate',
    }
    Logger.info(menu=LOGGING_MENU, action='get_init_data', msg='before request', url=url, headers=headers)
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
        menu=LOGGING_MENU, action='get_init_data', msg='after request',
        status_code=str(resp_status_code),
        body=str(resp_body),
        headers=str(resp_headers),
        cookies=str(resp_cookies),
    )
    return resp_body


class InitData(BaseBotRequest):

    def get_data(self, url, user: User, server_time: ServerTime) -> str:
        """

        :param url:
        :param user:
        :param server_time:
        :return:
        """
        return get_init_data(
            url=url,
            android_id=user.android_id,
            sent_at=server_time.get_curr_time(),
            game_access_token=user.game_access_token,
            player_id=user.player_id,
        )

    def parse_data(self, data, user: User) -> str:
        """

        :param data:
        :param user:
        :return:
        """
        mapping = {
            'competitions': self._parse_init_competitions,
            'event': self._parse_init_event,
            'events': self._parse_init_events,
            'factories': self._parse_init_factories,
            'jobs': self._parse_init_jobs,

        }
        json_data = json.loads(data, strict=False)

        success = json_data.get('Success')
        assert success

        server_time = json_data.get('Time')
        server_data = json_data.get('Data', [])

        for row in server_data:
            row_type = row.get('Type')
            row_data = row.get('Data')
            if row_type and row_data and row_type in mapping:
                mapping[row_type](data=row_data)
        return server_time

    def _parse_init_competitions(self, data):
        """
            {
                'Competitions': [
                {'Type': 'union', 'LevelFrom': 25, 'MaxAttendees': 15, 'CompetitionId': '0a96024d-fcee-4402-9f33-618eaf07ca5b', 'ContentCategory': 3, 'Rewards': [], 'StartsAt': '2022-12-05T12:00:00Z', 'EnrolmentAvailableTo': '2023-02-27T12:00:00Z', 'FinishesAt': '2023-02-27T12:00:00Z', 'ExpiresAt': '2023-03-03T12:00:00Z', 'PresentationDataId': 100001, 'GuildData': {'Status': 0}, 'Scope': 'global'},
                {'Type': 'union', 'LevelFrom': 25, 'MaxAttendees': 15, 'CompetitionId': '676046e4-4f11-462d-a741-afd05cad254b', 'ContentCategory': 3, 'Rewards': [], 'StartsAt': '2022-12-26T12:00:00Z', 'EnrolmentAvailableTo': '2023-01-01T12:00:00Z', 'FinishesAt': '2023-01-01T12:00:00Z', 'ExpiresAt': '2023-01-02T00:00:00Z', 'PresentationDataId': 100001, 'GuildData': {'Status': 0}, 'Scope': 'group'},
                {'Type': 'prestige', 'LevelFrom': 899, 'MaxAttendees': 15, 'CompetitionId': 'e65a0ecf-7e72-462c-ae02-6c58ed2fceab', 'ContentCategory': 4, 'Rewards': [{'Items': [{'Id': 8, 'Value': 9, 'Amount': 11}]}, {'Items': [{'Id': 8, 'Value': 9, 'Amount': 7}]}, {'Items': [{'Id': 8, 'Value': 9, 'Amount': 5}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 20}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 18}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 16}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 14}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 12}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 10}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 9}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 8}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 7}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 5}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 3}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 1}]}], 'StartsAt': '2022-12-26T12:00:00Z', 'EnrolmentAvailableTo': '2023-01-01T12:00:00Z', 'FinishesAt': '2023-01-01T12:00:00Z', 'ExpiresAt': '2023-01-01T23:59:50Z', 'PresentationDataId': 33, 'Scope': 'group'}, {'Type': 'default', 'LevelFrom': 12, 'MaxAttendees': 25, 'CompetitionId': '16b00d3f-e2b1-464b-8c9f-e218cfca0008', 'ContentCategory': 1, 'Rewards': [{'Items': [{'Id': 8, 'Value': 35001, 'Amount': 350}, {'Id': 6, 'Value': 100130}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 250}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 200}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 180}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 160}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 120}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 100}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 90}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 80}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 70}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 60}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 50}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 50}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 40}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 40}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 20}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 20}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 20}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 10}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 10}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 2}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 2}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 2}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 2}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 2}]}], 'StartsAt': '2022-12-27T12:00:00Z', 'EnrolmentAvailableTo': '2022-12-29T00:00:00Z', 'FinishesAt': '2022-12-29T12:00:00Z', 'ExpiresAt': '2022-12-29T23:59:50Z', 'PresentationDataId': 78, 'Scope': 'group'}]}
            :param data:
        :return:
        """
        pass

    def _parse_init_event(self, data):
        pass

    def _parse_init_events(self, data):
        pass

    def _parse_init_factories(self, data):
        pass

    def _parse_init_jobs(self, data):
        """

        "Jobs": [
          {
            "Id": "3b4581c4-b51f-445b-9a57-07f3c6c0f591",
            "JobLocationId": 152,
            "JobLevel": 2,
            "Sequence": 0,
            "JobType": 8,
            "Duration": 20,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {
              "Id": 100,
              "Amount": 30
            },
            "CurrentArticleAmount": 15,
            "Reward": {
              "Items": [
                {
                  "Id": 8,
                  "Value": 4,
                  "Amount": 40
                },
                {
                  "Id": 8,
                  "Value": 1,
                  "Amount": 15
                },
                {
                  "Id": 8,
                  "Value": 3,
                  "Amount": 40
                }
              ]
            },
            "Bonus": {
              "Reward": {
                "Items": []
              }
            },
            "Requirements": [
              {
                "Type": "region",
                "Value": 1
              }
            ],
            "UnlocksAt": "2022-08-27T06:01:41Z"
          },
        ]
        :param data:
        :return:
        """
        pass

    def _parse_init_player(self, data):
        pass

    def _parse_init_regions(self, data):
        pass

    def _parse_init_trains(self, data):
        pass

    def _parse_init_warehouse(self, data):
        """
        {
         'Level' = {int} 2
         'Articles' = {list: 9} [{'Id': 1, 'Amount': 35}, {'Id': 2, 'Amount': 27}, {'Id': 3, 'Amount': 254}, {'Id': 4, 'Amount': 55}, {'Id': 6, 'Amount': 185}, {'Id': 7, 'Amount': 51}, {'Id': 100, 'Amount': 38}, {'Id': 101, 'Amount': 23}, {'Id': 104, 'Amount': 49}]
          0 = {dict: 2} {'Id': 1, 'Amount': 35}
          1 = {dict: 2} {'Id': 2, 'Amount': 27}
          2 = {dict: 2} {'Id': 3, 'Amount': 254}
          3 = {dict: 2} {'Id': 4, 'Amount': 55}
          4 = {dict: 2} {'Id': 6, 'Amount': 185}
          5 = {dict: 2} {'Id': 7, 'Amount': 51}
          6 = {dict: 2} {'Id': 100, 'Amount': 38}
          7 = {dict: 2} {'Id': 101, 'Amount': 23}
          8 = {dict: 2} {'Id': 104, 'Amount': 49}
        }
        :param data:
        :return:
        """
        pass

    def _parse_init_whistles(self, data):
        """
            {'Whistles': [{'Category': 1, 'Position': 3, 'SpawnTime': '2022-12-29T10:32:46Z', 'CollectableFrom': '2022-12-29T10:32:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 2, 'Amount': 1}]}, 'IsForVideoReward': True, 'ExpiresAt': '2999-12-31T00:00:00Z'}, {'Category': 1, 'Position': 4, 'SpawnTime': '2022-12-29T10:33:46Z', 'CollectableFrom': '2022-12-29T10:33:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 8, 'Amount': 1}]}, 'IsForVideoReward': False}, {'Category': 1, 'Position': 1, 'SpawnTime': '2022-12-29T10:31:46Z', 'CollectableFrom': '2022-12-29T10:31:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 6, 'Amount': 1}]}, 'IsForVideoReward': False}, {'Category': 1, 'Position': 2, 'SpawnTime': '2022-12-29T10:32:06Z', 'CollectableFrom': '2022-12-29T10:32:06Z', 'Reward': {'Items': [{'Id': 8, 'Value': 104, 'Amount': 1}]}, 'IsForVideoReward': False}]}
        :param data:
        :return:
        """
