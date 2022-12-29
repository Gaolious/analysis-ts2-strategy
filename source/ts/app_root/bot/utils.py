import json
from datetime import timedelta
from functools import cached_property

import pytz
from django.utils import timezone
from dateutil import parser

from app_root.bot.helper import get_endpoints, login_with_device_id, login_with_remember_token, get_init_data, \
    get_definition

from app_root.bot.utils_definition import Definition
from app_root.bot.utils_endpoints import EndPoints
from app_root.bot.utils_init_data import InitData
from app_root.bot.utils_login import Login
from app_root.bot.utils_server_time import ServerTime
from app_root.users.models import User


LOGGING_MENU = 'bot.utils'


class Bot():
    user_id: int

    server_time: ServerTime
    endpoints: EndPoints
    login: Login
    definition: Definition
    init_data: InitData

    def __init__(self, user_id):
        self.user_id = user_id
        self.server_time = ServerTime()
        self.endpoints = EndPoints()
        self.login = Login()
        self.definition = Definition()
        self.init_data = InitData()

    @cached_property
    def user(self):
        """
        get user instance
        :return: users.User
        """
        return User.objects.filter(id=self.user_id).first()

    ###########################################################################
    # Step 1. Get Endpoints.
    ###########################################################################
    def run_endpoints(self):
        url = 'https://game.trainstation2.com/get-endpoints'
        self.endpoints.run(url=url, user=self.user, server_time=self.server_time)

    ###########################################################################
    # Step 2. Login
    ###########################################################################
    def run_login(self):
        url = self.endpoints.get_login_url()
        self.login.run(url=url, user=self.user, server_time=self.server_time)

    ###########################################################################
    # Step 3. Definition
    ###########################################################################
    def run_definition(self):
        url = self.endpoints.get_definition_url()
        self.definition.run(url=url, user=self.user, server_time=self.server_time)

    # Step 3. load Init Data
    def run_init_data(self):
        urls = self.endpoints.get_init_urls()
        for url in urls:
            self.init_data.run(url=url, user=self.user, server_time=self.server_time)



    """
Definition.


  
29 18:12:00 | T: 5998 | P | IO.Mem.Write    | buffer

https://cdn.trainstation2.com/client-resources/client-data-206.009.sqlite                                                  
    """

"""
기차보내기
21시 6분에 보내기 시작함. (london (30개중에 15개 보내진것. 에픽 1개 - 12개 1번, 레어 1개 - 3개 1번 ))

                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              04a037e0  60 3e c5 88 00 00 00 00 00 00 00 00 26 02 00 00  `>..........&...
                                              04a037f0  50 4f 53 54 20 2f 61 70 69 2f 76 32 2f 63 6f 6d  POST /api/v2/com
                                              04a03800  6d 61 6e 64 2d 70 72 6f 63 65 73 73 69 6e 67 2f  mand-processing/
                                              04a03810  72 75 6e 2d 63 6f 6c 6c 65 63 74 69 6f 6e 20 48  run-collection H
                                              04a03820  54 54 50 2f 31 2e 31 0d 0a 50 58 46 44 2d 52 65  TTP/1.1..PXFD-Re
                                              04a03830  71 75 65 73 74 2d 49 64 3a 20 31 64 66 65 30 31  quest-Id: 1dfe01
                                              04a03840  37 63 2d 32 64 30 35 2d 34 39 38 33 2d 61 66 61  7c-2d05-4983-afa
                                              04a03850  37 2d 37 65 65 61 34 31 36 30 33 31 65 62 0d 0a  7-7eea416031eb..
                                              04a03860  50 58 46 44 2d 52 65 74 72 79 2d 4e 6f 3a 20 30  PXFD-Retry-No: 0
                                              04a03870  0d 0a 50 58 46 44 2d 53 65 6e 74 2d 41 74 3a 20  ..PXFD-Sent-At: 
                                              04a03880  32 30 32 32 2d 31 32 2d 32 39 54 31 32 3a 30 37  2022-12-29T12:07
                                              04a03890  3a 33 36 2e 31 34 32 5a 0d 0a 50 58 46 44 2d 43  :36.142Z..PXFD-C
                                              04a038a0  6c 69 65 6e 74 2d 49 6e 66 6f 72 6d 61 74 69 6f  lient-Informatio
                                              04a038b0  6e 3a 20 7b 22 53 74 6f 72 65 22 3a 22 67 6f 6f  n: {"Store":"goo
                                              04a038c0  67 6c 65 5f 70 6c 61 79 22 2c 22 56 65 72 73 69  gle_play","Versi
                                              04a038d0  6f 6e 22 3a 22 32 2e 36 2e 32 2e 34 30 32 33 22  on":"2.6.2.4023"
                                              04a038e0  2c 22 4c 61 6e 67 75 61 67 65 22 3a 22 65 6e 22  ,"Language":"en"
                                              04a038f0  7d 0d 0a 50 58 46 44 2d 43 6c 69 65 6e 74 2d 56  }..PXFD-Client-V
                                              04a03900  65 72 73 69 6f 6e 3a 20 32 2e 36 2e 32 2e 34 30  ersion: 2.6.2.40
                                              04a03910  32 33 0d 0a 50 58 46 44 2d 44 65 76 69 63 65 2d  23..PXFD-Device-
                                              04a03920  54 6f 6b 65 6e 3a 20 33 30 62 32 37 30 63 61 36  Token: 30b270ca6
                                              04a03930  34 65 38 30 62 62 62 66 34 62 31 38 36 66 32 35  4e80bbbf4b186f25
                                              04a03940  31 62 61 33 35 38 61 0d 0a 50 58 46 44 2d 47 61  1ba358a..PXFD-Ga
                                              04a03950  6d 65 2d 41 63 63 65 73 73 2d 54 6f 6b 65 6e 3a  me-Access-Token:
                                              04a03960  20 39 32 36 31 39 38 32 34 2d 34 35 61 62 2d 35   92619824-45ab-5
                                              04a03970  38 66 66 2d 39 37 38 32 2d 62 65 64 32 39 61 65  8ff-9782-bed29ae
                                              04a03980  64 35 33 36 66 0d 0a 50 58 46 44 2d 50 6c 61 79  d536f..PXFD-Play
                                              04a03990  65 72 2d 49 64 3a 20 36 32 37 39 34 37 37 30 0d  er-Id: 62794770.
                                              04a039a0  0a 43 6f 6e 74 65 6e 74 2d 54 79 70 65 3a 20 61  .Content-Type: a
                                              04a039b0  70 70 6c 69 63 61 74 69 6f 6e 2f 6a 73 6f 6e 0d  pplication/json.
                                              04a039c0  0a 43 6f 6e 74 65 6e 74 2d 4c 65 6e 67 74 68 3a  .Content-Length:
                                              04a039d0  20 32 36 34 0d 0a 48 6f 73 74 3a 20 67 61 6d 65   264..Host: game
                                              04a039e0  2e 74 72 61 69 6e 73 74 61 74 69 6f 6e 32 2e 63  .trainstation2.c
                                              04a039f0  6f 6d 0d 0a 41 63 63 65 70 74 2d 45 6e 63 6f 64  om..Accept-Encod
                                              04a03a00  69 6e 67 3a 20 67 7a 69 70 2c 20 64 65 66 6c 61  ing: gzip, defla
                                              04a03a10  74 65 0d 0a 0d 0a                                te....

                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              02ed3010  7b 22 49 64 22 3a 34 2c 22 54 69 6d 65 22 3a 22  {"Id":4,"Time":"
                                              02ed3020  32 30 32 32 2d 31 32 2d 32 39 54 31 32 3a 30 37  2022-12-29T12:07
                                              02ed3030  3a 33 36 5a 22 2c 22 43 6f 6d 6d 61 6e 64 73 22  :36Z","Commands"
                                              02ed3040  3a 5b 7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 54 72  :[{"Command":"Tr
                                              02ed3050  61 69 6e 3a 44 69 73 70 61 74 63 68 54 6f 4a 6f  ain:DispatchToJo
                                              02ed3060  62 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 32 2d  b","Time":"2022-
                                              02ed3070  31 32 2d 32 39 54 31 32 3a 30 37 3a 33 34 5a 22  12-29T12:07:34Z"
                                              02ed3080  2c 22 50 61 72 61 6d 65 74 65 72 73 22 3a 7b 22  ,"Parameters":{"
                                              02ed3090  55 6e 69 71 75 65 49 64 22 3a 22 33 62 34 35 38  UniqueId":"3b458
                                              02ed30a0  31 63 34 2d 62 35 31 66 2d 34 34 35 62 2d 39 61  1c4-b51f-445b-9a
                                              02ed30b0  35 37 2d 30 37 66 33 63 36 63 30 66 35 39 31 22  57-07f3c6c0f591"
                                              02ed30c0  2c 22 54 72 61 69 6e 49 64 22 3a 32 2c 22 4a 6f  ,"TrainId":2,"Jo
                                              02ed30d0  62 4c 6f 63 61 74 69 6f 6e 49 64 22 3a 31 35 32  bLocationId":152
                                              02ed30e0  2c 22 4c 6f 61 64 22 3a 7b 22 49 64 22 3a 31 30  ,"Load":{"Id":10
                                              02ed30f0  30 2c 22 41 6d 6f 75 6e 74 22 3a 31 32 7d 7d 7d  0,"Amount":12}}}
                                              02ed3100  5d 2c 22 54 72 61 6e 73 61 63 74 69 6f 6e 61 6c  ],"Transactional
                                              02ed3110  22 3a 66 61 6c 73 65 7d 00 00 00 00 00 00 00 00  ":false}........
                                              02ed3120  00 00 00 00 00 00 00 00                          ........

9 21:07:39 | T: 8408 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              021d5010  7b 22 49 64 22 3a 35 2c 22 54 69 6d 65 22 3a 22  {"Id":5,"Time":"
                                              021d5020  32 30 32 32 2d 31 32 2d 32 39 54 31 32 3a 30 37  2022-12-29T12:07
                                              021d5030  3a 33 39 5a 22 2c 22 43 6f 6d 6d 61 6e 64 73 22  :39Z","Commands"
                                              021d5040  3a 5b 7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 54 72  :[{"Command":"Tr
                                              021d5050  61 69 6e 3a 44 69 73 70 61 74 63 68 54 6f 4a 6f  ain:DispatchToJo
                                              021d5060  62 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 32 2d  b","Time":"2022-
                                              021d5070  31 32 2d 32 39 54 31 32 3a 30 37 3a 33 38 5a 22  12-29T12:07:38Z"
                                              021d5080  2c 22 50 61 72 61 6d 65 74 65 72 73 22 3a 7b 22  ,"Parameters":{"
                                              021d5090  55 6e 69 71 75 65 49 64 22 3a 22 33 62 34 35 38  UniqueId":"3b458
                                              021d50a0  31 63 34 2d 62 35 31 66 2d 34 34 35 62 2d 39 61  1c4-b51f-445b-9a
                                              021d50b0  35 37 2d 30 37 66 33 63 36 63 30 66 35 39 31 22  57-07f3c6c0f591"
                                              021d50c0  2c 22 54 72 61 69 6e 49 64 22 3a 33 2c 22 4a 6f  ,"TrainId":3,"Jo
                                              021d50d0  62 4c 6f 63 61 74 69 6f 6e 49 64 22 3a 31 35 32  bLocationId":152
                                              021d50e0  2c 22 4c 6f 61 64 22 3a 7b 22 49 64 22 3a 31 30  ,"Load":{"Id":10
                                              021d50f0  30 2c 22 41 6d 6f 75 6e 74 22 3a 33 7d 7d 7d 5d  0,"Amount":3}}}]
                                              021d5100  2c 22 54 72 61 6e 73 61 63 74 69 6f 6e 61 6c 22  ,"Transactional"
                                              021d5110  3a 66 61 6c 73 65 7d 00 00 00 00 00 00 00 00 00  :false}.........
                                              021d5120  00 00 00 00 00 00 00                             .......
                                              
run-collection #1
29 21:04:32 | T: 8246 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              02b1b010  7b 22 49 64 22 3a 31 2c 22 54 69 6d 65 22 3a 22  {"Id":1,"Time":"
                                              02b1b020  32 30 32 32 2d 31 32 2d 32 39 54 31 32 3a 30 34  2022-12-29T12:04
                                              02b1b030  3a 33 31 5a 22 2c 22 43 6f 6d 6d 61 6e 64 73 22  :31Z","Commands"
                                              02b1b040  3a 5b 7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 47 61  :[{"Command":"Ga
                                              02b1b050  6d 65 3a 48 65 61 72 74 62 65 61 74 22 2c 22 54  me:Heartbeat","T
                                              02b1b060  69 6d 65 22 3a 22 32 30 32 32 2d 31 32 2d 32 39  ime":"2022-12-29
                                              02b1b070  54 31 32 3a 30 34 3a 33 31 5a 22 2c 22 50 61 72  T12:04:31Z","Par
                                              02b1b080  61 6d 65 74 65 72 73 22 3a 7b 7d 7d 5d 2c 22 54  ameters":{}}],"T
                                              02b1b090  72 61 6e 73 61 63 74 69 6f 6e 61 6c 22 3a 66 61  ransactional":fa
                                              02b1b0a0  6c 73 65 7d 00 00 00 00 00 00 00 00 00 00 00 00  lse}............
                                              02b1b0b0  00 00 00 00  
29 21:05:40 | T: 8245 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              036a8010  7b 22 49 64 22 3a 32 2c 22 54 69 6d 65 22 3a 22  {"Id":2,"Time":"
                                              036a8020  32 30 32 32 2d 31 32 2d 32 39 54 31 32 3a 30 35  2022-12-29T12:05
                                              036a8030  3a 33 36 5a 22 2c 22 43 6f 6d 6d 61 6e 64 73 22  :36Z","Commands"
                                              036a8040  3a 5b 7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 47 61  :[{"Command":"Ga
                                              036a8050  6d 65 3a 48 65 61 72 74 62 65 61 74 22 2c 22 54  me:Heartbeat","T
                                              036a8060  69 6d 65 22 3a 22 32 30 32 32 2d 31 32 2d 32 39  ime":"2022-12-29
                                              036a8070  54 31 32 3a 30 35 3a 33 34 5a 22 2c 22 50 61 72  T12:05:34Z","Par
                                              036a8080  61 6d 65 74 65 72 73 22 3a 7b 7d 7d 5d 2c 22 54  ameters":{}}],"T
                                              036a8090  72 61 6e 73 61 63 74 69 6f 6e 61 6c 22 3a 66 61  ransactional":fa
                                              036a80a0  6c 73 65 7d 00 00 00 00 00 00 00 00 00 00 00 00  lse}............
                                              036a80b0  00 00 00 00                                      ....
29 21:06:40 | T: 8367 | P | IO.Mem.Write    | buffer
                                                         0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
                                              04aee010  7b 22 49 64 22 3a 33 2c 22 54 69 6d 65 22 3a 22  {"Id":3,"Time":"
                                              04aee020  32 30 32 32 2d 31 32 2d 32 39 54 31 32 3a 30 36  2022-12-29T12:06
                                              04aee030  3a 34 30 5a 22 2c 22 43 6f 6d 6d 61 6e 64 73 22  :40Z","Commands"
                                              04aee040  3a 5b 7b 22 43 6f 6d 6d 61 6e 64 22 3a 22 47 61  :[{"Command":"Ga
                                              04aee050  6d 65 3a 48 65 61 72 74 62 65 61 74 22 2c 22 54  me:Heartbeat","T
                                              04aee060  69 6d 65 22 3a 22 32 30 32 32 2d 31 32 2d 32 39  ime":"2022-12-29
                                              04aee070  54 31 32 3a 30 36 3a 33 39 5a 22 2c 22 50 61 72  T12:06:39Z","Par
                                              04aee080  61 6d 65 74 65 72 73 22 3a 7b 7d 7d 5d 2c 22 54  ameters":{}}],"T
                                              04aee090  72 61 6e 73 61 63 74 69 6f 6e 61 6c 22 3a 66 61  ransactional":fa
                                              04aee0a0  6c 73 65 7d 00 00 00 00 00 00 00 00 00 00 00 00  lse}............
                                              04aee0b0  00 00 00 00                                      ....                                                                                            
"""