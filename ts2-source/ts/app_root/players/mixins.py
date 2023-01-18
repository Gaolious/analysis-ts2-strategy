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


class BaseRunMixin(models.Model):
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
    command_no = models.IntegerField(_('Command No'), null=False, blank=True, default=1)

    init_data_request_datetime = models.DateTimeField(_('init_data_request_datetime'), null=True, blank=False,
                                                      default=None)
    init_data_response_datetime = models.DateTimeField(_('init_data_response_datetime'), null=True, blank=False,
                                                       default=None)
    init_data_server_datetime = models.DateTimeField(_('init_data_server_datetime'), null=True, blank=False,
                                                     default=None)

    class Meta:
        abstract = True


class BaseVersionMixin(models.Model):
    version = models.ForeignKey(
        to='players.RunVersion',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )

    class Meta:
        abstract = True


class PlayerBuildingMixin(BaseVersionMixin):
    instance_id = models.IntegerField(_('instance id'), null=True, blank=False)
    definition_id = models.IntegerField(_('instance id'), null=True, blank=False)
    rotation = models.IntegerField(_('instance id'), null=True, blank=False)
    level = models.IntegerField(_('instance id'), null=True, blank=False)
    upgrade_task = models.CharField(_('upgrade task'), max_length=255, null=True, blank=False, default='')
    parcel_number = models.IntegerField(_('parcel_number'), null=True, blank=False, default=None)

    class Meta:
        abstract = True

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
                instance = cls(
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

    @property
    def is_placed(self):
        return True if self.parcel_number else False


class PlayerDestinationMixin(BaseVersionMixin):
    location = models.ForeignKey(
        to='server.TSLocation',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    definition = models.ForeignKey(
        to='server.TSDestination',
        on_delete=models.DO_NOTHING, related_name='+', null=False, blank=False, db_constraint=False
    )
    train_limit_count = models.IntegerField(_('train_limit_count'), null=True, blank=False)
    train_limit_refresh_time = models.DateTimeField(_('train_limit_refresh_time'), null=True, blank=False)
    train_limit_refresh_at = models.DateTimeField(_('train_limit_refresh_at'), null=True, blank=False)
    multiplier = models.IntegerField(_('multiplier'), null=True, blank=False, default='')

    class Meta:
        abstract = True

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

                instance = cls(
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