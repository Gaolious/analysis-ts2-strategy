from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin


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
    multiplier = models.IntegerField(_('multiplier'), max_length=255, null=True, blank=False, default='')

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
    job_level = models.IntegerField(_('CraftTime'), null=False, blank=False, default=0)
    sequence = models.IntegerField(_('Sequence'), null=False, blank=False, default=0)
    job_type = models.IntegerField(_('JobType'), null=False, blank=False, default=0)
    duration = models.IntegerField(_('Duration'), null=False, blank=False, default=0)
    condition_multiplier = models.IntegerField(_('ConditionMultiplier'), null=False, blank=False, default=0)
    reward_multiplier = models.IntegerField(_('RewardMultiplier'), null=False, blank=False, default=0)
    current_article_amount = models.IntegerField(_('CurrentArticleAmount'), null=False, blank=False, default=0)
    unlock_at = models.DateTimeField(_('UnlocksAt'), null=True, blank=False, default=None)

    class Meta:
        verbose_name = 'Player Job'
        verbose_name_plural = 'Player Jobs'


class PlayerJobRequirements(BaseModelMixin, TimeStampedMixin):
    """
      {
        "Type": "region",
        "Value": 1
      },
      {
        "Type": "rarity",
        "Value": 2
      },
      {
        "Type": "power",
        "Value": 30
      }
      {
        "Type": "era",
        "Value": 1
      }

    - "region" / 1, "rarity" / 2, "power" / 30
        지역 1, 레어기차, 30칸 이상
    - "region" / 2, "rarity" / 4
        지역 2 / legendary
    - "region" / 4, "era" / 1
        지역 4 / steam
    - "region" / 4, "era" / 3
        지역 4 / electronic
    - "region" / 4, "content_category" / 3
        지역 4 / union 기차.

    DIESEL : era=2 ?
    """
    job = models.ForeignKey(
        to='bot.PlayerJob',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    type = models.CharField(_('requirement type'), max_length=50, null=False, blank=False)
    value = models.IntegerField(_('requirement value'), null=False, blank=False)

    class Meta:
        verbose_name = 'Player Job Requirement'
        verbose_name_plural = 'Player Job Requirements'


class PlayerJobRequiredArticle(BaseModelMixin, TimeStampedMixin):
    job = models.ForeignKey(
        to='bot.PlayerJob',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    amount = models.IntegerField(_('amount'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Player Job Required Article'
        verbose_name_plural = 'Player Job Required Articles'


class PlayerJobReward(BaseModelMixin, TimeStampedMixin):
    job = models.ForeignKey(
        to='bot.PlayerJob',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    article = models.ForeignKey(
        to='bot.Article',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    value = models.IntegerField(_('value'), null=False, blank=False, default=0)
    amount = models.IntegerField(_('amount'), null=False, blank=False, default=0)

    class Meta:
        verbose_name = 'Player Job Reward'
        verbose_name_plural = 'Player Job Rewards'
#
# class PlayerTrain(BaseModelMixin, TimeStampedMixin):
#     pass