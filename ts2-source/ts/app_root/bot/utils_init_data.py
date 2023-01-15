import json
import uuid
from hashlib import md5
from typing import Dict, Callable

from dateutil import parser
from django.conf import settings
from django.utils import timezone

from app_root.bot.models import PlayerBuilding, PlayerDestination, PlayerFactory, PlayerFactoryProductOrder, PlayerJob, \
    PlayerTrain, PlayerWarehouse, PlayerWhistle, PlayerWhistleItem, PlayerGift, PlayerContractList, PlayerContract, \
    WarehouseLevel
from app_root.bot.utils_abstract import BaseBotHelper
from app_root.bot.utils_request import CrawlingHelper
from core.utils import disk_cache, Logger

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
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
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


class InitdataHelper(BaseBotHelper):

    def get_data(self, url) -> str:
        """

        :param url:
        :param user:
        :param server_time:
        :return:
        """
        return get_init_data(
            url=url,
            android_id=self.user.android_id,
            sent_at=self.server_time.get_curr_time(),
            game_access_token=self.user.game_access_token,
            player_id=self.user.player_id,
        )

    def _update_server_time(self, request_datetime, response_datetime, server_datetime):
        self.update_player_info()

        super(InitdataHelper, self)._update_server_time(
            request_datetime=request_datetime,
            response_datetime=response_datetime,
            server_datetime=server_datetime,
        )
        self.run_version.init_data_request_datetime = request_datetime
        self.run_version.init_data_response_datetime = response_datetime
        self.run_version.init_data_server_datetime = server_datetime
        self.run_version.save(
            update_fields=[
                'init_data_request_datetime',
                'init_data_response_datetime',
                'init_data_server_datetime',
            ]
        )

    def update_player_info(self):
        xp = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=1).first()
        gem = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=2).first()
        gold = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=3).first()
        key = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=4).first()

        self.run_version.xp = xp.amount if xp else 0
        self.run_version.gem = gem.amount if gem else 0
        self.run_version.gold = gold.amount if gold else 0
        self.run_version.key = key.amount if key else 0

        common_parts = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=6).first()
        rare_parts = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=7).first()
        epic_parts = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=8).first()
        legendary_parts = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=9).first()

        self.run_version.train_parts_common = common_parts.amount if common_parts else 0
        self.run_version.train_parts_rare = rare_parts.amount if rare_parts else 0
        self.run_version.train_parts_epic = epic_parts.amount if epic_parts else 0
        self.run_version.train_parts_legendary = legendary_parts.amount if legendary_parts else 0

        blue = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=10).first()
        yellow = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=11).first()
        red = PlayerWarehouse.objects.filter(version_id=self.run_version.id, article_id=12).first()

        self.run_version.blue_city_plans = blue.amount if blue else 0
        self.run_version.yellow_city_plans = yellow.amount if yellow else 0
        self.run_version.red_city_plans = red.amount if red else 0

        self.run_version.save()

    def parse_data(self, data) -> str:
        """

        :param data:
        :param user:
        :return:
        """
        mapping: Dict[str, Callable] = {
            'competitions': self._parse_init_competitions,
            'city_loop': self._parse_init_city_loop,
            'event': self._parse_init_event,
            'events': self._parse_init_events,
            'destinations': self._parse_init_destinations,
            'factories': self._parse_init_factories,
            'jobs': self._parse_init_jobs,
            'player': self._parse_init_player,
            'regions': self._parse_init_regions,
            'trains': self._parse_init_trains,
            'warehouse': self._parse_init_warehouse,
            'whistles': self._parse_init_whistles,
            'ship_offers': self._parse_init_ship_offers,
            'contracts': self._parse_init_contracts,
            'dispatcher': self._parse_init_dispatcher,
            'gifts': self._parse_init_gifts,

            'ab_test': self._parse_init_not_yet_implemented,
            'achievements': self._parse_init_not_yet_implemented,
            'maps': self._parse_init_not_yet_implemented,
            'locations': self._parse_init_not_yet_implemented,
            'login_profile': self._parse_init_not_yet_implemented,
            'game_features': self._parse_init_not_yet_implemented,
            'daily_reward': self._parse_init_not_yet_implemented,
            'unlocked_contents': self._parse_init_not_yet_implemented,
            'shop': self._parse_init_not_yet_implemented,
            'reminders': self._parse_init_not_yet_implemented,
            'seasons': self._parse_init_not_yet_implemented,
            'milestones': self._parse_init_not_yet_implemented,
            'markets': self._parse_init_not_yet_implemented,
            'guild': self._parse_init_not_yet_implemented,
            'game': self._parse_init_not_yet_implemented,
            'placements': self._parse_init_not_yet_implemented,
            'player_feature': self._parse_init_not_yet_implemented,
            'prestige': self._parse_init_not_yet_implemented,
            'ship_loop': self._parse_init_not_yet_implemented,
            'tutorial': self._parse_init_not_yet_implemented,
            'tickets': self._parse_init_not_yet_implemented,
            'task_lists': self._parse_init_not_yet_implemented,
            'offer_wall': self._parse_init_not_yet_implemented,
            'containers': self._parse_init_not_yet_implemented,
            'communities': self._parse_init_not_yet_implemented,
            'commodities': self._parse_init_not_yet_implemented,
            'city_building_shop': self._parse_init_not_yet_implemented,
            'calendars': self._parse_init_not_yet_implemented,
            'boosts': self._parse_init_not_yet_implemented,
            'vouchers': self._parse_init_not_yet_implemented,
        }
        json_data = json.loads(data, strict=False)
        self.check_response(json_data=json_data)

        server_time = json_data.get('Time')
        server_data = json_data.get('Data', [])

        for row in server_data:
            row_type = row.get('Type')
            row_data = row.get('Data')
            if row_type in mapping:
                mapping[row_type](data=row_data)
            else:
                print('unknown', row)

        return server_time

    def _parse_init_not_yet_implemented(self, data):
        pass

    def _parse_init_gifts(self, data):
        """
    {
      "Type": "gifts",
      "Data": {
        "Gifts": [
          {
            "Id": "8295a2de-d048-4228-ac02-e3d36c2d3b4a",
            "Reward": {
              "Items": [
                {
                  "Id": 8,
                  "Value": 100000,
                  "Amount": 1326
                },
                {
                  "Id": 8,
                  "Value": 100003,
                  "Amount": 792
                }
              ]
            },
            "Type": 6
          }
        ]
      }
    },
        :param data:
        :return:
        """
        gifts = data.pop('Gifts', [])
        if gifts:
            bulk_list = PlayerGift.create_instance(data=gifts, version_id=self.run_version.id)
            if bulk_list:
                PlayerGift.objects.bulk_create(bulk_list)

        self.print_remain('_parse_init_gifts', data)

    def _parse_init_competitions(self, data):
        """
            :param data:
        :return:
        """
        """
        Sample:
            'Competitions' = {list: 4} [{'Type': 'union', 'LevelFrom': 25, 'MaxAttendees': 15, 'CompetitionId': '0a96024d-fcee-4402-9f33-618eaf07ca5b', 'ContentCategory': 3, 'Rewards': [], 'StartsAt': '2022-12-05T12:00:00Z', 'EnrolmentAvailableTo': '2023-02-27T12:00:00Z', 'FinishesAt': '2023-02-27T12:00:00Z', 'ExpiresAt': '2023-03-03T12:00:00Z', 'PresentationDataId': 100001, 'GuildData': {'Status': 0}, 'Scope': 'global'}, {'Type': 'union', 'LevelFrom': 25, 'MaxAttendees': 15, 'CompetitionId': '676046e4-4f11-462d-a741-afd05cad254b', 'ContentCategory': 3, 'Rewards': [], 'StartsAt': '2022-12-26T12:00:00Z', 'EnrolmentAvailableTo': '2023-01-01T12:00:00Z', 'FinishesAt': '2023-01-01T12:00:00Z', 'ExpiresAt': '2023-01-02T00:00:00Z', 'PresentationDataId': 100001, 'GuildData': {'Status': 0}, 'Scope': 'group'}, {'Type': 'prestige', 'LevelFrom': 899, 'MaxAttendees': 15, 'CompetitionId': 'e65a0ecf-7e72-462c-ae02-6c58ed2fceab', 'ContentCategory': 4, 'Rewards': [{'Items': [{'Id': 8, 'Value': 9, 'Amount': 11}]}, {'Items': [{'Id': 8, 'Value'...
                 0 = {dict: 13} {'Type': 'union', 'LevelFrom': 25, 'MaxAttendees': 15, 'CompetitionId': '0a96024d-fcee-4402-9f33-618eaf07ca5b', 'ContentCategory': 3, 'Rewards': [], 'StartsAt': '2022-12-05T12:00:00Z', 'EnrolmentAvailableTo': '2023-02-27T12:00:00Z', 'FinishesAt': '2023-02-27T12:00:00Z', 'ExpiresAt': '2023-03-03T12:00:00Z', 'PresentationDataId': 100001, 'GuildData': {'Status': 0}, 'Scope': 'global'}
                 1 = {dict: 13} {'Type': 'union', 'LevelFrom': 25, 'MaxAttendees': 15, 'CompetitionId': '676046e4-4f11-462d-a741-afd05cad254b', 'ContentCategory': 3, 'Rewards': [], 'StartsAt': '2022-12-26T12:00:00Z', 'EnrolmentAvailableTo': '2023-01-01T12:00:00Z', 'FinishesAt': '2023-01-01T12:00:00Z', 'ExpiresAt': '2023-01-02T00:00:00Z', 'PresentationDataId': 100001, 'GuildData': {'Status': 0}, 'Scope': 'group'}
                 2 = {dict: 12} {'Type': 'prestige', 'LevelFrom': 899, 'MaxAttendees': 15, 'CompetitionId': 'e65a0ecf-7e72-462c-ae02-6c58ed2fceab', 'ContentCategory': 4, 'Rewards': [{'Items': [{'Id': 8, 'Value': 9, 'Amount': 11}]}, {'Items': [{'Id': 8, 'Value': 9, 'Amount': 7}]}, {'Items': [{'Id': 8, 'Value': 9, 'Amount': 5}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 20}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 18}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 16}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 14}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 12}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 10}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 9}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 8}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 7}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 5}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 3}]}, {'Items': [{'Id': 8, 'Value': 8, 'Amount': 1}]}], 'StartsAt': '2022-12-26T12:00:00Z', 'EnrolmentAvailableTo': '2023-01-01T12:00:00Z', 'FinishesAt': '2023-01-...
                 3 = {dict: 12} {'Type': 'default', 'LevelFrom': 12, 'MaxAttendees': 25, 'CompetitionId': '16b00d3f-e2b1-464b-8c9f-e218cfca0008', 'ContentCategory': 1, 'Rewards': [{'Items': [{'Id': 8, 'Value': 35001, 'Amount': 350}, {'Id': 6, 'Value': 100130}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 250}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 200}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 180}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 160}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 120}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 100}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 90}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 80}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 70}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 60}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 50}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 50}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 40}]}, {'Items': [{'Id': 8, 'Value': 35001, 'Amount': 40}]}, {'Items...
        """
        # 뭐해야 하지?..;
        pass

    def _parse_init_city_loop(self, data):
        """
            - population
            - population buildings

        :param data:
        :return:
        """
        """
        Sample:
            => population upgrade task, 및 population 수량. 확인.
        """
        # Population
        population = data.get('Population')
        if population:
            """
                'LastCalculatedCount' = {int} 33066
                'LastCalculatedAt' = {str} '2022-12-30T06:22:24Z'
            """
            self.run_version.population = population.get('LastCalculatedCount') or 0
            self.run_version.save(update_fields=['population'])

        # Buildings
        buildings = data.get('Buildings')
        if buildings:

            bulk_list = PlayerBuilding.create_instance(data=buildings, version_id=self.run_version.id)

            if bulk_list:
                PlayerBuilding.objects.bulk_create(bulk_list, 100)

    def _parse_init_event(self, data):
        """

        :param data:
        :return:
        """

        """
        Sample :
             'ActivationDate' = {str} '2022-12-28T12:00:00Z'
             'StartDate' = {str} '2022-12-29T12:00:00Z'
             'EndDate' = {str} '2023-01-02T12:00:00Z'
             'ExpirationDate' = {str} '2023-01-02T23:59:59Z'
             'EventId' = {int} 36
             'ActivatesAt' = {str} '2022-12-28T12:00:00Z'
             'StartsAt' = {str} '2022-12-29T12:00:00Z'
             'EndsAt' = {str} '2023-01-02T12:00:00Z'
             'ExpiresAt' = {str} '2023-01-02T23:59:59Z'
             'Shop' = {list: 0} []
        """
        pass

    def _parse_init_events(self, data):
        """

        :param data:
        :return:
        """

        """
        Sample:
            'Events' = {list: 2} [{'UniqueId': '777021c8-e22c-41b3-87e8-e0f3917f7cbc', 'EventId': 36, 'ActivatesAt': '2022-12-28T12:00:00Z', 'StartsAt': '2022-12-29T12:00:00Z', 'EndsAt': '2023-01-02T12:00:00Z', 'ExpiresAt': '2023-01-02T23:59:59Z', 'Shop': []}, {'UniqueId': '9ed5fc51-dff6-43e3-a701-919cd43d589b', 'EventId': 35, 'ActivatesAt': '2022-12-12T12:00:00Z', 'StartsAt': '2022-12-13T12:00:00Z', 'EndsAt': '2023-01-02T12:00:00Z', 'ExpiresAt': '2023-01-04T12:00:00Z', 'Shop': []}]
                 0 = {dict: 7} {'UniqueId': '777021c8-e22c-41b3-87e8-e0f3917f7cbc', 'EventId': 36, 'ActivatesAt': '2022-12-28T12:00:00Z', 'StartsAt': '2022-12-29T12:00:00Z', 'EndsAt': '2023-01-02T12:00:00Z', 'ExpiresAt': '2023-01-02T23:59:59Z', 'Shop': []}
                  'UniqueId' = {str} '777021c8-e22c-41b3-87e8-e0f3917f7cbc'
                  'EventId' = {int} 36
                  'ActivatesAt' = {str} '2022-12-28T12:00:00Z'
                  'StartsAt' = {str} '2022-12-29T12:00:00Z'
                  'EndsAt' = {str} '2023-01-02T12:00:00Z'
                  'ExpiresAt' = {str} '2023-01-02T23:59:59Z'
                  'Shop' = {list: 0} []
                  __len__ = {int} 7
                 1 = {dict: 7} {'UniqueId': '9ed5fc51-dff6-43e3-a701-919cd43d589b', 'EventId': 35, 'ActivatesAt': '2022-12-12T12:00:00Z', 'StartsAt': '2022-12-13T12:00:00Z', 'EndsAt': '2023-01-02T12:00:00Z', 'ExpiresAt': '2023-01-04T12:00:00Z', 'Shop': []}
        """
        pass

    def _parse_init_destinations(self, data):
        """
            Gold 수집 목적지.
        :param data:
        :return:
        """

        """
        Sample :
            0 = {dict: 6} {
                'LocationId': 152, 
                'DefinitionId': 152, 
                'TrainLimitCount': 0, 
                'TrainLimitRefreshTime': '2022-12-30T08:59:01Z', 
                'TrainLimitRefreshesAt': '2022-12-30T08:59:01Z', 
                'Multiplier': 0
            }
            1 = {dict: 6} {'LocationId': 230, 'DefinitionId': 230, 'TrainLimitCount': 0, 'TrainLimitRefreshTime': '2022-12-30T09:01:58Z', 'TrainLimitRefreshesAt': '2022-12-30T09:01:58Z', 'Multiplier': 0}
            2 = {dict: 6} {'LocationId': 329, 'DefinitionId': 304, 'TrainLimitCount': 0, 'TrainLimitRefreshTime': '2022-12-30T09:01:53Z', 'TrainLimitRefreshesAt': '2022-12-30T09:01:53Z', 'Multiplier': 0}
            3 = {dict: 6} {'LocationId': 406, 'DefinitionId': 406, 'TrainLimitCount': 0, 'TrainLimitRefreshTime': '2022-12-30T09:01:46Z', 'TrainLimitRefreshesAt': '2022-12-30T09:01:46Z', 'Multiplier': 0}        
        """
        destination = data.get('Destinations')
        if destination:
            bulk_list = PlayerDestination.create_instance(data=destination, version_id=self.run_version.id)

            if bulk_list:
                PlayerDestination.objects.bulk_create(bulk_list, 100)

    def _parse_init_factories(self, data):
        """

        :param data:
        :return:
        """
        """
        Sample:
            'Factories' = {list: 1} [{'DefinitionId': 1, 'SlotCount': 2, 'ProductOrders': []}]
                 0 = {dict: 3} {'DefinitionId': 1, 'SlotCount': 2, 'ProductOrders': []}
                  'DefinitionId' = {int} 1
                  'SlotCount' = {int} 2
                  'ProductOrders' = {list: 0} []
            'NextVideoSpeedUpAt' = {str} '2022-12-29T11:35:02Z'
        Sample 2:
            'Factories' = {list: 8} [{'DefinitionId': 1, 'SlotCount': 6, 'ProductOrders': [{'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:30:12Z', 'FinishesAt': '2022-12-30T00:30:12Z'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:35:12Z', 'FinishesAt': '2022-12-30T00:35:12Z'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T02:42:35Z', 'FinishesAt': '2022-12-30T02:42:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:12:35Z', 'FinishesAt': '2022-12-30T03:12:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:42:35Z', 'FinishesAt': '2022-12-30T03:42:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T04:12:35Z', 'FinishesAt': '2022-12-30T04:12:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}, {'Product': {'Id': 104, 'Amount': ...
                 0 = {dict: 3} {'DefinitionId': 1, 'SlotCount': 6, 'ProductOrders': [{'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:30:12Z', 'FinishesAt': '2022-12-30T00:30:12Z'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:35:12Z', 'FinishesAt': '2022-12-30T00:35:12Z'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T02:42:35Z', 'FinishesAt': '2022-12-30T02:42:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:12:35Z', 'FinishesAt': '2022-12-30T03:12:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:42:35Z', 'FinishesAt': '2022-12-30T03:42:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T04:12:35Z', 'FinishesAt': '2022-12-30T04:12:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}, {'Product': {'Id': 104, 'Amount': 4...
                    'DefinitionId' = {int} 1
                    'SlotCount' = {int} 6
                    'ProductOrders' = {list: 12} [{'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:30:12Z', 'FinishesAt': '2022-12-30T00:30:12Z'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:35:12Z', 'FinishesAt': '2022-12-30T00:35:12Z'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T02:42:35Z', 'FinishesAt': '2022-12-30T02:42:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:12:35Z', 'FinishesAt': '2022-12-30T03:12:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:42:35Z', 'FinishesAt': '2022-12-30T03:42:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T04:12:35Z', 'FinishesAt': '2022-12-30T04:12:35Z'}, {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}, {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}, {'Product': {'Id': 107,...
                        00 = {dict: 4} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:30:12Z', 'FinishesAt': '2022-12-30T00:30:12Z'}
                        01 = {dict: 4} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:35:12Z', 'FinishesAt': '2022-12-30T00:35:12Z'}
                        02 = {dict: 4} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T02:42:35Z', 'FinishesAt': '2022-12-30T02:42:35Z'}
                        03 = {dict: 4} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:12:35Z', 'FinishesAt': '2022-12-30T03:12:35Z'}
                        04 = {dict: 4} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:42:35Z', 'FinishesAt': '2022-12-30T03:42:35Z'}
                        05 = {dict: 4} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T04:12:35Z', 'FinishesAt': '2022-12-30T04:12:35Z'}
                        06 = {dict: 2} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}
                        07 = {dict: 2} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}
                        08 = {dict: 2} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}
                        09 = {dict: 2} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}
                        10 = {dict: 2} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}
                        11 = {dict: 2} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}                    
        """

        if data:
            video = data.pop('NextVideoSpeedUpAt', None)
            factories = data.get('Factories', [])

            factory_bulk_list, product_bulk_list = PlayerFactory.create_instance(data=factories, version_id=self.run_version.id)

            if factory_bulk_list:
                PlayerFactory.objects.bulk_create(factory_bulk_list, 100)

            if product_bulk_list:
                PlayerFactoryProductOrder.objects.bulk_create(product_bulk_list, 100)

        self.print_remain('_parse_init_factories', data)

    def _parse_init_jobs(self, data):
        """

        :param data:
        :return:
        """

        """
        Sample : 
            'Jobs' = {list: 4} [{'Id': '3b4581c4-b51f-445b-9a57-07f3c6c0f591', 'JobLocationId': 152, 'JobLevel': 2, 'Sequence': 0, 'JobType': 8, 'Duration': 20, 'ConditionMultiplier': 1, 'RewardMultiplier': 1, 'RequiredArticle': {'Id': 100, 'Amount': 30}, 'CurrentArticleAmount': 15, 'Reward': {'Items': [{'Id': 8, 'Value': 4, 'Amount': 40}, {'Id': 8, 'Value': 1, 'Amount': 15}, {'Id': 8, 'Value': 3, 'Amount': 40}]}, 'Bonus': {'Reward': {'Items': []}}, 'Requirements': [{'Type': 'region', 'Value': 1}], 'UnlocksAt': '2022-08-27T06:01:41Z'}, {'Id': 'f1a6673b-343d-4c13-8cb1-af7cf994742d', 'JobLocationId': 158, 'JobLevel': 1, 'Sequence': 0, 'JobType': 5, 'Duration': 1800, 'ConditionMultiplier': 1, 'RewardMultiplier': 1, 'RequiredArticle': {'Id': 104, 'Amount': 12}, 'CurrentArticleAmount': 0, 'Reward': {'Items': [{'Id': 8, 'Value': 4, 'Amount': 25}, {'Id': 8, 'Value': 1, 'Amount': 10}, {'Id': 8, 'Value': 3, 'Amount': 30}]}, 'Bonus': {'Reward': {'Items': []}}, 'Requirements': [{'Type': 'region', 'Value': 1}, {'Type': 'rarity'...
             0 = {dict: 14} {'Id': '3b4581c4-b51f-445b-9a57-07f3c6c0f591', 'JobLocationId': 152, 'JobLevel': 2, 'Sequence': 0, 'JobType': 8, 'Duration': 20, 'ConditionMultiplier': 1, 'RewardMultiplier': 1, 'RequiredArticle': {'Id': 100, 'Amount': 30}, 'CurrentArticleAmount': 15, 'Reward': {'Items': [{'Id': 8, 'Value': 4, 'Amount': 40}, {'Id': 8, 'Value': 1, 'Amount': 15}, {'Id': 8, 'Value': 3, 'Amount': 40}]}, 'Bonus': {'Reward': {'Items': []}}, 'Requirements': [{'Type': 'region', 'Value': 1}], 'UnlocksAt': '2022-08-27T06:01:41Z'}
              'Id' = {str} '3b4581c4-b51f-445b-9a57-07f3c6c0f591'
              'JobLocationId' = {int} 152
              'JobLevel' = {int} 2
              'Sequence' = {int} 0
              'JobType' = {int} 8
              'Duration' = {int} 20
              'ConditionMultiplier' = {int} 1
              'RewardMultiplier' = {int} 1
              'RequiredArticle' = {dict: 2} {'Id': 100, 'Amount': 30}
              'CurrentArticleAmount' = {int} 15
              'Reward' = {dict: 1} {'Items': [{'Id': 8, 'Value': 4, 'Amount': 40}, {'Id': 8, 'Value': 1, 'Amount': 15}, {'Id': 8, 'Value': 3, 'Amount': 40}]}
              'Bonus' = {dict: 1} {'Reward': {'Items': []}}
              'Requirements' = {list: 1} [{'Type': 'region', 'Value': 1}]
              'UnlocksAt' = {str} '2022-08-27T06:01:41Z'
              __len__ = {int} 14
             1 = {dict: 13} {'Id': 'f1a6673b-343d-4c13-8cb1-af7cf994742d', 'JobLocationId': 158, 'JobLevel': 1, 'Sequence': 0, 'JobType': 5, 'Duration': 1800, 'ConditionMultiplier': 1, 'RewardMultiplier': 1, 'RequiredArticle': {'Id': 104, 'Amount': 12}, 'CurrentArticleAmount': 0, 'Reward': {'Items': [{'Id': 8, 'Value': 4, 'Amount': 25}, {'Id': 8, 'Value': 1, 'Amount': 10}, {'Id': 8, 'Value': 3, 'Amount': 30}]}, 'Bonus': {'Reward': {'Items': []}}, 'Requirements': [{'Type': 'region', 'Value': 1}, {'Type': 'rarity', 'Value': 3}]}
             2 = {dict: 13} {'Id': '7b3ac11b-e040-4903-ab58-ea846c16d0b5', 'JobLocationId': 161, 'JobLevel': 1, 'Sequence': 0, 'JobType': 8, 'Duration': 20, 'ConditionMultiplier': 1, 'RewardMultiplier': 1, 'RequiredArticle': {'Id': 100, 'Amount': 30}, 'CurrentArticleAmount': 0, 'Reward': {'Items': [{'Id': 8, 'Value': 4, 'Amount': 25}, {'Id': 8, 'Value': 1, 'Amount': 10}]}, 'Bonus': {'Reward': {'Items': []}}, 'Requirements': [{'Type': 'region', 'Value': 1}]}
             3 = {dict: 13} {'Id': 'fee4f465-e72b-444e-bc42-f39006c40cab', 'JobLocationId': 162, 'JobLevel': 1, 'Sequence': 0, 'JobType': 8, 'Duration': 30, 'ConditionMultiplier': 1, 'RewardMultiplier': 1, 'RequiredArticle': {'Id': 100, 'Amount': 30}, 'CurrentArticleAmount': 0, 'Reward': {'Items': [{'Id': 8, 'Value': 4, 'Amount': 25}, {'Id': 8, 'Value': 1, 'Amount': 10}]}, 'Bonus': {'Reward': {'Items': []}}, 'Requirements': [{'Type': 'region', 'Value': 1}]}
             __len__ = {int} 4
            'NextReplaceAt' = {str} '2022-12-29T11:35:02Z'
            'NextVideoReplaceAt' = {str} '2022-12-29T11:35:02Z'       
        Sample 2:

          {
            "Id": "6ea8ce07-6d49-487a-b6fd-ce737a2a6fc2",
            "JobLocationId": 100007,
            "JobLevel": 9,
            "JobType": 45,
            "Duration": 3600,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {
              "Id": 100004,
              "Amount": 8300
            },
            "CurrentArticleAmount": 3016,
            "Reward": {
              "Items": [
                {
                  "Id": 8,
                  "Value": 100000,
                  "Amount": 3350
                },
                {
                  "Id": 8,
                  "Value": 100003,
                  "Amount": 1750
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
                "Value": 4
              },
              {
                "Type": "content_category",
                "Value": 3
              }
            ],
            "UnlocksAt": "2022-12-05T12:00:00Z",
            "ExpiresAt": "2023-03-03T12:00:00Z"
          },         
        """

        _ = data.pop('NextReplaceAt', None)
        _ = data.pop('NextVideoReplaceAt', None)
        jobs = data.get('Jobs')
        if jobs:
            bulk_list = PlayerJob.create_instance(data=jobs, version_id=self.run_version.id)

            if bulk_list:
                PlayerJob.objects.bulk_create(bulk_list, 100)

        self.print_remain('_parse_init_jobs', data)

    def _parse_init_player(self, data):
        """

        :param data:
        :return:
        """
        """
        Sample:
            'PlayerLevel' = {int} 4
            'PlayerId' = {int} 62794770
            'PlayerName' = {str} 'Player_62794770'
            'AvatarId' = {int} 1
            'Company' = {dict: 3} {'Rank': 1, 'Value': 599, 'Stats': [{'Type': 'complete_job', 'Progress': 27}, {'Type': 'open_train_container', 'Progress': 32}, {'Type': 'own_unique_trains', 'Progress': 500}, {'Type': 'population_max', 'Progress': 40}]}
                 'Rank' = {int} 1
                 'Value' = {int} 599
                 'Stats' = {list: 4} [{'Type': 'complete_job', 'Progress': 27}, {'Type': 'open_train_container', 'Progress': 32}, {'Type': 'own_unique_trains', 'Progress': 500}, {'Type': 'population_max', 'Progress': 40}]
                      0 = {dict: 2} {'Type': 'complete_job', 'Progress': 27}
                      1 = {dict: 2} {'Type': 'open_train_container', 'Progress': 32}
                      2 = {dict: 2} {'Type': 'own_unique_trains', 'Progress': 500}
                      3 = {dict: 2} {'Type': 'population_max', 'Progress': 40}        
        """
        player_level = data.pop('PlayerLevel')
        player_id = data.pop('PlayerId')
        player_name = data.pop('PlayerName')
        avatar_id = data.pop('AvatarId')
        self.run_version.player_id = player_id or ''
        self.run_version.player_name = player_name or ''
        self.run_version.level = player_level or 0
        self.run_version.save(update_fields=[
            'player_id',
            'player_name',
            'level',
        ])

    def _parse_init_regions(self, data):
        """

        :param data:
        :return:
        """
        """
        Sample:
            'RegionProgressions' = {list: 0} []
            'Quests' = {list: 4} [{'JobLocationId': 150, 'Milestone': 1, 'Progress': 1}, {'JobLocationId': 152, 'Milestone': 1, 'Progress': 1}, {'JobLocationId': 159, 'Milestone': 3, 'Progress': 3}, {'JobLocationId': 160, 'Milestone': 4, 'Progress': 4}]
             0 = {dict: 3} {'JobLocationId': 150, 'Milestone': 1, 'Progress': 1}
             1 = {dict: 3} {'JobLocationId': 152, 'Milestone': 1, 'Progress': 1}
             2 = {dict: 3} {'JobLocationId': 159, 'Milestone': 3, 'Progress': 3}
             3 = {dict: 3} {'JobLocationId': 160, 'Milestone': 4, 'Progress': 4}
             __len__ = {int} 4
            'VisitedRegions' = {list: 1} [101]        
        """
        pass

    def _parse_init_trains(self, data):
        """

        :param data:
        :return:
        """
        """
        Sample
            'Trains' = {list: 5} [{'InstanceId': 1, 'DefinitionId': 3, 'Level': 1, 'Route': {'RouteType': 'destination', 'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:47Z', 'ArrivalTime': '2022-12-27T10:05:17Z'}}, {'InstanceId': 2, 'DefinitionId': 5, 'Level': 1, 'Route': {'RouteType': 'destination', 'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:45Z', 'ArrivalTime': '2022-12-27T10:05:15Z'}}, {'InstanceId': 3, 'DefinitionId': 4, 'Level': 1, 'Route': {'RouteType': 'destination', 'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:46Z', 'ArrivalTime': '2022-12-27T10:05:16Z'}}, {'InstanceId': 4, 'DefinitionId': 2, 'Level': 1}, {'InstanceId': 5, 'DefinitionId': 1, 'Level': 1}]
                 0 = {dict: 4} {'InstanceId': 1, 'DefinitionId': 3, 'Level': 1, 'Route': {'RouteType': 'destination', 'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:47Z', 'ArrivalTime': '2022-12-27T10:05:17Z'}}
                 1 = {dict: 4} {'InstanceId': 2, 'DefinitionId': 5, 'Level': 1, 'Route': {'RouteType': 'destination', 'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:45Z', 'ArrivalTime': '2022-12-27T10:05:15Z'}}
                 2 = {dict: 4} {'InstanceId': 3, 'DefinitionId': 4, 'Level': 1, 'Route': {'RouteType': 'destination', 'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:46Z', 'ArrivalTime': '2022-12-27T10:05:16Z'}}
                 3 = {dict: 3} {'InstanceId': 4, 'DefinitionId': 2, 'Level': 1}
                 4 = {dict: 3} {'InstanceId': 5, 'DefinitionId': 1, 'Level': 1}
            'ReturnAsArray' = {bool} False
        """
        """
        Sample 2:
            "Trains": [
                  {
                    "InstanceId": 1,
                    "DefinitionId": 3,
                    "Level": 17,
                    "Route": {
                      "RouteType": "destination",
                      "DefinitionId": 150,
                      "DepartureTime": "2022-12-30T00:44:24Z",
                      "ArrivalTime": "2022-12-30T00:44:54Z"
                    }
                  },
                  {
                    "InstanceId": 19,
                    "DefinitionId": 15,
                    "Level": 41,
                    "Route": {
                      "RouteType": "destination",
                      "DefinitionId": 231,
                      "DepartureTime": "2022-12-30T06:23:13Z",
                      "ArrivalTime": "2022-12-30T06:28:13Z"
                    },
                    "TrainLoad": {
                      "Id": 103,
                      "Amount": 60
                    }
                  },
                {
                "InstanceId": 14,
                "DefinitionId": 10,
                "Level": 17,
                "Route": {
                  "RouteType": "job",
                  "DefinitionId": 34002,
                  "DepartureTime": "2022-12-08T06:41:34Z",
                  "ArrivalTime": "2022-12-08T07:41:34Z"
                }
              },
          {
            "InstanceId": 159,
            "DefinitionId": 35000,
            "Region": 4,
            "Level": 29,
            "Route": {
              "RouteType": "destination",
              "DefinitionId": 403,
              "DepartureTime": "2022-12-29T13:37:32Z",
              "ArrivalTime": "2022-12-29T13:42:32Z"
            }
          }              
        """

        trains = data.get('Trains')
        if trains:
            bulk_list = PlayerTrain.create_instance(data=trains, version_id=self.run_version.id)

            if bulk_list:
                PlayerTrain.objects.bulk_create(bulk_list, 100)

        self.print_remain('_parse_init_trains', data)

    def _parse_init_warehouse(self, data):
        """
        :param data:
        :return:
        """
        """
        Sample:
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
        """
        if data:
            level = data.pop('Level', None)
            wl = WarehouseLevel.objects.filter(id=level).first()
            self.run_version.warehouse_level = level
            self.run_version.warehouse = wl.capacity if wl else 0
            self.run_version.save(update_fields=['warehouse_level'])

            articles = data.pop('Articles', None)
            if articles:
                bulk_list = PlayerWarehouse.create_instance(data=articles, version_id=self.run_version.id)
                self.print_remain('_parse_init_warehouse', articles)

                if bulk_list:
                    PlayerWarehouse.objects.bulk_create(bulk_list, 100)

    def _parse_init_whistles(self, data):
        """
        :param data:
        :return:
        """
        """
        Sample:
            'Whistles' = {list: 4} [{'Category': 1, 'Position': 3, 'SpawnTime': '2022-12-29T10:32:46Z', 'CollectableFrom': '2022-12-29T10:32:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 2, 'Amount': 1}]}, 'IsForVideoReward': True, 'ExpiresAt': '2999-12-31T00:00:00Z'}, {'Category': 1, 'Position': 4, 'SpawnTime': '2022-12-29T10:33:46Z', 'CollectableFrom': '2022-12-29T10:33:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 8, 'Amount': 1}]}, 'IsForVideoReward': False}, {'Category': 1, 'Position': 1, 'SpawnTime': '2022-12-29T10:31:46Z', 'CollectableFrom': '2022-12-29T10:31:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 6, 'Amount': 1}]}, 'IsForVideoReward': False}, {'Category': 1, 'Position': 2, 'SpawnTime': '2022-12-29T10:32:06Z', 'CollectableFrom': '2022-12-29T10:32:06Z', 'Reward': {'Items': [{'Id': 8, 'Value': 104, 'Amount': 1}]}, 'IsForVideoReward': False}]
                 0 = {dict: 7} {'Category': 1, 'Position': 3, 'SpawnTime': '2022-12-29T10:32:46Z', 'CollectableFrom': '2022-12-29T10:32:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 2, 'Amount': 1}]}, 'IsForVideoReward': True, 'ExpiresAt': '2999-12-31T00:00:00Z'}
                 1 = {dict: 6} {'Category': 1, 'Position': 4, 'SpawnTime': '2022-12-29T10:33:46Z', 'CollectableFrom': '2022-12-29T10:33:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 8, 'Amount': 1}]}, 'IsForVideoReward': False}
                 2 = {dict: 6} {'Category': 1, 'Position': 1, 'SpawnTime': '2022-12-29T10:31:46Z', 'CollectableFrom': '2022-12-29T10:31:46Z', 'Reward': {'Items': [{'Id': 8, 'Value': 6, 'Amount': 1}]}, 'IsForVideoReward': False}
                 3 = {dict: 6} {'Category': 1, 'Position': 2, 'SpawnTime': '2022-12-29T10:32:06Z', 'CollectableFrom': '2022-12-29T10:32:06Z', 'Reward': {'Items': [{'Id': 8, 'Value': 104, 'Amount': 1}]}, 'IsForVideoReward': False}        
        """
        whistles = data.get('Whistles')
        if whistles:
            bulk_list, bulk_item_list = PlayerWhistle.create_instance(data=whistles, version_id=self.run_version.id)

            if bulk_list:
                PlayerWhistle.objects.bulk_create(bulk_list, 100)

            if bulk_item_list:
                PlayerWhistleItem.objects.bulk_create(bulk_item_list, 100)

        self.print_remain('_parse_init_whistles', data)

    def _parse_init_ship_offers(self, data):
        """

        :param data:
        :return:
        """

        """       
        """
        pass

    def _parse_init_contracts(self, data):
        """
        {
            'Contracts': [
                {
                    'Slot': 1,
                    'ContractListId': 3,
                    'Conditions': [{'Id': 112, 'Amount': 99}, {'Id': 125, 'Amount': 313}, {'Id': 115, 'Amount': 254}],
                    'Reward': {
                        'Items': [{'Id': 8, 'Value': 3, 'Amount': 320}, {'Id': 8, 'Value': 10, 'Amount': 14}, {'Id': 8, 'Value': 12, 'Amount': 6}, {'Id': 8, 'Value': 11, 'Amount': 10}]
                    },
                    'UsableFrom': '2023-01-08T07:44:58Z',
                    'AvailableFrom': '1970-01-01T00:00:00Z',
                    'AvailableTo': '2999-12-31T00:00:00Z'
                },
                {
                'Slot': 1, 'ContractListId': 100001, 'Conditions': [{'Id': 111, 'Amount': 85}], 'Reward': {'Items': [{'Id': 8, 'Value': 100004, 'Amount': 40}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 2, 'ContractListId': 100001, 'Conditions': [{'Id': 109, 'Amount': 116}], 'Reward': {'Items': [{'Id': 8, 'Value': 100004, 'Amount': 80}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 3, 'ContractListId': 100001, 'Conditions': [{'Id': 115, 'Amount': 308}], 'Reward': {'Items': [{'Id': 8, 'Value': 100004, 'Amount': 160}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 4, 'ContractListId': 100001, 'Conditions': [{'Id': 111, 'Amount': 85}], 'Reward': {'Items': [{'Id': 8, 'Value': 100005, 'Amount': 37}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 5, 'ContractListId': 100001, 'Conditions': [{'Id': 104, 'Amount': 369}], 'Reward': {'Items': [{'Id': 8, 'Value': 100005, 'Amount': 75}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 6, 'ContractListId': 100001, 'Conditions': [{'Id': 124, 'Amount': 170}], 'Reward': {'Items': [{'Id': 8, 'Value': 100005, 'Amount': 150}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 7, 'ContractListId': 100001, 'Conditions': [{'Id': 124, 'Amount': 85}], 'Reward': {'Items': [{'Id': 8, 'Value': 100006, 'Amount': 35}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 8, 'ContractListId': 100001, 'Conditions': [{'Id': 119, 'Amount': 90}], 'Reward': {'Items': [{'Id': 8, 'Value': 100006, 'Amount': 70}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 9, 'ContractListId': 100001, 'Conditions': [{'Id': 118, 'Amount': 141}], 'Reward': {'Items': [{'Id': 8, 'Value': 100006, 'Amount': 140}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 10, 'ContractListId': 100001, 'Conditions': [{'Id': 111, 'Amount': 85}], 'Reward': {'Items': [{'Id': 8, 'Value': 100007, 'Amount': 32}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 11, 'ContractListId': 100001, 'Conditions': [{'Id': 115, 'Amount': 231}], 'Reward': {'Items': [{'Id': 8, 'Value': 100007, 'Amount': 65}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 12, 'ContractListId': 100001, 'Conditions': [{'Id': 232, 'Amount': 492}], 'Reward': {'Items': [{'Id': 8, 'Value': 100007, 'Amount': 130}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 13, 'ContractListId': 100001, 'Conditions': [{'Id': 106, 'Amount': 92}], 'Reward': {'Items': [{'Id': 8, 'Value': 100008, 'Amount': 30}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 14, 'ContractListId': 100001, 'Conditions': [{'Id': 117, 'Amount': 176}], 'Reward': {'Items': [{'Id': 8, 'Value': 100008, 'Amount': 60}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 15, 'ContractListId': 100001, 'Conditions': [{'Id': 119, 'Amount': 120}], 'Reward': {'Items': [{'Id': 8, 'Value': 100008, 'Amount': 120}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 16, 'ContractListId': 100001, 'Conditions': [{'Id': 119, 'Amount': 60}], 'Reward': {'Items': [{'Id': 8, 'Value': 100009, 'Amount': 27}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 17, 'ContractListId': 100001, 'Conditions': [{'Id': 117, 'Amount': 176}], 'Reward': {'Items': [{'Id': 8, 'Value': 100009, 'Amount': 55}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 18, 'ContractListId': 100001, 'Conditions': [{'Id': 115, 'Amount': 308}], 'Reward': {'Items': [{'Id': 8, 'Value': 100009, 'Amount': 110}]}, 'UsableFrom': '2023-01-08T02:52:17Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 19, 'ContractListId': 100001, 'Conditions': [{'Id': 224, 'Amount': 82}], 'Reward': {'Items': [{'Id': 8, 'Value': 100010, 'Amount': 25}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 20, 'ContractListId': 100001, 'Conditions': [{'Id': 105, 'Amount': 137}], 'Reward': {'Items': [{'Id': 8, 'Value': 100010, 'Amount': 50}]}, 'UsableFrom': '2023-01-08T01:44:04Z', 'ExpiresAt': '2023-02-27T12:00:00Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}, {'Slot': 21, 'ContractListId': 100001, 'Conditions': [{'Id': 119, 'Amount': 120}], 'Reward': {'Items': [{'Id': 8, 'Value': 100010, 'Amount': 100}]}, 'UsableFrom': '2023-01-08T02:52:11Z', 'AvailableFrom': '2022-12-05T12:00:00Z', 'AvailableTo': '2023-02-27T12:00:00Z'}], 'ContractLists': [{'ContractListId': 3, 'NextReplaceAt': '2023-01-08T03:07:59Z', 'NextVideoReplaceAt': '2023-01-08T03:07:59Z', 'NextVideoRentAt': '2023-01-08T03:07:59Z', 'NextVideoSpeedUpAt': '2023-01-08T03:07:59Z'}, {'ContractListId': 100001, 'AvailableTo': '2023-02-27T12:00:00Z', 'NextReplaceAt': '2023-01-08T03:07:59Z', 'NextVideoReplaceAt': '2023-01-08T03:07:59Z', 'NextVideoRentAt': '2023-01-08T03:07:59Z', 'NextVideoSpeedUpAt': '2023-01-07T17:23:23Z', 'ExpiresAt': '2023-01-08T09:44:04Z'}]}}
        :param data:
        :return:
        """
        contracts = data.get('Contracts', [])
        contract_list = data.get('ContractLists', [])
        now = timezone.now()

        if contract_list:
            bulk_list = PlayerContractList.create_instance(data=contract_list, version_id=self.run_version.id)
            if bulk_list:
                PlayerContractList.objects.bulk_create(bulk_list)

        if contracts:
            bulk_list = PlayerContract.create_instance(data=contracts, version_id=self.run_version.id)
            if bulk_list:
                PlayerContract.objects.bulk_create(bulk_list)

        self.print_remain('_parse_init_contracts', data)

    def _parse_init_dispatcher(self, data):
        """
        {
            'PermanentLevel': 5,
            'TemporaryDispatchers': [
                {'DefinitionId': 3, 'ExpiredAt': '2022-12-15T05:07:42Z'},
                {'DefinitionId': 4, 'ExpiredAt': '2023-01-02T14:15:02Z'}
            ],
            'VideoRewardAvailableAt': '2023-01-02T19:15:02Z',
            'Dispatchers': [
                {
                    'TemporaryDispatchers': [
                        {'DefinitionId': 3, 'ExpiredAt': '2022-12-15T05:07:42Z'},
                        {'DefinitionId': 4, 'ExpiredAt': '2023-01-02T14:15:02Z'}
                    ],
                    'ContentCategory': 1,
                    'PermanentLevel': 5,
                    'VideoRewardAvailableAt': '2023-01-02T19:15:02Z'
                },
                {
                    'TemporaryDispatchers': [
                        {'DefinitionId': 34, 'ExpiredAt': '2023-01-07T13:28:26Z'}
                    ],
                    'ContentCategory': 3,
                    'PermanentLevel': 5,
                    'VideoRewardAvailableAt': '2023-01-07T16:28:26Z'
                }
            ]
        }
        :return:
        """
        _ = data.pop('PermanentLevel', None)
        _ = data.pop('TemporaryDispatchers', None)
        _ = data.pop('VideoRewardAvailableAt', None)
        dispatchers = data.pop('Dispatchers', [])

        for dispatcher in dispatchers:
            dispatcher.pop('TemporaryDispatchers')

            content_category = dispatcher.pop('ContentCategory', None)
            permanent_level = dispatcher.pop('PermanentLevel', None)
            video = dispatcher.pop('VideoRewardAvailableAt', None)
            if content_category == 1:
                self.run_version.dispatchers = permanent_level + 2
            elif content_category == 3:
                self.run_version.guild_dispatchers = permanent_level + 2

        self.run_version.save()

        self.print_remain('_parse_init_dispatcher', data)

    def reduce(self, data):
        if isinstance(data, list):
            ret = []
            for v in data:
                v = self.reduce(v)
                if v:
                    ret.append(v)
            return ret
        if isinstance(data, dict):
            ret = {}
            for f, v in data.items():
                v = self.reduce(v)
                if v:
                    ret.update({f: v})
            return ret
        return data

    def print_remain(self, msg, data):
        data = self.reduce(data=data)
        if data:
            print('[REMAIN]', msg, data)