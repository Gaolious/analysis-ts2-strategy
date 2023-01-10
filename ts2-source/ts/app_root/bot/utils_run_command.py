
class BaseCommand(object):
    pass


class TrainCollectCommand(BaseCommand):
    """
        # 기차에서 수집.
        {
            "Id":2,
            "Time":"2023-01-07T05:18:22Z",
            "Commands":[
                {
                    "Command":"Train:Unload",
                    "Time":"2023-01-07T05:18:16Z",
                    "Parameters":{"TrainId":92}
                },
                {
                    "Command":"Train:Unload",
                    "Time":"2023-01-07T05:18:21Z",
                    "Parameters":{"TrainId":19}
                }
            ],
            "Transactional":false
        }
    """


class TrainSendCommand(BaseCommand):
    pass


class FactoryCollectItemCommand(BaseCommand):
    """
        {
            "Id":10,
            "Time":"2023-01-07T05:20:06Z",
            "Commands":[
                {
                    "Command":"Factory:CollectProduct",
                    "Time":"2023-01-07T05:20:04Z",
                    "Parameters":{
                        "FactoryId":5,"Index":3
                    }
                },
                {
                    "Command":"Factory:CollectProduct",
                    "Time":"2023-01-07T05:20:05Z",
                    "Parameters":{
                        "FactoryId":5,
                        "Index":2
                    }
                }
            ],
            "Transactional":false
        }
    """
    pass


class FactoryOrderItemCommand(BaseCommand):
    """
{
    "Id":9,
    "Time":"2023-01-07T05:20:03Z",
    "Commands":[
        {
            "Command":"Factory:OrderProduct",
            "Time":"2023-01-07T05:20:01Z",
            "Parameters":{
                "FactoryId":5,
                "ArticleId":115
            }
        },
        {
            "Command":"Factory:OrderProduct",
            "Time":"2023-01-07T05:20:02Z",
            "Parameters":{
                "FactoryId":5,"ArticleId":115
            }
        }
    ],
    "Transactional":false
}

    """
    pass


class GiftClaimCommand(BaseCommand):
    """
POST /api/v2/command-processing/run-collection HTTP/1.1
PXFD-Request-Id: fceb920f-c2e5-4179-b7b9-61ae49f75270
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-01-09T02:37:59.667Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.6.2.4023","Language":"en"}
PXFD-Client-Version: 2.6.2.4023
PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
PXFD-Game-Access-Token: 2af7f36d-1392-59f4-841b-5207bbc735ec
PXFD-Player-Id: 61561146
Content-Type: application/json
Content-Length: 187
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate

{
    "Id":2,
    "Time":"2023-01-09T02:37:59Z",
    "Commands":[
        {
            "Command":"Gift:Claim",
            "Time":"2023-01-09T02:37:59Z",
            "Parameters":{
                "Id":"8295a2de-d048-4228-ac02-e3d36c2d3b4a"
            }
        }
    ],
    "Transactional":false
}
    """


class CommandManager(object):
    run_version_id: int

    def __init__(self, run_version_id: int):
        self.run_version_id = run_version_id

    def run(self):
        # collect train
        # collect gift
        # if has destination
        #       send destination train
        # if has union quest and small materials < 300
        #
        #       change contracts
        # if has union quest
        #       send quest.
        pass

    pass

"""
    POST /api/v2/command-processing/run-collection HTTP/1.1
    PXFD-Request-Id: efd5b2eb-755a-4d2a-a703-cf16f7e59da5
    PXFD-Retry-No: 0
    PXFD-Sent-At: 2023-01-07T05:18:22.358Z
    PXFD-Client-Information: {"Store":"google_play","Version":"2.6.2.4023","Language":"en"}
    PXFD-Client-Version: 2.6.2.4023
    PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
    PXFD-Game-Access-Token: ec82453c-2f81-514f-921d-159df83a0437
    PXFD-Player-Id: 61561146
    Content-Type: application/json
    Content-Length: 243
    Host: game.trainstation2.com
    Accept-Encoding: gzip, deflate


###########################
# 골드 기차 보내기                               
###########################
{
    "Id":4,
    "Time":"2023-01-07T05:19:00Z",
    "Commands":[
        {
            "Command":"Train:DispatchToDestination",
            "Time":"2023-01-07T05:18:58Z",
            "Parameters":{
                "TrainId":9,
                "DestinationId":152
            }
        }
    ],
    "Transactional":false
}
# id:4 / destinationid : 152 
# id:5 / destinationid : 230
# id:6 / de stinationid : 304

계약서
{
    "Id":8,
    "Time":"2023-01-07T05:19:42Z",
    "Commands":[
        {
            "Command":"Contract:Activate",
            "Time":"2023-01-07T05:19:41Z",
            "Parameters":{
                "ContractListId":100001,
                "Slot":20
            }
        }
    ],
    "Transactional":false
}



"""