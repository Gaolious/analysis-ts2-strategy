from unittest import mock

import pytest
from django.conf import settings

from app_root.bot.models import RunVersion
from app_root.bot.utils_endpoints import EndpointHelper
from app_root.bot.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.bot.utils_endpoints.CrawlingHelper.get') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.bot.utils_endpoints.CrawlingHelper.post') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious1_2022.12.29.json',
])
def test_utils_endpoint_helper(multidb, filename, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'endpoints' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    server_time = ServerTimeHelper()
    fixture_crawling_get.return_value = FakeResp()

    bot = EndpointHelper()
    ###########################################################################
    # call function
    bot.run(url='url', user=user, server_time=server_time, run_version=version)

    ###########################################################################
    # assert
    assert bot.endpoints
    assert bot.init_data_urls

    assert bot.get_login_url()
    assert bot.get_init_urls()
    assert bot.get_definition_url()
