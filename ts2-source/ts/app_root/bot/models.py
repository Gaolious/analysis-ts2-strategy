import json
from decimal import Decimal
from functools import cached_property

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin


class AbstractContentCategory(models.Model):

    content_category = models.IntegerField(_('content category'), null=False, blank=False, default=0)
    class Meta:
        abstract = True


def str_content_category(content_category: int):
    content_category = int(content_category)
    mapping = {
        1: '기본',
        2: '이벤트',
        3: '길드',
    }
    return mapping.get(content_category, 'Unknown')


class Definition(BaseModelMixin, TimeStampedMixin):
    version = models.CharField(_('version'), max_length=20, null=False, blank=False)
    checksum = models.CharField(_('checksum'), max_length=50, null=False, blank=False)
    url = models.URLField(_('download url'), null=False, blank=False)
    download_path = models.CharField(_('checksum'), max_length=200, null=False, blank=False)

    class Meta:
        verbose_name = 'Definition'
        verbose_name_plural = 'Definitions'


class Article(BaseModelMixin, TimeStampedMixin):
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
    content_category = models.IntegerField(_('content category'), null=False, blank=False, default=0)
    sprite = models.CharField(_('sprite id'), max_length=255, null=True, blank=False)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return f'[{self.sprite}/{str_content_category(self.content_category)}]'  #/type:{self.type}/event:{self.event}]'


class Factory(BaseModelMixin, TimeStampedMixin):
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
    content_category = models.IntegerField(_('content category'), null=False, blank=False, default=0)
    asset_name = models.CharField(_('asset_name'), max_length=255, null=False, blank=False)
    sprite = models.CharField(_('sprite id'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Factory'
        verbose_name_plural = 'Factories'

    def __str__(self):
        return f'[{self.sprite}/{str_content_category(self.content_category)}]'


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


class Train(BaseModelMixin, TimeStampedMixin):
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
    content_category = models.IntegerField(_('content_category'), null=False, blank=False, default=0)
    reward = models.BooleanField(_('reward'), null=False, blank=False, default=False)
    region = models.IntegerField(_('region'), null=False, blank=False, default=0)
    rarity = models.IntegerField(_('rarity'), null=False, blank=False, default=0)
    max_level = models.IntegerField(_('max_level'), null=False, blank=False, default=0)
    era = models.IntegerField(_('era'), null=False, blank=False, default=0)
    asset_name = models.CharField(_('asset_name'), max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Train'
        verbose_name_plural = 'Trains'


class Region(BaseModelMixin, TimeStampedMixin):
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
    content_category = models.IntegerField(_('content category'), null=False, blank=False, default=0)
    asset_name = models.CharField(_('sprite id'), max_length=255, null=False, blank=False)
    gold_amount_coefficient = models.IntegerField(_('gold_amount_coefficient'), null=False, blank=False, default=0)
    train_upgrade_price_coefficient = models.DecimalField(_('train_upgrade_price_coefficient'), max_digits=30, decimal_places=10, null=False, blank=True, default=Decimal('0.0'))
    city_currency_coefficient = models.IntegerField(_('city_currency_coefficient'), null=False, blank=False, default=0)
    ordering = models.IntegerField(_('ordering'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'


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
        to='bot.region',
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

    class Meta:
        verbose_name = 'Building'
        verbose_name_plural = 'Buildings'


class PlayerDestination(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    location_id = models.IntegerField(_('location_id'), null=True, blank=False)
    definition_id = models.IntegerField(_('definition_id'), null=True, blank=False)
    train_limit_count = models.IntegerField(_('train_limit_count'), null=True, blank=False)
    train_limit_refresh_time = models.DateTimeField(_('train_limit_refresh_time'), null=True, blank=False)
    train_limit_refresh_at = models.DateTimeField(_('train_limit_refresh_at'), null=True, blank=False)
    multiplier = models.IntegerField(_('multiplier'), null=True, blank=False, default='')

    class Meta:
        verbose_name = 'Building'
        verbose_name_plural = 'Buildings'


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


class PlayerJob(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    job_id = models.CharField(_('job id'), max_length=100, null=False, blank=False)

    location = models.ForeignKey(
        to='bot.Location',
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
    bonus = models.CharField(_('reward'), max_length=255, null=False, blank=False, default='')

    requirements = models.CharField(_('reward'), max_length=255, null=False, blank=False, default='')
    unlock_at = models.DateTimeField(_('UnlocksAt'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Player Job'
        verbose_name_plural = 'Player Jobs'

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

class PlayerTrain(BaseModelMixin, TimeStampedMixin):
    version = models.ForeignKey(
        to='bot.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    instance_id = models.IntegerField(_('instance_id'), null=False, blank=False, default=0)
    definition_id = models.IntegerField(_('definition_id'), null=False, blank=False, default=0)
    level = models.IntegerField(_('level'), null=False, blank=False, default=0)

    has_route = models.BooleanField(_('has route'), null=False, blank=True, default=False)
    route_type = models.CharField(_('route_type'), max_length=20, null=True, blank=True, default=None)
    route_definition_id = models.IntegerField(_('route_definition_id'), null=True, blank=True, default=None)
    route_departure_time = models.DateTimeField(_('route_departure_time'), null=True, blank=True, default=None)
    route_arrival_time = models.DateTimeField(_('route_arrival_time'), null=True, blank=True, default=None)
    """
'Route': {'RouteType': 'destination', 
'DefinitionId': 151, 'DepartureTime': '2022-12-27T10:04:46Z', 'ArrivalTime': '2022-12-27T10:05:16Z'}}
    """
    class Meta:
        verbose_name = 'Player Train'
        verbose_name_plural = 'Player Trains'


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
        return f'[{self.article} - {self.amount}개]'


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