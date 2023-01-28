import json
from datetime import datetime
from typing import Iterator, Tuple, List, Optional

from django.utils import timezone

from app_root.players.models import PlayerWhistle
from app_root.players.utils_import import InitdataHelper, LeaderboardHelper
from app_root.servers.models import RunVersion
from app_root.servers.utils_import import EndpointHelper, LoginHelper, SQLDefinitionHelper
from app_root.strategies.commands import HeartBeat, RunCommand, BaseCommand, TrainUnloadCommand, StartGame, \
    DailyRewardClaimWithVideoCommand, GameSleep, GameWakeup, DailyRewardClaimCommand, CollectWhistle
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find, warehouse_used_capacity, warehouse_add_article, \
    daily_reward_get_reward, warehouse_can_add, whistle_get_collectable_list
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
            instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
        elif instance.is_queued_task:
            # do next something...
            pass
        elif instance.is_processing_task:
            now = get_curr_server_datetime(version=instance)

            if instance.login_server and instance.login_server.hour != now.hour:
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
            else:
                # do next something...
                pass
        elif instance.is_error_task:
            # do nothing.
            instance = None
        elif instance.is_completed_task:
            now = get_curr_server_datetime(version=instance)
            if instance.next_event_datetime and instance.next_event_datetime > now:
                # do nothing.
                instance = None
            else:
                # do newly
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
        else:
            instance = None

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
        next_event_time: Optional[datetime] = None

        warehouse_capacity = warehouse_used_capacity(self.version)
        warehouse_used = warehouse_used_capacity(self.version)

        for train in trains_find(version=self.version, is_idle=True, has_load=True):
            article = train.load
            amount = train.load_amount

            if article.is_take_up_space and not (warehouse_used + amount <= warehouse_capacity):
                continue

            cmd = TrainUnloadCommand(version=self.version, train=train)
            self._send_commands(commands=[cmd])

            next_dt = cmd.get_next_event_time()

            if next_dt and (not next_event_time or next_event_time > next_dt):
                next_event_time = next_dt
        return next_event_time

    def _command_daily_reward(self) -> Optional[datetime]:
        next_event_time: Optional[datetime] = None

        daily_reward = daily_reward_get_reward(version=self.version)
        if daily_reward:
            if daily_reward.can_claim_with_video:
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
                next_dt = cmd.get_next_event_time()

                if next_dt and (not next_event_time or next_event_time > next_dt):
                    next_event_time = next_dt

            else:
                cmd = DailyRewardClaimCommand(version=self.version, reward=daily_reward)
                self._send_commands(commands=[cmd])
                next_dt = cmd.get_next_event_time()

                if next_dt and (not next_event_time or next_event_time > next_dt):
                    next_event_time = next_dt

        return next_event_time

    def _command_whistle(self) -> Optional[datetime]:
        next_event_time: Optional[datetime] = None

        for whistle in whistle_get_collectable_list(version=self.version):
            cmd = CollectWhistle(version=self.version, whistle=whistle)
            self._send_commands(commands=[cmd])

        now = get_curr_server_datetime(version=self.version)

        for whistle in PlayerWhistle.objects.filter(version_id=self.version.id).all():
            if not whistle.spawn_time:
                continue
            if not whistle.collectable_from:
                continue
            if whistle.expires_at and whistle.expires_at <= now:
                continue
            if whistle.is_for_video_reward:
                continue

            dt = max(whistle.spawn_time, whistle.collectable_from)

            if not next_event_time or next_event_time > dt:
                next_event_time = dt

        return next_event_time

    def collectable_commands(self):
        """

        """
        # todo: return next event time.
        next_event_time: Optional[datetime] = None

        # daily reward
        next_dt = self._command_daily_reward()
        if next_dt and (not next_event_time or next_event_time > next_dt):
            next_event_time = next_dt

        # train unload
        next_dt = self._command_train_unload()
        if next_dt and (not next_event_time or next_event_time > next_dt):
            next_event_time = next_dt

        next_dt = self._command_whistle()
        if next_dt and (not next_event_time or next_event_time > next_dt):
            next_event_time = next_dt

        # gift
        # ship
        return next_event_time

    def on_processing_status(self) -> datetime:
        """

        """
        next_event_time: Optional[datetime] = None

        self._send_commands(commands=[HeartBeat(version=self.version)])

        # 2. collect
        next_dt = self.collectable_commands()
        if next_dt and (not next_event_time or next_event_time > next_dt):
            next_event_time = next_dt
        # 3. assign job if
        # 4. prepare materials
        # 5. send train
        # 6. increase population
        # 7. collect gold
        return next_event_time

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

            if self.version.is_queued_task:
                self.on_queued_status()
                self.version.set_processing(save=True, update_fields=[])

            if self.version.is_processing_task:
                next_dt = self.on_processing_status()
                now = get_curr_server_datetime(version=self.version)

                if next_dt and (next_dt - now).total_seconds() > 30 * 60:
                    self.version.next_event_datetime = next_dt
                    self.version.set_completed(
                        save=True,
                        update_fields=['next_event_datetime']
                    )

        except Exception as e:
            if self.version:
                self.version.set_error(save=True, msg=str(e), update_fields=[])
            raise e
