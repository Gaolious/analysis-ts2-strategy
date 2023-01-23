from django.utils import timezone

from app_root.players.utils_import import InitdataHelper, LeaderboardHelper
from app_root.servers.models import RunVersion
from app_root.servers.utils_import import EndpointHelper, LoginHelper, SQLDefinitionHelper
from app_root.strategies.managers import find_jobs


class Strategy(object):
    version: RunVersion
    user_id: int

    def __init__(self, user_id):
        self.user_id = user_id
        self.version = None

    def create_version(self):
        instance = RunVersion.objects.filter(user_id=self.user_id).order_by('-pk').first()

        now = timezone.now()
        if not instance or instance.is_completed_task or (now - instance.modified).total_seconds() > 5 * 60:
            instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)

        elif instance.is_error_task:
            # fixme: 에러 상황이면 ??
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

        for job in find_jobs(version=self.version, union_jobs=True):
            lb_helper = LeaderboardHelper(version=self.version, player_job_id=job.id)
            lb_helper.run()

    def collectable_commands(self):
        # daily reward
        # train unload
        # gift
        # ship

        pass

    def on_processing_status(self):
        # 1. heartbeat
        # 2. collect
        # 3. assign job if
        # 4. prepare materials
        # 5. send train

        pass

    def run(self):

        self.version = self.create_version()

        if not self.version:
            raise Exception('Invalid Version')
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

