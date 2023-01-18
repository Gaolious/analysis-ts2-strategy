from unittest import mock

import pytest
from django.conf import settings

from app_root.bots.models import PlayerJob, \
    PlayerLeaderBoardProgress, PlayerLeaderBoard, JobLocation, Region, CONTENT_CATEGORY_UNION, Location
from app_root.bots.models import RunVersion
from app_root.bots.utils_get_leader_board_table import LeaderBoardHelper
from app_root.bots.utils_init_data import InitdataHelper
from app_root.bots.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp
from core.utils import convert_datetime


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.bot.utils_get_leader_board_table.CrawlingHelper.get') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.bot.utils_get_leader_board_table.CrawlingHelper.post') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_download_file():
    with mock.patch('app_root.bot.utils_get_leader_board_table.download_file') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious_2023.01.08.json',
])
def test_utils_leader_board_helper(multidb, filename, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'get_leader_board_table' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)
    region = Region.objects.create(asset_name='', content_category=CONTENT_CATEGORY_UNION)
    location = Location.objects.create(region=1)
    job_location=JobLocation.objects.create(location=location, region=region)
    job = PlayerJob.objects.create(version_id=version.id, job_id='a', job_type=45, job_location=job_location, required_article_id=1)

    server_time = ServerTimeHelper()
    fixture_crawling_get.return_value = FakeResp()
    bot = LeaderBoardHelper(job.id)

    ###########################################################################
    # call function
    bot.run(url='url', user=user, server_time=server_time, run_version=version)

    ###########################################################################
    # assert
    assert PlayerLeaderBoardProgress.objects.count() > 0
    assert PlayerLeaderBoard.objects.count() > 0
