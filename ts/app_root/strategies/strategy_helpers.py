from plistlib import Dict

from app_root.servers.models import RunVersion
from app_root.strategies.data_types import ArticleSource, FactoryStrategy


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

    def __init__(self,
                 version: RunVersion,
                 article_source: Dict[int, ArticleSource],
                 factory_strategy: Dict[int, FactoryStrategy]
    ):
        self.version = version
        self.article_source = article_source
        self.factory_strategy = factory_strategy

    def dump(self):
        pass


class CheckFactoryAcquire(StrategyMixin):
    TITLE = 'Check Factory Acquire'
