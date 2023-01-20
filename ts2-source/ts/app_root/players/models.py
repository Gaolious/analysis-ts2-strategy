from functools import cached_property
from typing import List, Tuple, Dict, Optional, Type

from django.db import models

from app_root.players.mixins import PlayerBuildingMixin, PlayerDestinationMixin, PlayerFactoryMixin, \
    PlayerFactoryProductOrderMixin, PlayerJobMixin, PlayerContractListMixin, PlayerContractMixin, PlayerGiftMixin, \
    PlayerLeaderBoardMixin, PlayerLeaderBoardProgressMixin, PlayerTrainMixin, PlayerWarehouseMixin, \
    PlayerWhistleItemMixin, PlayerWhistleMixin, PlayerAchievementMixin, PlayerDailyRewardMixin, PlayerMapMixin, \
    PlayerQuestMixin, PlayerVisitedRegionMixin
from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin

"""
    초기 데이터는 저장되어 있는 파일을 참고.
    
    RunVersion.TaskStatus
"""


class PlayerBuilding(PlayerBuildingMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Building'
        verbose_name_plural = 'Buildings'


class PlayerDestination(PlayerDestinationMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Destination'
        verbose_name_plural = 'Player Destination'


class PlayerFactory(PlayerFactoryMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Factory'
        verbose_name_plural = 'Player Factories'

    @classmethod
    def sub_model(cls) -> Optional[Type[models.Model]]:
        return PlayerFactoryProductOrder


class PlayerFactoryProductOrder(PlayerFactoryProductOrderMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Factory Product Order'
        verbose_name_plural = 'Player Factory Product Orders'


class PlayerJob(PlayerJobMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Job'
        verbose_name_plural = 'Player Jobs'

    @cached_property
    def current_guild_amount(self):
        return sum(PlayerLeaderBoardProgress.objects.filter(leader_board__player_job_id=self.id).values_list('progress',
                                                                                                             flat=True))

class PlayerContractList(PlayerContractListMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Contract List'
        verbose_name_plural = 'Player Contract Lists'


class PlayerContract(PlayerContractMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Contract'
        verbose_name_plural = 'Player Contracts'


class PlayerGift(PlayerGiftMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Gift'
        verbose_name_plural = 'Player Gifts'


class PlayerLeaderBoard(PlayerLeaderBoardMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Leader Board'
        verbose_name_plural = 'Player Leader Boards'

    @classmethod
    def sub_model(cls) -> Type['models.Model']:
        return PlayerLeaderBoardProgress


class PlayerLeaderBoardProgress(PlayerLeaderBoardProgressMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Leader Board Progress'
        verbose_name_plural = 'Player Leader Board Progresses'


class PlayerTrain(PlayerTrainMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Train'
        verbose_name_plural = 'Player Trains'


class PlayerWarehouse(PlayerWarehouseMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Warehouse'
        verbose_name_plural = 'Player Warehouses'


class PlayerWhistle(PlayerWhistleMixin, BaseModelMixin, TimeStampedMixin):

    class Meta:
        verbose_name = 'Player Whistle'
        verbose_name_plural = 'Player Whistles'

    @classmethod
    def sub_model(cls) -> Optional[Type['models.Model']]:
        return PlayerWhistleItem


class PlayerWhistleItem(PlayerWhistleItemMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Whistle Item'
        verbose_name_plural = 'Player Whistle Items'


class PlayerAchievement(PlayerAchievementMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Achievement'
        verbose_name_plural = 'Player Achievements'


class PlayerDailyReward(PlayerDailyRewardMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Daily Reward'
        verbose_name_plural = 'Player Daily Rewards'


class PlayerMap(PlayerMapMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Map'
        verbose_name_plural = 'Player Maps'

class PlayerQuest(PlayerQuestMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Quest'
        verbose_name_plural = 'Player Quests'

class PlayerVisitedRegion(PlayerVisitedRegionMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Visited Region'
        verbose_name_plural = 'Player Visited Regions'



