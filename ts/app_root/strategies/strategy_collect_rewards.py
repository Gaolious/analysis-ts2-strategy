from typing import Optional

from app_root.servers.models import RunVersion
from datetime import datetime, timedelta

from app_root.strategies.commands import GameSleep, send_commands, GameWakeup, DailyRewardClaimWithVideoCommand, \
    DailyRewardClaimCommand, ShopPurchaseItem, TrainUnloadCommand, ShopBuyContainer
from app_root.strategies.managers import daily_reward_get_reward, warehouse_can_add_with_rewards, \
    daily_reward_get_next_event_time, daily_offer_get_slots, daily_offer_get_next_event_time, trains_find, \
    warehouse_can_add, trains_get_next_unload_event_time, container_offer_find_iter, update_next_event_time
from app_root.utils import get_curr_server_str_datetime_s


def collect_daily_reward(version: RunVersion) -> datetime:
    """
    Daily Reward (일일 보상. 5일간 연속 로그인시 보상)

    :param version:
    :return:
    """
    daily_reward = daily_reward_get_reward(version=version)
    if daily_reward:
        if daily_reward.can_claim_with_video:
            ret = warehouse_can_add_with_rewards(
                version=version,
                reward=daily_reward.get_today_rewards(),
                multiply=2
            )

            if ret:
                video_started_datetime_s = get_curr_server_str_datetime_s(version=version)
                cmd = GameSleep(version=version, sleep_seconds=30)
                send_commands(commands=cmd)

                cmd = GameWakeup(version=version)
                send_commands(commands=cmd)

                cmd = DailyRewardClaimWithVideoCommand(
                    version=version,
                    reward=daily_reward,
                    video_started_datetime_s=video_started_datetime_s
                )
                send_commands(commands=cmd)

        else:
            cmd = DailyRewardClaimCommand(version=version, reward=daily_reward)
            send_commands(commands=cmd)

    return daily_reward_get_next_event_time(version=version)


def collect_daily_offer(version: RunVersion) -> datetime:
    """
    Daily Offer (일일 reward)

    video 보기 전용 only

    :param version:
    :return:
    """
    daily_offer_items = daily_offer_get_slots(
        version=version,
        available_video=True,
        availble_gem=False,
        available_gold=False,
    )

    for offer_item in daily_offer_items:
        cmd = ShopPurchaseItem(version=version, offer_item=offer_item)
        send_commands(commands=cmd)

    return daily_offer_get_next_event_time(version=version)


def collect_train_unload(version: RunVersion) -> datetime:
    for train in trains_find(version=version, has_load=True):
        if not warehouse_can_add(version=version, article_id=train.load_id, amount=train.load_amount):
            continue

        cmd = TrainUnloadCommand(version=version, train=train)
        send_commands(commands=cmd)

    return trains_get_next_unload_event_time(version=version)


def collect_whistle(version: RunVersion) -> datetime:

    # for whistle in whistle_get_collectable_list(version=self.version):
    #     cmd = CollectWhistle(version=self.version, whistle=whistle)
    #     self._send_commands(commands=[cmd])
    #
    # return whistle_get_next_event_time(version=self.version)

    pass


def collect_offer_container(version: RunVersion) -> datetime:
    ret = None

    for offer in container_offer_find_iter(version=version, available_only=True):

        cmd_no = None
        cmd_list = []

        if offer.is_video_reward:
            cmd_no = version.command_no
            cmd = GameSleep(version=version, sleep_seconds=30)
            send_commands(commands=cmd)

            cmd = GameWakeup(version=version)
            cmd_list.append(cmd)

        cmd = ShopBuyContainer(
            version=version,
            offer=offer,
            sleep_command_no=cmd_no,
        )
        cmd_list.append(cmd)
        send_commands(commands=cmd_list)

    for offer in container_offer_find_iter(version=version, available_only=False):
        container = offer.offer_container
        next_dt = offer.last_bought_at + timedelta(seconds=container.cooldown_duration)
        if version.now < next_dt:
            ret = update_next_event_time(previous=ret, event_time=next_dt)

    return ret


def strategy_collect_reward_commands(version: RunVersion) -> datetime:
    """

    :param version:
    :return:
    """
    # todo: return next event time.
    ret: Optional[datetime] = None

    # daily reward
    next_dt = collect_daily_reward(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # daily offer
    next_dt = collect_daily_offer(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # train unload
    next_dt = collect_train_unload(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    next_dt = collect_whistle(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # gift

    # ship

    # offer container
    next_dt = collect_offer_container(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    return ret