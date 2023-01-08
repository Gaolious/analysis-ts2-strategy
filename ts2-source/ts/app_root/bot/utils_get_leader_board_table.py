import uuid
from hashlib import md5
from pathlib import Path
from typing import Union, Optional, List, Dict

from django.conf import settings
from django.utils import timezone

from app_root.bot.models import Definition, Article, Factory, Product, Train, Destination, Region, Location, \
    JobLocation, PlayerLeaderBoard, PlayerJob, PlayerLeaderBoardProgress
from app_root.bot.utils_request import CrawlingHelper
from app_root.bot.utils_server_time import ServerTimeHelper
from core.utils import disk_cache, Logger, download_file

import json

from app_root.bot.utils_abstract import BaseBotHelper
from app_root.users.models import User

import sqlite3


LOGGING_MENU = 'utils.get_leader_board_table'


@disk_cache(prefix='get_leader_board_table', smt='{android_id}_{sent_at}.json')
def get_leader_board_table(*, url: str, android_id, sent_at: str, game_access_token: str, player_id: str, job_id: str):
    """
GET /api/v2/query/get-leader-board-table?LeaderBoardId=015bf3d8-d688-4cd0-b2c3-57b61f4e3373&Type=guild-job-contribution&Bracket=1 HTTP/1.1
PXFD-Request-Id: a9de3483-285f-49c8-ab4d-88d2f5313354
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-01-07T17:34:30.060Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.6.2.4023","Language":"en"}
PXFD-Client-Version: 2.6.2.4023
PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
PXFD-Game-Access-Token: ecbabebb-d9b6-50bb-9e25-a7ef5fb417d2
PXFD-Player-Id: 61561146
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate

    :param url:
    :param android_id:
    :param sent_at:
    :param game_access_token:
    :param player_id:
    :return:
    """
    param = {
        'LeaderBoardId': job_id,
        'Type': 'guild-job-contribution',
        'Bracket': '1'
    }
    client_info = {
        "Store": str(settings.CLIENT_INFORMATION_STORE),
        "Version": str(settings.CLIENT_INFORMATION_VERSION),
        "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
    }
    device_id = md5(android_id.encode('utf-8')).hexdigest()
    headers = {
        'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
        'PXFD-Retry-No': '0',
        'PXFD-Sent-At': str(sent_at),
        'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
        'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
        'PXFD-Device-Token': device_id,
        'PXFD-Game-Access-Token': game_access_token,
        'PXFD-Player-Id': player_id,
        'Accept-Encoding': 'gzip, deflate',
    }
    Logger.info(menu=LOGGING_MENU, action='get_definition', msg='before request', url=url, headers=headers)
    resp = CrawlingHelper.get(
        url=url,
        headers=headers,
        payload={},
        cookies={},
        params=param,
    )
    resp_status_code = resp.status_code
    resp_body = resp.content.decode('utf-8')
    resp_headers = {k: v for k, v in resp.headers.items()}
    resp_cookies = {k: v for k, v in resp.cookies.items()}

    Logger.info(
        menu=LOGGING_MENU, action='get_definition', msg='after request',
        status_code=str(resp_status_code),
        body=str(resp_body),
        headers=str(resp_headers),
        cookies=str(resp_cookies),
    )
    return resp_body


class LeaderBoardHelper(BaseBotHelper):
    instance: Optional[Definition]
    BASE_PATH = settings.SITE_PATH / 'download' / 'definition'
    player_job_id: int

    def __init__(self, player_job_id: int):

        super(LeaderBoardHelper, self).__init__()
        self.player_job_id = player_job_id
        self.instance = None

    def download_data(self):
        if self.instance:
            download_filename = Path(self.instance.download_path)

            if self.instance.url and not download_filename.exists():
                download_file(url=self.instance.url, download_filename=download_filename)

            return download_filename.lstat().st_size

    def get_data(self, url: str) -> str:
        """

        :param url:
        :param server_time:
        :param user:
        :return:
        """
        job = PlayerJob.objects.filter(id=self.player_job_id).first()
        if job and job.job_type == 45:
            return get_leader_board_table(
                url=url,
                android_id=self.user.android_id,
                sent_at=self.server_time.get_curr_time(),
                game_access_token=self.user.game_access_token,
                player_id=self.user.player_id,
                job_id=job.job_id,
            )

    def parse_data(self, data) -> str:
        """

        :param user:
        :param data:
        :return:
        """
        json_data = json.loads(data, strict=False)
        self.check_response(json_data=json_data)

        server_time = json_data.get('Time')
        server_data = json_data.get('Data', {})

        if server_data:
            """
                'LeaderboardId' = {str} '015bf3d8-d688-4cd0-b2c3-57b61f4e3373'
                'LeaderboardGroupId' = {str} '3a3dfa63-2e0f-4a40-b36c-08d252db9c2b'            
            """

            leader_board_id = server_data.pop('LeaderboardId', '')
            leader_board_group_id = server_data.pop('LeaderboardGroupId', '')
            progresses = server_data.pop('Progresses', [])
            rewards = server_data.pop('Rewards', [])

            leader_board = PlayerLeaderBoard.objects.create(
                version_id=self.run_version.id,
                player_job_id=self.player_job_id,
                leader_board_id=leader_board_id,
                leader_board_group_id=leader_board_group_id,
            )

            if leader_board and progresses and rewards:
                bulk_list = []
                now = timezone.now()

                for progress, reward in zip(progresses, rewards):
                    player_id = progress.pop('PlayerId', None)
                    avata_id = progress.pop('AvatarId', None)
                    firebase_uid = progress.pop('FirebaseUid', None)
                    _ = progress.pop('LeaderboardGroupId', None)
                    player_name = progress.pop('PlayerName', None)
                    progress_val = progress.pop('Progress', None)
                    position = progress.pop('Position', None)
                    last_updated_at = progress.pop('LastUpdatedAt', None)
                    reward_claimed = progress.pop('RewardClaimed', None)
                    bulk_list.append(
                        PlayerLeaderBoardProgress(
                            version_id=self.run_version.id,
                            player_job_id=self.player_job_id,
                            leader_board_id=leader_board.id,
                            player_id=player_id,
                            avata_id=avata_id,
                            firebase_uid=firebase_uid,
                            player_name=player_name,
                            progress=progress_val,
                            position=position,
                            last_updated_at=last_updated_at,
                            reward_claimed=reward_claimed,
                            rewards=json.dumps(reward, separators=(',', ':')) if reward else '',
                            created=now, modified=now,
                        )
                    )

                if bulk_list:
                    PlayerLeaderBoardProgress.objects.bulk_create(bulk_list, 100)

        return server_time
