import math
from typing import List, Dict, Tuple

from app_root.players.models import PlayerContract, PlayerQuest, PlayerVisitedRegion, PlayerJob, PlayerFactory, \
    PlayerFactoryProductOrder
from app_root.servers.models import RunVersion, TSDestination, TSProduct, TSArticle, TSJobLocation
from app_root.strategies.commands import ContractActivateCommand, ContractAcceptCommand, send_commands, \
    TrainSendToDestinationCommand, FactoryCollectProductCommand, FactoryOrderProductCommand, \
    ContractAcceptWithVideoReward, GameSleep, GameWakeup
from app_root.strategies.data_types import Material, FactoryStrategy, ArticleSource, MaterialStrategy
from app_root.strategies.managers import ship_find_iter, factory_find_player_factory, \
    factory_find_destination_and_factory_only_products, factory_find_product_orders, warehouse_countable, \
    article_find_contract, article_find_product, article_find_destination, warehouse_max_capacity, \
    trains_loads_amount_article_id, warehouse_get_amount, get_number_of_working_dispatchers, trains_find, \
    warehouse_used_capacity, warehouse_avg_count, contract_get_ship
from app_root.utils import get_curr_server_str_datetime_s


def get_ship_materials(version: RunVersion) -> Material:
    material = Material()

    for ship in ship_find_iter(version=version):

        remain = (ship.arrival_at - version.now).total_seconds()
        if remain > 1 * 60 * 60:
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
                material.add(article_id=required_article_id, amount=required_article_amount)

    return material


def command_collect_factory_product_redundancy(version: RunVersion, factory_strategy_dict: Dict[int, FactoryStrategy], article_source: Dict[int, ArticleSource]):
    """
        창고에 factory 제품 부족분 만큼 채운다.
    :param version:
    :param factory_strategy_dict:
    :param article_source:
    :return:
    """
    avg_amount = warehouse_avg_count(version=version)

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
            product_amount = product.article_amount

            if warehouse_amount + product_amount < avg_amount:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Warehouse[{warehouse_amount} | In Factory[{cnt}*{product.article_amount}] Try Collect")
                material = Material()
                material.add_dict(product.conditions_to_article_dict)
                command_collect_factory_if_possible(
                    version=version,
                    required_article_id=article_id,
                    required_amount=avg_amount - product_amount,
                    article_source=article_source
                )


def command_order_product_in_factory(version: RunVersion, product: TSProduct, count: int):
    article_id = int(product.article_id)
    factory_id = int(product.factory_id)

    player_factory = factory_find_player_factory(version=version, factory_id=factory_id)
    if isinstance(player_factory, list):
        player_factory = player_factory[0]

    material = Material()
    material.add_dict(product.conditions_to_article_dict)

    for _ in range(count):
        completed, processing, waiting = factory_find_product_orders(
            version=version,
            factory_id=factory_id
        )
        completed_count = len(completed)
        waiting_count = len(waiting)
        processing_count = len(processing)
        available_slot = player_factory.slot_count - processing_count - waiting_count
        if available_slot < 1:
            break

        if not check_all_has_in_warehouse(version=version, requires=material):
            break

        cmd = FactoryOrderProductCommand(version=version, product=product)
        send_commands(cmd)

    if count == 0:
        return True

    return False


def command_send_destination(version: RunVersion, destination: TSDestination, amount: int):
    normal_workers, union_workers = get_number_of_working_dispatchers(version=version)
    required_article_id = int(destination.article_id)

    possible_train = list(trains_find(version=version, **destination.requirements_to_dict, is_idle=True))
    possible_train.sort(key=lambda x: x.capacity(), reverse=True)

    send_amount = 0

    used = warehouse_used_capacity(version=version)
    max_capacity = warehouse_max_capacity(version=version)
    train_loads_amount = trains_loads_amount_article_id(version=version, article_id=required_article_id)
    amount -= train_loads_amount

    for train in possible_train:
        if normal_workers >= version.dispatchers + 2:
            print(
                f"    - Dest Location ID #{destination.location_id} / Dispatcher Working:{normal_workers} >= {version.dispatchers + 2} | PASS")
            break
        if used + train.capacity() + send_amount > max_capacity:
            print(
                f"    - Dest Location ID #{destination.location_id} / Train[{train.capacity()}] + used Warehouse[{used}] > max Warehouse[{max_capacity}] | PASS")
            break
        if send_amount >= amount:
            break

        cmd = TrainSendToDestinationCommand(
            version=version,
            train=train,
            dest=destination,
            article_id=required_article_id,
            amount=train.capacity(),
        )
        send_commands(cmd)
        send_amount += train.capacity()
        normal_workers += 1


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

            if need_more_count < 0:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Try Collect")
                command_collect_factory(version=version, product=product, count=-need_more_count)
                continue

            if need_more_count == 0:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Satisfied | PASS")
                continue

            available_slot = player_factory.slot_count - (len(processing) + len(waiting))
            if available_slot <= 0:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Available Slot:{available_slot} | Reach to Max Slot")
                continue
            # if len(processing) > 0:
            #     print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Available Slot:{available_slot} | Producing Now.")
            #     continue

            need_more_count = min(1, min(available_slot, need_more_count))

            material = Material()
            material.add_dict(product.conditions_to_article_dict)

            if check_all_has_in_warehouse(version=version, requires=material):
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Try Order")
                command_order_product_in_factory(version=version, product=product, count=1)
            else:
                print(f"    - Factory: {product.factory} | Article[#{product.article_id}|{product.article.name}] | Need {need_more_count} | Not Enough Material")


def get_destination_materials(version: RunVersion) -> Material:
    material = Material()

    warehouse_countable_articles = warehouse_countable(version=version, basic=True, event=False, union=False)

    avg_amount = warehouse_avg_count(version=version, warehouse_countable_articles=warehouse_countable_articles)

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

        material.add(article_id=article_id, amount=avg_amount)

    return material


def check_all_has_in_warehouse(version: RunVersion, requires: Material) -> bool:
    for required_article_id, required_amount in requires.items():
        if required_amount > warehouse_get_amount(version=version, article_id=required_article_id):
            return False
    return True


def command_trade_contract(version: RunVersion, contract: PlayerContract):
    """
    배 계약서
    :param version:
    :param contract:
    :return:
    """
    if not contract:
        return
    contract.refresh_from_db()

    if not contract.is_available(version.now):
        print(f"    - Contract Slot : {contract.slot} Not Available | PASS")
        return

    if contract.expires_at is None:
        cmd = ContractActivateCommand(version=version, contract=contract)
        send_commands([cmd])

    contract.refresh_from_db()
    if contract.expires_at is None:
        return

    contract_materials = Material()
    contract_materials.add_dict(contract.conditions_to_article_dict)

    # 계약서 재료가 없으면 pass
    if not check_all_has_in_warehouse(version=version, requires=contract_materials):
        print(f"    - Contract Slot : {contract.slot} Not enough material | PASS")
        return

    accept_at = get_curr_server_str_datetime_s(version=version)
    cmd = GameSleep(version=version, sleep_seconds=30)
    send_commands(commands=cmd)

    cmd_list = [
        GameWakeup(version=version),
        ContractAcceptWithVideoReward(version=version, contract=contract, accept_at=accept_at)
    ]

    send_commands(cmd_list)


def command_collect_contract(version: RunVersion, contract: PlayerContract):
    # 계약서 사용 가능하면
    contract.refresh_from_db()

    if not contract.is_available(version.now):
        print(f"    - Contract Slot : {contract.slot} Not Available | PASS")
        return

    if contract.expires_at is None:
        cmd = ContractActivateCommand(version=version, contract=contract)
        send_commands([cmd])

    contract.refresh_from_db()
    if contract.expires_at is None:
        return

    contract_materials = Material()
    contract_materials.add_dict(contract.conditions_to_article_dict)

    # 계약서 재료가 없으면 pass
    if not check_all_has_in_warehouse(version=version, requires=contract_materials):
        print(f"    - Contract Slot : {contract.slot} Not enough material | PASS")
        return

    cmd = ContractAcceptCommand(version=version, contract=contract)
    send_commands([cmd])


def command_collect_contract_if_possible(version: RunVersion, required_article_id: int, required_amount: int, article_source: Dict[int, ArticleSource]):
    # 계약서 사용 가능하면
    source = article_source[required_article_id]

    for contract in source.contracts:
        contract.refresh_from_db()

        if not contract.is_available(version.now):
            continue

        if contract.expires_at is None:
            cmd = ContractActivateCommand(version=version, contract=contract)
            send_commands([cmd])

        contract.refresh_from_db()
        if contract.expires_at is None:
            continue

        warehouse_amount = warehouse_get_amount(version=version, article_id=required_article_id)
        if required_amount <= warehouse_amount:
            print(f"    - #{required_article_id} : required:{required_amount} <= {warehouse_amount} | PASS")
            break
        if not contract.is_available(version.now):
            print(f"    - #{required_article_id} : required:{required_amount} <= {warehouse_amount} | Not Available. PASS")
            continue

        contract_materials = Material()
        contract_materials.add_dict(contract.conditions_to_article_dict)

        # 계약서 재료가 없으면 pass
        if not check_all_has_in_warehouse(version=version, requires=contract_materials):
            continue

        cmd = ContractAcceptCommand(version=version, contract=contract)
        send_commands([cmd])


def command_collect_destination_if_possible(version: RunVersion, required_article_id: int, required_amount: int, article_source: Dict[int, ArticleSource]):

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

            used = warehouse_used_capacity(version=version)
            max_capacity = warehouse_max_capacity(version=version)
            if used + train.capacity() > max_capacity:
                print(f"    - Dest Location ID #{destination.location_id} / Train[{train.capacity()}] + used Warehouse[{used}] > max Warehouse[{max_capacity}] | PASS")
                continue

            cmd = TrainSendToDestinationCommand(
                version=version,
                train=train,
                dest=destination,
                article_id=required_article_id,
                amount=train.capacity(),
            )
            send_commands(cmd)
            normal_workers += 1


def command_collect_factory(version: RunVersion, product: TSProduct, count: int):
    factory_id = int(product.factory_id)
    article_id = int(product.article_id)

    completed, processing, waiting = factory_find_product_orders(version=version, factory_id=factory_id, article_id=article_id)

    cnt = 0
    for order in completed:
        if cnt >= count:
            return
        cnt += 1

        order: PlayerFactoryProductOrder
        order.refresh_from_db()

        used = warehouse_used_capacity(version=version)
        max_capacity = warehouse_max_capacity(version=version)

        if used + order.amount > max_capacity:
            continue

        cmd = FactoryCollectProductCommand(version=version, order=order)
        send_commands(cmd)


def command_collect_factory_if_possible(version: RunVersion, required_article_id: int, required_amount: int, article_source: Dict[int, ArticleSource]):
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

            used = warehouse_used_capacity(version=version)
            max_capacity = warehouse_max_capacity(version=version)
            if used + order.amount > max_capacity:
                print(f"    - Factory: {product.factory} | Try Collect Item Index={order.index} | amount={required_amount} + used Warehouse[{used}] > max Warehouse[{max_capacity}] | PASS")
                continue

            print(f"    - Factory: {product.factory} | Try Collect Item Index={order.index} | required amount={required_amount} > warehouse={warehouse_amount}")
            order.refresh_from_db()
            command_order_product_in_factory(version=version, product=product, count=1)

            cmd = FactoryCollectProductCommand(version=version, order=order)
            send_commands(cmd)


def command_collect_materials_if_possible(version: RunVersion, requires: Material, article_source: Dict[int, ArticleSource]):
    """
    필요한 재료만큼 수집

    :param version:
    :param requires:
    :param article_source:
    :return:
    """
    for required_article_id, required_amount in requires.items():

        command_collect_contract_if_possible(version=version, required_article_id=required_article_id, required_amount=required_amount, article_source=article_source)

        command_collect_destination_if_possible(version=version, required_article_id=required_article_id, required_amount=required_amount, article_source=article_source)

        command_collect_factory_if_possible(version=version, required_article_id=required_article_id, required_amount=required_amount, article_source=article_source)


def material_strategy_add_queue(
        version: RunVersion,
        requires: Material,
        article_source: Dict[int, ArticleSource],
        strategy: MaterialStrategy,
        warehouse_count: Dict[int, Tuple[TSArticle, int]],
        depth: int = 1
):
    ret = []

    for required_article_id, required_article_amount in requires.items():
        source = article_source.get(required_article_id)
        if source.contracts:
            if required_article_amount * 2 < warehouse_get_amount(version=version, article_id=required_article_id):
                ret.append(f'''{'  ' * depth} - Required:[{source.article}] - Enough material (more than x2)| PASS''')
                continue

            s = 0
            for contract in source.contracts:
                if s >= required_article_amount: break
                amount = sum([v for k, v in contract.reward_to_article_dict.items() if k == required_article_id])
                s += amount
                strategy.push_contract(contract)
                ret.append(f'''{'  ' * depth} - Required:[{source.article}] - Contract Slot[{contract.slot}][{amount} 개]''')

        elif source.destinations:
            warehouse_amount = 0
            wc = warehouse_count.get(required_article_id)
            if wc:
                warehouse_amount = wc[1]

            remain_warehouse_amount = warehouse_amount - strategy.get_used_warehouse(required_article_id)
            used_warehouse_amount = min(required_article_amount, remain_warehouse_amount)
            strategy.add_used_warehouse(article_id=required_article_id, amount=used_warehouse_amount)
            required_article_amount -= used_warehouse_amount

            if required_article_amount > 0:
                ret.append(f'''{'  ' * depth} - Required:[{source.article}] - Destination[{source.destinations[0].id}][{required_article_amount} 개]''')
                strategy.push_destination(source.destinations[0], required_article_amount)

        elif source.products:
            ret.append(f'''{'  ' * depth} - Required:[{source.article}] - Product[{required_article_amount} 개]''')
            strategy.push_factory(source.products[0], required_article_amount)

    print(f'''{'  ' * depth}# material_strategy_add_queue''')
    print('\n'.join(ret))


def material_strategy_contract(
        version: RunVersion,
        article_source: Dict[int, ArticleSource],
        strategy: MaterialStrategy,
        warehouse_count: Dict[int, Tuple[TSArticle, int]],
        depth: int = 1
):
    while not strategy.empty_contract():
        contract = strategy.pop_contract()

        material = Material()
        material.add_dict(contract.conditions_to_article_dict)
        required_material_name = []

        all_satisfied = True
        for required_article_id, required_article_amount in material.items():
            warehouse_amount = 0
            ret = warehouse_count.get(required_article_id)
            article = None
            if ret:
                article = ret[0]
                warehouse_amount = ret[1]
            if article:
                required_material_name.append(
                    f'[{article}:{required_article_amount}개]'
                )
            if warehouse_amount < required_article_amount + strategy.get_used_warehouse(required_article_id):
                all_satisfied = False
                break

        if all_satisfied:
            print(f'''{'  ' * depth} - Check Contract Slot[{contract.slot}] (Require:{'|'.join(required_material_name)}) - You Can collect''')
            strategy.add_collectable_contract(contract)
        else:
            print(f'''{'  ' * depth} - Check Contract Slot[{contract.slot}] (Require:{'|'.join(required_material_name)}) - Not Enough''')

            material_strategy_add_queue(
                version=version,
                requires=material,
                article_source=article_source,
                strategy=strategy,
                warehouse_count=warehouse_count,
                depth=depth+1,
            )


def material_strategy_factory(
        version: RunVersion,
        article_source: Dict[int, ArticleSource],
        strategy: MaterialStrategy,
        warehouse_count: Dict[int, Tuple[TSArticle, int]]
):
    player_factories = factory_find_player_factory(version=version)
    product_orders = {}

    for player_factory in player_factories:
        factory_id = int(player_factory.factory_id)
        product_orders.update({
            factory_id: factory_find_product_orders(version=version, factory_id=factory_id)
        })

    while not strategy.all_empty_factory():

        for player_factory in player_factories:
            factory_id = int(player_factory.factory_id)

            completed, processing, waiting = product_orders[factory_id]

            while not strategy.empty_factory_queue(factory_id=factory_id):
                product, required_article_amount = strategy.pop_factory(factory_id=factory_id)
                required_article_id = product.article_id

                completed_amount = sum([c.amount for c in completed if c.article_id == required_article_id])
                processing_amount = sum([c.amount for c in processing if c.article_id == required_article_id])
                waiting_amount = sum([c.amount for c in waiting if c.article_id == required_article_id])
                uncompleted_amount = processing_amount + waiting_amount

                completed_amount -= strategy.get_used_collectable_factory(product=product)
                uncompleted_amount -= strategy.get_used_uncollectable_factory(product=product)

                warehouse_amount = 0
                ret = warehouse_count.get(required_article_id)
                if ret:
                    warehouse_amount = ret[1]

                remain_warehouse_amount = warehouse_amount - strategy.get_used_warehouse(required_article_id)

                used_warehouse_amount = min(required_article_amount, remain_warehouse_amount)
                if used_warehouse_amount > 0:
                    strategy.add_used_warehouse(product.article_id, required_article_amount)
                    remain_warehouse_amount -= used_warehouse_amount
                    required_article_amount -= used_warehouse_amount

                used_completed_product_amount = min(completed_amount, required_article_amount)
                if used_completed_product_amount > 0:
                    strategy.add_collectable_factory(product, used_completed_product_amount)
                    completed_amount -= used_completed_product_amount
                    required_article_amount -= used_completed_product_amount

                used_uncompleted_product_amount = min(uncompleted_amount, required_article_amount)
                if used_uncompleted_product_amount > 0:
                    strategy.add_uncollectable_factory(product, used_uncompleted_product_amount)
                    uncompleted_amount -= used_uncompleted_product_amount
                    required_article_amount -= used_uncompleted_product_amount

                if required_article_amount > 0:
                    strategy.add_prepare_factory(product, required_article_amount)

        material = Material()

        for player_factory in player_factories:
            factory_id = int(player_factory.factory_id)
            condition = {}
            products = {}

            while not strategy.empty_factory_prepare(factory_id=factory_id):
                product, amount = strategy.pop_factory_prepare(factory_id=factory_id)
                article_id = product.article_id
                products.update({article_id: product})

                condition.setdefault(article_id, 0)
                condition[article_id] += amount

            for article_id, amount in condition.items():
                if amount < 1: continue

                product: TSProduct = products[article_id]
                cnt = math.ceil(amount / product.article_amount)

                for k, v in product.conditions_to_article_dict.items():
                    # product#13 / 40개 짜리 - 43개 필요시
                    # product#13의 부품 * 2배.
                    material.add(article_id=k, amount=v * cnt)

        material_strategy_add_queue(
            version=version,
            requires=material,
            article_source=article_source,
            strategy=strategy,
            warehouse_count=warehouse_count
        )


def expand_material_strategy(
        version: RunVersion,
        requires: Material,
        article_source: Dict[int, ArticleSource],
        strategy: MaterialStrategy,
) -> Tuple[bool, MaterialStrategy]:
    """
        필요한 재료 material 에 대해

        창고 수량을 체크하여, 추가 필요분 체크.

    :param strategy:
    :param version:
    :param requires:
    :param article_source:
    :return:
    """
    warehouse_count = warehouse_countable(version=version, basic=True, event=False, union=True)

    print('# [Expand Material Condition]')
    print('--------------------------------------------------------------------------------')

    material_strategy_add_queue(version=version, requires=requires, article_source=article_source, strategy=strategy, warehouse_count=warehouse_count)

    # Step 1. Contracts.
    material_strategy_contract(version=version, article_source=article_source, strategy=strategy, warehouse_count=warehouse_count)

    # Step 2. material_strategy_factory
    material_strategy_factory(version=version, article_source=article_source, strategy=strategy, warehouse_count=warehouse_count)


def command_material_strategy(
        version: RunVersion,
        strategy: MaterialStrategy,
):

    for destination, amount in strategy.destination_queue:
        article_id = int(destination.article_id)
        train_loads_amount = trains_loads_amount_article_id(version=version, article_id=article_id)
        amount -= train_loads_amount
        if amount > 0:
            command_send_destination(version=version, destination=destination, amount=amount)

    for factory_id in strategy.factory_uncollectable:
        for product, amount in strategy.factory_uncollectable[factory_id]:
            cnt = math.ceil(amount / product.article_amount)
            command_order_product_in_factory(version=version, product=product, count=cnt)

    for factory_id in strategy.factory_collectable:
        for product, amount in strategy.factory_collectable[factory_id]:
            cnt = math.ceil(amount / product.article_amount)
            command_collect_factory(version=version, product=product, count=cnt)

    for contract in strategy.contract_collectable:
        command_collect_contract(version=version, contract=contract)


def command_ship_trade(
        version: RunVersion,
        requires: Material,
        article_source: Dict[int, ArticleSource],
        strategy: MaterialStrategy,
):
    expand_material_strategy(
        version=version,
        requires=requires,
        article_source=article_source,
        strategy=strategy,
    )
    command_material_strategy(
        version=version,
        strategy=strategy
    )
    contract = contract_get_ship(version=version)
    if contract:
        command_trade_contract(version=version, contract=contract)