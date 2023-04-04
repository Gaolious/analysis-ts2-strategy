import json
import random
from datetime import timedelta, datetime
from time import sleep
from typing import List, Iterator, Tuple, Dict, Optional, Callable, Union

from django.conf import settings

from app_root.exceptions import check_response
from app_root.mixins import ImportHelperMixin
from app_root.players.models import (
    PlayerTrain,
    PlayerDailyReward,
    PlayerWhistle,
    PlayerWhistleItem,
    PlayerDestination,
    PlayerDailyOfferContainer,
    PlayerDailyOffer,
    PlayerDailyOfferItem,
    PlayerJob,
    PlayerLeaderBoard,
    PlayerContract,
    PlayerFactoryProductOrder,
    PlayerContractList,
    PlayerAchievement,
    PlayerQuest,
    PlayerGift,
    PlayerBuilding,
    PlayerCityLoopTask,
)
from app_root.servers.models import (
    RunVersion,
    EndPoint,
    TSDestination,
    TSProduct,
    TSTrainUpgrade,
    TSFactory,
)
from app_root.strategies.managers import (
    warehouse_add_article,
    whistle_remove,
    trains_unload,
    trains_set_destination,
    container_offer_set_used,
    Player_destination_set_used,
    daily_offer_set_used,
    trains_set_job,
    contract_set_used,
    factory_order_product,
    factory_collect_product,
    contract_set_active,
    achievement_set_used,
    jobs_set_collect,
    jobs_set_dispatched,
    user_level_up,
    trains_set_upgrade,
    factory_acquire,
    collect_gift,
    cityloop_building_set_upgrade,
)
from app_root.utils import get_curr_server_str_datetime_s, get_curr_server_datetime
from core.utils import convert_datetime


class BaseCommand(object):
    """
    BaseCommand
    """

    version: RunVersion

    COMMAND = ""
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
            "Command": self.COMMAND,
            "Time": get_curr_server_str_datetime_s(version=self.version),
            "Parameters": self.get_parameters(),
        }

    def duration(self) -> int:
        return 0

    def __str__(self):
        return f"""[{self.COMMAND}] / parameters: {self.get_parameters()}"""

    def post_processing(self, server_data: Dict):
        pass


###################################################################
# COMMAND - common
###################################################################
class HeartBeat(BaseCommand):
    COMMAND = "Game:Heartbeat"
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

    COMMAND = "Game:Sleep"
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
        return {"Debug": {"CollectionsInQueue": 0, "CollectionsInQueueIds": ""}}

    def post_processing(self, server_data: Dict):
        sleep(self.sleep_seconds)
        self.version.update_now(
            self.version.now + timedelta(seconds=self.sleep_seconds)
        )


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

    COMMAND = "Game:WakeUp"
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

    COMMAND = "Train:Unload"
    train: PlayerTrain
    SLEEP_RANGE = (0.2, 0.5)

    def __init__(self, *, train: PlayerTrain, **kwargs):
        super(TrainUnloadCommand, self).__init__(**kwargs)
        self.train = train

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {"TrainId": self.train.instance_id}

    def post_processing(self, server_data: Dict):
        warehouse_add_article(
            version=self.version,
            article_id=self.train.load_id,
            amount=self.train.load_amount,
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

    COMMAND = "Train:DispatchToDestination"
    train: PlayerTrain
    dest: TSDestination
    SLEEP_RANGE = (1.0, 1.5)
    article_id: int
    amount: int

    def __init__(
        self,
        *,
        article_id: int,
        amount: int,
        train: PlayerTrain,
        dest: TSDestination,
        **kwargs,
    ):
        super(TrainSendToDestinationCommand, self).__init__(**kwargs)
        self.train = train
        self.dest = dest
        self.article_id = article_id
        self.amount = amount

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            "TrainId": self.train.instance_id,
            "DestinationId": self.dest.id,
        }

    def post_processing(self, server_data: Dict):
        departure_at = self.version.now
        arrival_at = departure_at + timedelta(seconds=self.dest.travel_duration)
        trains_set_destination(
            version=self.version,
            train=self.train,
            definition_id=self.dest.id,
            departure_at=departure_at,
            arrival_at=arrival_at,
            article_id=self.article_id,
            amount=self.amount,
        )


class TrainSendToGoldDestinationCommand(BaseCommand):
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

    COMMAND = "Train:DispatchToDestination"
    train: PlayerTrain
    dest: PlayerDestination
    SLEEP_RANGE = (1.0, 1.5)
    article_id: int
    amount: int

    def __init__(
        self,
        *,
        article_id: int,
        amount: int,
        train: PlayerTrain,
        dest: PlayerDestination,
        **kwargs,
    ):
        super(TrainSendToGoldDestinationCommand, self).__init__(**kwargs)
        self.train = train
        self.dest = dest
        self.article_id = article_id
        self.amount = amount

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            "TrainId": self.train.instance_id,
            "DestinationId": self.dest.definition_id,
        }

    def post_processing(self, server_data: Dict):
        departure_at = self.version.now
        arrival_at = departure_at + timedelta(
            seconds=self.dest.definition.travel_duration
        )
        trains_set_destination(
            version=self.version,
            train=self.train,
            definition_id=self.dest.definition_id,
            departure_at=departure_at,
            arrival_at=arrival_at,
            article_id=self.article_id,
            amount=self.amount,
        )
        Player_destination_set_used(version=self.version, dest=self.dest)


class TrainDispatchToJobCommand(BaseCommand):
    COMMAND = "Train:DispatchToJob"
    train: PlayerTrain
    job: PlayerJob
    leaderboard: PlayerLeaderBoard
    amount: int
    SLEEP_RANGE = (1.0, 1.5)

    def __init__(self, *, train: PlayerTrain, job: PlayerJob, amount: int, **kwargs):
        super(TrainDispatchToJobCommand, self).__init__(**kwargs)
        self.train = train
        self.job = job
        self.amount = amount
        self.leaderboard = PlayerLeaderBoard.objects.filter(
            player_job_id=job.id
        ).first()

    def get_parameters(self) -> dict:
        """

        :return:
        """
        unique_id = self.job.job_id
        # if self.leaderboard:
        #     unique_id = self.leaderboard.leader_board_group_id
        return {
            "UniqueId": unique_id,
            "TrainId": self.train.instance_id,
            "JobLocationId": self.job.job_location_id,
            "Load": {"Id": self.job.required_article_id, "Amount": self.amount},
        }

    def post_processing(self, server_data: Dict):
        departure_at = self.version.now
        arrival_at = departure_at + timedelta(seconds=self.job.duration)
        trains_set_job(
            version=self.version,
            train=self.train,
            definition_id=self.job.job_location_id,
            departure_at=departure_at,
            arrival_at=arrival_at,
        )
        warehouse_add_article(
            version=self.version,
            article_id=self.job.required_article_id,
            amount=-self.amount,
        )
        jobs_set_dispatched(
            version=self.version,
            job=self.job,
            departure_at=departure_at,
            arrival_at=arrival_at,
            amount=self.amount,
        )


class TrainUpgradeCommand(BaseCommand):
    """
    {"Command":"Train:Upgrade","Time":"2023-02-18T04:02:02Z","Parameters":{"TrainId":16}}

    """

    COMMAND = "Train:Upgrade"
    train: PlayerTrain
    train_upgrade: TSTrainUpgrade
    job: PlayerJob
    leaderboard: PlayerLeaderBoard
    amount: int
    SLEEP_RANGE = (0.3, 0.5)

    def __init__(self, *, train: PlayerTrain, upgrade: TSTrainUpgrade, **kwargs):
        super(TrainUpgradeCommand, self).__init__(**kwargs)
        self.train = train
        self.train_upgrade = upgrade

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            "TrainId": self.train.instance_id,
        }

    def post_processing(self, server_data: Dict):
        trains_set_upgrade(
            version=self.version,
            train=self.train,
            upgrade=self.train_upgrade,
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

    COMMAND = "DailyReward:Claim"
    reward: PlayerDailyReward

    def __init__(self, reward, **kwargs):
        super(DailyRewardClaimCommand, self).__init__(**kwargs)
        self.reward = reward

    def post_processing(self, server_data: Dict):
        if self.reward:
            today_reward = self.reward.get_today_rewards()
            if today_reward:
                _id = today_reward.get("Id", None)
                _value = today_reward.get("Value", None)
                _amount = today_reward.get("Amount", None)

                if _id == 8 and _amount:
                    warehouse_add_article(
                        version=self.version, article_id=_value, amount=_amount
                    )

            self.reward.day = (self.reward.day + 1) % 5
            self.reward.available_from = self.reward.available_from + timedelta(days=1)
            self.reward.expire_at = self.reward.expire_at + timedelta(days=1)
            self.reward.save(
                update_fields=[
                    "day",
                    "available_from",
                    "expire_at",
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

    COMMAND = "DailyReward:ClaimWithVideoReward"
    video_started_at: str
    reward: PlayerDailyReward

    def __init__(self, reward, video_started_datetime_s: str, **kwargs):
        super(DailyRewardClaimWithVideoCommand, self).__init__(**kwargs)
        self.reward = reward
        self.video_started_at = video_started_datetime_s

    def get_parameters(self) -> dict:
        return {
            "VideoStartedAt": self.video_started_at,  # "2023-01-23T12:53:04Z",
            "VideoReference": "TBA",
        }

    def post_processing(self, server_data: Dict):
        if self.reward:
            today_reward = self.reward.get_today_rewards()
            for reward in today_reward:
                _id = reward.get("Id", None)
                _value = reward.get("Value", None)
                _amount = reward.get("Amount", None)

                if _id == 8 and _amount:
                    warehouse_add_article(
                        version=self.version, article_id=_value, amount=_amount * 2
                    )

            self.reward.day = (self.reward.day + 1) % 5
            self.reward.available_from = self.reward.available_from + timedelta(days=1)
            self.reward.expire_at = self.reward.expire_at + timedelta(days=1)
            self.reward.save(
                update_fields=[
                    "day",
                    "available_from",
                    "expire_at",
                ]
            )


###################################################################
# Achievement
###################################################################
class CollectAchievementCommand(BaseCommand):
    COMMAND = "Achievement:CollectWithVideoReward"
    achievement: PlayerAchievement

    reward_article_id: int
    reward_article_amount: int
    """
{"AchievementId": "complete_job","Level": 0,"Progress": 41},

{"Id":6,"Time":"2023-02-17T01:32:14Z","Commands":[
{"Command":"Game:Sleep","Time":"2023-02-17T01:32:14Z","Parameters":{},"Debug":{"CollectionsInQueue":0,"CollectionsInQueueIds":""}}],"Transactional":false}
{"Success":true,"RequestId":"37e4192d-840a-4a45-927b-cb08b2b59288","Time":"2023-02-17T01:32:14Z","Data":{"CollectionId":6,"Commands":[]}}

{"Id":7,"Time":"2023-02-17T01:32:53Z","Commands":[
{"Command":"Game:WakeUp","Time":"2023-02-17T01:32:14Z","Parameters":{}},
{"Command":"Achievement:CollectWithVideoReward","Time":"2023-02-17T01:32:50Z","Parameters":{"AchievementId":"complete_job"}}],"Transactional":false}
{"Success":true,"RequestId":"04725979-5448-44f7-a9fa-d617bb31b998","Time":"2023-02-17T01:32:54Z","Data":{"CollectionId":7,"Commands":[]}}

    """

    def __init__(
        self, achievement, reward_article_id: int, reward_article_amount: int, **kwargs
    ):
        super(CollectAchievementCommand, self).__init__(**kwargs)
        self.achievement = achievement
        self.reward_article_id = reward_article_id
        self.reward_article_amount = reward_article_amount

    def get_parameters(self) -> dict:
        return {
            "AchievementId": self.achievement.achievement,  # "complete_job"
        }

    def post_processing(self, server_data: Dict):
        achievement_set_used(version=self.version, achievement=self.achievement)
        warehouse_add_article(
            version=self.version,
            article_id=self.reward_article_id,
            amount=self.reward_article_amount * 2,
        )


###################################################################
# Whistle
###################################################################
class CollectWhistle(BaseCommand):
    COMMAND = "Whistle:Collect"
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
                    version=self.version, article_id=item.value, amount=item.amount
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

    COMMAND = "Shop:BuyContainer"
    offer: PlayerDailyOfferContainer
    sleep_command_no: int
    SLEEP_RANGE = (0.5, 1)

    def __init__(
        self, *, offer: PlayerDailyOfferContainer, sleep_command_no: int, **kwargs
    ):
        super(ShopBuyContainer, self).__init__(**kwargs)
        self.offer = offer
        self.sleep_command_no = sleep_command_no

    def get_debug(self) -> dict:
        in_queue = 0
        in_queue_ids = ""
        if self.sleep_command_no:
            in_queue = 1
            in_queue_ids = f"{self.sleep_command_no}-1"

        return {
            "Debug": {
                "CollectionsInQueue": in_queue,
                "CollectionsInQueueIds": in_queue_ids,
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

    COMMAND = "Shop:DailyOffer:PurchaseItem"
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


06 13:57:34 | T: 3397 | I | SSL_AsyncWrite  | {"Command":"Guild:Job:Complete","Time":"2023-02-06T04:57:27Z","Parameters":{
"GuildId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","JobId":"e6d646b6-732d-448a-869d-9a25e3cec41b"}}
06 13:57:34 | T: 3635 | I | IO.Mem.Write    | {"Success":true,"RequestId":"f3c6c29d-7c8f-40d3-9e15-19e0c627ff5c","Time":"2023-02-06T04:57:34Z","Data":{"CommandName":"Guild:Job:Complete","Commands":[]}}
"""


class GuildJobCompleteCommand(BaseCommand):
    COMMAND = "Guild:Job:Complete"
    job: PlayerJob
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, job: PlayerJob, **kwargs):
        super(GuildJobCompleteCommand, self).__init__(**kwargs)
        self.job = job

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "GuildId": self.version.guild_id,
            "JobId": self.job.job_id,
        }

    def post_processing(self, server_data: Dict):
        self.job.delete()


###################################################################
# Union Quest - Contract Accept
###################################################################
class ContractListRefreshCommand(BaseCommand):
    """
    {"Command":"ContractList:Refresh","Time":"2023-02-18T10:45:38Z","Parameters":{"ContractListId":100001}}
    """

    COMMAND = "ContractList:Refresh"
    contract_list: PlayerContractList
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, contract_list: PlayerContractList, **kwargs):
        super(ContractListRefreshCommand, self).__init__(**kwargs)
        self.contract_list = contract_list

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "ContractListId": self.contract_list.contract_list_id,
        }

    def post_processing(self, server_data: Dict):
        self.contract_list.refresh_from_db()


class ContractActivateCommand(BaseCommand):
    """
    {"Id":4,"Time":"2023-02-06T04:58:24Z","Commands":[{"Command":"Contract:Activate","Time":"2023-02-06T04:58:22Z","Parameters":{
    "ContractListId":100001,"Slot":21}}],"Transactional":false}
    """

    COMMAND = "Contract:Activate"
    contract: PlayerContract
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, contract: PlayerContract, **kwargs):
        super(ContractActivateCommand, self).__init__(**kwargs)
        self.contract = contract

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "ContractListId": self.contract.contract_list.contract_list_id,
            "Slot": self.contract.slot,
        }

    def post_processing(self, server_data: Dict):
        contract_set_active(version=self.version, contract=self.contract)


class ContractAcceptCommand(BaseCommand):
    """
    {"Id":4,"Time":"2023-02-06T04:58:24Z","Commands":[{"Command":"Contract:Accept","Time":"2023-02-06T04:58:22Z","Parameters":{
    "ContractListId":100001,"Slot":21}}],"Transactional":false}
    """

    COMMAND = "Contract:Accept"
    contract: PlayerContract
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, contract: PlayerContract, **kwargs):
        super(ContractAcceptCommand, self).__init__(**kwargs)
        self.contract = contract

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "ContractListId": self.contract.contract_list.contract_list_id,
            "Slot": self.contract.slot,
        }

    def post_processing(self, server_data: Dict):
        for article_id, amount in self.contract.conditions_to_article_dict.items():
            warehouse_add_article(
                version=self.version, article_id=article_id, amount=-amount
            )

        for article_id, amount in self.contract.reward_to_article_dict.items():
            warehouse_add_article(
                version=self.version, article_id=article_id, amount=amount
            )

        contract_set_used(version=self.version, contract=self.contract)


class ContractAcceptWithVideoReward(BaseCommand):
    COMMAND = "Contract:AcceptWithVideoReward"
    contract: PlayerContract
    accept_at: str
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, contract: PlayerContract, accept_at, **kwargs):
        super(ContractAcceptWithVideoReward, self).__init__(**kwargs)
        self.contract = contract
        self.accept_at = accept_at

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "ContractListId": self.contract.contract_list.contract_list_id,
            "Slot": self.contract.slot,
            "AcceptedAt": self.accept_at,
        }

    def post_processing(self, server_data: Dict):
        for article_id, amount in self.contract.conditions_to_article_dict.items():
            warehouse_add_article(
                version=self.version, article_id=article_id, amount=-amount
            )

        for article_id, amount in self.contract.reward_to_article_dict.items():
            warehouse_add_article(
                version=self.version, article_id=article_id, amount=amount
            )

        contract_set_used(version=self.version, contract=self.contract)


###################################################################
# Product Order in Factory
###################################################################
class FactoryAcquireCommand(BaseCommand):
    """
    Factory:AcquireFactory
    """

    COMMAND = "Factory:AcquireFactory"
    factory: TSFactory
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, factory: TSFactory, **kwargs):
        super(FactoryAcquireCommand, self).__init__(**kwargs)
        self.factory = factory

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "FactoryId": self.factory.id,
        }

    def post_processing(self, server_data: Dict):
        factory_acquire(version=self.version, factory=self.factory)


class FactoryOrderProductCommand(BaseCommand):
    """
    {"Command":"Factory:OrderProduct","Time":"2023-01-14T10:29:41Z","Parameters":{"FactoryId":6000,"ArticleId":6004}},
    {"Command":"Factory:OrderProduct","Time":"2023-01-14T10:29:42Z","Parameters":{"FactoryId":6000,"ArticleId":6004}}

    """

    COMMAND = "Factory:OrderProduct"
    product: TSProduct
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, product: TSProduct, **kwargs):
        super(FactoryOrderProductCommand, self).__init__(**kwargs)
        self.product = product

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "FactoryId": self.product.factory_id,
            "ArticleId": self.product.article_id,
        }

    def post_processing(self, server_data: Dict):
        factory_order_product(version=self.version, product=self.product)


class FactoryCollectProductCommand(BaseCommand):
    """
    {
        "Command":"Factory:CollectProduct",
        "Time":"2023-01-14T10:29:35Z",
        "Parameters":{"FactoryId":6000,"Index":0}
    },
    {
        "Command":"Factory:CollectProduct",
        "Time":"2023-01-14T10:29:36Z",
        "Parameters":{"FactoryId":6000,"Index":0}
    }

    """

    COMMAND = "Factory:CollectProduct"
    order: PlayerFactoryProductOrder
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, order: PlayerFactoryProductOrder, **kwargs):
        super(FactoryCollectProductCommand, self).__init__(**kwargs)
        self.order = order

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "FactoryId": self.order.player_factory.factory_id,
            "Index": self.order.index - 1,  # 서버는 0 base / local은 1 base
        }

    def post_processing(self, server_data: Dict):
        factory_collect_product(version=self.version, order=self.order)


###################################################################
# Product Order in Factory
###################################################################
class JobCollectCommand(BaseCommand):
    """
    {"Command":"Job:Collect","Time":"2023-02-18T04:01:40Z","Parameters":{"JobLocationId":153}}],"Transactional":false}
    """

    COMMAND = "Job:Collect"
    job: PlayerJob
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, job: PlayerJob, **kwargs):
        super(JobCollectCommand, self).__init__(**kwargs)
        self.job = job

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "JobLocationId": self.job.job_location_id,
        }

    def post_processing(self, server_data: Dict):
        jobs_set_collect(version=self.version, job=self.job)


class RegionQuestCommand(BaseCommand):
    """
    {"Command":"Region:Quest:Collect","Time":"2023-02-18T04:01:38Z","Parameters":{"JobLocationId":231}},
    """

    COMMAND = "Region:Quest:Collect"
    job: PlayerJob
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, job: PlayerJob, **kwargs):
        super(RegionQuestCommand, self).__init__(**kwargs)
        self.job = job

    def get_parameters(self) -> dict:
        """
        :return:
        """
        return {
            "JobLocationId": self.job.job_location_id,
        }


class LevelUpCommand(BaseCommand):
    """
    {"Command":"Region:Quest:Collect","Time":"2023-02-18T04:01:38Z","Parameters":{"JobLocationId":231}},
    """

    COMMAND = "Player:LevelUp"
    SLEEP_RANGE = (0.5, 1)

    def post_processing(self, server_data: Dict):
        user_level_up(version=self.version)


###################################################################
# CityLoop
###################################################################


class CityLoopBuildingUpgradeCommand(BaseCommand):
    """
    24 14:07:02 | T: 2644 | I | SSL_AsyncWrite  | {"Id":3,"Time":"2023-02-24T05:07:01Z","Commands":[
    {"Command":"CityLoop:Building:Upgrade","Time":"2023-02-24T05:07:01Z","Parameters":{"BuildingId":6,"UsesAutoCollect":false}}],"Transactional":false}
    24 14:07:03 | T: 2644 | I | IO.Mem.Write    | {"Success":true,"RequestId":"97d8bc1c-8258-422d-b754-4b81c1500a1d","Time":"2023-02-24T05:07:03Z","Data":{"CollectionId":3,"Commands":[{"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":3,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:19:03Z","RequiredArticles":[{"Id":12,"Amount":13},{"Id":232,"Amount":25}]}}},{"Command":"Population:Update","Data":{"Population":{"LastCalculatedCount":59,"LastCalculatedAt":"2023-02-24T05:07:01Z"}}},{"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"city_task","Level":2,"Progress":53}}}]}}

    """

    COMMAND = "CityLoop:Building:Upgrade"
    building: PlayerBuilding
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, building: PlayerBuilding, **kwargs):
        super(CityLoopBuildingUpgradeCommand, self).__init__(**kwargs)
        self.building = building

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {"BuildingId": self.building.instance_id, "UsesAutoCollect": False}

    def post_processing(self, server_data: Dict):
        cityloop_building_set_upgrade(version=self.version, building=self.building)


class CityLoopBuildingReplaceCommand(BaseCommand):
    """
    {"Id":2,"Time":"2023-02-24T05:06:29Z","Commands":[{"Command":"CityLoop:Building:UpgradeTask:Replace","Time":"2023-02-24T05:06:29Z","Parameters":{"BuildingId":3}}],"Transactional":false}
    {"Success":true,"RequestId":"1f23af25-3b5e-412e-9deb-242e2481adca","Time":"2023-02-24T05:06:32Z","Data":{"CollectionId":2,"Commands":[
        {"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":7,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:06:32Z","RequiredArticles":[{"Id":12,"Amount":7},{"Id":10,"Amount":6},{"Id":107,"Amount":7}]}}}]}}
    """

    COMMAND = "CityLoop:Building:UpgradeTask:Replace"
    building: PlayerBuilding
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, building: PlayerBuilding, **kwargs):
        super(CityLoopBuildingReplaceCommand, self).__init__(**kwargs)
        self.building = building

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            "BuildingId": self.building.instance_id,
        }

    def post_processing(self, server_data: Dict):
        self.building.upgrade_task = ""
        self.building.save(update_fields=["upgrade_task"])
        task = PlayerCityLoopTask.objects.filter(version_id=self.version.id).first()
        if task:
            task.next_replace_at = self.version.now + timedelta(hours=4)
            task.save(update_fields=["next_replace_at"])


class CityLoopBuildingReplaceInstantlyCommand(BaseCommand):
    """
    {"Id":5,"Time":"2023-02-24T05:07:49Z","Commands":[
        {"Command":"Game:WakeUp","Time":"2023-02-24T05:07:09Z","Parameters":{}},
        {"Command":"CityLoop:Building:UpgradeTask:ReplaceInstantly","Time":"2023-02-24T05:07:46Z",
        "Parameters":{"BuildingId":2,"ArticleId":16}}],"Transactional":false}
    {"Success":true,"RequestId":"01d6522a-f9f6-404a-be19-5ac0ab2d7740","Time":"2023-02-24T05:07:50Z","Data":{"CollectionId":5,"Commands":[{"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":6,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:07:50Z","RequiredArticles":[{"Id":10,"Amount":14},{"Id":107,"Amount":10}]}}}]}}

    """

    COMMAND = "CityLoop:Building:UpgradeTask:ReplaceInstantly"
    building: PlayerBuilding
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, building: PlayerBuilding, **kwargs):
        super(CityLoopBuildingReplaceInstantlyCommand, self).__init__(**kwargs)
        self.building = building

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            "BuildingId": self.building.instance_id,
            "ArticleId": 16,  # video reward
        }

    def post_processing(self, server_data: Dict):
        self.building.upgrade_task = ""
        self.building.save(update_fields=["upgrade_task"])
        task = PlayerCityLoopTask.objects.filter(version_id=self.version.id).first()
        if task:
            task.next_video_replace_at = self.version.now + timedelta(hours=1)
            task.save(update_fields=["next_video_replace_at"])


###################################################################
# Warehouse Upgrade
###################################################################


###################################################################
# Gift
###################################################################


class CollectGiftCommand(BaseCommand):
    """
    gift에서 수집
    {
        "Command":"Gift:Claim",
        "Time":"2023-01-09T02:37:59Z",
        "Parameters":{
            "Id":"8295a2de-d048-4228-ac02-e3d36c2d3b4a"
        }
    }
    """

    COMMAND = "Gift:Claim"
    gift: PlayerGift
    SLEEP_RANGE = (0.5, 1)

    def __init__(self, *, gift: PlayerGift, **kwargs):
        super(CollectGiftCommand, self).__init__(**kwargs)
        self.gift = gift

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {"Id": self.gift.job_id}

    def post_processing(self, server_data: Dict):
        collect_gift(version=self.version, gift=self.gift)


class FirebaseAuthToken(ImportHelperMixin):
    NAME = "firebase"
    """
{"Name":"firebase_auth_token","Url":"https://game.trainstation2.com/api/v2/query/get-firebase-auth-token"},

22 09:38:34 | T: 5734 | I | SSL_AsyncWrite  | GET /api/v2/query/get-firebase-auth-token HTTP/1.1
PXFD-Request-Id: 1b0774e9-5c8a-456e-af7b-db41fcce178f
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-02-22T00:38:34.000Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.7.0.4123","Language":"ko"}
PXFD-Client-Version: 2.7.0.4123
PXFD-Device-Token: 0cbd8657b85587591462e728d4129ab0
PXFD-Game-Access-Token: 8df91df3-89f2-5708-9b03-0c59e4c9f0bc
PXFD-Player-Id: 76408422
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate


22 09:38:35 | T: 5735 | I | IO.Mem.Write    | {"Success":true,"RequestId":"1b0774e9-5c8a-456e-af7b-db41fcce178f","Time":"2023-02-22T00:38:35Z",
"Data":{
    "Uid":"prod_76408422",
    "Token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJmaXJlYmFzZS1hZG1pbnNkay1nNmR6NkB0cmFpbnN0YXRpb24tMi0zMDIyMzA3Ni5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsInN1YiI6ImZpcmViYXNlLWFkbWluc2RrLWc2ZHo2QHRyYWluc3RhdGlvbi0yLTMwMjIzMDc2LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwiYXVkIjoiaHR0cHM6Ly9pZGVudGl0eXRvb2xraXQuZ29vZ2xlYXBpcy5jb20vZ29vZ2xlLmlkZW50aXR5LmlkZW50aXR5dG9vbGtpdC52MS5JZGVudGl0eVRvb2xraXQiLCJ1aWQiOiJwcm9kXzc2NDA4NDIyIiwiaWF0IjoxNjc3MDI2MzE1LjM2NzcxNCwiZXhwIjoxNjc3MDI5OTE1LjM2NzcxNH0.QjPjNOHm4pf1tHDuYYmXa8cgX30qfdTL6T733AL2BHCuTzT3UnH4CGALJ_TBiae4VVfJia0ATrZiuTOfrP2RpBORqKdFnoAyBrAQTNRp3KijIhzXPsm36bFWUwWleErq-WK4j0OdU8m5ZRbIzCK56xGiJgwSQcj3T_R0As8xPfdnDWBX0y5Z1p5UWva7ojF55DKJz7BzPFiM06NDeOaNdJ03nE1BbS2OAWA2VfFp9dCoq7WXOOSO0SabQaE9T_PWsgl8KUgbn6R6Q6BFVxkXGix4tN2VSSw2y8wrxy4FRZf5W3P6RaPDBDEHBgdxPnpk7XG-6l1CyCJnMsXzsGEyiA",
    "Env":"prod"
}
}
   
    """

    def get_urls(self) -> Iterator[Tuple[str, str, str, str]]:
        for url in EndPoint.get_urls(EndPoint.ENDPOINT_FIREBASE_AUTH):
            yield url, "", "", ""
            break

    def get_data(self, url, **kwargs) -> str:
        """

        :param url:
        :param kwargs:
        :return:
        """
        mask = (
            self.HEADER_REQUEST_ID
            | self.HEADER_RETRY_NO
            | self.HEADER_SENT_AT
            | self.HEADER_CLIENT_INFORMATION
            | self.HEADER_CLIENT_VERSION
            | self.HEADER_DEVICE_TOKEN
            | self.HEADER_GAME_ACCESS_TOKEN
            | self.HEADER_PLAYER_ID
        )

        headers = self.get_headers(mask=mask)

        return self.get(
            url=url,
            headers=headers,
            params={},
        )

    def parse_data(self, data, **kwargs) -> str:
        """
        data =
        {"Success":true,"RequestId":"df10975f-2ba4-4fc0-a40e-5ba2fa574844","Time":"2023-03-07T13:45:34Z","Data":{"Uid":"prod_76406092","Token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJmaXJlYmFzZS1hZG1pbnNkay1nNmR6NkB0cmFpbnN0YXRpb24tMi0zMDIyMzA3Ni5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsInN1YiI6ImZpcmViYXNlLWFkbWluc2RrLWc2ZHo2QHRyYWluc3RhdGlvbi0yLTMwMjIzMDc2LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwiYXVkIjoiaHR0cHM6Ly9pZGVudGl0eXRvb2xraXQuZ29vZ2xlYXBpcy5jb20vZ29vZ2xlLmlkZW50aXR5LmlkZW50aXR5dG9vbGtpdC52MS5JZGVudGl0eVRvb2xraXQiLCJ1aWQiOiJwcm9kXzc2NDA2MDkyIiwiaWF0IjoxNjc4MTk2NzM0Ljc4ODA4NiwiZXhwIjoxNjc4MjAwMzM0Ljc4ODA4Nn0.noZlvUTf8lduYG93tUrfyQKdsn0BsenK4wc4pEleu2DnpVUt4r5BO73M6nNEEqISW_6zIWHIdfbB3DBVATjg309FIJYbws5Mq_W7zwG58If80jyBSnLXdopjWaoSml9t4I2YrAmXeq2X1mp9KPanxdlJoK-Ju0C-xgM3tCYAqqHsrmub8CfTnPTrsvtMdJ9fdXTYwIoAPLC_VnqYFqTd91V4b-EmOAhw4jFxa-3ltrjVBEyTeBCcRDuy2wU7N4V3mLx0POgq2j7xC4vlwaY37GscgYobuVGlo1tlPgg7VsJlWxFpQeKfnD-borN9LzVEIvp90FGm7T0PBcfPd1vzuQ","Env":"prod"}}
        :param data:
        :param kwargs:
        :return:
        """
        json_data = json.loads(data, strict=False)

        if json_data:
            data = json_data.get("Data", {})

            if data:
                uid = data.get("Uid", "")
                token = data.get("Token", "")
                self.version.firebase_token = token
                self.version.firebase_uid = uid

                self.version.save(
                    update_fields=[
                        "firebase_token",
                        "firebase_uid",
                    ]
                )


class StartGame(ImportHelperMixin):
    NAME = "startgame"

    def get_urls(self) -> Iterator[Tuple[str, str, str, str]]:
        for url in EndPoint.get_urls(EndPoint.ENDPOINT_START_GAME):
            yield url, "", "", ""
            break

    def get_data(self, url, **kwargs) -> str:
        """

        :param url:
        :param kwargs:
        :return:
        """
        mask = (
            self.HEADER_REQUEST_ID
            | self.HEADER_RETRY_NO
            | self.HEADER_SENT_AT
            | self.HEADER_CLIENT_INFORMATION
            | self.HEADER_CLIENT_VERSION
            | self.HEADER_DEVICE_TOKEN
            | self.HEADER_GAME_ACCESS_TOKEN
            | self.HEADER_PLAYER_ID
        )

        headers = self.get_headers(mask=mask)
        payload = {}

        return self.post(url=url, headers=headers, payload=payload)

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
            yield url, "", "", ""
            break

    def get_data(self, url, **kwargs) -> str:
        mask = (
            self.HEADER_REQUEST_ID
            | self.HEADER_RETRY_NO
            | self.HEADER_SENT_AT
            | self.HEADER_CLIENT_INFORMATION
            | self.HEADER_CLIENT_VERSION
            | self.HEADER_DEVICE_TOKEN
            | self.HEADER_GAME_ACCESS_TOKEN
            | self.HEADER_PLAYER_ID
        )

        headers = self.get_headers(mask=mask)
        payload = {
            "Id": self.version.command_no,
            "Time": get_curr_server_str_datetime_s(version=self.version),
            "Commands": [cmd.get_command() for cmd in self.commands],
            "Transactional": False,
        }

        for cmd in self.commands:
            dbg = cmd.get_debug()
            if dbg and isinstance(dbg, dict):
                payload.update(**dbg)

        print(payload)

        return self.post(
            url=url, headers=headers, payload=json.dumps(payload, separators=(",", ":"))
        )

    def processing_server_response(self, server_data: Dict):
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
            "Whistle:Spawn": self._parse_command_whistle_spawn,
            "Contract:New": self._parse_command_contract_new,
            "Map:NewJob": self._parse_command_new_job,
            "Region:Quest:Change": self._parse_command_quest_change,
            "ContractList:Update": self._parse_command_contract_list_update,
            "CityLoop:Building:UpgradeTask": self._parse_cityloop_building_upgrade_task,
            "Population:Update": self._parse_population_update,
            "Achievement:Change": self._parse_population_update,
        }
        commands = server_data.pop("Commands", [])
        if commands:
            for command in commands:
                cmd = command.pop("Command", None)
                data = command.pop("Data", None)
                if cmd in mapping:
                    mapping[cmd](data=data)

    def _parse_gift(self, data):
        """
            06 13:57:37 | T: 3397 | I | IO.Mem.Write    | {"Success":true,"RequestId":"26dd80c3-ca05-4aee-ab1b-b31133c7af75","Time":"2023-02-06T04:57:37Z","Data":{"CollectionId":2,"Commands":[{"Command":"Gift:Add","Data":{"Gift":{"Id":"e6d646b6-732d-448a-869d-9a25e3cec41b","Reward":{"Items":[{"Id":8,"Value":100000,"Amount":2337},{"Id":8,"Value":100003,"Amount":1569}]},"Type":6}}}]}}
        :param data:
        :return:
        """
        pass

    def _parse_command_contract_list_update(self, data):
        """
                "Command":"ContractList:Update",
                "Data":{
                    "ContractList":{"ContractListId":100001,"AvailableTo":"2023-02-27T12:00:00Z","NextReplaceAt":"2023-02-18T10:45:43Z","NextVideoReplaceAt":"2023-02-18T10:45:43Z","NextVideoRentAt":"2023-02-18T10:45:43Z","NextVideoSpeedUpAt":"2023-02-16T09:28:33Z","ExpiresAt":"2023-02-18T18:45:38Z"}},"Id":"540bf688-8e02-45d0-bf8d-9e33de3c06c4"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":1,"ContractListId":100001,"Conditions":[{"Id":107,"Amount":85}],
                "Reward":{"Items":[{"Id":8,"Value":100004,"Amount":40}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"61919a22-6204-4254-a572-515119c021cd"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":2,"ContractListId":100001,"Conditions":[{"Id":224,"Amount":123}],"Reward":{"Items":[{"Id":8,"Value":100004,"Amount":80}]},
                "UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"58d9a5ed-441d-4428-b9ff-ae7309dbfe6d"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":3,"ContractListId":100001,"Conditions":[{"Id":105,"Amount":183}],
                "Reward":{"Items":[{"Id":8,"Value":100004,"Amount":160}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"e47066b6-ffbb-4f3e-b820-8ee28ce97c91"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":4,"ContractListId":100001,"Conditions":[{"Id":112,"Amount":60}],"Reward":{"Items":[{"Id":8,"Value":100005,"Amount":37}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"79c048b6-b3cc-4d48-8c67-c377ae8b7809"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":5,"ContractListId":100001,"Conditions":[{"Id":118,"Amount":106}],"Reward":{"Items":[{"Id":8,"Value":100005,"Amount":75}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"4cc7713b-a501-4407-91e4-1f476208b5da"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":6,"ContractListId":100001,"Conditions":[{"Id":120,"Amount":110}],"Reward":{"Items":[{"Id":8,"Value":100005,"Amount":150}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"aa356193-9dcc-4c84-bcb0-7c1d5051ca88"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":7,"ContractListId":100001,"Conditions":[{"Id":120,"Amount":55}],"Reward":{"Items":[{"Id":8,"Value":100006,"Amount":35}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"82094f0f-ab0c-423f-a139-884754a28963"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":8,"ContractListId":100001,"Conditions":[{"Id":108,"Amount":98}],"Reward":{"Items":[{"Id":8,"Value":100006,"Amount":70}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"b7dadae7-879f-46a0-8588-4d07b3e19dfb"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":9,"ContractListId":100001,"Conditions":[{"Id":108,"Amount":130}],"Reward":{"Items":[{"Id":8,"Value":100006,"Amount":140}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"10dfaff9-43a9-4155-bc2a-adce492fedfe"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":10,"ContractListId":100001,"Conditions":[{"Id":115,"Amount":154}],"Reward":{"Items":[{"Id":8,"Value":100007,"Amount":32}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"ef82ada3-db37-4d89-9d67-4953faa035ba"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":11,"ContractListId":100001,"Conditions":[{"Id":105,"Amount":137}],"Reward":{"Items":[{"Id":8,"Value":100007,"Amount":65}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"920a8afa-dc5a-4b5b-bf60-3fbfa167ba26"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":12,"ContractListId":100001,"Conditions":[{"Id":106,"Amount":183}],"Reward":{"Items":[{"Id":8,"Value":100007,"Amount":130}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"25f27fb2-5778-4f94-a936-4ed9e0d8402e"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":13,"ContractListId":100001,"Conditions":[{"Id":111,"Amount":85}],"Reward":{"Items":[{"Id":8,"Value":100008,"Amount":30}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"67a8c2bb-bb78-4e4f-be8e-528d3a9d3d2b"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":14,"ContractListId":100001,"Conditions":[{"Id":224,"Amount":123}],"Reward":{"Items":[{"Id":8,"Value":100008,"Amount":60}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"2aecaa85-ad44-4441-a3e7-8c45d58e131b"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":15,"ContractListId":100001,"Conditions":[{"Id":224,"Amount":164}],"Reward":{"Items":[{"Id":8,"Value":100008,"Amount":120}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"2b89e9bd-5915-4ecf-8e9b-27e54e219e7b"}
                {"Command":"Contract:New","Data":{"Contract":{"Slot":16,"ContractListId":100001,"Conditions":[{"Id":107,"Amount":85}],"Reward":{"Items":[{"Id":8,"Value":100009,"Amount":27}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"ec8af687-d675-4f9d-abea-e7fb8b5d9eb6"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":17,"ContractListId":100001,"Conditions":[{"Id":118,"Amount":106}],"Reward":{"Items":[{"Id":8,"Value":100009,"Amount":55}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"9d0d89f9-5dcf-4e9e-bf9c-c0c113ad5296"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":18,"ContractListId":100001,"Conditions":[{"Id":117,"Amount":235}],"Reward":{"Items":[{"Id":8,"Value":100009,"Amount":110}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"70279acc-ab32-4caf-b6b9-0c87721006f7"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":19,"ContractListId":100001,"Conditions":[{"Id":123,"Amount":92}],"Reward":{"Items":[{"Id":8,"Value":100010,"Amount":25}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"87211a0d-542d-4046-89c6-027d653869ba"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":20,"ContractListId":100001,"Conditions":[{"Id":119,"Amount":90}],"Reward":{"Items":[{"Id":8,"Value":100010,"Amount":50}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"5d7ec184-a143-4bbd-96d6-a723f5df2a36"},
                {"Command":"Contract:New","Data":{"Contract":{"Slot":21,"ContractListId":100001,"Conditions":[{"Id":105,"Amount":183}],"Reward":{"Items":[{"Id":8,"Value":100010,"Amount":100}]},"UsableFrom":"2023-02-18T10:45:38Z","AvailableFrom":"2022-12-05T12:00:00Z","AvailableTo":"2023-02-27T12:00:00Z"}},"Id":"246c6655-8af1-4fa0-89aa-f483d430e9ce"}
            ]}
        :param data:
        :return:
        """
        contract_list = data.get("ContractList", [])
        if contract_list:
            bulk_list, _ = PlayerContractList.create_instance(
                data=contract_list, version_id=self.version.id
            )

            if bulk_list:
                for instance in bulk_list:
                    instance: PlayerContractList
                    old = PlayerContractList.objects.filter(
                        version_id=self.version.id,
                        contract_list_id=instance.contract_list_id,
                    ).first()
                    if old:
                        instance.id = old.id
                        instance.save()
                bulk_list = [o for o in bulk_list if not o.id]

            if bulk_list:
                PlayerContract.objects.bulk_create(bulk_list, 100)

    def _parse_command_contract_new(self, data):
        """
            {
                \"Contract\":{
                    \"Slot\":12,
                    \"ContractListId\":100001,
                    \"Conditions\":[{\"Id\":111,\"Amount\":170}],
                    \"Reward\":{
                        \"Items\":[{\"Id\":8,\"Value\":100007,\"Amount\":130}]
                    },
                    \"UsableFrom\":\"2023-02-11T09:47:19Z\",
                    \"AvailableFrom\":\"2022-12-05T12:00:00Z\",
                    \"AvailableTo\":\"2023-02-27T12:00:00Z\"
                }
            }
        :param data:
        :return:
        """
        contracts = data.get("Contract", [])
        if contracts:
            contract_list = list(
                PlayerContractList.objects.filter(version_id=self.version.id).all()
            )
            bulk_list, _ = PlayerContract.create_instance(
                data=contracts, version_id=self.version.id, contract_list=contract_list
            )

            if bulk_list:
                for instance in bulk_list:
                    old = PlayerContract.objects.filter(
                        version_id=self.version.id, slot=instance.slot
                    ).first()
                    if old:
                        instance.id = old.id
                        instance.save()
                bulk_list = [o for o in bulk_list if not o.id]

            if bulk_list:
                PlayerContract.objects.bulk_create(bulk_list, 100)

    def _parse_command_whistle_spawn(self, data):
        whistles = data.get("Whistle")
        if whistles:
            bulk_list, bulk_item_list = PlayerWhistle.create_instance(
                data=whistles, version_id=self.version.id
            )

            if bulk_list:
                PlayerWhistle.objects.bulk_create(bulk_list, 100)

            if bulk_item_list:
                PlayerWhistleItem.objects.bulk_create(bulk_item_list, 100)

        self.print_remain("_parse_init_whistles", data)

    def _parse_command_quest_change(self, data):
        quests = data.get("Quest")
        if quests:
            bulk_list, _ = PlayerQuest.create_instance(
                data=quests, version_id=self.version.id
            )

            for instance in bulk_list:
                instance: PlayerQuest
                old = PlayerQuest.objects.filter(
                    version_id=self.version.id, job_location_id=instance.job_location_id
                ).first()
                if old:
                    instance.id = old.id
                instance.save()

    def _parse_command_new_job(self, data):
        jobs = data.get("Job")
        if jobs:
            bulk_list, _ = PlayerJob.create_instance(
                data=jobs, version_id=self.version.id
            )

            if bulk_list:
                PlayerJob.objects.bulk_create(bulk_list, 100)

    def _parse_population_update(self, data):
        """
        {"Command":"Population:Update","Data":{"Population":{"LastCalculatedCount":59,"LastCalculatedAt":"2023-02-24T05:07:01Z"}}},

        :param data:
        :return:
        """
        if data:
            population = data.pop("Population", {})

            if population:
                self.version.population = population.get("LastCalculatedCount") or 0
                self.version.save(update_fields=["population"])

    def _parse_achievement_change(self, data):
        """
        {"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"city_task","Level":2,"Progress":53}}}]}}

        :param data:
        :return:
        """
        if data:
            achievement = data.pop("Achievement", {})
            bulk_list, _ = PlayerAchievement.create_instance(
                data=achievement, version_id=self.version.id
            )
            if bulk_list:
                for instance in bulk_list:
                    old = PlayerAchievement.objects.filter(
                        version_id=self.version.id, achievement=instance.achievement
                    ).first()
                    if old:
                        instance.id = old.id
                        instance.save()
                bulk_list = [o for o in bulk_list if not o.id]

            if bulk_list:
                PlayerAchievement.objects.bulk_create(bulk_list, 100)

    def _parse_cityloop_building_upgrade_task(self, data):
        """
                {"Success":true,"RequestId":"97d8bc1c-8258-422d-b754-4b81c1500a1d","Time":"2023-02-24T05:07:03Z","Data":{"CollectionId":3,"Commands":[
                {"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":3,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:19:03Z","RequiredArticles":[{"Id":12,"Amount":13},{"Id":232,"Amount":25}]}}},

        {"Success":true,"RequestId":"1f23af25-3b5e-412e-9deb-242e2481adca","Time":"2023-02-24T05:06:32Z","Data":{"CollectionId":2,"Commands":[
            {"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":7,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:06:32Z","RequiredArticles":[{"Id":12,"Amount":7},{"Id":10,"Amount":6},{"Id":107,"Amount":7}]}}}]}}

        {"Success":true,"RequestId":"01d6522a-f9f6-404a-be19-5ac0ab2d7740","Time":"2023-02-24T05:07:50Z","Data":{"CollectionId":5,"Commands":[
        {"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":6,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:07:50Z","RequiredArticles":[{"Id":10,"Amount":14},{"Id":107,"Amount":10}]}}}]}}

                :param data:
                :return:
        """
        if data:
            building_id = data.pop("BuildingId", None)
            upgrade_task = data.pop("UpgradeTask", "")
            if building_id:
                bld = PlayerBuilding.objects.filter(
                    version=self.version, instance_id=building_id
                ).first()
                bld.upgrade_task = (
                    json.dumps(upgrade_task, separators=(",", ":"))
                    if upgrade_task
                    else ""
                )
                bld.save(update_fields=["upgrade_task"])

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
            print("[REMAIN]", msg, data)

    def parse_data(self, data, **kwargs) -> str:
        json_data = json.loads(data, strict=False)

        check_response(json_data=json_data)

        self.version.command_no += 1
        self.version.save(update_fields=["command_no"])

        server_time = json_data.get("Time")
        server_data = json_data.get("Data", {})
        st = convert_datetime(server_time)
        if st:
            self.version.update_now(now=st)

        if server_data:
            for cmd in self.commands:
                cmd.post_processing(server_data=server_data)
                self.processing_server_response(server_data)

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


def send_commands(commands: Union[BaseCommand, List[BaseCommand]]):
    if not isinstance(commands, list):
        commands = [commands]

    cmd = RunCommand(version=commands[0].version, commands=commands)
    cmd.run()


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
