import json
import random
from datetime import timedelta, datetime
from time import sleep
from typing import List, Iterator, Tuple, Dict, Optional, Callable

from django.conf import settings

from app_root.exceptions import check_response
from app_root.mixins import ImportHelperMixin
from app_root.players.models import PlayerTrain, PlayerDailyReward, PlayerWhistle, PlayerWhistleItem
from app_root.servers.models import RunVersion, EndPoint
from app_root.strategies.managers import warehouse_add_article, whistle_remove
from app_root.utils import get_curr_server_str_datetime_s
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

    def get_next_event_time(self) -> Optional[datetime]:
        return None

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
        self.train.has_load = False
        self.train.load_amount = 0
        self.train.load_id = None
        self.train.save(update_fields=[
            'has_load',
            'load_amount',
            'load_id',
        ])


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
            today_reward = self.reward.get_today_reward()
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
            today_reward = self.reward.get_today_reward()
            if today_reward:
                _id = today_reward.get('Id', None)
                _value = today_reward.get('Value', None)
                _amount = today_reward.get('Amount', None)

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
        """
            POST /api/v2/command-processing/run-collection HTTP/1.1
            PXFD-Request-Id: 0a645537-2b6d-4c99-81ef-d968877ca303
            PXFD-Retry-No: 0
            PXFD-Sent-At: 2023-01-23T12:43:05.815Z
            PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}
            PXFD-Client-Version: 2.6.3.4068
            PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
            PXFD-Game-Access-Token: f5019986-472e-52ca-b95a-aa520bdbfbca
            PXFD-Player-Id: 62794770
            Content-Type: application/json
            Content-Length: 148
            Host: game.trainstation2.com
            Accept-Encoding: gzip, deflate

    {
        "Id":1,
        "Time":"2023-01-23T12:43:05Z",
        "Commands":[
            {
                "Command":"Game:Heartbeat",
                "Time":"2023-01-23T12:43:05Z",
                "Parameters":{}
            }
        ],
        "Transactional":false
    }

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

        self.version.command_no += 1
        self.version.save(
            update_fields=['command_no']
        )
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

    def _parse_command_whistle_spawn(self, data):
        whistles = data.get('Whistle')
        if whistles:
            bulk_list, bulk_item_list = PlayerWhistle.create_instance(data=whistles, version_id=self.version.id)

            if bulk_list:
                PlayerWhistle.objects.bulk_create(bulk_list, 100)

            if bulk_item_list:
                PlayerWhistleItem.objects.bulk_create(bulk_item_list, 100)

        self.print_remain('_parse_init_whistles', data)

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
