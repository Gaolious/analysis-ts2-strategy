from typing import Optional

from django.utils import timezone

from app_root.bot.models import RunVersion
from app_root.bot.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.utils import Logger


class BaseBotHelper:
    """
        Bot Helper
    """
    run_version: Optional[RunVersion]
    user: Optional[User]
    server_time: Optional[ServerTimeHelper]
    
    def __init__(self):
        self.run_version = None
        self.user = None
        self.server_time = None

    def get_data(self, url) -> str:
        raise NotImplementedError

    def _update_server_time(self, request_datetime, response_datetime, server_datetime):
        mid = (response_datetime - request_datetime)/2
        self.server_time.adjust_time(server_datetime=server_datetime, now=request_datetime + mid)

    def run(self, run_version, url, user: User, server_time: ServerTimeHelper):
        self.run_version = run_version
        self.user = user
        self.server_time = server_time

        request_datetime = timezone.now()
        data = self.get_data(url=url)
        response_datetime = timezone.now()
        if data:
            ret_time = self.parse_data(data=data)

            server_resp_datetime = self.server_time.convert_strtime_to_datetime(ret_time)

            self._update_server_time(
                request_datetime=request_datetime,
                response_datetime=response_datetime,
                server_datetime=server_resp_datetime,
            )

    def parse_data(self, data) -> str:
        raise NotImplementedError

    def check_response(self, json_data):
        """

        :param json_data:
        """
        success = json_data.get('Success')

        if not success:
            error = json_data.get('Error')
            if error:
                msg = error.get('Message')
                err_msg = error.get('ErrorMessage')
                err_code = error.get('Code')

                if err_msg == 'Invalid or expired session':
                    Logger.error(menu='BOT', action='Server Error', msg=msg, err_msg=err_msg, err_code=err_code)

                    self.user.player_id = ''
                    self.user.game_access_token = ''
                    self.user.authentication_token = ''
                    self.user.remember_me_token = ''
                    self.user.device_id = ''
                    self.user.support_url = ''
                    self.user.save(update_fields=[
                        'player_id',
                        'game_access_token',
                        'authentication_token',
                        'remember_me_token',
                        'device_id',
                        'support_url',
                    ])

            raise Exception('Login Error - Retry !')
