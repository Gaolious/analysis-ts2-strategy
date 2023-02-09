import json
from datetime import datetime, timedelta
from typing import Iterator, Tuple, List, Optional

from django.conf import settings
from django.utils import timezone

from app_root.players.models import PlayerWhistle
from app_root.players.utils_import import InitdataHelper, LeaderboardHelper
from app_root.servers.models import RunVersion
from app_root.servers.utils_import import EndpointHelper, LoginHelper, SQLDefinitionHelper
from app_root.strategies.commands import HeartBeat, RunCommand, BaseCommand, TrainUnloadCommand, StartGame, \
    DailyRewardClaimWithVideoCommand, GameSleep, GameWakeup, DailyRewardClaimCommand, CollectWhistle, \
    TrainSendToDestinationCommand, ShopBuyContainer, ShopPurchaseItem
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find, warehouse_used_capacity, warehouse_add_article, \
    daily_reward_get_reward, warehouse_can_add, whistle_get_collectable_list, warehouse_can_add_with_rewards, \
    daily_reward_get_next_event_time, trains_get_next_unload_event_time, whistle_get_next_event_time, \
    update_next_event_time, trains_max_capacity, destination_gold_find_iter, container_offer_find_iter, \
    warehouse_max_capacity, daily_offer_get_next_event_time, daily_offer_get_slots, \
    materials_find_from_ship, materials_find_from_jobs, article_find_all_article_and_factory, \
    article_find_all_article_and_destination, article_find_all_article_and_contract, materials_find_redundancy, \
    jobs_find_priority
from app_root.utils import get_curr_server_str_datetime_s, get_curr_server_datetime


class Strategy(object):
    version: RunVersion
    user_id: int

    def __init__(self, user_id):
        self.user_id = user_id
        self.version = None

    def create_version(self):
        instance = RunVersion.objects.filter(user_id=self.user_id).order_by('-pk').first()

        if not instance:
            print(f"""[CreateVersion] Not Exist - start with new instance""")
            instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
            return instance

        elif instance.is_queued_task:
            print(f"""[CreateVersion] Status=Queued. start with previous instance""")
            # do next something...
            return instance

        elif instance.is_error_task:
            version_list = RunVersion.objects.filter(user_id=self.user_id).order_by('-pk').all()[:5]
            for v in version_list:
                if not v.is_error_task:
                    instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                    return instance

            print(f"""[CreateVersion] Status=Error. Stop""")
            # do nothing.
            return None

        elif instance.is_processing_task:
            now = get_curr_server_datetime(version=instance)

            now_format = now.astimezone(settings.KST).strftime('%Y-%m-%d %H')
            srv_format = instance.login_server.astimezone(settings.KST).strftime('%Y-%m-%d %H')

            if now_format != srv_format:
                print(f"""[CreateVersion] Status=processing. passed over 1hour. start with new instance""")
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                return instance

            if instance.next_event_datetime and instance.next_event_datetime > now:
                print(f"""[CreateVersion] Status=processing. waiting for next event. Next event time is[{instance.next_event_datetime.astimezone(settings.KST)}] / Now is {now.astimezone(settings.KST)}""")
                return None

            print(f"""[CreateVersion] Status=processing. start with previous instance""")
            return instance

        elif instance.is_completed_task:
            now = get_curr_server_datetime(version=instance)
            if instance.next_event_datetime and instance.next_event_datetime > now:
                print(f"""[CreateVersion] Status=Completed. waiting for next event. Next event time is[{instance.next_event_datetime.astimezone(settings.KST)}] / Now is {now.astimezone(settings.KST)}""")
                # do nothing.
                return None
            else:
                # do newly
                print(f"""[CreateVersion] Status=Completed. start with new instance""")
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                return instance
        else:
            return None

        return instance

    def on_queued_status(self):
        ep_helper = EndpointHelper(version=self.version)
        ep_helper.run()

        login_helper = LoginHelper(version=self.version)
        login_helper.run()

        sd_helper = SQLDefinitionHelper(version=self.version)
        sd_helper.run()

        init_helper = InitdataHelper(version=self.version)
        init_helper.run()

        for job in jobs_find(version=self.version, union_jobs=True):
            lb_helper = LeaderboardHelper(version=self.version, player_job_id=job.id)
            lb_helper.run()

        sg = StartGame(version=self.version)
        sg.run()

        ts_dump(version=self.version)

    def _command_train_unload(self) -> Optional[datetime]:
        for train in trains_find(version=self.version, is_idle=True, has_load=True):
            if not warehouse_can_add(version=self.version, article_id=train.load_id, amount=train.load_amount):
                continue

            cmd = TrainUnloadCommand(version=self.version, train=train)
            self._send_commands(commands=[cmd])

        return trains_get_next_unload_event_time(version=self.version)

    def _command_daily_reward(self) -> Optional[datetime]:

        daily_reward = daily_reward_get_reward(version=self.version)
        if daily_reward:
            if daily_reward.can_claim_with_video:
                ret = warehouse_can_add_with_rewards(
                    version=self.version,
                    reward=daily_reward.get_today_rewards(),
                    multiply=2
                )

                if ret:
                    video_started_datetime_s = get_curr_server_str_datetime_s(version=self.version)
                    cmd = GameSleep(version=self.version, sleep_seconds=30)
                    self._send_commands(commands=[cmd])

                    cmd = GameWakeup(version=self.version)
                    self._send_commands(commands=[cmd])

                    cmd = DailyRewardClaimWithVideoCommand(
                        version=self.version,
                        reward=daily_reward,
                        video_started_datetime_s=video_started_datetime_s
                    )
                    self._send_commands(commands=[cmd])

            else:
                cmd = DailyRewardClaimCommand(version=self.version, reward=daily_reward)
                self._send_commands(commands=[cmd])

        return daily_reward_get_next_event_time(version=self.version)

    def _command_daily_offer(self) -> Optional[datetime]:
        daily_offer_items = daily_offer_get_slots(
            version=self.version,
            available_video=True,
            availble_gem=False,
            available_gold=False,
        )

        for offer_item in daily_offer_items:
            cmd = ShopPurchaseItem(version=self.version, offer_item=offer_item)
            self._send_commands(commands=[cmd])

        return daily_offer_get_next_event_time(version=self.version)

    def _command_whistle(self) -> Optional[datetime]:
        for whistle in whistle_get_collectable_list(version=self.version):
            cmd = CollectWhistle(version=self.version, whistle=whistle)
            self._send_commands(commands=[cmd])

        return whistle_get_next_event_time(version=self.version)

    def _command_offer_container(self) -> Optional[datetime]:
        ret = None

        for offer in container_offer_find_iter(version=self.version, available_only=True):

            cmd_no = None
            cmd_list = []

            if offer.is_video_reward:
                cmd_no = self.version.command_no
                cmd = GameSleep(version=self.version, sleep_seconds=30)
                self._send_commands(commands=[cmd])

                cmd = GameWakeup(version=self.version)
                cmd_list.append(cmd)

            cmd = ShopBuyContainer(
                version=self.version,
                offer=offer,
                sleep_command_no=cmd_no,
            )
            cmd_list.append(cmd)
            self._send_commands(commands=cmd_list)

        for offer in container_offer_find_iter(version=self.version, available_only=False):
            container = offer.offer_container
            next_dt = offer.last_bought_at + timedelta(seconds=container.cooldown_duration)
            ret = update_next_event_time(previous=ret, event_time=next_dt)

        return ret

    def collectable_commands(self) -> Optional[datetime]:
        """

        """
        # todo: return next event time.
        ret: Optional[datetime] = None

        # daily reward
        next_dt = self._command_daily_reward()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # daily offer
        next_dt = self._command_daily_offer()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # train unload
        next_dt = self._command_train_unload()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_whistle()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # gift

        # ship

        # offer container
        next_dt = self._command_offer_container()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        return ret

    def _command_send_gold_destination(self) -> Optional[datetime]:
        now = get_curr_server_datetime(version=self.version)
        ret = None
        for destination in destination_gold_find_iter(version=self.version):
            if destination.is_available(now=now):
                requirerments = destination.definition.requirements_to_dict
                possibles = []
                for train in trains_max_capacity(version=self.version, **requirerments):
                    if train.is_idle(now=now):
                        possibles.append(train)
                if possibles:
                    cmd = TrainSendToDestinationCommand(
                        version=self.version,
                        train=possibles[0],
                        dest=destination,
                    )
                    self._send_commands(commands=[cmd])
            elif destination.train_limit_refresh_at and destination.train_limit_refresh_at > now:
                ret = update_next_event_time(previous=ret, event_time=destination.train_limit_refresh_at)

        return ret

    def _command_prepare_materials(self) -> Optional[datetime]:
        ret = None

        # warehouse_capacity = warehouse_max_capacity(version=self.version)
        # article_source_factory = article_find_all_article_and_factory(version=self.version)
        # article_source_destination = article_find_all_article_and_destination(version=self.version)
        # article_source_contract = article_find_all_article_and_contract(version=self.version)
        #
        # # ship
        # ship_materials = materials_find_from_ship(version=self.version)
        #
        # # union quest item
        # train_job_ids = jobs_find_priority(version=self.version, with_warehouse_limit=False)
        #
        # # prepare
        # # redundancy_materials = materials_find_redundancy(version=self.version)

        return ret

    def dispatchers_commands(self) -> Optional[datetime]:
        ret: Optional[datetime] = None

        next_dt = self._command_send_gold_destination()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_prepare_materials()
        ret = update_next_event_time(previous=ret, event_time=next_dt)
        return ret

    def on_finally(self) -> Optional[datetime]:
        ret = None
        now = get_curr_server_datetime(version=self.version)

        for train in trains_find(version=self.version, is_idle=False):
            if train.route_arrival_time and train.route_arrival_time > now:
                ret = update_next_event_time(previous=ret, event_time=train.route_arrival_time)

        return ret

    def on_processing_status(self) -> Optional[datetime]:
        """

        """
        ret: Optional[datetime] = None
        self._send_commands(commands=[HeartBeat(version=self.version)])

        # 2. collect
        next_dt = self.collectable_commands()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self.dispatchers_commands()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # 3. assign job if
        # 4. prepare materials
        # 5. send train
        # 6. increase population
        # 7. collect gold
        return ret

    def _send_commands(self, commands: List[BaseCommand]):
        if not isinstance(commands, list):
            commands = [commands]
        cmd = RunCommand(version=self.version, commands=commands)
        cmd.run()

    def run(self):

        self.version = self.create_version()

        if not self.version:
            return

        try:
            ret = None

            if self.version.is_queued_task:
                self.on_queued_status()
                self.version.set_processing(save=True, update_fields=[])

            if self.version.is_processing_task:
                next_dt = self.on_processing_status()
                ret = update_next_event_time(previous=ret, event_time=next_dt)

            next_dt = self.on_finally()
            ret = update_next_event_time(previous=ret, event_time=next_dt)

            self.version.next_event_datetime = ret
            self.version.save(
                update_fields=['next_event_datetime']
            )

        except Exception as e:
            if self.version:
                self.version.set_error(save=True, msg=str(e), update_fields=[])
            raise e
