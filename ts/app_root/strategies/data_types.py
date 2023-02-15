from typing import List, Dict, Type, Optional, Tuple

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


class MaterialStrategy:
    warehouse_used: Dict[int, int]

    # contract, amount
    contract_queue: List[PlayerContract]
    contract_collectable: List[PlayerContract]

    # factory_id, [ TSProduct, amount ]
    factory_queue: Dict[int, List[Tuple[TSProduct, int]]]
    factory_collectable: Dict[int, List[Tuple[TSProduct, int]]]
    factory_uncollectable: Dict[int, List[Tuple[TSProduct, int]]]
    factory_prepare: Dict[int, List[Tuple[TSProduct, int]]]

    # destination_id, [TSdestination, amount
    destination_queue: List[Tuple[TSDestination, int]]

    def __init__(self):
        self.clear()

    def clear(self):
        self.warehouse_used = {}

        self.contract_queue = []
        self.contract_collectable = []

        self.factory_queue = {}
        self.factory_collectable = {}
        self.factory_uncollectable = {}
        self.factory_prepare = {}

        self.destination_queue = []

    def get_used_warehouse(self, article_id: int) -> int:
        return self.warehouse_used.get(article_id, 0)

    def add_used_warehouse(self, article_id: int, amount: int):
        self.warehouse_used.setdefault(article_id, 0)
        self.warehouse_used[article_id] += amount

    def push_contract(self, contract: PlayerContract):
        self.contract_queue.append(contract)

    def push_factory(self, product: TSProduct, amount: int):
        factory_id = int(product.factory_id)
        if factory_id not in self.factory_queue:
            self.factory_queue.update({factory_id: []})
        self.factory_queue[factory_id].append((product, amount))

    def push_destination(self, destination: TSDestination, amount: int):
        self.destination_queue.append((destination, amount))

    def empty_contract(self) -> bool:
        if self.contract_queue:
            return False
        return True

    def pop_contract(self) -> PlayerContract:
        ret = self.contract_queue.pop(0)
        return ret

    def add_collectable_contract(self, contract: PlayerContract):
        for k, v in contract.conditions_to_article_dict.items():
            self.add_used_warehouse(k, v)

        self.contract_collectable.append(contract)

    def all_empty_factory(self) -> bool:
        for k in self.factory_queue:
            if self.factory_queue[k]:
                return False
        return True

    def empty_factory_queue(self, factory_id: int) -> bool:
        if self.factory_queue.get(factory_id):
            return False
        return True

    def pop_factory(self, factory_id):
        ret = self.factory_queue[factory_id].pop(0)
        return ret

    def add_collectable_factory(self, product: TSProduct, amount: int):
        factory_id = int(product.factory_id)
        if factory_id not in self.factory_collectable:
            self.factory_collectable.update({factory_id: []})
        self.factory_collectable[factory_id].append((product, amount))

    def get_used_collectable_factory(self, product: TSProduct) -> int :
        factory_id = int(product.factory_id)
        ret = 0
        for prod, amount in self.factory_collectable.get(factory_id, []):
            prod: TSProduct
            if prod.article_id == product.article_id:
                ret += amount
        return ret

    def get_used_uncollectable_factory(self, product: TSProduct) -> int:
        factory_id = int(product.factory_id)
        ret = 0
        for prod, amount in self.factory_uncollectable.get(factory_id, []):
            prod: TSProduct
            if prod.article_id == product.article_id:
                ret += amount
        return ret

    def add_uncollectable_factory(self, product: TSProduct, amount: int):
        factory_id = int(product.factory_id)
        if factory_id not in self.factory_uncollectable:
            self.factory_uncollectable.update({factory_id: []})
        self.factory_uncollectable[factory_id].append((product, amount))

    def add_prepare_factory(self, product: TSProduct, amount: int):
        factory_id = int(product.factory_id)
        if factory_id not in self.factory_prepare:
            self.factory_prepare.update({factory_id: []})
        self.factory_prepare[factory_id].append((product, amount))

    def empty_factory_prepare(self, factory_id: int) -> bool:
        if self.factory_prepare.get(factory_id):
            return False
        return True

    def pop_factory_prepare(self, factory_id: int):
        ret = self.factory_prepare[factory_id].pop(0)
        return ret