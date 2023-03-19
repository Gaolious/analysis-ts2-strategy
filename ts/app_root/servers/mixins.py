from django.db import models
from django.utils.translation import gettext_lazy as _

CONTENT_CATEGORY_BASIC = 1
CONTENT_CATEGORY_EVENT = 2
CONTENT_CATEGORY_UNION = 3
CHOICE_CONTENT_CATEGORY = (
    (CONTENT_CATEGORY_BASIC, "기본"),
    (CONTENT_CATEGORY_EVENT, "이벤트"),
    (CONTENT_CATEGORY_UNION, "유니언"),
)

RARITY_COMMON = 1
RARITY_RARE = 2
RARITY_EPIC = 3
RARITY_LEGENDARY = 4
CHOICE_RARITY = (
    (RARITY_COMMON, "일반"),
    (RARITY_RARE, "레어"),
    (RARITY_EPIC, "에픽"),
    (RARITY_LEGENDARY, "전설"),
)

ERA_STEAM = 1
ERA_ELECTRON = 2
ERA_DIESEL = 3
CHOICE_ERA = (
    (ERA_STEAM, "스팀"),
    (ERA_ELECTRON, "전기"),
    (ERA_DIESEL, "디젤"),
)
"""
    Reward : 
        0 = {dict: 1} {'Items': [{'Id': 8, 'Value': 4, 'Amount': 20}]}
        1 = {dict: 1} {'Items': [{'Id': 8, 'Value': 7, 'Amount': 20}]}
        2 = {dict: 1} {'Items': [{'Id': 8, 'Value': 3, 'Amount': 36}]}
        3 = {dict: 1} {'Items': [{'Id': 8, 'Value': 2, 'Amount': 10}]}
        4 = {dict: 1} {'Items': [{'Id': 1, 'Value': 13}]}
    id=8 은 article
    id=1 은 container (maybe) 

"""


class ContentCategoryMixin(models.Model):
    """
    기본 / 이벤트 / 유니언
    """

    content_category = models.IntegerField(
        _("content category"),
        null=False,
        blank=False,
        default=0,
        choices=CHOICE_CONTENT_CATEGORY,
    )

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

    rarity = models.IntegerField(
        _("rarity"), null=False, blank=False, default=0, choices=CHOICE_RARITY
    )

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

    era = models.IntegerField(
        _("era"), null=False, blank=False, default=0, choices=CHOICE_ERA
    )

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
