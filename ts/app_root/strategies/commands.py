import json
import random
from datetime import timedelta, datetime
from time import sleep
from typing import List, Iterator, Tuple, Dict, Optional, Callable

from django.conf import settings

from app_root.exceptions import check_response
from app_root.mixins import ImportHelperMixin
from app_root.players.models import PlayerTrain, PlayerDailyReward, PlayerWhistle, PlayerWhistleItem, PlayerDestination, \
    PlayerDailyOfferContainer, PlayerDailyOffer, PlayerDailyOfferItem
from app_root.servers.models import RunVersion, EndPoint
from app_root.strategies.managers import warehouse_add_article, whistle_remove, trains_unload, \
    trains_set_destination, container_offer_set_used, destination_set_used, daily_offer_set_used
from app_root.utils import get_curr_server_str_datetime_s, get_curr_server_datetime


class BaseCommand(object):
    """
        BaseCommand
    """
    version: RunVersion

    COMMAND = ''
    SLEEP_RANGE = (0.5, 1.5)

    def __init__(self, version: RunVersion, **kwargs):
        super(BaseCommand, self).__init__()
        self.version = version

    def get_debug(self) -> dict:
        return {}

    def get_parameters(self) -> dict:
        return {}

    def get_command(self):
        return {
            'Command': self.COMMAND,
            'Time': get_curr_server_str_datetime_s(version=self.version),
            'Parameters': self.get_parameters()
        }

    def duration(self) -> int:
        return 0

    def __str__(self):
        return f'''[{self.COMMAND}] / parameters: {self.get_parameters()}'''

    def post_processing(self, server_data: Dict):
        pass


###################################################################
# COMMAND - common
###################################################################
class HeartBeat(BaseCommand):
    COMMAND = 'Game:Heartbeat'
    SLEEP_RANGE = (0.0, 0.2)


class GameSleep(BaseCommand):
    """
        POST /api/v2/command-processing/run-collection HTTP/1.1
        PXFD-Request-Id: 3d8728e2-8f6d-401d-a603-c59c1bff48af
        PXFD-Retry-No: 0
        PXFD-Sent-At: 2023-01-23T12:53:52.839Z
        PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}
        PXFD-Client-Version: 2.6.3.4068
        PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
        PXFD-Game-Access-Token: f5019986-472e-52ca-b95a-aa520bdbfbca
        PXFD-Player-Id: 62794770
        Content-Type: application/json
        Content-Length: 146
        Host: game.trainstation2.com
        Accept-Encoding: gzip, deflate


        {"Id":42,"Time":"2023-01-23T12:53:52Z","Commands":[{"Command":"Game:WakeUp","Time":"2023-01-23T12:53:04Z","Parameters":{}}],"Transactional":false}

        {"Success":true,"RequestId":"3d8728e2-8f6d-401d-a603-c59c1bff48af","Time":"2023-01-23T12:53:53Z","Data":{"CollectionId":42,"Commands":[]}}
    """
    COMMAND = 'Game:Sleep'
    SLEEP_RANGE = (0.0, 0.2)
    sleep_seconds: int

    def __init__(self, *, sleep_seconds, **kwargs):
        super(GameSleep, self).__init__(**kwargs)
        self.sleep_seconds = sleep_seconds

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {}

    def get_debug(self) -> dict:
        return {
            "Debug": {
                "CollectionsInQueue": 0,
                "CollectionsInQueueIds": ""
            }
        }

    def post_processing(self, server_data: Dict):
        sleep(self.sleep_seconds)


class GameWakeup(BaseCommand):
    """
        POST /api/v2/command-processing/run-collection HTTP/1.1
        PXFD-Request-Id: 3d8728e2-8f6d-401d-a603-c59c1bff48af
        PXFD-Retry-No: 0
        PXFD-Sent-At: 2023-01-23T12:53:52.839Z
        PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}
        PXFD-Client-Version: 2.6.3.4068
        PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
        PXFD-Game-Access-Token: f5019986-472e-52ca-b95a-aa520bdbfbca
        PXFD-Player-Id: 62794770
        Content-Type: application/json
        Content-Length: 146
        Host: game.trainstation2.com
        Accept-Encoding: gzip, deflate


        {"Id":42,"Time":"2023-01-23T12:53:52Z","Commands":[{"Command":"Game:WakeUp","Time":"2023-01-23T12:53:04Z","Parameters":{}}],"Transactional":false}

        {"Success":true,"RequestId":"3d8728e2-8f6d-401d-a603-c59c1bff48af","Time":"2023-01-23T12:53:53Z","Data":{"CollectionId":42,"Commands":[]}}
    """

    COMMAND = 'Game:WakeUp'
    SLEEP_RANGE = (0.0, 0.2)


###################################################################
# COMMAND - Train
###################################################################
class TrainUnloadCommand(BaseCommand):
    """
    기차에서 수집
    {
        "Command":"Train:Unload",
        "Time":"2023-01-11T01:01:44Z",
        "Parameters":{
            "TrainId":10
        }
    }
    """

    COMMAND = 'Train:Unload'
    train: PlayerTrain
    SLEEP_RANGE = (0.2, 0.5)

    def __init__(self, *, train: PlayerTrain, **kwargs):
        super(TrainUnloadCommand, self).__init__(**kwargs)
        self.train = train

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            'TrainId': self.train.instance_id
        }

    def post_processing(self, server_data: Dict):

        warehouse_add_article(
            version=self.version,
            article_id=self.train.load_id,
            amount=self.train.load_amount
        )

        trains_unload(version=self.version, train=self.train)


class TrainSendToDestinationCommand(BaseCommand):
    """
        기차 보내기
        {
            "Id":2,
            "Time":"2023-01-13T03:19:45Z",
            "Commands":[
                {
                    "Command":"Train:DispatchToDestination",
                    "Time":"2023-01-13T03:19:43Z",
                    "Parameters":{
                        "TrainId":9,   (PlayerTrain.instance_id)
                        "DestinationId":150
                    }
                }
            ],
            "Transactional":false
        }
    """

    COMMAND = 'Train:DispatchToDestination'
    train: PlayerTrain
    dest: PlayerDestination
    SLEEP_RANGE = (1.0, 1.5)

    def __init__(self, *, train: PlayerTrain, dest: PlayerDestination, **kwargs):
        super(TrainSendToDestinationCommand, self).__init__(**kwargs)
        self.train = train
        self.dest = dest

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            'TrainId': self.train.instance_id,
            'DestinationId': self.dest.definition_id,
        }

    def post_processing(self, server_data: Dict):
        departure_at = get_curr_server_datetime(version=self.version)
        arrival_at = departure_at + timedelta(seconds=self.dest.definition.travel_duration)
        trains_set_destination(
            version=self.version,
            train=self.train,
            definition_id=self.dest.definition_id,
            departure_at=departure_at,
            arrival_at=arrival_at
        )
        destination_set_used(
            version=self.version,
            dest=self.dest
        )


###################################################################
# Daily Reward
###################################################################
class DailyRewardClaimCommand(BaseCommand):
    """
        "Rewards": [
            {"Items": [{"Id": 8,"Value": 3,"Amount": 450}]},
            {"Items": [{"Id": 8,"Value": 4,"Amount": 40}]},
            {"Items": [{"Id": 8,"Value": 8,"Amount": 9}]},
            {"Items": [{"Id": 8,"Value": 2,"Amount": 10}]},
            {"Items": [{"Id": 1,"Value": 3}]}
        ],
        "PoolId": 3,
        "Day": 4
      }

        #############################################################################
        # 5일차 container
        #############################################################################
        POST /api/v2/command-processing/run-collection HTTP/1.1
        PXFD-Request-Id: 5c5d8dfb-9a07-4423-a951-7cbe41ed2f48
        PXFD-Retry-No: 0
        PXFD-Sent-At: 2023-01-20T00:06:04.736Z
        PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"en"}
        PXFD-Client-Version: 2.6.3.4068
        PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
        PXFD-Game-Access-Token: b99ffa79-8d3c-584d-8c1e-a22dd632610f
        PXFD-Player-Id: 61561146
        Content-Type: application/json
        Content-Length: 151
        Host: game.trainstation2.com
        Accept-Encoding: gzip, deflate

        {"Id":3,"Time":"2023-01-20T00:06:04Z","Commands":[{"Command":"DailyReward:Claim","Time":"2023-01-20T00:06:04Z","Parameters":{}}],"Transactional":false}

        {"Success":true,"RequestId":"5c5d8dfb-9a07-4423-a951-7cbe41ed2f48","Time":"2023-01-20T00:06:05Z","Data":{
        "CollectionId":3,
        "Commands":[
            {"Command":"Achievement:Change",
            "Data":{"Achievement":{"AchievementId":"daily_bonus_train","Level":5,"Progress":175}}},
        {"Command":"Container:ShowContent","Data":{"Containers":[{"ContainerId":3,"Train":{"InstanceId":162,"DefinitionId":40,"Level":1}}]}},
        {"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"open_train_container","Level":4,"Progress":551}}},
        {"Command":"PlayerCompany:Stats:Change","Data":{"Stats":{"Type":"open_train_container","Progress":4408}}},
        {"Command":"PlayerCompany:ChangeValue","Data":{"Value":180860}}]}}
    """
    COMMAND = 'DailyReward:Claim'
    reward: PlayerDailyReward

    def __init__(self, reward, **kwargs):
        super(DailyRewardClaimCommand, self).__init__(**kwargs)
        self.reward = reward

    def post_processing(self, server_data: Dict):
        if self.reward:
            today_reward = self.reward.get_today_rewards()
            if today_reward:
                _id = today_reward.get('Id', None)
                _value = today_reward.get('Value', None)
                _amount = today_reward.get('Amount', None)

                if _id == 8 and _amount:
                    warehouse_add_article(
                        version=self.version,
                        article_id=_value,
                        amount=_amount
                    )

            self.reward.day = (self.reward.day + 1) % 5
            self.reward.available_from = self.reward.available_from + timedelta(days=1)
            self.reward.expire_at = self.reward.expire_at + timedelta(days=1)
            self.reward.save(
                update_fields=[
                    'day',
                    'available_from',
                    'expire_at',
                ]
            )


class DailyRewardClaimWithVideoCommand(BaseCommand):
    """

        # 5일짜리 일일 보상 첫번째
        Before
                "AvailableFrom": "2023-01-23T00:00:00Z",
                "ExpireAt": "2023-01-23T23:59:59Z",
                "Rewards": [
                    {"Items": [{"Id": 8,"Value": 4,"Amount": 20}]},
                    {"Items": [{"Id": 8,"Value": 7,"Amount": 20}]},
                    {"Items": [{"Id": 8,"Value": 3,"Amount": 36}]},
                    {"Items": [{"Id": 8,"Value": 2,"Amount": 10}]},
                    {"Items": [{"Id": 1,"Value": 13}]}
                ],
                "PoolId": 1,
                "Day": 0
        After
                available_from : 2023-01-24 00:00:00+00:00 | remain : -1 day, 15:49:04.023994
                expire_at : 2023-01-24 23:59:59+00:00 | remain : 15:49:03.023963
                rewards : [
                    {"Items":[{"Id":8,"Value":4,"Amount":20}]},
                    {"Items":[{"Id":8,"Value":7,"Amount":20}]},
                    {"Items":[{"Id":8,"Value":3,"Amount":36}]},
                    {"Items":[{"Id":8,"Value":2,"Amount":10}]},
                    {"Items":[{"Id":1,"Value":13}]}
                ]
                pool_id : 1
                day : 1

        POST /api/v2/command-processing/run-collection HTTP/1.1
        PXFD-Request-Id: 6d172f82-a372-48cc-a61c-46d4a01fd659
        PXFD-Retry-No: 0
        PXFD-Sent-At: 2023-01-23T12:53:55.808Z
        PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}
        PXFD-Client-Version: 2.6.3.4068
        PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
        PXFD-Game-Access-Token: f5019986-472e-52ca-b95a-aa520bdbfbca
        PXFD-Player-Id: 62794770
        Content-Type: application/json
        Content-Length: 229
        Host: game.trainstation2.com
        Accept-Encoding: gzip, deflate


        {"Id":43,"Time":"2023-01-23T12:53:55Z","Commands":[{"Command":"DailyReward:ClaimWithVideoReward","Time":"2023-01-23T12:53:55Z","Parameters":{"VideoStartedAt":"2023-01-23T12:53:04Z","VideoReference":"TBA"}}],"Transactional":false}

        {"Success":true,"RequestId":"6d172f82-a372-48cc-a61c-46d4a01fd659","Time":"2023-01-23T12:53:56Z","Data":{"CollectionId":43,"Commands":[{"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"daily_bonus_train","Level":1,"Progress":3}}}]}}

    """
    COMMAND = 'DailyReward:ClaimWithVideoReward'
    video_started_at: str
    reward: PlayerDailyReward

    def __init__(self, reward, video_started_datetime_s: str, **kwargs):
        super(DailyRewardClaimWithVideoCommand, self).__init__(**kwargs)
        self.reward = reward
        self.video_started_at = video_started_datetime_s

    def get_parameters(self) -> dict:
        return {
            "VideoStartedAt": self.video_started_at,  # "2023-01-23T12:53:04Z",
            "VideoReference": "TBA"
        }

    def post_processing(self, server_data: Dict):
        if self.reward:
            today_reward = self.reward.get_today_rewards()
            for reward in today_reward:
                _id = reward.get('Id', None)
                _value = reward.get('Value', None)
                _amount = reward.get('Amount', None)

                if _id == 8 and _amount:
                    warehouse_add_article(
                        version=self.version,
                        article_id=_value,
                        amount=_amount * 2
                    )

            self.reward.day = (self.reward.day + 1) % 5
            self.reward.available_from = self.reward.available_from + timedelta(days=1)
            self.reward.expire_at = self.reward.expire_at + timedelta(days=1)
            self.reward.save(
                update_fields=[
                    'day',
                    'available_from',
                    'expire_at',
                ]
            )


###################################################################
# Whistle
###################################################################
class CollectWhistle(BaseCommand):
    """
{'buffer': 'POST /api/v2/command-processing/run-collection HTTP/1.1\r\nPXFD-Request-Id: 06ec734c-466b-4c2b-a1c1-37352444b819\r\nPXFD-Retry-No: 0\r\nPXFD-Sent-At: 2023-01-12T02:14:44.124Z\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json\r\nContent-Length: 175\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

{'buffer': '{"Id":10,"Time":"2023-01-12T02:14:44Z","Commands":[{"Command":"Whistle:Collect","Time":"2023-01-12T02:14:43Z","Parameters":{"Category":1,"Position":1}}],"Transactional":false}'}

{"Success":true,"RequestId":"06ec734c-466b-4c2b-a1c1-37352444b819","Time":"2023-01-12T02:14:44Z",
"Data":{
    "CollectionId":10,
    "Commands":[
        {
            "Command":"Whistle:Spawn",
            "Data":{
                "Whistle":{
                "Category":1,"Position":1,"SpawnTime":"2023-01-12T02:20:43Z","CollectableFrom":"2023-01-12T02:20:43Z",
                    "Reward":{
                    "Items":[
                        {"Id":8,"Value":103,"Amount":4}
                    ]
                },
                "IsForVideoReward":false
            }
        }
    },
    {"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"whistle_tap","Level":5,"Progress":16413}}}]}}
    """

    COMMAND = 'Whistle:Collect'
    whistle: PlayerWhistle
    SLEEP_RANGE = (0.5, 1)
    # {"Command":"Whistle:Collect","Time":"2023-01-16T03:10:39Z","Parameters":{"Category":1,"Position":3}}

    def __init__(self, *, whistle: PlayerWhistle, **kwargs):
        super(CollectWhistle, self).__init__(**kwargs)
        self.whistle = whistle

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "Category": self.whistle.category,
            "Position": self.whistle.position,
        }

    def post_processing(self, server_data: Dict):
        for item in PlayerWhistleItem.objects.filter(player_whistle=self.whistle).all():
            if item.item_id == 8 and item.amount:
                warehouse_add_article(
                    version=self.version,
                    article_id=item.value,
                    amount=item.amount
                )

        whistle_remove(version=self.version, whistle=self.whistle)


###################################################################
# Daily Offer
###################################################################
class ShopBuyContainer(BaseCommand):
    """
    {
        "Command":"Shop:BuyContainer",
        "Time":"2023-01-23T12:44:06Z",
        "Parameters":{"OfferId":1,"Amount":1},
        "Debug":{
            "CollectionsInQueue":0,
            "CollectionsInQueueIds":""
        }
    }
    """

    COMMAND = 'Shop:BuyContainer'
    offer: PlayerDailyOfferContainer
    sleep_command_no: int
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, offer: PlayerDailyOfferContainer, sleep_command_no: int, **kwargs):
        super(ShopBuyContainer, self).__init__(**kwargs)
        self.offer = offer
        self.sleep_command_no = sleep_command_no

    def get_debug(self) -> dict:
        in_queue = 0
        in_queue_ids = ''
        if self.sleep_command_no:
            in_queue = 1
            in_queue_ids = f'{self.sleep_command_no}-1'

        return {
            "Debug": {
                "CollectionsInQueue": in_queue,
                "CollectionsInQueueIds": in_queue_ids
            }
        }

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "OfferId": self.offer.offer_container_id,
            "Amount": 1,
        }

    def post_processing(self, server_data: Dict):
        container_offer_set_used(version=self.version, offer=self.offer)


class ShopPurchaseItem(BaseCommand):
    """
         {
            "Command":"Shop:DailyOffer:PurchaseItem",
            "Time":"2023-02-08T08:54:01Z",
            "Parameters":{"Slot":11,"Amount":1}
        }
    """

    COMMAND = 'Shop:DailyOffer:PurchaseItem'
    offer_item: PlayerDailyOfferItem
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, offer_item: PlayerDailyOfferItem, **kwargs):
        super(ShopPurchaseItem, self).__init__(**kwargs)
        self.offer_item = offer_item

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "Slot": self.offer_item.slot,
            "Amount": 1,
        }

    def post_processing(self, server_data: Dict):
        daily_offer_set_used(version=self.version, offer_item=self.offer_item)

"""
{"Success":true,"RequestId":"0c894a43-baf6-4aee-bda2-3bbba8463b94","Time":"2023-02-08T08:53:34Z","Data":[{"Type":"ab_test","Data":{"AbTests":[]}},{"Type":"achievements","Data":{"Achievements":[{"AchievementId":"complete_job","Level":0,"Progress":14},{"AchievementId":"daily_bonus_train","Level":1,"Progress":9},{"AchievementId":"open_train_container","Level":1,"Progress":5},{"AchievementId":"own_unique_trains","Level":0,"Progress":6},{"AchievementId":"population_max","Level":0,"Progress":40},{"AchievementId":"reach_player_level","Level":0,"Progress":5},{"AchievementId":"smelting_plant_production","Level":0,"Progress":2},{"AchievementId":"train_to_gold_destination","Level":0,"Progress":21},{"AchievementId":"train_to_material_destination","Level":1,"Progress":36},{"AchievementId":"upgrade_common_train_to_max","Level":0,"Progress":3},{"AchievementId":"upgrade_train","Level":0,"Progress":87},{"AchievementId":"warehouse_upgrade","Level":1,"Progress":600},{"AchievementId":"whistle_tap","Level":1,"Progress":68}],"ReturnAsArray":false}},{"Type":"boosts","Data":{"Boosts":[]}},{"Type":"calendars","Data":{"Calendars":[]}},{"Type":"city_building_shop","Data":{"Shops":[],"Buildings":[],"NextVideoReplaceAt":"2023-02-08T08:53:34Z","NextReplaceAt":"2023-02-08T08:53:34Z"}},{"Type":"city_loop","Data":{"Population":{"LastCalculatedCount":25,"LastCalculatedAt":"2022-08-27T06:02:48Z"},"UpgradeTaskNextReplaceAt":"2023-02-08T08:53:34Z","UpgradeTaskNextVideoReplaceAt":"2023-02-08T08:53:34Z","Parcels":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],"ShopOffers":[],"Buildings":[{"InstanceId":1,"DefinitionId":100,"ParcelNumber":1,"Rotation":0,"Level":1},{"InstanceId":2,"DefinitionId":102,"ParcelNumber":2,"Rotation":0,"Level":1},{"InstanceId":3,"DefinitionId":104,"ParcelNumber":3,"Rotation":0,"Level":1},{"InstanceId":4,"DefinitionId":109,"ParcelNumber":4,"Rotation":0,"Level":1},{"InstanceId":5,"DefinitionId":106,"ParcelNumber":5,"Rotation":0,"Level":1},{"InstanceId":6,"DefinitionId":101,"Rotation":0,"Level":1},{"InstanceId":7,"DefinitionId":103,"Rotation":0,"Level":1},{"InstanceId":8,"DefinitionId":105,"Rotation":0,"Level":1}]}},{"Type":"commodities","Data":{"Commodities":[]}},{"Type":"communities","Data":{"SelectedCommunityTeams":[],"ContestWinners":[]}},{"Type":"competitions","Data":{"Competitions":[{"Type":"union","LevelFrom":25,"MaxAttendees":15,"CompetitionId":"0a96024d-fcee-4402-9f33-618eaf07ca5b","ContentCategory":3,"Rewards":[],"StartsAt":"2022-12-05T12:00:00Z","EnrolmentAvailableTo":"2023-02-27T12:00:00Z","FinishesAt":"2023-02-27T12:00:00Z","ExpiresAt":"2023-03-03T12:00:00Z","PresentationDataId":100001,"GuildData":{"Status":0},"Scope":"global"},{"Type":"prestige","LevelFrom":899,"MaxAttendees":15,"CompetitionId":"1cd43cc9-07e8-4cca-b0fe-64bd5eb44aa8","ContentCategory":4,"Rewards":[{"Items":[{"Id":8,"Value":9,"Amount":11}]},{"Items":[{"Id":8,"Value":9,"Amount":7}]},{"Items":[{"Id":8,"Value":9,"Amount":5}]},{"Items":[{"Id":8,"Value":8,"Amount":20}]},{"Items":[{"Id":8,"Value":8,"Amount":18}]},{"Items":[{"Id":8,"Value":8,"Amount":16}]},{"Items":[{"Id":8,"Value":8,"Amount":14}]},{"Items":[{"Id":8,"Value":8,"Amount":12}]},{"Items":[{"Id":8,"Value":8,"Amount":10}]},{"Items":[{"Id":8,"Value":8,"Amount":9}]},{"Items":[{"Id":8,"Value":8,"Amount":8}]},{"Items":[{"Id":8,"Value":8,"Amount":7}]},{"Items":[{"Id":8,"Value":8,"Amount":5}]},{"Items":[{"Id":8,"Value":8,"Amount":3}]},{"Items":[{"Id":8,"Value":8,"Amount":1}]}],"StartsAt":"2023-02-06T12:00:00Z","EnrolmentAvailableTo":"2023-02-12T12:00:00Z","FinishesAt":"2023-02-12T12:00:00Z","ExpiresAt":"2023-02-12T23:59:50Z","PresentationDataId":33,"Scope":"group"},{"Type":"union","LevelFrom":25,"MaxAttendees":15,"CompetitionId":"fe40b122-dadd-4153-a0dc-e03503ad6bbb","ContentCategory":3,"Rewards":[],"StartsAt":"2023-02-06T12:00:00Z","EnrolmentAvailableTo":"2023-02-12T12:00:00Z","FinishesAt":"2023-02-12T12:00:00Z","ExpiresAt":"2023-02-13T00:00:00Z","PresentationDataId":100001,"GuildData":{"Status":0},"Scope":"group"},{"Type":"default","LevelFrom":12,"MaxAttendees":25,"CompetitionId":"fe92e154-6ece-4a77-9984-8b9187160923","ContentCategory":1,"Rewards":[{"Items":[{"Id":8,"Value":38001,"Amount":350},{"Id":6,"Value":100136}]},{"Items":[{"Id":8,"Value":38001,"Amount":250}]},{"Items":[{"Id":8,"Value":38001,"Amount":200}]},{"Items":[{"Id":8,"Value":38001,"Amount":180}]},{"Items":[{"Id":8,"Value":38001,"Amount":160}]},{"Items":[{"Id":8,"Value":38001,"Amount":120}]},{"Items":[{"Id":8,"Value":38001,"Amount":100}]},{"Items":[{"Id":8,"Value":38001,"Amount":90}]},{"Items":[{"Id":8,"Value":38001,"Amount":80}]},{"Items":[{"Id":8,"Value":38001,"Amount":70}]},{"Items":[{"Id":8,"Value":38001,"Amount":60}]},{"Items":[{"Id":8,"Value":38001,"Amount":50}]},{"Items":[{"Id":8,"Value":38001,"Amount":50}]},{"Items":[{"Id":8,"Value":38001,"Amount":40}]},{"Items":[{"Id":8,"Value":38001,"Amount":40}]},{"Items":[{"Id":8,"Value":38001,"Amount":20}]},{"Items":[{"Id":8,"Value":38001,"Amount":20}]},{"Items":[{"Id":8,"Value":38001,"Amount":20}]},{"Items":[{"Id":8,"Value":38001,"Amount":10}]},{"Items":[{"Id":8,"Value":38001,"Amount":10}]},{"Items":[{"Id":8,"Value":38001,"Amount":2}]},{"Items":[{"Id":8,"Value":38001,"Amount":2}]},{"Items":[{"Id":8,"Value":38001,"Amount":2}]},{"Items":[{"Id":8,"Value":38001,"Amount":2}]},{"Items":[{"Id":8,"Value":38001,"Amount":2}]}],"StartsAt":"2023-02-07T12:00:00Z","EnrolmentAvailableTo":"2023-02-09T00:00:00Z","FinishesAt":"2023-02-09T12:00:00Z","ExpiresAt":"2023-02-09T23:59:50Z","PresentationDataId":81,"Scope":"group"}]}},{"Type":"containers","Data":{"Containers":[]}},{"Type":"contracts","Data":{"Contracts":[],"ContractLists":[]}},{"Type":"daily_reward","Data":{"AvailableFrom":"2023-02-09T00:00:00Z","ExpireAt":"2023-02-09T23:59:59Z","Rewards":[{"Items":[{"Id":8,"Value":4,"Amount":30}]},{"Items":[{"Id":8,"Value":3,"Amount":36}]},{"Items":[{"Id":8,"Value":2,"Amount":10}]},{"Items":[{"Id":8,"Value":9,"Amount":2}]},{"Items":[{"Id":1,"Value":3}]}],"PoolId":2,"Day":0}},{"Type":"destinations","Data":{"Destinations":[{"LocationId":152,"DefinitionId":152,"TrainLimitCount":0,"TrainLimitRefreshTime":"2023-02-08T02:19:36Z","TrainLimitRefreshesAt":"2023-02-08T02:19:36Z","Multiplier":0}],"ReturnAsArray":false}},{"Type":"dispatcher","Data":{"PermanentLevel":1,"TemporaryDispatchers":[],"Dispatchers":[{"TemporaryDispatchers":[],"ContentCategory":1,"PermanentLevel":1},{"TemporaryDispatchers":[],"ContentCategory":3,"PermanentLevel":1}]}},{"Type":"event","Data":{"ActivationDate":"2023-02-06T12:00:00Z","StartDate":"2023-02-07T12:00:00Z","EndDate":"2023-02-27T12:00:00Z","ExpirationDate":"2023-03-01T12:00:00Z","EventId":38,"ActivatesAt":"2023-02-06T12:00:00Z","StartsAt":"2023-02-07T12:00:00Z","EndsAt":"2023-02-27T12:00:00Z","ExpiresAt":"2023-03-01T12:00:00Z","Shop":[]}},{"Type":"events","Data":{"Events":[{"UniqueId":"61007323-df94-4a9b-9bad-9495ddf77d2f","EventId":38,"ActivatesAt":"2023-02-06T12:00:00Z","StartsAt":"2023-02-07T12:00:00Z","EndsAt":"2023-02-27T12:00:00Z","ExpiresAt":"2023-03-01T12:00:00Z","Shop":[]}]}},{"Type":"factories","Data":{"Factories":[{"DefinitionId":1,"SlotCount":2,"ProductOrders":[]},{"DefinitionId":2,"SlotCount":2,"ProductOrders":[]}],"NextVideoSpeedUpAt":"2023-02-08T08:53:34Z"}},{"Type":"game_features","Data":{"Features":[{"Name":"depot","DefinitionId":1,"LevelFrom":3,"Enabled":true},{"Name":"warehouse","DefinitionId":2,"LevelFrom":2,"Enabled":true},{"Name":"job_list","DefinitionId":3,"LevelFrom":4,"Enabled":true},{"Name":"regions","DefinitionId":4,"LevelFrom":4,"Enabled":true},{"Name":"city_shop","DefinitionId":5,"LevelFrom":9,"Enabled":true},{"Name":"quest_log","DefinitionId":6,"LevelFrom":10,"Enabled":true},{"Name":"message_board","DefinitionId":7,"LevelFrom":5,"Enabled":true},{"Name":"event","DefinitionId":8,"LevelFrom":12,"Enabled":true},{"Name":"competition","DefinitionId":9,"LevelFrom":0,"Enabled":true},{"Name":"achievements","DefinitionId":10,"LevelFrom":4,"Enabled":true},{"Name":"shop","DefinitionId":11,"LevelFrom":2,"Enabled":true},{"Name":"special_offers","DefinitionId":12,"LevelFrom":5,"Enabled":true},{"Name":"your_station","DefinitionId":13,"LevelFrom":4,"Enabled":true},{"Name":"product_shortcut","DefinitionId":14,"LevelFrom":5,"Enabled":true},{"Name":"offer_wall","DefinitionId":15,"LevelFrom":10,"Enabled":true},{"Name":"headquarters","DefinitionId":16,"LevelFrom":4,"Enabled":true},{"Name":"redeem_code","DefinitionId":18,"LevelFrom":0,"Enabled":true},{"Name":"city_loop","DefinitionId":19,"LevelFrom":7,"Enabled":true},{"Name":"ship_loop","DefinitionId":20,"LevelFrom":11,"Enabled":true},{"Name":"prestige","DefinitionId":21,"LevelFrom":699,"Enabled":true},{"Name":"population","DefinitionId":22,"LevelFrom":7,"Enabled":true},{"Name":"guilds","DefinitionId":24,"LevelFrom":25,"Enabled":true},{"Name":"seasons","DefinitionId":25,"LevelFrom":25,"Enabled":true},{"Name":"region_progression_map","DefinitionId":26,"LevelFrom":5,"Enabled":true}]}},{"Type":"game","Data":{"Env":"prod","FirebaseEnv":"prod"}},{"Type":"gifts","Data":{"Gifts":[]}},{"Type":"guild","Data":{"WasInGuild":false,"Shops":[],"ClaimedRewardIds":[]}},{"Type":"jobs","Data":{"Jobs":[{"Id":"02ec5679-0c4c-4785-aefe-8fa96cd92847","JobLocationId":154,"JobLevel":1,"Sequence":0,"JobType":5,"Duration":30,"ConditionMultiplier":1,"RewardMultiplier":1,"RequiredArticle":{"Id":100,"Amount":40},"CurrentArticleAmount":0,"Reward":{"Items":[{"Id":8,"Value":4,"Amount":25},{"Id":8,"Value":1,"Amount":20}]},"Bonus":{"Reward":{"Items":[]}},"Requirements":[{"Type":"region","Value":1}]},{"Id":"eee0d5a5-3a9c-44f6-b782-bebe7f2e6757","JobLocationId":155,"JobLevel":1,"Sequence":0,"JobType":5,"Duration":30,"ConditionMultiplier":1,"RewardMultiplier":1,"RequiredArticle":{"Id":104,"Amount":30},"CurrentArticleAmount":0,"Reward":{"Items":[{"Id":8,"Value":4,"Amount":25},{"Id":8,"Value":1,"Amount":20}]},"Bonus":{"Reward":{"Items":[]}},"Requirements":[{"Type":"region","Value":1}]},{"Id":"f1a6673b-343d-4c13-8cb1-af7cf994742d","JobLocationId":158,"JobLevel":1,"Sequence":0,"JobType":5,"Duration":1800,"ConditionMultiplier":1,"RewardMultiplier":1,"RequiredArticle":{"Id":104,"Amount":12},"CurrentArticleAmount":0,"Reward":{"Items":[{"Id":8,"Value":4,"Amount":25},{"Id":8,"Value":1,"Amount":10},{"Id":8,"Value":3,"Amount":30}]},"Bonus":{"Reward":{"Items":[]}},"Requirements":[{"Type":"region","Value":1},{"Type":"rarity","Value":3}]},{"Id":"2ae660d1-e5b7-4395-95e9-e8d69d417641","JobLocationId":161,"JobLevel":3,"Sequence":0,"JobType":8,"Duration":3600,"ConditionMultiplier":1,"RewardMultiplier":1,"RequiredArticle":{"Id":104,"Amount":10},"CurrentArticleAmount":0,"Reward":{"Items":[{"Id":8,"Value":4,"Amount":40},{"Id":8,"Value":1,"Amount":30},{"Id":8,"Value":3,"Amount":40}]},"Bonus":{"Reward":{"Items":[]}},"Requirements":[{"Type":"region","Value":1}],"UnlocksAt":"2023-01-23T13:20:50Z"},{"Id":"4374d7d3-d480-41eb-b2e0-3990477f0e73","JobLocationId":162,"JobLevel":3,"Sequence":0,"JobType":8,"Duration":1800,"ConditionMultiplier":1,"RewardMultiplier":1,"RequiredArticle":{"Id":104,"Amount":6},"CurrentArticleAmount":0,"Reward":{"Items":[{"Id":8,"Value":4,"Amount":25},{"Id":8,"Value":1,"Amount":20}]},"Bonus":{"Reward":{"Items":[]}},"Requirements":[{"Type":"region","Value":1},{"Type":"rarity","Value":2}],"UnlocksAt":"2023-01-23T12:57:07Z"}],"NextReplaceAt":"2023-02-08T08:53:34Z","NextVideoReplaceAt":"2023-02-08T08:53:34Z"}},{"Type":"locations","Data":{"Skins":[]}},{"Type":"login_profile","Data":{}},{"Type":"maps","Data":{"Maps":[{"Id":"region_101","Spots":[{"SpotId":161,"Position":{"X":3,"Y":0},"Connections":[164],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[161],"Reward":{"Items":[]}}}},{"SpotId":164,"Position":{"X":5,"Y":0},"Connections":[153],"IsResolved":false,"Content":{"Category":"quest","Data":{"JobLocationIds":[164],"Reward":{"Items":[{"Id":6,"Value":100008}]}}}},{"SpotId":153,"Position":{"X":7,"Y":0},"Connections":[],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[153],"Reward":{"Items":[]}}}},{"SpotId":150,"Position":{"X":0,"Y":1},"Connections":[159],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[150],"Reward":{"Items":[]}}}},{"SpotId":159,"Position":{"X":1,"Y":1},"Connections":[160],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[159],"Reward":{"Items":[]}}}},{"SpotId":160,"Position":{"X":2,"Y":1},"Connections":[161,162,152],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[160],"Reward":{"Items":[{"Id":1,"Value":34}]}}}},{"SpotId":162,"Position":{"X":3,"Y":1},"Connections":[163],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[162],"Reward":{"Items":[]}}}},{"SpotId":163,"Position":{"X":4,"Y":1},"Connections":[165],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[163],"Reward":{"Items":[]}}}},{"SpotId":165,"Position":{"X":6,"Y":1},"Connections":[153],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[165],"Reward":{"Items":[]}}}},{"SpotId":152,"Position":{"X":3,"Y":2},"Connections":[],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[152],"Reward":{"Items":[]}}}},{"SpotId":158,"Position":{"X":4,"Y":2},"Connections":[],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[158],"Reward":{"Items":[]}}}},{"SpotId":155,"Position":{"X":5,"Y":2},"Connections":[],"IsResolved":true,"Content":{"Category":"quest","Data":{"JobLocationIds":[155],"Reward":{"Items":[]}}}},{"SpotId":154,"Position":{"X":6,"Y":2},"Connections":[],"IsResolved":false,"Content":{"Category":"quest","Data":{"JobLocationIds":[154],"Reward":{"Items":[{"Id":1,"Value":34}]}}}},{"SpotId":157,"Position":{"X":7,"Y":2},"Connections":[],"IsResolved":false,"Content":{"Category":"quest","Data":{"JobLocationIds":[157],"Reward":{"Items":[{"Id":2,"Value":14,"Amount":1}]}}}},{"SpotId":156,"Position":{"X":8,"Y":2},"Connections":[],"IsResolved":false,"Content":{"Category":"quest","Data":{"JobLocationIds":[156],"Reward":{"Items":[{"Id":8,"Value":8,"Amount":2}]}}}}]}]}},{"Type":"markets","Data":{"Markets":[]}},{"Type":"milestones","Data":{"Milestones":[]}},{"Type":"offer_wall","Data":{}},{"Type":"placements","Data":{"Competition":[]}},{"Type":"player_feature","Data":{"Features":[]}},{"Type":"player","Data":{"PlayerLevel":5,"PlayerId":62794770,"PlayerName":"Player_62794770","AvatarId":1,"Company":{"Rank":2,"Value":1322,"Stats":[{"Type":"complete_job","Progress":42},{"Type":"open_train_container","Progress":40},{"Type":"own_unique_trains","Progress":600},{"Type":"population_max","Progress":40},{"Type":"upgrade_common_train_to_max","Progress":600}]}}},{"Type":"prestige","Data":{"Prestiges":[{"PrestigeId":"084a3ff3-9c80-4691-a3cb-d4aca320ef5a","DefinitionId":2,"ActivationDate":"2023-02-06T12:00:00Z","ActivatesAt":"2023-02-06T12:00:00Z","StartDate":"2023-02-06T12:00:00Z","StartsAt":"2023-02-06T12:00:00Z","EndDate":"2023-02-13T12:00:00Z","EndsAt":"2023-02-13T12:00:00Z","ExpirationDate":"2023-02-13T12:00:00Z","ExpiresAt":"2023-02-13T12:00:00Z","HasJoined":false}]}},{"Type":"regions","Data":{"RegionProgressions":[],"Quests":[{"JobLocationId":150,"Milestone":1,"Progress":1},{"JobLocationId":152,"Milestone":2,"Progress":2},{"JobLocationId":159,"Milestone":3,"Progress":3},{"JobLocationId":160,"Milestone":4,"Progress":4},{"JobLocationId":161,"Milestone":2,"Progress":2},{"JobLocationId":162,"Milestone":2,"Progress":2}],"VisitedRegions":[101]}},{"Type":"reminders","Data":{"Reminders":[{"Category":"notification","RemindsAt":"2023-02-04T01:12:07Z"}]}},{"Type":"seasons","Data":{"Seasons":[{"UniqueId":"8068a940-1de9-4230-bb0f-62238aa5cd28","DefinitionId":100,"ActivatesAt":"2022-12-05T11:00:00Z","StartsAt":"2022-12-05T12:00:00Z","EndsAt":"2023-02-27T12:00:00Z","ExpiresAt":"2023-03-03T12:00:00Z"},{"UniqueId":"efadd4dd-5a58-4d0b-9ac0-743abda2637b","DefinitionId":200,"ActivatesAt":"2023-03-03T12:00:00Z","StartsAt":"2023-03-06T12:00:00Z","EndsAt":"2023-05-29T12:00:00Z","ExpiresAt":"2023-06-02T12:00:00Z"}],"Phases":[{"SeasonDefinitionId":100,"DefinitionId":101,"StartsAt":"2022-12-05T12:00:00Z","EndsAt":"2023-01-02T11:59:59Z"},{"SeasonDefinitionId":100,"DefinitionId":102,"StartsAt":"2023-01-02T12:00:00Z","EndsAt":"2023-01-30T11:59:59Z"},{"SeasonDefinitionId":100,"DefinitionId":103,"StartsAt":"2023-01-30T12:00:00Z","EndsAt":"2023-02-27T12:00:00Z"},{"SeasonDefinitionId":200,"DefinitionId":202,"StartsAt":"2023-04-03T12:00:00Z","EndsAt":"2023-05-01T11:59:59Z"},{"SeasonDefinitionId":200,"DefinitionId":203,"StartsAt":"2023-05-01T12:00:00Z","EndsAt":"2023-05-29T12:00:00Z"},{"SeasonDefinitionId":200,"DefinitionId":201,"StartsAt":"2023-03-06T12:00:00Z","EndsAt":"2023-04-03T11:59:59Z"}]}},{"Type":"shop","Data":{"OfferContainers":[{"DefinitionId":1,"LastBoughtAt":"2023-02-07T22:19:02Z","Count":21},{"DefinitionId":2,"LastBoughtAt":"2022-08-27T06:02:12Z","Count":4},{"DefinitionId":6,"LastBoughtAt":"2023-02-07T22:19:34Z","Count":20}],"SpecialOffers":[],"DailyOffer":{"ExpireAt":"2023-02-09T00:00:00Z","ExpiresAt":"2023-02-09T00:00:00Z","OfferItems":[{"Slot":11,"Price":{"Id":16,"Amount":1},"Reward":{"Items":[{"Id":8,"Value":8,"Amount":3}]},"Purchased":false,"PurchaseCount":0,"DefinitionId":55},{"Slot":12,"Price":{"Id":3,"Amount":120},"Reward":{"Items":[{"Id":1,"Value":35}]},"Purchased":false,"PurchaseCount":0,"DefinitionId":56},{"Slot":13,"Price":{"Id":3,"Amount":250},"Reward":{"Items":[{"Id":8,"Value":8,"Amount":15}]},"Purchased":false,"PurchaseCount":0,"DefinitionId":57},{"Slot":14,"Price":{"Id":2,"Amount":20},"Reward":{"Items":[{"Id":1,"Value":34}]},"Purchased":false,"PurchaseCount":0,"DefinitionId":58},{"Slot":15,"Price":{"Id":2,"Amount":250},"Reward":{"Items":[{"Id":8,"Value":8,"Amount":100}]},"Purchased":false,"PurchaseCount":0,"DefinitionId":59},{"Slot":16,"Price":{"Id":2,"Amount":350},"Reward":{"Items":[{"Id":1,"Value":69}]},"Purchased":false,"PurchaseCount":0,"DefinitionId":60}]},"OfferWall":{"Claimed":[],"Unclaimed":[]},"PaymentData":{"Verified":[]}}},{"Type":"task_lists","Data":{"TaskLists":[],"ReturnAsArray":false}},{"Type":"tickets","Data":{"Tickets":[]}},{"Type":"trains","Data":{"Trains":[{"InstanceId":1,"DefinitionId":3,"Level":17,"Route":{"RouteType":"destination","DefinitionId":152,"DepartureTime":"2023-02-07T22:19:36Z","ArrivalTime":"2023-02-07T22:20:36Z"}},{"InstanceId":2,"DefinitionId":5,"Level":21,"Route":{"RouteType":"destination","DefinitionId":151,"DepartureTime":"2023-02-04T14:21:36Z","ArrivalTime":"2023-02-04T14:22:06Z"}},{"InstanceId":3,"DefinitionId":4,"Level":20,"Route":{"RouteType":"destination","DefinitionId":151,"DepartureTime":"2023-02-04T14:21:37Z","ArrivalTime":"2023-02-04T14:22:07Z"}},{"InstanceId":4,"DefinitionId":2,"Level":17},{"InstanceId":5,"DefinitionId":1,"Level":17},{"InstanceId":6,"DefinitionId":136,"Level":1}],"ReturnAsArray":false}},{"Type":"tutorial","Data":{"Groups":["GoToBritain_LVL2_0","introduction1C","introduction2C","introduction3C","job_listC","trigger_100_keysC","trigger_player_stationC","trigger_send_2_trainsC","trigger_shopC","trigger_train_upgradeC","TriggerCloseJobC"]}},{"Type":"unlocked_contents","Data":{"UnlockedContents":[{"DefinitionId":150,"UnlockedAt":"2022-08-25T10:00:47Z"},{"DefinitionId":151,"UnlockedAt":"2022-08-27T05:14:23Z"},{"DefinitionId":152,"UnlockedAt":"2022-12-29T12:08:16Z"},{"DefinitionId":154,"UnlockedAt":"2022-08-25T10:00:47Z"},{"DefinitionId":173,"UnlockedAt":"2023-01-23T12:57:23Z"},{"DefinitionId":175,"UnlockedAt":"2023-01-23T12:57:23Z"}]}},{"Type":"vouchers","Data":{"Vouchers":[]}},{"Type":"warehouse","Data":{"Level":2,"Articles":[{"Id":1,"Amount":28},{"Id":2,"Amount":67},{"Id":3,"Amount":158},{"Id":4,"Amount":344},{"Id":6,"Amount":1310},{"Id":7,"Amount":10},{"Id":8,"Amount":0},{"Id":9,"Amount":3},{"Id":100,"Amount":54},{"Id":101,"Amount":51},{"Id":104,"Amount":65},{"Id":232,"Amount":1}]}},{"Type":"whistles","Data":{"Whistles":[{"Category":1,"Position":1,"SpawnTime":"2023-02-08T08:55:04Z","CollectableFrom":"2023-02-08T08:55:04Z","Reward":{"Items":[{"Id":8,"Value":232,"Amount":1}]},"IsForVideoReward":false},{"Category":1,"Position":3,"SpawnTime":"2023-02-08T08:56:04Z","CollectableFrom":"2023-02-08T08:56:04Z","Reward":{"Items":[{"Id":8,"Value":101,"Amount":1}]},"IsForVideoReward":false},{"Category":1,"Position":4,"SpawnTime":"2023-02-08T08:57:04Z","CollectableFrom":"2023-02-08T08:57:04Z","Reward":{"Items":[{"Id":8,"Value":101,"Amount":1}]},"IsForVideoReward":false},{"Category":1,"Position":2,"SpawnTime":"2023-02-08T08:55:24Z","CollectableFrom":"2023-02-08T08:55:24Z","Reward":{"Items":[{"Id":8,"Value":4,"Amount":1}]},"IsForVideoReward":false}]}}]}


08 17:54:04 | T: 8258 | I | IO.Mem.Write    | {"Id":2,"Time":"2023-02-08T08:54:03Z","Commands":[{"Command":"Shop:DailyOffer:PurchaseItem","Time":"2023-02-08T08:54:01Z","Parameters":{"Slot":11,"Amount":1}}],"Transactional":false}
08 17:54:04 | T: 8260 | I | SSL_AsyncWrite  | POST /api/v2/command-processing/run-collection HTTP/1.1
PXFD-Request-Id: 544754d1-22ca-402a-905d-5e9ad1cd1667
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-02-08T08:54:03.053Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.7.0.4123","Language":"ko"}
PXFD-Client-Version: 2.7.0.4123
PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
PXFD-Game-Access-Token: 79c5daef-c77d-5de2-8cec-6e84539d9caa
PXFD-Player-Id: 62794770
Content-Type: application/json
Content-Length: 182
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate


08 17:54:04 | T: 8263 | I | SSL_AsyncWrite  | {"Id":2,"Time":"2023-02-08T08:54:03Z","Commands":[{"Command":"Shop:DailyOffer:PurchaseItem","Time":"2023-02-08T08:54:01Z","Parameters":{"Slot":11,"Amount":1}}],"Transactional":false}
08 17:54:04 | T: 8263 | I | IO.Mem.Write    | {"Success":true,"RequestId":"544754d1-22ca-402a-905d-5e9ad1cd1667","Time":"2023-02-08T08:54:04Z","Data":{"CollectionId":2,"Commands":[]}}

08 17:54:25 | T: 8261 | I | IO.Mem.Write    | {"Id":3,"Time":"2023-02-08T08:54:24Z","Commands":[{"Command":"Shop:DailyOffer:PurchaseItem","Time":"2023-02-08T08:54:23Z","Parameters":{"Slot":12,"Amount":1}}],"Transactional":false}
08 17:54:25 | T: 8260 | I | SSL_AsyncWrite  | POST /api/v2/command-processing/run-collection HTTP/1.1
PXFD-Request-Id: 1a58e894-6912-4719-9cdb-b0e650f7a85f
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-02-08T08:54:24.791Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.7.0.4123","Language":"ko"}
PXFD-Client-Version: 2.7.0.4123
PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
PXFD-Game-Access-Token: 79c5daef-c77d-5de2-8cec-6e84539d9caa
PXFD-Player-Id: 62794770
Content-Type: application/json
Content-Length: 182
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate


08 17:54:25 | T: 8263 | I | SSL_AsyncWrite  | {"Id":3,"Time":"2023-02-08T08:54:24Z","Commands":[{"Command":"Shop:DailyOffer:PurchaseItem","Time":"2023-02-08T08:54:23Z","Parameters":{"Slot":12,"Amount":1}}],"Transactional":false}
08 17:54:25 | T: 8260 | I | IO.Mem.Write    | {"Success":true,"RequestId":"1a58e894-6912-4719-9cdb-b0e650f7a85f","Time":"2023-02-08T08:54:25Z","Data":{"CollectionId":3,"Commands":[{"Command":"Container:ShowContent","Data":{"Containers":[{"ContainerId":35,"Reward":{"Items":[{"Id":8,"Value":6,"Amount":360}]}}]}}]}}

"""


###################################################################
# Union Quest - Completed
###################################################################
"""
Guild Quest 완료시점에 Complete -> 새로운 Quest 추가.
06 13:57:34 | T: 3397 | I | SSL_AsyncWrite  | POST /api/v2/command-processing/run-command HTTP/1.1
PXFD-Request-Id: f3c6c29d-7c8f-40d3-9e15-19e0c627ff5c
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-02-06T04:57:27.743Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"en"}
PXFD-Client-Version: 2.6.3.4068
PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
PXFD-Game-Access-Token: cde3b8ab-390d-5a24-91b9-6e782d544063
PXFD-Player-Id: 61561146
Content-Type: application/json
Content-Length: 173
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate


06 13:57:34 | T: 3397 | I | SSL_AsyncWrite  | {"Command":"Guild:Job:Complete","Time":"2023-02-06T04:57:27Z","Parameters":{"GuildId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","JobId":"e6d646b6-732d-448a-869d-9a25e3cec41b"}}
06 13:57:34 | T: 3635 | I | IO.Mem.Write    | {"Success":true,"RequestId":"f3c6c29d-7c8f-40d3-9e15-19e0c627ff5c","Time":"2023-02-06T04:57:34Z","Data":{"CommandName":"Guild:Job:Complete","Commands":[]}}
"""

###################################################################
# Union Quest - Contract Accept
###################################################################
"""
[기존] / "Time":"2023-02-06T04:56:56Z"
{"Slot": 20,"ContractListId": 100001,"Conditions": [{"Id": 112,"Amount": 90}],"Reward": {"Items": [{"Id": 8,"Value": 100010,"Amount": 50}]},"UsableFrom": "2023-02-06T03:55:35Z","AvailableFrom": "2022-12-05T12:00:00Z","AvailableTo": "2023-02-27T12:00:00Z"},
{"Slot": 21,"ContractListId": 100001,"Conditions": [{"Id": 120,"Amount": 110}],"Reward": {"Items": [{"Id": 8,"Value": 100010,"Amount": 100}]},"UsableFrom": "2023-02-06T03:55:33Z","AvailableFrom": "2022-12-05T12:00:00Z","AvailableTo": "2023-02-27T12:00:00Z"}

[과거에 받아놓은건가?..] ?????????????
[REQUEST]
    POST /api/v2/command-processing/run-collection HTTP/1.1
    {"Id":3,"Time":"2023-02-06T04:58:15Z","Commands":[
        {"Command":"Contract:Activate","Time":"2023-02-06T04:58:15Z","Parameters":{"ContractListId":100001,"Slot":20}},
        {"Command":"Contract:Activate","Time":"2023-02-06T04:58:15Z","Parameters":{"ContractListId":100001,"Slot":21}}],
    "Transactional":false}

[RESPONSE]
    {"Success":true,"RequestId":"6fc2bfe3-4cf9-4444-a735-d8f38135117c","Time":"2023-02-06T04:58:16Z","Data":{"CollectionId":3,"Commands":[]}}


[REQUEST]
    POST /api/v2/command-processing/run-collection HTTP/1.1
    {"Id":4,"Time":"2023-02-06T04:58:24Z","Commands":[{"Command":"Contract:Accept","Time":"2023-02-06T04:58:22Z","Parameters":{"ContractListId":100001,"Slot":21}}],"Transactional":false}
[RESPONSE]
    {"Success":true,"RequestId":"74eff9f6-340b-4ce6-9e8a-11ab95cbd432","Time":"2023-02-06T04:58:25Z","Data":{"CollectionId":4,"Commands":[
        {"Command":"Contract:New","Data":{
            "Contract":{"Slot":21,"ContractListId":100001,"Conditions":[{"Id":126,"Amount":547}],"Reward":{"Items":[{"Id":8,"Value":100010,"Amount":100}]},"UsableFrom":"2023-02-06T05:58:22Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"caaeeb65-f22f-4b97-8ed6-706bc25ee9a6"}]}}

[두번째 Login 했을 때] / "Time":"2023-02-06T04:59:04Z"
slot 21번은 timer 약 59분 남은 상태 (UsableFrom..)
{"Slot": 20,"ContractListId": 100001,"Conditions": [{"Id": 112,"Amount": 90}],"Reward": {"Items": [{"Id": 8,"Value": 100010,"Amount": 50}]},"UsableFrom": "2023-02-06T03:55:35Z","ExpiresAt": "2023-02-27T12:00:00Z","AvailableFrom": "2022-12-05T12:00:00Z","AvailableTo": "2023-02-27T12:00:00Z"},          
{"Slot": 21,"ContractListId": 100001,"Conditions": [{"Id": 126,"Amount": 547}],"Reward": {"Items": [{"Id": 8,"Value": 100010,"Amount": 100}]},"UsableFrom": "2023-02-06T05:58:22Z","AvailableFrom": "2022-12-05T12:00:00Z","AvailableTo": "2023-02-27T12:00:00Z"}


"""
class StartGame(ImportHelperMixin):
    def get_urls(self) -> Iterator[Tuple[str, str, str, str]]:
        for url in EndPoint.get_urls(EndPoint.ENDPOINT_START_GAME):
            yield url, '', '', ''
            break

    def get_data(self, url, **kwargs) -> str:
        """

        :param url:
        :param kwargs:
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
        payload = {}

        return self.post(
            url=url,
            headers=headers,
            payload=payload
        )

    def parse_data(self, data, **kwargs) -> str:
        pass


class RunCommand(ImportHelperMixin):
    commands: List[BaseCommand]

    def __init__(self, commands: List, **kwargs):
        super(RunCommand, self).__init__(**kwargs)

        if not isinstance(commands, list):
            commands = [commands]

        self.commands = commands

    def get_urls(self) -> Iterator[Tuple[str, str, str, str]]:

        for url in EndPoint.get_urls(EndPoint.ENDPOINT_COMMAND_PROCESSING):
            yield url, '', '', ''
            break

    def get_data(self, url, **kwargs) -> str:

        mask = self.HEADER_REQUEST_ID \
               | self.HEADER_RETRY_NO \
               | self.HEADER_SENT_AT \
               | self.HEADER_CLIENT_INFORMATION \
               | self.HEADER_CLIENT_VERSION \
               | self.HEADER_DEVICE_TOKEN \
               | self.HEADER_GAME_ACCESS_TOKEN \
               | self.HEADER_PLAYER_ID

        headers = self.get_headers(mask=mask)
        payload = {
            'Id': self.version.command_no,
            'Time': get_curr_server_str_datetime_s(version=self.version),
            'Commands': [cmd.get_command() for cmd in self.commands],
            'Transactional': False,
        }

        for cmd in self.commands:
            dbg = cmd.get_debug()
            if dbg and isinstance(dbg, dict):
                payload.update(**dbg)

        print(payload)

        return self.post(
            url=url,
            headers=headers,
            payload=json.dumps(payload, separators=(',', ':'))
        )

    def preprocessing_server_response(self, server_data: Dict):
        """
            "CollectionId":10,
            "Commands":[
                {
                    "Command":"Whistle:Spawn",
                    "Data":{
                        "Whistle":{
                        "Category":1,"Position":1,"SpawnTime":"2023-01-12T02:20:43Z","CollectableFrom":"2023-01-12T02:20:43Z",
                            "Reward":{
                            "Items":[
                                {"Id":8,"Value":103,"Amount":4}
                            ]
                        },
                        "IsForVideoReward":false
                    }
                }
            },
            {"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"whistle_tap","Level":5,"Progress":16413}}}]}}
        """
        mapping: Dict[str, Callable] = {
            'Whistle:Spawn': self._parse_command_whistle_spawn
        }
        commands = server_data.pop('Commands', [])
        if commands:
            for command in commands:
                cmd = command.pop('Command', None)
                data = command.pop('Data', None)
                if cmd in mapping:
                    mapping[cmd](data=data)

    def _parse_gift(self, data):
        """
            06 13:57:37 | T: 3397 | I | IO.Mem.Write    | {"Success":true,"RequestId":"26dd80c3-ca05-4aee-ab1b-b31133c7af75","Time":"2023-02-06T04:57:37Z","Data":{"CollectionId":2,"Commands":[{"Command":"Gift:Add","Data":{"Gift":{"Id":"e6d646b6-732d-448a-869d-9a25e3cec41b","Reward":{"Items":[{"Id":8,"Value":100000,"Amount":2337},{"Id":8,"Value":100003,"Amount":1569}]},"Type":6}}}]}}
        :param data:
        :return:
        """
        pass

    def _parse_command_whistle_spawn(self, data):
        pass
        # whistles = data.get('Whistle')
        # if whistles:
        #     bulk_list, bulk_item_list = PlayerWhistle.create_instance(data=whistles, version_id=self.version.id)
        #
        #     if bulk_list:
        #         PlayerWhistle.objects.bulk_create(bulk_list, 100)
        #
        #     if bulk_item_list:
        #         PlayerWhistleItem.objects.bulk_create(bulk_item_list, 100)
        #
        # self.print_remain('_parse_init_whistles', data)

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

    def parse_data(self, data, **kwargs) -> str:

        json_data = json.loads(data, strict=False)

        check_response(json_data=json_data)

        self.version.command_no += 1
        self.version.save(
            update_fields=['command_no']
        )
        
        server_time = json_data.get('Time')
        server_data = json_data.get('Data', {})

        if server_data:
            if not isinstance(server_data, list):
                server_data = [server_data]
            for cmd, data in zip(self.commands, server_data):
                cmd.post_processing(server_data=data)
                self.preprocessing_server_response(data)

        return server_time

    def run(self):
        min_second = max([cmd.SLEEP_RANGE[0] for cmd in self.commands])
        max_second = max([cmd.SLEEP_RANGE[1] for cmd in self.commands])

        m = 100000
        l = min_second * m
        r = max_second * m
        rd = random.randint(int(l), int(r))
        sleep(rd / m)

        for url, _, _, _ in self.get_urls():
            data = self.get_data(url=url)
            if data:
                self.parse_data(data=data)

"""
    CLIENT VERSION 을 global 하게 저장해놔야 할 듯.
    
08 16:35:06 | T: 2911 | I | SSL_AsyncWrite  | GET /get-endpoints HTTP/1.1
PXFD-Request-Id: 77bf0924-62e3-4067-87e8-36845ae8eb43
PXFD-Retry-No: 0
PXFD-Sent-At: 0001-01-01T00:00:00.000
PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"en"}
PXFD-Client-Version: 2.6.3.4068
PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
Connection: keep-alive
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate

    {"Success":false,"Error":{"Message":"Internal server error.","ErrorMessage":"Client version is no longer supported. (Required: 2.7.0, Current: 2.6.3.4068)","Code":4},"RequestId":"77bf0924-62e3-4067-87e8-36845ae8eb43","Time":"2023-02-08T07:35:06Z"}
    


아래 사이트에서 버전 읽어서 처리 해보자.    
    https://apkcombo.com/ko/train-station-2/com.pixelfederation.ts2/download/apk
    
"""