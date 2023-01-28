import json
from datetime import datetime
from typing import Iterator, Tuple, List

from django.utils import timezone

from app_root.players.utils_import import InitdataHelper, LeaderboardHelper
from app_root.servers.models import RunVersion
from app_root.servers.utils_import import EndpointHelper, LoginHelper, SQLDefinitionHelper
from app_root.strategies.commands import HeartBeat, RunCommand, BaseCommand, TrainUnloadCommand, StartGame, \
    DailyRewardClaimWithVideoCommand, GameSleep, GameWakeup, DailyRewardClaimCommand
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find, warehouse_used_capacity, warehouse_add_article, \
    daily_reward_get_reward, warehouse_can_add
from app_root.utils import get_curr_server_str_datetime_s


class Strategy(object):
    version: RunVersion
    user_id: int

    def __init__(self, user_id):
        self.user_id = user_id
        self.version = None

    def create_version(self):
        instance = RunVersion.objects.filter(user_id=self.user_id).order_by('-pk').first()

        now = timezone.now()

        if not instance:
            instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
        elif instance.is_queued_task:
            # do next something...
            pass
        elif instance.is_processing_task:
            if instance.next_event_datetime and instance.next_event_datetime > now:
                # do nothing.
                instance = None
            else:
                # do next something...
                pass
        elif instance.is_error_task:
            # do nothing.
            instance = None
        elif instance.is_completed_task:
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

    def _command_train_unload(self):

        warehouse_capacity = warehouse_used_capacity(self.version)
        warehouse_used = warehouse_used_capacity(self.version)

        for train in trains_find(version=self.version, is_idle=True, has_load=True):
            article = train.load
            amount = train.load_amount

            if article.is_take_up_space and not (warehouse_used + amount <= warehouse_capacity):
                continue

            cmd = TrainUnloadCommand(version=self.version, train=train)
            self._send_commands(commands=[cmd])

    def _command_daily_reward(self):
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
            else:
                cmd = DailyRewardClaimCommand(version=self.version)
                self._send_commands(commands=[cmd])

    def collectable_commands(self):
        """

        """
        # todo: return next event time.
        
        # daily reward
        self._command_daily_reward()
        # train unload
        self._command_train_unload()
        # gift
        # ship
        pass

    def on_processing_status(self):
        """

        """
        self._send_commands(commands=[HeartBeat(version=self.version)])

        # 2. collect
        self.collectable_commands()

        # 3. assign job if
        # 4. prepare materials
        # 5. send train
        # 6. increase population
        # 7. collect gold

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
                self.on_processing_status()

        except Exception as e:
            if self.version:
                self.version.set_error(save=True, msg=str(e), update_fields=[])
            raise e
