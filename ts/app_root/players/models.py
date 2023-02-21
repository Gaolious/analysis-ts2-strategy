from functools import cached_property
from typing import List, Tuple, Dict, Optional, Type

from django.db import models

from app_root.players.mixins import PlayerBuildingMixin, PlayerDestinationMixin, PlayerFactoryMixin, \
    PlayerFactoryProductOrderMixin, PlayerJobMixin, PlayerContractListMixin, PlayerContractMixin, PlayerGiftMixin, \
    PlayerLeaderBoardMixin, PlayerLeaderBoardProgressMixin, PlayerTrainMixin, PlayerWarehouseMixin, \
    PlayerWhistleItemMixin, PlayerWhistleMixin, PlayerAchievementMixin, PlayerDailyRewardMixin, PlayerMapMixin, \
    PlayerQuestMixin, PlayerVisitedRegionMixin, PlayerShipOfferMixin, PlayerCompetitionMixin, \
    PlayerUnlockedContentMixin, PlayerOfferContainerMixin, PlayerDailyOfferMixin, PlayerDailyOfferItemMixin
from app_root.utils import get_remain_time
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

    def __str__(self):
        return f'FactoryId={self.player_factory.factory_id}/article=[{self.article_id}|{self.article}]/Index={self.index}'


class PlayerJob(PlayerJobMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Job'
        verbose_name_plural = 'Player Jobs'

    @cached_property
    def current_progress(self):
        """
            길드 이벤트의 총 진행율.
        :return:
        """
        if self.is_union_job:
            return sum(
                PlayerLeaderBoardProgress.objects.filter(
                    leader_board__player_job_id=self.id
                ).values_list(
                    'progress', flat=True
                )
            )
        else:
            return self.current_article_amount

    def __str__(self):
        ret = []
        ret.append(f'#{self.id}')
        if self.is_story_job:
            ret.append('StoryJob')
        if self.is_side_job:
            ret.append('SideJob')
        if self.is_union_job:
            ret.append('UnionJob')
        if self.is_event_job:
            ret.append('EventJob')

        if self.completed_at:
            ret.append(f'완료:{self.completed_at}')
        if self.completed_at:
            ret.append(f'수령:{self.collectable_from}')

        ret.append(self.str_requirements)

        if self.is_union_job:
            ret.append(f'Progress: {self.current_progress}/{self.required_amount} ({self.current_progress / self.required_amount * 100:.2f} %)')
        else:
            ret.append(f'Progress: {self.current_article_amount}/{self.required_amount} ({self.current_article_amount/self.required_amount*100:.2f} %)')

        ret.append(f'Required: #{self.required_article.id}|{self.required_article.name}')
        return ' / '.join(ret)


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
    ARTICLE_XP = 1
    ARTICLE_GEM = 2
    ARTICLE_GOLD = 3
    ARTICLE_KEY = 4

    ARTICLE_TRAIN_PARTS_COMMON = 6
    ARTICLE_TRAIN_PARTS_RARE = 7
    ARTICLE_TRAIN_PARTS_EPIC = 8
    ARTICLE_TRAIN_PARTS_LEGENDARY = 9
    ARTICLE_TRAIN_PARTS_UNION = 5

    ARTICLE_BLUE_CITY_PLANS = 10
    ARTICLE_YELLOW_CITY_PLANS = 11
    ARTICLE_RED_CITY_PLANS = 12

    ARTICLE_GIFT = 14
    ARTICLE_POPULATION = 15

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


class PlayerShipOffer(PlayerShipOfferMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Ship Offer'
        verbose_name_plural = 'Player Ship Offers'


class PlayerCompetition(PlayerCompetitionMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Competition'
        verbose_name_plural = 'Player Competitions'


class PlayerUnlockedContent(PlayerUnlockedContentMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player Unlocked Content'
        verbose_name_plural = 'Player Unlocked Contents'


class PlayerDailyOfferContainer(PlayerOfferContainerMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player DailyOffer Container'
        verbose_name_plural = 'Player DailyOffer Containers'


class PlayerDailyOffer(PlayerDailyOfferMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player DailyOffer'
        verbose_name_plural = 'Player DailyOffers'

    @classmethod
    def sub_model(cls) -> Optional[Type['models.Model']]:
        """

        :return:
        """
        return PlayerDailyOfferItem


class PlayerDailyOfferItem(PlayerDailyOfferItemMixin, BaseModelMixin, TimeStampedMixin):
    class Meta:
        verbose_name = 'Player DailyOffer Item'
        verbose_name_plural = 'Player DailyOffer Items'

