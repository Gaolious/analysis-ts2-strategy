import json
import random
from datetime import timedelta, datetime
from time import sleep
from typing import List, Iterator, Tuple, Dict, Optional, Callable

from django.conf import settings

from app_root.exceptions import check_response
from app_root.mixins import ImportHelperMixin
from app_root.players.models import PlayerTrain, PlayerDailyReward, PlayerWhistle, PlayerWhistleItem, PlayerDestination, \
    PlayerDailyOfferContainer, PlayerDailyOffer, PlayerDailyOfferItem, PlayerJob, PlayerLeaderBoard, PlayerContract, \
    PlayerFactoryProductOrder
from app_root.servers.models import RunVersion, EndPoint, TSDestination, TSProduct
from app_root.strategies.managers import warehouse_add_article, whistle_remove, trains_unload, \
    trains_set_destination, container_offer_set_used, destination_set_used, daily_offer_set_used, trains_set_job, \
    contract_set_used, factory_order_product, factory_collect_product
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
    dest: TSDestination
    SLEEP_RANGE = (1.0, 1.5)

    def __init__(self, *, train: PlayerTrain, dest: TSDestination, **kwargs):
        super(TrainSendToDestinationCommand, self).__init__(**kwargs)
        self.train = train
        self.dest = dest

    def get_parameters(self) -> dict:
        """

        :return:
        """
        return {
            'TrainId': self.train.instance_id,
            'DestinationId': self.dest.id,
        }

    def post_processing(self, server_data: Dict):
        departure_at = get_curr_server_datetime(version=self.version)
        arrival_at = departure_at + timedelta(seconds=self.dest.travel_duration)
        trains_set_destination(
            version=self.version,
            train=self.train,
            definition_id=self.dest.id,
            departure_at=departure_at,
            arrival_at=arrival_at
        )
        destination_set_used(
            version=self.version,
            dest=self.dest
        )


class TrainDispatchToJobCommand(BaseCommand):
    """
[LeaderBoard]
{"Success":true,"RequestId":"37549e03-92c2-4850-9f32-efcd381e3282","Time":"2023-02-06T05:04:09Z","Data":{"LeaderboardId":"329a0e3a-038d-4bd4-a99d-b19ed9dcde20","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","Bracket":"1","Progresses":[{"PlayerId":20873082,"AvatarId":59,"FirebaseUid":"prod_20873082","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"DJ.GRooWER Hun","Progress":142,"LastUpdate":"2023-02-06T04:18:58Z","RewardClaimed":false},{"PlayerId":36725548,"AvatarId":70,"FirebaseUid":"prod_36725548","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Offiget","Progress":98,"LastUpdate":"2023-02-05T21:21:05Z","RewardClaimed":false},{"PlayerId":42991064,"AvatarId":59,"FirebaseUid":"prod_42991064","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"John co","Progress":20,"LastUpdate":"2023-02-05T16:06:51Z","RewardClaimed":false},{"PlayerId":43023388,"AvatarId":70,"FirebaseUid":"prod_43023388","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"JarHead0352","Progress":72,"LastUpdate":"2023-02-05T23:42:06Z","RewardClaimed":false},{"PlayerId":51701244,"AvatarId":59,"FirebaseUid":"prod_51701244","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Squidworth","Progress":50,"LastUpdate":"2023-02-05T21:44:11Z","RewardClaimed":false},{"PlayerId":52529982,"AvatarId":8,"FirebaseUid":"prod_52529982","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Jessen","Progress":0,"LastUpdate":"2023-02-03T12:08:09Z","RewardClaimed":false},{"PlayerId":53255036,"AvatarId":71,"FirebaseUid":"prod_53255036","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"ShadowV1965","Progress":0,"LastUpdate":"2023-02-03T12:08:14Z","RewardClaimed":false},{"PlayerId":55570560,"AvatarId":123,"FirebaseUid":"prod_55570560","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Spider","Progress":35,"LastUpdate":"2023-02-05T19:33:59Z","RewardClaimed":false},{"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"SRand","Progress":0,"LastUpdate":"2023-02-03T12:08:28Z","RewardClaimed":false},{"PlayerId":61656034,"AvatarId":121,"FirebaseUid":"prod_61656034","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Cootabang","Progress":0,"LastUpdate":"2023-02-03T12:08:31Z","RewardClaimed":false},{"PlayerId":63527822,"AvatarId":120,"FirebaseUid":"prod_63527822","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Adnan","Progress":80,"LastUpdate":"2023-02-05T21:21:39Z","RewardClaimed":false},{"PlayerId":65333042,"AvatarId":1,"FirebaseUid":"prod_65333042","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"flobuiss ","Progress":91,"LastUpdate":"2023-02-06T04:35:59Z","RewardClaimed":false},{"PlayerId":65958250,"AvatarId":1,"FirebaseUid":"prod_65958250","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Choo Choo Charlie","Progress":182,"LastUpdate":"2023-02-06T04:33:54Z","RewardClaimed":false},{"PlayerId":66288442,"AvatarId":14,"FirebaseUid":"prod_66288442","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"AMJ Railroad ","Progress":11,"LastUpdate":"2023-02-03T17:01:03Z","RewardClaimed":false},{"PlayerId":66674602,"AvatarId":70,"FirebaseUid":"prod_66674602","LeaderBoardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","LeaderboardGroupId":"e391e702-32fd-41fe-8866-639e50e39352","PlayerName":"Claudemir ","Progress":60,"LastUpdate":"2023-02-05T22:22:41Z","RewardClaimed":false}],"Rewards":[{"Items":[{"Id":8,"Value":8,"Amount":176}]},{"Items":[{"Id":8,"Value":8,"Amount":150}]},{"Items":[{"Id":8,"Value":8,"Amount":110}]},{"Items":[{"Id":8,"Value":8,"Amount":64}]},{"Items":[{"Id":8,"Value":8,"Amount":40}]},{"Items":[{"Id":8,"Value":8,"Amount":33}]},{"Items":[{"Id":8,"Value":8,"Amount":31}]},{"Items":[{"Id":8,"Value":8,"Amount":22}]},{"Items":[{"Id":8,"Value":8,"Amount":20}]},{"Items":[{"Id":8,"Value":8,"Amount":18}]},{"Items":[{"Id":8,"Value":8,"Amount":11}]},{"Items":[{"Id":8,"Value":8,"Amount":9}]},{"Items":[{"Id":8,"Value":8,"Amount":7}]},{"Items":[{"Id":8,"Value":8,"Amount":5}]},{"Items":[{"Id":8,"Value":8,"Amount":3}]}]}}
{"Success":true,"RequestId":"984210f6-0180-4ee7-81ef-d3b340dc7278","Time":"2023-02-06T05:04:33Z","Data":{"LeaderboardId":"563b3067-a1a7-4a8b-9986-4ab8b0048e26","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","Bracket":"1","Progresses":[{"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"SRand","Progress":240,"Position":1,"LastUpdatedAt":"2023-02-06T05:04:30Z","RewardClaimed":false},{"PlayerId":45329266,"AvatarId":11,"FirebaseUid":"prod_45329266","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"shine1219","Progress":60,"Position":2,"LastUpdatedAt":"2023-02-05T14:32:42Z","RewardClaimed":false},{"PlayerId":45387522,"AvatarId":1,"FirebaseUid":"prod_45387522","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Kr.Wanja","Progress":53,"Position":3,"LastUpdatedAt":"2023-02-06T03:34:30Z","RewardClaimed":false},{"PlayerId":37482414,"AvatarId":24,"FirebaseUid":"prod_37482414","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"DARKCHOCO","Progress":40,"Position":4,"LastUpdatedAt":"2023-02-05T18:35:13Z","RewardClaimed":false},{"PlayerId":26401848,"AvatarId":24,"FirebaseUid":"prod_26401848","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Clutch","Progress":38,"Position":5,"LastUpdatedAt":"2023-02-05T15:05:41Z","RewardClaimed":false},{"PlayerId":2147982,"AvatarId":109,"FirebaseUid":"prod_2147982","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Ghind","Progress":33,"Position":6,"LastUpdatedAt":"2023-02-05T16:42:00Z","RewardClaimed":false},{"PlayerId":31423644,"AvatarId":89,"FirebaseUid":"prod_31423644","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Cindy","Progress":30,"Position":7,"LastUpdatedAt":"2023-02-06T00:21:59Z","RewardClaimed":false},{"PlayerId":51063284,"AvatarId":71,"FirebaseUid":"prod_51063284","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Greenday","Progress":30,"Position":8,"LastUpdatedAt":"2023-02-06T00:52:57Z","RewardClaimed":false},{"PlayerId":27674098,"AvatarId":25,"FirebaseUid":"prod_27674098","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"KTKSRTK","Progress":15,"Position":9,"LastUpdatedAt":"2023-02-06T01:51:12Z","RewardClaimed":false}],"Rewards":[{"Items":[{"Id":8,"Value":100000,"Amount":69},{"Id":8,"Value":100003,"Amount":52}]},{"Items":[{"Id":8,"Value":100000,"Amount":17},{"Id":8,"Value":100003,"Amount":13}]},{"Items":[{"Id":8,"Value":100000,"Amount":15},{"Id":8,"Value":100003,"Amount":11}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":9},{"Id":8,"Value":100003,"Amount":7}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":4},{"Id":8,"Value":100003,"Amount":3}]}]}}
{"Success":true,"RequestId":"90098378-fcf7-4c3d-ac80-3e0039888e36","Time":"2023-02-06T05:04:36Z","Data":{"LeaderboardId":"563b3067-a1a7-4a8b-9986-4ab8b0048e26","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","Bracket":"1","Progresses":[{"PlayerId":61561146,"AvatarId":58,"FirebaseUid":"prod_61561146","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"SRand","Progress":270,"Position":1,"LastUpdatedAt":"2023-02-06T05:04:33Z","RewardClaimed":false},{"PlayerId":45329266,"AvatarId":11,"FirebaseUid":"prod_45329266","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"shine1219","Progress":60,"Position":2,"LastUpdatedAt":"2023-02-05T14:32:42Z","RewardClaimed":false},{"PlayerId":45387522,"AvatarId":1,"FirebaseUid":"prod_45387522","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Kr.Wanja","Progress":53,"Position":3,"LastUpdatedAt":"2023-02-06T03:34:30Z","RewardClaimed":false},{"PlayerId":37482414,"AvatarId":24,"FirebaseUid":"prod_37482414","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"DARKCHOCO","Progress":40,"Position":4,"LastUpdatedAt":"2023-02-05T18:35:13Z","RewardClaimed":false},{"PlayerId":26401848,"AvatarId":24,"FirebaseUid":"prod_26401848","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Clutch","Progress":38,"Position":5,"LastUpdatedAt":"2023-02-05T15:05:41Z","RewardClaimed":false},{"PlayerId":2147982,"AvatarId":109,"FirebaseUid":"prod_2147982","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Ghind","Progress":33,"Position":6,"LastUpdatedAt":"2023-02-05T16:42:00Z","RewardClaimed":false},{"PlayerId":31423644,"AvatarId":89,"FirebaseUid":"prod_31423644","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Cindy","Progress":30,"Position":7,"LastUpdatedAt":"2023-02-06T00:21:59Z","RewardClaimed":false},{"PlayerId":51063284,"AvatarId":71,"FirebaseUid":"prod_51063284","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"Greenday","Progress":30,"Position":8,"LastUpdatedAt":"2023-02-06T00:52:57Z","RewardClaimed":false},{"PlayerId":27674098,"AvatarId":25,"FirebaseUid":"prod_27674098","LeaderboardGroupId":"3a3dfa63-2e0f-4a40-b36c-08d252db9c2b","PlayerName":"KTKSRTK","Progress":15,"Position":9,"LastUpdatedAt":"2023-02-06T01:51:12Z","RewardClaimed":false}],"Rewards":[{"Items":[{"Id":8,"Value":100000,"Amount":78},{"Id":8,"Value":100003,"Amount":58}]},{"Items":[{"Id":8,"Value":100000,"Amount":17},{"Id":8,"Value":100003,"Amount":13}]},{"Items":[{"Id":8,"Value":100000,"Amount":15},{"Id":8,"Value":100003,"Amount":11}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":11},{"Id":8,"Value":100003,"Amount":8}]},{"Items":[{"Id":8,"Value":100000,"Amount":9},{"Id":8,"Value":100003,"Amount":7}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":8},{"Id":8,"Value":100003,"Amount":6}]},{"Items":[{"Id":8,"Value":100000,"Amount":4},{"Id":8,"Value":100003,"Amount":3}]}]}}
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
        return {
            "UniqueId": self.leaderboard.leader_board_group_id,
            "TrainId": self.train.instance_id,
            "JobLocationId": self.job.job_location_id,
            "Load": {
                "Id": self.job.required_article_id,
                "Amount": self.amount
            }
        }

    def post_processing(self, server_data: Dict):
        departure_at = get_curr_server_datetime(version=self.version)
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


###################################################################
# Product Order in Factory
###################################################################
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
# Ship Offer
###################################################################
"""
Step 1. 제품 수집

################################################
Step 2. ship 보내기 - sleep 
################################################
12 11:35:39 | T: 6701 | I | SSL_AsyncWrite  | buffer : 
                                              {'buffer': 'POST /api/v2/command-processing/run-collection HTTP/1.1\r\nPXFD-Request-Id: a8438911-4593-4144-98ce-540a288a90ec\r\nPXFD-Retry-No: 0\r\nPXFD-Sent-At: 2023-01-12T02:35:38.982Z\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json\r\nContent-Length: 205\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

12 11:35:39 | T: 6692 | I | WebReqStream    | buffer : 
                                              {'buffer': '{"Id":36,"Time":"2023-01-12T02:35:38Z","Commands":[{"Command":"Game:Sleep","Time":"2023-01-12T02:35:38Z","Parameters":{},"Debug":{"CollectionsInQueue":0,"CollectionsInQueueIds":""}}],"Transactional":false}'}

12 11:35:39 | T: 6700 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              05ad7010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
                                              05ad7020  22 52 65 71 75 65 73 74 49 64 22 3a 22 61 38 34  "RequestId":"a84
                                              05ad7030  33 38 39 31 31 2d 34 35 39 33 2d 34 31 34 34 2d  38911-4593-4144-
                                              05ad7040  39 38 63 65 2d 35 34 30 61 32 38 38 61 39 30 65  98ce-540a288a90e
                                              05ad7050  63 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 33 2d  c","Time":"2023-
                                              05ad7060  30 31 2d 31 32 54 30 32 3a 33 35 3a 33 39 5a 22  01-12T02:35:39Z"
                                              05ad7070  2c 22 44 61 74 61 22 3a 7b 22 43 6f 6c 6c 65 63  ,"Data":{"Collec
                                              05ad7080  74 69 6f 6e 49 64 22 3a 33 36 2c 22 43 6f 6d 6d  tionId":36,"Comm
                                              05ad7090  61 6e 64 73 22 3a 5b 5d 7d 7d                    ands":[]}}

################################################
Step 2. ship 보내기 - ????
################################################

12 11:36:14 | T: 6700 | I | SSL_AsyncWrite  | buffer : 
                                              {'buffer': 'POST /api/v2/transfer-client-event/video_ads HTTP/1.1\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: 71\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

12 11:36:14 | T: 6701 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              05ad7010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
                                              05ad7020  22 52 65 71 75 65 73 74 49 64 22 3a 22 30 31 32  "RequestId":"012
                                              05ad7030  63 63 38 66 61 2d 38 32 38 63 2d 34 34 36 37 2d  cc8fa-828c-4467-
                                              05ad7040  62 38 37 34 2d 64 30 35 62 35 61 64 66 32 65 61  b874-d05b5adf2ea
                                              05ad7050  61 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 33 2d  a","Time":"2023-
                                              05ad7060  30 31 2d 31 32 54 30 32 3a 33 36 3a 31 35 5a 22  01-12T02:36:15Z"
                                              05ad7070  7d                                               }


12 11:36:15 | T: 6701 | I | SSL_AsyncWrite  | buffer : 
                                              {'buffer': 'POST /api/v2/transfer-client-event/video_ads HTTP/1.1\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: 73\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

12 11:36:15 | T: 6701 | I | WebReqStream    | buffer : 
                                              {'buffer': '{"Placement":"ship_offer_claim_double","Action":"Rewarded","ErrorCode":0}'}

12 11:36:15 | T: 6700 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              052d5010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
                                              052d5020  22 52 65 71 75 65 73 74 49 64 22 3a 22 36 66 64  "RequestId":"6fd
                                              052d5030  37 33 65 34 64 2d 36 62 34 38 2d 34 31 36 34 2d  73e4d-6b48-4164-
                                              052d5040  61 63 38 36 2d 62 34 39 36 38 62 30 63 34 35 38  ac86-b4968b0c458
                                              052d5050  62 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 33 2d  b","Time":"2023-
                                              052d5060  30 31 2d 31 32 54 30 32 3a 33 36 3a 31 35 5a 22  01-12T02:36:15Z"
                                              052d5070  7d                                               }

12 11:36:15 | T: 6700 | I | SSL_AsyncWrite  | buffer : 
                                              {'buffer': 'POST /api/v2/transfer-client-event/video_ads HTTP/1.1\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: 71\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

12 11:36:15 | T: 6701 | I | WebReqStream    | buffer : 
                                              {'buffer': '{"Placement":"ship_offer_claim_double","Action":"Closed","ErrorCode":0}'}

12 11:36:15 | T: 6688 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              05ad7010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
                                              05ad7020  22 52 65 71 75 65 73 74 49 64 22 3a 22 64 64 39  "RequestId":"dd9
                                              05ad7030  32 36 64 32 31 2d 64 32 63 33 2d 34 36 63 32 2d  26d21-d2c3-46c2-
                                              05ad7040  61 33 38 33 2d 30 38 62 34 62 34 65 66 64 34 32  a383-08b4b4efd42
                                              05ad7050  38 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 33 2d  8","Time":"2023-
                                              05ad7060  30 31 2d 31 32 54 30 32 3a 33 36 3a 31 35 5a 22  01-12T02:36:15Z"
                                              05ad7070  7d                                               }

12 11:36:17 | T: 6688 | I | parse_req_data  | RequestData
                                              {'instance': '0x89a3a840', 'monitor': '0x0', 'url': 'https://game.trainstation2.com/api/v2/command-processing/run-collection', 'method': 'POST', 'req_id': 'c51ca065-ceac-4845-8a1f-92db0526df3e', 'is_binary': 0, 'retry_no': 0}
 
12 11:36:17 | T: 6688 | I | IO.Mem.Write    | onEnter - params : 
                                              {'instance': '0x296d150', 'buffer': '0x2949000', 'offset': '0x0', 'count': 300, 'method': '0x88461560'}
12 11:36:17 | T: 6688 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              02949010  7b 22 49 64 22 3a 33 37 2c 22 54 69 6d 65 22 3a  {"Id":37,"Time":
                                              02949020  22 32 30 32 33 2d 30 31 2d 31 32 54 30 32 3a 33  "2023-01-12T02:3
                                              02949030  36 3a 31 37 5a 22 2c 22 43 6f 6d 6d 61 6e 64 73  6:17Z","Commands
                                              02949040  22 3a 5b 7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 47  ":[{"Command":"G
                                              02949050  61 6d 65 3a 57 61 6b 65 55 70 22 2c 22 54 69 6d  ame:WakeUp","Tim
                                              02949060  65 22 3a 22 32 30 32 33 2d 30 31 2d 31 32 54 30  e":"2023-01-12T0
                                              02949070  32 3a 33 35 3a 33 38 5a 22 2c 22 50 61 72 61 6d  2:35:38Z","Param
                                              02949080  65 74 65 72 73 22 3a 7b 7d 7d 2c 7b 22 43 6f 6d  eters":{}},{"Com
                                              02949090  6d 61 6e 64 22 3a 22 43 6f 6e 74 72 61 63 74 3a  mand":"Contract:
                                              029490a0  41 63 63 65 70 74 57 69 74 68 56 69 64 65 6f 52  AcceptWithVideoR
                                              029490b0  65 77 61 72 64 22 2c 22 54 69 6d 65 22 3a 22 32  eward","Time":"2
                                              029490c0  30 32 33 2d 30 31 2d 31 32 54 30 32 3a 33 36 3a  023-01-12T02:36:
                                              029490d0  31 37 5a 22 2c 22 50 61 72 61 6d 65 74 65 72 73  17Z","Parameters
                                              029490e0  22 3a 7b 22 43 6f 6e 74 72 61 63 74 4c 69 73 74  ":{"ContractList
                                              029490f0  49 64 22 3a 33 2c 22 53 6c 6f 74 22 3a 31 2c 22  Id":3,"Slot":1,"
                                              02949100  41 63 63 65 70 74 65 64 41 74 22 3a 22 32 30 32  AcceptedAt":"202
                                              02949110  33 2d 30 31 2d 31 32 54 30 32 3a 33 35 3a 33 38  3-01-12T02:35:38
                                              02949120  5a 22 7d 7d 5d 2c 22 54 72 61 6e 73 61 63 74 69  Z"}}],"Transacti
                                              02949130  6f 6e 61 6c 22 3a 66 61 6c 73 65 7d              onal":false}

12 11:36:17 | T: 6701 | I | SSL_AsyncWrite  | buffer : 
                                              {'buffer': 'POST /api/v2/command-processing/run-collection HTTP/1.1\r\nPXFD-Request-Id: c51ca065-ceac-4845-8a1f-92db0526df3e\r\nPXFD-Retry-No: 0\r\nPXFD-Sent-At: 2023-01-12T02:36:17.809Z\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json\r\nContent-Length: 300\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

12 11:36:17 | T: 6700 | I | WebReqStream    | buffer : 
                                              {'buffer': '{"Id":37,"Time":"2023-01-12T02:36:17Z","Commands":[{"Command":"Game:WakeUp","Time":"2023-01-12T02:35:38Z","Parameters":{}},{"Command":"Contract:AcceptWithVideoReward","Time":"2023-01-12T02:36:17Z","Parameters":{"ContractListId":3,"Slot":1,"AcceptedAt":"2023-01-12T02:35:38Z"}}],"Transactional":false}'}

12 11:36:18 | T: 6701 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              05f3c010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
                                              05f3c020  22 52 65 71 75 65 73 74 49 64 22 3a 22 63 35 31  "RequestId":"c51
                                              05f3c030  63 61 30 36 35 2d 63 65 61 63 2d 34 38 34 35 2d  ca065-ceac-4845-
                                              05f3c040  38 61 31 66 2d 39 32 64 62 30 35 32 36 64 66 33  8a1f-92db0526df3
                                              05f3c050  65 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 33 2d  e","Time":"2023-
                                              05f3c060  30 31 2d 31 32 54 30 32 3a 33 36 3a 31 38 5a 22  01-12T02:36:18Z"
                                              05f3c070  2c 22 44 61 74 61 22 3a 7b 22 43 6f 6c 6c 65 63  ,"Data":{"Collec
                                              05f3c080  74 69 6f 6e 49 64 22 3a 33 37 2c 22 43 6f 6d 6d  tionId":37,"Comm
                                              05f3c090  61 6e 64 73 22 3a 5b 7b 22 43 6f 6d 6d 61 6e 64  ands":[{"Command
                                              05f3c0a0  22 3a 22 53 68 69 70 4c 6f 6f 70 3a 43 68 61 6e  ":"ShipLoop:Chan
                                              05f3c0b0  67 65 22 2c 22 44 61 74 61 22 3a 7b 22 44 65 66  ge","Data":{"Def
                                              05f3c0c0  69 6e 69 74 69 6f 6e 49 64 22 3a 35 7d 2c 22 49  initionId":5},"I
                                              05f3c0d0  64 22 3a 22 61 37 64 36 63 64 31 34 2d 64 64 63  d":"a7d6cd14-ddc
                                              05f3c0e0  61 2d 34 62 35 63 2d 39 65 63 33 2d 64 38 66 37  a-4b5c-9ec3-d8f7
                                              05f3c0f0  35 31 64 36 35 63 38 32 22 7d 2c 7b 22 43 6f 6d  51d65c82"},{"Com
                                              05f3c100  6d 61 6e 64 22 3a 22 41 63 68 69 65 76 65 6d 65  mand":"Achieveme
                                              05f3c110  6e 74 3a 43 68 61 6e 67 65 22 2c 22 44 61 74 61  nt:Change","Data
                                              05f3c120  22 3a 7b 22 41 63 68 69 65 76 65 6d 65 6e 74 22  ":{"Achievement"
                                              05f3c130  3a 7b 22 41 63 68 69 65 76 65 6d 65 6e 74 49 64  :{"AchievementId
                                              05f3c140  22 3a 22 73 68 69 70 5f 6c 6f 6f 70 5f 74 72 61  ":"ship_loop_tra
                                              05f3c150  64 65 22 2c 22 4c 65 76 65 6c 22 3a 35 2c 22 50  de","Level":5,"P
                                              05f3c160  72 6f 67 72 65 73 73 22 3a 32 31 36 7d 7d 7d 2c  rogress":216}}},
                                              05f3c170  7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 50 6c 61 79  {"Command":"Play
                                              05f3c180  65 72 43 6f 6d 70 61 6e 79 3a 53 74 61 74 73 3a  erCompany:Stats:
                                              05f3c190  43 68 61 6e 67 65 22 2c 22 44 61 74 61 22 3a 7b  Change","Data":{
                                              05f3c1a0  22 53 74 61 74 73 22 3a 7b 22 54 79 70 65 22 3a  "Stats":{"Type":
                                              05f3c1b0  22 73 68 69 70 5f 6c 6f 6f 70 5f 74 72 61 64 65  "ship_loop_trade
                                              05f3c1c0  22 2c 22 50 72 6f 67 72 65 73 73 22 3a 34 33 32  ","Progress":432
                                              05f3c1d0  30 7d 7d 7d 2c 7b 22 43 6f 6d 6d 61 6e 64 22 3a  0}}},{"Command":
                                              05f3c1e0  22 43 6f 6e 74 72 61 63 74 3a 4e 65 77 22 2c 22  "Contract:New","
                                              05f3c1f0  44 61 74 61 22 3a 7b 22 43 6f 6e 74 72 61 63 74  Data":{"Contract
                                              05f3c200  22 3a 7b 22 53 6c 6f 74 22 3a 32 2c 22 43 6f 6e  ":{"Slot":2,"Con
                                              05f3c210  74 72 61 63 74 4c 69 73 74 49 64 22 3a 33 2c 22  tractListId":3,"
                                              05f3c220  43 6f 6e 64 69 74 69 6f 6e 73 22 3a 5b 7b 22 49  Conditions":[{"I
                                              05f3c230  64 22 3a 31 30 34 2c 22 41 6d 6f 75 6e 74 22 3a  d":104,"Amount":
                                              05f3c240  34 30 36 7d 2c 7b 22 49 64 22 3a 31 31 31 2c 22  406},{"Id":111,"
                                              05f3c250  41 6d 6f 75 6e 74 22 3a 31 34 30 7d 2c 7b 22 49  Amount":140},{"I
                                              05f3c260  64 22 3a 31 30 38 2c 22 41 6d 6f 75 6e 74 22 3a  d":108,"Amount":
                                              05f3c270  31 30 37 7d 5d 2c 22 52 65 77 61 72 64 22 3a 7b  107}],"Reward":{
                                              05f3c280  22 49 74 65 6d 73 22 3a 5b 7b 22 49 64 22 3a 38  "Items":[{"Id":8
                                              05f3c290  2c 22 56 61 6c 75 65 22 3a 32 2c 22 41 6d 6f 75  ,"Value":2,"Amou
                                              05f3c2a0  6e 74 22 3a 36 7d 2c 7b 22 49 64 22 3a 38 2c 22  nt":6},{"Id":8,"
                                              05f3c2b0  56 61 6c 75 65 22 3a 31 31 2c 22 41 6d 6f 75 6e  Value":11,"Amoun
                                              05f3c2c0  74 22 3a 31 30 7d 2c 7b 22 49 64 22 3a 38 2c 22  t":10},{"Id":8,"
                                              05f3c2d0  56 61 6c 75 65 22 3a 31 32 2c 22 41 6d 6f 75 6e  Value":12,"Amoun
                                              05f3c2e0  74 22 3a 37 7d 2c 7b 22 49 64 22 3a 38 2c 22 56  t":7},{"Id":8,"V
                                              05f3c2f0  61 6c 75 65 22 3a 31 30 2c 22 41 6d 6f 75 6e 74  alue":10,"Amount
                                              05f3c300  22 3a 31 33 7d 5d 7d 2c 22 55 73 61 62 6c 65 46  ":13}]},"UsableF
                                              05f3c310  72 6f 6d 22 3a 22 32 30 32 33 2d 30 31 2d 31 32  rom":"2023-01-12
                                              05f3c320  54 31 38 3a 33 35 3a 33 38 5a 22 2c 22 41 76 61  T18:35:38Z","Ava
                                              05f3c330  69 6c 61 62 6c 65 46 72 6f 6d 22 3a 22 31 39 37  ilableFrom":"197
                                              05f3c340  30 2d 30 31 2d 30 31 54 30 30 3a 30 30 3a 30 30  0-01-01T00:00:00
                                              05f3c350  5a 22 2c 22 41 76 61 69 6c 61 62 6c 65 54 6f 22  Z","AvailableTo"
                                              05f3c360  3a 22 32 39 39 39 2d 31 32 2d 33 31 54 30 30 3a  :"2999-12-31T00:
                                              05f3c370  30 30 3a 30 30 5a 22 7d 7d 2c 22 49 64 22 3a 22  00:00Z"}},"Id":"
                                              05f3c380  63 62 34 61 61 33 64 33 2d 30 66 37 34 2d 34 62  cb4aa3d3-0f74-4b
                                              05f3c390  32 61 2d 38 30 36 62 2d 36 30 62 36 64 33 39 37  2a-806b-60b6d397
                                              05f3c3a0  35 33 63 31 22 7d 2c 7b 22 43 6f 6d 6d 61 6e 64  53c1"},{"Command
                                              05f3c3b0  22 3a 22 53 68 69 70 3a 4f 66 66 65 72 22 2c 22  ":"Ship:Offer","
                                              05f3c3c0  44 61 74 61 22 3a 7b 22 53 68 69 70 22 3a 7b 22  Data":{"Ship":{"
                                              05f3c3d0  44 65 66 69 6e 69 74 69 6f 6e 49 64 22 3a 35 2c  DefinitionId":5,
                                              05f3c3e0  22 43 6f 6e 64 69 74 69 6f 6e 73 22 3a 5b 7b 22  "Conditions":[{"
                                              05f3c3f0  49 64 22 3a 31 30 34 2c 22 41 6d 6f 75 6e 74 22  Id":104,"Amount"
                                              05f3c400  3a 34 30 36 7d 2c 7b 22 49 64 22 3a 31 31 31 2c  :406},{"Id":111,
                                              05f3c410  22 41 6d 6f 75 6e 74 22 3a 31 34 30 7d 2c 7b 22  "Amount":140},{"
                                              05f3c420  49 64 22 3a 31 30 38 2c 22 41 6d 6f 75 6e 74 22  Id":108,"Amount"
                                              05f3c430  3a 31 30 37 7d 5d 2c 22 52 65 77 61 72 64 22 3a  :107}],"Reward":
                                              05f3c440  7b 22 49 74 65 6d 73 22 3a 5b 7b 22 49 64 22 3a  {"Items":[{"Id":
                                              05f3c450  38 2c 22 56 61 6c 75 65 22 3a 32 2c 22 41 6d 6f  8,"Value":2,"Amo
                                              05f3c460  75 6e 74 22 3a 36 7d 2c 7b 22 49 64 22 3a 38 2c  unt":6},{"Id":8,
                                              05f3c470  22 56 61 6c 75 65 22 3a 31 31 2c 22 41 6d 6f 75  "Value":11,"Amou
                                              05f3c480  6e 74 22 3a 31 30 7d 2c 7b 22 49 64 22 3a 38 2c  nt":10},{"Id":8,
                                              05f3c490  22 56 61 6c 75 65 22 3a 31 32 2c 22 41 6d 6f 75  "Value":12,"Amou
                                              05f3c4a0  6e 74 22 3a 37 7d 2c 7b 22 49 64 22 3a 38 2c 22  nt":7},{"Id":8,"
                                              05f3c4b0  56 61 6c 75 65 22 3a 31 30 2c 22 41 6d 6f 75 6e  Value":10,"Amoun
                                              05f3c4c0  74 22 3a 31 33 7d 5d 7d 2c 22 41 72 72 69 76 61  t":13}]},"Arriva
                                              05f3c4d0  6c 41 74 22 3a 22 32 30 32 33 2d 30 31 2d 31 32  lAt":"2023-01-12
                                              05f3c4e0  54 31 38 3a 33 35 3a 33 38 5a 22 7d 7d 2c 22 49  T18:35:38Z"}},"I
                                              05f3c4f0  64 22 3a 22 38 64 65 33 36 32 66 38 2d 61 62 31  d":"8de362f8-ab1
                                              05f3c500  33 2d 34 66 61 31 2d 62 32 39 61 2d 66 65 34 31  3-4fa1-b29a-fe41
                                              05f3c510  62 36 38 63 64 33 32 64 22 7d 2c 7b 22 43 6f 6d  b68cd32d"},{"Com
                                              05f3c520  6d 61 6e 64 22 3a 22 50 6c 61 79 65 72 43 6f 6d  mand":"PlayerCom
                                              05f3c530  70 61 6e 79 3a 43 68 61 6e 67 65 56 61 6c 75 65  pany:ChangeValue
                                              05f3c540  22 2c 22 44 61 74 61 22 3a 7b 22 56 61 6c 75 65  ","Data":{"Value
                                              05f3c550  22 3a 31 37 35 33 38 34 7d 7d 5d 7d 7d           ":175384}}]}}

"""
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