#
# class BaseCommand(object):
#     """
#         BaseCommand
#     """
#     COMMAND = ''
#     helper: BaseCommandHelper
#     SLEEP_RANGE = (0.5, 1.5)
#     _start_datetime: datetime
#
#     def __init__(self, *, helper: BaseCommandHelper, **kwargs):
#         self.helper = helper
#
#     def get_parameters(self) -> dict:
#         return {}
#
#     def get_command(self):
#         self._start_datetime = self.helper.server_time.get_curr_datetime()
#
#         return {
#             'Command': self.COMMAND,
#             'Time': self.helper.server_time.get_curr_time_s(),
#             'Parameters': self.get_parameters()
#         }
#
#     def sleep(self):
#         self.helper._do_sleep(min_second=self.SLEEP_RANGE[0], max_second=self.SLEEP_RANGE[1])
#
#     def duration(self) -> int:
#         return 0
#
#     def end_datetime(self) -> datetime:
#         return self._start_datetime + timedelta(seconds=self.duration())
#
#     def __str__(self):
#         return f'''[{self.COMMAND}] / parameters: {self.get_parameters()}'''
#
#     def post_processing(self):
#         pass
#
#
# class TrainUnloadCommand(BaseCommand):
#     """
#     기차에서 수집
#     {
#         "Command":"Train:Unload",
#         "Time":"2023-01-11T01:01:44Z",
#         "Parameters":{
#             "TrainId":10
#         }
#     }
#     """
#     COMMAND = 'Train:Unload'
#     train: PlayerTrain
#     SLEEP_RANGE = (0.2, 0.5)
#
#     def __init__(self, *, train: PlayerTrain, **kwargs):
#         super(TrainUnloadCommand, self).__init__(**kwargs)
#         self.train = train
#
#     def get_parameters(self) -> dict:
#         """
#
#         :return:
#         """
#         return {
#             'TrainId': self.train.instance_id
#         }
#
#     def post_processing(self):
#         if self.train.load_id:
#             self.helper.add_warehouse(
#                 article_id=self.train.load_id,
#                 amount=self.train.load_amount
#             )
#         self.train.has_load = False
#         self.train.load_amount = 0
#         self.train.load_id = None
#
#
# class CollectGiftCommand(BaseCommand):
#     """
#     gift에서 수집
#     {
#         "Command":"Gift:Claim",
#         "Time":"2023-01-09T02:37:59Z",
#         "Parameters":{
#             "Id":"8295a2de-d048-4228-ac02-e3d36c2d3b4a"
#         }
#     }
#     """
#     COMMAND = 'Gift:Claim'
#     gift: PlayerGift
#     SLEEP_RANGE = (0.5, 1)
#
#     def __init__(self, *, gift: PlayerGift, **kwargs):
#         super(CollectGiftCommand, self).__init__(**kwargs)
#         self.gift = gift
#
#     def get_parameters(self) -> dict:
#         """
#
#         :return:
#         """
#         return {
#             'Id': self.gift.job_id
#         }
#
#     def post_processing(self):
#         if self.gift.job_id:
#             job = self.helper.find_job_with_job_id(job_id=self.gift.job_id)
#             if job:
#                 reward = job.rewards_to_article_dict
#
#         self.gift.job_id = ''
#
#
# class CollectJobReward(BaseCommand):
#     # request
#     """
#         POST /api/v2/command-processing/run-collection HTTP/1.1
#         PXFD-Request-Id: b496033d-84d2-4861-b263-58c7166c0da1
#         PXFD-Retry-No: 0
#         PXFD-Sent-At: 2023-01-12T02:58:29.445Z
#         PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}
#         PXFD-Client-Version: 2.6.3.4068
#         PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
#         PXFD-Game-Access-Token: d3a50b5b-53c6-5adf-b693-4018854f773e
#         PXFD-Player-Id: 61561146
#         Content-Type: application/json
#         Content-Length: 165
#         Host: game.trainstation2.com
#         Accept-Encoding: gzip, deflate
#
#
#         {
#             "Id":2,
#             "Time":"2023-01-12T02:58:29Z",
#             "Commands":[
#                 {
#                     "Command":"Job:Collect",
#                     "Time":"2023-01-12T02:58:28Z",
#                     "Parameters":{"JobLocationId":6005}
#                 }
#             ],
#             "Transactional":false
#         }
#     """
#
#     # resp
#     """
# {
#     "Success":true,
#     "RequestId":"b496033d-84d2-4861-b263-58c7166c0da1",
#     "Time":"2023-01-12T02:58:32Z",
#     "Data":{
#         "CollectionId":2,
#         "Commands":[
#             {
#                 "Command":"CommunityTeam:Progress:Update",
#                 "Data":{
#                     "Team":{"CommunityId":6000,"CommunityTeamId":6001,"Progress":1108}
#                 },
#                 "Id":"4dae53a0-06c4-44a3-bb46-854d85cd2b20"
#             },
#             {
#                 "Command":"Milestone:Change",
#                 "Data":{"MilestoneId":6000,"MilestoneProgress":1108}
#             },
#             {
#                 "Command":"Milestone:Change",
#                 "Data":{
#                     "MilestoneId":6002,"MilestoneProgress":1108
#                 }
#             },
#             {
#                 "Command":"LeaderBoard:UpdatePlayerProgress",
#                 "Data":{
#                     "LeaderBoardId":"47595621-5d10-4fcc-a1a6-62acaf0a8645",
#                     "ProgressData":{
#                         "PlayerId":61561146,
#                         "AvatarId":130,
#                         "FirebaseUid":"prod_61561146",
#                         "LeaderBoardGroupId":"e2735b5e-72b1-4212-875b-5443efe668c2",
#                         "LeaderboardGroupId":"e2735b5e-72b1-4212-875b-5443efe668c2",
#                         "PlayerName":"SRand",
#                         "Progress":1108,
#                         "LastUpdate":"2023-01-12T02:58:28Z",
#                         "RewardClaimed":false
#                     }
#                 }
#             },
#             {
#                 "Command":"Map:NewJob",
#                 "Data":{
#                     "Job":{
#                         "Id":"4be2507e-40df-4ff9-980d-986911980e8a",
#                         "JobLocationId":6005,
#                         "JobLevel":12,
#                         "Sequence":0,
#                         "JobType":4,"Duration":3600,
#                         "ConditionMultiplier":1,
#                         "RewardMultiplier":1,
#                         "RequiredArticle":{"Id":6007,"Amount":220},
#                         "CurrentArticleAmount":0,
#                         "Reward":{
#                             "Items":[
#                                 {"Id":8,"Value":6000,"Amount":41},{"Id":8,"Value":33,"Amount":41},{"Id":8,"Value":1,"Amount":1052}
#                             ]
#                         },
#                         "Bonus":{"Reward":{"Items":[]}},
#                         "Requirements":[
#                             {"Type":"region","Value":4},{"Type":"rarity","Value":3}
#                         ],
#                         "UnlocksAt":"2023-01-10T12:00:00Z",
#                         "ExpiresAt":"2023-02-01T12:00:00Z"
#                     }
#                 },
#                 "Id":"4a70215c-2a7c-4ab6-b27b-514094a5ec22"
#             },
#             {
#                 "Command":"Region:Quest:Change",
#                 "Data":{
#                     "Quest":{"JobLocationId":6005,"Milestone":1,"Progress":11}
#                 },
#                 "Id":"a8e12cd4-39e7-4fb0-b770-0c5ccc156b12"
#             },
#             {"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"complete_job","Level":5,"Progress":2643}}},
#             {"Command":"PlayerCompany:Stats:Change","Data":{"Stats":{"Type":"complete_job","Progress":7929}}},
#             {"Command":"PlayerCompany:ChangeValue","Data":{"Value":175387}}
#         ]
#     }
# }
#     """
#     COMMAND = 'Job:Collect'
#     job: PlayerJob
#
#     def __init__(self, *, job: PlayerJob, **kwargs):
#         super(CollectJobReward, self).__init__(**kwargs)
#         self.job = job
#
#     def get_parameters(self) -> dict:
#         """
#
#         :return:
#         """
#         return {
#             'JobLocationId': self.job.job_location_id,
#         }
#
#     def post_processing(self):
#         self.helper.remove_job(self.job)
#
#
# class CollectWhistle(BaseCommand):
#     """
# {'buffer': 'POST /api/v2/command-processing/run-collection HTTP/1.1\r\nPXFD-Request-Id: 06ec734c-466b-4c2b-a1c1-37352444b819\r\nPXFD-Retry-No: 0\r\nPXFD-Sent-At: 2023-01-12T02:14:44.124Z\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json\r\nContent-Length: 175\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}
#
# {'buffer': '{"Id":10,"Time":"2023-01-12T02:14:44Z","Commands":[{"Command":"Whistle:Collect","Time":"2023-01-12T02:14:43Z","Parameters":{"Category":1,"Position":1}}],"Transactional":false}'}
#
# {"Success":true,"RequestId":"06ec734c-466b-4c2b-a1c1-37352444b819","Time":"2023-01-12T02:14:44Z","Data":{"CollectionId":10,"Commands":[{"Command":"Whistle:Spawn","Data":{"Whistle":{"Category":1,"Position":1,"SpawnTime":"2023-01-12T02:20:43Z","CollectableFrom":"2023-01-12T02:20:43Z","Reward":{"Items":[{"Id":8,"Value":103,"Amount":4}]},"IsForVideoReward":false}}},{"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"whistle_tap","Level":5,"Progress":16413}}}]}}
#     """
#
#     COMMAND = 'Whistle:Collect'
#     whistle: PlayerWhistle
#     # {"Command":"Whistle:Collect","Time":"2023-01-16T03:10:39Z","Parameters":{"Category":1,"Position":3}}
#
#     def __init__(self, *, whistle: PlayerWhistle, **kwargs):
#         super(CollectWhistle, self).__init__(**kwargs)
#         self.whistle = whistle
#
#     def get_parameters(self) -> dict:
#         """
#         :return:
#         """
#         return {
#             "Category": self.whistle.category,
#             "Position": self.whistle.position,
#         }
#
#     def post_processing(self):
#         self.helper.remove_whistle(self.whistle)
#
#
# class TrainSendToDestinationCommand(BaseCommand):
#     """
#     기차 보내기
#     {
#         "Id":2,
#         "Time":"2023-01-13T03:19:45Z",
#         "Commands":[
#             {
#                 "Command":"Train:DispatchToDestination",
#                 "Time":"2023-01-13T03:19:43Z",
#                 "Parameters":{
#                     "TrainId":9,   (PlayerTrain.instance_id)
#                     "DestinationId":150
#                 }
#             }
#         ],
#         "Transactional":false
#     }
#
#     -  Region #1
#         -  #  9 Lv.41/41 STEAM      legendary  Old_Crampton
#         -  # 27 Lv.41/41 STEAM      legendary  LNER_A4_Mallard
#         -  # 10 Lv.34/34 STEAM      epic       Shay_Class_C
#         -  # 26 Lv.34/34 STEAM      epic       GWR_3041_The_Queen
#
#     - Destination Table
#         to get article_id=101,
#             send to destination_id 150
#             requirements : region 1
#
#         +-----+--------------------------+--------------------------+-----------------------------------------+----+---------------+----------+------------+-----------+--------+--------------------------+----------+-----------+---------+
#         |id   |created                   |modified                  |sprite                                   |time|travel_duration|multiplier|refresh_time|train_limit|capacity|requirements              |article_id|location_id|region_id|
#         +-----+--------------------------+--------------------------+-----------------------------------------+----+---------------+----------+------------+-----------+--------+--------------------------+----------+-----------+---------+
#         |150  |2023-01-13 03:23:44.955526|2023-01-13 03:23:44.955526|destination_coal_mine                    |30  |30             |1         |0           |-1         |-1      |region;1                  |101       |150        |101      |
#         |151  |2023-01-13 03:23:44.955526|2023-01-13 03:23:44.955526|destination_iron_ore_mine                |30  |30             |1         |0           |-1         |-1      |region;1                  |100       |151        |101      |
#         |152  |2023-01-13 03:23:44.955526|2023-01-13 03:23:44.955526|destination_london                       |60  |60             |3         |14400       |1          |-1      |region;1                  |3         |152        |101      |
#         |153  |2023-01-13 03:23:44.955526|2023-01-13 03:23:44.955526|destination_steel                        |180 |180            |1         |0           |-1         |-1      |rarity;3|rarity;4|region;1|104       |153        |101      |
#
#     """
#     train: PlayerTrain
#     dest: Destination
#
#     COMMAND = 'Train:DispatchToDestination'
#     SLEEP_RANGE = (1.5, 2)
#
#     def __init__(self, *, train: PlayerTrain, dest: Destination, **kwargs):
#         super(TrainSendToDestinationCommand, self).__init__(**kwargs)
#         self.train = train
#         self.dest = dest
#
#     def get_parameters(self) -> dict:
#         """
#
#         :return:
#         """
#         return {
#             'TrainId': self.train.instance_id,
#             'DestinationId': self.dest.id,
#         }
#
#     def duration(self) -> int:
#         return self.dest.time
#
#     def post_processing(self):
#         self.train.has_route = True
#         self.train.route_type = 'destination'
#         self.train.route_definition_id = self.dest.id
#         self.train.route_departure_time = self.end_datetime()
#         self.train.route_arrival_time = self.end_datetime()
#
#
# class CollectProductFromFactoryCommand(BaseCommand):
#     """
#         {
#             "Id":10,
#             "Time":"2023-01-07T05:20:06Z",
#             "Commands":[
#                 {
#                     "Command":"Factory:CollectProduct",
#                     "Time":"2023-01-07T05:20:04Z",
#                     "Parameters":{
#                         "FactoryId":5,"Index":3
#                     }
#                 },
#                 {
#                     "Command":"Factory:CollectProduct",
#                     "Time":"2023-01-07T05:20:05Z",
#                     "Parameters":{
#                         "FactoryId":5,
#                         "Index":2
#                     }
#                 }
#             ],
#             "Transactional":false
#         }
#     """
#
#
# class OrderProductFromFactoryCommand(BaseCommand):
#     """
#         {
#             "Id":9,
#             "Time":"2023-01-07T05:20:03Z",
#             "Commands":[
#                 {
#                     "Command":"Factory:OrderProduct",
#                     "Time":"2023-01-07T05:20:01Z",
#                     "Parameters":{
#                         "FactoryId":5,
#                         "ArticleId":115
#                     }
#                 },
#                 {
#                     "Command":"Factory:OrderProduct",
#                     "Time":"2023-01-07T05:20:02Z",
#                     "Parameters":{
#                         "FactoryId":5,"ArticleId":115
#                     }
#                 }
#             ],
#             "Transactional":false
#         }
#     """
#
#
# class TrainUpgradeCommand(BaseCommand):
#     """
# 16 01:14:17 | T: 7907 | I | SSL_AsyncWrite  | POST /api/v2/command-processing/run-collection HTTP/1.1
# PXFD-Request-Id: d9d4fa2f-5b8e-4ddf-a94b-52c4f26b116c
# PXFD-Retry-No: 0
# PXFD-Sent-At: 2023-01-15T16:14:17.278Z
# PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}
# PXFD-Client-Version: 2.6.3.4068
# PXFD-Device-Token: 30b270ca64e80bbbf4b186f251ba358a
# PXFD-Game-Access-Token: b57a9952-1ca7-5c50-a5df-5b5e7fb0ae48
# PXFD-Player-Id: 62794770
# Content-Type: application/json
# Content-Length: 159
# Host: game.trainstation2.com
# Accept-Encoding: gzip, deflate
#
#
# 16 01:14:17 | T: 7907 | I | SSL_AsyncWrite  | {"Id":11,"Time":"2023-01-15T16:14:17Z","Commands":[{"Command":"Train:Upgrade","Time":"2023-01-15T16:14:16Z","Parameters":{"TrainId":3}}],"Transactional":false}
# 16 01:14:18 | T: 7908 | I | IO.Mem.Write    | {"Success":true,"RequestId":"d9d4fa2f-5b8e-4ddf-a94b-52c4f26b116c","Time":"2023-01-15T16:14:17Z","Data":{"CollectionId":11,"Commands":[{"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"upgrade_train","Level":0,"Progress":1}}}]}}
#
#
#     """
#
#
# class GameHeatbeat(BaseCommand):
#     """
#     16 12:08:42 | T: 3717 | I | SSL_AsyncWrite  | {"Id":6,"Time":"2023-01-16T03:08:43Z","Commands":[{"Command":"Game:Heartbeat","Time":"2023-01-16T03:08:41Z","Parameters":{}}],"Transactional":false}
#
#     """
#     COMMAND = 'Game:Heartbeat'
#     SLEEP_RANGE = (0.5, 1)
#
#     def __init__(self, **kwargs):
#         super(GameHeatbeat, self).__init__(**kwargs)
#
#     def get_parameters(self) -> dict:
#         """
#
#         :return:
#         """
#         return {}
