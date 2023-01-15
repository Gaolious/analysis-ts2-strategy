import datetime
import json
from decimal import Decimal
from functools import cached_property
from typing import List, Tuple, Dict

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin
from core.utils import convert_time, convert_datetime

CONTENT_CATEGORY_BASIC = 1
CONTENT_CATEGORY_EVENT = 2
CONTENT_CATEGORY_UNION = 3
CHOICE_CONTENT_CATEGORY = (
    (CONTENT_CATEGORY_BASIC, '기본'),
    (CONTENT_CATEGORY_EVENT, '이벤트'),
    (CONTENT_CATEGORY_UNION, '유니언'),
)

RARITY_COMMON = 1
RARITY_RARE = 2
RARITY_EPIC = 3
RARITY_LEGENDARY = 4
CHOICE_RARITY = (
    (RARITY_COMMON, '일반'),
    (RARITY_RARE, '레어'),
    (RARITY_EPIC, '에픽'),
    (RARITY_LEGENDARY, '전설'),
)

ERA_STEAM = 1
ERA_DIESEL = 2
ERA_ELECTRON = 3
CHOICE_ERA = (
    (ERA_STEAM, '스팀'),
    (ERA_DIESEL, '디젤'),
    (ERA_ELECTRON, '전기'),
)


class ContentCategoryMixin(models.Model):
    """
        기본 / 이벤트 / 유니언
    """
    content_category = models.IntegerField(_('content category'), null=False, blank=False, default=0, choices=CHOICE_CONTENT_CATEGORY)

    class Meta:
        abstract = True

    @property
    def is_basic(self) -> bool:
        return self.content_category == CONTENT_CATEGORY_BASIC

    @property
    def is_event(self) -> bool:
        return self.content_category == CONTENT_CATEGORY_EVENT

    @property
    def is_union(self) -> bool:
        return self.content_category == CONTENT_CATEGORY_UNION


class RarityMixin(models.Model):
    """
        일반 / 레어 / 에픽 / 전설
    """

    rarity = models.IntegerField(_('rarity'), null=False, blank=False, default=0, choices=CHOICE_RARITY)

    class Meta:
        abstract = True

    @property
    def is_common(self) -> bool:
        return self.rarity == RARITY_COMMON

    @property
    def is_rare(self) -> bool:
        return self.rarity == RARITY_RARE

    @property
    def is_epic(self) -> bool:
        return self.rarity == RARITY_EPIC

    @property
    def is_legendary(self) -> bool:
        return self.rarity == RARITY_LEGENDARY


class EraMixin(models.Model):
    """
        스팀 / 디젤 / 전기
    """

    era = models.IntegerField(_('era'), null=False, blank=False, default=0, choices=CHOICE_ERA)

    class Meta:
        abstract = True

    @property
    def is_steam(self) -> bool:
        return self.era == ERA_STEAM

    @property
    def is_diesel(self) -> bool:
        return self.era == ERA_DIESEL

    @property
    def is_electron(self) -> bool:
        return self.era == ERA_ELECTRON


class Definition(BaseModelMixin, TimeStampedMixin):
    version = models.CharField(_('version'), max_length=20, null=False, blank=False)
    checksum = models.CharField(_('checksum'), max_length=50, null=False, blank=False)
    url = models.URLField(_('download url'), null=False, blank=False)
    download_path = models.CharField(_('checksum'), max_length=200, null=False, blank=False)

    class Meta:
        verbose_name = 'Definition'
        verbose_name_plural = 'Definitions'


class UserLevel(BaseModelMixin, TimeStampedMixin):
    xp = models.IntegerField(_('XP'), null=False, blank=False, default=0)
    rewards = models.CharField(_('rewards'), max_length=255, null=False, blank=False, default='')

    class Meta:
        verbose_name = 'User Level'
        verbose_name_plural = 'User Levels'


class WarehouseLevel(BaseModelMixin, TimeStampedMixin):
    capacity = models.IntegerField(_('capacity'), null=False, blank=False, default=0)
    upgrade_article_ids = models.CharField(_('upgrade_article_ids'), max_length=255, null=False, blank=False, default='')
    upgrade_article_amounts = models.CharField(_('upgrade_article_amounts'), max_length=255, null=False, blank=False, default='')

    class Meta:
        verbose_name = 'Warehouse Level'
        verbose_name_plural = 'Warehouse Levels'


class Article(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin):
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


class Factory(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin):
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


class Product(BaseModelMixin, TimeStampedMixin):
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
        to='bot.Factory',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )

    article = models.ForeignKey(
        to='bot.Article',
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


class Train(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin, RarityMixin, EraMixin):
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


class TrainLevel(BaseModelMixin, TimeStampedMixin):
    """
    CREATE TABLE train_level (train_level INTEGER NOT NULL, power VARCHAR(255) NOT NULL, PRIMARY KEY(train_level))
    """
    train_level = models.IntegerField(_('train_level'), null=False, blank=False, default=0)
    power = models.CharField(_('power'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Train Level'
        verbose_name_plural = 'Train Levels'


class Region(BaseModelMixin, TimeStampedMixin, ContentCategoryMixin):
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


class Location(BaseModelMixin, TimeStampedMixin):
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


class JobLocation(BaseModelMixin, TimeStampedMixin):
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
        to='bot.Location',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    region = models.ForeignKey(
        to='bot.Region',
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


class Destination(BaseModelMixin, TimeStampedMixin):
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
        to='bot.Location',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    region = models.ForeignKey(
        to='bot.Region',
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

class RunVersion(BaseModelMixin, TimeStampedMixin, TaskModelMixin):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    player_id = models.CharField(_('PlayerId'), max_length=50, null=False, blank=False)
    player_name = models.CharField(_('PlayerName'), max_length=50, null=False, blank=False)

    # article id = 1
    xp = models.IntegerField(_('xp'), null=False, blank=False, default=0)
    # article id = 2
    gem = models.IntegerField(_('gem'), null=False, blank=False, default=0)
    # article id = 3
    gold = models.IntegerField(_('gold'), null=False, blank=False, default=0)
    # article id = 4
    key = models.IntegerField(_('key'), null=False, blank=False, default=0)

    level = models.IntegerField(_('level'), null=False, blank=False, default=0)
    population = models.IntegerField(_('population'), null=False, blank=False, default=0)
    warehouse = models.IntegerField(_('warehouse'), null=False, blank=False, default=0)
    warehouse_level = models.IntegerField(_('warehouse_level'), null=False, blank=False, default=0)

    train_parts_common = models.IntegerField(_('train_common'), null=False, blank=False, default=0)
    train_parts_rare = models.IntegerField(_('train_rare'), null=False, blank=False, default=0)
    train_parts_epic = models.IntegerField(_('train_epic'), null=False, blank=False, default=0)
    train_parts_legendary = models.IntegerField(_('train_legendary'), null=False, blank=False, default=0)

    # article id = 10
    blue_city_plans = models.IntegerField(_('blue_city_plans'), null=False, blank=False, default=0)
    # article id = 11
    yellow_city_plans = models.IntegerField(_('yellow_city_plans'), null=False, blank=False, default=0)
    # article id = 12
    red_city_plans = models.IntegerField(_('red_city_plans'), null=False, blank=False, default=0)

    dispatchers = models.IntegerField(_('dispatchers'), null=False, blank=False, default=0)
    guild_dispatchers = models.IntegerField(_('guild_dispatchers'), null=False, blank=False, default=0)

    next_event_datetime = models.DateTimeField(_('next event datetime'), null=True, blank=False, default=None)

    init_data_request_datetime = models.DateTimeField(_('init_data_request_datetime'), null=True, blank=False, default=None)
    init_data_response_datetime = models.DateTimeField(_('init_data_response_datetime'), null=True, blank=False, default=None)
    init_data_server_datetime = models.DateTimeField(_('init_data_server_datetime'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Version'
        verbose_name_plural = 'Versions'

    def get_all_trains(self):
        return list(
            PlayerTrain.objects.filter(version_id=self.id).all()
        )

    def get_all_coin_destinations(self):
        return list(
            PlayerDestination.objects.filter(version_id=self.id).all()
        )


class PlayerBuilding(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    instance_id = models.IntegerField(_('instance id'), null=True, blank=False)
    definition_id = models.IntegerField(_('instance id'), null=True, blank=False)
    rotation = models.IntegerField(_('instance id'), null=True, blank=False)
    level = models.IntegerField(_('instance id'), null=True, blank=False)
    upgrade_task = models.CharField(_('upgrade task'), max_length=255, null=True, blank=False, default='')
    parcel_number = models.IntegerField(_('parcel_number'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Building'
        verbose_name_plural = 'Buildings'

    @property
    def is_placed(self):
        return True if self.parcel_number else False

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for bld in data:
                instance_id = bld.get('InstanceId')
                definition_id = bld.get('DefinitionId')
                rotation = bld.get('Rotation')
                level = bld.get('Level')
                upgrade_task = bld.get('UpgradeTask')
                parcel_number = bld.get('ParcelNumber')
                instance = PlayerBuilding(
                    version_id=version_id,
                    instance_id=instance_id or 0,
                    definition_id=definition_id or 0,
                    rotation=rotation or 0,
                    level=level or 0,
                    parcel_number = parcel_number or 0,
                    upgrade_task=json.dumps(upgrade_task, separators=(',', ':')) if upgrade_task else '',
                    created=now, modified=now,
                )

                ret.append(instance)

        return ret


class PlayerDestination(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    location = models.ForeignKey(
        to='bot.Location',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    definition = models.ForeignKey(
        to='bot.Destination',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    train_limit_count = models.IntegerField(_('train_limit_count'), null=True, blank=False)
    train_limit_refresh_time = models.DateTimeField(_('train_limit_refresh_time'), null=True, blank=False)
    train_limit_refresh_at = models.DateTimeField(_('train_limit_refresh_at'), null=True, blank=False)
    multiplier = models.IntegerField(_('multiplier'), null=True, blank=False, default='')

    class Meta:
        verbose_name = 'Building'
        verbose_name_plural = 'Buildings'

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for row in data:
                location_id = row.get('LocationId')
                definition_id = row.get('DefinitionId')
                train_limit_count = row.get('TrainLimitCount')
                train_limit_refresh_time = row.get('TrainLimitRefreshTime')
                train_limit_refresh_at = row.get('TrainLimitRefreshesAt')
                multiplier = row.get('Multiplier')

                instance = PlayerDestination(
                    version_id=version_id,
                    location_id=location_id or 0,
                    definition_id=definition_id or 0,
                    train_limit_count=train_limit_count or 0,
                    train_limit_refresh_time=convert_datetime(train_limit_refresh_time),
                    train_limit_refresh_at=convert_datetime(train_limit_refresh_at),
                    multiplier=multiplier or 0,
                    created=now, modified=now,
                )
                ret.append(instance)

        return ret

    def next_event_datetime(self, init_data_request_datetime, init_data_server_datetime, now) -> datetime:

        diff = init_data_request_datetime - init_data_server_datetime
        next_event = (self.train_limit_refresh_at + diff).astimezone(settings.KST)
        return next_event

    def remain_seconds(self, init_data_request_datetime, init_data_server_datetime, now) -> float:
        diff = init_data_request_datetime - init_data_server_datetime
        next_event = (self.train_limit_refresh_at + diff).astimezone(settings.KST)
        remain = next_event - now
        return remain.total_seconds()


class PlayerFactory(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    factory = models.ForeignKey(
        to='bot.Factory',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    slot_count = models.IntegerField(_('slot count'), null=False, blank=False)

    class Meta:
        verbose_name = 'Player Factory'
        verbose_name_plural = 'Player Factories'

    @classmethod
    def create_instance(cls, data, version_id: int) -> Tuple[List, List]:
        ret = []
        sub_ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:

            for factory in data:
                definition_id = factory.pop('DefinitionId', None)
                slot_count = factory.pop('SlotCount', None)

                player_factory = PlayerFactory(
                    version_id=version_id,
                    factory_id=definition_id,
                    slot_count=slot_count,
                    created=now, modified=now,
                )
                ret.append(player_factory)

                sub_ret += PlayerFactoryProductOrder.create_instance(
                    data=factory.get('ProductOrders', []),
                    player_factory=player_factory,
                    version_id=version_id,
                )

        return ret, sub_ret


class PlayerFactoryProductOrder(BaseModelMixin, TimeStampedMixin):
    """
        00 = {dict: 4} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:30:12Z', 'FinishesAt': '2022-12-30T00:30:12Z'}
        01 = {dict: 4} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T00:35:12Z', 'FinishesAt': '2022-12-30T00:35:12Z'}
        02 = {dict: 4} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00', 'FinishTime': '2022-12-30T02:42:35Z', 'FinishesAt': '2022-12-30T02:42:35Z'}
        03 = {dict: 4} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:12:35Z', 'FinishesAt': '2022-12-30T03:12:35Z'}
        04 = {dict: 4} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T03:42:35Z', 'FinishesAt': '2022-12-30T03:42:35Z'}
        05 = {dict: 4} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00', 'FinishTime': '2022-12-30T04:12:35Z', 'FinishesAt': '2022-12-30T04:12:35Z'}
        06 = {dict: 2} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}
        07 = {dict: 2} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}
        08 = {dict: 2} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}
        09 = {dict: 2} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}
        10 = {dict: 2} {'Product': {'Id': 107, 'Amount': 80}, 'CraftTime': '00:30:00'}
        11 = {dict: 2} {'Product': {'Id': 104, 'Amount': 40}, 'CraftTime': '00:05:00'}
    """
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    player_factory = models.ForeignKey(
        to='bot.PlayerFactory',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    index = models.IntegerField(_('index'), null=False, blank=False, default=0)
    amount = models.IntegerField(_('amount'), null=False, blank=False, default=0)
    craft_time = models.IntegerField(_('CraftTime'), null=False, blank=False, default=0)
    finish_time = models.DateTimeField(_('FinishTime'), null=True, blank=False, default=None)
    finishes_at = models.DateTimeField(_('FinishesAt'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Player Factory Product Order'
        verbose_name_plural = 'Player Factory Product Orders'

    @classmethod
    def create_instance(cls, data, player_factory, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:

            idx = 0
            for order in data:
                product_id = order.get('Product', {}).pop('Id', None)
                product_amount = order.get('Product', {}).pop('Amount', None)
                craft_time = order.pop('CraftTime', {})
                finish_time = order.pop('FinishTime', None)
                finishes_at = order.pop('FinishesAt', None)
                idx += 1
                instance = PlayerFactoryProductOrder(
                    version_id=version_id,
                    player_factory=player_factory,
                    article_id=product_id,
                    index=idx,
                    amount=product_amount,
                    craft_time=convert_time(craft_time),
                    finish_time=convert_datetime(finish_time),
                    finishes_at=convert_datetime(finishes_at),
                    created=now, modified=now,
                )
                ret.append(instance)

        return ret


class PlayerJob(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    job_id = models.CharField(_('job id'), max_length=100, null=False, blank=False)

    job_location = models.ForeignKey(
        to='bot.JobLocation',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )

    job_level = models.IntegerField(_('CraftTime'), null=False, blank=False, default=0)
    sequence = models.IntegerField(_('Sequence'), null=True, blank=False, default=0)
    job_type = models.IntegerField(_('JobType'), null=False, blank=False, default=0)
    duration = models.IntegerField(_('Duration'), null=False, blank=False, default=0)
    condition_multiplier = models.IntegerField(_('ConditionMultiplier'), null=False, blank=False, default=0)
    reward_multiplier = models.IntegerField(_('RewardMultiplier'), null=False, blank=False, default=0)

    required_article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    required_amount = models.IntegerField(_('required_amount'), null=False, blank=False, default=0)
    current_article_amount = models.IntegerField(_('CurrentArticleAmount'), null=False, blank=False, default=0)

    reward = models.CharField(_('reward'), max_length=255, null=False, blank=False, default='')
    bonus = models.CharField(_('bonus'), max_length=255, null=False, blank=False, default='')

    expires_at = models.DateTimeField(_('ExpiresAt'), null=True, blank=False, default=None)

    requirements = models.CharField(_('reward'), max_length=255, null=False, blank=False, default='')
    unlock_at = models.DateTimeField(_('UnlocksAt'), null=True, blank=False, default=None)

    # 완료시간
    collectable_from = models.DateTimeField(_('CollectableFrom'), null=True, blank=False, default=None)
    # 보상 수집시간
    completed_at = models.DateTimeField(_('CompletedAt'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Player Job'
        verbose_name_plural = 'Player Jobs'

    @cached_property
    def current_guild_amount(self):
        return sum(PlayerLeaderBoardProgress.objects.filter(leader_board__player_job_id=self.id).values_list('progress', flat=True))

    def is_completed(self, init_data_server_datetime: datetime):
        return self.completed_at and self.completed_at <= init_data_server_datetime

    def is_collectable(self, init_data_server_datetime: datetime):
        return self.collectable_from and self.collectable_from <= init_data_server_datetime

    def is_expired(self, init_data_server_datetime: datetime):
        return self.expires_at and self.expires_at <= init_data_server_datetime


    @cached_property
    def str_rewards(self):
        """
            {"Items": [{"Id": 8, "Value": 4, "Amount": 6}, {"Id": 8, "Value": 1, "Amount": 140}]}
        :return:
        """
        if self.reward:
            json_data = json.loads(self.reward)
            items = json_data.get('Items')
            ret = []
            if items:
                for item in items:
                    _id = item.get('Id')
                    _value = item.get('Value')
                    _amount = item.get('Amount')
                    article = Article.objects.filter(id=_value).first()
                    if article:
                        ret.append(f'{article}-{_amount}개')
            return ' '.join(ret)
        return ''

    @cached_property
    def str_requirements(self):
        rarity = {
            1: 'common',
            2: 'rare',
            3: 'epic',
            4: 'legendary',
        }
        era = {
            1: 'STEAM',
            2: 'DIESEL',
            3: 'ELECTRON',
        }
        if self.requirements:
            json_data = json.loads(self.requirements)
            ret = []
            for cond in json_data:
                _type = cond.get('Type')
                _value = cond.get('Value')

                if _type == 'region':
                    ret.append(f'{_value} 지역')
                elif _type == 'rarity':
                    ret.append(f'{rarity.get(_value, "unknown")}')
                elif _type == 'power':
                    ret.append(f'{_value}칸 이상')
                elif _type == 'era':
                    ret.append(f'{era.get(_value, "unknown")}')
                elif _type == 'content_category':
                    ret.append(f'길드기차')
                else:
                    ret.append(f'unknown: type={_type}, value={_value}')
            return ' & '.join(ret)
        return ''

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for job in data:
                job_id = job.pop('Id', None)
                job_location_id = job.pop('JobLocationId', None)
                job_level = job.pop('JobLevel', None)
                sequence = job.pop('Sequence', None)
                job_type = job.pop('JobType', None)
                duration = job.pop('Duration', None)
                condition_multiplier = job.pop('ConditionMultiplier', None)
                reward_multiplier = job.pop('RewardMultiplier', None)
                required_article = job.pop('RequiredArticle', None)
                current_article_amount = job.pop('CurrentArticleAmount', None)
                reward = job.pop('Reward', None)
                bonus = job.pop('Bonus', None)
                requirements = job.pop('Requirements', None)
                unlock_at = job.pop('UnlocksAt', None)
                expires_at = job.pop('ExpiresAt', None)
                collectable_from = job.pop('CollectableFrom', None)
                completed_at = job.pop('CompletedAt', None)

                instance = PlayerJob(
                    version_id=version_id,
                    job_id=job_id,
                    job_location_id=job_location_id,
                    job_level=job_level,
                    sequence=sequence,
                    job_type=job_type,
                    duration=duration,
                    condition_multiplier=condition_multiplier,
                    reward_multiplier=reward_multiplier,
                    required_article_id=required_article.get('Id'),
                    required_amount=required_article.get('Amount'),
                    current_article_amount=current_article_amount,
                    reward=json.dumps(reward, separators=(',', ':')) if reward else '',
                    requirements=json.dumps(requirements, separators=(',', ':')) if requirements else '',
                    bonus=json.dumps(bonus, separators=(',', ':')) if bonus else '',
                    unlock_at=convert_datetime(unlock_at),
                    expires_at=convert_datetime(expires_at),
                    collectable_from=convert_datetime(collectable_from),
                    completed_at=convert_datetime(completed_at),
                    created=now, modified=now,
                )

                ret.append(instance)

        return ret


class PlayerContractList(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    contract_list_id = models.IntegerField(_('contract list id'), null=False, blank=False, default=0)
    available_to = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)
    next_replace_at = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)
    next_video_replace_at = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)
    next_video_rent_at = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)
    next_video_speed_up_at = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)
    expires_at = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Player Contract List'
        verbose_name_plural = 'Player Contract Lists'

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for cl in data:
                contract_list_id = cl.pop('ContractListId', None)
                available_to = cl.pop('AvailableTo', None)
                next_replace_at = cl.pop('NextReplaceAt', None)
                next_video_replace_at = cl.pop('NextVideoReplaceAt', None)
                next_video_rent_at = cl.pop('NextVideoRentAt', None)
                next_video_speed_up_at = cl.pop('NextVideoSpeedUpAt', None)
                expires_at = cl.pop('ExpiresAt', None)

                instance = PlayerContractList(
                    version_id=version_id,
                    contract_list_id=contract_list_id,
                    available_to=convert_datetime(available_to),
                    next_replace_at=convert_datetime(next_replace_at),
                    next_video_replace_at=convert_datetime(next_video_replace_at),
                    next_video_rent_at=convert_datetime(next_video_rent_at),
                    next_video_speed_up_at=convert_datetime(next_video_speed_up_at),
                    expires_at=convert_datetime(expires_at),
                    created=now, modified=now,
                )
                ret.append(instance)

        return ret


class PlayerContract(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    contract_list = models.ForeignKey(
        to='bot.PlayerContractList',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    """
'Slot' = {int} 18
'ContractListId' = {int} 100001
'Conditions' = {list: 1} [{'Id': 126, 'Amount': 547}]
'Reward' = {dict: 1} {'Items': [{'Id': 8, 'Value': 100009, 'Amount': 110}]}
'UsableFrom' = {str} '2023-01-09T05:25:44Z'
'AvailableFrom' = {str} '2022-12-05T12:00:00Z'
'AvailableTo' = {str} '2023-02-27T12:00:00Z'    
    """
    slot = models.IntegerField(_('slot'), null=False, blank=False, default=0)

    conditions = models.CharField(_('conditions'), max_length=255, null=False, blank=False, default='')
    reward = models.CharField(_('reward'), max_length=255, null=False, blank=False, default='')

    usable_from = models.DateTimeField(_('UsableFrom'), null=True, blank=False, default=None)
    available_from = models.DateTimeField(_('AvailableFrom'), null=True, blank=False, default=None)
    available_to = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)
    expires_at = models.DateTimeField(_('AvailableTo'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Player Contract'
        verbose_name_plural = 'Player Contracts'

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:

            cl = {
                o.contract_list_id: o for o in PlayerContractList.objects.filter(version_id=version_id).all()
            }

            for contract in data:
                slot = contract.pop('Slot', None)
                contract_list_id = contract.pop('ContractListId', None)
                conditions = contract.pop('Conditions', [])
                reward = contract.pop('Reward', {})
                usable_from = contract.pop('UsableFrom', None)
                available_from = contract.pop('AvailableFrom', None)
                available_to = contract.pop('AvailableTo', None)
                expires_at = contract.pop('ExpiresAt', None)

                instance = PlayerContract(
                    version_id=version_id,
                    contract_list_id=cl[contract_list_id].id,
                    slot=slot,
                    conditions=json.dumps(conditions, separators=(',', ':')) if conditions else '',
                    reward=json.dumps(reward, separators=(',', ':')) if reward else '',
                    usable_from=convert_datetime(usable_from),
                    available_from=convert_datetime(available_from),
                    available_to=convert_datetime(available_to),
                    expires_at=convert_datetime(expires_at),
                    created=now, modified=now,
                )
                ret.append(instance)

        return ret


class PlayerGift(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    job_id = models.CharField(_('job id'), max_length=100, null=False, blank=False)
    reward = models.CharField(_('reward'), max_length=255, null=False, blank=False, default='')
    gift_type = models.IntegerField(_('gift_type'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Player Gift'
        verbose_name_plural = 'Player Gifts'

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
                "Gifts":[
                    {
                        "Id":"8295a2de-d048-4228-ac02-e3d36c2d3b4a",
                        "Reward":{
                            "Items":[
                                {"Id":8,"Value":100000,"Amount":1326},
                                {"Id":8,"Value":100003,"Amount":792}
                            ]
                        },
                        "Type":6
                    }
                ]
            """
            for gift in data:
                _id = gift.pop('Id', None)
                reward = gift.pop('Reward', [])
                _type = gift.pop('Type', None)

                if _id and _type:
                    instance = PlayerGift(
                        version_id=version_id,
                        job_id=_id,
                        reward=json.dumps(reward, separators=(',', ':')) if reward else '',
                        gift_type=_type,
                        created=now, modified=now
                    )
                    ret.append(instance)

        return ret


class PlayerLeaderBoard(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    player_job = models.ForeignKey(
        to='bot.PlayerJob',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    leader_board_id = models.CharField(_('LeaderboardId'), max_length=50, blank=False, null=False, default='')
    leader_board_group_id = models.CharField(_('LeaderboardGroupId'), max_length=50, blank=False, null=False, default='')

    class Meta:
        verbose_name = 'Player Leader Board'
        verbose_name_plural = 'Player Leader Boards'

    @classmethod
    def create_instance(cls, data, player_job_id: int, version_id: int) -> Tuple[List, List]:
        ret = []
        sub_list = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for board in data:
                leader_board_id = board.pop('LeaderboardId', '')
                leader_board_group_id = board.pop('LeaderboardGroupId', '')
                progresses = board.pop('Progresses', [])
                rewards = board.pop('Rewards', [])

                leader_board = PlayerLeaderBoard(
                    version_id=version_id,
                    player_job_id=player_job_id,
                    leader_board_id=leader_board_id,
                    leader_board_group_id=leader_board_group_id,
                    created=now, modified=now,
                )
                ret.append(leader_board)
                sub_list += PlayerLeaderBoardProgress.create_instance(
                    progresses=progresses,
                    rewards=rewards,
                    leader_board=leader_board,
                )

        return ret, sub_list


class PlayerLeaderBoardProgress(BaseModelMixin, TimeStampedMixin):

    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    leader_board = models.ForeignKey(
        to='bot.PlayerLeaderBoard',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    player_id = models.IntegerField(_('PlayerId'), null=False, blank=False, default=0)
    avata_id = models.IntegerField(_('AvatarId'), null=False, blank=False, default=0)
    firebase_uid = models.CharField(_('FirebaseUid'), max_length=50, null=False, blank=False, default='')
    player_name = models.CharField(_('player_name'), max_length=50, null=False, blank=False, default='')
    progress = models.IntegerField(_('progress'), null=False, blank=False, default=0)
    position = models.IntegerField(_('position'), null=False, blank=False, default=0)
    last_updated_at = models.DateTimeField(_('LastUpdatedAt'), null=False, blank=False, default=0)
    reward_claimed = models.BooleanField(_('RewardClaimed'), null=False, blank=False, default=False)

    rewards = models.CharField(_('rewards'), max_length=255, null=False, blank=False, default='')

    """
    rewards:
        [{'Id': 8, 'Value': 100000, 'Amount': 402}, {'Id': 8, 'Value': 100003, 'Amount': 240}]    
    """
    class Meta:
        verbose_name = 'Player Leader Board Progress'
        verbose_name_plural = 'Player Leader Board Progresses'

    @classmethod
    def create_instance(cls, progresses, rewards, leader_board: PlayerLeaderBoard) -> List:
        ret = []
        now = timezone.now()
        if progresses and rewards and leader_board:
            for progress, reward in zip(progresses, rewards):
                player_id = progress.pop('PlayerId', None)
                avata_id = progress.pop('AvatarId', None)
                firebase_uid = progress.pop('FirebaseUid', None)
                _ = progress.pop('LeaderboardGroupId', None)
                player_name = progress.pop('PlayerName', None)
                progress_val = progress.pop('Progress', None)
                position = progress.pop('Position', None)
                last_updated_at = progress.pop('LastUpdatedAt', None)
                reward_claimed = progress.pop('RewardClaimed', None)
                instance = PlayerLeaderBoardProgress(
                    version_id=leader_board.version_id,
                    leader_board=leader_board,
                    player_id=player_id,
                    avata_id=avata_id,
                    firebase_uid=firebase_uid,
                    player_name=player_name,
                    progress=progress_val,
                    position=position,
                    last_updated_at=last_updated_at,
                    reward_claimed=reward_claimed,
                    rewards=json.dumps(reward, separators=(',', ':')) if reward else '',
                    created=now, modified=now,
                )
                ret.append(instance)

        return ret


class PlayerTrain(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    instance_id = models.IntegerField(_('instance_id'), null=False, blank=False, default=0)
    train = models.ForeignKey(
        to='bot.Train',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    level = models.IntegerField(_('level'), null=False, blank=False, default=0)
    region = models.IntegerField(_('region'), null=True, blank=True, default=None)

    has_route = models.BooleanField(_('has route'), null=False, blank=True, default=False)
    route_type = models.CharField(_('route_type'), max_length=20, null=True, blank=True, default=None)
    route_definition_id = models.IntegerField(_('route_definition_id'), null=True, blank=True, default=None)
    route_departure_time = models.DateTimeField(_('route_departure_time'), null=True, blank=True, default=None)
    route_arrival_time = models.DateTimeField(_('route_arrival_time'), null=True, blank=True, default=None)

    has_load = models.BooleanField(_('has load'), null=False, blank=True, default=False)
    load = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=True, blank=False, db_constraint=False, default=None
    )
    load_amount = models.IntegerField(_('load amount'), null=False, blank=False, default=0)

    """
            "Route": {
              "RouteType": "destination",
              "DefinitionId": 403,
              "DepartureTime": "2022-12-30T06:28:33Z",
              "ArrivalTime": "2022-12-30T06:33:33Z"
            },
            "TrainLoad": {
              "Id": 122,
              "Amount": 79
            }
    """
    class Meta:
        verbose_name = 'Player Train'
        verbose_name_plural = 'Player Trains'

    @cached_property
    def capacity(self):
        lv = TrainLevel.objects.filter(train_level=self.level).first()
        if lv:
            powers = lv.power.split(';')
            return int(powers[self.train.rarity - 1])

    @cached_property
    def max_capacity(self):
        lv = TrainLevel.objects.filter(train_level=self.train.max_level).first()
        if lv:
            powers = lv.power.split(';')
            return int(powers[self.train.rarity - 1])

    def get_region(self):
        return self.region or self.train.region

    def get_region_id(self):
        val = self.get_region()
        mapping = {
            1: 101,
            2: 202,
            3: 302,
            4: 401,
        }
        return mapping.get(val) or val

    def is_working(self, init_data_server_datetime):
        if self.route_arrival_time and self.route_arrival_time >= init_data_server_datetime:
            return True
        return False

    def is_idle(self, init_data_server_datetime):
        return not self.is_working(init_data_server_datetime)

    def __str__(self):
        return self.str_dump()

    def str_dump(self):
        ret = []
        ret.append(f'#{self.instance_id:3d}')
        ret.append(f'[{self.capacity:3d}]')
        ret.append(f'{self.train.get_era_display():10s}')
        ret.append(f'{self.train.get_rarity_display():10s}')
        ret.append(f'{self.train.asset_name:25s}')

        return ' '.join(ret)

    @property
    def is_destination_route(self):
        return self.route_type == 'destination'

    @property
    def is_job_route(self):
        return self.route_type == 'job'

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:

            for train in data:
                instance_id = train.pop('InstanceId', None)
                definition_id = train.pop('DefinitionId', None)
                level = train.pop('Level', None)
                route = train.pop('Route', None)
                region = train.pop('Region', None)
                load = train.pop('TrainLoad', None)

                has_route = True if route else False
                route_type = route.pop('RouteType', None) if route else None
                route_definition_id = route.pop('DefinitionId', None) if route else None
                route_departure_time = route.pop('DepartureTime', None) if route else None
                route_arrival_time = route.pop('ArrivalTime', None) if route else None

                has_load = True if load else False
                load_id = load.pop('Id', None) if load else None
                load_amount = load.pop('Amount', None) if load else 0

                instance = PlayerTrain(
                    version_id=version_id,
                    instance_id=instance_id,
                    train_id=definition_id,
                    level=level,
                    region=region,
                    has_route=has_route,
                    route_type=route_type,
                    route_definition_id=route_definition_id,
                    route_departure_time=convert_datetime(route_departure_time),
                    route_arrival_time=convert_datetime(route_arrival_time),
                    has_load=has_load,
                    load_id=load_id,
                    load_amount=load_amount,
                    created=now, modified=now,
                )

                ret.append(instance)

        return ret


class PlayerWarehouse(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    amount = models.IntegerField(_('amount'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Player Warehouse'
        verbose_name_plural = 'Player Warehouses'

    def __str__(self):
        return f'#{self.article_id} {self.article} - {self.amount}개'

    @classmethod
    def create_instance(cls, data, version_id: int) -> List:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:

            for article in data:
                instance = PlayerWarehouse(
                    version_id=version_id,
                    article_id=article.pop('Id', None),
                    amount=article.pop('Amount', None),
                    created=now, modified=now
                )
                ret.append(instance)

        return ret


class PlayerWhistle(BaseModelMixin, TimeStampedMixin):
    """
        'Category': 1,
        'Position': 3,
        'SpawnTime': '2022-12-29T10:32:46Z',
        'CollectableFrom': '2022-12-29T10:32:46Z',
        'Reward': {
            'Items': [
                {'Id': 8, 'Value': 2, 'Amount': 1}
            ]
        },
        'IsForVideoReward': True,
        'ExpiresAt': '2999-12-31T00:00:00Z'
    """
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    category = models.IntegerField(_('category'), null=False, blank=False, default=0)
    position = models.IntegerField(_('position'), null=False, blank=False, default=0)
    spawn_time = models.DateTimeField(_('SpawnTime'), null=True, blank=True, default=None)
    collectable_from = models.DateTimeField(_('CollectableFrom'), null=True, blank=True, default=None)

    is_for_video_reward = models.BooleanField(_('IsForVideoReward'), null=True, blank=True, default=None)
    expires_at = models.DateTimeField(_('ExpiresAt'), null=True, blank=True, default=None)

    class Meta:
        verbose_name = 'Player Whistle'
        verbose_name_plural = 'Player Whistles'

    def is_collectable(self, init_data_server_datetime) -> bool:
        if self.spawn_time and self.spawn_time < init_data_server_datetime:
            return False
        if self.collectable_from and self.collectable_from < init_data_server_datetime:
            return False
        if self.expires_at and self.expires_at >= init_data_server_datetime:
            return False
        if self.is_for_video_reward:
            return False
        return True

    @classmethod
    def create_instance(cls, data, version_id: int) -> Tuple[List, List]:
        ret = []
        sub_ret = []

        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:

            for whistle in data:
                category = whistle.pop('Category', None)
                position = whistle.pop('Position', None)
                spawn_time = whistle.pop('SpawnTime', None)
                collectable_from = whistle.pop('CollectableFrom', None)
                reward = whistle.pop('Reward', None)
                is_for_video_reward = whistle.pop('IsForVideoReward', None)
                expires_at = whistle.pop('ExpiresAt', None)

                player_whistle = PlayerWhistle(
                    version_id=version_id,
                    category=category,
                    position=position,
                    spawn_time=convert_datetime(spawn_time),
                    collectable_from=convert_datetime(collectable_from),
                    is_for_video_reward=is_for_video_reward,
                    expires_at=convert_datetime(expires_at),
                    created=now, modified=now,
                )
                sub_ret += PlayerWhistleItem.create_instance(
                    data=(reward.get('Items') or []) if reward else None,
                    player_whistle=player_whistle,
                    version_id=version_id,
                )
                ret.append(player_whistle)

        return ret, sub_ret


class PlayerWhistleItem(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    player_whistle = models.ForeignKey(
        to='bot.PlayerWhistle',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    value = models.IntegerField(_('value'), null=False, blank=False, default=0)
    amount = models.IntegerField(_('amount'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Player Whistle Item'
        verbose_name_plural = 'Player Whistle Items'

    @classmethod
    def create_instance(cls, data, player_whistle, version_id: int) -> List:
        ret = []

        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for item in data:
                item_id = item.get('Id')
                value = item.get('Value')
                amount = item.get('Amount')
                instance = PlayerWhistleItem(
                    version_id=version_id,
                    player_whistle=player_whistle,
                    article_id=item_id,
                    value=value,
                    amount=amount,
                    created=now, modified=now,
                )
                ret.append(instance)

        return ret
