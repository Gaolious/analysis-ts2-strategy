from typing import List, Dict, Type, Optional

from app_root.players.models import PlayerJob, PlayerTrain, PlayerFactory, PlayerContract, PlayerFactoryProductOrder
from app_root.servers.models import TSDestination, TSArticle, TSProduct


class JobPriority:
    job: PlayerJob
    train: PlayerTrain
    amount: int

    def __init__(self, train: PlayerTrain, job: PlayerJob, amount: int):
        self.job = job
        self.train = train
        self.amount = amount


class ArticleSource:
    article: TSArticle
    destinations: List[TSDestination]
    products: List[TSProduct]
    contracts: List[PlayerContract]

    def __init__(self, article: TSArticle):
        self.article = article
        self.destinations = []
        self.products = []
        self.contracts = []

    def add_destination(self, dest: TSDestination):
        self.destinations.append(dest)

    def add_product(self, product: TSProduct):
        self.products.append(product)

    def add_contract(self, contract: PlayerContract):
        self.contracts.append(contract)


class Material:
    required_articles: Dict[int, int]

    def __init__(self):
        self.required_articles = {}

    def __add__(self, other):
        for k, v in other.items():
            if k not in self.required_articles:
                self.required_articles.update({k: v})
            self.required_articles[k] += v

    def add(self, article_id: int, amount: int):
        if article_id not in self.required_articles:
            self.required_articles.update({
                article_id: 0
            })
        self.required_articles[article_id] += amount

    def add_dict(self, article_amount_dict: Dict[int, int]):
        for article_id, amount in article_amount_dict.items():
            self.add(article_id, amount)

    def items(self):
        return list(self.required_articles.items())

    def clear(self):
        self.required_articles = {}


class FactoryStrategy:
    player_factory: PlayerFactory
    factory_only_products: List[TSProduct]
    destination_products: List[TSProduct]

    strategy_article_count: Dict[int, int]  # 미리 생성해놔야 하는 개수.
    waiting_article_count: Dict[int, int]
    processing_article_count: Dict[int, int]
    completed_article_count: Dict[int, int]

    def __init__(self, player_factory: PlayerFactory, factory_only_products: List[TSProduct], destination_products: List[TSProduct]):
        self.player_factory = player_factory
        self.factory_only_products = factory_only_products
        self.destination_products = destination_products

        self.strategy_article_count = {}
        self.waiting_article_count = {}
        self.processing_article_count = {}
        self.completed_article_count = {}

    def update(self, completed: List[PlayerFactoryProductOrder], processing: List[PlayerFactoryProductOrder], waiting: List[PlayerFactoryProductOrder]):
        self.waiting_article_count = {}
        self.processing_article_count = {}
        self.completed_article_count = {}

        for order in waiting:
            self.waiting_article_count.setdefault(order.article_id, 0)
            self.waiting_article_count[order.article_id] += 1

        for order in processing:
            self.processing_article_count.setdefault(order.article_id, 0)
            self.processing_article_count[order.article_id] += 1

        for order in completed:
            self.completed_article_count.setdefault(order.article_id, 0)
            self.completed_article_count[order.article_id] += 1

