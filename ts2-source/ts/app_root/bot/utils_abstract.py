from datetime import datetime

from django.utils import timezone

from app_root.bot.models import RunVersion
from app_root.bot.utils_server_time import ServerTimeHelper
from app_root.users.models import User


class BaseBotHelper:
    run_version: RunVersion
    user: User
    server_time: ServerTimeHelper

    def get_data(self, url) -> str:
        raise NotImplementedError

    def run(self, run_version, url, user: User, server_time: ServerTimeHelper):
        self.run_version = run_version
        self.user = user
        self.server_time = server_time

        s = timezone.now()
        data = self.get_data(url=url)
        e = timezone.now()
        mid = (e-s)/2

        ret_time = self.parse_data(data=data)

        server_time.adjust_time(ret_time=ret_time, now=s+mid)

    def parse_data(self, data) -> str:
        raise NotImplementedError
