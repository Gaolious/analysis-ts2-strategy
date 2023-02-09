import math
from datetime import timedelta, datetime
from typing import List, Set, Dict, Type, Optional, Tuple

from django.conf import settings

from app_root.players.models import PlayerJob, PlayerTrain, PlayerVisitedRegion, PlayerContract, PlayerContractList, \
    PlayerWarehouse, PlayerDailyReward, PlayerWhistle, PlayerDestination, PlayerDailyOfferContainer, PlayerDailyOffer, \
    PlayerDailyOfferItem, PlayerShipOffer
from app_root.servers.models import RunVersion, TSProduct, TSDestination, TSWarehouseLevel, TSArticle, TSFactory
from app_root.utils import get_curr_server_datetime


def update_next_event_time(previous: Optional[datetime], event_time: Optional[datetime]) -> datetime:
    """
        이벤트 발생시간 계산.

    :param previous:
    :param event_time:
    :return:
    """
    if not previous or not event_time:
        return previous or event_time
    if previous > event_time:
        return event_time
    return previous


###########################################################################
# Job 검색
###########################################################################
def jobs_find(
        version: RunVersion,
        event_jobs: bool = None,
        union_jobs: bool = None,
        story_jobs: bool = None,
        side_jobs: bool = None,
        collectable_jobs: bool = None,
        completed_jobs: bool = None,
        expired_jobs: bool = None,
        job_location_id: int = None,
) -> List[PlayerJob]:
    """
        Job를 검색 합니다.

    :param job_location_id:
    :param version:
    :param event_jobs:
    :param union_jobs:
    :param story_jobs:
    :param side_jobs:
    :param collectable_jobs:
    :param completed_jobs:
    :param expired_jobs:
    :return:
    """
    queryset = PlayerJob.objects.filter(version_id=version.id).all()
    now = get_curr_server_datetime(version=version)

    ret = []
    for job in queryset.all():
        if event_jobs is not None and event_jobs != job.is_event_job:
            continue
        if union_jobs is not None and union_jobs != job.is_union_job:
            continue
        if story_jobs is not None and story_jobs != job.is_story_job:
            continue
        if side_jobs is not None and side_jobs != job.is_side_job:
            continue
        if collectable_jobs is not None and collectable_jobs != job.is_collectable(now):
            continue
        if completed_jobs is not None and completed_jobs != job.is_completed(now):
            continue
        if expired_jobs is not None and expired_jobs != job.is_expired(now):
            continue
        if job_location_id is not None and job_location_id != job.job_location_id:
            continue

        ret.append(job)

    return ret

###########################################################################
# 기차 검색
###########################################################################
def trains_find(
        version: RunVersion,
        available_region: Set[int] = None,
        available_rarity: Set[int] = None,
        available_era: Set[int] = None,
        available_min_power: int = None,
        available_content_category: Set[int] = None,
        is_idle: bool = None,
        has_load: bool = None
) -> List[PlayerTrain]:
    """
        가용 가능한 기차를 검색 합니다.

    :param version:
    :param available_region: {1,2,3, ...}
    :param available_rarity: {1,2,3,4}
    :param available_era: {1,2,3}
    :param available_min_power: {30}
    :param available_content_category: {1, 2, 3}
    :param is_idle: True/False
    :param has_load: True/False
    :return:
    """
    ret = []
    now = get_curr_server_datetime(version=version)

    queryset = PlayerTrain.objects.filter(
        version_id=version.id
    ).prefetch_related(
        'level', 'train', 'load'
    ).all()

    # if available_region:
    #     queryset = queryset.filter(train__region__in=available_region)
    if available_rarity:
        queryset = queryset.filter(train__rarity__in=available_rarity)
    if available_era:
        queryset = queryset.filter(train__era__in=available_era)
    if available_content_category:
        queryset = queryset.filter(train__content_category__in=available_content_category)

    for player_train in queryset.all():
        player_train: PlayerTrain

        if available_region and player_train.get_region() not in available_region:
            continue

        if available_min_power is not None and player_train.capacity() < available_min_power:
            continue

        if is_idle is not None and player_train.is_idle(now=now) != is_idle:
            continue

        if has_load is not None and player_train.has_load != has_load:
            continue

        ret.append(player_train)

    return ret


def trains_find_match_with_job(version: RunVersion, job: PlayerJob) -> List[PlayerTrain]:
    """
        job에 맞는 기차를 검색 합니다.
        작업중인 / 대기중인 기차를 검색합니다.

    :param version:
    :param job:
    :return:
    """
    requirements = job.requirements_to_dict

    return trains_find(version=version, **requirements)


def trains_unload(version: RunVersion, train: PlayerTrain):
    """
    기차에서 싣고 온 article을 unload합니다.

    :param version:
    :param train:
    :return:
    """
    version.add_log(
        msg='[Train Unload]',
        train_id=train.id,
        has_load=[train.has_load, False],
        load_amount=[train.load_amount, 0],
        load_id=[train.load_id, None],
    )
    train.has_load = False
    train.load_amount = 0
    train.load_id = None
    train.save(update_fields=[
        'has_load',
        'load_amount',
        'load_id',
    ])


def trains_set_destination(version: RunVersion, train: PlayerTrain, definition_id: Type[int], departure_at: datetime, arrival_at: datetime):
    """
        기차를 목적지에 셋팅 합니다.
     2 = {dict: 4} {'InstanceId': 3, 'DefinitionId': 4, 'Level': 1,
     'Route': {
     'RouteType': 'destination',
     'DefinitionId': 151,
     'DepartureTime': '2022-12-27T10:04:46Z',
     'ArrivalTime': '2022-12-27T10:05:16Z'}}

    :param version:
    :param train:
    :param definition_id:
    :param departure_at:
    :param arrival_at:
    """
    version.add_log(
        msg='[Train SendDestination]',
        train_id=train.id,
        has_load=[train.has_load, True],
        route_type=[train.route_type, 'destination'],
        route_definition_id=[train.route_definition_id, definition_id],
        route_departure_time=[train.route_departure_time, departure_at],
        route_arrival_time=[train.route_arrival_time, arrival_at],
    )
    train.route_type = 'destination'
    train.has_load = True
    train.route_definition_id = definition_id
    train.route_departure_time = departure_at
    train.route_arrival_time = arrival_at
    train.save(update_fields=[
        'has_load',
        'route_type',
        'route_definition_id',
        'route_departure_time',
        'route_arrival_time',
    ])


def trains_set_job(version: RunVersion, train: PlayerTrain, definition_id: Type[int], departure_at: datetime, arrival_at: datetime):
    """
        기차를 목적지에 셋팅 합니다.
     2 = {dict: 4} {'InstanceId': 3, 'DefinitionId': 4, 'Level': 1,
     'Route': {
     'RouteType': 'destination',
     'DefinitionId': 151,
     'DepartureTime': '2022-12-27T10:04:46Z',
     'ArrivalTime': '2022-12-27T10:05:16Z'}}

    :param version:
    :param train:
    :param definition_id:
    :param departure_at:
    :param arrival_at:
    """
    version.add_log(
        msg='[Train SendDestination]',
        train_id=train.id,
        has_load=[train.has_load, True],
        route_type=[train.route_type, 'destination'],
        route_definition_id=[train.route_definition_id, definition_id],
        route_departure_time=[train.route_departure_time, departure_at],
        route_arrival_time=[train.route_arrival_time, arrival_at],
    )
    train.route_type = 'destination'
    train.has_load = True
    train.route_definition_id = definition_id
    train.route_departure_time = departure_at
    train.route_arrival_time = arrival_at
    train.save(update_fields=[
        'has_load',
        'route_type',
        'route_definition_id',
        'route_departure_time',
        'route_arrival_time',
    ])

def trains_get_next_unload_event_time(version: RunVersion):
    ret = None

    for train in trains_find(version=version, is_idle=False):
        ret = update_next_event_time(previous=ret, event_time=train.route_arrival_time)

    return ret


def trains_max_capacity(version: RunVersion, **kwargs) -> List[PlayerTrain]:
    capacity = -1
    ret = []

    for train in trains_find(version=version, **kwargs):
        if train.capacity() > capacity:
            capacity = train.capacity()
            ret = [train]
        elif train.capacity() == capacity:
            ret.append(train)

    return ret

###########################################################################
# article을 구하기 위한 source 검색 (factory, destination, contractor, job)
###########################################################################
def article_find_all_article_and_factory(version: RunVersion) -> Dict[int, TSFactory]:
    """
    :param version:
    :return:
    """
    queryset = TSProduct.objects.filter(
        level_req__lte=version.level_id,
        level_from__lte=version.level_id,
        factory__level_req__lte=version.level_id,
        factory__level_from__lte=version.level_id,
    ).all()

    return {row.article_id: row.factory_id for row in queryset.all()}


def article_source_find_factory(version: RunVersion, article_id: int) -> List[TSProduct]:
    """
        article id에 해당하는 product 검색
    :param version:
    :param article_id:
    :return:
    """
    queryset = TSProduct.objects.filter(
        article_id=article_id,
        level_req__lte=version.level_id,
        level_from__lte=version.level_id,
    ).all()

    return list(queryset.all())


def article_find_all_article_and_destination(version: RunVersion) -> Dict[int, TSDestination]:
    visited_region_list = list(
        PlayerVisitedRegion.objects.filter(version_id=version.id).values_list('region_id', flat=True)
    )

    queryset = TSDestination.objects.filter(
        region_id__in=visited_region_list,
    ).all()

    return {row.article_id: row for row in queryset.all()}


def article_source_find_destination(version: RunVersion, article_id: int) -> List[TSDestination]:
    """
        article id에 해당하는 destination 검색
    :param version:
    :param article_id:
    :return:
    """
    ret = article_find_all_article_and_destination(version=version)

    return ret.get(article_id, [])


def article_find_all_article_and_contract(version: RunVersion) -> Dict[int, List[PlayerContract]]:

    now = get_curr_server_datetime(version=version)
    delta = timedelta(minutes=1)

    ret = {}
    for contract_list in PlayerContractList.objects.filter(version_id=version.id).all():

        # contract_list.contract_list_id == 1 => ship.

        # fixme: expired check
        if contract_list.next_replace_at and now < contract_list.next_replace_at < now + delta:
            continue
        if contract_list.available_to and now + delta >= contract_list.available_to:
            continue
        if contract_list.expires_at and now + delta >= contract_list.expires_at:
            continue

        for contract in PlayerContract.objects.filter(contract_list_id=contract_list.id).all():
            # fixme: expired check
            # fixme: article exist in reward?
            # yield contract

            """
              from                         to
                +----------+---------------+
                          now
            """

            if contract.usable_from and contract.usable_from > now:
                continue
            if contract.available_from and contract.available_from > now:
                continue
            if contract.available_to and now + delta >= contract.available_to:
                continue
            if contract.expires_at and now + delta >= contract.expires_at:
                continue

            rewards = contract.reward_to_article_dict
            found = False
            for reward_article_id, reward_amount in rewards.items():
                if reward_article_id not in ret:
                    ret.update({reward_article_id: []})

                ret[reward_article_id].append(contract)

    return ret


def article_source_find_contract(version: RunVersion, article_id: int) -> List[PlayerContract]:
    """
        article id에 해당하는 contractor 검색
    :param version:
    :param article_id:
    :return:
    """
    ret = article_find_all_article_and_contract(version=version)
    return ret.get(article_id, [])


def article_source_find_jobs(version: RunVersion, article_id: int) -> List[PlayerJob]:
    """
        article id에 해당하는 다른 job 검색
    :param version:
    :param article_id:
    :return:
    """
    ret = []

    for job in PlayerJob.objects.filter(version_id=version.id).all():
        rewards = job.reward_to_article_dict

        found = False
        for reward_article_id, reward_amount in rewards.items():
            if reward_article_id == article_id:
                found = True
                break

        if found:
            ret.append(job)

    return ret


###########################################################################
# Destination 검색 함수
###########################################################################
def destination_find(version: RunVersion, destination_id: int) -> TSDestination:
    return TSDestination.objects.filter(id=destination_id).first()


###########################################################################
# Gold Destination 검색 함수
###########################################################################
def destination_gold_find_iter(version: RunVersion) -> List[PlayerDestination]:
    queryset = PlayerDestination.objects.filter(version_id=version.id).order_by('pk')
    return list(queryset.all())


def destination_set_used(version: RunVersion, dest: PlayerDestination):
    if dest and dest.definition.refresh_time > 0:
        now = get_curr_server_datetime(version=version)
        dest.train_limit_refresh_at = now + timedelta(seconds=dest.definition.refresh_time)
        dest.train_limit_refresh_time = now + timedelta(seconds=dest.definition.refresh_time)
        dest.save(update_fields=[
            'train_limit_refresh_at',
            'train_limit_refresh_time',
        ])

###########################################################################
# Job 우선순위 정하는 함수.
###########################################################################
def jobs_find_sources(version: RunVersion, job: PlayerJob) -> List:
    article = job.required_article

    from_factory = list(article_source_find_factory(version=version, article_id=article.id))
    from_destination = list(article_source_find_destination(version=version, article_id=article.id))
    from_contract = list(article_source_find_contract(version=version, article_id=article.id))
    from_jobs = list(article_source_find_jobs(version=version, article_id=article.id))

    possibles = []
    possibles += from_factory
    possibles += from_destination
    possibles += from_contract
    possibles += from_jobs

    return possibles


class TRAIN:
    instance_id: int
    capacity: int

    def __init__(self, instance_id, capacity):
        self.instance_id = instance_id
        self.capacity = capacity


class JOB:
    article_id: int
    total_count: int
    curr_count: int

    def __init__(self, article_id, total_count, curr_count):
        self.article_id = article_id
        self.total_count = total_count
        self.curr_count = curr_count


class WAREHOUSE:
    article_id: int
    article_amount: int
    factory_count: int
    contract_count: int

    def __init__(self, article_id: int, amount: int):
        self.article_id = article_id
        self.article_amount = amount


class UnionJobFinder:
    number_of_dispatchers: int
    trains: Dict[int, TRAIN]
    jobs: Dict[int, JOB]
    warehouse: Dict[int, WAREHOUSE]

    train_job_relation: Dict[int, List[int]]

    def __init__(self, dispatcher):
        self.number_of_dispatchers = dispatcher
        self.trains = {}
        self.jobs = {}
        self.warehouse = {}
        self.train_job_relation = {}

    def add_job_train(self, job: PlayerJob, trains: List[PlayerTrain]):
        self.jobs.update({
            job.id: JOB(
                article_id=job.required_article_id,
                total_count=job.required_amount,
                curr_count=job.current_guild_amount,
            )
        })
        for train in trains:
            self.trains.update({
                train.id: TRAIN(
                    instance_id=train.instance_id,
                    capacity=train.capacity()
                )
            })

            if train.id not in self.train_job_relation:
                self.train_job_relation.update({train.id: []})

            self.train_job_relation[train.id].append(job.id)

    def add_warehouse(self, article_id, amount):
        self.warehouse.update({
            article_id: WAREHOUSE(article_id=article_id, amount=amount)
        })

    best_score: int = -1
    best_assign: Dict[int, int]

    train_id_list: List[int] = []
    assigned_job_amount: Dict[int, int] = {}
    assign: Dict[int, int] = {}

    def get_score(self, used_dispatcher: int) -> int:
        ret = 0

        count = {}
        INF_COUNT = 100000
        has_infinity = False

        for job_id, amount in self.assigned_job_amount.items():
            count.update({job_id: 0})

            total = self.jobs[job_id].total_count
            curr = min(total, self.jobs[job_id].curr_count)

            remain = total - curr
            if remain < 1:
                continue
            if self.assigned_job_amount[job_id] < 1:
                has_infinity = True
                continue

            count.update({job_id: math.ceil(remain / self.assigned_job_amount[job_id])})

        for job_id, amount in self.assigned_job_amount.items():
            total = self.jobs[job_id].total_count
            curr = min(total, self.jobs[job_id].curr_count + self.assigned_job_amount[job_id])

            ret += 1 - curr / total

        # 가능한 하나라도 완료에 가까운 곳으로.

        # 전체 수행 횟수를 줄이는 것.

        score = 0

        if has_infinity:
            score += 10000

        max_count = max(count.values())
        avg_progress = ret / len(self.assigned_job_amount)
        return ret

    def recur(self, idx: int, used_dispatcher: int, with_warehouse_limit: bool):

        score = self.get_score(used_dispatcher)

        if self.best_score < 0 or score < self.best_score:
            self.best_score = score
            self.best_assign = {k: v for k, v in self.assign.items()}

        if used_dispatcher >= self.number_of_dispatchers:
            return
        if idx >= len(self.train_id_list):
            return

        train_id = self.train_id_list[idx]

        train_capacity = self.trains[train_id].capacity
        possible_job_id_list = []

        for job_id in self.train_job_relation[train_id]:
            total = self.jobs[job_id].total_count
            curr = min(total, self.jobs[job_id].curr_count + self.assigned_job_amount[job_id])
            if curr < total:
                possible_job_id_list.append(job_id)

        for job_id in possible_job_id_list:
            total = self.jobs[job_id].total_count
            curr = min(total, self.jobs[job_id].curr_count + self.assigned_job_amount[job_id])

            amount = max(0, total - curr)
            amount = min(amount, train_capacity)

            if with_warehouse_limit:
                required_article_id = self.jobs[job_id].article_id
                has_amount = self.warehouse[required_article_id].article_amount if required_article_id in self.warehouse else 0
                available_amount = max(0, has_amount - self.assigned_job_amount[job_id])

                amount = min(available_amount, amount)

            if amount == 0:
                continue

            self.assigned_job_amount[job_id] += amount
            self.assign.update({train_id: job_id})

            self.recur(idx=idx+1, used_dispatcher=used_dispatcher+1, with_warehouse_limit=with_warehouse_limit)

            self.assigned_job_amount[job_id] -= amount
            self.assign.pop(train_id)

        if len(possible_job_id_list) != 1:
            self.recur(idx=idx+1, used_dispatcher=used_dispatcher, with_warehouse_limit=with_warehouse_limit)

    def dispatching(self, with_warehouse_limit: bool) -> Dict[int, int]:
        """

        :return:
            train_id, job_id
        """
        self.train_id_list = sorted(self.train_job_relation.keys(), key=lambda k: self.trains[k].capacity, reverse=True)
        self.best_score = -1
        self.assigned_job_amount = {job_id: 0 for job_id in self.jobs}
        self.best_assign = {}
        self.assign = {}

        self.recur(idx=0, used_dispatcher=0, with_warehouse_limit=with_warehouse_limit)

        print("------------------------------------------------------------------------------------------")
        print(f"Update Score : {self.best_score} / used  dispatcher : {len(self.best_assign)}")
        for train_id, job_id in self.best_assign.items():
            print(f"TrainID={train_id}, InstanceID={self.trains[train_id].instance_id} / JobID={job_id}")

        return self.best_assign


def jobs_find_priority(version: RunVersion, with_warehouse_limit: bool) -> Dict[int, int]:
    """

    :param version:
    :return:
    """

    # 재료 수집이 가능한가 ? & expired 체크 & event expired 체크 & union expired 체크
    # job의 travel time (1hour) 고려해서

    # job 우선순위를 정하고.

    # 재료 수집에 걸리는 시간
    #
    ret = {}
    if version.has_union:
        finder = UnionJobFinder(dispatcher=version.guild_dispatchers + 2)
        jobs = list(jobs_find(version, union_jobs=True, expired_jobs=False))
        if jobs:
            for job in jobs:
                materials = jobs_find_sources(version=version, job=job)
                trains = trains_find_match_with_job(version=version, job=job)
                print(f"[Job] : {job}")

                print("materials")
                for src in materials:
                    print(f"    {src}")

                print("trains")
                for train in trains:
                    print(f"    {train}")

                finder.add_job_train(job, trains)

                warehouse_cnt = warehouse_amount(version=version, article_id=job.required_article_id)

                finder.add_warehouse(
                    article_id=job.required_article_id,
                    amount=warehouse_cnt
                )

            return finder.dispatching(with_warehouse_limit)

    return ret


###########################################################################
# warehouse
###########################################################################
def warehouse_add_article(version: RunVersion, article_id: Type[int], amount: int) -> bool:
    """
        article 추가, 삭제
    :param version:
    :param article_id:
    :param amount:
    :return:
    """
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=article_id).first()
    if not instance:
        instance = PlayerWarehouse.objects.create(version_id=version.id, article_id=article_id, amount=0)

    version.add_log(
        msg='[Add Article]',
        article_id=article_id,
        before_amount=instance.amount,
        after_amount=instance.amount + amount,
    )

    instance.amount += amount
    if instance.amount >= 0:
        instance.save(update_fields=['amount'])
        return True


def warehouse_can_add(version: RunVersion, article_id: Type[int], amount: int) -> bool:
    article = TSArticle.objects.filter(id=article_id).first()
    if article:
        used = warehouse_used_capacity(version=version)
        max_capacity = warehouse_max_capacity(version=version)

        if article.type in (2, 3):
            if 0 <= used + amount <= max_capacity:
                return True
            else:
                return False
        else:
            return True

    return False


def warehouse_amount(version: RunVersion, article_id: Type[int]) -> int:
    article = PlayerWarehouse.objects.filter(version_id=version.id, article_id=article_id).first()
    if article:
        return article.amount
    return 0


def warehouse_can_add_with_rewards(version: RunVersion, reward: List[Dict], multiply: int = 1) -> bool:

    used = warehouse_used_capacity(version=version)
    max_capacity = warehouse_max_capacity(version=version)

    for item in reward:
        _id = item.get('Id', None)
        article_id = item.get('Value', None)
        amount = item.get('Amount', None)
        if _id != 8:
            continue

        pw = PlayerWarehouse.objects.filter(version_id=version.id, article_id=article_id).first()
        article = TSArticle.objects.filter(id=article_id).first()

        cnt = pw.amount if pw else 0

        if article.is_take_up_space:
            if 0 > (cnt + amount * multiply):
                return False
            if (used + amount * multiply) < 0 or (used + amount * multiply) > max_capacity:
                return False

            used += amount * multiply

    return True


def warehouse_max_capacity(version: RunVersion) -> int:
    instance = TSWarehouseLevel.objects.filter(id=version.warehouse_level).first()
    if instance:
        return instance.capacity


def warehouse_used_capacity(version: RunVersion):
    queryset = PlayerWarehouse.objects.filter(version_id=version.id)
    data_list = list(queryset.filter(article__type__in=[2, 3]).values_list('amount', flat=True))
    capacity = sum(data_list) if data_list else 0
    return capacity


def find_xp(version: RunVersion) -> int:
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_XP).first()
    return instance.amount


def find_key(version: RunVersion) -> int:
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_KEY).first()
    return instance.amount


def find_gem(version: RunVersion) -> int:
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_GEM).first()
    return instance.amount


def find_gold(version: RunVersion) -> int:
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_GOLD).first()
    return instance.amount


###########################################################################
# Daily Reward (일일 보상. 5일간 연속 로그인시 보상)
###########################################################################
def daily_reward_get_reward(version: RunVersion) -> PlayerDailyReward:
    """
        # 5일짜리 일일 보상 첫번째
        Before
                "AvailableFrom": "2023-01-23T00:00:00Z",
                "ExpireAt": "2023-01-23T23:59:59Z",
                "Rewards": [
                    {"Items": [{"Id": 8,"Value": 4,"Amount": 20}]},
                    {"Items": [{"Id": 8,"Value": 7,"Amount": 20}]},
                    {"Items": [{"Id": 8,"Value": 3,"Amount": 36}]},
                    {"Items": [{"Id": 8,"Value": 2,"Amount": 10}]},
                    {"Items": [{"Id": 1,"Value": 13}]}
                ],
                "PoolId": 1,
                "Day": 0
        After
                available_from : 2023-01-24 00:00:00+00:00 | remain : -1 day, 15:49:04.023994
                expire_at : 2023-01-24 23:59:59+00:00 | remain : 15:49:03.023963
                rewards : [
                    {"Items":[{"Id":8,"Value":4,"Amount":20}]},
                    {"Items":[{"Id":8,"Value":7,"Amount":20}]},
                    {"Items":[{"Id":8,"Value":3,"Amount":36}]},
                    {"Items":[{"Id":8,"Value":2,"Amount":10}]},
                    {"Items":[{"Id":1,"Value":13}]}
                ]
                pool_id : 1
                day : 1

    :param version:
    :return:
    """
    INTERVAL_SECOND = 12 * 60
    now = get_curr_server_datetime(version=version)
    queryset = PlayerDailyReward.objects.filter(version_id=version.id).all()

    if version.login_server and (now - version.login_server).total_seconds() > INTERVAL_SECOND:
        # 12분 후

        for reward in queryset:
            if reward.available_from and now < reward.available_from:
                continue
            if reward.expire_at and reward.expire_at <= now:
                continue
            return reward


def daily_reward_get_next_event_time(version: RunVersion) -> datetime:
    queryset = PlayerDailyReward.objects.filter(version_id=version.id).all()
    now = get_curr_server_datetime(version=version)

    for reward in queryset:
        return max(now, reward.available_from)

###########################################################################
# Daily Offer (일일 제공. 4시간? 5시간? 마다 제공)
###########################################################################
def daily_offer_get_slots(version: RunVersion, available_video: bool = None, availble_gem: bool = None, available_gold: bool = None):

    now = get_curr_server_datetime(version=version)
    queryset = PlayerDailyOffer.objects.filter(version_id=version.id).all()

    ret = []

    for daily in queryset:
        if daily.expire_at and daily.expire_at < now:
            continue
        if daily.expires_at and daily.expires_at < now:
            continue

        for item in PlayerDailyOfferItem.objects.filter(daily_offer_id=daily.id).prefetch_related('price').all():
            item: PlayerDailyOfferItem

            if item.purchased:
                continue

            if available_video is False and item.price.is_video_reward_article is True:
                continue

            if availble_gem is False and item.price.is_gem_article is True:
                continue

            if available_gold is False and item.price.is_gold_article is True:
                continue

            if available_video is True and item.price.is_video_reward_article is True:
                ret.append(item)
                continue

            if availble_gem is True and item.price.is_gem_article is True:
                ret.append(item)
                continue

            if available_gold is True and item.price.is_gold_article is True:
                ret.append(item)
                continue

    return ret


def daily_offer_get_next_event_time(version: RunVersion) -> datetime:
    now = get_curr_server_datetime(version=version)
    ret = now
    queryset = PlayerDailyOffer.objects.filter(version_id=version.id).all()
    delta = timedelta(seconds=10)

    for daily in queryset:
        if daily.expire_at:
            ret = max(ret, daily.expire_at + delta)
        if daily.expires_at:
            ret = max(ret, daily.expires_at + delta)

    if now < ret:
        return ret


def daily_offer_set_used(version: RunVersion, offer_item: PlayerDailyOfferItem):

    if offer_item:
        version.add_log(
            msg='[daily_offer]',
            slot=offer_item.slot,
            price_id=offer_item.price_id,
            price=str(offer_item.price),
            price_amount=offer_item.price_amount,
            purchased=[offer_item.purchased, True],
            purchase_count=[offer_item.purchase_count, offer_item.purchase_count+1],
        )

        offer_item.purchased = True
        offer_item.purchase_count += 1
        offer_item.save(update_fields=[
            'purchased',
            'purchase_count',
        ])

###########################################################################
# Whistle
###########################################################################

def whistle_get_collectable_list(version: RunVersion) -> List[PlayerWhistle]:
    now = get_curr_server_datetime(version=version)
    queryset = PlayerWhistle.objects.filter(version_id=version.id).all()
    delta = timedelta(seconds=settings.WHISTLE_INTERVAL_SECOND)
    ret = []

    max_spawn = None

    for whistle in queryset:
        # if whistle.spawn_time and now < whistle.spawn_time + delta:
        #     continue
        # if whistle.collectable_from and now < whistle.collectable_from + delta:
        #     continue
        if whistle.expires_at and whistle.expires_at <= now:
            continue
        if whistle.is_for_video_reward:
            continue

        if not max_spawn or max_spawn < whistle.spawn_time:
            max_spawn = whistle.spawn_time
        if not max_spawn or max_spawn < whistle.collectable_from:
            max_spawn = whistle.spawn_time
        ret.append(whistle)

    if max_spawn + delta <= now:
        return ret
    else:
        return []


def whistle_remove(version: RunVersion, whistle: PlayerWhistle) -> bool:
    if whistle:
        now = version.login_server

        version.add_log(
            msg='[whistle_remove]',
            whistle_id=whistle.id,
            before_expires_at=whistle.expires_at,
            after_expires_at=now,
        )

        whistle.expires_at = now
        whistle.save(update_fields=[
            'expires_at'
        ])
        return True

    return False


def whistle_get_next_event_time(version: RunVersion) -> datetime:
    now = get_curr_server_datetime(version=version)
    ret = None

    for whistle in PlayerWhistle.objects.filter(version_id=version.id).all():
        if not whistle.spawn_time:
            continue
        if not whistle.collectable_from:
            continue
        if whistle.expires_at and whistle.expires_at <= now:
            continue
        if whistle.is_for_video_reward:
            continue

        ret = update_next_event_time(previous=ret, event_time=whistle.spawn_time)
        ret = update_next_event_time(previous=ret, event_time=whistle.collectable_from)

    return ret

###########################################################################
# Container Offer
###########################################################################
def container_offer_find_iter(version: RunVersion, available_only: bool) -> List[PlayerDailyOfferContainer]:
    now = get_curr_server_datetime(version=version)
    queryset = PlayerDailyOfferContainer.objects.filter(version_id=version.id).order_by('id').all()
    ret = []
    for offer in queryset.all():
        container = offer.offer_container
        if container.min_player_level > version.level_id:
            continue
        if container.offer_presentation_id != 1:
            continue

        if container.price_article_id not in (16, 17):
            continue

        if available_only:
            if offer.last_bought_at and offer.last_bought_at + timedelta(seconds=container.cooldown_duration) >= now:
                continue

        ret.append(offer)

    return ret


def container_offer_set_used(version: RunVersion, offer: PlayerDailyOfferContainer):
    now = get_curr_server_datetime(version=version)
    offer.last_bought_at = now
    offer.count += 1
    offer.save(update_fields=[
        'last_bought_at',
        'count',
    ])


###########################################################################
# Container Offer
###########################################################################
def materials_find_from_ship(version: RunVersion) -> Dict[int, int]:
    ret = {}

    queryset = PlayerShipOffer.objects.filter(version_id=version.id).all()
    for ship in queryset:
        conditions_dict = ship.conditions_to_article_dict

        for k, v in conditions_dict.items():
            if k not in ret:
                ret.update({k: 0})
            ret[k] += v

    return ret


def materials_find_from_jobs(version: RunVersion, jobs: List[PlayerJob]) -> Dict[int, int]:
    pass


def materials_find_redundancy(version: RunVersion, min_cnt_factory, min_cnt_destination, min_cnt_contract):
    """

    :param version:
    :param min_cnt_factory:
    :param min_cnt_destination:
    :param min_cnt_contract:
    :return:
    """
    amount_warehouse = {row.article_id: row.amount for row in PlayerWarehouse.objects.all()}
    amount_factory = {}

    article_factory_dict = article_find_all_article_and_factory(version=version)
    article_destination_dict = article_find_all_article_and_destination(version=version)
    article_contract_dict = article_find_all_article_and_contract(version=version)
    all_article = {article.id: article for article in TSArticle.objects.all()}
    ret = {}
    if amount_warehouse:
        for article in TSArticle.objects.all():

            if article.level_req > version.level_id:
                continue
            if article.level_from > version.level_id:
                continue
            if article.type == 1:
                continue
            if article.is_event:
                continue

            if article.id in article_destination_dict:
                ret.setdefault(article.id, min_cnt_destination)
                continue

            if article.id in article_factory_dict:
                ret.setdefault(article.id, min_cnt_factory)
                continue

            if article.id in article_contract_dict:
                ret.setdefault(article.id, min_cnt_contract)

    for article_id, required in ret.items():
        has = amount_warehouse.get(article_id, 0)

        if has < required:
            print(f"article [{article_id}|{all_article[article_id].name}] need {required - has} more")

