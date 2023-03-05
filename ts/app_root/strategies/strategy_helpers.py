from datetime import datetime, timedelta
from functools import cached_property
from plistlib import Dict
from typing import List

from app_root.servers.models import RunVersion, TSFactory
from app_root.strategies.data_types import ArticleSource, FactoryStrategy
from app_root.strategies.managers import factory_find_need_create, get_number_of_working_dispatchers, \
    warehouse_used_capacity, warehouse_max_capacity


class StrategyMixin:
    TITLE = ''
    article_source: Dict[int, ArticleSource]
    factory_strategy: Dict[int, FactoryStrategy]
    version: RunVersion

    before_used_dispatcher: int
    after_used_dispatcher: int

    before_union_dispatcher: int
    after_union_dispatcher: int

    before_used_warehouse: int
    peak_used_warehouse: int
    after_used_warehouse: int

    next_event_time: datetime

    def __init__(self,
                 version: RunVersion,
                 article_source: Dict[int, ArticleSource],
                 factory_strategy: Dict[int, FactoryStrategy]
    ):
        self.version = version
        self.article_source = article_source
        self.factory_strategy = factory_strategy


    @property
    def max_normal_workers(self):
        return self.version.dispatchers + 2

    @property
    def max_union_workers(self):
        return self.version.guild_dispatchers + 2

    @cached_property
    def max_warehouse_capacity(self):
        return warehouse_max_capacity(version=self.version)

    def update_peak_warehouse_usage(self, peak):
        self.peak_used_warehouse = peak

    def update_after_warehouse_usage(self, usage):
        self.after_used_warehouse = usage

    def setup(self):
        self.before_used_dispatcher, self.before_union_dispatcher = get_number_of_working_dispatchers(version=self.version)
        self.after_used_dispatcher, self.after_union_dispatcher = self.before_used_dispatcher, self.before_union_dispatcher

        self.next_event_time = self.version.now + timedelta(hours=100)

        self.before_used_warehouse = warehouse_used_capacity(version=self.version)

        self.peak_used_warehouse = self.before_used_warehouse
        self.after_used_warehouse = self.before_used_warehouse

    def check(self) -> bool:
        # check warehouse
        # check
        pass

    def command(self):
        pass


class CheckFactoryAcquire(StrategyMixin):
    TITLE = '공장 생성 - 레벨 업에 따른 새로운 공장이 생성 되었는가?'
    factory_list: List[TSFactory] = []

    def setup(self):
        super(CheckFactoryAcquire, self).setup()

    def command(self):
        for factory in factory_find_need_create(version=self.version):
            pass


class CheckDailyReward(StrategyMixin):
    TITLE = '일일 보상 - 5일간 연속 로그인시 보상'

    def setup(self):
        super(CheckDailyReward, self).setup()
