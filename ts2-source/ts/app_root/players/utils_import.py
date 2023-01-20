import json
import uuid
from hashlib import md5
from typing import Dict, Callable, Iterator, Tuple

from django.conf import settings
from django.utils import timezone

from app_root.mixins import ImportHelperMixin
from app_root.players.models import PlayerBuilding, PlayerDestination, PlayerFactory, PlayerFactoryProductOrder, \
    PlayerJob, \
    PlayerTrain, PlayerWarehouse, PlayerWhistle, PlayerWhistleItem, PlayerGift, PlayerContractList, PlayerContract, \
    PlayerAchievement, PlayerDailyReward, PlayerMap, PlayerQuest, PlayerVisitedRegion
from app_root.servers.models import TSWarehouseLevel, EndPoint

# , , PlayerQuest, PlayerVisitedRegion,
from core.utils import disk_cache, Logger

LOGGING_MENU = 'plyaers.import'


class InitdataHelper(ImportHelperMixin):
    def get_urls(self) -> Iterator[Tuple[str, str, str, str]]:

        idx = 1

        for url in EndPoint.get_urls(EndPoint.ENDPOINT_INIT_DATA_URLS):
            yield url, f'init_sent_{idx}', f'init_server_{idx}', f'init_recv_{idx}'
            idx = 3 - idx

    def get_data(self, url) -> str:
        """
        'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
        'PXFD-Retry-No': '0',
        'PXFD-Sent-At': str(sent_at),
        'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
        'PXFD-Device-Token': device_id,
        'PXFD-Game-Access-Token': game_access_token,
        'PXFD-Player-Id': player_id,
        'Accept-Encoding': 'gzip, deflate',

        :param url:
        :return:
        """

        mask = self.HEADER_REQUEST_ID \
               | self.HEADER_RETRY_NO \
               | self.HEADER_SENT_AT \
               | self.HEADER_CLIENT_INFORMATION \
               | self.HEADER_CLIENT_VERSION \
               | self.HEADER_DEVICE_TOKEN \
               | self.HEADER_GAME_ACCESS_TOKEN \
               | self.HEADER_PLAYER_ID

        headers = self.get_headers(mask=mask)
        
        return self.get(
            url=url,
            headers=headers,
            params={}
        )
    
    # def update_player_info(self):
        # xp = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=1).first()
        # gem = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=2).first()
        # gold = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=3).first()
        # key = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=4).first()
        # 
        # self.run_version.xp = xp.amount if xp else 0
        # self.run_version.gem = gem.amount if gem else 0
        # self.run_version.gold = gold.amount if gold else 0
        # self.run_version.key = key.amount if key else 0
        # 
        # common_parts = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=6).first()
        # rare_parts = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=7).first()
        # epic_parts = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=8).first()
        # legendary_parts = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=9).first()
        # 
        # self.run_version.train_parts_common = common_parts.amount if common_parts else 0
        # self.run_version.train_parts_rare = rare_parts.amount if rare_parts else 0
        # self.run_version.train_parts_epic = epic_parts.amount if epic_parts else 0
        # self.run_version.train_parts_legendary = legendary_parts.amount if legendary_parts else 0
        # 
        # blue = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=10).first()
        # yellow = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=11).first()
        # red = PlayerWarehouse.objects.filter(version_id=self.version.id, article_id=12).first()
        # 
        # self.run_version.blue_city_plans = blue.amount if blue else 0
        # self.run_version.yellow_city_plans = yellow.amount if yellow else 0
        # self.run_version.red_city_plans = red.amount if red else 0
        # 
        # self.run_version.save()

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
            'locations': self._parse_init_locations,
            'achievements': self._parse_init_achievements,
            'daily_reward': self._parse_init_daily_reward,
            'milestones': self._parse_init_milestones,
            'task_lists': self._parse_init_task_lists,
            'seasons': self._parse_init_seasons,
            'commodities': self._parse_init_commodities,
            'offer_wall': self._parse_init_offer_wall,
            'containers': self._parse_init_containers,
            'maps': self._parse_init_maps,

            'ab_test': self._parse_init_not_yet_implemented,
            'login_profile': self._parse_init_not_yet_implemented,
            'game_features': self._parse_init_not_yet_implemented,
            'unlocked_contents': self._parse_init_not_yet_implemented,
            'shop': self._parse_init_not_yet_implemented,
            'reminders': self._parse_init_not_yet_implemented,
            'markets': self._parse_init_not_yet_implemented,
            'guild': self._parse_init_not_yet_implemented,
            'game': self._parse_init_not_yet_implemented,
            'placements': self._parse_init_not_yet_implemented,
            'player_feature': self._parse_init_not_yet_implemented,
            'prestige': self._parse_init_not_yet_implemented,
            'ship_loop': self._parse_init_not_yet_implemented,
            'tutorial': self._parse_init_not_yet_implemented,
            'tickets': self._parse_init_not_yet_implemented,
            'communities': self._parse_init_not_yet_implemented,
            'city_building_shop': self._parse_init_not_yet_implemented,
            'calendars': self._parse_init_not_yet_implemented,
            'boosts': self._parse_init_not_yet_implemented,
            'vouchers': self._parse_init_not_yet_implemented,
        }
        json_data = json.loads(data, strict=False)
        # self.check_response(json_data=json_data)

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
            bulk_list, _ = PlayerGift.create_instance(data=gifts, version_id=self.version.id)
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
            self.version.population = population.get('LastCalculatedCount') or 0
            self.version.save(update_fields=['population'])

        # Buildings
        buildings = data.get('Buildings')
        if buildings:

            bulk_list, _ = PlayerBuilding.create_instance(data=buildings, version_id=self.version.id)

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
            bulk_list, _ = PlayerDestination.create_instance(data=destination, version_id=self.version.id)

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

            factory_bulk_list, product_bulk_list = PlayerFactory.create_instance(data=factories,
                                                                                 version_id=self.version.id)

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
            bulk_list, _ = PlayerJob.create_instance(data=jobs, version_id=self.version.id)

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
        self.version.player_id = player_id or ''
        self.version.player_name = player_name or ''
        self.version.level = player_level or 0
        self.version.save(update_fields=[
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

        quests = data.get('Quests')
        if quests:
            bulk_list, _ = PlayerQuest.create_instance(data=quests, version_id=self.version.id)
            if bulk_list:
                PlayerQuest.objects.bulk_create(bulk_list, 100)

        visited_regions = data.get('VisitedRegions')
        if visited_regions:
            bulk_list, _ = PlayerVisitedRegion.create_instance(data=visited_regions, version_id=self.version.id)
            if bulk_list:
                PlayerVisitedRegion.objects.bulk_create(bulk_list, 100)

        self.print_remain('_parse_init_regions', data)

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
            bulk_list, _ = PlayerTrain.create_instance(data=trains, version_id=self.version.id)

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
            # wl = TSWarehouseLevel.objects.filter(id=level).first()
            self.version.warehouse_level = level
            # self.version.warehouse = wl.capacity if wl else 0
            self.version.save(update_fields=['warehouse_level'])

            articles = data.pop('Articles', None)
            if articles:
                bulk_list, _ = PlayerWarehouse.create_instance(data=articles, version_id=self.version.id)
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
            bulk_list, bulk_item_list = PlayerWhistle.create_instance(data=whistles, version_id=self.version.id)

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
            bulk_list, _ = PlayerContractList.create_instance(data=contract_list, version_id=self.version.id)
            if bulk_list:
                PlayerContractList.objects.bulk_create(bulk_list)

        if contracts:
            contract_list = list(PlayerContractList.objects.filter(version_id=self.version.id).all())
            bulk_list, _ = PlayerContract.create_instance(data=contracts, version_id=self.version.id, contract_list=contract_list)
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
                self.version.dispatchers = permanent_level
            elif content_category == 3:
                self.version.guild_dispatchers = permanent_level

        self.version.save()

        self.print_remain('_parse_init_dispatcher', data)

    def _parse_init_locations(self, data):
        pass

    def _parse_init_achievements(self, data):
        """

        "Achievements": [
          {
            "AchievementId": "chemical_and_refinery_production",
            "Level": 5,
            "Progress": 1456
          },
          {
            "AchievementId": "city_task",
            "Level": 5,
            "Progress": 2212
          },
          {
            "AchievementId": "complete_job",
            "Level": 5,
            "Progress": 2687
          },

        :param data:
        :return:
        """
        achievements = data.get('Achievements')
        _ = data.pop('ReturnAsArray')
        if achievements:
            bulk_list, _ = PlayerAchievement.create_instance(data=achievements, version_id=self.version.id)

            if bulk_list:
                PlayerAchievement.objects.bulk_create(bulk_list, 100)

        self.print_remain('_parse_init_achievements', data)

    def _parse_init_daily_reward(self, data):
        """

        "AvailableFrom": "2023-01-16T00:00:00Z",
        "ExpireAt": "2023-01-16T23:59:59Z",
        "Rewards": [
          {
            "Items": [ { "Id": 8, "Value": 3, "Amount": 450 } ]
          },
          {
            "Items": [ { "Id": 8, "Value": 4, "Amount": 40 } ]
          },
          {
            "Items": [ {"Id": 8,"Value": 8,"Amount": 9}]
          },
          {
            "Items": [{"Id": 8,"Value": 2,"Amount": 10}]
          },
          {
            "Items": [{"Id": 1,"Value": 3}]
          }
        ],
        "PoolId": 3,
        "Day": 0
      }

        :param data:
        :return:
        """
        bulk_list, _ = PlayerDailyReward.create_instance(data=data, version_id=self.version.id)

        if bulk_list:
            PlayerDailyReward.objects.bulk_create(bulk_list, 100)

        self.print_remain('_parse_init_daily_reward', data)

    def _parse_init_milestones(self, data):
        pass

    def _parse_init_task_lists(self, data):
        pass

    def _parse_init_seasons(self, data):
        pass

    def _parse_init_commodities(self, data):
        pass

    def _parse_init_offer_wall(self, data):
        pass

    def _parse_init_containers(self, data):
        pass

    def _parse_init_maps(self, data):
        maps = data.get('Maps')
        if maps:
            bulk_list, _ = PlayerMap.create_instance(data=maps, version_id=self.version.id)

            if bulk_list:
                PlayerMap.objects.bulk_create(bulk_list, 100)

        self.print_remain('_parse_init_maps', data)

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
