from unittest import mock

import pytest
from django.conf import settings

from app_root.bot.utils_init_data import InitData
from app_root.bot.utils_server_time import ServerTime
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.bot.utils_init_data.CrawlingHelper.get') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.bot.utils_init_data.CrawlingHelper.post') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious1_2022.12.29.json',
])
def test_init_data(multidb, filename, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    server_time = ServerTime()
    fixture_crawling_get.return_value = FakeResp()

    bot = InitData()
    ###########################################################################
    # call function
    bot.run(url='url', user=user, server_time=server_time)

    ###########################################################################
    # assert
