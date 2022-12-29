from datetime import datetime

from django.utils import timezone

from app_root.bot.utils_server_time import ServerTime
from app_root.users.models import User


class BaseBotRequest:

    def get_data(self, url, user: User, server_time: ServerTime) -> str:
        raise NotImplementedError

    def run(self, url, user: User, server_time: ServerTime):
        s = timezone.now()
        data = self.get_data(url=url, user=user, server_time=server_time)
        e = timezone.now()
        mid = (e-s)/2

        ret_time = self.parse_data(data=data, user=user)

        server_time.adjust_time(ret_time=ret_time, now=s+mid)

    def parse_data(self, data, user: User) -> str:
        raise NotImplementedError
