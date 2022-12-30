import uuid
from hashlib import md5
from pathlib import Path
from typing import Union, Optional, List, Dict

from django.conf import settings
from django.utils import timezone

from app_root.bot.models import Definition, Article, Factory, Product, Train, Destination, Region, Location
from app_root.bot.utils_request import CrawlingHelper
from app_root.bot.utils_server_time import ServerTimeHelper
from core.utils import disk_cache, Logger, download_file

import json

from app_root.bot.utils_abstract import BaseBotHelper
from app_root.users.models import User

import sqlite3


LOGGING_MENU = 'utils.login'


@disk_cache(prefix='get_definition', smt='{android_id}_{sent_at}.json')
def get_definition(*, url: str, android_id, sent_at: str, game_access_token: str, player_id: str):
    """
    Header
        01dbf010  47 45 54 20 2f 61 70 69 2f 76 32 2f 67 65 74 2d  GET /api/v2/get-
        01dbf020  64 65 66 69 6e 69 74 69 6f 6e 20 48 54 54 50 2f  definition HTTP/
        01dbf030  31 2e 31 0d 0a 50 58 46 44 2d 52 65 71 75 65 73  1.1..PXFD-Reques
        01dbf040  74 2d 49 64 3a 20 31 33 63 61 64 33 63 63 2d 33  t-Id: 13cad3cc-3
        01dbf050  61 33 64 2d 34 34 37 63 2d 62 63 34 30 2d 32 61  a3d-447c-bc40-2a
        01dbf060  32 35 64 64 39 61 39 36 34 33 0d 0a 50 58 46 44  25dd9a9643..PXFD
        01dbf070  2d 52 65 74 72 79 2d 4e 6f 3a 20 30 0d 0a 50 58  -Retry-No: 0..PX
        01dbf080  46 44 2d 53 65 6e 74 2d 41 74 3a 20 32 30 32 32  FD-Sent-At: 2022
        01dbf090  2d 31 32 2d 32 39 54 30 39 3a 31 31 3a 35 35 2e  -12-29T09:11:55.
        01dbf0a0  30 30 30 5a 0d 0a 50 58 46 44 2d 43 6c 69 65 6e  000Z..PXFD-Clien
        01dbf0b0  74 2d 49 6e 66 6f 72 6d 61 74 69 6f 6e 3a 20 7b  t-Information: {
        01dbf0c0  22 53 74 6f 72 65 22 3a 22 67 6f 6f 67 6c 65 5f  "Store":"google_
        01dbf0d0  70 6c 61 79 22 2c 22 56 65 72 73 69 6f 6e 22 3a  play","Version":
        01dbf0e0  22 32 2e 36 2e 32 2e 34 30 32 33 22 2c 22 4c 61  "2.6.2.4023","La
        01dbf0f0  6e 67 75 61 67 65 22 3a 22 65 6e 22 7d 0d 0a 50  nguage":"en"}..P
        01dbf100  58 46 44 2d 43 6c 69 65 6e 74 2d 56 65 72 73 69  XFD-Client-Versi
        01dbf110  6f 6e 3a 20 32 2e 36 2e 32 2e 34 30 32 33 0d 0a  on: 2.6.2.4023..
        01dbf120  50 58 46 44 2d 44 65 76 69 63 65 2d 54 6f 6b 65  PXFD-Device-Toke
        01dbf130  6e 3a 20 33 30 62 32 37 30 63 61 36 34 65 38 30  n: 30b270ca64e80
        01dbf140  62 62 62 66 34 62 31 38 36 66 32 35 31 62 61 33  bbbf4b186f251ba3
        01dbf150  35 38 61 0d 0a 50 58 46 44 2d 47 61 6d 65 2d 41  58a..PXFD-Game-A
        01dbf160  63 63 65 73 73 2d 54 6f 6b 65 6e 3a 20 30 33 63  ccess-Token: 03c
        01dbf170  61 31 30 64 33 2d 35 39 32 62 2d 35 32 65 66 2d  a10d3-592b-52ef-
        01dbf180  61 63 64 63 2d 39 36 64 33 31 36 34 63 38 61 30  acdc-96d3164c8a0
        01dbf190  62 0d 0a 50 58 46 44 2d 50 6c 61 79 65 72 2d 49  b..PXFD-Player-I
        01dbf1a0  64 3a 20 36 32 37 39 34 37 37 30 0d 0a 48 6f 73  d: 62794770..Hos
        01dbf1b0  74 3a 20 67 61 6d 65 2e 74 72 61 69 6e 73 74 61  t: game.trainsta
        01dbf1c0  74 69 6f 6e 32 2e 63 6f 6d 0d 0a 41 63 63 65 70  tion2.com..Accep
        01dbf1d0  74 2d 45 6e 63 6f 64 69 6e 67 3a 20 67 7a 69 70  t-Encoding: gzip
        01dbf1e0  2c 20 64 65 66 6c 61 74 65 0d 0a 0d 0a           , deflate....
    Resp
                   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F  0123456789ABCDEF
        020a5010  7b 22 53 75 63 63 65 73 73 22 3a 74 72 75 65 2c  {"Success":true,
        020a5020  22 52 65 71 75 65 73 74 49 64 22 3a 22 31 33 63  "RequestId":"13c
        020a5030  61 64 33 63 63 2d 33 61 33 64 2d 34 34 37 63 2d  ad3cc-3a3d-447c-
        020a5040  62 63 34 30 2d 32 61 32 35 64 64 39 61 39 36 34  bc40-2a25dd9a964
        020a5050  33 22 2c 22 54 69 6d 65 22 3a 22 32 30 32 32 2d  3","Time":"2022-
        020a5060  31 32 2d 32 39 54 30 39 3a 31 32 3a 30 30 5a 22  12-29T09:12:00Z"
        020a5070  2c 22 44 61 74 61 22 3a 7b 22 56 65 72 73 69 6f  ,"Data":{"Versio
        020a5080  6e 22 3a 22 32 30 36 2e 30 30 39 22 2c 22 43 68  n":"206.009","Ch
        020a5090  65 63 6b 73 75 6d 22 3a 22 32 34 30 37 38 36 30  ecksum":"2407860
        020a50a0  65 63 65 31 61 66 37 62 62 32 66 64 30 38 63 65  ece1af7bb2fd08ce
        020a50b0  65 32 36 66 33 65 38 30 32 31 30 31 30 39 37 61  e26f3e802101097a
        020a50c0  32 22 2c 22 55 72 6c 22 3a 22 68 74 74 70 73 3a  2","Url":"https:
        020a50d0  2f 2f 63 64 6e 2e 74 72 61 69 6e 73 74 61 74 69  //cdn.trainstati
        020a50e0  6f 6e 32 2e 63 6f 6d 2f 63 6c 69 65 6e 74 2d 72  on2.com/client-r
        020a50f0  65 73 6f 75 72 63 65 73 2f 63 6c 69 65 6e 74 2d  esources/client-
        020a5100  64 61 74 61 2d 32 30 36 2e 30 30 39 2e 73 71 6c  data-206.009.sql
        020a5110  69 74 65 22 7d 7d 00 00 00 00 00 00 00 00 00 00  ite"}}..........
        020a5120  00 00 00 00 00 00                                ......
    :param url:
    :param android_id:
    :param sent_at:
    :param game_access_token:
    :param player_id:
    :return:
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
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_LANGUAGE),
        'PXFD-Device-Token': device_id,
        'PXFD-Game-Access-Token': game_access_token,
        'PXFD-Player-Id': player_id,
        'Accept-Encoding': 'gzip, deflate',
    }
    Logger.info(menu=LOGGING_MENU, action='get_definition', msg='before request', url=url, headers=headers)
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
        menu=LOGGING_MENU, action='get_definition', msg='after request',
        status_code=str(resp_status_code),
        body=str(resp_body),
        headers=str(resp_headers),
        cookies=str(resp_cookies),
    )
    return resp_body


class DefinitionHelper(BaseBotHelper):
    instance: Optional[Definition]
    BASE_PATH = settings.SITE_PATH / 'download' / 'definition'

    def __init__(self):
        self.instance = None
        self.articles = {}
        self.factories = {}
        self.trains = {}

    def download_data(self):
        if self.instance:
            download_filename = Path(self.instance.download_path)

            if self.instance.url and not download_filename.exists():
                download_file(url=self.instance.url, download_filename=download_filename)

            return download_filename.lstat().st_size

    def get_data(self, url) -> str:
        """

        :param url:
        :param server_time:
        :param user:
        :return:
        """
        return get_definition(
            url=url,
            android_id=self.user.android_id,
            sent_at=self.server_time.get_curr_time(),
            game_access_token=self.user.game_access_token,
            player_id=self.user.player_id,
        )

    def parse_data(self, data) -> str:
        """

        :param user:
        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)

        success = json_data.get('Success')
        assert success

        server_time = json_data.get('Time')
        server_data = json_data.get('Data', {})

        if server_data:
            """
                'Version' = {str} '206.009'
                'Checksum' = {str} '2407860ece1af7bb2fd08cee26f3e802101097a2'
                'Url' = {str} 'https://cdn.trainstation2.com/client-resources/client-data-206.009.sqlite'            
            """
            version = server_data.get('Version', '')
            checksum = server_data.get('Checksum', '')
            url = server_data.get('Url', '')

            if version and checksum and url:
                self.instance = Definition.objects.order_by('-pk').first()

                # try:
                if not self.instance or self.instance.version != version:
                    self.instance = Definition.objects.create(
                        version=version,
                        checksum=checksum,
                        url=url,
                        download_path=self.BASE_PATH / f'{version}.sqlite'
                    )

                    if self.download_data():
                        self.read_sqlite()

                # except Exception as e:
                #     if self.instance:
                #         self.instance.delete()
                #     raise e

        return server_time

    def _read_sqlite(self, model, remote_table_name, mapping, cur):
        model.objects.all().delete()

        bulk_list = []
        now = timezone.now()

        local_fields = list(mapping.keys())
        remote_fields_in_order = ','.join([
            mapping[f] for f in local_fields
        ])
        sql = f'SELECT {remote_fields_in_order} FROM {remote_table_name}'

        for row in cur.execute(sql):
            param = {
                local_fields[i]: row[i] for i in range(len(local_fields))
            }
            obj = model(**param, created=now, modified=now)
            bulk_list.append(obj)

        if bulk_list:
            model.objects.bulk_create(bulk_list, 100)

    def _read_article(self, cur):
        model = Article
        remote_table_name = 'article'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'level_req': 'level_req',
            'level_from': 'level_from',
            'type': 'type_id',
            'event': 'event_id',
            'content_category': 'content_category',
            'sprite': 'sprite_id',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_factory(self, cur):

        model = Factory
        remote_table_name = 'factory'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'level_req': 'level_req',
            'level_from': 'level_from',
            'starting_slot_count': 'starting_slot_count',
            'max_slot_count': 'max_slot_count',
            'type': 'type_id',
            'content_category': 'content_category',
            'asset_name': 'asset_name',
            'sprite': 'sprite_id',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_product(self, cur):
        model = Product
        remote_table_name = 'product'
        mapping = {  # local DB field : remote db field
            'factory_id': 'factory_id',
            'article_id': 'article_id',  # replace article id to id
            'article_amount': 'article_amount',
            'craft_time': 'craft_time',
            'article_ids': 'article_ids',
            'article_amounts': 'article_amounts',
            'level_req': 'level_req',
            'level_from': 'level_from',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_train(self, cur):
        model = Train
        remote_table_name = 'train'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'content_category': 'content_category',
            'reward': 'reward',
            'region': 'region',
            'rarity': 'rarity_id',
            'max_level': 'max_level',
            'era': 'era_id',
            'asset_name': 'asset_name',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_region(self, cur):
        model = Region
        remote_table_name = 'region'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'level_from': 'level_from',
            'content_category': 'content_category',
            'asset_name': 'asset_name',
            'gold_amount_coefficient': 'gold_amount_coefficient',
            'train_upgrade_price_coefficient': 'train_upgrade_price_coefficient',
            'city_currency_coefficient': 'city_currency_coefficient',
            'ordering': 'ordering',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_location(self, cur):
        model = Location
        remote_table_name = 'location'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'region': 'region',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_destination(self, cur):
        model = Destination
        remote_table_name = 'destination'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'location_id': 'location_id',
            'article_id': 'article_id',
            'region_id': 'region_id',
            'sprite': 'sprite_id',
            'time': 'time',
            'travel_duration': 'travel_duration',
            'multiplier': 'multiplier',
            'refresh_time': 'refresh_time',
            'train_limit': 'train_limit',
            'capacity': 'capacity',
            'requirements': 'requirements',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def read_sqlite(self):
        if self.instance:
            con = sqlite3.connect(self.instance.download_path)
            cur = con.cursor()
            self._read_article(cur=cur)
            self._read_factory(cur=cur)
            self._read_product(cur=cur)
            self._read_train(cur=cur)
            self._read_region(cur=cur)
            self._read_location(cur=cur)
            self._read_destination(cur=cur)
            con.close()
