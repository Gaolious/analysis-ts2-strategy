import json
import uuid
from hashlib import md5
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.utils import timezone

from app_root.bots.models import DbDefinition, PlayerLeaderBoard, PlayerJob, PlayerLeaderBoardProgress
from app_root.bots.utils_abstract import BaseBotHelper
from app_root.bots.utils_request import CrawlingHelper
from core.utils import disk_cache, Logger, download_file

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
    instance: Optional[DbDefinition]
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
        if job and job.job_location.region.is_union:
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
            bulk_leader_board_list, bulk_leader_board_progress_list = PlayerLeaderBoard.create_instance(
                data=server_data,
                version_id=self.run_version.id,
                player_job_id=self.player_job_id,
            )

            if bulk_leader_board_list:
                PlayerLeaderBoard.objects.bulk_create(bulk_leader_board_list, 100)
            if bulk_leader_board_list:
                PlayerLeaderBoardProgress.objects.bulk_create(bulk_leader_board_progress_list, 100)

        return server_time
