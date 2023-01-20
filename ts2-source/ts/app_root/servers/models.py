from datetime import timedelta
from decimal import Decimal
from functools import cached_property
from typing import List, Dict, Tuple

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_root.servers.mixins import ContentCategoryMixin, RarityMixin, EraMixin
from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin
from core.utils import hash10


class RunVersion(BaseModelMixin, TimeStampedMixin, TaskModelMixin):

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )

    # from _parse_init_player
    player_id = models.CharField(_('PlayerId'), max_length=50, null=False, blank=False)
    player_name = models.CharField(_('PlayerName'), max_length=50, null=False, blank=False)
    level = models.IntegerField(_('level'), null=False, blank=False, default=0)

    # from _parse_init_city_loop
    population = models.IntegerField(_('population'), null=False, blank=False, default=0)

    # from _parse_init_warehouse
    # warehouse_capacity = models.IntegerField(_('warehouse'), null=False, blank=False, default=0)
    warehouse_level = models.IntegerField(_('warehouse_level'), null=False, blank=False, default=0)

    # _parse_init_dispatcher
    dispatchers = models.IntegerField(_('dispatchers'), null=False, blank=False, default=0)
    guild_dispatchers = models.IntegerField(_('guild_dispatchers'), null=False, blank=False, default=0)

    # next event
    next_event_datetime = models.DateTimeField(_('next event datetime'), null=True, blank=False, default=None)

    # command no.
    command_no = models.IntegerField(_('Command No'), null=False, blank=True, default=1)

    is_completed = models.BooleanField(_('is completed'), null=False, blank=True, default=False)
    has_error = models.BooleanField(_('has error'), null=False, blank=True, default=False)

    # Step 1. Endpoint
    ep_sent = models.DateTimeField(_('Endpoint Sent Datetime'), null=True, blank=False, default=None)
    ep_server = models.DateTimeField(_('Endpoint Server Datetime'), null=True, blank=False, default=None)
    ep_recv = models.DateTimeField(_('Endpoint Recv Datetime'), null=True, blank=False, default=None)

    # Step 2. Login
    login_sent = models.DateTimeField(_('Login Sent Datetime'), null=True, blank=False, default=None)
    login_server = models.DateTimeField(_('Login Server Datetime'), null=True, blank=False, default=None)
    login_recv = models.DateTimeField(_('Login Recv Datetime'), null=True, blank=False, default=None)

    # Step 3. SQL Definition.
    sd_sent = models.DateTimeField(_('SQL Definition Sent Datetime'), null=True, blank=False, default=None)
    sd_server = models.DateTimeField(_('SQL Definition Server Datetime'), null=True, blank=False, default=None)
    sd_recv = models.DateTimeField(_('SQL Definition Recv Datetime'), null=True, blank=False, default=None)

    # Step 4. Init Data
    init_sent_1 = models.DateTimeField(_('Init Data Sent Datetime'), null=True, blank=False, default=None)
    init_server_1 = models.DateTimeField(_('Init Data Server Datetime'), null=True, blank=False, default=None)
    init_recv_1 = models.DateTimeField(_('Init Data Recv Datetime'), null=True, blank=False, default=None)

    # Step 4. Init Data (legacy)
    init_sent_2 = models.DateTimeField(_('Init Data Sent Datetime'), null=True, blank=False, default=None)
    init_server_2 = models.DateTimeField(_('Init Data Server Datetime'), null=True, blank=False, default=None)
    init_recv_2 = models.DateTimeField(_('Init Data Recv Datetime'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Version'
        verbose_name_plural = 'Versions'

    @property
    def delta(self) -> timedelta:
        delta = []
        if self.ep_sent and self.ep_server and self.ep_recv:
            delta.append(self.ep_server - self.ep_recv)

        if self.login_sent and self.login_server and self.login_recv:
            delta.append(self.login_server - self.login_recv)

        if self.sd_sent and self.sd_server and self.sd_recv:
            delta.append(self.sd_server - self.sd_recv)

        if self.init_sent_1 and self.init_server_1 and self.init_recv_1:
            delta.append(self.init_server_1 - self.init_recv_1)

        if self.init_sent_2 and self.init_server_2 and self.init_recv_2:
            delta.append(self.init_server_2 - self.init_recv_2)

        return sum(delta) / len(delta) if delta else timedelta(seconds=0)


class EndPoint(BaseModelMixin, TimeStampedMixin):

    ENDPOINT_LOGIN = 'login'
    ENDPOINT_DEFINITION = 'definitions'
    ENDPOINT_LEADER_BOARD = 'leaderboard'
    ENDPOINT_COMMAND_PROCESSING = 'command_processing_collection'
    ENDPOINT_START_GAME = 'start_game'
    ENDPOINT_UPDATE_DEVICE_ID = 'update_device_id'
    ENDPOINT_INIT_DATA_URLS = '_initdata_urls_'
    name = models.CharField(_('version'), max_length=255, null=False, blank=False)
    name_hash = models.BigIntegerField(_('name hash'), null=False, blank=False, default=0, db_index=True)

    url = models.CharField(_('version'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Endpoint'
        verbose_name_plural = 'Endpoints'

    @classmethod
    def create_instance(cls, *, data: Dict, version_id: int, **kwargs) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
                {"Name":"login","Url":"https://game.trainstation2.com/login"}
                {"Name":"login_v2","Url":"https://game.trainstation2.com/login/v2"}                
            """
            for ep in data:
                name = ep.get('Name')
                url = ep.get('Url')
                ret.append(
                    EndPoint(
                        name=name,
                        name_hash=hash10(name),
                        url=url,
                        created=now, modified=now
                    )
                )

        return ret, _

    @classmethod
    def create_init_urls(cls, *, data: List) -> List:
        # InitialDataUrls
        """
            "InitialDataUrls\":[
                [\"https://game.trainstation2.com/api/v2/initial-data/load\",\"https://game.trainstation2.com/api/v2/initial-data/legacy\"]
            ]}}
        """
        ret = []
        now = timezone.now()

        for row in data:
            for url in row:
                ret.append(
                    EndPoint(
                        name=cls.ENDPOINT_INIT_DATA_URLS,
                        name_hash=hash10(cls.ENDPOINT_INIT_DATA_URLS),
                        url=url,
                        created=now, modified=now
                    )
                )

        return ret
    @classmethod
    def get_urls(cls, endpoint) -> List[str]:
        ret = []
        queryset = cls.objects.filter(name_hash=hash10(endpoint), name=endpoint).all()
        for row in queryset.all():
            ret.append(row.url)
        return ret

    @classmethod
    def get_login_urls(cls) -> List[str]:
        return cls.get_urls(cls.ENDPOINT_LOGIN)

    @classmethod
    def get_definition_urls(cls) -> List[str]:
        return cls.get_urls(cls.ENDPOINT_DEFINITION)


class SQLDefinition(TaskModelMixin, BaseModelMixin, TimeStampedMixin):
    version = models.CharField(_('version'), max_length=20, null=False, blank=False)
    checksum = models.CharField(_('checksum'), max_length=50, null=False, blank=False)
    url = models.URLField(_('download url'), null=False, blank=False)
    download_path = models.CharField(_('checksum'), max_length=200, null=False, blank=False)

    class Meta:
        verbose_name = 'Definition'
        verbose_name_plural = 'Definitions'


class TSUserLevel(BaseModelMixin, TimeStampedMixin):
    xp = models.IntegerField(_('XP'), null=False, blank=False, default=0)
    rewards = models.CharField(_('rewards'), max_length=255, null=False, blank=False, default='')

    class Meta:
        verbose_name = 'User Level'
        verbose_name_plural = 'User Levels'


class TSWarehouseLevel(BaseModelMixin, TimeStampedMixin):
    capacity = models.IntegerField(_('capacity'), null=False, blank=False, default=0)
    upgrade_article_ids = models.CharField(_('upgrade_article_ids'), max_length=255, null=False, blank=False, default='')
    upgrade_article_amounts = models.CharField(_('upgrade_article_amounts'), max_length=255, null=False, blank=False, default='')

    class Meta:
        verbose_name = 'Warehouse Level'
        verbose_name_plural = 'Warehouse Levels'


class TSArticle(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin):
    """
    CREATE TABLE article (
    id INTEGER NOT NULL,
    loca_key VARCHAR(255) NOT NULL,
    name_loca_key VARCHAR(255) DEFAULT NULL,
    hint_loca_key VARCHAR(255) DEFAULT NULL,
    level_req INTEGER NOT NULL,
    level_from VARCHAR(255) NOT NULL,
    type_id INTEGER NOT NULL,
     event_id INTEGER NOT NULL,
     content_category INTEGER NOT NULL,
     sprite_id VARCHAR(255) DEFAULT NULL,
     wagon_type VARCHAR(255) NOT NULL,
      gem_price NUMERIC(19, 2) DEFAULT NULL, max_gem_price INTEGER NOT NULL, PRIMARY KEY(id))
    """
    level_req = models.IntegerField(_('level required'), null=False, blank=False, default=0)
    level_from = models.IntegerField(_('level from'), null=False, blank=False, default=0)
    type = models.IntegerField(_('type'), null=False, blank=False, default=0)
    event = models.IntegerField(_('event'), null=False, blank=False, default=0)
    sprite = models.CharField(_('sprite id'), max_length=255, null=True, blank=False)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return f'[{self.sprite}/{self.get_content_category_display()}]'  #/type:{self.type}/event:{self.event}]'


class TSFactory(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin):
    """
        CREATE TABLE factory (
            id INTEGER NOT NULL,
            loca_key VARCHAR(255) NOT NULL,
            name_loca_key VARCHAR(255) NOT NULL,
            level_req INTEGER NOT NULL,
            level_from INTEGER NOT NULL,
            starting_slot_count INTEGER NOT NULL,
            max_slot_count INTEGER NOT NULL,
            type_id INTEGER NOT NULL,
            content_category INTEGER NOT NULL,
            asset_name VARCHAR(255) NOT NULL,
            background_color VARCHAR(255) NOT NULL,
            sprite_id VARCHAR(255) NOT NULL,
            unlocked_by INTEGER DEFAULT NULL,
            PRIMARY KEY(id)
        )
    """
    level_req = models.IntegerField(_('level required'), null=False, blank=False, default=0)
    level_from = models.IntegerField(_('level from'), null=False, blank=False, default=0)

    starting_slot_count = models.IntegerField(_('starting_slot_count'), null=False, blank=False, default=0)
    max_slot_count = models.IntegerField(_('max_slot_count'), null=False, blank=False, default=0)
    type = models.IntegerField(_('type'), null=False, blank=False, default=0)
    asset_name = models.CharField(_('asset_name'), max_length=255, null=False, blank=False)
    sprite = models.CharField(_('sprite id'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Factory'
        verbose_name_plural = 'Factories'

    def __str__(self):
        return f'[{self.sprite}/{self.get_content_category_display()}]'


class TSProduct(BaseModelMixin, TimeStampedMixin):
    """
        CREATE TABLE product (
            factory_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            article_amount INTEGER NOT NULL,
            craft_time INTEGER NOT NULL,
            article_ids VARCHAR(255) NOT NULL,
            article_amounts VARCHAR(255) NOT NULL,
            level_req INTEGER NOT NULL,
            level_from INTEGER NOT NULL,
            PRIMARY KEY(factory_id, article_id)
        )
    """
    factory = models.ForeignKey(
        to='servers.TSFactory',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )

    article = models.ForeignKey(
        to='servers.TSArticle',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )

    article_amount = models.IntegerField(_('article_amount'), null=False, blank=False, default=0)
    craft_time = models.IntegerField(_('craft_time'), null=False, blank=False, default=0)

    article_ids = models.CharField(_('article_ids'), max_length=255, null=False, blank=False)
    article_amounts = models.CharField(_('article_amounts'), max_length=255, null=False, blank=False)
    level_req = models.IntegerField(_('level required'), null=False, blank=False, default=0)
    level_from = models.IntegerField(_('level from'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class TSTrain(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin, RarityMixin, EraMixin):
    """
    CREATE TABLE train (
        id INTEGER NOT NULL,
        content_category INTEGER NOT NULL,
        loca_key VARCHAR(255) NOT NULL,
        name_loca_key VARCHAR(255) NOT NULL,
        reward BOOLEAN NOT NULL,
        region INTEGER NOT NULL,
        rarity_id INTEGER NOT NULL,
        max_level INTEGER NOT NULL,
        era_id INTEGER NOT NULL,
        asset_name VARCHAR(255) NOT NULL,
        asset_name_alt VARCHAR(255) DEFAULT NULL,
        unlocked_by INTEGER DEFAULT NULL,
        contractor_id INTEGER DEFAULT NULL,
        PRIMARY KEY(id)
    )
    """
    reward = models.BooleanField(_('reward'), null=False, blank=False, default=False)
    region = models.IntegerField(_('region'), null=False, blank=False, default=0)
    max_level = models.IntegerField(_('max_level'), null=False, blank=False, default=0)
    asset_name = models.CharField(_('asset_name'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Train'
        verbose_name_plural = 'Trains'

    def __str__(self):
        return f'''content:{self.get_content_category_display()}/rewared:{self.reward}/region:{self.region}/rarity:{self.get_rarity_display()}/max_level:{self.max_level}/era:{self.get_era_display()}/asset:{self.asset_name}'''


class TSTrainLevel(BaseModelMixin, TimeStampedMixin):
    """
    CREATE TABLE train_level (train_level INTEGER NOT NULL, power VARCHAR(255) NOT NULL, PRIMARY KEY(train_level))
    """
    train_level = models.IntegerField(_('train_level'), null=False, blank=False, default=0)
    power = models.CharField(_('power'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Train Level'
        verbose_name_plural = 'Train Levels'


class TSRegion(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin):
    """
        CREATE TABLE region (
        id INTEGER NOT NULL,
        level_from INTEGER NOT NULL,
        name_loca_key VARCHAR(255) NOT NULL,
        picture_asset_name VARCHAR(255) NOT NULL,
        content_category INTEGER NOT NULL,
        map_id VARCHAR(255) DEFAULT NULL,
        asset_name VARCHAR(255) NOT NULL,
        contractor_asset_name VARCHAR(255) NOT NULL,
        gold_amount_coefficient INTEGER NOT NULL,
        train_upgrade_price_coefficient NUMERIC(19, 2) NOT NULL,
        city_currency_coefficient INTEGER NOT NULL,
        ordering INTEGER NOT NULL,
        music_track_id INTEGER DEFAULT NULL,
        event_registration_required BOOLEAN NOT NULL,
        PRIMARY KEY(id)
    )
    """
    level_from = models.IntegerField(_('level from'), null=False, blank=False, default=0)
    asset_name = models.CharField(_('sprite id'), max_length=255, null=False, blank=False)
    gold_amount_coefficient = models.IntegerField(_('gold_amount_coefficient'), null=False, blank=False, default=0)
    train_upgrade_price_coefficient = models.DecimalField(_('train_upgrade_price_coefficient'), max_digits=30, decimal_places=10, null=False, blank=True, default=Decimal('0.0'))
    city_currency_coefficient = models.IntegerField(_('city_currency_coefficient'), null=False, blank=False, default=0)
    ordering = models.IntegerField(_('ordering'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'

    def __str__(self):
        return f'''{self.asset_name}'''


class TSLocation(BaseModelMixin, TimeStampedMixin):
    """
        CREATE TABLE location (
        id INTEGER NOT NULL,
        region INTEGER NOT NULL,
        available_skins VARCHAR(255) DEFAULT NULL,
        PRIMARY KEY(id)
    )
    """
    region = models.IntegerField(_('region'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    def __str__(self):
        return f'[region:{self.region}]'


class TSJobLocation(BaseModelMixin, TimeStampedMixin):
    """
    CREATE TABLE job_location_v2 (
        job_location_id INTEGER NOT NULL,
        location_id INTEGER NOT NULL,
        region_id INTEGER NOT NULL,
        loca_key VARCHAR(255) NOT NULL,
        name_loca_key VARCHAR(255) DEFAULT NULL,
        contractor_id INTEGER NOT NULL,
        max_level INTEGER NOT NULL,
        sequence_loca_key VARCHAR(255) DEFAULT NULL,
        unlocked_by VARCHAR(255) DEFAULT NULL,
        level_from INTEGER NOT NULL,
        available_from DATETIME DEFAULT NULL --(DC2Type:datetime_immutable)
        , available_to DATETIME DEFAULT NULL --(DC2Type:datetime_immutable)
        , PRIMARY KEY(job_location_id)
    )
    """
    # job_location_id = models.IntegerField(_('Job Location ID'), null=False, blank=False, default=0)
    location = models.ForeignKey(
        to='servers.TSLocation',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    region = models.ForeignKey(
        to='servers.TSRegion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    local_key = models.CharField(_('local key'), max_length=255, null=False, blank=False, default='')
    name_local_key = models.CharField(_('local key'), max_length=255, null=True, blank=False, default='')
    contractor_id = models.IntegerField(_('Contractor ID'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Job Location'
        verbose_name_plural = 'Job Locations'

    def __str__(self):
        return f'[{self.region}:{self.name_local_key}]'


class TSDestination(BaseModelMixin, TimeStampedMixin):
    """
        CREATE TABLE destination (
            id INTEGER NOT NULL,
            loca_key VARCHAR(255) NOT NULL,
            name_loca_key VARCHAR(255) DEFAULT NULL,
            location_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            region_id INTEGER NOT NULL,
            sprite_id VARCHAR(255) DEFAULT NULL,
            time INTEGER NOT NULL,
            travel_duration INTEGER NOT NULL,
            multiplier INTEGER NOT NULL,
            refresh_time INTEGER NOT NULL,
            train_limit INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            period_start_hour INTEGER DEFAULT NULL,
            period_length INTEGER DEFAULT NULL,
            unlocked_by INTEGER DEFAULT NULL,
            requirements VARCHAR(255) NOT NULL,
            PRIMARY KEY(id)
        )
    """
    location = models.ForeignKey(
        to='servers.TSLocation',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='servers.TSArticle',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    region = models.ForeignKey(
        to='servers.TSRegion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    sprite = models.CharField(_('sprite id'), max_length=255, null=True, blank=False)
    time = models.IntegerField(_('time'), null=False, blank=False, default=0)
    travel_duration = models.IntegerField(_('travel_duration'), null=False, blank=False, default=0)
    multiplier = models.IntegerField(_('multiplier'), null=False, blank=False, default=0)
    refresh_time = models.IntegerField(_('refresh_time'), null=False, blank=False, default=0)
    train_limit = models.IntegerField(_('train_limit'), null=False, blank=False, default=0)
    capacity = models.IntegerField(_('capacity'), null=False, blank=False, default=0)
    requirements = models.CharField(_('requirements'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Destination'
        verbose_name_plural = 'Destinations'

    @cached_property
    def split_requirements(self) -> Dict[str, int]:
        ret = {}

        arr = self.requirements.split('|')
        for a in arr:
            t = a.split(';')
            if len(t) == 2:
                k, v = t

                if k not in ret:
                    ret.update({k: []})

                ret[k].append(int(v))

        return ret

    def get_rarity_requirements(self) -> List:
        """
        rarity;3|rarity;4|region;1
        rarity;3|rarity;4|region;2
        rarity;4|region;3
        rarity;4|region;4
        :return:
        """
        return self.split_requirements.get('rarity', [])

    def get_region_requirements(self) -> List:
        """
        rarity;3|rarity;4|region;1
        rarity;3|rarity;4|region;2
        rarity;4|region;3
        rarity;4|region;4
        :return:
        """
        return self.split_requirements.get('region', [])