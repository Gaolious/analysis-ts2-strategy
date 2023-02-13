import math
from typing import List, Dict

from app_root.players.models import PlayerContract
from app_root.servers.models import RunVersion, TSDestination
from app_root.strategies.commands import ContractActivateCommand, ContractAcceptCommand, send_commands, \
    TrainSendToDestinationCommand, FactoryCollectProductCommand, FactoryOrderProductCommand
from app_root.strategies.data_types import Material, FactoryStrategy, ArticleSource
from app_root.strategies.managers import ship_find_iter, factory_find_player_factory, \
    factory_find_destination_and_factory_only_products, factory_find_product_orders, warehouse_countable, \
    article_find_contract, article_find_product, article_find_destination, warehouse_max_capacity, \
    trains_loads_amount_article_id, warehouse_get_amount, get_number_of_working_dispatchers, trains_find


def get_ship_materials(version: RunVersion) -> Material:
    material = Material()

    for ship in ship_find_iter(version=version):

        remain = (ship.arrival_at - version.now).total_seconds()
        if remain > 2 * 60 * 60:
            continue
        material.add_dict(ship.conditions_to_article_dict)

    return material


def build_article_sources(version: RunVersion) -> Dict[int, ArticleSource]:
    article_source = {}

    countables = warehouse_countable(version=version, basic=True, event=False, union=True)

    for article_id, (article, amount) in countables.items():
        if article_id not in article_source:
            article_source.update({
                article_id: ArticleSource(article=article)
            })

        contract_list = article_find_contract(version=version, article_id=article_id, available_only=False).get(article_id, [])
        for contract in contract_list:
            article_source[article_id].add_contract(contract=contract)

        destination_list = article_find_destination(version=version, article_id=article_id).get(article_id, [])
        for destination in destination_list:
            article_source[article_id].add_destination(dest=destination)

        products_list = article_find_product(version=version, article_id=article_id).get(article_id, [])
        for product in products_list:
            article_source[article_id].add_product(product=product)

    return article_source


def build_factory_strategy(version: RunVersion) -> Dict[int, FactoryStrategy]:
    ret: Dict[int, FactoryStrategy] = {}

    for player_factory in factory_find_player_factory(version=version):
        if player_factory.factory.is_event:
            continue

        destination_product_list, factory_product_list = factory_find_destination_and_factory_only_products(
            version=version,
            player_factory=player_factory
        )
        completed, processing, waiting = factory_find_product_orders(
            version=version,
            factory_id=int(player_factory.factory_id)
        )

        strategy = FactoryStrategy(
            player_factory=player_factory,
            factory_only_products=factory_product_list,
            destination_products=destination_product_list,
        )
        strategy.update(completed=completed, processing=processing, waiting=waiting)

        ret.update({int(player_factory.factory_id): strategy})

        if len(factory_product_list) == 1:
            article_id = int(factory_product_list[0].article_id)
            strategy.strategy_article_count.update({article_id: player_factory.slot_count * 2})

        elif len(factory_product_list) > 1:
            products = sorted(factory_product_list, key=lambda x: (x.craft_time, x.article_amount), reverse=True)

            #   아이템 개수 x 2  <= slot count 이 큰 경우 모두 n개씩 할당
            remain = player_factory.slot_count
            while remain > 0 and len(products) > 0:
                cnt = math.ceil(remain / len(products))
                article_id = int(products[0].article_id)

                strategy.strategy_article_count.update({article_id: cnt})
                remain -= cnt
                del products[0]

    return ret


def get_factory_materials(version: RunVersion, factory_strategy_dict: Dict[int, FactoryStrategy]) -> Material:
    """
        Factory의 개수를 채운다.

    :param version:
    :param factory_strategy_dict:
    :return:
    """
    material = Material()

    for factory_id, strategy in factory_strategy_dict.items():
        completed, processing, waiting = factory_find_product_orders(
            version=version,
            factory_id=factory_id
        )
        strategy.update(completed=completed, processing=processing, waiting=waiting)

        for product in strategy.factory_only_products:
            article_id = int(product.article_id)
            article_amount = int(product.article_amount)

            completed_count = strategy.completed_article_count.get(article_id, 0)
            waiting_count = strategy.waiting_article_count.get(article_id, 0)
            processing_count = strategy.processing_article_count.get(article_id, 0)
            required_count = strategy.strategy_article_count.get(article_id, 0)

            need_more_count = required_count - (processing_count + waiting_count + completed_count)
            if need_more_count <= 0:
                continue

            for required_article_id, required_article_amount in product.conditions_to_article_dict.items():
                material.add(article_id=article_id, amount=required_article_amount)

    return material


def command_collect_factory_product_redundancy(version: RunVersion, factory_strategy_dict: Dict[int, FactoryStrategy], article_source: Dict[int, ArticleSource]):
    """
        창고에 factory 제품 부족분 만큼 채운다.
    :param version:
    :param factory_strategy_dict:
    :param article_source:
    :return:
    """
    warehouse_capacity = warehouse_max_capacity(version=version)
    warehouse_countable_articles = warehouse_countable(version=version, basic=True, event=False, union=False)

    avg_amount = warehouse_capacity // len(warehouse_countable_articles)

    for factory_id, strategy in factory_strategy_dict.items():
        completed, processing, waiting = factory_find_product_orders(
            version=version,
            factory_id=factory_id,
        )
        strategy.update(completed=completed, processing=processing, waiting=waiting)

        for product in strategy.factory_only_products:
            article_id = int(product.article_id)
            completed_count = strategy.completed_article_count.get(article_id, 0)
            waiting_count = strategy.waiting_article_count.get(article_id, 0)
            processing_count = strategy.processing_article_count.get(article_id, 0)
            cnt = completed_count + waiting_count + processing_count

            warehouse_amount = warehouse_get_amount(version=version, article_id=product.article_id)
            product_amount = product.article_amount * min(1, cnt)

            if warehouse_amount + product_amount < avg_amount:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Warehouse[{warehouse_amount} | In Factory[{cnt}*{product.article_amount}] Try Collect")
                command_collect_from_factory(
                    version=version,
                    required_article_id=article_id,
                    required_amount=avg_amount - (warehouse_amount + product_amount),
                    article_source=article_source
                )


def command_factory_strategy(version: RunVersion, factory_strategy_dict: Dict[int, FactoryStrategy], article_source: Dict[int, ArticleSource]):
    """
        계획된 개수만큼 Factory를 채운다.
    :param version:
    :param factory_strategy_dict:
    :param article_source:
    :return:
    """
    for factory_id, strategy in factory_strategy_dict.items():
        completed, processing, waiting = factory_find_product_orders(
            version=version,
            factory_id=factory_id
        )
        strategy.update(completed=completed, processing=processing, waiting=waiting)
        player_factory = factory_find_player_factory(version=version, factory_id=factory_id)
        if isinstance(player_factory, list):
            player_factory = player_factory[0]

        for product in strategy.factory_only_products:
            article_id = int(product.article_id)

            completed_count = strategy.completed_article_count.get(article_id, 0)
            waiting_count = strategy.waiting_article_count.get(article_id, 0)
            processing_count = strategy.processing_article_count.get(article_id, 0)
            required_count = strategy.strategy_article_count.get(article_id, 0)

            need_more_count = required_count - (processing_count + waiting_count + completed_count)
            if need_more_count <= 0:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | PASS")
                continue

            available_slot = player_factory.slot_count - (len(processing) + len(waiting))
            if available_slot <= 0:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Available Slot:{available_slot} | Reach to Max Slot")
                continue
            if len(processing) > 0:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Available Slot:{available_slot} | Producing Now.")
                continue

            need_more_count = min(1, min(available_slot, need_more_count))

            material = Material()
            material.add_dict(product.conditions_to_article_dict)

            if check_all_has_in_warehouse(version=version, requires=material):
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Try Order")
                cmd = FactoryOrderProductCommand(version=version, product=product)
                send_commands(cmd)
            else:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Not Enough Material")


def get_destination_materials(version: RunVersion) -> Material:
    material = Material()

    warehouse_capacity = warehouse_max_capacity(version=version)
    warehouse_countable_articles = warehouse_countable(version=version, basic=True, event=False, union=False)

    avg_amount = int(warehouse_capacity / len(warehouse_countable_articles) * 0.8)

    for article_id, (article, has_amount) in warehouse_countable_articles.items():

        if article.is_event:
            continue
        if article.is_union:
            continue
        if not article.is_take_up_space:
            continue

        destinations = article_find_destination(version=version, article_id=article_id).get(article_id, [])
        if not destinations:
            continue
        # train_amount = trains_loads_amount_article_id(version=version, article_id=article_id)
        #
        # if avg_amount <= has_amount + train_amount:
        #     continue

        material.add(article_id=article_id, amount=avg_amount)

    return material


def check_all_has_in_warehouse(version: RunVersion, requires: Material) -> bool:
    for required_article_id, required_amount in requires.items():
        if required_amount > warehouse_get_amount(version=version, article_id=required_article_id):
            return False
    return True


def command_accept_contract(version: RunVersion, required_article_id: int, required_amount: int, article_source: Dict[int, ArticleSource]):
    # 계약서 사용 가능하면
    source = article_source[required_article_id]

    for contract in source.contracts:
        warehouse_amount = warehouse_get_amount(version=version, article_id=required_article_id)
        if required_amount <= warehouse_amount:
            print(f"    - #{required_article_id} : required:{required_amount} <= {warehouse_amount} | PASS")
            break
        if not contract.is_available(version.now):
            print(f"    - #{required_article_id} : required:{required_amount} <= {warehouse_amount} | Not Available. PASS")
            continue

        contract_materials = Material()
        contract_materials.add_dict(contract.conditions_to_article_dict)
        # 계약서 재료를 수집 시도 해보고,
        command_collect_materials(version=version, requires=contract_materials, article_source=article_source)

        # 계약서 재료가 없으면 pass
        if not check_all_has_in_warehouse(version=version, requires=contract_materials):
            continue

        cmd_list = []
        if not contract.expires_at:
            cmd = ContractActivateCommand(version=version, contract=contract)
            cmd_list.append(cmd)

        cmd = ContractAcceptCommand(version=version, contract=contract)
        cmd_list.append(cmd)

        send_commands(cmd_list)


def command_send_destination(version: RunVersion, required_article_id: int, required_amount: int, article_source: Dict[int, ArticleSource]):

    normal_workers, union_workers = get_number_of_working_dispatchers(version=version)
    source = article_source[required_article_id]

    for destination in source.destinations:

        possible_train = list(trains_find(version=version, **destination.requirements_to_dict, is_idle=True))
        possible_train.sort(key=lambda x: x.capacity(), reverse=True)

        for train in possible_train:
            if normal_workers >= version.dispatchers + 2:
                print(f"    - Dest Location ID #{destination.location_id} / Dispatcher Working:{normal_workers} >= {version.dispatchers+2} | PASS")
                return
            warehouse_amount = warehouse_get_amount(version=version, article_id=required_article_id)
            train_loads_amount = trains_loads_amount_article_id(version=version, article_id=required_article_id)

            if warehouse_amount + train_loads_amount > required_amount:
                return

            cmd = TrainSendToDestinationCommand(
                version=version,
                train=train,
                dest=destination,
                article_id=required_article_id,
                amount=train.capacity(),
            )
            send_commands(cmd)
            normal_workers += 1


def command_collect_from_factory(version: RunVersion, required_article_id: int, required_amount: int, article_source: Dict[int, ArticleSource]):
    source = article_source[required_article_id]

    if source.destinations:
        return

    for product in source.products:
        completed, processing, waiting = factory_find_product_orders(version=version, factory_id=product.factory_id, article_id=required_article_id)
        for order in completed:
            warehouse_amount = warehouse_get_amount(version=version, article_id=required_article_id)
            if required_amount <= warehouse_amount:
                print(f"    - Factory: {product.factory} | required amount={required_amount} <= warehouse={warehouse_amount}| PASS")
                break
            print(f"    - Factory: {product.factory} | Try Collect Item Index={order.index} | required amount={required_amount} > warehouse={warehouse_amount}")
            order.refresh_from_db()
            cmd = FactoryCollectProductCommand(version=version, order=order)
            send_commands(cmd)


def command_collect_materials(version: RunVersion, requires: Material, article_source: Dict[int, ArticleSource]):
    """
    필요한 재료만큼 수집

    :param version:
    :param requires:
    :param article_source:
    :return:
    """
    for required_article_id, required_amount in requires.items():

        command_accept_contract(version=version, required_article_id=required_article_id, required_amount=required_amount, article_source=article_source)

        command_send_destination(version=version, required_article_id=required_article_id, required_amount=required_amount, article_source=article_source)

        command_collect_from_factory(version=version, required_article_id=required_article_id, required_amount=required_amount, article_source=article_source)

