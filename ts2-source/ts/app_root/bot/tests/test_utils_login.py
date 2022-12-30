from unittest import mock

import pytest
from django.conf import settings

from app_root.bot.models import RunVersion
from app_root.bot.utils_init_data import InitdataHelper
from app_root.bot.utils_login import LoginHelper
from app_root.bot.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.bot.utils_login.CrawlingHelper.get') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.bot.utils_login.CrawlingHelper.post') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('remember_me_token, filename', [
    ('', 'gaolious1_2022.12.29_with_device_id.json'),
    ('a', 'gaolious1_2022.12.29_with_remember_token.json'),
    ('', 'gaolious_2022.12.30_with_device_id.json'),
    ('a', 'gaolious_2022.12.30_with_remember_token.json'),
])
def test_utils_login_helper(multidb, filename, remember_me_token, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'login' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test', remember_me_token=remember_me_token)
    version = RunVersion.objects.create(user_id=user.id)

    server_time = ServerTimeHelper()
    fixture_crawling_post.return_value = FakeResp()

    bot = LoginHelper()
    ###########################################################################
    # call function
    bot.run(url='url', user=user, server_time=server_time, run_version=version)

    ###########################################################################
    # assert
    user.refresh_from_db()
    assert user.player_id
    assert user.game_access_token
    assert user.authentication_token
    assert user.remember_me_token
    assert user.device_id
    assert user.support_url