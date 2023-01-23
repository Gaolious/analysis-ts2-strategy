from datetime import timedelta
from typing import Iterator, List, Set, Dict

from app_root.players.models import PlayerJob, PlayerTrain, PlayerVisitedRegion, PlayerContract, PlayerContractList, \
    PlayerWarehouse
from app_root.servers.models import RunVersion, TSProduct, TSDestination
from app_root.utils import get_curr_server_datetime


###########################################################################
# Job 검색
###########################################################################
def find_jobs(
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
def find_trains(
        version: RunVersion,
        available_region: Set[int] = None,
        available_rarity: Set[int] = None,
        available_era: Set[int] = None,
        available_min_power: int = None,
        available_content_category: Set[int] = None,
        available_only: bool = None,
) -> Iterator[PlayerTrain]:
    """
        가용 가능한 기차를 검색 합니다.

    :param version:
    :param available_region:
    :param available_rarity:
    :param available_era:
    :param available_min_power:
    :param available_content_category:
    :param available_only
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

        if available_only is not None and player_train.is_idle(now=now) != available_only:
            continue

        yield player_train


def find_trains_by_job(version: RunVersion, job: PlayerJob) -> Iterator[PlayerTrain]:
    """
        job에 맞는 기차를 검색 합니다.

    :param version:
    :param job:
    :return:
    """
    requirements = job.requirements_to_dict

    iter_train = find_trains(
        version=version,
        **requirements,
        available_only=True
    )
    for train in iter_train:
        yield train


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
def find_job_materials(version: RunVersion, jobs: List[PlayerJob]) -> Dict[int, List[PlayerTrain]]:
    now = get_curr_server_datetime(version=version)

    # 재료 수집이 가능한가 ? & expired 체크 & event expired 체크 & union expired 체크
    # job의 travel time (1hour) 고려해서

    # job 우선순위를 정하고.

    # 재료 수집에 걸리는 시간
    #
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
    if version.has_union:
        jobs = list(find_jobs(version, union_jobs=True, expired_jobs=False))
        if jobs:
            return jobs


def find_xp(version: RunVersion) -> int :
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_XP).first()
    return instance.amount


def find_key(version: RunVersion) -> int :
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_KEY).first()
    return instance.amount


def find_gem(version: RunVersion) -> int :
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_GEM).first()
    return instance.amount


def find_gold(version: RunVersion) -> int :
    instance = PlayerWarehouse.objects.filter(version_id=version.id, article_id=PlayerWarehouse.ARTICLE_GOLD).first()
    return instance.amount

