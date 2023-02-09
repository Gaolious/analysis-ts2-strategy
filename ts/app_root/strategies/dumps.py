import datetime
import json
from typing import List, Dict

from django.conf import settings

from app_root.players.models import PlayerDestination, PlayerFactory, PlayerFactoryProductOrder, PlayerWarehouse, \
    PlayerContract, PlayerContractList, PlayerShipOffer, PlayerDailyReward, PlayerWhistle, PlayerDailyOfferContainer, \
    PlayerDailyOffer, PlayerDailyOfferItem
from app_root.servers.models import RunVersion, TSArticle
from app_root.strategies.managers import find_xp, find_key, find_gem, find_gold, trains_find, jobs_find, \
    destination_find, warehouse_used_capacity, warehouse_max_capacity, container_offer_find_iter
from app_root.utils import get_curr_server_datetime, get_remain_time
from core.models.utils import chunk_list


def ts_dump_default(version: RunVersion) -> List[str]:
    ret = []
    line = '-' * 80
    ##########################################################################################
    # 기본
    ##########################################################################################
    lv = f'Lv. {version.level_id}'
    xp = f'XP: {find_xp(version):,d} / {version.level.xp:,d}'
    key = f'Key: {find_key(version):,d}'
    gem = f'Gem: {find_gem(version):,d}'
    gold = f'Gold: {find_gold(version):,d}'
    warehouse = f'Warehouse : {warehouse_used_capacity(version)} / {warehouse_max_capacity(version)}'
    ret.append('# [Default]')
    ret.append(line)
    ret.append(f'{lv:10s} | {xp:20s} | {key:10s} | {gem:10s} | {gold:10s}')
    ret.append(warehouse)
    ret.append('')
    return ret


def ts_dump_working_dispatcher(version: RunVersion) -> List[str]:
    line = '-' * 80
    ret = []

    ##########################################################################################
    # dispatcher
    ##########################################################################################
    trains = list(trains_find(version=version, is_idle=False))

    normal_dispatchers: Dict[str, Dict[int, List]] = {}
    union_dispatchers: Dict[str, Dict[int, List]] = {}
    working_normal_dispatcher_count = 0
    working_union_dispatcher_count = 0
    jobs = {}
    destinations = {}

    """
        + Union Dispatcher
            - Job
                - Trains
            - Destination
                - Trains

        + Normal Dispatcher
            - Job
                - Trains
            - Destination
                - Trains
    """

    def add_normal_dispatcher(route_type: str, key: int, train: object):
        normal_dispatchers.setdefault(route_type, {})
        normal_dispatchers[route_type].setdefault(key, [])
        normal_dispatchers[route_type][key].append(train)

    def add_union_dispatcher(route_type: str, key: int, train: object):
        union_dispatchers.setdefault(route_type, {})
        union_dispatchers[route_type].setdefault(key, [])
        union_dispatchers[route_type][key].append(train)

    for train in trains:
        is_union = False
        data = None

        if train.is_job_route:
            ret_list = list(jobs_find(version=version, job_location_id=train.route_definition_id))
            if ret_list:
                data = ret_list[0]
                is_union = data.job_location.region.is_union
                jobs.setdefault(data.id, data)

        elif train.is_destination_route:
            data = destination_find(version=version, destination_id=train.route_definition_id)
            is_union = data.region.is_union
            destinations.setdefault(data.id, data)

        if is_union:
            working_union_dispatcher_count += 1
            add_union_dispatcher(route_type=train.route_type, key=data.id, train=train)
        else:
            working_normal_dispatcher_count += 1
            add_normal_dispatcher(route_type=train.route_type, key=data.id, train=train)

    ret.append(f'# [Dispatcher - Normal Working {working_normal_dispatcher_count} / {version.dispatchers + 2}]')
    ret.append(line)

    for route_type in normal_dispatchers:
        data_dict = jobs if route_type == 'job' else destinations
        for pk in normal_dispatchers[route_type]:
            ret.append(f' + {route_type} : {data_dict[pk]}')
            for train in normal_dispatchers[route_type][pk]:
                instance_id = f'{train.instance_id:3d}'
                capacity = f'{train.capacity():4d}'
                era = f'{train.train.get_era_display():2s}'
                rarity = f'{train.train.get_rarity_display():2s}'
                name = f'{train.train.asset_name:27s}'
                remain_time = f'{get_remain_time(version=version, finish_at=train.route_arrival_time)}'
                ret.append(
                    f'    Id:{instance_id} / Capacity:{capacity} / era:{era} / rarity:{rarity} / name:{name} / remain:{remain_time} / finish at: {train.route_arrival_time.astimezone(settings.KST)}')
    ret.append('')

    ret.append(f'# [Dispatcher - Union Working {working_union_dispatcher_count} / {version.guild_dispatchers + 2}]')
    ret.append(line)
    for route_type in union_dispatchers:
        data_dict = jobs if route_type == 'job' else destinations
        for pk in union_dispatchers[route_type]:
            ret.append(f' + {route_type} : {data_dict[pk]}')
            for train in union_dispatchers[route_type][pk]:
                instance_id = f'{train.instance_id:3d}'
                capacity = f'{train.capacity():4d}'
                era = f'{train.train.get_era_display():2s}'
                rarity = f'{train.train.get_rarity_display():2s}'
                name = f'{train.train.asset_name:27s}'
                ret.append(f'    Id:{instance_id} / Capacity:{capacity} / era:{era} / rarity:{rarity} / name:{name}')
    ret.append('')

    return ret


def ts_dump_jobs(version: RunVersion) -> List[str]:
    ret = []
    line = '-' * 80

    ret.append(f'# [Jobs]')
    ret.append(line)
    union_jobs = list(jobs_find(version=version, union_jobs=True))
    if len(union_jobs) > 0:
        ret.append('Union Jobs')
        for job in union_jobs:
            ret.append(f'    {job}')
    else:
        ret.append('Union Jobs 없음')

    event_jobs = list(jobs_find(version=version, event_jobs=True))
    if len(event_jobs) > 0:
        ret.append('Event Jobs')
        for job in event_jobs:
            ret.append(f'    {job}')
    else:
        ret.append('Event Jobs 없음')

    story_jobs = list(jobs_find(version=version, story_jobs=True))
    if len(story_jobs) > 0:
        ret.append('Story Jobs')
        for job in story_jobs:
            ret.append(f'    {job}')
    else:
        ret.append('Story Jobs 없음')

    ret.append('')
    return ret


def ts_dump_destination(version: RunVersion) -> List[str]:
    ret = []
    line = '-' * 80

    ret.append(f'# [Destination]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)

    for destination in PlayerDestination.objects.filter(version_id=version.id).order_by('pk').all():
        if destination.is_available(now=now):
            remain_time = '사용가능'
        else:
            remain_time = f'{get_remain_time(version=version, finish_at=destination.train_limit_refresh_at)}'
        ret.append(f' - Location : {destination.location_id} / remain: {remain_time}')
    ret.append('')
    return ret


def ts_dump_factory(version: RunVersion):
    ret = []
    line = '-' * 80

    ret.append('# [Factory]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)

    queryset = PlayerFactory.objects.filter(version_id=version.id).order_by('id').select_related('factory').all()

    for factory in queryset.all():
        ret.append(f"""  Factory - #{factory.factory_id} {factory.factory}""")
        completed_list = []
        processing_list = []
        waiting_list = []

        for order in PlayerFactoryProductOrder.objects.filter(player_factory_id=factory.id).select_related('article').order_by('index').all():
            if order.is_completed(now):
                completed_list.append(order)
            elif order.is_processing(now):
                processing_list.append(order)
            elif order.is_waiting(now):
                waiting_list.append(order)
            else:
                raise Exception(str(order))

        a = [f'[#{o.id}/{o.article.sprite}/{order.amount}개]' for o in completed_list]
        b = [f'[#{o.id}/{o.article.sprite}/{order.amount}개]' for o in processing_list]
        c = [f'[#{o.id}/{o.article.sprite}/{order.amount}개]' for o in waiting_list]

        ret.append(f'''    대기 : {' '.join(c)}''')
        ret.append(f'''    생성 : {' '.join(b)}''')
        ret.append(f'''    완료 : {' '.join(a)}''')

    ret.append('')
    return ret


def ts_dump_warehouse(version: RunVersion) -> List[str]:
    ret = []
    line = '-' * 80

    ret.append('# [Warehouse]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)

    queryset = PlayerWarehouse.objects.filter(
        version_id=version.id,
        article__level_from__lte=version.level_id
    ).order_by(
        'article__type'
    ).select_related(
        'article'
    ).all()

    countable: Dict[int, List[PlayerWarehouse]] = {}

    for warehouse in queryset:
        warehouse: PlayerWarehouse
        countable.setdefault(warehouse.article.type, [])
        countable[warehouse.article.type].append(warehouse)

    for article_type in countable:
        ret.append(f'  + [Article Type : {article_type}]')
        for rows in chunk_list(countable[article_type], chunk_size=6):
            s = [f'[{o.article_id:6d}|{o.article.name:18s}:{o.amount:5d}]' for o in rows]

            ret.append(f'''    {' '.join(s)}''')

    ret.append('')
    return ret


def ts_dump_ship(version: RunVersion) -> List[str]:
    ret = []
    line = '-' * 80

    ret.append('# [Ship]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)
    queryset = PlayerShipOffer.objects.filter(version_id=version.id).all()

    for ship in queryset:
        reward_dict = ship.reward_to_article_dict
        reward_articles = {o.id: o for o in TSArticle.objects.filter(id__in=reward_dict.keys()).all()}
        str_reward = [
            f'''[{article_id}|{reward_articles[article_id].name}:{article_amount}]'''
            for article_id, article_amount in reward_dict.items()
        ]

        condition_dict = ship.conditions_to_article_dict
        condition_articles = {o.id: o for o in TSArticle.objects.filter(id__in=condition_dict.keys()).all()}
        str_condition = [
            f'''[{article_id}|{condition_articles[article_id].name}:{article_amount}]'''
            for article_id, article_amount in condition_dict.items()
        ]

        ret.append(f'''   arrival_at : {ship.arrival_at} | remain : {get_remain_time(version=version, finish_at=ship.arrival_at)}''')
        ret.append(f'''   expire_at : {ship.expire_at} | remain : {get_remain_time(version=version, finish_at=ship.expire_at)}''')
        ret.append(f'''   conditions : {' '.join(str_condition)}''')
        ret.append(f'''   reward : {' '.join(str_reward)}''')
    ret.append('')
    return ret


def ts_dump_contract(version: RunVersion) -> List[str]:
    ret = []
    line = '-' * 80

    ret.append('# [Contract]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)

    for contract_list in PlayerContractList.objects.filter(version_id=version.id).all():
        ret.append(f''' contract_list : {contract_list.contract_list_id} : ''')
        ret.append(f''' available : {contract_list.available_to} | remain : {get_remain_time(version=version, finish_at=contract_list.available_to)}''')
        ret.append(f''' next_replace_at : {contract_list.next_replace_at} | remain : {get_remain_time(version=version, finish_at=contract_list.next_replace_at)}''')
        ret.append(f''' next_video_replace_at : {contract_list.next_video_replace_at} | remain : {get_remain_time(version=version, finish_at=contract_list.next_video_replace_at)}''')
        ret.append(f''' next_video_rent_at : {contract_list.next_video_rent_at} | remain : {get_remain_time(version=version, finish_at=contract_list.next_video_rent_at)}''')
        ret.append(f''' next_video_speed_up_at : {contract_list.next_video_speed_up_at} | remain : {get_remain_time(version=version, finish_at=contract_list.next_video_speed_up_at)}''')

        for contract in PlayerContract.objects.filter(contract_list_id=contract_list.id).all():
            reward_dict = contract.reward_to_article_dict
            reward_articles = {o.id: o for o in TSArticle.objects.filter(id__in=reward_dict.keys()).all()}
            str_reward = [
                f'''[{article_id}|{reward_articles[article_id].name}:{article_amount}]'''
                for article_id, article_amount in reward_dict.items()
            ]

            condition_dict = contract.conditions_to_article_dict
            condition_articles = {o.id: o for o in TSArticle.objects.filter(id__in=condition_dict.keys()).all()}
            str_condition = [
                f'''[{article_id}|{condition_articles[article_id].name}:{article_amount}]'''
                for article_id, article_amount in condition_dict.items()
            ]

            if contract.is_available(now):
                msg = '가능'
            else:
                msg = '대기'
            ret.append(f'''   Slot : {contract.slot:2d} | {msg} / 필요: {' '.join(str_condition):20s} / 보상: {' '.join(str_reward):20s}''')
            # ret.append(f'''   usable_from : {contract.usable_from} | remain : {get_remain_time(version=version, finish_at=contract.usable_from)}''')
            # ret.append(f'''   available_from : {contract.available_from} | remain : {get_remain_time(version=version, finish_at=contract.available_from)}''')
            # ret.append(f'''   available_to : {contract.available_to} | remain : {get_remain_time(version=version, finish_at=contract.available_to)}''')
            # ret.append(f'''   expires_at : {contract.expires_at} | remain : {get_remain_time(version=version, finish_at=contract.expires_at)}''')
    ret.append('')
    return ret


def ts_dump_daily_reward(version: RunVersion):
    ret = []
    line = '-' * 80

    ret.append('# [Daily Reward]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)
    queryset = PlayerDailyReward.objects.filter(version_id=version.id).all()
    for daily in queryset:
        ret.append(f'''   available_from : {daily.available_from} | remain : {get_remain_time(version=version, finish_at=daily.available_from)}''')
        ret.append(f'''   expire_at : {daily.expire_at} | remain : {get_remain_time(version=version, finish_at=daily.expire_at)}''')
        ret.append(f'''   rewards : {daily.rewards}''')
        ret.append(f'''   pool_id : {daily.pool_id}''')
        ret.append(f'''   day : {daily.day}''')
        pass
    ret.append('')
    return ret


def ts_dump_daily_offer(version: RunVersion):
    ret = []
    line = '-' * 80

    ret.append('# [Daily Offer]')
    ret.append(line)
    now = get_curr_server_datetime(version=version)
    queryset = PlayerDailyOffer.objects.filter(version_id=version.id).all()
    for daily in queryset:
        ret.append(f'''   expire_at : {daily.expire_at} | remain : {get_remain_time(version=version, finish_at=daily.expire_at)}''')
        ret.append(f'''   expires_at : {daily.expires_at} | remain : {get_remain_time(version=version, finish_at=daily.expires_at)}''')

        for item in PlayerDailyOfferItem.objects.filter(daily_offer_id=daily.id).all():
            purchased = '가능' if item.purchased == False else '완료'

            required = f'''[{item.price_id}|{item.price.name}:{item.price_amount}]'''
            rewards = []
            for reward in json.loads(item.reward)['Items']:
                _id = reward.get('Id')
                _value = reward.get('Value')
                _amount = reward.get('Amount')

                article = TSArticle.objects.filter(id=_value).first()
                if not article:
                    rewards.append(
                        f'''[{reward}]'''
                    )
                elif _amount:
                    rewards.append(
                        f'''[{article.id}|{article.name}:{_amount}]'''
                    )
                else:
                    rewards.append(
                        f'''[{article.id}|{article.name}]'''
                    )

            ret.append(f'''       Slot: {item.slot:2d} | {purchased} | {required:20s} | {','.join(rewards)}''')

    ret.append('')
    return ret


def ts_dump_offer_container(version: RunVersion):
    ret = []
    line = '-' * 80

    ret.append('# [Offer Container]')
    ret.append(line)

    now = get_curr_server_datetime(version=version)
    for offer in container_offer_find_iter(version=version, available_only=False):

        next_event = offer.last_bought_at + datetime.timedelta(seconds=offer.offer_container.cooldown_duration)
        ret.append(f'''   offer_container: {offer.offer_container_id}, Cnt:{offer.count}, Last Bought: {offer.last_bought_at}, Next : {next_event}|remain:{get_remain_time(version=version, finish_at=next_event)}''')
        pass
    ret.append('')
    return ret


def ts_dump_whistle(version: RunVersion):
    ret = []
    line = '-' * 80

    ret.append('# [Whistle]')
    ret.append(line)

    now = get_curr_server_datetime(version=version)
    queryset = PlayerWhistle.objects.filter(version_id=version.id).all()
    for whistle in queryset:
        ret.append(f'''   category: {whistle.category} | Position: {whistle.position} | spawn_time : {whistle.spawn_time} | remain : {get_remain_time(version=version, finish_at=whistle.spawn_time)} | collectable_from : {whistle.collectable_from} | remain : {get_remain_time(version=version, finish_at=whistle.collectable_from)} | expires_at : {whistle.expires_at} | remain : {get_remain_time(version=version, finish_at=whistle.expires_at)}''')
        pass
    ret.append('')
    return ret


def ts_dump(version: RunVersion):
    ret = []
    ret += ts_dump_default(version=version)

    ret += ts_dump_working_dispatcher(version=version)

    ret += ts_dump_jobs(version=version)

    ret += ts_dump_destination(version=version)

    ret += ts_dump_factory(version=version)

    # ship
    ret += ts_dump_ship(version=version)

    # warehouse
    ret += ts_dump_warehouse(version=version)

    # contract
    ret += ts_dump_contract(version=version)

    # daily reward
    ret += ts_dump_daily_reward(version=version)

    # daily offer
    ret += ts_dump_daily_offer(version=version)

    # offer container
    ret += ts_dump_offer_container(version=version)

    # whistle
    ret += ts_dump_whistle(version=version)

    base_path = settings.SITE_PATH / 'dump' / f'{version.user.username}'
    base_path.mkdir(0o755, True, exist_ok=True)

    str_dt = version.created.strftime('%Y%m%d_%H%M%S')
    filename = base_path / f'{version.id}_{str_dt}.txt'
    with open(filename, 'wt') as fout:
        for row in ret:
            s = f' {row:80s}'
            print(s)
            fout.write(s + '\n')
        print()
