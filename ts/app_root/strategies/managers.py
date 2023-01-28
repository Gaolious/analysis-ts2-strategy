from datetime import timedelta
from typing import Iterator, List, Set, Dict, Type

from app_root.players.models import PlayerJob, PlayerTrain, PlayerVisitedRegion, PlayerContract, PlayerContractList, \
    PlayerWarehouse, PlayerDailyReward, PlayerWhistle
from app_root.servers.models import RunVersion, TSProduct, TSDestination, TSWarehouseLevel, TSArticle
from app_root.utils import get_curr_server_datetime


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
) -> Iterator[PlayerJob]:
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

        yield job


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
) -> Iterator[PlayerTrain]:
    """
        가용 가능한 기차를 검색 합니다.

    :param version:
    :param available_region:
    :param available_rarity:
    :param available_era:
    :param available_min_power:
    :param available_content_category:
    :param is_idle
    :param has_load:
    :return:
    """

    now = get_curr_server_datetime(version=version)

    queryset = PlayerTrain.objects.filter(
        version_id=version.id
    ).prefetch_related(
        'level', 'train', 'load'
    ).all()

    # if available_region:
    #     queryset = queryset.filter(train__region__in=available_region)
    if available_rarity is not None:
        queryset = queryset.filter(train__rarity__in=available_rarity)
    if available_era is not None:
        queryset = queryset.filter(train__era__in=available_era)
    if available_content_category is not None:
        queryset = queryset.filter(train__content_category__in=available_content_category)

    for player_train in queryset.all():
        player_train: PlayerTrain

        if available_region is not None and player_train.get_region() not in available_region:
            continue

        # if available_rarity and player_train.train.rarity not in available_rarity:
        #     continue
        #
        # if available_era and player_train.train.era not in available_era:
        #     continue

        if available_min_power is not None and player_train.capacity() < available_min_power:
            continue

        # if available_content_category and player_train.train.content_category not in available_content_category:
        #     continue

        if is_idle is not None and player_train.is_idle(now=now) != is_idle:
            continue

        if has_load is not None and player_train.has_load != has_load:
            continue

        yield player_train


def trains_find_match_with_job(version: RunVersion, job: PlayerJob) -> Iterator[PlayerTrain]:
    """
        job에 맞는 기차를 검색 합니다.

    :param version:
    :param job:
    :return:
    """
    requirements = job.requirements_to_dict

    iter_train = trains_find(
        version=version,
        **requirements,
        is_idle=True
    )
    for train in iter_train:
        yield train


def trains_unload(version: RunVersion, train: PlayerTrain):
    """
    기차에서 싣고 온 article을 unload합니다.

    :param version:
    :param train:
    :return:
    """
    pass


###########################################################################
# article을 구하기 위한 source 검색 (factory, destination, contractor, job)
###########################################################################
def find_article_source_factory(version: RunVersion, article_id: int) -> Iterator[TSProduct]:
    """
        article id에 해당하는 product 검색
    :param version:
    :param article_id:
    :return:
    """
    queryset = TSProduct.objects.filter(
        article_id=article_id,
        level_req__lte=version.level,
        level_from__lte=version.level,
    ).all()

    for src in queryset:
        yield src


def find_article_source_destination(version: RunVersion, article_id: int) -> Iterator[TSDestination]:
    """
        article id에 해당하는 destination 검색
    :param version:
    :param article_id:
    :return:
    """
    visited_region_list = list(
        PlayerVisitedRegion.objects.filter(version_id=version.id).values_list('region_id', flat=True)
    )

    queryset = TSDestination.objects.filter(
        region_id__in=visited_region_list,
        article_id=article_id
    ).all()

    for src in queryset:
        yield src


def find_article_source_contractor(version: RunVersion, article_id: int) -> Iterator[PlayerContract]:
    """
        article id에 해당하는 contractor 검색
    :param version:
    :param article_id:
    :return:
    """
    now = get_curr_server_datetime(version=version)
    delta = timedelta(minutes=1)

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
                if reward_article_id == article_id:
                    found = True
                    break

            if found:
                yield contract


def find_article_source_jobs(version: RunVersion, article_id: int) -> Iterator[PlayerJob]:
    """
        article id에 해당하는 다른 job 검색
    :param version:
    :param article_id:
    :return:
    """
    for job in PlayerJob.objects.filter(version_id=version.id).all():
        rewards = job.reward_to_article_dict

        found = False
        for reward_article_id, reward_amount in rewards.items():
            if reward_article_id == article_id:
                found = True
                break

        if found:
            yield job


###########################################################################
# Destination 검색 함수
###########################################################################
def find_destination(version: RunVersion, destination_id: int) -> TSDestination:
    instance = TSDestination.objects.filter(id=destination_id).first()
    return instance


###########################################################################
# Job 우선순위 정하는 함수.
###########################################################################
def find_job_sources(version: RunVersion, jobs: List[PlayerJob]) -> Dict[int, List]:
    now = get_curr_server_datetime(version=version)

    material_sources = {}

    for job in jobs:
        amouunt = job.required_amount
        article = job.required_article

        from_factory = list(find_article_source_factory(version=version, article_id=article.id))
        from_destination = list(find_article_source_destination(version=version, article_id=article.id))
        from_contract = list(find_article_source_contractor(version=version, article_id=article.id))
        from_jobs = list(find_article_source_jobs(version=version, article_id=article.id))

        possibles = []
        possibles += from_factory
        possibles += from_destination
        possibles += from_contract
        possibles += from_jobs
        material_sources.update({
            job.id: possibles
        })

    return material_sources


def find_job_priority(version: RunVersion) -> List[PlayerJob]:

    # 재료 수집이 가능한가 ? & expired 체크 & event expired 체크 & union expired 체크
    # job의 travel time (1hour) 고려해서

    # job 우선순위를 정하고.

    # 재료 수집에 걸리는 시간
    #
    if version.has_union:
        jobs = list(jobs_find(version, union_jobs=True, expired_jobs=False))
        if jobs:
            return jobs


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
# Daily Reward
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


###########################################################################
# Whistle
###########################################################################
def whistle_get_collectable_list(version: RunVersion) -> Iterator[PlayerWhistle]:
    INTERVAL_SECOND = 2 * 60
    now = get_curr_server_datetime(version=version)
    queryset = PlayerWhistle.objects.filter(version_id=version.id).all()

    if version.login_server and (now - version.login_server).total_seconds() > INTERVAL_SECOND:
        for whistle in queryset:
            if whistle.spawn_time and now < whistle.spawn_time:
                continue
            if whistle.collectable_from and now < whistle.collectable_from:
                continue
            if whistle.expires_at and whistle.expires_at <= now:
                continue
            if whistle.is_for_video_reward:
                continue

            yield whistle


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
