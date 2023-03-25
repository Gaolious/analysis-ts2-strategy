import datetime
import json
from functools import cached_property
from typing import List, Tuple, Dict, Optional, Type

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_root.servers.mixins import CHOICE_RARITY, CHOICE_ERA, ContentCategoryMixin
from core.utils import convert_time, convert_datetime

BUFFER_TIME = datetime.timedelta(seconds=5)


class BaseVersionMixin(models.Model):
    version = models.ForeignKey(
        to="servers.RunVersion",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )

    @classmethod
    def sub_model(cls) -> Optional[Type["BaseVersionMixin"]]:
        return None

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        return [], []

    class Meta:
        abstract = True


class PlayerBuildingMixin(BaseVersionMixin):
    instance_id = models.IntegerField(_("instance id"), null=True, blank=False)
    definition_id = models.IntegerField(_("instance id"), null=True, blank=False)
    rotation = models.IntegerField(_("instance id"), null=True, blank=False)
    level = models.IntegerField(_("instance id"), null=True, blank=False)
    upgrade_task = models.CharField(
        _("upgrade task"), max_length=255, null=True, blank=False, default=""
    )
    parcel_number = models.IntegerField(
        _("parcel_number"), null=True, blank=False, default=None
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
                "UpgradeTask": {
                    "AvailableFrom": "2023-01-14T17:44:00Z",
                    "RequiredArticles": [
                        {
                            "Id": 104,
                            "Amount": 290
                        },
                        {
                            "Id": 122,
                            "Amount": 194
                        }
                    ]
                },
                "InstanceId": 15,
                "DefinitionId": 9,
                "ParcelNumber": 4,
                "Rotation": 90,
                "Level": 104
            },
            {
                "InstanceId": 16,
                "DefinitionId": 10,
                "ParcelNumber": 11,
                "Rotation": 0,
                "Level": 150
            },
            {
                "InstanceId": 12,
                "DefinitionId": 6,
                "Rotation": 0,
                "Level": 11
            },
            """
            for bld in data:
                instance_id = bld.get("InstanceId")
                definition_id = bld.get("DefinitionId")
                rotation = bld.get("Rotation")
                level = bld.get("Level")
                upgrade_task = bld.get("UpgradeTask")
                parcel_number = bld.get("ParcelNumber")
                instance = cls(
                    version_id=version_id,
                    instance_id=instance_id or 0,
                    definition_id=definition_id or 0,
                    rotation=rotation or 0,
                    level=level or 0,
                    parcel_number=parcel_number or 0,
                    upgrade_task=json.dumps(upgrade_task, separators=(",", ":"))
                    if upgrade_task
                    else "",
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    @property
    def is_placed(self):
        return True if self.parcel_number else False

    @cached_property
    def _upgrade_task_json(self) -> Dict:
        if self.upgrade_task:
            return json.loads(self.upgrade_task)
        else:
            return {}

    @cached_property
    def requirements_to_dict(self) -> Dict[int, int]:
        json_data = self._upgrade_task_json
        ret = {}
        if json_data:
            for cond in json_data.get("RequiredArticles", []):
                _article_id = cond.get("Id")
                _amount = cond.get("Amount")
                ret.setdefault(_article_id, 0)
                ret[_article_id] += _amount
        return ret

    @cached_property
    def available_from(self) -> datetime:
        json_data = json.loads(self.upgrade_task)
        if json_data:
            return convert_datetime(json_data.get("AvailableFrom"))

    def __str__(self):
        return f"""#{self.instance_id:3d} / Lv. {self.level:3d} / parcel {self.parcel_number:2d} / {self.upgrade_task}"""


class PlayerDestinationMixin(BaseVersionMixin):
    location = models.ForeignKey(
        to="servers.TSLocation",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    definition = models.ForeignKey(
        to="servers.TSDestination",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    train_limit_count = models.IntegerField(
        _("train_limit_count"), null=True, blank=False
    )
    train_limit_refresh_time = models.DateTimeField(
        _("train_limit_refresh_time"), null=True, blank=False
    )
    train_limit_refresh_at = models.DateTimeField(
        _("train_limit_refresh_at"), null=True, blank=False
    )
    multiplier = models.IntegerField(
        _("multiplier"), null=True, blank=False, default=""
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
                "LocationId": 152,
                "DefinitionId": 152,
                "TrainLimitCount": 0,
                "TrainLimitRefreshTime": "2023-01-15T06:48:38Z",
                "TrainLimitRefreshesAt": "2023-01-15T06:48:38Z",
                "Multiplier": 0
            },

            """
            for row in data:
                location_id = row.get("LocationId")
                definition_id = row.get("DefinitionId")
                train_limit_count = row.get("TrainLimitCount")
                train_limit_refresh_time = row.get("TrainLimitRefreshTime")
                train_limit_refresh_at = row.get("TrainLimitRefreshesAt")
                multiplier = row.get("Multiplier")

                instance = cls(
                    version_id=version_id,
                    location_id=location_id or 0,
                    definition_id=definition_id or 0,
                    train_limit_count=train_limit_count or 0,
                    train_limit_refresh_time=convert_datetime(train_limit_refresh_time),
                    train_limit_refresh_at=convert_datetime(train_limit_refresh_at),
                    multiplier=multiplier or 0,
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    def next_event_datetime(
        self, init_data_request_datetime, init_data_server_datetime, now
    ) -> datetime:
        diff = init_data_request_datetime - init_data_server_datetime
        next_event = (self.train_limit_refresh_at + diff).astimezone(settings.KST)
        return next_event

    def remain_seconds(
        self, init_data_request_datetime, init_data_server_datetime, now
    ) -> float:
        diff = init_data_request_datetime - init_data_server_datetime
        next_event = (self.train_limit_refresh_at + diff).astimezone(settings.KST)
        remain = next_event - now
        return remain.total_seconds()

    def is_available(self, now) -> bool:
        if self.train_limit_refresh_at and self.train_limit_refresh_at < now:
            return True
        return False


class PlayerFactoryMixin(BaseVersionMixin):
    factory = models.ForeignKey(
        to="servers.TSFactory",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    slot_count = models.IntegerField(_("slot count"), null=False, blank=False)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        sub_ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """

            "Factories": [
              {
                "DefinitionId": 1,
                "SlotCount": 6,
                "ProductOrders": [
                  {
                    "Product": {
                      "Id": 107,
                      "Amount": 80
                    },
                    "CraftTime": "00:30:00",
                    "FinishTime": "2023-01-06T11:40:28Z",
                    "FinishesAt": "2023-01-06T11:40:28Z"
                  },
                  {
                    "Product": {
                      "Id": 107,
                      "Amount": 80
                    },
                    "CraftTime": "00:30:00",
                    "FinishTime": "2023-01-13T14:16:54Z",
                    "FinishesAt": "2023-01-13T14:16:54Z"
                  },
                  {
                    "Product": {
                      "Id": 104,
                      "Amount": 40
                    },
                    "CraftTime": "00:05:00",
                    "FinishTime": "2023-01-15T05:23:21Z",
                    "FinishesAt": "2023-01-15T05:23:21Z"
                  },
                  {
                    "Product": {
                      "Id": 107,
                      "Amount": 80
                    },
                    "CraftTime": "00:30:00",
                    "FinishTime": "2023-01-15T07:07:00Z",
                    "FinishesAt": "2023-01-15T07:07:00Z"
                  },
                  {
                    "Product": {
                      "Id": 104,
                      "Amount": 40
                    },
                    "CraftTime": "00:05:00",
                    "FinishTime": "2023-01-15T07:24:03Z",
                    "FinishesAt": "2023-01-15T07:24:03Z"
                  },
                  {
                    "Product": {
                      "Id": 104,
                      "Amount": 40
                    },
                    "CraftTime": "00:05:00",
                    "FinishTime": "2023-01-15T07:29:03Z",
                    "FinishesAt": "2023-01-15T07:29:03Z"
                  }
                ]
              },
            """
            for factory in data:
                definition_id = factory.pop("DefinitionId", None)
                slot_count = factory.pop("SlotCount", None)

                player_factory = cls(
                    version_id=version_id,
                    factory_id=definition_id,
                    slot_count=slot_count,
                    created=now,
                    modified=now,
                )
                ret.append(player_factory)

                sub, _ = cls.sub_model().create_instance(
                    data=factory.get("ProductOrders", []),
                    player_factory=player_factory,
                    version_id=version_id,
                )
                sub_ret += sub

        return ret, sub_ret


class PlayerFactoryProductOrderMixin(BaseVersionMixin):
    player_factory = models.ForeignKey(
        to="players.PlayerFactory",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    article = models.ForeignKey(
        to="servers.TSArticle",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    index = models.IntegerField(_("index"), null=False, blank=False, default=0)
    amount = models.IntegerField(_("amount"), null=False, blank=False, default=0)
    craft_time = models.IntegerField(_("CraftTime"), null=False, blank=False, default=0)
    finish_time = models.DateTimeField(
        _("FinishTime"), null=True, blank=False, default=None
    )
    finishes_at = models.DateTimeField(
        _("FinishesAt"), null=True, blank=False, default=None
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
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
            idx = 0
            for order in data:
                product_id = order.get("Product", {}).pop("Id", None)
                product_amount = order.get("Product", {}).pop("Amount", None)
                craft_time = order.pop("CraftTime", {})
                finish_time = order.pop("FinishTime", None)
                finishes_at = order.pop("FinishesAt", None)
                idx += 1
                ret.append(
                    cls(
                        version_id=version_id,
                        player_factory=kwargs.get("player_factory"),
                        article_id=product_id,
                        index=idx,
                        amount=product_amount,
                        craft_time=convert_time(craft_time),
                        finish_time=convert_datetime(finish_time),
                        finishes_at=convert_datetime(finishes_at),
                        created=now,
                        modified=now,
                    )
                )

        return ret, []

    def is_completed(self, now) -> bool:
        if self.finish_time and self.finish_time <= now:
            return True
        return False

    def is_processing(self, now) -> bool:
        if self.finish_time and now < self.finish_time <= now + datetime.timedelta(
            seconds=self.craft_time
        ):
            return True
        return False

    def is_waiting(self, now) -> bool:
        if (
            not self.finish_time
            or now + datetime.timedelta(seconds=self.craft_time) < self.finish_time
        ):
            return True
        return False


class PlayerJobMixin(BaseVersionMixin):
    job_id = models.CharField(_("job id"), max_length=100, null=False, blank=False)

    job_location = models.ForeignKey(
        to="servers.TSJobLocation",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )

    job_level = models.IntegerField(_("CraftTime"), null=False, blank=False, default=0)
    sequence = models.IntegerField(_("Sequence"), null=True, blank=False, default=0)
    job_type = models.IntegerField(_("JobType"), null=False, blank=False, default=0)
    duration = models.IntegerField(_("Duration"), null=False, blank=False, default=0)
    condition_multiplier = models.IntegerField(
        _("ConditionMultiplier"), null=False, blank=False, default=0
    )
    reward_multiplier = models.IntegerField(
        _("RewardMultiplier"), null=False, blank=False, default=0
    )

    required_article = models.ForeignKey(
        to="servers.TSArticle",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    required_amount = models.IntegerField(
        _("required_amount"), null=False, blank=False, default=0
    )
    current_article_amount = models.IntegerField(
        _("CurrentArticleAmount"), null=False, blank=False, default=0
    )

    reward = models.CharField(
        _("reward"), max_length=255, null=False, blank=False, default=""
    )
    bonus = models.CharField(
        _("bonus"), max_length=255, null=False, blank=False, default=""
    )

    expires_at = models.DateTimeField(
        _("ExpiresAt"), null=True, blank=False, default=None
    )

    requirements = models.CharField(
        _("reward"), max_length=255, null=False, blank=False, default=""
    )
    unlock_at = models.DateTimeField(
        _("UnlocksAt"), null=True, blank=False, default=None
    )

    # 완료시간
    collectable_from = models.DateTimeField(
        _("CollectableFrom"), null=True, blank=False, default=None
    )
    # 보상 수집시간
    completed_at = models.DateTimeField(
        _("CompletedAt"), null=True, blank=False, default=None
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
              "Id": "723b7b26-2101-422e-a75c-136b299fc329",
              "JobLocationId": 166,
              "JobLevel": 1,
              "JobType": 1,
              "Duration": 3600,
              "ConditionMultiplier": 1,
              "RewardMultiplier": 1,
              "RequiredArticle": {
                "Id": 105,
                "Amount": 80
              },
              "CurrentArticleAmount": 70,
              "Reward": {
                "Items": [
                  {
                    "Id": 8,
                    "Value": 4,
                    "Amount": 6
                  },
                  {
                    "Id": 8,
                    "Value": 1,
                    "Amount": 140
                  }
                ]
              },
              "Bonus": {
                "Reward": {
                  "Items": []
                }
              },
              "Requirements": [
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
              ],
              "UnlocksAt": "2022-08-13T02:22:19Z"
            },
            """
            for job in data:
                job_id = job.pop("Id", None)
                job_location_id = job.pop("JobLocationId", None)
                job_level = job.pop("JobLevel", None)
                sequence = job.pop("Sequence", None)
                job_type = job.pop("JobType", None)
                duration = job.pop("Duration", None)
                condition_multiplier = job.pop("ConditionMultiplier", 1)
                reward_multiplier = job.pop("RewardMultiplier", 1)
                required_article = job.pop("RequiredArticle", None)
                current_article_amount = job.pop("CurrentArticleAmount", None)
                reward = job.pop("Reward", None)
                bonus = job.pop("Bonus", None)
                requirements = job.pop("Requirements", None)
                unlock_at = job.pop("UnlocksAt", None)
                expires_at = job.pop("ExpiresAt", None)
                collectable_from = job.pop("CollectableFrom", None)
                completed_at = job.pop("CompletedAt", None)
                closed_at = job.pop("ClosedAt", None)
                if closed_at:
                    continue

                if not collectable_from:
                    collectable_from = job.pop("CompletableFrom", None)
                if not completed_at:
                    completed_at = job.pop("FinishedAt", None)

                ret.append(
                    cls(
                        version_id=version_id,
                        job_id=job_id,
                        job_location_id=job_location_id,
                        job_level=job_level,
                        sequence=sequence,
                        job_type=job_type,
                        duration=duration,
                        condition_multiplier=condition_multiplier,
                        reward_multiplier=reward_multiplier,
                        required_article_id=required_article.get("Id"),
                        required_amount=required_article.get("Amount"),
                        current_article_amount=current_article_amount,
                        reward=json.dumps(reward, separators=(",", ":"))
                        if reward
                        else "",
                        requirements=json.dumps(requirements, separators=(",", ":"))
                        if requirements
                        else "",
                        bonus=json.dumps(bonus, separators=(",", ":")) if bonus else "",
                        unlock_at=convert_datetime(unlock_at),
                        expires_at=convert_datetime(expires_at),
                        collectable_from=convert_datetime(collectable_from),
                        completed_at=convert_datetime(completed_at),
                        created=now,
                        modified=now,
                    )
                )

        return ret, []

    # @cached_property
    # def current_guild_amount(self):
    #     return sum(PlayerLeaderBoardProgress.objects.filter(leader_board__player_job_id=self.id).values_list('progress', flat=True))

    @property
    def is_event_job(self) -> bool:
        if self.job_location.region.is_event:
            return True
        return False

    @property
    def is_union_job(self) -> bool:
        if self.job_location.region.is_union:
            return True
        return False

    @property
    def is_story_job(self) -> bool:
        if self.job_location.region.is_basic and self.job_type != 1:
            return True
        return False

    @property
    def is_side_job(self) -> bool:
        if self.job_location.region.is_basic and self.job_type == 1:
            return True
        return False

    def is_completed(self, init_data_server_datetime: datetime) -> bool:
        if self.completed_at and self.completed_at <= init_data_server_datetime:
            return True
        return False

    def is_collectable(self, init_data_server_datetime: datetime) -> bool:
        if self.collectable_from and self.collectable_from <= init_data_server_datetime:
            return True
        return False

    def is_expired(self, init_data_server_datetime: datetime) -> bool:
        if self.expires_at and self.expires_at <= init_data_server_datetime:
            return True
        return False

    @cached_property
    def requirements_to_dict(self) -> Dict[str, List]:
        json_data = json.loads(self.requirements)
        ret = {
            "available_region": set([]),
            "available_rarity": set([]),
            "available_era": set([]),
            "available_min_power": 0,
            "available_content_category": set([]),
        }

        for cond in json_data:
            _type = cond.get("Type")
            _value = cond.get("Value")

            if _type == "region":
                ret["available_region"].add(_value)
            elif _type == "rarity":
                ret["available_rarity"].add(_value)
            elif _type == "era":
                ret["available_era"].add(_value)
            elif _type == "power":
                ret["available_min_power"] = max(_value, ret["available_min_power"])
            elif _type == "content_category":
                ret["available_content_category"].add(_value)
        return ret

    @property
    def reward_to_article_dict(self) -> Dict:
        ret = {}
        if self.reward:
            data = json.loads(self.reward, strict=False).get("Items", [])
            for row in data:
                _id = row.get("Id", 0)
                if _id == 8:
                    ret.update({row.get("Value"): row.get("Amount")})

        return ret

    @cached_property
    def str_requirements(self):
        rarity = {k: v for (k, v) in CHOICE_RARITY}
        era = {k: v for (k, v) in CHOICE_ERA}
        if self.requirements:
            json_data = json.loads(self.requirements)
            ret = []
            for cond in json_data:
                _type = cond.get("Type")
                _value = cond.get("Value")

                if _type == "region":
                    ret.append(f"{_value} 지역")
                elif _type == "rarity":
                    ret.append(f'{rarity.get(_value, "unknown")}')
                elif _type == "power":
                    ret.append(f"{_value}칸 이상")
                elif _type == "era":
                    ret.append(f'{era.get(_value, "unknown")}')
                elif _type == "content_category":
                    ret.append(f"길드기차")
                else:
                    ret.append(f"unknown: type={_type}, value={_value}")
            return " & ".join(ret)
        return ""


class PlayerContractListMixin(BaseVersionMixin):
    contract_list_id = models.IntegerField(
        _("contract list id"), null=False, blank=False, default=0
    )
    available_to = models.DateTimeField(
        _("Available To"), null=True, blank=False, default=None
    )
    next_replace_at = models.DateTimeField(
        _("Next Replace At"), null=True, blank=False, default=None
    )
    next_video_replace_at = models.DateTimeField(
        _("Next Video Replace At"), null=True, blank=False, default=None
    )
    next_video_rent_at = models.DateTimeField(
        _("Next Video Rent At"), null=True, blank=False, default=None
    )
    next_video_speed_up_at = models.DateTimeField(
        _("Next Video SpeedUp At"), null=True, blank=False, default=None
    )
    expires_at = models.DateTimeField(
        _("Expires At"), null=True, blank=False, default=None
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
              "ContractListId": 3,
              "NextReplaceAt": "2023-01-15T07:33:39Z",
              "NextVideoReplaceAt": "2023-01-15T07:33:39Z",
              "NextVideoRentAt": "2023-01-15T07:33:39Z",
              "NextVideoSpeedUpAt": "2023-01-15T07:33:39Z"
            },
            {
              "ContractListId": 100001,
              "AvailableTo": "2023-02-27T12:00:00Z",
              "NextReplaceAt": "2023-01-15T07:33:39Z",
              "NextVideoReplaceAt": "2023-01-15T07:33:39Z",
              "NextVideoRentAt": "2023-01-15T07:33:39Z",
              "NextVideoSpeedUpAt": "2023-01-14T08:46:51Z",
              "ExpiresAt": "2023-01-15T10:48:05Z"
            }
            """
            for cl in data:
                contract_list_id = cl.pop("ContractListId", None)
                available_to = cl.pop("AvailableTo", None)
                next_replace_at = cl.pop("NextReplaceAt", None)
                next_video_replace_at = cl.pop("NextVideoReplaceAt", None)
                next_video_rent_at = cl.pop("NextVideoRentAt", None)
                next_video_speed_up_at = cl.pop("NextVideoSpeedUpAt", None)
                expires_at = cl.pop("ExpiresAt", None)

                ret.append(
                    cls(
                        version_id=version_id,
                        contract_list_id=contract_list_id,
                        available_to=convert_datetime(available_to),
                        next_replace_at=convert_datetime(next_replace_at),
                        next_video_replace_at=convert_datetime(next_video_replace_at),
                        next_video_rent_at=convert_datetime(next_video_rent_at),
                        next_video_speed_up_at=convert_datetime(next_video_speed_up_at),
                        expires_at=convert_datetime(expires_at),
                        created=now,
                        modified=now,
                    )
                )

        return ret, []

    def is_available(self, now) -> bool:
        if self.available_to and not (now < self.available_to):
            return False
        if self.expires_at and not (now < self.expires_at):
            return False
        return True

    def is_expired(self, now) -> bool:
        if self.expires_at and (now >= self.expires_at):
            return True
        return False


class PlayerContractMixin(BaseVersionMixin):
    contract_list = models.ForeignKey(
        to="players.PlayerContractList",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )

    slot = models.IntegerField(_("slot"), null=False, blank=False, default=0)

    conditions = models.CharField(
        _("conditions"), max_length=255, null=False, blank=False, default=""
    )
    reward = models.CharField(
        _("reward"), max_length=255, null=False, blank=False, default=""
    )

    usable_from = models.DateTimeField(
        _("UsableFrom"), null=True, blank=False, default=None
    )
    available_from = models.DateTimeField(
        _("AvailableFrom"), null=True, blank=False, default=None
    )
    available_to = models.DateTimeField(
        _("AvailableTo"), null=True, blank=False, default=None
    )
    expires_at = models.DateTimeField(
        _("AvailableTo"), null=True, blank=False, default=None
    )

    class Meta:
        abstract = True

    @cached_property
    def reward_to_article_dict(self) -> Dict:
        ret = {}
        if self.reward:
            data = json.loads(self.reward, strict=False).get("Items", [])
            for row in data:
                _id = row.get("Id", 0)
                if _id == 8:
                    ret.update({row.get("Value"): row.get("Amount")})

        return ret

    @cached_property
    def conditions_to_article_dict(self) -> Dict:
        ret = {}
        if self.conditions:
            data = json.loads(self.conditions, strict=False)
            for row in data:
                _id = row.get("Id", 0)
                _amount = row.get("Amount", 0)
                ret.update({_id: _amount})

        return ret

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            'Slot' = {int} 18
            'ContractListId' = {int} 100001
            'Conditions' = {list: 1} [{'Id': 126, 'Amount': 547}]
            'Reward' = {dict: 1} {'Items': [{'Id': 8, 'Value': 100009, 'Amount': 110}]}
            'UsableFrom' = {str} '2023-01-09T05:25:44Z'
            'AvailableFrom' = {str} '2022-12-05T12:00:00Z'
            'AvailableTo' = {str} '2023-02-27T12:00:00Z'
            """
            contract_list = kwargs.get("contract_list", [])
            cl = {o.contract_list_id: o for o in contract_list}

            for contract in data:
                slot = contract.pop("Slot", None)
                contract_list_id = contract.pop("ContractListId", None)
                conditions = contract.pop("Conditions", [])
                reward = contract.pop("Reward", {})
                usable_from = contract.pop("UsableFrom", None)
                available_from = contract.pop("AvailableFrom", None)
                available_to = contract.pop("AvailableTo", None)
                expires_at = contract.pop("ExpiresAt", None)

                instance = cls(
                    version_id=version_id,
                    contract_list_id=cl[contract_list_id].id,
                    slot=slot,
                    conditions=json.dumps(conditions, separators=(",", ":"))
                    if conditions
                    else "",
                    reward=json.dumps(reward, separators=(",", ":")) if reward else "",
                    usable_from=convert_datetime(usable_from),
                    available_from=convert_datetime(available_from),
                    available_to=convert_datetime(available_to),
                    expires_at=convert_datetime(expires_at),
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    def is_available(self, now) -> bool:
        if self.available_from and not (self.available_from + BUFFER_TIME < now):
            return False
        if self.usable_from and not (self.usable_from + BUFFER_TIME < now):
            return False

        if self.available_to and not (now < self.available_to - BUFFER_TIME):
            return False
        if self.expires_at and not (now < self.expires_at - BUFFER_TIME):
            return False
        return True


class PlayerGiftMixin(BaseVersionMixin):
    job_id = models.CharField(_("job id"), max_length=100, null=False, blank=False)
    reward = models.CharField(
        _("reward"), max_length=255, null=False, blank=False, default=""
    )
    gift_type = models.IntegerField(_("gift_type"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
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
                _id = gift.pop("Id", None)
                reward = gift.pop("Reward", [])
                _type = gift.pop("Type", None)

                if _id and _type:
                    instance = cls(
                        version_id=version_id,
                        job_id=_id,
                        reward=json.dumps(reward, separators=(",", ":"))
                        if reward
                        else "",
                        gift_type=_type,
                        created=now,
                        modified=now,
                    )
                    ret.append(instance)

        return ret, []

    @cached_property
    def reward_to_dict(self) -> Dict[int, int]:
        json_data = json.loads(self.reward)
        ret = {}

        for cond in json_data.get("Items", []):
            _id = cond.get("Id")
            _article_id = cond.get("Value")
            _amount = cond.get("Amount")
            if _id == 8:
                ret.setdefault(_article_id, 0)
                ret[_article_id] += _amount
        return ret


class PlayerLeaderBoardMixin(BaseVersionMixin):
    player_job = models.ForeignKey(
        to="players.PlayerJob",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    leader_board_id = models.CharField(
        _("LeaderboardId"), max_length=50, blank=False, null=False, default=""
    )
    leader_board_group_id = models.CharField(
        _("LeaderboardGroupId"), max_length=50, blank=False, null=False, default=""
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        sub_list = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            player_job_id = kwargs.get("player_job_id", 0)

            for board in data:
                leader_board_id = board.pop("LeaderboardId", "")
                leader_board_group_id = board.pop("LeaderboardGroupId", "")

                leader_board = cls(
                    version_id=version_id,
                    player_job_id=player_job_id,
                    leader_board_id=leader_board_id,
                    leader_board_group_id=leader_board_group_id,
                    created=now,
                    modified=now,
                )

                ret.append(leader_board)
                sub, _ = cls.sub_model().create_instance(
                    data=board,
                    leader_board=leader_board,
                    version_id=version_id,
                )
                sub_list += sub

        return ret, sub_list


class PlayerLeaderBoardProgressMixin(BaseVersionMixin):
    leader_board = models.ForeignKey(
        to="players.PlayerLeaderBoard",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    player_id = models.IntegerField(_("PlayerId"), null=False, blank=False, default=0)
    avata_id = models.IntegerField(_("AvatarId"), null=False, blank=False, default=0)
    firebase_uid = models.CharField(
        _("FirebaseUid"), max_length=50, null=False, blank=False, default=""
    )
    player_name = models.CharField(
        _("player_name"), max_length=50, null=False, blank=False, default=""
    )
    progress = models.IntegerField(_("progress"), null=False, blank=False, default=0)
    position = models.IntegerField(_("position"), null=False, blank=False, default=0)
    last_updated_at = models.DateTimeField(
        _("LastUpdatedAt"), null=False, blank=False, default=0
    )
    reward_claimed = models.BooleanField(
        _("RewardClaimed"), null=False, blank=False, default=False
    )

    rewards = models.CharField(
        _("rewards"), max_length=255, null=False, blank=False, default=""
    )

    """
    rewards:
        [{'Id': 8, 'Value': 100000, 'Amount': 402}, {'Id': 8, 'Value': 100003, 'Amount': 240}]    
    """

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()
        progresses = data.pop("Progresses", [])
        rewards = data.pop("Rewards", [])
        leader_board = kwargs.get("leader_board", None)

        if progresses and rewards and leader_board:
            for progress, reward in zip(progresses, rewards):
                player_id = progress.pop("PlayerId", None)
                avata_id = progress.pop("AvatarId", None)
                firebase_uid = progress.pop("FirebaseUid", None)
                progress.pop("LeaderboardGroupId", None)
                player_name = progress.pop("PlayerName", None)
                progress_val = progress.pop("Progress", None)
                position = progress.pop("Position", None)
                last_updated_at = progress.pop("LastUpdatedAt", None)
                reward_claimed = progress.pop("RewardClaimed", None)
                instance = cls(
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
                    rewards=json.dumps(reward, separators=(",", ":")) if reward else "",
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []


class PlayerTrainMixin(BaseVersionMixin):
    instance_id = models.IntegerField(
        _("instance_id"), null=False, blank=False, default=0
    )
    train = models.ForeignKey(
        to="servers.TSTrain",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    level = models.ForeignKey(
        to="servers.TSTrainLevel",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    region = models.IntegerField(_("region"), null=True, blank=True, default=None)

    has_route = models.BooleanField(
        _("has route"), null=False, blank=True, default=False
    )
    route_type = models.CharField(
        _("route_type"), max_length=20, null=True, blank=True, default=None
    )
    route_definition_id = models.IntegerField(
        _("route_definition_id"), null=True, blank=True, default=None
    )
    route_departure_time = models.DateTimeField(
        _("route_departure_time"), null=True, blank=True, default=None
    )
    route_arrival_time = models.DateTimeField(
        _("route_arrival_time"), null=True, blank=True, default=None
    )

    has_load = models.BooleanField(_("has load"), null=False, blank=True, default=False)
    load = models.ForeignKey(
        to="servers.TSArticle",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=True,
        blank=False,
        db_constraint=False,
        default=None,
    )
    load_amount = models.IntegerField(
        _("load amount"), null=False, blank=False, default=0
    )

    class Meta:
        abstract = True

    # @cached_property
    # def capacity(self):
    #     lv = TrainLevel.objects.filter(train_level=self.level).first()
    #     if lv:
    #         powers = lv.power.split(';')
    #         return int(powers[self.train.rarity - 1])
    #
    # @cached_property
    # def max_capacity(self):
    #     lv = TrainLevel.objects.filter(train_level=self.train.max_level).first()
    #     if lv:
    #         powers = lv.power.split(';')
    #         return int(powers[self.train.rarity - 1])

    def get_region(self):
        return self.region or self.train.region

    def capacity(self):
        ret = {
            1: self.level.common,
            2: self.level.rare,
            3: self.level.epic,
            4: self.level.legendary,
        }
        return ret.get(self.train.rarity, 0)

    def is_working(self, now):
        if self.route_arrival_time and self.route_arrival_time + BUFFER_TIME >= now:
            return True
        return False

    def is_idle(self, now):
        return not self.is_working(now)

    def __str__(self):
        return self.str_dump()

    def str_dump(self):
        ret = []
        ret.append(f"#{self.instance_id:3d}")
        ret.append(f"[{self.capacity():3d}]")
        ret.append(f"{self.train.get_era_display():10s}")
        ret.append(f"{self.train.get_rarity_display():10s}")
        ret.append(f"{self.train.asset_name:25s}")

        return " ".join(ret)

    @property
    def is_destination_route(self):
        return self.route_type == "destination"

    @property
    def is_job_route(self):
        return self.route_type == "job"

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
              "InstanceId": 75,
              "DefinitionId": 28004,
              "Region": 3,
              "Level": 49,
              "Route": {
                "RouteType": "job",
                "DefinitionId": 6004,
                "DepartureTime": "2023-01-15T06:36:18Z",
                "ArrivalTime": "2023-01-15T07:36:18Z"
              }
            },
            """
            for train in data:
                instance_id = train.pop("InstanceId", None)
                definition_id = train.pop("DefinitionId", None)
                level = train.pop("Level", None)
                route = train.pop("Route", None)
                region = train.pop("Region", None)
                load = train.pop("TrainLoad", None)

                has_route = True if route else False
                route_type = route.pop("RouteType", None) if route else None
                route_definition_id = route.pop("DefinitionId", None) if route else None
                route_departure_time = (
                    route.pop("DepartureTime", None) if route else None
                )
                route_arrival_time = route.pop("ArrivalTime", None) if route else None

                has_load = True if load else False
                load_id = load.pop("Id", None) if load else None
                load_amount = load.pop("Amount", None) if load else 0

                instance = cls(
                    version_id=version_id,
                    instance_id=instance_id,
                    train_id=definition_id,
                    level_id=level,
                    region=region,
                    has_route=has_route,
                    route_type=route_type,
                    route_definition_id=route_definition_id,
                    route_departure_time=convert_datetime(route_departure_time),
                    route_arrival_time=convert_datetime(route_arrival_time),
                    has_load=has_load,
                    load_id=load_id,
                    load_amount=load_amount,
                    created=now,
                    modified=now,
                )

                ret.append(instance)

        return ret, []


class PlayerWarehouseMixin(BaseVersionMixin):
    article = models.ForeignKey(
        to="servers.TSArticle",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    amount = models.IntegerField(_("amount"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for article in data:
                instance = cls(
                    version_id=version_id,
                    article_id=article.pop("Id", None),
                    amount=article.pop("Amount", None),
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    def __str__(self):
        return f"#{self.article_id} {self.article} - {self.amount}개"


class PlayerWhistleMixin(BaseVersionMixin):
    category = models.IntegerField(_("category"), null=False, blank=False, default=0)
    position = models.IntegerField(_("position"), null=False, blank=False, default=0)
    spawn_time = models.DateTimeField(
        _("SpawnTime"), null=True, blank=True, default=None
    )
    collectable_from = models.DateTimeField(
        _("CollectableFrom"), null=True, blank=True, default=None
    )

    is_for_video_reward = models.BooleanField(
        _("IsForVideoReward"), null=True, blank=True, default=None
    )
    expires_at = models.DateTimeField(
        _("ExpiresAt"), null=True, blank=True, default=None
    )

    class Meta:
        abstract = True

    # def is_collectable(self, login_dt, now) -> bool:
    #     login_dt = login_dt + datetime.timedelta(seconds=self.INTERVAL_SECONDS)
    #
    #     dt = min(login_dt, now)
    #     if self.spawn_time and self.spawn_time < dt:
    #         return False
    #     if self.collectable_from and self.collectable_from < dt:
    #         return False
    #     if self.expires_at and now <= self.expires_at:
    #         return False
    #     if self.is_for_video_reward:
    #         return False
    #     return True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        sub_ret = []

        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
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

            for whistle in data:
                category = whistle.pop("Category", None)
                position = whistle.pop("Position", None)
                spawn_time = whistle.pop("SpawnTime", None)
                collectable_from = whistle.pop("CollectableFrom", None)
                reward = whistle.pop("Reward", None)
                is_for_video_reward = whistle.pop("IsForVideoReward", None)
                expires_at = whistle.pop("ExpiresAt", None)

                player_whistle = cls(
                    version_id=version_id,
                    category=category,
                    position=position,
                    spawn_time=convert_datetime(spawn_time),
                    collectable_from=convert_datetime(collectable_from),
                    is_for_video_reward=is_for_video_reward,
                    expires_at=convert_datetime(expires_at),
                    created=now,
                    modified=now,
                )
                sub, _ = cls.sub_model().create_instance(
                    data=(reward.get("Items") or []) if reward else None,
                    player_whistle=player_whistle,
                    version_id=version_id,
                )
                ret.append(player_whistle)
                sub_ret += sub

        return ret, sub_ret


class PlayerWhistleItemMixin(BaseVersionMixin):
    player_whistle = models.ForeignKey(
        to="players.PlayerWhistle",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    item_id = models.IntegerField(_("value"), null=False, blank=False, default=0)
    value = models.IntegerField(_("value"), null=False, blank=False, default=0)
    amount = models.IntegerField(_("amount"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        """

        :param data:
        :param version_id:
        :return:
        """
        ret = []

        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            player_whistle = kwargs.get("player_whistle")

            for item in data:
                item_id = item.get("Id")
                value = item.get("Value")
                amount = item.get("Amount")
                ret.append(
                    cls(
                        version_id=version_id,
                        player_whistle=player_whistle,
                        item_id=item_id,
                        value=value,
                        amount=amount,
                        created=now,
                        modified=now,
                    )
                )

        return ret, []


class PlayerAchievementMixin(BaseVersionMixin):
    achievement = models.CharField(
        _("achievement"), max_length=255, null=False, blank=False, default=""
    )
    level = models.IntegerField(_("level"), null=False, blank=False, default=0)
    progress = models.IntegerField(_("level"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
                "AchievementId": "complete_job",
                "Level": 5,
                "Progress": 2687
            },
            """
            for achievement in data:
                instance = cls(
                    version_id=version_id,
                    achievement=achievement.pop("AchievementId", None),
                    level=achievement.pop("Level", None),
                    progress=achievement.pop("Progress", None),
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []


class PlayerDailyRewardMixin(BaseVersionMixin):
    available_from = models.DateTimeField(
        _("AvailableFrom"), null=True, blank=True, default=None
    )
    expire_at = models.DateTimeField(_("ExpireAt"), null=True, blank=True, default=None)
    rewards = models.CharField(
        _("Rewards"), max_length=255, null=False, blank=False, default=""
    )
    pool_id = models.IntegerField(_("PoolId"), null=False, blank=False, default=0)
    day = models.IntegerField(_("Day"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
                "AvailableFrom": "2023-01-16T00:00:00Z",
                "ExpireAt": "2023-01-16T23:59:59Z",
                "Rewards": [
                  {
                    "Items": [ { "Id": 8, "Value": 3, "Amount": 450 } ]
                  },
                  {
                    "Items": [ { "Id": 8, "Value": 4, "Amount": 40 } ]
                  },
                  {
                    "Items": [ {"Id": 8,"Value": 8,"Amount": 9}]
                  },
                  {
                    "Items": [{"Id": 8,"Value": 2,"Amount": 10}]
                  },
                  {
                    "Items": [{"Id": 1,"Value": 3}]
                  }
                ],
                "PoolId": 3,
                "Day": 0
            },
            """
            for daily in data:
                rewards = daily.pop("Rewards", None)
                instance = cls(
                    version_id=version_id,
                    available_from=convert_datetime(daily.pop("AvailableFrom", None)),
                    expire_at=convert_datetime(daily.pop("ExpireAt", None)),
                    rewards=json.dumps(rewards, separators=(",", ":"))
                    if rewards
                    else "",
                    pool_id=daily.pop("PoolId", None),
                    day=daily.pop("Day", None),
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    def get_today_rewards(self) -> List[Dict]:
        """
            [ { "Id": 8, "Value": 3, "Amount": 450 } ]
        :return:
        """
        ret = {}
        rewards = json.loads(self.rewards, strict=False)
        day = self.day
        if len(rewards) >= day:
            reward = rewards[day]
            return reward.get("Items", [])

    @property
    def can_claim_with_video(self) -> bool:
        rewards = self.get_today_rewards()
        if rewards:
            cnt, has_amount_cnt = 0, 0

            for item in rewards:
                _id = item.get("Id", None)
                _value = item.get("Value", None)
                _amount = item.get("Amount", None)
                cnt += 1
                if _amount is not None:
                    has_amount_cnt += 1

            if 0 < cnt == has_amount_cnt:
                return True

        return False


class PlayerMapMixin(BaseVersionMixin):
    region_name = models.CharField(
        _("region name"), max_length=20, null=False, blank=False, default=""
    )
    spot_id = models.IntegerField(_("SpotId"), null=False, blank=False, default=0)
    position_x = models.IntegerField(
        _("Position X"), null=False, blank=False, default=0
    )
    position_y = models.IntegerField(
        _("Position Y"), null=False, blank=False, default=0
    )
    connections = models.CharField(
        _("connections"), max_length=50, null=False, blank=False, default=""
    )
    is_resolved = models.BooleanField(
        _("IsResolved"), null=False, blank=False, default=False
    )
    content = models.CharField(
        _("region name"), max_length=255, null=False, blank=False, default=""
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            "Id": "region_101",
            "Spots": [
              {
                "SpotId": 161,
                "Position": {
                  "X": 3,
                  "Y": 0
                },
                "Connections": [
                  164
                ],
                "IsResolved": true,
                "Content": {
                  "Category": "quest",
                  "Data": {
                    "JobLocationIds": [
                      161
                    ],
                    "Reward": {
                      "Items": []
                    }
                  }
                }
              },

            """
            for region in data:
                region_name = region.pop("Id", None)
                spots = region.get("Spots", [])

                for spot in spots:
                    spot_id = spot.pop("SpotId", None)
                    position = spot.get("Position", {})
                    x = position.pop("X", 0)
                    y = position.pop("Y", 0)
                    connections = spot.pop("Connections", [])
                    is_resolved = spot.pop("IsResolved", False)
                    content = spot.pop("Content", {})

                    instance = cls(
                        version_id=version_id,
                        region_name=region_name,
                        spot_id=spot_id,
                        position_x=x,
                        position_y=y,
                        connections=json.dumps(connections, separators=(",", ":"))
                        if connections
                        else "",
                        is_resolved=is_resolved,
                        content=json.dumps(content, separators=(",", ":"))
                        if content
                        else "",
                        created=now,
                        modified=now,
                    )
                    ret.append(instance)

        return ret, []

    @cached_property
    def next_spot_ids(self):
        ret = []
        if self.connections:
            ret = json.loads(self.connections, strict=False)
        return ret


class PlayerQuestMixin(BaseVersionMixin):
    job_location = models.ForeignKey(
        to="servers.TSJobLocation",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    milestone = models.IntegerField(_("Milestone"), null=False, blank=False, default=0)
    progress = models.IntegerField(_("Progress"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return f"""#{self.job_location_id}/{self.milestone}/{self.progress}"""

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            [
                 0 = {dict: 3} {'JobLocationId': 150, 'Milestone': 1, 'Progress': 1}
                 1 = {dict: 3} {'JobLocationId': 152, 'Milestone': 1, 'Progress': 1}
                 2 = {dict: 3} {'JobLocationId': 159, 'Milestone': 3, 'Progress': 3}
                 3 = {dict: 3} {'JobLocationId': 160, 'Milestone': 4, 'Progress': 4}
            ]
            """

            for region in data:
                job_location_id = region.pop("JobLocationId", 0)
                milestone = region.pop("Milestone", 0)
                progress = region.pop("Progress", 0)
                instance = cls(
                    version_id=version_id,
                    job_location_id=job_location_id,
                    milestone=milestone,
                    progress=progress,
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []


class PlayerVisitedRegionMixin(BaseVersionMixin):
    region = models.ForeignKey(
        to="servers.TSRegion",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            'VisitedRegions' = {list: 1} [101]
            """
            while len(data) > 0:
                region_id = data.pop(0)
                instance = cls(
                    version_id=version_id,
                    region_id=region_id,
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []


class PlayerShipOfferMixin(BaseVersionMixin):
    definition_id = models.IntegerField(_("definition_id"), null=True, blank=False)
    conditions = models.CharField(
        _("Conditions"), max_length=255, null=False, blank=False, default=""
    )
    reward = models.CharField(
        _("reward"), max_length=255, null=False, blank=False, default=""
    )
    arrival_at = models.DateTimeField(_("ArrivalAt"), null=True, blank=False)
    expire_at = models.DateTimeField(_("ExpireAt"), null=True, blank=False)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            0 = {dict: 5} {'DefinitionId': 2, 'Conditions': [{'Id': 120, 'Amount': 91}, {'Id': 124, 'Amount': 140}, {'Id': 232, 'Amount': 406}], 'Reward': {'Items': [{'Id': 8, 'Value': 3, 'Amount': 320}, {'Id': 8, 'Value': 10, 'Amount': 12}, {'Id': 8, 'Value': 11, 'Amount': 11}, {'
             'DefinitionId' = {int} 2
             'Conditions' = {list: 3} [{'Id': 120, 'Amount': 91}, {'Id': 124, 'Amount': 140}, {'Id': 232, 'Amount': 406}]
             'Reward' = {dict: 1} {'Items': [{'Id': 8, 'Value': 3, 'Amount': 320}, {'Id': 8, 'Value': 10, 'Amount': 12}, {'Id': 8, 'Value': 11, 'Amount': 11}, {'Id': 8, 'Value': 12, 'Amount': 7}]}
             'ArrivalAt' = {str} '2022-12-30T04:56:11Z'
             'ExpireAt' = {str} '2022-12-30T09:08:24Z'
             __len__ = {int} 5
            """
            for ship in data:
                definition_id = ship.pop("DefinitionId", 0)
                conditions = ship.pop("Conditions", [])
                reward = ship.pop("Reward", {})
                arrival_at = ship.pop("ArrivalAt", None)
                expire_at = ship.pop("ExpireAt", None)

                instance = cls(
                    version_id=version_id,
                    definition_id=definition_id,
                    conditions=json.dumps(conditions, separators=(",", ":"))
                    if conditions
                    else "",
                    reward=json.dumps(reward, separators=(",", ":")) if reward else "",
                    arrival_at=convert_datetime(arrival_at),
                    expire_at=convert_datetime(expire_at),
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    @cached_property
    def reward_to_article_dict(self) -> Dict:
        ret = {}
        if self.reward:
            data = json.loads(self.reward, strict=False).get("Items", [])
            for row in data:
                _id = row.get("Id", 0)
                if _id == 8:
                    ret.update({row.get("Value"): row.get("Amount")})

        return ret

    @cached_property
    def conditions_to_article_dict(self) -> Dict:
        ret = {}
        if self.conditions:
            data = json.loads(self.conditions, strict=False)
            for row in data:
                _id = row.get("Id", 0)
                _amount = row.get("Amount", 0)
                ret.update({_id: _amount})

        return ret


class PlayerCompetitionMixin(BaseVersionMixin, ContentCategoryMixin):
    type = models.CharField(
        _("Type"), max_length=20, null=False, blank=False, default=""
    )
    level_from = models.IntegerField(_("LevelFrom"), null=True, blank=False)
    max_attendees = models.IntegerField(_("MaxAttendees"), null=True, blank=False)
    competition_id = models.CharField(
        _("CompetitionId"), max_length=50, null=False, blank=False, default=""
    )
    rewards = models.CharField(
        _("Rewards"), max_length=255, null=False, blank=False, default=""
    )
    starts_at = models.DateTimeField(_("StartsAt"), null=True, blank=False)
    enrolment_available_to = models.DateTimeField(
        _("EnrolmentAvailableTo"), null=True, blank=False
    )
    finishes_at = models.DateTimeField(_("FinishesAt"), null=True, blank=False)
    expires_at = models.DateTimeField(_("ExpiresAt"), null=True, blank=False)
    activated_at = models.DateTimeField(_("ActivatedAt"), null=True, blank=False)
    progress = models.CharField(
        _("Progress"), max_length=255, null=False, blank=False, default=""
    )
    presentation_data_id = models.IntegerField(
        _("PresentationDataId"), null=True, blank=False
    )
    guild_data = models.CharField(
        _("GuildData"), max_length=255, null=False, blank=False, default=""
    )
    scope = models.CharField(
        _("Scope"), max_length=20, null=False, blank=False, default=""
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            'Type' = {str} 'union'
            'LevelFrom' = {int} 25
            'MaxAttendees' = {int} 15
            'CompetitionId' = {str} '0a96024d-fcee-4402-9f33-618eaf07ca5b'
            'ContentCategory' = {int} 3
            'Rewards' = {list: 0} []
            'StartsAt' = {str} '2022-12-05T12:00:00Z'
            'EnrolmentAvailableTo' = {str} '2023-02-27T12:00:00Z'
            'FinishesAt' = {str} '2023-02-27T12:00:00Z'
            'ExpiresAt' = {str} '2023-03-03T12:00:00Z'
            'ActivatedAt' = {str} '2022-12-05T12:00:51Z'
            'Progress' = {dict: 7} {'PlayerId': 61561146, 'AvatarId': 58, 'FirebaseUid': 'prod_61561146', 'PlayerName': 'SRand', 'Progress': 26278, 'LastUpdate': '2023-01-20T14:16:29Z', 'RewardClaimed': False}
            'PresentationDataId' = {int} 100001
            'GuildData' = {dict: 5} {'Status': 0, 'MemberContributionEnrolledAt': '2022-12-05T12:00:03Z', 'GuildEnrolledAt': '2022-12-05T12:00:03Z', 'GuildId': '3a3dfa63-2e0f-4a40-b36c-08d252db9c2b', 'EnrolledAt': '2022-12-05T12:00:03Z'}
            'Scope' = {str} 'global'
            """
            for competition in data:
                _type = competition.pop("Type", "")
                _level_from = competition.pop("LevelFrom", 0)
                _max_attendees = competition.pop("MaxAttendees", 0)
                _competition_id = competition.pop("CompetitionId", "")
                _rewards = competition.pop("Rewards", [])
                _starts_at = competition.pop("StartsAt", "")
                _enrolment_available_to = competition.pop("EnrolmentAvailableTo", "")
                _finishes_at = competition.pop("FinishesAt", "")
                _expires_at = competition.pop("ExpiresAt", "")
                _activated_at = competition.pop("ActivatedAt", "")
                _progress = competition.pop("Progress", {})
                _presentation_data_id = competition.pop("PresentationDataId", 0)
                _guild_data = competition.pop("GuildData", {})
                _scope = competition.pop("Scope", "")
                _content_category = competition.pop("ContentCategory", 0)

                instance = cls(
                    version_id=version_id,
                    type=_type,
                    level_from=_level_from,
                    max_attendees=_max_attendees,
                    competition_id=_competition_id,
                    rewards=json.dumps(_rewards, separators=(",", ":"))
                    if _rewards
                    else "",
                    starts_at=convert_datetime(_starts_at),
                    enrolment_available_to=convert_datetime(_enrolment_available_to),
                    finishes_at=convert_datetime(_finishes_at),
                    expires_at=convert_datetime(_expires_at),
                    activated_at=convert_datetime(_activated_at),
                    progress=json.dumps(_progress, separators=(",", ":"))
                    if _progress
                    else "",
                    presentation_data_id=_presentation_data_id,
                    guild_data=json.dumps(_guild_data, separators=(",", ":"))
                    if _guild_data
                    else "",
                    content_category=_content_category,
                    scope=_scope,
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []


class PlayerUnlockedContentMixin(BaseVersionMixin):
    job_location = models.ForeignKey(
        to="servers.TSJobLocation",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    unlocked_at = models.DateTimeField(_("UnlockedAt"), null=True, blank=False)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {
                'DefinitionId': 150,
                'UnlockedAt': '2022-07-30T08:31:20Z'
            }
            """
            for unlocked_content in data:
                job_location_id = unlocked_content.pop("DefinitionId", 0)
                unlocked_at = unlocked_content.pop("UnlockedAt", None)

                instance = cls(
                    version_id=version_id,
                    job_location_id=job_location_id,
                    unlocked_at=convert_datetime(unlocked_at),
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []


class PlayerOfferContainerMixin(BaseVersionMixin):
    offer_container = models.ForeignKey(
        to="servers.TSOfferContainer",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    last_bought_at = models.DateTimeField(_("LastBoughtAt"), null=True, blank=False)
    count = models.IntegerField(_("Count"), null=True, blank=False)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {'DefinitionId': 1, 'LastBoughtAt': '2022-08-27T05:35:42Z', 'Count': 2}
            """
            for offer in data:
                definition_id = offer.pop("DefinitionId", 0)
                last_bought_at = offer.pop("LastBoughtAt", None)
                count = offer.pop("Count", None)

                instance = cls(
                    version_id=version_id,
                    offer_container_id=definition_id,
                    last_bought_at=last_bought_at,
                    count=count,
                    created=now,
                    modified=now,
                )
                ret.append(instance)

        return ret, []

    @property
    def is_video_reward(self) -> bool:
        if self.offer_container.price_article_id == 16:
            return True
        return False

    def is_available(self, now) -> bool:
        if (
            self.last_bought_at
            and self.last_bought_at
            + datetime.timedelta(seconds=self.offer_container.cooldown_duration)
            < now
        ):
            return True
        return False


class PlayerDailyOfferMixin(BaseVersionMixin):
    expire_at = models.DateTimeField(_("ExpireAt"), null=True, blank=False)
    expires_at = models.DateTimeField(_("ExpiresAt"), null=True, blank=False)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        sub_ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            'ExpireAt' = {str} '2023-01-18T00:00:00Z'
            'ExpiresAt' = {str} '2023-01-18T00:00:00Z'
            'OfferItems' = [{'Slot': 11, 'Price': {'Id': 16, 'Amount': 1}, 'Reward': {'Items': [{'Id': 8, 'Value': 7, 'Amount': 30}]}, 'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 49}, {'Slot': 12, 'Price': {'Id': 3, 'Amount': 40}, 'Reward': {'Items': [{'Id': 1, 'Value': 34}]}, 'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 50}, {'Slot': 13, 'Price': {'Id': 3, 'Amount': 100}, 'Reward': {'Items': [{'Id': 8, 'Value': 7, 'Amount': 100}]}, 'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 51}, {'Slot': 14, 'Price': {'Id': 2, 'Amount': 40}, 'Reward': {'Items': [{'Id': 1, 'Value': 35}]}, 'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 52}, {'Slot': 15, 'Price': {'Id': 2, 'Amount': 200}, 'Reward': {'Items': [{'Id': 8, 'Value': 7, 'Amount': 550}]}, 'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 53}, {'Slot': 16, 'Price': {'Id': 2, 'Amount': 80}, 'Reward': {'Items': [{'Id': 1, 'Value': 68}]}, 'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 54}]
            """
            for offer in data:
                expire_at = offer.pop("ExpireAt", None)
                expires_at = offer.pop("ExpiresAt", None)
                offer_items = offer.get("OfferItems", [])
                instance = cls(
                    version_id=version_id,
                    expire_at=expire_at,
                    expires_at=expires_at,
                    created=now,
                    modified=now,
                )
                ret.append(instance)

                sub, _ = cls.sub_model().create_instance(
                    data=offer_items,
                    daily_offer=instance,
                    version_id=version_id,
                )
                sub_ret += sub

        return ret, sub_ret


class PlayerDailyOfferItemMixin(BaseVersionMixin):
    """
    {'Slot': 13, 'Price': {'Id': 3, 'Amount': 100},
    'Reward': {'Items': [{'Id': 8, 'Value': 7, 'Amount': 100}]},
    'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 51}
    """

    slot = models.IntegerField(_("slot"), null=False, blank=False, default=0)
    daily_offer = models.ForeignKey(
        to="players.PlayerDailyOffer",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    price = models.ForeignKey(
        to="servers.TSArticle",
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=False,
        blank=False,
        db_constraint=False,
    )
    price_amount = models.IntegerField(
        _("Price Amount"), null=False, blank=False, default=0
    )
    reward = models.CharField(
        _("reward"), max_length=255, null=False, blank=False, default=""
    )
    purchased = models.BooleanField(
        _("Purchased"), null=False, blank=False, default=False
    )
    purchase_count = models.IntegerField(
        _("PurchaseCount"), null=False, blank=False, default=0
    )
    definition_id = models.IntegerField(
        _("DefinitionId"), null=False, blank=False, default=0
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            """
            {'Slot': 13, 'Price': {'Id': 3, 'Amount': 100},
            'Reward': {'Items': [{'Id': 8, 'Value': 7, 'Amount': 100}]},
            'Purchased': False, 'PurchaseCount': 0, 'DefinitionId': 51}
            """
            daily_offer = kwargs.get("daily_offer")

            for offer in data:
                slot = offer.pop("Slot", None)
                price = offer.get("Price", None)
                price_id = price.pop("Id", 0)
                price_amount = price.pop("Amount", 0)
                reward = offer.pop("Reward", {})
                purchased = offer.pop("Purchased", {})
                purchase_count = offer.pop("PurchaseCount", 0)
                definition_id = offer.pop("DefinitionId", 0)

                instance = cls(
                    version_id=version_id,
                    slot=slot,
                    daily_offer=daily_offer,
                    price_id=price_id,
                    price_amount=price_amount,
                    reward=json.dumps(reward, separators=(",", ":")) if reward else "",
                    purchased=purchased,
                    purchase_count=purchase_count,
                    definition_id=definition_id,
                    created=now,
                    modified=now,
                )

                ret.append(instance)

        return ret, []


class PlayerCityLoopParcelMixin(BaseVersionMixin):
    parcel = models.IntegerField(_("parcel"), null=False, blank=False, default=0)

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for parcel in data:
                instance = cls(
                    version_id=version_id, parcel=parcel, created=now, modified=now
                )

                ret.append(instance)

        return ret, []


class PlayerCityLoopTaskMixin(BaseVersionMixin):
    next_replace_at = models.DateTimeField(
        _("UpgradeTaskNextReplaceAt"), null=True, blank=False
    )
    next_video_replace_at = models.DateTimeField(
        _("UpgradeTaskNextVideoReplaceAt"), null=True, blank=False
    )

    class Meta:
        abstract = True

    @classmethod
    def create_instance(
        cls, *, data: Dict, version_id: int, **kwargs
    ) -> Tuple[List, List]:
        ret = []
        now = timezone.now()

        if data and isinstance(data, dict):
            data = [data]

        if data:
            for task in data:
                next_replace_at = task.pop("UpgradeTaskNextReplaceAt", None)
                next_video_replace_at = task.get("UpgradeTaskNextVideoReplaceAt", None)

                instance = cls(
                    version_id=version_id,
                    next_replace_at=next_replace_at,
                    next_video_replace_at=next_video_replace_at,
                    created=now,
                    modified=now,
                )

                ret.append(instance)

        return ret, []
