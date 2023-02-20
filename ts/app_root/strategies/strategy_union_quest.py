from datetime import datetime, timedelta
from typing import List

from app_root.players.models import PlayerDestination
from app_root.servers.models import RunVersion
from app_root.strategies.commands import TrainDispatchToJobCommand, send_commands, TrainSendToGoldDestinationCommand
from app_root.strategies.data_types import JobPriority
from app_root.strategies.managers import get_number_of_working_dispatchers, warehouse_get_amount, \
    destination_gold_find_iter, trains_max_capacity, update_next_event_time, article_find_destination


def strategy_dispatching_gold_destinations(version: RunVersion) -> datetime:
    """
    골드 벌어오기

    :param version:
    :return:
    """
    print(f"# [Strategy Process] - Send Gold Destination")

    normal_workers, union_workers = get_number_of_working_dispatchers(version=version)
    max_normal_workers = version.dispatchers + 2
    max_union_workers = version.guild_dispatchers + 2

    ret = None
    for destination in destination_gold_find_iter(version=version):
        if normal_workers >= max_normal_workers:
            print(f"    - Dest Location ID #{destination.location_id} / Dispatcher Working:{normal_workers} >= {version.dispatchers + 2} | PASS")
            break

        if destination.is_available(now=version.now):
            requirerments = destination.definition.requirements_to_dict
            possibles = []
            for train in trains_max_capacity(version=version, **requirerments):
                if train.is_idle(now=version.now):
                    possibles.append(train)
            if possibles:
                cmd = TrainSendToGoldDestinationCommand(
                    version=version,
                    article_id=3,
                    amount=possibles[0].capacity() * destination.definition.multiplier,
                    train=possibles[0],
                    dest=destination,
                )
                send_commands(commands=cmd)
                normal_workers += 1

        elif destination.train_limit_refresh_at and destination.train_limit_refresh_at > version.now:
            ret = update_next_event_time(previous=ret, event_time=destination.train_limit_refresh_at)

    # for article_id, destination_list in article_find_destination(version=version, article_id=3).items():
    #     for destination in destination_list:
    #         pd = PlayerDestination.objects.filter(version=version, definition_id=destination.id).first()
    #         possibles = []
    #         for train in trains_max_capacity(version=version, **destination.requirements_to_dict):
    #             if train.is_idle(now=version.now):
    #                 possibles.append(train)
    #
    #         if not pd:
    #             pd = PlayerDestination.objects.create(
    #                 version=version,
    #                 location=destination.location,
    #                 definition=destination,
    #                 train_limit_count=1,
    #                 train_limit_refresh_at=version.now + timedelta(days=-1),
    #                 train_limit_refresh_time= version.now + timedelta(days=-1),
    #                 multiplier=1,
    #             )
    #
    #         if pd and pd.is_available(now=version.now) and possibles:
    #             cmd = TrainSendToGoldDestinationCommand(
    #                 version=version,
    #                 article_id=3,
    #                 amount=possibles[0].capacity() * destination.multiplier,
    #                 train=possibles[0],
    #                 dest=pd,
    #             )
    #             send_commands(commands=cmd)
    return ret


def dispatching_job(version: RunVersion, job_priority: List[JobPriority]):
    """
    Job 보내기

    :param version:
    :param job_priority:
    :return:
    """
    normal_workers, union_workers = get_number_of_working_dispatchers(version=version)
    max_normal_workers = version.dispatchers + 2
    max_union_workers = version.guild_dispatchers + 2

    for instance in job_priority:
        if instance.job.is_union_job:
            if union_workers >= max_union_workers:
                continue
        else:
            if normal_workers >= max_normal_workers:
                continue

        instance.train.refresh_from_db()

        if instance.train.is_working(now=version.now):
            continue
        if instance.train.has_load:
            continue

        warehouse_amount = warehouse_get_amount(version=version, article_id=instance.job.required_article_id)
        amount = min(min(instance.amount, warehouse_amount), instance.train.capacity())

        if amount > 0:
            cmd = TrainDispatchToJobCommand(
                version=version,
                train=instance.train,
                job=instance.job,
                amount=amount,
            )
            send_commands(commands=cmd)

            if instance.job.is_union_job:
                union_workers += 1
            else:
                normal_workers += 1


