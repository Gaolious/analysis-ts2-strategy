import json
import sqlite3
from hashlib import md5
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from app_root.exceptions import check_response
from app_root.mixins import ImportHelperMixin
from app_root.servers.models import EndPoint, SQLDefinition, TSJobLocation, TSDestination, TSLocation, TSRegion, \
    TSTrainLevel, TSTrain, TSProduct, TSFactory, TSWarehouseLevel, TSUserLevel, TSArticle
from app_root.utils import get_curr_server_str_datetime_ms
from core.utils import download_file, hash10


class EndpointHelper(ImportHelperMixin):
    FIELD_REQUEST_DATETIME = 'ep_sent'
    FIELD_SERVER_DATETIME = 'ep_server'
    FIELD_RESPONSE_DATETIME = 'ep_recv'

    def get_data(self) -> str:
        url = 'https://game.trainstation2.com/get-endpoints'
        headers = self.default_header()
        return self.get(
            url=url,
            headers=headers,
            params={}
        )

    def parse_data(self, data) -> str:
        """

        :param user:
        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)

        check_response(json_data=json_data)

        server_time = json_data.get('Time')
        ret, _ = EndPoint.create_instance(
            data=json_data.get('Data', {}).get('Endpoints', []),
            version_id=self.version.id,
        )
        stores = list(EndPoint.objects.all())

        a = set([(a.name, a.url) for a in ret])
        b = set([(a.name, a.url) for a in stores])

        if a != b:
            EndPoint.objects.all().delete()

            if ret:
                EndPoint.objects.bulk_create(ret)

        return server_time


class LoginHelper(ImportHelperMixin):

    FIELD_REQUEST_DATETIME = 'login_sent'
    FIELD_SERVER_DATETIME = 'login_server'
    FIELD_RESPONSE_DATETIME = 'login_recv'

    def get_data(self) -> str:
        urls = EndPoint.get_login_url()

        headers = self.default_header()
        """
            "headers": {
                "PXFD-Request-Id": "68d3d880-04ab-402c-bf96-1c19ef2e4152", 
                "PXFD-Retry-No": "0", 
                "PXFD-Sent-At": "2023-01-17T04:09:17.207Z",
                'PXFD-Client-Information': '{"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}', 
                "PXFD-Client-Version": "2.6.3.4068", 
                "PXFD-Device-Token": "30b270ca64e80bbbf4b186f251ba358a", 
                "Content-Type": "application/json", 
                "Accept-Encoding": "gzip, deflate"
            }, 
        """
        headers.update({
            'PXFD-Sent-At': get_curr_server_str_datetime_ms(version=self.version),  # 'PXFD-Sent-At': '2023-01-17T04:09:17.617Z',
            'Accept-Encoding': 'gzip, deflate',
        })

        if self.version.user.remember_me_token:
            payload = {
                'LoginType': 'remember_me_token',
                'Identity': self.version.user.remember_me_token,
            }
        else:
            payload = {
                'LoginType': 'device_id',
                'Identity': self.version.user.device_id,
            }

        return self.post(
            url=urls[0] if urls else None,
            headers=headers,
            payload=json.dumps(payload, separators=(',', ':')),
        )

    def parse_data(self, data) -> str:
        """

        :param user:
        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)

        check_response(json_data=json_data)

        server_time = json_data.get('Time')
        ret, _ = EndPoint.create_instance(
            data=json_data.get('Data', {}).get('Endpoints', []),
            version_id=self.version.id,
        )
        stores = list(EndPoint.objects.all())

        a = set([(a.name, a.url) for a in ret])
        b = set([(a.name, a.url) for a in stores])

        if a != b:
            EndPoint.objects.all().delete()

            if ret:
                EndPoint.objects.bulk_create(ret)

        return server_time


class SQLDefinitionHelper(ImportHelperMixin):
    FIELD_REQUEST_DATETIME = 'sd_sent'
    FIELD_SERVER_DATETIME = 'sd_server'
    FIELD_RESPONSE_DATETIME = 'sd_recv'

    BASE_PATH = settings.SITE_PATH / 'download' / 'definition'

    def get_data(self) -> str:

        urls = EndPoint.get_definition_url()

        headers = self.default_header()
        """
            "headers": {
                'PXFD-Request-Id': '28d035ae-cc67-4234-a12e-d333cfcbcd14', 
                'PXFD-Retry-No': '0', 
                'PXFD-Sent-At': '2023-01-17T04:09:17.617Z', 
                'PXFD-Client-Information': '{"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}', 
                'PXFD-Client-Version': '2.6.3.4068', 
                'PXFD-Device-Token': '30b270ca64e80bbbf4b186f251ba358a', 
                'PXFD-Game-Access-Token': '54bd72c2-d294-5e74-95b1-2f81210e1381',
                'PXFD-Player-Id': '62794770', 
                'Accept-Encoding': 'gzip, deflate'
            }
        """
        headers.update({
            'PXFD-Sent-At': get_curr_server_str_datetime_ms(version=self.version),  # 'PXFD-Sent-At': '2023-01-17T04:09:17.617Z',
            'PXFD-Game-Access-Token': self.version.user.game_access_token,
            'PXFD-Player-Id': self.version.player_id,
            'Accept-Encoding': 'gzip, deflate',
        })

        return self.get(
            url=urls[0] if urls else None,
            headers=headers,
            params={}
        )

    def parse_data(self, data) -> str:
        """

        :param user:
        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)

        check_response(json_data=json_data)

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
                instance = SQLDefinition.objects.order_by('-pk').first()

                # try:
                if not instance or instance.version != version:
                    instance = SQLDefinition.objects.create(
                        version=version,
                        checksum=checksum,
                        url=url,
                        download_path=self.BASE_PATH / f'{version}.sqlite'
                    )

                    if self.download_data(instance):
                        self.read_sqlite(instance)

        return server_time

    def download_data(self, instance: SQLDefinition):
        if instance:
            download_filename = Path(instance.download_path)

            if instance.url and not download_filename.exists():
                download_file(url=instance.url, download_filename=download_filename)

            return download_filename.lstat().st_size

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
        model = TSArticle
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

    def _read_user_level(self, cur):
        model = TSUserLevel
        remote_table_name = 'player_level'
        mapping = {  # local DB field : remote db field
            'id': 'level',
            'xp': 'xp',
            'rewards': 'rewards',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_warehouse_level(self, cur):
        model = TSWarehouseLevel
        remote_table_name = 'warehouse_level'
        mapping = {  # local DB field : remote db field
            'id': 'level',
            'capacity': 'capacity',
            'upgrade_article_ids': 'upgrade_article_ids',
            'upgrade_article_amounts': 'upgrade_article_amounts',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_factory(self, cur):
        model = TSFactory
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
        model = TSProduct
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
        model = TSTrain
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

    def _read_train_level(self, cur):
        model = TSTrainLevel
        remote_table_name = 'train_level'
        mapping = {  # local DB field : remote db field
            'train_level': 'train_level',
            'power': 'power',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_region(self, cur):
        model = TSRegion
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
        model = TSLocation
        remote_table_name = 'location'
        mapping = {  # local DB field : remote db field
            'id': 'id',
            'region': 'region',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def _read_destination(self, cur):
        model = TSDestination
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

    def _read_job_location(self, cur):
        model = TSJobLocation
        remote_table_name = 'job_location_v2'
        mapping = {  # local DB field : remote db field
            'id': 'job_location_id',
            'location_id': 'location_id',
            'region_id': 'region_id',
            'local_key': 'loca_key',
            'name_local_key': 'name_loca_key',
            'contractor_id': 'contractor_id',
        }
        self._read_sqlite(model=model, remote_table_name=remote_table_name, mapping=mapping, cur=cur)

    def read_sqlite(self, instance: SQLDefinition):
        if instance:
            con = sqlite3.connect(instance.download_path)
            cur = con.cursor()
            self._read_article(cur=cur)
            self._read_user_level(cur=cur)
            self._read_warehouse_level(cur=cur)
            self._read_factory(cur=cur)
            self._read_product(cur=cur)
            self._read_train(cur=cur)
            self._read_train_level(cur=cur)
            self._read_region(cur=cur)
            self._read_location(cur=cur)
            self._read_destination(cur=cur)
            self._read_job_location(cur=cur)
            con.close()