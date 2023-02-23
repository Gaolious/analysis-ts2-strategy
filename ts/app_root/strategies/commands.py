import json
import random
from datetime import timedelta, datetime
from time import sleep
from typing import List, Iterator, Tuple, Dict, Optional, Callable, Union

from django.conf import settings

from app_root.exceptions import check_response
from app_root.mixins import ImportHelperMixin
from app_root.players.models import PlayerTrain, PlayerDailyReward, PlayerWhistle, PlayerWhistleItem, PlayerDestination, \
    PlayerDailyOfferContainer, PlayerDailyOffer, PlayerDailyOfferItem, PlayerJob, PlayerLeaderBoard, PlayerContract, \
    PlayerFactoryProductOrder, PlayerContractList, PlayerAchievement, PlayerQuest
from app_root.servers.models import RunVersion, EndPoint, TSDestination, TSProduct, TSTrainUpgrade, TSFactory
from app_root.strategies.managers import warehouse_add_article, whistle_remove, trains_unload, \
    trains_set_destination, container_offer_set_used, Player_destination_set_used, daily_offer_set_used, trains_set_job, \
    contract_set_used, factory_order_product, factory_collect_product, contract_set_active, achievement_set_used, \
    jobs_set_collect, jobs_set_dispatched, user_level_up, trains_set_upgrade, factory_acquire
from app_root.utils import get_curr_server_str_datetime_s, get_curr_server_datetime
from core.utils import convert_datetime


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
    dest: TSDestination
    SLEEP_RANGE = (1.0, 1.5)
    article_id: int
    amount: int

    def __init__(self, *, article_id: int, amount: int, train: PlayerTrain, dest: TSDestination, **kwargs):
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
            'TrainId': self.train.instance_id,
            'DestinationId': self.dest.id,
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

    COMMAND = 'Train:DispatchToDestination'
    train: PlayerTrain
    dest: PlayerDestination
    SLEEP_RANGE = (1.0, 1.5)
    article_id: int
    amount: int

    def __init__(self, *, article_id: int, amount: int, train: PlayerTrain, dest: PlayerDestination, **kwargs):
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
            'TrainId': self.train.instance_id,
            'DestinationId': self.dest.definition_id,
        }

    def post_processing(self, server_data: Dict):
        departure_at = self.version.now
        arrival_at = departure_at + timedelta(seconds=self.dest.definition.travel_duration)
        trains_set_destination(
            version=self.version,
            train=self.train,
            definition_id=self.dest.definition_id,
            departure_at=departure_at,
            arrival_at=arrival_at,
            article_id=self.article_id,
            amount=self.amount,
        )
        Player_destination_set_used(
            version=self.version,
            dest=self.dest
        )


class TrainDispatchToJobCommand(BaseCommand):
    """
[LeaderBoard]
{"Success":true,"RequestId":"37549e03-92c2-4850-9f32-efcd381e3282","Time":"2023-02-06T05:04:09Z","Data":{
    "LeaderboardId":"329a0e3a-038d-4bd4-a99d-b19ed9dcde20",
    "LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352",
    "Bracket":"1",
    "Progresses":[
        {"PlayerId":20873082,"AvatarId":59,"FirebaseUid":"prod_20873082","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"DJ.GRooWER Hun","Progress":142,"LastUpdate":"2023-02-06T04:18:58Z","RewardClaimed":false},
        {"PlayerId":36725548,"AvatarId":70,"FirebaseUid":"prod_36725548","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Offiget","Progress":98,"LastUpdate":"2023-02-05T21:21:05Z","RewardClaimed":false},
        {"PlayerId":42991064,"AvatarId":59,"FirebaseUid":"prod_42991064","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"John co","Progress":20,"LastUpdate":"2023-02-05T16:06:51Z","RewardClaimed":false},
        {"PlayerId":43023388,"AvatarId":70,"FirebaseUid":"prod_43023388","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"JarHead0352","Progress":72,"LastUpdate":"2023-02-05T23:42:06Z","RewardClaimed":false},
        {"PlayerId":51701244,"AvatarId":59,"FirebaseUid":"prod_51701244","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Squidworth","Progress":50,"LastUpdate":"2023-02-05T21:44:11Z","RewardClaimed":false},
        {"PlayerId":52529982,"AvatarId":8,"FirebaseUid":"prod_52529982","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Jessen","Progress":0,"LastUpdate":"2023-02-03T12:08:09Z","RewardClaimed":false},
        {"PlayerId":53255036,"AvatarId":71,"FirebaseUid":"prod_53255036","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"ShadowV1965","Progress":0,"LastUpdate":"2023-02-03T12:08:14Z","RewardClaimed":false},
        {"PlayerId":55570560,"AvatarId":123,"FirebaseUid":"prod_55570560","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Spider","Progress":35,"LastUpdate":"2023-02-05T19:33:59Z","RewardClaimed":false},
        {"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"SRand","Progress":0,"LastUpdate":"2023-02-03T12:08:28Z","RewardClaimed":false},
        {"PlayerId":61656034,"AvatarId":121,"FirebaseUid":"prod_61656034","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Cootabang","Progress":0,"LastUpdate":"2023-02-03T12:08:31Z","RewardClaimed":false},
        {"PlayerId":63527822,"AvatarId":120,"FirebaseUid":"prod_63527822","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Adnan","Progress":80,"LastUpdate":"2023-02-05T21:21:39Z","RewardClaimed":false},
        {"PlayerId":65333042,"AvatarId":1,"FirebaseUid":"prod_65333042","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"flobuiss ","Progress":91,"LastUpdate":"2023-02-06T04:35:59Z","RewardClaimed":false},
        {"PlayerId":65958250,"AvatarId":1,"FirebaseUid":"prod_65958250","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Choo Choo Charlie","Progress":182,"LastUpdate":"2023-02-06T04:33:54Z","RewardClaimed":false},
        {"PlayerId":66288442,"AvatarId":14,"FirebaseUid":"prod_66288442","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"AMJ Railroad ","Progress":11,"LastUpdate":"2023-02-03T17:01:03Z","RewardClaimed":false},
        {"PlayerId":66674602,"AvatarId":70,"FirebaseUid":"prod_66674602","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Claudemir ","Progress":60,"LastUpdate":"2023-02-05T22:22:41Z","RewardClaimed":false}
    ],
    "Rewards":[
        {"Items":[{"Id":8,"Value":8,"Amount":176}]},
        {"Items":[{"Id":8,"Value":8,"Amount":150}]},
        {"Items":[{"Id":8,"Value":8,"Amount":110}]},
        {"Items":[{"Id":8,"Value":8,"Amount":64}]},
        {"Items":[{"Id":8,"Value":8,"Amount":40}]},
        {"Items":[{"Id":8,"Value":8,"Amount":33}]},
        {"Items":[{"Id":8,"Value":8,"Amount":31}]},
        {"Items":[{"Id":8,"Value":8,"Amount":22}]},
        {"Items":[{"Id":8,"Value":8,"Amount":20}]},
        {"Items":[{"Id":8,"Value":8,"Amount":18}]},
        {"Items":[{"Id":8,"Value":8,"Amount":11}]},{"Items":[{"Id":8,"Value":8,"Amount":9}]},{"Items":[{"Id":8,"Value":8,"Amount":7}]},{"Items":[{"Id":8,"Value":8,"Amount":5}]},{"Items":[{"Id":8,"Value":8,"Amount":3}]}]}}
{"Success":true,"RequestId":"984210f6-0180-4ee7-81ef-d3b340dc7278","Time":"2023-02-06T05:04:33Z","Data":{
    "LeaderboardId":"563b3067-a1a7-4a8b-9986-4ab8b0048e26",
    "LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b",
    "Bracket":"1","Progresses":[
    {"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"SRand","Progress":240,"Position":1,"LastUpdatedAt":"2023-02-06T05:04:30Z","RewardClaimed":false},
    {"PlayerId":45329266,"AvatarId":11,"FirebaseUid":"prod_45329266","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"shine1219","Progress":60,"Position":2,"LastUpdatedAt":"2023-02-05T14:32:42Z","RewardClaimed":false}
    ,{"PlayerId":45387522,"AvatarId":1,"FirebaseUid":"prod_45387522","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Kr.Wanja","Progress":53,"Position":3,"LastUpdatedAt":"2023-02-06T03:34:30Z","RewardClaimed":false},
    {"PlayerId":37482414,"AvatarId":24,"FirebaseUid":"prod_37482414","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"DARKCHOCO","Progress":40,"Position":4,"LastUpdatedAt":"2023-02-05T18:35:13Z","RewardClaimed":false},
    {"PlayerId":26401848,"AvatarId":24,"FirebaseUid":"prod_26401848","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Clutch","Progress":38,"Position":5,"LastUpdatedAt":"2023-02-05T15:05:41Z","RewardClaimed":false},
    {"PlayerId":2147982,"AvatarId":109,"FirebaseUid":"prod_2147982","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Ghind","Progress":33,"Position":6,"LastUpdatedAt":"2023-02-05T16:42:00Z","RewardClaimed":false},
    {"PlayerId":31423644,"AvatarId":89,"FirebaseUid":"prod_31423644","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Cindy","Progress":30,"Position":7,"LastUpdatedAt":"2023-02-06T00:21:59Z","RewardClaimed":false},
    {"PlayerId":51063284,"AvatarId":71,"FirebaseUid":"prod_51063284","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Greenday","Progress":30,"Position":8,"LastUpdatedAt":"2023-02-06T00:52:57Z","RewardClaimed":false},
    {"PlayerId":27674098,"AvatarId":25,"FirebaseUid":"prod_27674098","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"KTKSRTK","Progress":15,"Position":9,"LastUpdatedAt":"2023-02-06T01:51:12Z","RewardClaimed":false}
    ],"Rewards":[{"Items":[{"Id":8,"Value":100000,"Amount":69},{"Id":8,"Value":100003,"Amount":52}]},{"Items":[{"Id":8,"Value":100000,"Amount":17},{"Id":8,"Value":100003,"Amount":13}]},{"Items":[{"Id":8,"Value":100000,"Amount":15},{"Id":8,"Value":100003,"Amount":11}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":9},{"Id":8,"Value":100003,"Amount":7}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":4},{"Id":8,"Value":100003,"Amount":3}]}]}}
{"Success":true,"RequestId":"90098378-fcf7-4c3d-ac80-3e0039888e36","Time":"2023-02-06T05:04:36Z","Data":{
    "LeaderboardId":"563b3067-a1a7-4a8b-9986-4ab8b0048e26","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","Bracket":"1",
    "Progresses":[
    {"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"SRand","Progress":270,"Position":1,"LastUpdatedAt":"2023-02-06T05:04:33Z","RewardClaimed":false},
    {"PlayerId":45329266,"AvatarId":11,"FirebaseUid":"prod_45329266","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"shine1219","Progress":60,"Position":2,"LastUpdatedAt":"2023-02-05T14:32:42Z","RewardClaimed":false},
    {"PlayerId":45387522,"AvatarId":1,"FirebaseUid":"prod_45387522","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Kr.Wanja","Progress":53,"Position":3,"LastUpdatedAt":"2023-02-06T03:34:30Z","RewardClaimed":false},
    {"PlayerId":37482414,"AvatarId":24,"FirebaseUid":"prod_37482414","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"DARKCHOCO","Progress":40,"Position":4,"LastUpdatedAt":"2023-02-05T18:35:13Z","RewardClaimed":false},
    {"PlayerId":26401848,"AvatarId":24,"FirebaseUid":"prod_26401848","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Clutch","Progress":38,"Position":5,"LastUpdatedAt":"2023-02-05T15:05:41Z","RewardClaimed":false},
    {"PlayerId":2147982,"AvatarId":109,"FirebaseUid":"prod_2147982","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Ghind","Progress":33,"Position":6,"LastUpdatedAt":"2023-02-05T16:42:00Z","RewardClaimed":false},
    {"PlayerId":31423644,"AvatarId":89,"FirebaseUid":"prod_31423644","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Cindy","Progress":30,"Position":7,"LastUpdatedAt":"2023-02-06T00:21:59Z","RewardClaimed":false}
    ,{"PlayerId":51063284,"AvatarId":71,"FirebaseUid":"prod_51063284","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Greenday","Progress":30,"Position":8,"LastUpdatedAt":"2023-02-06T00:52:57Z","RewardClaimed":false},
    {"PlayerId":27674098,"AvatarId":25,"FirebaseUid":"prod_27674098","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"KTKSRTK","Progress":15,"Position":9,"LastUpdatedAt":"2023-02-06T01:51:12Z","RewardClaimed":false}
    ],"Rewards":[{"Items":[{"Id":8,"Value":100000,"Amount":78},{"Id":8,"Value":100003,"Amount":58}]},{"Items":[{"Id":8,"Value":100000,"Amount":17},{"Id":8,"Value":100003,"Amount":13}]},
    {"Items":[{"Id":8,"Value":100000,"Amount":15},{"Id":8,"Value":100003,"Amount":11}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},
    {"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":9},{"Id":8,"Value":100003,"Amount":7}]},
    {"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},
    {"Items":[{"Id":8,"Value":100000,"Amount":4},{"Id":8,"Value":100003,"Amount":3}]}]}}
{"Success":true,"RequestId":"a6656868-aa7b-4b10-b094-aaea7b34307d","Time":"2023-02-06T05:04:45Z","Data":{"LeaderboardId":"5f446bee-6f0a-44db-8520-22c7c6c7e542","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","Bracket":"1","Progresses":[{"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"SRand","Progress":60,"Position":1,"LastUpdatedAt":"2023-02-06T05:04:43Z","RewardClaimed":false}],"Rewards":[{"Items":[{"Id":8,"Value":100000,"Amount":52},{"Id":8,"Value":100003,"Amount":35}]}]}}

[Jobs]
        {"Id": "723b7b26-2101-422e-a75c-136b299fc329","JobLocationId": 166,"JobLevel": 1,"JobType": 1,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 105,"Amount": 80},"CurrentArticleAmount": 70,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 6},{"Id": 8,"Value": 1,"Amount": 140}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 1},{"Type": "rarity","Value": 2},{"Type": "power","Value": 30}],"UnlocksAt": "2022-08-13T02:22:19Z"},
        {"Id": "3d532945-b633-4f3c-ac24-ad2db86bdfb4","JobLocationId": 167,"JobLevel": 1,"JobType": 1,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 106,"Amount": 80},"CurrentArticleAmount": 48,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 6},{"Id": 8,"Value": 1,"Amount": 151}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 1},{"Type": "rarity","Value": 3},{"Type": "power","Value": 40}],"UnlocksAt": "2022-08-14T10:40:01Z"},
        {"Id": "b40c155dd-2b20-4a4d-98b5-1dd0595abd17","JobLocationId": 168,"JobLevel": 1,"JobType": 1,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 108,"Amount": 150},"CurrentArticleAmount": 0,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 7},{"Id": 8,"Value": 1,"Amount": 251}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 1},{"Type": "rarity","Value": 3},{"Type": "power","Value": 45}],"UnlocksAt": "2022-09-06T15:34:55Z"},
        {"Id": "8d7508c7-c0de-43f3-8f94-0937511ca8f2","JobLocationId": 253,"JobLevel": 1,"JobType": 1,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 116,"Amount": 160},"CurrentArticleAmount": 61,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 7},{"Id": 8,"Value": 1,"Amount": 568}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 2},{"Type": "rarity","Value": 4}]},
        {"Id": "5cae482c-f2de-4228-8080-88c33c5ac5ff","JobLocationId": 350,"JobLevel": 1,"JobType": 2,"Duration": 1800,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 111,"Amount": 150},"CurrentArticleAmount": 0,"Reward": {"Items": [{"Id": 8,"Value": 30,"Amount": 2},{"Id": 8,"Value": 1,"Amount": 1387}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 3},{"Type": "rarity","Value": 1}],"ExpiresAt": "2023-02-07T00:00:00Z"},
        {"Id": "87e8fe6f-bc4e-48d5-bd02-c5b3c6b9e24f","JobLocationId": 351,"JobLevel": 1,"JobType": 1,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 118,"Amount": 70},"CurrentArticleAmount": 0,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 18},{"Id": 8,"Value": 1,"Amount": 1872}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 3},{"Type": "rarity","Value": 1}],"UnlocksAt": "2022-11-08T06:24:34Z"},
        {"Id": "bab81faa-b26d-4441-9bb7-fee9c0cb6a15","JobLocationId": 411,"JobLevel": 2,"Sequence": 0,"JobType": 5,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 224,"Amount": 90},"CurrentArticleAmount": 0,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 21},{"Id": 8,"Value": 1,"Amount": 5615}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "rarity","Value": 1}],"UnlocksAt": "2022-12-08T10:45:32Z"},
        {"Id": "afe8f8a4-ca8a-4a3e-8e3f-85b7ca694d62","JobLocationId": 412,"JobLevel": 1,"JobType": 2,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 104,"Amount": 150},"CurrentArticleAmount": 0,"Reward": {"Items": [{"Id": 8,"Value": 30,"Amount": 7},{"Id": 8,"Value": 1,"Amount": 4225}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "rarity","Value": 3}],"ExpiresAt": "2023-02-07T00:00:00Z"},
        {"Id": "d15e01ce-8d3d-425a-b7c2-cec4ad8e8c67","JobLocationId": 418,"JobLevel": 11,"Sequence": 0,"JobType": 8,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 124,"Amount": 80},"CurrentArticleAmount": 55,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 17},{"Id": 8,"Value": 1,"Amount": 5050},{"Id": 8,"Value": 3,"Amount": 125}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "era","Value": 1}],"UnlocksAt": "2022-11-15T12:10:15Z"},
        {"Id": "4a173e10-541c-4e4f-9442-5c3e49b38036","JobLocationId": 419,"JobLevel": 12,"Sequence": 0,"JobType": 8,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 111,"Amount": 80},"CurrentArticleAmount": 26,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 24},{"Id": 8,"Value": 1,"Amount": 5345}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "rarity","Value": 2}],"UnlocksAt": "2022-11-15T11:09:37Z"},
        {"Id": "e4fe741c-c484-4f52-bbf7-2449fa395b26","JobLocationId": 421,"JobLevel": 8,"Sequence": 0,"JobType": 8,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 112,"Amount": 100},"CurrentArticleAmount": 26,"Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 22},{"Id": 8,"Value": 1,"Amount": 5105},{"Id": 8,"Value": 3,"Amount": 125}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "rarity","Value": 1}],"UnlocksAt": "2022-11-15T12:10:07Z"},
        {"Id": "121e177c-01f2-49fb-917a-e8f869599aa1","JobLocationId": 39000,"JobLevel": 1,"Sequence": 0,"JobType": 10,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 105,"Amount": 150},"CurrentArticleAmount": 0,"Reward": {"Items": [{"Id": 8,"Value": 39000,"Amount": 100}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "rarity","Value": 3}],"UnlocksAt": "2023-02-03T12:00:00Z","ExpiresAt": "2023-02-06T23:59:59Z"},
        {"Id": "dfab2318-b542-46b8-be2e-1899bc0f3ea9","JobLocationId": 100002,"JobLevel": 7,"JobType": 45,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 100005,"Amount": 12800},"CurrentArticleAmount": 3250,"Reward": {"Items": [{"Id": 8,"Value": 100000,"Amount": 3350},{"Id": 8,"Value": 100003,"Amount": 2250}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "rarity","Value": 3},{"Type": "era","Value": 1}],"UnlocksAt": "2022-12-05T12:00:00Z","ExpiresAt": "2023-03-03T12:00:00Z"},
        {"Id": "563b3067-a1a7-4a8b-9986-4ab8b0048e26","JobLocationId": 100005,"JobLevel": 7,"JobType": 45,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 100010,"Amount": 11500},"CurrentArticleAmount": 120,"Reward": {"Items": [{"Id": 8,"Value": 100000,"Amount": 3350},{"Id": 8,"Value": 100003,"Amount": 2500}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "content_category","Value": 3}],"UnlocksAt": "2022-12-05T12:00:00Z","ExpiresAt": "2023-03-03T12:00:00Z"},
        {"Id": "e6d6466-732d-448a-869d-9a25e3cec41b","JobLocationId": 100007,"JobLevel": 17,"JobType": 45,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 100010,"Amount": 10300},"CurrentArticleAmount": 7187,"Reward": {"Items": [{"Id": 8,"Value": 100000,"Amount": 3350},{"Id": 8,"Value": 100003,"Amount": 2250}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 4},{"Type": "content_category","Value": 3}],"UnlocksAt": "2022-12-05T12:00:00Z","ExpiresAt": "2023-03-03T12:00:00Z"},
        {"Id": "7a3e7c99-c24d-4192-9af3-424e921f516c","JobLocationId": 100010,"JobLevel": 18,"JobType": 45,"Duration": 3600,"ConditionMultiplier": 1,"RewardMultiplier": 1,"RequiredArticle": {"Id": 100010,"Amount": 12800},"CurrentArticleAmount": 900,"Reward": {"Items": [{"Id": 8,"Value": 100000,"Amount": 3350},{"Id": 8,"Value": 100003,"Amount": 2250}]},"Bonus": {"Reward": {"Items": []}},"Requirements": [{"Type": "region","Value": 3},{"Type": "rarity","Value": 3},{"Type": "era","Value": 2}],"UnlocksAt": "2022-12-05T12:00:00Z","ExpiresAt": "2023-03-03T12:00:00Z"}

{"Id":4,"Time":"2023-02-06T05:04:41Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-02-06T05:04:41Z","Parameters":{"UniqueId":"5f446bee-6f0a-44db-8520-22c7c6c7e542","TrainId":134,"JobLocationId":100007,"Load":{"Id":100010,"Amount":20}}}],"Transactional":false}
{"Id":5,"Time":"2023-02-06T05:04:44Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-02-06T05:04:42Z","Parameters":{"UniqueId":"5f446bee-6f0a-44db-8520-22c7c6c7e542","TrainId":135,"JobLocationId":100007,"Load":{"Id":100010,"Amount":20}}},{"Command":"Train:DispatchToJob","Time":"2023-02-06T05:04:43Z","Parameters":{"UniqueId":"5f446bee-6f0a-44db-8520-22c7c6c7e542","TrainId":137,"JobLocationId":100007,"Load":{"Id":100010,"Amount":20}}}],"Transactional":false}
{"Id":6,"Time":"2023-02-06T05:04:50Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-02-06T05:04:50Z","Parameters":{"UniqueId":"7a3e7c99-c24d-4192-9af3-424e921f516c","TrainId":71,"JobLocationId":100010,"Load":{"Id":100010,"Amount":45}}}],"Transactional":false}


    """

    COMMAND = 'Train:DispatchToJob'
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
        self.leaderboard = PlayerLeaderBoard.objects.filter(player_job_id=job.id).first()

    def get_parameters(self) -> dict:
        """

        :return:
        """
        unique_id = self.job.job_id
        if self.leaderboard:
            unique_id = self.leaderboard.leader_board_group_id
        return {
            "UniqueId": unique_id,
            "TrainId": self.train.instance_id,
            "JobLocationId": self.job.job_location_id,
            "Load": {
                "Id": self.job.required_article_id,
                "Amount": self.amount
            }
        }

    def post_processing(self, server_data: Dict):
        departure_at = self.version.now
        arrival_at = departure_at + timedelta(seconds=self.job.duration)
        trains_set_job(
            version=self.version,
            train=self.train,
            definition_id=self.job.job_location_id,
            departure_at=departure_at,
            arrival_at=arrival_at
        )
        warehouse_add_article(
            version=self.version,
            article_id=self.job.required_article_id,
            amount=-self.amount
        )
        jobs_set_dispatched(
            version=self.version,
            job=self.job,
            departure_at=departure_at,
            arrival_at=arrival_at,
            amount=self.amount
        )


class TrainUpgradeCommand(BaseCommand):
    """
    {"Command":"Train:Upgrade","Time":"2023-02-18T04:02:02Z","Parameters":{"TrainId":16}}

    """
    COMMAND = 'Train:Upgrade'
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
# Achievement
class CollectAchievementCommand(BaseCommand):
    COMMAND = 'Achievement:CollectWithVideoReward'
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

    def __init__(self, achievement, reward_article_id: int, reward_article_amount: int, **kwargs):
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
            amount=self.reward_article_amount * 2
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
class ContractListRefreshCommand(BaseCommand):
    """
    {"Command":"ContractList:Refresh","Time":"2023-02-18T10:45:38Z","Parameters":{"ContractListId":100001}}
    """
    COMMAND = 'ContractList:Refresh'
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

    COMMAND = 'Contract:Activate'
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

    COMMAND = 'Contract:Accept'
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
            warehouse_add_article(version=self.version, article_id=article_id, amount=-amount)

        for article_id, amount in self.contract.reward_to_article_dict.items():
            warehouse_add_article(version=self.version, article_id=article_id, amount=amount)

        contract_set_used(version=self.version, contract=self.contract)


class ContractAcceptWithVideoReward(BaseCommand):
    COMMAND = 'Contract:AcceptWithVideoReward'
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
            warehouse_add_article(version=self.version, article_id=article_id, amount=-amount)

        for article_id, amount in self.contract.reward_to_article_dict.items():
            warehouse_add_article(version=self.version, article_id=article_id, amount=amount)

        contract_set_used(version=self.version, contract=self.contract)


###################################################################
# Product Order in Factory
###################################################################
class FactoryAcquireCommand(BaseCommand):
    """
    Factory:AcquireFactory
    """
    COMMAND = 'Factory:AcquireFactory'
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
    COMMAND = 'Factory:OrderProduct'
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

    COMMAND = 'Factory:CollectProduct'
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

    COMMAND = 'Job:Collect'
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

    COMMAND = 'Region:Quest:Collect'
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

    COMMAND = 'Player:LevelUp'
    SLEEP_RANGE = (0.5, 1)

    def post_processing(self, server_data: Dict):
        user_level_up(version=self.version)


class StartGame(ImportHelperMixin):
    NAME = 'startgame'

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
            'Whistle:Spawn': self._parse_command_whistle_spawn,
            'Contract:New': self._parse_command_contract_new,
            'Map:NewJob': self._parse_command_new_job,
            'Region:Quest:Change': self._parse_command_quest_change,
            'ContractList:Update': self._parse_command_contract_list_update,
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
        contract_list = data.get('ContractList', [])
        if contract_list:
            bulk_list, _ = PlayerContractList.create_instance(data=contract_list, version_id=self.version.id)

            if bulk_list:

                for instance in bulk_list:
                    instance: PlayerContractList
                    old = PlayerContractList.objects.filter(version_id=self.version.id, contract_list_id=instance.contract_list_id).first()
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
        contracts = data.get('Contract', [])
        if contracts:
            contract_list = list(PlayerContractList.objects.filter(version_id=self.version.id).all())
            bulk_list, _ = PlayerContract.create_instance(data=contracts, version_id=self.version.id, contract_list=contract_list)

            if bulk_list:
                for instance in bulk_list:
                    old = PlayerContract.objects.filter(version_id=self.version.id, slot=instance.slot).first()
                    if old:
                        instance.id = old.id
                        instance.save()
                bulk_list = [o for o in bulk_list if not o.id]

            if bulk_list:
                PlayerContract.objects.bulk_create(bulk_list, 100)

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

    def _parse_command_quest_change(self, data):
        quests = data.get('Quest')
        if quests:
            bulk_list, _ = PlayerQuest.create_instance(data=quests, version_id=self.version.id)

            for instance in bulk_list:
                instance: PlayerQuest
                old = PlayerQuest.objects.filter(version_id=self.version.id, job_location_id=instance.job_location_id).first()
                if old:
                    instance.id = old.id
                instance.save()

    def _parse_command_new_job(self, data):
        jobs = data.get('Job')
        if jobs:
            bulk_list, _ = PlayerJob.create_instance(data=jobs, version_id=self.version.id)

            if bulk_list:
                PlayerJob.objects.bulk_create(bulk_list, 100)


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

"""
      "Type": "gifts",
      "Data": {
        "Gifts": [
          {
            "Id": "3feee06e-56f5-419d-8606-bde30f4ee606",
            "Reward": {
              "Items": [
                {
                  "Id": 8,
                  "Value": 100000,
                  "Amount": 1316
                },
                {
                  "Id": 8,
                  "Value": 100003,
                  "Amount": 982
                }
              ]
            },
            "Type": 6
          }
        ]
      }


      
          {
            "Id": "dfab2318-b542-46b8-be2e-1899bc0f3ea9",
            "JobLocationId": 100002,
            "JobLevel": 7,
            "JobType": 45,
            "Duration": 3600,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {
              "Id": 100005,
              "Amount": 12800
            },
            "CurrentArticleAmount": 3250,
            "Reward": {"Items": [{"Id": 8,"Value": 100000,"Amount": 3350},{"Id": 8,"Value": 100003,"Amount": 2250}]
            },
            "UnlocksAt": "2022-12-05T12:00:00Z",
            "ExpiresAt": "2023-03-03T12:00:00Z"
          },
          {
            "Id": "563b3067-a1a7-4a8b-9986-4ab8b0048e26",
            "JobLocationId": 100005,
            "JobLevel": 7,
            "JobType": 45,
            "Duration": 3600,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {
              "Id": 100010,
              "Amount": 11500
            },
            "CurrentArticleAmount": 120,
            "Reward": {"Items": [{"Id": 8,"Value": 100000,"Amount": 3350},{"Id": 8,"Value": 100003,"Amount": 2500}]
            },
            "UnlocksAt": "2022-12-05T12:00:00Z",
            "ExpiresAt": "2023-03-03T12:00:00Z"
          },
          {
            "Id": "e6d646b6-732d-448a-869d-9a25e3cec41b",
            "JobLocationId": 100007,
            "JobLevel": 17,
            "JobType": 45,
            "Duration": 3600,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {
              "Id": 100010,
              "Amount": 10300
            },
            "CurrentArticleAmount": 7187,
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
                  "Amount": 2250
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
          {
            "Id": "7a3e7c99-c24d-4192-9af3-424e921f516c",
            "JobLocationId": 100010,
            "JobLevel": 18,
            "JobType": 45,
            "Duration": 3600,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {
              "Id": 100010,
              "Amount": 12800
            },
            "CurrentArticleAmount": 900,
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
                  "Amount": 2250
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
                "Value": 3
              },
              {
                "Type": "rarity",
                "Value": 3
              },
              {
                "Type": "era",
                "Value": 2
              }
            ],
            "UnlocksAt": "2022-12-05T12:00:00Z",
            "ExpiresAt": "2023-03-03T12:00:00Z"
          }
        ],

"""

"""


"""